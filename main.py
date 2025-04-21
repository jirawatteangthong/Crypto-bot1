import time
import hmac
import hashlib
import requests
import json
from flask import Flask, request

# === CONFIG ===
API_KEY = 'e8e/82c5a-6ccd-4cb3-92a9-3f10144ecd28'
API_SECRET = '3E0BDFF2AF2EF11217C2DCC7E88400C3'
API_PASS = 'Jirawat1-'
TELEGRAM_TOKEN = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
TELEGRAM_CHAT_ID = '8104629569'
SYMBOL = 'BTC-USDT-SWAP'
LEVERAGE = 13
CAPITAL_USAGE = 0.3  # 30% ของพอร์ต

app = Flask(__name__)
position_open = False  # สำหรับป้องกันเปิดซ้อน

# === OKX API ===
def get_server_time():
    r = requests.get('https://www.okx.com/api/v5/public/time')
    return r.json()['data'][0]['ts']

def get_headers():
    timestamp = str(int(get_server_time()) / 1000)
    msg = f'{timestamp}GET/api/v5/account/balance'
    sign = hmac.new(API_SECRET.encode(), msg.encode(), hashlib.sha256).digest()
    sign_b64 = base64.b64encode(sign).decode()
    return {
        'OK-ACCESS-KEY': API_KEY,
        'OK-ACCESS-SIGN': sign_b64,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': API_PASS,
        'Content-Type': 'application/json'
    }

def send_telegram(text):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': text}
    requests.post(url, json=data)

def get_balance():
    url = 'https://www.okx.com/api/v5/account/balance'
    r = requests.get(url, headers=get_headers())
    usdt = float([x for x in r.json()['data'][0]['details'] if x['ccy'] == 'USDT'][0]['availBal'])
    return usdt

def place_order(side, entry_price, sl_price, tp_price, sz):
    url = 'https://www.okx.com/api/v5/trade/order'
    data = {
        'instId': SYMBOL,
        'tdMode': 'isolated',
        'side': side,
        'ordType': 'market',
        'sz': str(sz),
        'lever': str(LEVERAGE)
    }
    r = requests.post(url, headers=get_headers(), json=data)
    send_telegram(f"เปิดออเดอร์: {side.upper()}\nEntry: {entry_price}\nSL: {sl_price}\nTP: {tp_price}")
    return r.json()

def get_candles(timeframe='1H', limit=50):
    url = f'https://www.okx.com/api/v5/market/candles?instId={SYMBOL}&bar={timeframe}&limit={limit}'
    r = requests.get(url)
    return r.json()['data'][::-1]

# === STRATEGY ===
def analyze_trend():
    tf_1d = get_candles('1D', 3)
    tf_1h = get_candles('1H', 3)

    def is_bullish(c):
        return float(c[4]) > float(c[1])  # close > open

    trend_1d = 'bullish' if is_bullish(tf_1d[-2]) else 'bearish'
    trend_1h = 'bullish' if is_bullish(tf_1h[-2]) else 'bearish'

    if trend_1d == trend_1h:
        return trend_1d
    return None

def entry_signal(trend):
    m15 = get_candles('15m', 3)
    last_close = float(m15[-2][4])
    prev_close = float(m15[-3][4])

    if trend == 'bullish' and last_close > prev_close:
        return 'buy', last_close
    elif trend == 'bearish' and last_close < prev_close:
        return 'sell', last_close
    return None, None

def calculate_tp_sl(entry_price, side, rr=2.0):
    risk = entry_price * 0.005  # 0.5% SL
    if side == 'buy':
        sl = entry_price - risk
        tp = entry_price + (risk * rr)
    else:
        sl = entry_price + risk
        tp = entry_price - (risk * rr)
    return round(sl, 2), round(tp, 2)

def open_trade():
    global position_open
    if position_open:
        return

    trend = analyze_trend()
    if trend:
        side, entry_price = entry_signal(trend)
        if side and entry_price:
            balance = get_balance()
            trade_value = balance * CAPITAL_USAGE * LEVERAGE
            size = round(trade_value / entry_price, 3)
            sl, tp = calculate_tp_sl(entry_price, side)
            place_order(side, entry_price, sl, tp, size)
            position_open = True

def check_position_closed():
    global position_open
    url = f'https://www.okx.com/api/v5/account/positions?instId={SYMBOL}'
    r = requests.get(url, headers=get_headers())
    positions = r.json()['data']
    has_position = any(float(p['pos']) > 0 for p in positions)
    if not has_position and position_open:
        send_telegram("ปิดออเดอร์เรียบร้อยแล้ว")
        position_open = False

# === TELEGRAM BOT ===
@app.route('/', methods=['POST'])
def webhook():
    data = request.json
    msg = data['message']['text'].strip().lower()

    if msg == '/ping':
        send_telegram("บอทยังทำงานอยู่ครับ")
    elif msg == '/status':
        status = "มีออเดอร์เปิดอยู่" if position_open else "ยังไม่มีออเดอร์เปิด"
        send_telegram(f"สถานะบอท: {status}")
    elif msg == '/now':
        candles = get_candles('1H', 1)
        price = candles[-1][4]
        send_telegram(f"ราคาล่าสุด BTC: {price} USDT")
    return '', 200

# === MAIN LOOP (เรียกทุก 1 นาที) ===
def run_bot():
    while True:
        try:
            open_trade()
            check_position_closed()
        except Exception as e:
            send_telegram(f"เกิดข้อผิดพลาด: {str(e)}")
        time.sleep(60)

if __name__ == '__main__':
    from threading import Thread
    Thread(target=run_bot).start()
    app.run(host='0.0.0.0', port=10000)
