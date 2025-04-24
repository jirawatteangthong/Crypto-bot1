import ccxt
import time
import requests
import math
import pandas as pd
import pandas_ta as ta

# -------- CONFIG --------
API_KEY = '0659b6f2-c86a-466a-82ec-f1a52979bc33'
API_SECRET = 'CCB0A67D53315671F599050FCD712CD1'
API_PASSWORD = 'Jirawat1-'
SYMBOL = 'BTC/USDT:USDT'
TELEGRAM_TOKEN = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
TELEGRAM_CHAT_ID = '8104629569'
LEVERAGE = 20
RISK_PER_TRADE = 1.0  # ใช้ทุนทั้งหมดแบบ all-in

# -------- INIT --------
exchange = ccxt.okx({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSWORD,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

# -------- FUNCTIONS --------
def send_telegram(msg):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': msg}
    requests.post(url, data=data)

def get_last_price():
    return exchange.fetch_ticker(SYMBOL)['last']

def get_balance():
    balance = exchange.fetch_balance()
    return balance['total']['USDT']

def get_macd_signal():
    ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe='1m', limit=100)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    macd = ta.macd(df['close'])
    df = pd.concat([df, macd], axis=1)
    latest = df.iloc[-1]

    macd_line = latest['MACD_12_26_9']
    signal_line = latest['MACDs_12_26_9']

    if pd.isna(macd_line) or pd.isna(signal_line):
        return None

    if macd_line > signal_line:
        return 'long'
    elif macd_line < signal_line:
        return 'short'
    else:
        return None

def get_poi_signal():
    ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe='15m', limit=50)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    last_low = df['low'].rolling(window=10).min().iloc[-1]
    last_high = df['high'].rolling(window=10).max().iloc[-1]
    current_price = df['close'].iloc[-1]

    distance_to_low = abs(current_price - last_low)
    distance_to_high = abs(current_price - last_high)

    if distance_to_low < distance_to_high and distance_to_low < current_price * 0.005:
        return 'long'
    elif distance_to_high < current_price * 0.005:
        return 'short'
    return None

def calculate_order_size(balance, entry, sl, side):
    risk = balance * RISK_PER_TRADE
    risk_per_unit = abs(entry - sl)
    size = (risk * LEVERAGE) / risk_per_unit
    return round(size, 3)

def place_order(entry, sl, tp, size, side):
    params = {
        'tdMode': 'isolated',
        'reduceOnly': False,
        'slTriggerPx': sl,
        'slOrdPx': sl,
        'tpTriggerPx': tp,
        'tpOrdPx': tp,
        'tpTriggerPxType': 'last',
        'slTriggerPxType': 'last'
    }
    if side == 'long':
        return exchange.create_market_buy_order(SYMBOL, size, params)
    else:
        return exchange.create_market_sell_order(SYMBOL, size, params)

def move_sl_to_be():
    # OKX ยังไม่เปิดให้แก้ SL ตรงๆ ใน order-algo
    # ฟังก์ชันนี้จะเป็น placeholder
    send_telegram("SL moved to Break-even (simulated)")

# -------- MAIN LOOP --------
def main():
    send_telegram("Bot Started (MACD + POI + Long/Short enabled)")

    while True:
        try:
            trend_macd = get_macd_signal()
            poi_signal = get_poi_signal()

            if not trend_macd or not poi_signal:
                time.sleep(15)
                continue

            if trend_macd == poi_signal:
                side = trend_macd
                entry_price = get_last_price()
                balance = get_balance()

                sl = entry_price * 0.99 if side == 'long' else entry_price * 1.01
                tp = entry_price * 1.02 if side == 'long' else entry_price * 0.98

                size = calculate_order_size(balance, entry_price, sl, side)
                exchange.set_leverage(LEVERAGE, SYMBOL)

                order = place_order(entry_price, sl, tp, size, side)
                send_telegram(f"[{side.upper()}] Entry: {entry_price}\nSL: {sl}\nTP: {tp}\nSize: {size}")

                half_tp = entry_price + (tp - entry_price) / 2 if side == 'long' else entry_price - (entry_price - tp) / 2

                while True:
                    current_price = get_last_price()
                    if (side == 'long' and current_price >= half_tp) or (side == 'short' and current_price <= half_tp):
                        move_sl_to_be()
                        break
                    time.sleep(5)

                break  # 1 trade only per run
            else:
                time.sleep(10)

        except Exception as e:
            send_telegram(f"Error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
