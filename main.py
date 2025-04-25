import time
import requests
import okx.Account_api as AccountAPI
import okx.Funding_api as FundingAPI
import okx.Market_api as MarketAPI
import okx.Trade_api as TradeAPI
import okx.Order_api as OrderAPI

# ตั้งค่า API ของ OKX
API_KEY = "0659b6f2-c86a-466a-82ec-f1a52979bc33"
API_SECRET = "CCB0A67D53315671F599050FCD712CD1"
PASSPHRASE = "Jirawat1-"
okx_account = AccountAPI.AccountAPI(API_KEY, API_SECRET, PASSPHRASE)
okx_trade = TradeAPI.TradeAPI(API_KEY, API_SECRET, PASSPHRASE)
okx_market = MarketAPI.MarketAPI(API_KEY, API_SECRET, PASSPHRASE)

# กำหนดจุด OB สำหรับ Buy และ Sell
order_block_low = 20000  # จุดต่ำสุดของ OB
order_block_high = 20500  # จุดสูงสุดของ OB

# ระบุสีของ OB
order_block_color = "blue"  # สีฟ้าหมายถึง Buy, สีแดงหมายถึง Sell

# คำนวณ TP และ SL
sl_offset = 10  # ค่าต่ำกว่าหรือสูงกว่าจุด OB
tp_offset = 20  # ค่าสูงกว่าหรือต่ำกว่าจุด OB

sl = order_block_low - sl_offset if order_block_color == "blue" else order_block_high + sl_offset  # SL
tp = order_block_high + tp_offset if order_block_color == "blue" else order_block_low - tp_offset  # TP

# ฟังก์ชั่นเช็คราคาเข้าซื้อ/ขาย
def check_entry(price, order_block_low, order_block_high, order_block_color):
    if price <= order_block_high and price >= order_block_low:
        if order_block_color == "blue":  # Buy
            print(f"Buy Order: ราคาเข้าซื้อที่: {price}, SL: {sl}, TP: {tp}")
            return "buy"
        elif order_block_color == "red":  # Sell
            print(f"Sell Order: ราคาเข้าขายที่: {price}, SL: {sl}, TP: {tp}")
            return "sell"
    return None

# ฟังก์ชั่นเปิดออเดอร์จริง
def place_order(side, size, price, sl, tp):
    if side == "buy":
        order = okx_trade.create_order(instId="BTC-USDT", tdMode="cross", side="buy", ordType="market", sz=str(size))
    elif side == "sell":
        order = okx_trade.create_order(instId="BTC-USDT", tdMode="cross", side="sell", ordType="market", sz=str(size))
    # ตั้งค่า SL และ TP
    okx_trade.set_stop_loss_take_profit(instId="BTC-USDT", side=side, price=str(price), sl=sl, tp=tp)
    print(f"Order placed: {side} at {price}")
    return order

# ฟังก์ชั่นเช็คราคาและการเปิดออเดอร์
def trade_logic():
    # สมมุติราคา (ราคาปัจจุบันของ BTC)
    current_price = 20100  # คุณสามารถดึงราคาจริงจาก OKX API ได้

    # ตรวจสอบว่าราคาเข้าโซน OB หรือไม่
    side = check_entry(current_price, order_block_low, order_block_high, order_block_color)
    if side:
        # เปิดออเดอร์
        size = 0.01  # ขนาดออเดอร์ (ใช้ตามที่เหมาะสมกับทุนของคุณ)
        place_order(side, size, current_price, sl, tp)

# ฟังก์ชั่นแจ้งเตือนทาง Telegram
def send_telegram_alert(message):
    telegram_url = "https://api.telegram.org/bot7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY/sendMessage"
    chat_id = "8104629569"
    params = {"chat_id": chat_id, "text": message}
    requests.get(telegram_url, params=params)

# ฟังก์ชั่นรันบอท
def main():
    while True:
        try:
            # รัน logic การเทรดทุกๆ 5 วินาที
            trade_logic()

            # แจ้งเตือนเมื่อมีการเปิด/ปิดออเดอร์
            send_telegram_alert("เปิดออเดอร์แล้ว: Buy หรือ Sell")

            # รอ 5 วินาที
            time.sleep(5)
        except Exception as e:
            print(f"เกิดข้อผิดพลาด: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
