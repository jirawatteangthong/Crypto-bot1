from flask import Flask
import threading
import time
import requests
import os
import hmac
import hashlib
import base64
import json
import datetime

# === ตั้งค่า OKX API ===
OKX_API_KEY = 'a279dbed-ae3c-44c2-b0c4-fcf1ff6e76cb'
OKX_SECRET_KEY = 'FA68643E5A176C00AB09637CBC5DA82E'
OKX_PASSPHRASE = 'Jirawat1-'

# === Telegram ===
TELEGRAM_TOKEN = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
TELEGRAM_CHAT_ID = '8104629569'

# === สัญลักษณ์ที่เทรด ===
SYMBOL = 'BTC-USDT-SWAP'

# === Flask App ===
app = Flask(__name__)

def notify_telegram(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"[ERROR] Telegram: {e}")

# === สร้าง signature ===
def generate_signature(timestamp, method, request_path, body):
    if not body:
        body = ""
    message = f"{timestamp}{method.upper()}{request_path}{body}"
    mac = hmac.new(OKX_SECRET_KEY.encode(), msg=message.encode(), digestmod=hashlib.sha256)
    return base64.b64encode(mac.digest()).decode()

# === ดึงราคาล่าสุดจาก OKX ===
def get_price():
    url = 'https://www.okx.com/api/v5/market/ticker?instId=' + SYMBOL
    try:
        response = requests.get(url)
        data = response.json()
        return float(data['data'][0]['last'])
    except Exception as e:
        notify_telegram(f"[ERROR] ดึงราคาล้มเหลว: {e}")
        return None

# === ส่งคำสั่งเทรด ===
def send_order(side, size):
    url = 'https://www.okx.com/api/v5/trade/order'
    timestamp = datetime.datetime.utcnow().isoformat("T", "milliseconds") + "Z"
    body = json.dumps({
        "instId": SYMBOL,
        "tdMode": "cross",
        "side": side,
        "ordType": "market",
        "sz": str(size)
    })

    headers = {
        'OK-ACCESS-KEY': OKX_API_KEY,
        'OK-ACCESS-SIGN': generate_signature(timestamp, 'POST', '/api/v5/trade/order', body),
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': OKX_PASSPHRASE,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, data=body)
        res = response.json()
        notify_telegram(f"[TRADE] สั่ง {side.upper()} OKX: {res}")
    except Exception as e:
        notify_telegram(f"[ERROR] ส่งคำสั่งเทรดล้มเหลว: {e}")

# === ฟังก์ชันหลักบอท ===
def trading_bot():
    notify_telegram("บอท OKX เริ่มทำงานแล้ว!")

    while True:
        price = get_price()
        if price:
            print(f"[INFO] ราคาล่าสุด {SYMBOL}: {price}")
            # TODO: เพิ่ม logic กลยุทธ์ M15 CHoCH + Fibo + M5 CHoCH ที่นี่
            # เช่น ตรวจแนวโน้มจากแท่งเทียน → วัด Fibonacci → หาสัญญาณ CHoCH จาก M5
            # ถ้าพบสัญญาณ: send_order('buy' หรือ 'sell', size)

        else:
            print("[ERROR] ดึงราคาไม่ได้")

        time.sleep(30)

@app.route('/')
def home():
    return "OKX Crypto Bot is running!"

if __name__ == '__main__':
    # รัน Background Bot Thread
    bot_thread = threading.Thread(target=trading_bot)
    bot_thread.start()

    # รัน Flask ให้ Render รู้ว่าบอทยังทำงานอยู่
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
