import time
import json
import hmac
import hashlib
import requests
import threading
from datetime import datetime
from flask import Flask, request

# ===== CONFIG =====
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

# ===== UTIL =====
def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text})

def sign(ts, method, path, body=""):
    msg = f"{ts}{method}{path}{body}"
    return hmac.new(API_SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()

def headers(method, path, body=""):
    ts = str(time.time())
    return {
        "OK-ACCESS-KEY": API_KEY,
        "OK-ACCESS-SIGN": sign(ts, method, path, body),
        "OK-ACCESS-TIMESTAMP": ts,
        "OK-ACCESS-PASSPHRASE": API_PASSPHRASE,
        "Content-Type": "application/json"
    }

def get_price():
    path = f"/api/v5/market/ticker?instId={SYMBOL}"
    res = requests.get(BASE_URL + path, headers=headers("GET", path)).json()
    return float(res["data"][0]["last"])

def get_balance():
    path = "/api/v5/account/balance?ccy=USDT"
    res = requests.get(BASE_URL + path, headers=headers("GET", path)).json()
    return float(res["data"][0]["details"][0]["availBal"])

# ===== ORDER =====
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
    res = requests.post(BASE_URL + path, headers=headers("POST", path, body), data=body).json()
    order_id = res["data"][0]["ordId"]
    price = get_price()
    active_position.update({"side": side, "entry": price, "size": size, "order_id": order_id})
    send_telegram(f"[OPEN] {side.upper()} @ {price:.2f}")
    return res

def close_order():
    if not active_position["order_id"]:
        return
    side = "sell" if active_position["side"] == "buy" else "buy"
    size = active_position["size"]
    price_open = active_position["entry"]
    price_close = get_price()
    pnl = (price_close - price_open) * size if side == "sell" else (price_open - price_close) * size
    place_order(side, size)
    send_telegram(f"[CLOSE] @ {price_close:.2f}\nPnL: {pnl:.2f} USDT")
    active_position.update({"side": None, "entry": None, "size": None, "order_id": None})

# ===== LOGIC =====
def trade_loop():
    while True:
        if not bot_active or active_position["order_id"]:
            time.sleep(10)
            continue
        balance = get_balance()
        size = round((balance * 0.1 * LEVERAGE) / get_price(), 4)
        side = "buy"
        place_order(side, size)
        time.sleep(600)  # ถือ 10 นาที
        close_order()
        time.sleep(60)

# ===== TELEGRAM =====
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    global bot_active
    msg = request.json["message"]["text"].lower()
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

# ===== MAIN =====
threading.Thread(target=trade_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
