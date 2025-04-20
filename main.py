import os
import time
import json
import hmac
import hashlib
import requests
import schedule
import threading
from datetime import datetime
from flask import Flask, request

app = Flask(__name__)

# ===== API Keys =====
API_KEY = "a279dbed-ae3c-44c2-b0c4-fcf1ff6e76cb"
API_SECRET = "FA68643E5A176C00AB09637CBC5DA82E"
API_PASSPHRASE = "Jirawat1-"
TELEGRAM_TOKEN = "7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY"
TELEGRAM_CHAT_ID = "8104629569"

SYMBOL = "BTC-USDT-SWAP"
BASE_URL = "https://www.okx.com"
LEVERAGE = 15
RISK_PER_TRADE = 0.02
USE_PORTFOLIO_PERCENT = 0.30
ATR_THRESHOLD = 1000

active_position = {
    "last_profit": None,
    "side": None,
    "entry": None,
    "tp": None,
    "sl": None,
    "size": None,
    "algo_id": None
}

# ===== Helper Functions =====
def sign(timestamp, method, request_path, body=''):
    msg = f"{timestamp}{method}{request_path}{body}"
    return hmac.new(API_SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()

def get_headers(method, path, body=''):
    timestamp = str(time.time())
    signature = sign(timestamp, method, path, body)
    return {
        "OK-ACCESS-KEY": API_KEY,
        "OK-ACCESS-SIGN": signature,
        "OK-ACCESS-TIMESTAMP": timestamp,
        "OK-ACCESS-PASSPHRASE": API_PASSPHRASE,
        "Content-Type": "application/json"
    }

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})

# ===== OKX API Calls =====
def get_candles():
    path = f"/api/v5/market/candles?instId={SYMBOL}&bar=1H&limit=100"
    res = requests.get(BASE_URL + path, headers=get_headers("GET", path))
    return res.json()["data"][::-1]

def get_balance():
    path = "/api/v5/account/balance?ccy=USDT"
    res = requests.get(BASE_URL + path, headers=get_headers("GET", path))
    return float(res.json()['data'][0]['details'][0]['availBal'])

def get_open_orders():
    path = f"/api/v5/trade/orders-pending?instId={SYMBOL}"
    res = requests.get(BASE_URL + path, headers=get_headers("GET", path))
    return res.json()["data"]

def place_order(side, size):
    path = "/api/v5/trade/order"
    data = {
        "instId": SYMBOL,
        "tdMode": "isolated",
        "side": side,
        "ordType": "market",
        "sz": str(size),
        "lever": str(LEVERAGE)
    }
    body = json.dumps(data)
    headers = get_headers("POST", path, body)
    res = requests.post(BASE_URL + path, headers=headers, data=body).json()
    send_telegram(f"[ORDER] {side.upper()} {SYMBOL} | Size: {size}")
    return res

def place_tp_sl(entry, sl, tp, side, size):
    path = "/api/v5/trade/order-algo"
    exit_side = "sell" if side == "buy" else "buy"
    data = {
        "instId": SYMBOL,
        "tdMode": "isolated",
        "side": exit_side,
        "ordType": "oco",
        "slTriggerPx": f"{sl:.2f}",
        "slOrdPx": "-1",
        "tpTriggerPx": f"{tp:.2f}",
        "tpOrdPx": "-1",
        "sz": str(size)
    }
    body = json.dumps(data)
    headers = get_headers("POST", path, body)
    res = requests.post(BASE_URL + path, headers=headers, data=body).json()
    if "data" in res:
        algo_id = res["data"][0]["algoId"]
        active_position["algo_id"] = algo_id
    return res

def cancel_algo_order(algo_id):
    path = "/api/v5/trade/cancel-algos"
    data = {"instId": SYMBOL, "algoIds": [algo_id]}
    body = json.dumps(data)
    headers = get_headers("POST", path, body)
    res = requests.post(BASE_URL + path, headers=headers, data=body).json()
    return res

# ===== Strategy Logic =====
def calculate_atr(candles, period=14):
    trs = []
    for i in range(1, period + 1):
        high = float(candles[-i][2])
        low = float(candles[-i][3])
        prev_close = float(candles[-i - 1][4])
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
    return sum(trs) / period

def detect_fvg(candles):
    for i in range(2, len(candles)):
        c1 = candles[i - 2]
        c3 = candles[i]
        high1 = float(c1[2])
        low3 = float(c3[3])
        if low3 > high1:
            return {"side": "buy", "entry": (low3 + high1) / 2}
        low1 = float(c1[3])
        high3 = float(c3[2])
        if high3 < low1:
            return {"side": "sell", "entry": (high3 + low1) / 2}
    return None

def find_swing_levels(candles, side):
    if side == "buy":
        swing_low = min(float(c[3]) for c in candles[-5:])
        swing_high = max(float(c[2]) for c in candles[-5:])
        return swing_low, swing_high
    else:
        swing_high = max(float(c[2]) for c in candles[-5:])
        swing_low = min(float(c[3]) for c in candles[-5:])
        return swing_high, swing_low

# ===== Core Trade Function =====
def trade():
    if get_open_orders():
        return

    candles = get_candles()
    atr = calculate_atr(candles)
    if atr > ATR_THRESHOLD:
        return

    signal = detect_fvg(candles)
    if not signal:
        return

    entry = signal["entry"]
    side = signal["side"]
    sl, tp = find_swing_levels(candles, side)
    sl_distance = abs(entry - sl)
    if sl_distance == 0:
        return

    balance = get_balance()
    risk = balance * RISK_PER_TRADE
    size = round(risk / sl_distance, 4)

    place_order(side, size)
    time.sleep(1)
    place_tp_sl(entry, sl, tp, side, size)

    active_position.update({
        "side": side,
        "entry": entry,
        "tp": tp,
        "sl": sl,
        "size": size
    })

    msg = "[ICT TRADE OPENED]\n"
    msg += f"Side: {side.upper()}\nEntry: {entry:.2f}\nSL: {sl:.2f}\nTP: {tp:.2f}\nSize: {size}\nATR: {atr:.2f}"
    send_telegram(msg)

# ===== Move SL to Break-Even =====
def monitor_open_position():
    if not active_position["entry"] or not active_position["algo_id"]:
        return

    candles = get_candles()
    last_price = float(candles[-1][4])
    side = active_position["side"]
    entry = active_position["entry"]
    tp = active_position["tp"]
    size = active_position["size"]

    tp_half = entry + (tp - entry) * 0.5 if side == "buy" else entry - (entry - tp) * 0.5
    if (side == "buy" and last_price >= tp_half) or (side == "sell" and last_price <= tp_half):
        cancel_algo_order(active_position["algo_id"])
        time.sleep(1)
        place_tp_sl(entry, entry, tp, side, size)
        active_position["sl"] = entry
        send_telegram(f"[SL MOVED TO BE] SL moved to Break-Even at {entry:.2f}")
        active_position["algo_id"] = None

# ===== Telegram Bot Handlers =====
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    data = request.get_json()
    message = data.get("message", {}).get("text", "").lower()

    if "à¸à¸³à¸à¸²à¸à¹à¸«à¸¡" in message:
        send_telegram("à¸à¸­à¸à¸à¸³à¸à¸²à¸à¸­à¸¢à¸¹à¹à¸à¸£à¸±à¸")
    elif "à¸£à¸²à¸à¸²" in message:
        price = float(get_candles()[-1][4])
        send_telegram(f"à¸£à¸²à¸à¸²à¸¥à¹à¸²à¸ªà¸¸à¸ BTC: {price:.2f} USDT")
    elif "à¸à¸¸à¸à¹à¸à¹à¸²" in message:
        if active_position["entry"]:
            send_telegram(f"à¸à¸¸à¸à¹à¸à¹à¸²à¸­à¸­à¹à¸à¸­à¸£à¹à¸¥à¹à¸²à¸ªà¸¸à¸: {active_position['entry']:.2f}")
        else:
            send_telegram("à¸¢à¸±à¸à¹à¸¡à¹à¸¡à¸µà¸à¸¸à¸à¹à¸à¹à¸²à¸­à¸­à¹à¸à¸­à¸£à¹")
    elif "à¸à¸³à¹à¸£" in message:
        if active_position["entry"]:
            current = float(get_candles()[-1][4])
            entry = active_position["entry"]
            size = active_position["size"]
            pnl = (current - entry) * size if active_position["side"] == "buy" else (entry - current) * size
            send_telegram(f"à¸à¸³à¹à¸£/à¸à¸²à¸à¸à¸¸à¸à¸à¸±à¸à¸à¸¸à¸à¸±à¸: {pnl:.2f} USDT")
        else:
            send_telegram("à¸¢à¸±à¸à¹à¸¡à¹à¸¡à¸µà¸­à¸­à¹à¸à¸­à¸£à¹à¸à¸µà¹à¹à¸à¸´à¸à¸­à¸¢à¸¹à¹")
    elif "à¸à¸­à¸£à¹à¸" in message:
        balance = get_balance()
        send_telegram(f"à¸¢à¸­à¸à¸à¸à¹à¸«à¸¥à¸·à¸­à¸à¸­à¸£à¹à¸: {balance:.2f} USDT")
    return "ok"

# ===== Schedule =====
def run_schedule():
    schedule.every().hour.at(":00").do(trade)
    schedule.every(5).minutes.do(monitor_open_position)
    while True:
        schedule.run_pending()
        time.sleep(1)

# ===== Flask App =====
@app.route("/")
def home():
    return f"ICT Bot Running - {datetime.utcnow()}"

threading.Thread(target=run_schedule, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
