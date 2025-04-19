 from flask import Flask
import threading
import time
import os
import requests
import hmac
import hashlib
import json
from datetime import datetime

app = Flask(__name__)

# ========== CONFIG ==========
API_KEY = 'EmgLSyDgCyWym11Xcjq8tLeDaWuszl8n3PsOw9SYypVqlCHulrKxvRxNctCq121X'
API_SECRET = '2jqYRrjyO8RTOOHT5yKNdtHuFNmS0OcRmOrB7Tj9wDnRaTjwspCxfkPxqJUL3GOJ'
TELEGRAM_TOKEN = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
TELEGRAM_CHAT_ID = '8104629569'

symbol = 'BTCUSDT'
leverage = 15
trade_percent = 0.3  # 30%
base_url = 'https://fapi.binance.com'

headers = {
    'X-MBX-APIKEY': API_KEY
}

# ========== UTIL ==========
def notify_telegram(msg):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': msg}
    try:
        requests.post(url, data=data)
    except:
        pass

def get_price():
    url = f'{base_url}/fapi/v1/ticker/price?symbol={symbol}'
    r = requests.get(url)
    return float(r.json()['price'])

def sign_request(params):
    query = '&'.join([f"{key}={params[key]}" for key in params])
    signature = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    return f"{query}&signature={signature}"

def get_balance():
    url = f'{base_url}/fapi/v2/balance'
    r = requests.get(url, headers=headers)
    for b in r.json():
        if b['asset'] == 'USDT':
            return float(b['availableBalance'])
    return 0

def set_leverage():
    url = f'{base_url}/fapi/v1/leverage'
    data = {'symbol': symbol, 'leverage': leverage}
    r = requests.post(url, headers=headers, params=data)

def place_order(side, quantity, entry_price):
    url = f'{base_url}/fapi/v1/order'
    tp_price = round(entry_price * 1.3, 2) if side == 'BUY' else round(entry_price * 0.7, 2)
    sl_price = round(entry_price * 0.88, 2) if side == 'BUY' else round(entry_price * 1.12, 2)

    # ส่งคำสั่ง Market
    data = {
        'symbol': symbol,
        'side': side,
        'type': 'MARKET',
        'quantity': quantity,
        'timestamp': int(time.time() * 1000)
    }
    signed = sign_request(data)
    r = requests.post(f'{base_url}/fapi/v1/order?{signed}', headers=headers)

    # ส่ง TP/SL
    stop_side = 'SELL' if side == 'BUY' else 'BUY'
    tp = {
        'symbol': symbol,
        'side': stop_side,
        'type': 'TAKE_PROFIT_MARKET',
        'stopPrice': tp_price,
        'closePosition': True,
        'timeInForce': 'GTC',
        'timestamp': int(time.time() * 1000)
    }
    sl = {
        'symbol': symbol,
        'side': stop_side,
        'type': 'STOP_MARKET',
        'stopPrice': sl_price,
        'closePosition': True,
        'timeInForce': 'GTC',
        'timestamp': int(time.time() * 1000)
    }
    requests.post(f'{base_url}/fapi/v1/order?{sign_request(tp)}', headers=headers)
    requests.post(f'{base_url}/fapi/v1/order?{sign_request(sl)}', headers=headers)

    notify_telegram(f"เปิดออเดอร์ {side}\nราคา: {entry_price}\nTP: {tp_price}\nSL: {sl_price}")

# ========== STRATEGY ==========
def check_trade_condition():
    # NOTE: ตัวอย่างนี้เป็นแค่ MOCK — ต้องแทนที่ด้วยการวิเคราะห์จริงจากแท่งเทียน M15 และ M5
    price = get_price()
    now = datetime.utcnow().minute
    if now % 15 == 0:  # แกล้งให้เปิดทุก 15 นาทีเพื่อทดสอบ
        return {
            'side': 'BUY' if int(price) % 2 == 0 else 'SELL',
            'entry_price': price
        }
    return None

# ========== MAIN BOT ==========
def run_bot():
    notify_telegram("บอทเริ่มทำงานแล้ว")
    set_leverage()
    while True:
        try:
            signal = check_trade_condition()
            if signal:
                balance = get_balance()
                entry_price = signal['entry_price']
                qty = round((balance * trade_percent * leverage) / entry_price, 3)
                place_order(signal['side'], qty, entry_price)
                time.sleep(3600)  # พัก 1 ชม. หลังเทรด
            else:
                print("ไม่มีสัญญาณเทรด...")
        except Exception as e:
            notify_telegram(f"Error: {str(e)}")
        time.sleep(60)

# ========== FLASK ==========
@app.route('/')
def home():
    return "Crypto Bot is running!"

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
