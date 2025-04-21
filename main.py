# main.py

import time
import hmac
import hashlib
import base64
import json
import requests
import traceback
from flask import Flask, request
from threading import Thread

# ========== CONFIG ==========
API_KEY = 'a279dbed-ae3c-44c2-b0c4-fcf1ff6e76cb'
API_SECRET = 'FA68643E5A176C00AB09637CBC5DA82E'
API_PASSPHRASE = 'Jirawat1-'
BASE_URL = 'https://www.okx.com'
SYMBOL = 'BTC-USDT-SWAP'
LEVERAGE = 10
CAPITAL_USAGE = 0.3  # 30%
TELEGRAM_TOKEN = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
TELEGRAM_CHAT_ID = '8104629569'
WEBHOOK_URL = f'/webhook/{TELEGRAM_TOKEN}'
PORT = 5000
# ============================

app = Flask(__name__)
bot_status = {'active': True}
last_entry = {}
last_pnl = "ยังไม่มีข้อมูล"

def get_server_timestamp():
    try:
        r = requests.get(f'{BASE_URL}/api/v5/public/time')
        return r.json()['data'][0]['ts']
    except:
        return str(int(time.time() * 1000))

def sign_request(timestamp, method, request_path, body=''):
    message = f'{timestamp}{method}{request_path}{body}'
    mac = hmac.new(bytes(API_SECRET, 'utf-8'), message.encode('utf-8'), digestmod='sha256')
    return base64.b64encode(mac.digest()).decode()

def okx_request(method, endpoint, payload=None, retry=3):
    for attempt in range(retry):
        try:
            timestamp = get_server_timestamp()
            body = json.dumps(payload) if payload else ''
            headers = {
                'OK-ACCESS-KEY': API_KEY,
                'OK-ACCESS-SIGN': sign_request(timestamp, method.upper(), endpoint, body),
                'OK-ACCESS-TIMESTAMP': str(int(timestamp) / 1000),
                'OK-ACCESS-PASSPHRASE': API_PASSPHRASE,
                'Content-Type': 'application/json'
            }
            r = requests.request(method, BASE_URL + endpoint, headers=headers, data=body)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt == retry - 1:
                send_telegram(f"[ERROR]\n{str(e)}\n{traceback.format_exc()}")
                return None
            time.sleep(2)

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={'chat_id': TELEGRAM_CHAT_ID, 'text': msg})

def get_balance():
    result = okx_request('GET', '/api/v5/account/balance')
    if result:
        for asset in result['data'][0]['details']:
            if asset['ccy'] == 'USDT':
                return float(asset['cashBal'])
    return 0

def get_price():
    result = okx_request('GET', f'/api/v5/market/ticker?instId={SYMBOL}')
    return float(result['data'][0]['last']) if result else 0

def cancel_all_orders():
    okx_request('POST', '/api/v5/trade/cancel-all-orders', {'instId': SYMBOL})

def close_all_positions():
    okx_request('POST', '/api/v5/trade/close-position', {'instId': SYMBOL, 'mgnMode': 'isolated'})

def place_order(side, size, entry_price, sl_price, tp_price):
    # Entry Order
    order = {
        'instId': SYMBOL,
        'tdMode': 'isolated',
        'side': side,
        'ordType': 'market',
        'sz': str(size),
        'lever': str(LEVERAGE),
        'posSide': 'long' if side == 'buy' else 'short'
    }
    res = okx_request('POST', '/api/v5/trade/order', order)
    if not res or res.get("code") != '0':
        send_telegram(f"[เปิดออเดอร์ล้มเหลว] {side.upper()} {res}")
        return

    # TP/SL
    algo = {
        'instId': SYMBOL,
        'tdMode': 'isolated',
        'side': 'sell' if side == 'buy' else 'buy',
        'ordType': 'oco',
        'tpTriggerPx': str(tp_price),
        'tpOrdPx': '-1',
        'slTriggerPx': str(sl_price),
        'slOrdPx': '-1',
        'sz': str(size),
        'posSide': 'long' if side == 'buy' else 'short'
    }
    okx_request('POST', '/api/v5/trade/order-algo', algo)

    global last_entry
    last_entry = {'price': entry_price, 'side': side, 'size': size}
    send_telegram(f"[เปิดออเดอร์] {side.upper()}\nราคา: {entry_price}")

def check_exit_conditions():
    # This is a placeholder
    pass

def ict_strategy():
    while True:
        if not bot_status['active']:
            time.sleep(10)
            continue

        try:
            # ===== STRATEGY PLACEHOLDER =====
            # สมมุติว่าพบโอกาสเข้า BUY
            signal = True  # ต้องเขียนจริงในระบบจริง
            direction = 'buy'
            price = get_price()
            balance = get_balance()
            position_size = round((balance * CAPITAL_USAGE * LEVERAGE) / price, 3)

            if signal:
                sl = round(price * 0.99, 2)
                tp = round(price * 1.02, 2)
                place_order(direction, position_size, price, sl, tp)
                time.sleep(60 * 15)  # รอ 15 นาที ก่อนหาจังหวะใหม่
        except Exception as e:
            send_telegram(f"[CRITICAL ERROR]\n{str(e)}\n{traceback.format_exc()}")
            time.sleep(10)

@app.route(WEBHOOK_URL, methods=['POST'])
def telegram_webhook():
    data = request.get_json()
    if 'message' not in data: return "ok"
    msg = data['message']
    text = msg.get('text', '').lower()
    user = msg['from']['first_name']

    if 'ping' in text:
        send_telegram("pong")
    elif 'ราคา' in text:
        price = get_price()
        send_telegram(f"ราคาปัจจุบัน: {price} USDT")
    elif 'จุดเข้า' in text:
        if last_entry:
            send_telegram(f"จุดเข้า: {last_entry['price']} ({last_entry['side']}) ขนาด {last_entry['size']}")
        else:
            send_telegram("ยังไม่มีการเข้าออเดอร์")
    elif 'กำไรล่าสุด' in text:
        send_telegram(f"กำไรล่าสุด: {last_pnl}")
    elif 'สถานะ' in text or 'status' in text:
        status = "Active" if bot_status['active'] else "Paused"
        send_telegram(f"สถานะบอท: {status}")
    elif 'stop' in text:
        bot_status['active'] = False
        send_telegram("บอทถูกหยุดแล้ว")
    elif 'resume' in text:
        bot_status['active'] = True
        send_telegram("บอทกลับมาเปิดทำงานแล้ว")

    return "ok"

if __name__ == '__main__':
    Thread(target=ict_strategy).start()
    app.run(host='0.0.0.0', port=PORT)
