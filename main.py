# main.py
from flask import Flask
import threading
import time
import requests
import hmac
import base64
import json
import datetime
import hashlib

# === ตั้งค่า API / Telegram ===
OKX_API_KEY = "a279dbed-ae3c-44c2-b0c4-fcf1ff6e76cb"
OKX_API_SECRET = "FA68643E5A176C00AB09637CBC5DA82E"
OKX_API_PASSPHRASE = "Jirawat1-"
TELEGRAM_TOKEN = "7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY"
TELEGRAM_CHAT_ID = "8104629569"

# === ตั้งค่าทั่วไป ===
SYMBOL = "BTC-USDT"
LEVERAGE = 15
POSITION_SIZE_PERCENT = 30
SL_PERCENT = 12
TP_PERCENT = 30
TRAIL_SL_TRIGGER = 10
TRAIL_SL_SET = 2
current_position = None

# === Flask App ===
app = Flask(__name__)

# === Telegram Notify ===
def notify_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"[Telegram Error] {e}")

# === OKX Auth Helper ===
def okx_headers(method, path, body=""):
    timestamp = datetime.datetime.utcnow().isoformat("T", "milliseconds") + "Z"
    msg = f"{timestamp}{method}{path}{body}"
    sign = base64.b64encode(hmac.new(OKX_API_SECRET.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    return {
        "OK-ACCESS-KEY": OKX_API_KEY,
        "OK-ACCESS-SIGN": sign,
        "OK-ACCESS-TIMESTAMP": timestamp,
        "OK-ACCESS-PASSPHRASE": OKX_PASSPHRASE,
        "Content-Type": "application/json"
    }

# === Fetch Market Price ===
def get_okx_price():
    url = f"https://www.okx.com/api/v5/market/ticker?instId={SYMBOL}"
    try:
        r = requests.get(url)
        price = float(r.json()['data'][0]['last'])
        return price
    except Exception as e:
        notify_telegram(f"[ERROR] ดึงราคาจาก OKX ไม่สำเร็จ: {e}")
        return None

# === Fetch Balance USDT ===
def get_balance():
    url = "/api/v5/account/balance"
    headers = okx_headers("GET", url)
    r = requests.get("https://www.okx.com" + url, headers=headers)
    try:
        data = r.json()
        for asset in data['data'][0]['details']:
            if asset['ccy'] == 'USDT':
                return float(asset['availBal'])
    except:
        notify_telegram(f"[ERROR] ดึง balance ไม่ได้: {r.text}")
    return 0

# === Place Market Order ===
def place_order(side, size):
    url = "/api/v5/trade/order"
    path = "https://www.okx.com" + url
    body = {
        "instId": SYMBOL,
        "tdMode": "cross",
        "side": side,
        "ordType": "market",
        "sz": str(size),
        "lever": str(LEVERAGE),
        "posSide": "long" if side == "buy" else "short"
    }
    body_json = json.dumps(body)
    headers = okx_headers("POST", url, body_json)
    r = requests.post(path, headers=headers, data=body_json)
    try:
        resp = r.json()
        if resp['code'] == '0':
            notify_telegram(f"เปิดออเดอร์ {side.upper()} สำเร็จ\nจำนวน: {size}")
            return True
        else:
            notify_telegram(f"[ERROR] เปิดออเดอร์ไม่สำเร็จ: {resp['msg']}")
    except:
        notify_telegram("[ERROR] ไม่สามารถเปิดออเดอร์ได้")
    return False

# === Simulate CHoCH (placeholder) ===
def detect_choch():
    # TODO: เขียนวิเคราะห์ CHoCH จริงในภายหลัง
    return True  # ให้เจอ CHoCH ตลอดเพื่อเทสต์

# === Simulate Fibo zone ===
def is_in_fibo_zone(price, high, low):
    fib_618 = high - (high - low) * 0.618
    fib_786 = high - (high - low) * 0.786
    return fib_786 <= price <= fib_618

# === Main Bot Logic ===
def trading_bot():
    global current_position
    notify_telegram("บอทเริ่มทำงานแล้ว!")
    high = low = None

    while True:
        price = get_okx_price()
        if not price:
            time.sleep(30)
            continue

        print(f"[INFO] BTC/USDT = {price}")

        if not current_position:
            if detect_choch():
                notify_telegram(f"พบ CHoCH ที่ราคา {price}")
                high = price * 1.01
                low = price * 0.99

            if high and low and is_in_fibo_zone(price, high, low):
                notify_telegram(f"ราคาเข้าโซน Fibonacci: {price}")
                balance = get_balance()
                if balance:
                    qty = (balance * POSITION_SIZE_PERCENT / 100) * LEVERAGE / price
                    if place_order("buy", round(qty, 3)):
                        current_position = {"entry": price, "side": "buy"}
        else:
            # กำไร/ขาดทุน
            entry = current_position["entry"]
            pnl_percent = ((price - entry) / entry) * 100 if current_position["side"] == "buy" else ((entry - price) / entry) * 100

            # TP
            if pnl_percent >= TP_PERCENT:
                notify_telegram(f"ถึงเป้า TP: {pnl_percent:.2f}% — ปิดออเดอร์")
                current_position = None

            # SL
            elif pnl_percent <= -SL_PERCENT:
                notify_telegram(f"โดน SL: {pnl_percent:.2f}% — ปิดออเดอร์")
                current_position = None

            # Trailing SL
            elif pnl_percent >= TRAIL_SL_TRIGGER:
                notify_telegram(f"เลื่อน SL: ล็อคกำไร {TRAIL_SL_SET}%")
                # NOTE: ยังไม่ส่งคำสั่งปรับ SL จริง (สามารถเพิ่มได้ภายหลัง)

        time.sleep(60)

# === Flask Route ===
@app.route('/')
def index():
    return "OKX Futures Bot is running."

# === Run ===
if __name__ == '__main__':
    threading.Thread(target=trading_bot).start()
    app.run(host="0.0.0.0", port=10000)
