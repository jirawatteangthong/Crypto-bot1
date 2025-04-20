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

# ===== Manual Config (แทน .env) =====
API_KEY = "a279dbed-ae3c-44c2-b0c4-fcf1ff6e76cb"
API_SECRET = "FA68643E5A176C00AB09637CBC5DA82E"
API_PASSPHRASE = "Jirawat1-"
TELEGRAM_TOKEN = "7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY"
TELEGRAM_CHAT_ID = "8104629569"

SYMBOL = "BTC-USDT-SWAP"
BASE_URL = "https://www.okx.com"
LEVERAGE = 15
USE_PORTFOLIO_PERCENT = 0.30
RISK_PER_TRADE = 0.02

active_position = {
    "side": None,
    "entry": None,
    "tp": None,
    "sl": None,
    "size": None,
    "algo_id": None,
    "last_profit": None
}

bot_active = True
start_time = time.time()

# ===== Helper Functions =====
def sign(timestamp, method, request_path, body=""):
    msg = f"{timestamp}{method}{request_path}{body}"
    return hmac.new(API_SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()

def get_headers(method, path, body=""):
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

def get_price():
    candles = get_candles("1m", 1)
    return float(candles[-1][4])

# ===== OKX API =====
def get_candles(tf="1H", limit=100):
    path = f"/api/v5/market/candles?instId={SYMBOL}&bar={tf}&limit={limit}"
    res = requests.get(BASE_URL + path, headers=get_headers("GET", path)).json()
    return res["data"][::-1]

def get_balance():
    path = "/api/v5/account/balance?ccy=USDT"
    res = requests.get(BASE_URL + path, headers=get_headers("GET", path)).json()
    return float(res['data'][0]['details'][0]['availBal'])

def get_open_orders():
    path = f"/api/v5/trade/orders-pending?instId={SYMBOL}"
    res = requests.get(BASE_URL + path, headers=get_headers("GET", path)).json()
    return res["data"]

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
    active_position["algo_id"] = res["data"][0]["algoId"]
    return res

def cancel_algo_order(algo_id):
    path = "/api/v5/trade/cancel-algos"
    data = {"instId": SYMBOL, "algoIds": [algo_id]}
    body = json.dumps(data)
    headers = get_headers("POST", path, body)
    return requests.post(BASE_URL + path, headers=headers, data=body).json()

# ===== ICT Logic (1D -> H1 -> M15) =====
def detect_entry_signal():
    m15 = get_candles("15m", 50)
    for i in range(2, len(m15)):
        high1 = float(m15[i - 2][2])
        low3 = float(m15[i][3])
        if low3 > high1:
            return {"side": "buy", "entry": (low3 + high1) / 2}
        low1 = float(m15[i - 2][3])
        high3 = float(m15[i][2])
        if high3 < low1:
            return {"side": "sell", "entry": (high3 + low1) / 2}
    return None

def find_swing_levels(candles, side):
    if side == "buy":
        sl = min(float(c[3]) for c in candles[-5:])
        tp = max(float(c[2]) for c in candles[-5:])
    else:
        sl = max(float(c[2]) for c in candles[-5:])
        tp = min(float(c[3]) for c in candles[-5:])
    return sl, tp

# ===== Trade Logic =====
def trade():
    if not bot_active or get_open_orders():
        return

    signal = detect_entry_signal()
    if not signal:
        return

    entry = signal["entry"]
    side = signal["side"]
    h1 = get_candles("1H", 20)
    sl, tp = find_swing_levels(h1, side)

    balance = get_balance()
    risk = balance * RISK_PER_TRADE
    size = round(risk / abs(entry - sl), 4)

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

    send_telegram(f"[TRADE OPENED]\nSide: {side.upper()}\nEntry: {entry:.2f}\nSL: {sl:.2f}\nTP: {tp:.2f}\nSize: {size}")

def monitor_position():
    if not active_position["entry"] or not active_position["algo_id"]:
        return
    price = get_price()
    entry = active_position["entry"]
    tp = active_position["tp"]
    side = active_position["side"]
    size = active_position["size"]
    tp_half = entry + (tp - entry) * 0.5 if side == "buy" else entry - (entry - tp) * 0.5
    if (side == "buy" and price >= tp_half) or (side == "sell" and price <= tp_half):
        cancel_algo_order(active_position["algo_id"])
        time.sleep(1)
        place_tp_sl(entry, entry, tp, side, size)
        active_position["sl"] = entry
        send_telegram(f"[SL to BE] SL moved to Breakeven at {entry:.2f}")
        active_position["algo_id"] = None

# ===== Telegram Webhook =====
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    global bot_active
    msg = request.json["message"]["text"].lower()
    if "/ping" in msg:
        send_telegram(f"ทำงานปกติ | เวลา: {datetime.utcnow()}")
    elif "/uptime" in msg:
        uptime = round((time.time() - start_time) / 3600, 2)
        send_telegram(f"Uptime: {uptime} ชั่วโมง")
    elif "/status" in msg:
        send_telegram(f"Bot Status: {'ทำงานอยู่' if bot_active else 'หยุดอยู่'}")
    elif "stop bot" in msg:
        bot_active = False
        send_telegram("บอทหยุดทำงานแล้ว")
    elif "resume bot" in msg:
        bot_active = True
        send_telegram("บอทกลับมาทำงานแล้ว")
    elif "ราคาตอนนี้" in msg:
        send_telegram(f"ราคา BTC: {get_price()} USDT")
    elif "จุดเข้า" in msg:
        send_telegram(f"Entry ล่าสุด: {active_position['entry']}")
    elif "กำไรล่าสุด" in msg:
        send_telegram(f"กำไรล่าสุด: {active_position['last_profit']}")
    elif "สถานะพอร์ต" in msg:
        send_telegram(f"USDT คงเหลือ: {get_balance()}")
    return "ok"

@app.route("/")
def home():
    return f"ICT Bot Running - {datetime.utcnow()}"

# ===== Run Scheduler =====
threading.Thread(target=lambda: (
    schedule.every().hour.at(":00").do(trade),
    schedule.every(5).minutes.do(monitor_position),
    [schedule.run_pending() or time.sleep(1) for _ in iter(int, 1)]
), daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
