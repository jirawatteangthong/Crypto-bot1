import time
import requests
import hmac
import hashlib
import base64
import json
import datetime
import numpy as np
import pytz
import traceback
import ccxt
from statistics import stdev, mean
import pandas as pd

# ----------- CONFIG ------------
API_KEY = "0659b6f2-c86a-466a-82ec-f1a52979bc33"
API_SECRET = "CCB0A67D53315671F599050FCD712CD1"
PASSPHRASE = "Jirawat1-"

TELEGRAM_TOKEN = "7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY"
TELEGRAM_CHAT_ID = "8104629569"

SYMBOL = "BTC-USDT-SWAP"
LEVERAGE = 20
BASE_CAPITAL = 20
RISK_PER_TRADE = 0.02  # ใช้ 2% ของทุนรวม

# ----------- HELPERS ------------
def telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})
    except:
        pass

def now_iso():
    return datetime.datetime.now(pytz.utc).isoformat()

def retry_request(func):
    def wrapper(*args, **kwargs):
        for i in range(3):
            try:
                return func(*args, **kwargs)
            except Exception:
                time.sleep(1)
        raise Exception("API failed 3 times")
    return wrapper

# ----------- OKX SETUP ------------
okx = ccxt.okx({
    "apiKey": API_KEY,
    "secret": API_SECRET,
    "password": PASSPHRASE,
    "enableRateLimit": True,
    "options": {"defaultType": "swap"},
})
okx.set_leverage(LEVERAGE, SYMBOL)

# ----------- STRATEGY LOGIC ------------
def get_ohlcv(symbol, timeframe, limit=100):
    return okx.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

def calculate_macd(close):
    fast = 12
    slow = 26
    signal = 9
    ema_fast = np.array(pd.Series(close).ewm(span=fast).mean())
    ema_slow = np.array(pd.Series(close).ewm(span=slow).mean())
    macd_line = ema_fast - ema_slow
    signal_line = pd.Series(macd_line).ewm(span=signal).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

def check_entry():
    try:
        h4 = get_ohlcv(SYMBOL, '4h')
        m15 = get_ohlcv(SYMBOL, '15m')
        m1 = get_ohlcv(SYMBOL, '1m')

        h4_close = [x[4] for x in h4]
        trend_up = h4_close[-1] > h4_close[-2] > h4_close[-3]

        m15_highs = [x[2] for x in m15[-5:]]
        m15_lows = [x[3] for x in m15[-5:]]
        poi_high = max(m15_highs)
        poi_low = min(m15_lows)

        m1_close = [x[4] for x in m1]
        macd, signal, hist = calculate_macd(m1_close)
        cross_up = macd[-2] < signal[-2] and macd[-1] > signal[-1]

        price = m1_close[-1]
        price_sd = stdev(m1_close[-20:])
        price_mean = mean(m1_close[-20:])
        inside_deviation = abs(price - price_mean) <= 2 * price_sd

        if trend_up and price <= poi_low and cross_up and inside_deviation:
            return "long", price
        elif not trend_up and price >= poi_high and not cross_up and inside_deviation:
            return "short", price
        return None, None
    except Exception as e:
        telegram(f"[ERROR] Strategy check failed: {str(e)}")
        return None, None

# ----------- ORDER FUNCTIONS ------------
@retry_request
def place_order(direction, price):
    size = round((BASE_CAPITAL * LEVERAGE * RISK_PER_TRADE) / price, 3)
    side = 'buy' if direction == 'long' else 'sell'
    order = okx.create_market_order(SYMBOL, side, size)
    order_id = order['id']

    sl = price * (0.995 if direction == 'long' else 1.005)
    tp = price * (1.01 if direction == 'long' else 0.99)
    sl = round(sl, 2)
    tp = round(tp, 2)

    okx.private_post_trade_order_algo({
        "instId": SYMBOL,
        "tdMode": "isolated",
        "side": side,
        "ordType": "oco",
        "sz": str(size),
        "tpTriggerPx": str(tp),
        "tpOrdPx": "-1",
        "slTriggerPx": str(sl),
        "slOrdPx": "-1"
    })

    telegram(f"[ENTRY] {direction.upper()} @ {price}\nTP: {tp}\nSL: {sl}")
    return price, tp, sl

# ----------- MAIN LOOP ------------
win_count = 0
running = True

telegram("บอทเริ่มทำงานแล้ว!")

while running:
    try:
        direction, entry_price = check_entry()
        if direction:
            price, tp, sl = place_order(direction, entry_price)
            time.sleep(1800)  # รอ 30 นาทีต่อไม้
            result_price = okx.fetch_ticker(SYMBOL)['last']
            pnl = (result_price - price) if direction == "long" else (price - result_price)
            profit = pnl * LEVERAGE * BASE_CAPITAL * RISK_PER_TRADE
            telegram(f"[CLOSE] {direction.upper()} @ {result_price} | PnL: ${profit:.2f}")

            if profit > 0:
                win_count += 1
                if win_count % 3 == 0:
                    telegram("[แจ้งเตือน] ชนะครบ 3 ไม้ — แนะนำถอนกำไรครึ่งหนึ่ง!")

        else:
            time.sleep(60)
    except Exception as e:
        telegram(f"[ERROR] {traceback.format_exc()}")
        time.sleep(60)
