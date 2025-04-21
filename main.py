import time
import hmac
import json
import hashlib
import requests
import threading
from flask import Flask, request
import os

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
        r = requests.get(f"{BASE_URL}/api/v5/public/time", timeout=5)
        return r.json()["data"][0]["ts"]
    except:
        return str(int(time.time() * 1000))

def sign(ts, method, path, body=""):
    msg = f"{ts}{method}{path}{body}"
    return hmac.new(API_SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()

def headers(method, path, body=""):
    ts = get_server_timestamp()
    return {
        "OK-ACCESS-KEY": API_KEY,
        "OK-ACCESS-SIGN": sign(ts, method, path, body),
        "OK-ACCESS-TIMESTAMP": str(int(ts) / 1000),
        "OK-ACCESS-PASSPHRASE": API_PASSPHRASE,
        "Content-Type": "application/json"
    }

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except Exception as e:
        print(f"[Telegram Error] {e}")

def retry_request(method, url, headers=None, data=None, retries=3):
    for _ in range(retries):
        try:
            if method == "GET":
                r = requests.get(url, headers=headers, timeout=10)
            else:
                r = requests.post(url, headers=headers, data=data, timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"[Retry] {method} {url} failed: {e}")
            time.sleep(2)
    return None

def get_price():
    path = f"/api/v5/market/ticker?instId={SYMBOL}"
    res = retry_request("GET", BASE_URL + path, headers=headers("GET", path))
    return float(res["data"][0]["last"]) if res and "data" in res else None

def get_balance():
    path = "/api/v5/account/balance?ccy=USDT"
    res = retry_request("GET", BASE_URL + path, headers=headers("GET", path))
    if res and "data" in res:
        return float(res["data"][0]["details"][0]["availBal"])
    send_telegram("[ERROR] Failed to get balance")
    return 0

# === ORDER ===
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
    res = retry_request("POST", BASE_URL + path, headers=headers("POST", path, body), data=body)
    if res and "data" in res:
        order_id = res["data"][0]["ordId"]
        price = get_price()
        active_position.update({"side": side, "entry": price, "size": size, "order_id": order_id})
        send_telegram(f"[OPEN] {side.upper()} @ {price:.2f}")
        return order_id
    send_telegram(f"[เปิดออเดอร์ล้มเหลว] {side.upper()} {size}")
    return None

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

# === LOGIC ===
def trade_loop():
    while True:
        try:
            if not bot_active or active_position["order_id"]:
                time.sleep(5)
                continue
            balance = get_balance()
            price = get_price()
            if not price or balance == 0:
                time.sleep(5)
                continue
            size = round((balance * 0.3 * LEVERAGE) / price, 4)
            side = "buy"
            place_order(side, size)
            time.sleep(600)  # ถือ 10 นาที
            close_order()
            time.sleep(60)
        except Exception as e:
            send_telegram(f"[ERROR] Bot crashed: {e}")
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
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
