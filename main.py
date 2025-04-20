# main.py
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

# === CONFIG ===
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

start_time = time.time()
bot_active = True

active_position = {
    "last_profit": None,
    "side": None,
    "entry": None,
    "tp": None,
    "sl": None,
    "size": None,
    "algo_id": None
}

# === HELPERS ===
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

# === OKX API ===
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
    algo_id = res["data"][0]["algoId"]
    active_position["algo_id"] = algo_id
    return res

def cancel_algo_order(algo_id):
    path = "/api/v5/trade/cancel-algos"
    data = {"instId": SYMBOL, "algoIds": [algo_id]}
    body = json.dumps(data)
    headers = get_headers("POST", path, body)
    return requests.post(BASE_URL + path, headers=headers, data=body).json()

# === STRATEGY ===
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

# === TRADE ===
def trade():
    if not bot_active or get_open_orders():
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

    send_telegram(f"[ICT TRADE OPENED]\nSide: {side.upper()}\nEntry: {entry:.2f}\nSL: {sl:.2f}\nTP: {tp:.2f}\nSize: {size}")

# === MONITOR ===
def monitor_open_position():
    if not bot_active or not active_position["entry"]:
        return

    candles = get_candles()
    price = float(candles[-1][4])
    entry = active_position["entry"]
    tp = active_position["tp"]
    sl = active_position["sl"]
    side = active_position["side"]
    size = active_position["size"]
    algo_id = active_position["algo_id"]

    # SL to BE
    tp_half = entry + (tp - entry) * 0.5 if side == "buy" else entry - (entry - tp) * 0.5
    if (side == "buy" and price >= tp_half) or (side == "sell" and price <= tp_half):
        cancel_algo_order(algo_id)
        time.sleep(1)
        place_tp_sl(entry, entry, tp, side, size)
        active_position["sl"] = entry
        send_telegram(f"[SL MOVED TO BE] SL moved to Break-Even at {entry:.2f}")
        active_position["algo_id"] = None

    # Trailing Stop
    gain = (price - entry) if side == "buy" else (entry - price)
    if gain > abs(tp - entry) * 0.8:
        new_tp = price + (tp - entry) if side == "buy" else price - (entry - tp)
        new_sl = entry + (gain * 0.5) if side == "buy" else entry - (gain * 0.5)
        cancel_algo_order(algo_id)
        time.sleep(1)
        place_tp_sl(entry, new_sl, new_tp, side, size)
        send_telegram(f"[TRAILING STOP] New TP: {new_tp:.2f}, New SL: {new_sl:.2f}")
        active_position["tp"], active_position["sl"] = new_tp, new_sl

# === SCHEDULER ===
def run_schedule():
    schedule.every().hour.at(":00").do(trade)
    schedule.every(5).minutes.do(monitor_open_position)
    while True:
        schedule.run_pending()
        time.sleep(1)

# === TELEGRAM BOT ===
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    global bot_active
    data = request.json
    if "message" in data:
        text = data["message"]["text"]
        chat_id = data["message"]["chat"]["id"]

        if str(chat_id) != TELEGRAM_CHAT_ID:
            return "unauthorized", 403

        if text == "/ping":
            now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            send_telegram(f"Bot ทำงานปกติ | เวลา: {now}")

        elif text == "/uptime":
            uptime = int(time.time() - start_time)
            hours = uptime // 3600
            send_telegram(f"บอทรันมาแล้ว {hours} ชั่วโมง")

        elif text == "stop bot":
            bot_active = False
            send_telegram("บอทหยุดทำงานชั่วคราวแล้ว")

        elif text == "resume bot":
            bot_active = True
            send_telegram("บอทกลับมาทำงานอีกครั้งแล้ว")

        elif text == "กำไรล่าสุด":
            profit = active_position["last_profit"]
            send_telegram(f"กำไรล่าสุด: {profit}" if profit else "ยังไม่มีกำไรล่าสุด")

        elif text == "สถานะพอร์ต":
            bal = get_balance()
            send_telegram(f"ยอดพอร์ตปัจจุบัน: {bal:.2f} USDT")

        elif text == "บอททำงานไหม":
            send_telegram("บอทกำลังทำงานอยู่ครับ" if bot_active else "บอทหยุดอยู่ครับ")

        elif text == "ราคา":
            candles = get_candles()
            price = float(candles[-1][4])
            send_telegram(f"ราคาล่าสุด BTC: {price:.2f}")

        elif text == "จุดเข้า":
            entry = active_position["entry"]
            send_telegram(f"จุดเข้าออเดอร์: {entry}" if entry else "ยังไม่มีออเดอร์")

    return "ok", 200

# === START ===
threading.Thread(target=run_schedule, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
