from flask import Flask
import threading
import requests
import time
import hmac
import hashlib
import base64
import uuid
import json
import datetime
import os

# === CONFIG ===
OKX_API_KEY = "a279dbed-ae3c-44c2-b0c4-fcf1ff6e76cb"
OKX_API_SECRET = "FA68643E5A176C00AB09637CBC5DA82E"
OKX_API_PASSPHRASE = "Jirawat1-"
TELEGRAM_TOKEN = "7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY"
TELEGRAM_CHAT_ID = "8104629569"
SYMBOL = "BTC-USDT"
LEVERAGE = 15
TRADE_PERCENT = 0.3
TP_PERCENT = 0.30
SL_PERCENT = -0.12
TRAIL_SL_PROFIT = 0.10
TRAIL_SL_MOVE = 0.02

app = Flask(__name__)
active_order_id = None

def notify_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except:
        pass

def okx_headers(method, path, body=""):
    now = datetime.datetime.utcnow().isoformat("T", "milliseconds") + "Z"
    prehash = f"{now}{method.upper()}{path}{body}"
    sign = hmac.new(OKX_API_SECRET.encode(), prehash.encode(), hashlib.sha256).digest()
    sign_b64 = base64.b64encode(sign).decode()

    return {
        "OK-ACCESS-KEY": OKX_API_KEY,
        "OK-ACCESS-SIGN": sign_b64,
        "OK-ACCESS-TIMESTAMP": now,
        "OK-ACCESS-PASSPHRASE": OKX_API_PASSPHRASE,
        "Content-Type": "application/json"
    }

def get_latest_price():
    try:
        res = requests.get(f"https://www.okx.com/api/v5/market/ticker?instId={SYMBOL}")
        data = res.json()
        return float(data["data"][0]["last"])
    except Exception as e:
        notify_telegram(f"[ERROR] ไม่สามารถดึงราคาจาก OKX ได้: {e}")
        return None

def get_balance():
    url = "/api/v5/account/balance"
    headers = okx_headers("GET", url)
    res = requests.get(f"https://www.okx.com{url}", headers=headers)
    data = res.json()
    for acc in data["data"][0]["details"]:
        if acc["ccy"] == "USDT":
            return float(acc["cashBal"])
    return 0

def set_leverage():
    url = "/api/v5/account/set-leverage"
    payload = {
        "instId": SYMBOL,
        "lever": str(LEVERAGE),
        "mgnMode": "cross"
    }
    headers = okx_headers("POST", url, json.dumps(payload))
    requests.post(f"https://www.okx.com{url}", headers=headers, json=payload)

def place_order(side, size):
    global active_order_id
    url = "/api/v5/trade/order"
    order_id = str(uuid.uuid4())
    payload = {
        "instId": SYMBOL,
        "tdMode": "cross",
        "clOrdId": order_id,
        "side": side,
        "ordType": "market",
        "sz": str(size)
    }
    headers = okx_headers("POST", url, json.dumps(payload))
    res = requests.post(f"https://www.okx.com{url}", headers=headers, json=payload)
    result = res.json()
    if result.get("code") == "0":
        active_order_id = order_id
        notify_telegram(f"[ORDER] เปิดออเดอร์ {side.upper()} {size} BTC สำเร็จ")
    else:
        notify_telegram(f"[ERROR] ไม่สามารถเปิดออเดอร์ได้:\n{result}")

def check_position():
    url = f"/api/v5/account/positions?instId={SYMBOL}"
    headers = okx_headers("GET", url)
    res = requests.get(f"https://www.okx.com{url}", headers=headers)
    data = res.json()
    if data["data"]:
        pos = data["data"][0]
        return float(pos["pos"]), pos["side"]
    return 0, None

def cancel_all_orders():
    url = "/api/v5/trade/cancel-all-orders"
    payload = [{"instId": SYMBOL}]
    headers = okx_headers("POST", url, json.dumps(payload))
    requests.post(f"https://www.okx.com{url}", headers=headers, json=payload)

def analyze_and_trade():
    global active_order_id

    notify_telegram("บอทเริ่มทำงานแล้ว!")

    set_leverage()

    while True:
        try:
            price = get_latest_price()
            if not price:
                time.sleep(15)
                continue

            balance = get_balance()
            qty = round((balance * TRADE_PERCENT * LEVERAGE) / price, 3)

            pos_size, pos_side = check_position()

            if pos_size == 0:
                # == ตรงนี้คือจุดเข้า == (ตัวอย่าง: เข้าเมื่อราคาลดลงมาเร็ว)
                if price < 80000:  # ตัวอย่าง logic แทน CHoCH + Fibo
                    place_order("buy", qty)

            else:
                # == ตรงนี้คือ TP / SL ==
                entry_price = price  # ควรดึงจาก position จริง
                pnl = ((price - entry_price) / entry_price) if pos_side == "long" else ((entry_price - price) / entry_price)

                if pnl >= TP_PERCENT:
                    notify_telegram("[TP] ปิดกำไร +30%")
                    cancel_all_orders()
                elif pnl <= SL_PERCENT:
                    notify_telegram("[SL] Stop loss -12%")
                    cancel_all_orders()
                elif pnl >= TRAIL_SL_PROFIT:
                    notify_telegram("[TRAIL SL] กำไรถึง +10% เลื่อน SL เป็น +2%")
                    # เพิ่ม Trailing SL Logic ตรงนี้

        except Exception as e:
            notify_telegram(f"[ERROR] run_bot: {e}")

        time.sleep(30)

@app.route('/')
def index():
    return "OKX Futures Bot is running!"

if __name__ == '__main__':
    bot_thread = threading.Thread(target=analyze_and_trade)
    bot_thread.daemon = True
    bot_thread.start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
