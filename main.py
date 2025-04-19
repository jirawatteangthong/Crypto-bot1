from flask import Flask
import threading
import time
import hmac
import hashlib
import base64
import requests
import datetime
import json
import os

# ====== CONFIG ======
SYMBOL = "BTC-USDT"
TELEGRAM_TOKEN = "7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY"
TELEGRAM_CHAT_ID = "8104629569"
OKX_API_KEY = "a279dbed-ae3c-44c2-b0c4-fcf1ff6e76cb"
OKX_SECRET_KEY = "FA68643E5A176C00AB09637CBC5DA82E"
OKX_PASSPHRASE = "Jirawat1-"
POSITION_SIZE_PERCENT = 0.3  # 30% of balance
LEVERAGE = 15
TIMEFRAME_MAIN = "15m"
TIMEFRAME_ENTRY = "5m"
SL_PERCENT = 12
TP_PERCENT = 30
MOVE_SL_AT_PROFIT = 10
MOVE_SL_TO = 2

# ====== FLASK SETUP ======
app = Flask(__name__)

# ====== TELEGRAM ======
def telegram_notify(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

# ====== OKX AUTH ======
def get_timestamp():
    return datetime.datetime.utcnow().isoformat("T", "milliseconds") + "Z"

def sign(message, secret_key):
    return base64.b64encode(hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).digest())

def okx_headers(method, path, body=""):
    timestamp = get_timestamp()
    msg = f"{timestamp}{method}{path}{body}"
    signature = sign(msg, OKX_SECRET_KEY)
    return {
        "OK-ACCESS-KEY": OKX_API_KEY,
        "OK-ACCESS-SIGN": signature.decode(),
        "OK-ACCESS-TIMESTAMP": timestamp,
        "OK-ACCESS-PASSPHRASE": OKX_PASSPHRASE,
        "Content-Type": "application/json"
    }

# ====== PRICE & BALANCE ======
def get_price():
    try:
        r = requests.get(f"https://www.okx.com/api/v5/market/ticker?instId={SYMBOL}")
        price = float(r.json()['data'][0]['last'])
        return price
    except Exception as e:
        telegram_notify(f"[ERROR] ดึงราคาไม่สำเร็จ: {e}")
        return None

def get_balance():
    try:
        headers = okx_headers("GET", "/api/v5/account/balance")
        r = requests.get("https://www.okx.com/api/v5/account/balance", headers=headers)
        data = r.json()
        for item in data['data'][0]['details']:
            if item['ccy'] == "USDT":
                return float(item['availBal'])
        return 0
    except:
        return 0

# ====== PLACE ORDER ======
def place_order(side, price):
    try:
        balance = get_balance()
        amount = (balance * POSITION_SIZE_PERCENT * LEVERAGE) / price
        order = {
            "instId": SYMBOL,
            "tdMode": "cross",
            "side": side,
            "ordType": "market",
            "sz": str(round(amount, 3)),
            "posSide": "long" if side == "buy" else "short"
        }
        headers = okx_headers("POST", "/api/v5/trade/order", json.dumps(order))
        r = requests.post("https://www.okx.com/api/v5/trade/order", headers=headers, data=json.dumps(order))
        telegram_notify(f"ส่งออเดอร์ {side.upper()} เรียบร้อยแล้ว\nราคา: {price}")
        return r.json()
    except Exception as e:
        telegram_notify(f"[ERROR] ส่งออเดอร์ล้มเหลว: {e}")

# ====== SIMULATED STRATEGY LOGIC ======
def is_choch_detected():
    # สำหรับตอนนี้จำลองการเจอ CHoCH
    return True

def is_fibo_zone_hit():
    # จำลองการเข้าโซน Fibonacci 61.8 - 78.6
    return True

def run_strategy():
    telegram_notify("บอทเริ่มทำงานแล้ว!")

    while True:
        try:
            price = get_price()
            if not price:
                time.sleep(10)
                continue

            # --- Step 1: วิเคราะห์ TF M15 ว่ามี CHoCH หรือไม่
            if is_choch_detected():
                # --- Step 2: วัด Fibonacci แล้วรอให้ราคาย่อลงมาโซน 61.8-78.6
                if is_fibo_zone_hit():
                    # --- Step 3: ย่อกราฟไป TF M5 หาจังหวะ CHoCH แล้วเข้าออเดอร์
                    if is_choch_detected():
                        # จำลองเปิดออเดอร์ Buy (หรือ Sell ตามเงื่อนไขจริง)
                        place_order("buy", price)
        except Exception as e:
            telegram_notify(f"[ERROR] Strategy error: {e}")
        time.sleep(60)

@app.route('/')
def home():
    return "Crypto Bot is running!"

if __name__ == '__main__':
    # run strategy in background
    t = threading.Thread(target=run_strategy)
    t.start()

    # start Flask server for Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
