import time
import requests
import hmac
import hashlib
import base64
import json
import threading
from datetime import datetime
from collections import deque

# ------------------- OKX CONFIG -------------------
API_KEY = "e8e/82c5a-6ccd-4cb3-92a9-3f10144ecd28"
API_SECRET = "3E0BDFF2AF2EF11217C2DCC7E88400C3"
PASSPHRASE = "Jirawat1-"
BASE_URL = "https://www.okx.com"
SYMBOL = "BTC-USDT-SWAP"
LEVERAGE = 10
TRADE_PERCENTAGE = 0.3  # 30% ของพอร์ต

# ------------------- TELEGRAM CONFIG -------------------
TELEGRAM_TOKEN = "7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY"
CHAT_ID = "8104629569"

# ------------------- SYSTEM STATE -------------------
state = {
    "in_position": False,
    "entry_price": 0.0,
    "order_id": None,
    "stop_loss_price": 0.0,
    "take_profit_price": 0.0,
    "partial_tp_done": False,
    "break_even_done": False,
    "trailing_sl_active": False
}

price_history = deque(maxlen=200)  # ใช้เก็บราคาย้อนหลังสำหรับ Swing

# ------------------- TELEGRAM FUNCTION -------------------
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg}
        requests.post(url, data=data)
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

# ------------------- AUTH / SIGN -------------------
def get_server_time():
    response = requests.get(f"{BASE_URL}/api/v5/public/time")
    return str(response.json()['data'][0]['ts'])

def sign_request(timestamp, method, request_path, body=''):
    message = f"{timestamp}{method.upper()}{request_path}{body}"
    mac = hmac.new(bytes(API_SECRET, encoding='utf8'), bytes(message, encoding='utf8'), digestmod=hashlib.sha256)
    return base64.b64encode(mac.digest()).decode()

# ------------------- OKX REQUEST -------------------
def okx_request(method, path, data=None, private=False):
    timestamp = get_server_time()
    body = json.dumps(data) if data else ''
    headers = {
        'OK-ACCESS-KEY': API_KEY,
        'OK-ACCESS-SIGN': sign_request(timestamp, method, path, body),
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': PASSPHRASE,
        'Content-Type': 'application/json'
    } if private else {}

    url = BASE_URL + path
    try:
        if method == "GET":
            r = requests.get(url, headers=headers)
        elif method == "POST":
            r = requests.post(url, headers=headers, json=data)
        elif method == "DELETE":
            r = requests.delete(url, headers=headers)

        res = r.json()
        if 'data' not in res:
            send_telegram(f"[DEBUG] ไม่มี 'data':\n{json.dumps(res, indent=2)}")
            return None
        return res
    except Exception as e:
        send_telegram(f"[ERROR] EXCEPTION ใน okx_request:\n{str(e)}")
        return None

# ------------------- PRICE / BALANCE -------------------
def get_price():
    res = okx_request("GET", f"/api/v5/market/ticker?instId={SYMBOL}")
    if res and "data" in res:
        return float(res["data"][0]["last"])
    return 0.0

def get_balance():
    res = okx_request("GET", "/api/v5/account/balance", private=True)
    if res and "data" in res:
        for d in res["data"][0]["details"]:
            if d["ccy"] == "USDT":
                return float(d["availEq"])
    return 0.0

def set_leverage():
    return okx_request("POST", "/api/v5/account/set-leverage", {
        "instId": SYMBOL,
        "lever": str(LEVERAGE),
        "mgnMode": "isolated"
    }, private=True)

def fetch_ohlc(tf="1H", limit=100):
    res = okx_request("GET", f"/api/v5/market/candles?instId={SYMBOL}&bar={tf}&limit={limit}")
    if res and "data" in res:
        data = [[float(i) for i in item] for item in res["data"]]
        data.reverse()  # ทำให้เป็นลำดับเวลาใหม่ -> เก่าสุดไปใหม่สุด
        return data
    return []

def find_swing_high_low(data, lookback=5):
    swing_high, swing_low = None, None
    for i in range(lookback, len(data)-lookback):
        highs = [data[j][2] for j in range(i-lookback, i+lookback+1)]
        lows = [data[j][3] for j in range(i-lookback, i+lookback+1)]
        if data[i][2] == max(highs):
            swing_high = data[i][2]
        if data[i][3] == min(lows):
            swing_low = data[i][3]
    return swing_high, swing_low

def is_buy_signal():
    h4 = fetch_ohlc("4H", 50)
    m15 = fetch_ohlc("15m", 50)
    m1 = fetch_ohlc("1m", 30)
    if not h4 or not m15 or not m1:
        return False

    sh, sl = find_swing_high_low(h4)
    if not sh or not sl:
        return False

    last_price = get_price()
    if sl < last_price < sh and m15[-1][4] > m15[-2][4] and m1[-1][4] > m1[-2][4]:
        return {"side": "buy", "entry": last_price, "sl": sl * 0.997, "tp": last_price * 1.02}
    return False

def is_sell_signal():
    h4 = fetch_ohlc("4H", 50)
    m15 = fetch_ohlc("15m", 50)
    m1 = fetch_ohlc("1m", 30)
    if not h4 or not m15 or not m1:
        return False

    sh, sl = find_swing_high_low(h4)
    if not sh or not sl:
        return False

    last_price = get_price()
    if sl < last_price < sh and m15[-1][4] < m15[-2][4] and m1[-1][4] < m1[-2][4]:
        return {"side": "sell", "entry": last_price, "sl": sh * 1.003, "tp": last_price * 0.98}
    return False

def open_position(signal):
    size = round(get_balance() * RISK_PER_TRADE * LEVERAGE / signal["entry"], 3)
    order = okx_request("POST", "/api/v5/trade/order", {
        "instId": SYMBOL,
        "tdMode": "isolated",
        "side": signal["side"],
        "ordType": "market",
        "sz": str(size)
    }, private=True)

    time.sleep(2)

    # Set SL/TP
    sl_price = round(signal["sl"], 2)
    tp_price = round(signal["tp"], 2)
    algo = okx_request("POST", "/api/v5/trade/order-algo", {
        "instId": SYMBOL,
        "tdMode": "isolated",
        "side": "sell" if signal["side"] == "buy" else "buy",
        "ordType": "oco",
        "sz": str(size),
        "tpTriggerPx": str(tp_price),
        "tpOrdPx": "-1",
        "slTriggerPx": str(sl_price),
        "slOrdPx": "-1"
    }, private=True)

    send_telegram(f"เข้าออเดอร์: {signal['side'].upper()}\nราคา: {signal['entry']:.2f}\nTP: {tp_price}\nSL: {sl_price}")
    return {"side": signal["side"], "entry": signal["entry"], "tp": tp_price, "sl": sl_price, "size": size, "status": "open"}

def check_order_status(position):
    last = get_price()
    if not position:
        return None

    if position["side"] == "buy":
        if last >= position["tp"]:
            send_telegram(f"ปิดกำไร: BUY ที่ {last:.2f}")
            return None
        elif last <= position["sl"]:
            send_telegram(f"โดน SL: BUY ที่ {last:.2f}")
            return None
    else:
        if last <= position["tp"]:
            send_telegram(f"ปิดกำไร: SELL ที่ {last:.2f}")
            return None
        elif last >= position["sl"]:
            send_telegram(f"โดน SL: SELL ที่ {last:.2f}")
            return None
    return position

def run_bot():
    send_telegram("บอทเริ่มทำงานแล้วนจ๊ะ")
    set_leverage()

    position = None
    while True:
        try:
            if not position:
                buy = is_buy_signal()
                sell = is_sell_signal()
                signal = buy if buy else sell
                if signal:
                    position = open_position(signal)

            position = check_order_status(position)
            time.sleep(15)
        except Exception as e:
            send_telegram(f"[ERROR LOOP] {str(e)}")
            time.sleep(60)

# เริ่มทำงานทันที
if __name__ == "__main__":
    run_bot()
