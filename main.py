import time
import json
import hmac
import hashlib
import requests
import threading
from datetime import datetime
from flask import Flask, request

# === CONFIG ===
API_KEY = "e8e82c5a-6ccd-4cb3-92a9-3f10144ecd28"
API_SECRET = "3E0BDFF2AF2EF11217C2DCC7E88400C3"
API_PASSPHRASE = "Jirawat1-"
TELEGRAM_TOKEN = "7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY"
TELEGRAM_CHAT_ID = "8104629569"
BASE_URL = "https://www.okx.com"
SYMBOL = "BTC-USDT-SWAP"
LEVERAGE = 10

app = Flask(__name__)
bot_active = True
active_position = {"side": None, "entry": None, "size": None, "order_id": None}

# === UTIL ===
def get_server_timestamp():
    try:
        r = requests.get(f"{BASE_URL}/api/v5/public/time")
        return str(int(r.json()['data'][0]['ts']) / 1000)
    except:
        return str(time.time())

def sign(ts, method, path, body=""):
    msg = f"{ts}{method}{path}{body}"
    return hmac.new(API_SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()

def headers(method, path, body=""):
    ts = get_server_timestamp()
    return {
        "OK-ACCESS-KEY": API_KEY,
        "OK-ACCESS-SIGN": sign(ts, method, path, body),
        "OK-ACCESS-TIMESTAMP": ts,
        "OK-ACCESS-PASSPHRASE": API_PASSPHRASE,
        "Content-Type": "application/json"
    }

def send_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text})
    except:
        print("[ERROR] Failed to send Telegram message")

# === API ===
def get_price():
    try:
        path = f"/api/v5/market/ticker?instId={SYMBOL}"
        res = requests.get(BASE_URL + path, headers=headers("GET", path)).json()
        return float(res["data"][0]["last"])
    except Exception as e:
        send_telegram("[ERROR] Failed to get price")
        return None

def get_balance():
    try:
        path = "/api/v5/account/balance?ccy=USDT"
        res = requests.get(BASE_URL + path, headers=headers("GET", path)).json()
        return float(res["data"][0]["details"][0]["availBal"])
    except Exception as e:
        send_telegram(f"[ERROR] Failed to get balance: {str(e)}")
        return 0

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
    try:
        res = requests.post(BASE_URL + path, headers=headers("POST", path, body), data=body).json()
        order_id = res["data"][0]["ordId"]
        price = get_price()
        active_position.update({"side": side, "entry": price, "size": size, "order_id": order_id})
        send_telegram(f"[OPEN] {side.upper()} @ {price:.2f}")
        return True
    except Exception as e:
        send_telegram(f"[เปิดออเดอร์ล้มเหลว] {side.upper()} {str(e)}")
        return False

def close_order():
    if not active_position["order_id"]:
        return
    side = "sell" if active_position["side"] == "buy" else "buy"
    size = active_position["size"]
    entry = active_position["entry"]
    price_close = get_price()
    pnl = (price_close - entry) * size if side == "sell" else (entry - price_close) * size
    place_order(side, size)
    send_telegram(f"[CLOSE] @ {price_close:.2f}\nPnL: {pnl:.2f} USDT")
    active_position.update({"side": None, "entry": None, "size": None, "order_id": None})

# === LOGIC ===
def trade_loop():
    while True:
        try:
            if not bot_active or active_position["order_id"]:
                time.sleep(5)
                continue
            balance = get_balance()
            if balance == 0:
                time.sleep(5)
                continue
            size = round((balance * 0.3 * LEVERAGE) / get_price(), 3)
            side = "buy"
            if place_order(side, size):
                time.sleep(600)
                close_order()
                time.sleep(60)
        except Exception as e:
            send_telegram(f"[ERROR] {str(e)}")
            time.sleep(10)

# === TELEGRAM ===
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    global bot_active
    data = request.json
    if "message" not in data or "text" not in data["message"]:
        return "ignored"

    msg = data["message"]["text"].lower()
    if "stop" in msg:
        bot_active = False
        send_telegram("Bot paused")
    elif "resume" in msg:
        bot_active = True
        send_telegram("Bot resumed")
    elif "status" in msg:
        send_telegram(f"Bot status: {'Active' if bot_active else 'Paused'}\nPosition: {active_position}")
    return "ok"

@app.route("/")
def index():
    return "OKX Bot running"

# === MAIN ===
threading.Thread(target=trade_loop, daemon=True).start()

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
