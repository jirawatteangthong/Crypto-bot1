from flask import Flask
import threading
import time
import requests
import os

# === ตั้งค่า Telegram ===
TELEGRAM_TOKEN = "7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY"
TELEGRAM_CHAT_ID = "8104629569"

# === ตั้งค่า Binance Futures ===
SYMBOL = "BTCUSDT"

# === Flask App ===
app = Flask(__name__)

def notify_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, data=payload)
    except Exception as e:
        print(f"[ERROR] ไม่สามารถแจ้ง Telegram ได้: {e}")
def get_price(symbol):
    url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}"
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)

        print(f"[DEBUG] HTTP Status Code: {response.status_code}")
        print(f"[DEBUG] Raw Response Text: {response.text}")

        data = response.json()

        price_str = data.get('price')
        if price_str is not None:
            return float(price_str)
        else:
            notify_telegram(f"[ERROR] ไม่พบราคาจาก Binance: {data}")
            return None

    except Exception as e:
        notify_telegram(f"[ERROR] ดึงราคาไม่สำเร็จ:\n{str(e)}")
        return None
def get_price(symbol, retries=3):
    url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"[WARN] Attempt {attempt+1}: Status Code {response.status_code}")
                time.sleep(1)
                continue

            data = response.json()
            price_str = data.get('price')

            if price_str is not None:
                return float(price_str)
            else:
                notify_telegram(f"[ERROR] ไม่พบราคาจาก Binance: {data}")
                return None
        except Exception as e:
            print(f"[ERROR] Attempt {attempt+1}: {e}")
            time.sleep(1)

    notify_telegram("[ERROR] ดึงราคาไม่สำเร็จหลังจากพยายามหลายครั้ง")
    return None
def home():
    return "Crypto Bot is running!"

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
