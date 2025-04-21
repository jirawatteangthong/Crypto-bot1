import time
import json
import hmac
import hashlib
import requests
import threading
from datetime import datetime
from flask import Flask, request
import os

# === CONFIG ===
API_KEY = "e5a0da48-989e-4897-b637-d3475020fd70"
API_SECRET = "81AF116E5773A7B094DF03844731E342"
API_PASSPHRASE = "Jirawat1-"
TELEGRAM_TOKEN = "7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY"
TELEGRAM_CHAT_ID = "8104629569"
BASE_URL = "https://www.okx.com"
SYMBOL = "BTC-USDT-SWAP"
LEVERAGE = 10

app = Flask(__name__)
bot_active = True
active_position = {"side": None, "entry": None, "size": None, "order_id": None}

# === UTILS ===
def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text})
    except Exception as e:
        print("Telegram Error:", e)

def okx_timestamp():
    r = requests.get("https://www.okx.com/api/v5/public/time")
    return r.json()["data"][0]["ts"]

def sign(ts, method, path, body=""):
    msg = f"{ts}{method}{path}{body}"
    return hmac.new(API_SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()

def headers(method, path, body=""):
    ts = str(int(okx_timestamp()))
    return {
        "OK-ACCESS-KEY": API_KEY,
        "OK-ACCESS-SIGN": sign(ts, method, path, body),
        "OK-ACCESS-TIMESTAMP": ts,
        "OK-ACCESS-PASSPHRASE": API_PASSPHRASE,
        "Content-Type": "application/json"
    }

def get_price():
    try:
        path = f"/api/v5/market/ticker?instId={SYMBOL}"
        res = requests.get(BASE_URL + path, headers=headers("GET", path)).json()
        if "data" in res and res["data"]:
            return float(res["data"][0]["last"])
        else:
            send_telegram(f"[ERROR] Failed to get price: {res}")
            return None
    except Exception as e:
        send_telegram(f"[ERROR] Exception in get_price(): {e}")
        return None

def get_balance():
    try:
        path = "/api/v5/account/balance?ccy=USDT"
        res = requests.get(BASE_URL + path, headers=headers("GET", path)).json()
        if "data" in res and res["data"]:
            return float(res["data"][0]["details"][0]["availBal"])
        else:
            send_telegram(f"[ERROR] Failed to get balance: {res}")
            return 0
    except Exception as e:
        send_telegram(f"[ERROR] Exception in get_balance(): {e}")
        return 0

# === ORDER FUNCTIONS ===
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
    r = requests.post(BASE_URL + path, headers=headers("POST", path, body), data=body)
    result = r.json()
    order_id = result["data"][0]["ordId"]
    entry_price = get_price()
    active_position.update({"side": side, "entry": entry_price, "size": size, "order_id": order_id})
    send_telegram(f"[OPEN] {side.upper()} @ {entry_price:.2f}")
    return result

def close_order():
    if not active_position["order_id"]:
        return
    side = "buy" if active_position["side"] == "sell" else "sell"
    size = active_position["size"]
    entry = active_position["entry"]
    exit_price = get_price()
    pnl = (exit_price - entry) * size if side == "sell" else (entry - exit_price) * size
    place_order(side, size)
    send_telegram(f"[CLOSE] @ {exit_price:.2f}\nPnL: {pnl:.2f} USDT")
    active_position.update({"side": None, "entry": None, "size": None, "order_id": None})

# === TRADE LOGIC ===
def trade_loop():
    while True:
        try:
            if not bot_active or active_position["order_id"]:
                time.sleep(10)
                continue

            balance = get_balance()
            price = get_price()
            size = round((balance * 0.3 * LEVERAGE) / price, 4)
            side = "buy"
            place_order(side, size)
            time.sleep(600)  # ถือ 10 นาที
            close_order()
            time.sleep(60)
        except Exception as e:
            send_telegram(f"[ERROR] {e}")
            time.sleep(30)

# === TELEGRAM WEBHOOK ===
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
        status = f"Bot status: {'Active' if bot_active else 'Paused'}\nPosition: {active_position}"
        send_telegram(status)
    return "ok"

@app.route("/")
def index():
    return "OKX Bot Running"

# === START ===
threading.Thread(target=trade_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
