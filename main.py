 from flask import Flask
import threading
import time
import requests
import datetime
import os

app = Flask(__name__)

# ====== ตั้งค่าพื้นฐาน ======
API_KEY = 'EmgLSyDgCyWym11Xcjq8tLeDaWuszl8n3PsOw9SYypVqlCHulrKxvRxNctCq121X'
API_SECRET = '2jqYRrjyO8RTOOHT5yKNdtHuFNmS0OcRmOrB7Tj9wDnRaTjwspCxfkPxqJUL3GOJ'

TELEGRAM_TOKEN = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
TELEGRAM_CHAT_ID = '8104629569'

symbol = 'BTCUSDT'
interval = '15m'
base_url = 'https://fapi.binance.com'

headers = {
    'X-MBX-APIKEY': API_KEY
}


# ====== ส่งข้อความไป Telegram ======
def notify_telegram(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    try:
        requests.post(url, data=data)
    except:
        pass


# ====== โหลดกราฟ M15 ======
def fetch_klines(symbol="BTCUSDT", interval="15m", limit=100):
    url = f'https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}'
    response = requests.get(url)
    data = response.json()
    klines = []
    for k in data:
        klines.append({
            "time": datetime.datetime.fromtimestamp(k[0] / 1000),
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4])
        })
    return klines


# ====== วิเคราะห์ CHoCH และหา Fibonacci ======
def find_choch_and_fib():
    candles = fetch_klines()
    last = candles[-1]
    prev = candles[-2]

    if last['high'] > prev['high'] and last['low'] > prev['low']:
        trend = "up"
        fib_low = min([c['low'] for c in candles[-10:]])
        fib_high = max([c['high'] for c in candles[-10:]])
        fib_618 = fib_high - (fib_high - fib_low) * 0.618
        fib_786 = fib_high - (fib_high - fib_low) * 0.786

        notify_telegram(f"พบสัญญาณขาขึ้น (CHoCH)\nFibo Buy Zone: {round(fib_786,2)} - {round(fib_618,2)}")
        return "buy", fib_786, fib_618

    elif last['low'] < prev['low'] and last['high'] < prev['high']:
        trend = "down"
        fib_high = max([c['high'] for c in candles[-10:]])
        fib_low = min([c['low'] for c in candles[-10:]])
        fib_618 = fib_low + (fib_high - fib_low) * 0.618
        fib_786 = fib_low + (fib_high - fib_low) * 0.786

        notify_telegram(f"พบสัญญาณขาลง (CHoCH)\nFibo Sell Zone: {round(fib_618,2)} - {round(fib_786,2)}")
        return "sell", fib_618, fib_786

    return None, None, None


# ====== รันบอทใน Background ======
def run_bot():
    notify_telegram("บอทเริ่มทำงานแล้ว!")
    while True:
        side, fib1, fib2 = find_choch_and_fib()
        # (ยังไม่เปิดออเดอร์จริงในขั้นตอนนี้)
        time.sleep(300)  # วิเคราะห์ทุก 5 นาที


# ====== หน้าเว็บหลัก ======
@app.route('/')
def home():
    return 'Crypto Bot is running!'


# ====== Main ======
if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
