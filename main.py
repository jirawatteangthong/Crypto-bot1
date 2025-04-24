import ccxt
import pandas as pd
import talib
import time
import telegram
import math

# ตั้งค่าการเชื่อมต่อกับ OKX
api_key = '0659b6f2-c86a-466a-82ec-f1a52979bc33'
api_secret = 'CCB0A67D53315671F599050FCD712CD1'
password = 'Jirawat1-'
exchange = ccxt.okx({
    'apiKey': api_key,
    'secret': api_secret,
    'password': password
})

# ตั้งค่า Telegram
telegram_bot = telegram.Bot(token='7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY')
chat_id = '8104629569'

# ฟังก์ชันแจ้งเตือนผ่าน Telegram
def send_telegram(message):
    telegram_bot.send_message(chat_id=chat_id, text=message)

# ฟังก์ชันเช็กเทรนด์จาก H1
def check_trend_h1():
    ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=100)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['high_prev'] = df['high'].shift(1)
    df['low_prev'] = df['low'].shift(1)
    
    if df['high'].iloc[-1] > df['high_prev'].iloc[-1] and df['low'].iloc[-1] > df['low_prev'].iloc[-1]:
        return 'uptrend'
    elif df['high'].iloc[-1] < df['high_prev'].iloc[-1] and df['low'].iloc[-1] < df['low_prev'].iloc[-1]:
        return 'downtrend'
    return 'neutral'

# ฟังก์ชันหา POI จาก M15
def find_poi_m15():
    ohlcv = exchange.fetch_ohlcv('BTC/USDT', '15m', limit=100)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    low_recent = df['low'].min()
    return low_recent

# ฟังก์ชันคอนเฟิร์มจุดเข้า (MACD + Standard Deviation)
def confirm_entry_m1():
    ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1m', limit=100)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    # คำนวณ MACD
    macd, signal, hist = talib.MACD(df['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    macd_cross = macd.iloc[-1] > signal.iloc[-1]
    
    # คำนวณ Standard Deviation
    std_dev = df['close'].std()
    price_in_std_range = df['close'].iloc[-1] < (df['close'].mean() + 2 * std_dev) and df['close'].iloc[-1] > (df['close'].mean() - 2 * std_dev)
    
    if macd_cross and price_in_std_range:
        return True
    return False

# ฟังก์ชันคำนวณขนาดออเดอร์และ Leverage
def calculate_position_size(balance, sl_distance, leverage=None):
    risk = 0.02  # ความเสี่ยง 2% ของทุน
    position_size = (balance * risk) / sl_distance
    
    if leverage:
        position_size *= leverage
    return position_size

# ฟังก์ชันคำนวณ Leverage จาก SL
def calculate_leverage(sl_distance, balance):
    risk_per_trade = 0.02  # เสี่ยง 2% ของทุน
    required_margin = sl_distance * risk_per_trade
    leverage = balance / required_margin
    return leverage

# ฟังก์ชันเปิดออเดอร์พร้อม TP/SL (OCO)
def place_order_oco(symbol, position_size, sl_price, tp_price):
    params = {
        'stop_loss_price': sl_price,
        'take_profit_price': tp_price,
    }
    order = exchange.create_market_buy_order(symbol, position_size, params=params)
    send_telegram(f"Order placed: {order}")
    return order

# ฟังก์ชันตรวจสอบผลลัพธ์ของออเดอร์
def check_order_closed(order_id):
    order = exchange.fetch_order(order_id, 'BTC/USDT')
    if order['status'] == 'closed':
        send_telegram(f"Order {order_id} closed")
        return True
    return False

# ฟังก์ชันปรับ SL และ Leverage ถ้าทำกำไรได้เกิน 50% ของ TP
def adjust_sl_and_leverage(order_id, tp_price, current_price, sl_price, leverage):
    # คำนวณ % กำไรที่ทำได้
    profit_percent = (current_price - sl_price) / (tp_price - sl_price)
    
    if profit_percent >= 0.5:  # ถ้ากำไรได้เกิน 50% ของ TP
        new_sl = sl_price  # ขยับ SL เป็น break-even
        new_leverage = min(leverage * 1.2, 50)  # ปรับ Leverage เพิ่มขึ้น (ไม่เกิน 50x)
        
        # ปรับ SL และ Leverage
        order = exchange.create_market_order('BTC/USDT', order_id, params={
            'stop_loss_price': new_sl,
            'leverage': new_leverage
        })
        
        send_telegram(f"SL moved to break-even and leverage increased to {new_leverage}x.")
        return order
    return None

# ฟังก์ชันหลัก
def main():
    balance = exchange.fetch_balance()['total']['USDT']
    trend = check_trend_h1()
    
    if trend == 'uptrend':
        poi = find_poi_m15()
        if confirm_entry_m1():
            sl_distance = abs(poi - balance)  # คำนวณระยะ SL
            leverage = calculate_leverage(sl_distance, balance)
            position_size = calculate_position_size(balance, sl_distance, leverage)
            
            # คำนวณ TP ตามกราฟ (ใช้แนวต้านหรือแนวรับที่สำคัญ)
            tp_price = balance * 1.02  # ตั้ง TP ที่เป็นระยะที่เหมาะสมกับกราฟ
            
            sl_price = balance * 0.98  # ตั้ง SL ที่ -2% ของราคาปัจจุบัน
            
            order = place_order_oco('BTC/USDT', position_size, sl_price, tp_price)
            time.sleep(10)
            
            # หลังจากออเดอร์เปิดแล้ว ให้ตรวจสอบว่าออเดอร์ทำกำไรได้เกิน 50% ของ TP หรือยัง
            if check_order_closed(order['id']):
                current_price = exchange.fetch_ticker('BTC/USDT')['last']  # ราคาปัจจุบัน
                adjust_sl_and_leverage(order['id'], tp_price, current_price, sl_price, leverage)
                # อัปเดตทุนหลังจากผลลัพธ์
                balance = exchange.fetch_balance()['total']['USDT']
                send_telegram(f"New balance: {balance}")
                
                # ถ้าชนะ 3 ครั้ง ถอนครึ่งหนึ่ง
                if balance > 3 * 20:  # ถ้าเป็นกำไร 3 ไม้
                    send_telegram(f"Withdraw half of the profit: {balance / 2}")
                    
    else:
        send_telegram("No valid trend, skipping trade.")

if __name__ == "__main__":
    while True:
        main()
        time.sleep(60)  # เช็กทุกๆ 1 นาที
