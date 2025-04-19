from flask import Flask
import threading
import requests
import time
import hmac, hashlib
import json
import time
import urllib.parse

app = Flask(__name__)

# ========== CONFIG ==========
API_KEY = 'EmgLSyDgCyWym11Xcjq8tLeDaWuszl8n3PsOw9SYypVqlCHulrKxvRxNctCq121X'
API_SECRET = '2jqYRrjyO8RTOOHT5yKNdtHuFNmS0OcRmOrB7Tj9wDnRaTjwspCxfkPxqJUL3GOJ'
TELEGRAM_TOKEN = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
TELEGRAM_CHAT_ID = '8104629569'

symbol = 'BTCUSDT'
leverage = 15
risk_percent = 30  # % ต่อไม้
SL_PERCENT = 12
TP_PERCENT = 30

base_url = 'https://fapi.binance.com'
headers = {'X-MBX-APIKEY': API_KEY}


# ========== UTILITIES ==========
def notify_telegram(msg):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': msg}
    try:
        requests.post(url, data=data)
    except:
        pass

def get_timestamp():
    return int(time.time() * 1000)

def sign(params):
    query_string = urllib.parse.urlencode(params)
    signature = hmac.new(API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    return signature

def get_price():
    url = f"{base_url}/fapi/v1/ticker/price?symbol={symbol}"
    res = requests.get(url)
    return float(res.json()['price'])

def get_balance():
    url = f"{base_url}/fapi/v2/account"
    params = {'timestamp': get_timestamp()}
    params['signature'] = sign(params)
    res = requests.get(url, headers=headers, params=params)
    assets = res.json().get("assets", [])
    for asset in assets:
        if asset['asset'] == 'USDT':
            return float(asset['availableBalance'])
    return 0

def open_order(side, qty, entry_price):
    url = f"{base_url}/fapi/v1/order"
    sl_price = entry_price * (1 - SL_PERCENT/100) if side == "BUY" else entry_price * (1 + SL_PERCENT/100)
    tp_price = entry_price * (1 + TP_PERCENT/100) if side == "BUY" else entry_price * (1 - TP_PERCENT/100)

    params = {
        'symbol': symbol,
        'side': side,
        'type': 'MARKET',
        'quantity': round(qty, 3),
        'timestamp': get_timestamp()
    }
    params['signature'] = sign(params)
    r = requests.post(url, headers=headers, params=params)
    notify_telegram(f"{side} Order Executed: {qty} BTC at ${entry_price:.2f}")
    notify_telegram(f"TP: {tp_price:.2f}, SL: {sl_price:.2f}")
    return r.json()

def set_leverage():
    url = f"{base_url}/fapi/v1/leverage"
    params = {
        'symbol': symbol,
        'leverage': leverage,
        'timestamp': get_timestamp()
    }
    params['signature'] = sign(params)
    requests.post(url, headers=headers, params=params)

# ========== MAIN TRADING LOGIC ==========
def trade_bot():
    set_leverage()
    notify_telegram("บอทเทรดเริ่มทำงานแล้ว!")
    while True:
        try:
            # ดึงราคาปัจจุบัน
            price = get_price()
            balance = get_balance()
            usdt_risk = (balance * risk_percent) / 100
            qty = round(usdt_risk * leverage / price, 3)

            # ----------- ตัวอย่างจำลองการเข้าเทรด -------------
            if int(time.time()) % 120 == 0:  # สมมุติเข้าเทรดทุก 2 นาที (เปลี่ยนเป็น logic จริงได้)
                side = "BUY" if int(time.time()) % 4 == 0 else "SELL"
                open_order(side, qty, price)

            time.sleep(10)
        except Exception as e:
            notify_telegram(f"ERROR: {str(e)}")
            time.sleep(30)

# ========== FLASK ==========
@app.route('/')
def home():
    return "Crypto Bot is running!"

if __name__ == '__main__':
    bot_thread = threading.Thread(target=trade_bot)
    bot_thread.start()
    app.run(host='0.0.0.0', port=10000)
