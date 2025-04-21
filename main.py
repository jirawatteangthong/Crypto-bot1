import time
import hmac
import hashlib
import base64
import requests
import threading
import datetime
import json
from flask import Flask
import pandas as pd

# ---------------------------- CONFIG ----------------------------
API_KEY = 'e8e/82c5a-6ccd-4cb3-92a9-3f10144ecd28'
API_SECRET = '3E0BDFF2AF2EF11217C2DCC7E88400C3'
API_PASSPHRASE = 'Jirawat1-'
TELEGRAM_TOKEN = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
TELEGRAM_CHAT_ID = '8104629569'
SYMBOL = 'BTC-USDT'
LEVERAGE = 13
TRADE_PERCENTAGE = 0.3
BASE_URL = 'https://www.okx.com'
HEADERS = {
    'Content-Type': 'application/json',
    'OK-ACCESS-KEY': API_KEY,
    'OK-ACCESS-PASSPHRASE': API_PASSPHRASE
}

current_order_id = None
choch_notified = False
fibo_notified = False

# ---------------------------- UTILS ----------------------------
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})

def get_iso_timestamp():
    return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()

def sign_request(method, path, body=''):
    timestamp = get_iso_timestamp()
    message = f'{timestamp}{method}{path}{body}'
    mac = hmac.new(bytes(API_SECRET, 'utf-8'), bytes(message, 'utf-8'), digestmod=hashlib.sha256)
    sign = base64.b64encode(mac.digest()).decode()
    HEADERS.update({
        'OK-ACCESS-SIGN': sign,
        'OK-ACCESS-TIMESTAMP': timestamp
    })
    return HEADERS

def get_candles(symbol, bar, limit=150):
    url = f'{BASE_URL}/api/v5/market/candles?instId={symbol}&bar={bar}&limit={limit}'
    r = requests.get(url)
    df = pd.DataFrame(r.json()['data'], columns=[
    'timestamp', 'open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote', 'confirm'])
    df = df.iloc[::-1]
    df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].astype(float)
    return df

def detect_choch(df):
    if len(df) < 3:
        return None
    high1, high2 = df.iloc[-3]['high'], df.iloc[-2]['high']
    low1, low2 = df.iloc[-3]['low'], df.iloc[-2]['low']
    current_high, current_low = df.iloc[-1]['high'], df.iloc[-1]['low']
    if high2 > high1 and current_low < low2:
        return 'bearish'
    elif low2 < low1 and current_high > high2:
        return 'bullish'
    return None

def get_balance():
    path = '/api/v5/account/balance'
    headers = sign_request('GET', path)
    res = requests.get(BASE_URL + path, headers=headers)
    data = res.json()['data'][0]['details']
    for d in data:
        if d['ccy'] == 'USDT':
            return float(d['cashBal'])
    return 0

def place_order(side, size):
    global current_order_id
    path = '/api/v5/trade/order'
    body = {
        "instId": SYMBOL,
        "tdMode": "cross",
        "side": side,
        "ordType": "market",
        "sz": str(size),
        "lever": str(LEVERAGE),
        "posSide": "long" if side == "buy" else "short"
    }
    body_str = json.dumps(body)
    headers = sign_request('POST', path, body_str)
    res = requests.post(BASE_URL + path, headers=headers, data=body_str)
    result = res.json()
    if 'data' in result:
        current_order_id = result['data'][0]['ordId']
    return result

def close_all_positions():
    path = '/api/v5/trade/close-position'
    body = {"instId": SYMBOL, "mgnMode": "cross"}
    body_str = json.dumps(body)
    headers = sign_request('POST', path, body_str)
    requests.post(BASE_URL + path, headers=headers, data=body_str)

def get_position():
    path = f'/api/v5/account/positions?instId={SYMBOL}'
    headers = sign_request('GET', path)
    res = requests.get(BASE_URL + path, headers=headers).json()
    if res['data']:
        pos = res['data'][0]
        return {
            "side": pos['posSide'],
            "size": float(pos['pos']),
            "entry_price": float(pos['avgPx']),
            "unrealized": float(pos['upl']),
        }
    return None

# ---------------------------- STRATEGY LOOP ----------------------------
def strategy_loop():
    global choch_notified, fibo_notified, current_order_id
    send_telegram("Bot started and running on Render 24/7")
    while True:
        try:
            df_m15 = get_candles(SYMBOL, '15m')
            choch = detect_choch(df_m15)
            if choch and not choch_notified:
                send_telegram(f"CHoCH detected on M15: {choch}")
                choch_notified = True

                fib_high = df_m15['high'].iloc[-3]
                fib_low = df_m15['low'].iloc[-3]
                fib_zone = (fib_low + 0.618 * (fib_high - fib_low), fib_low + 0.786 * (fib_high - fib_low))

            last_price = float(df_m15['close'].iloc[-1])
            if choch_notified and fib_zone[0] <= last_price <= fib_zone[1] and not fibo_notified:
                send_telegram("Price entered Fibonacci zone")
                fibo_notified = True

                df_m5 = get_candles(SYMBOL, '5m')
                choch_m5 = detect_choch(df_m5)
                if choch_m5:
                    send_telegram(f"CHoCH confirmed on M5: {choch_m5}")
                    balance = get_balance()
                    trade_value = balance * TRADE_PERCENTAGE * LEVERAGE
                    mark_price = float(df_m5['close'].iloc[-1])
                    size = round(trade_value / mark_price, 4)

                    place_order("buy" if choch_m5 == "bullish" else "sell", size)
                    send_telegram(f"Opened {choch_m5.upper()} order: Size {size}")
                    monitor_position()

                    # Reset for next cycle
                    choch_notified = False
                    fibo_notified = False
                    current_order_id = None

            time.sleep(30)
        except Exception as e:
            send_telegram(f"Error: {str(e)}")
            time.sleep(60)

# ---------------------------- POSITION MONITOR ----------------------------
def monitor_position():
    entry_checked = False
    while True:
        pos = get_position()
        if not pos or pos['size'] == 0:
            return

        pnl = pos['unrealized']
        entry = pos['entry_price']
        side = pos['side']
        size = pos['size']
        pnl_pct = (pnl / (entry * size)) * 100

        if pnl_pct <= -12:
            send_telegram(f"SL Hit (-12%): {pnl_pct:.2f}%")
            close_all_positions()
            return
        elif pnl_pct >= 30:
            send_telegram(f"TP Hit (+30%): {pnl_pct:.2f}%")
            close_all_positions()
            return
        elif pnl_pct >= 10 and not entry_checked:
            send_telegram("Profit +10%, setting trailing SL to +2%")
            entry_checked = True

        elif entry_checked and pnl_pct <= 2:
            send_telegram("Trailing SL Hit (+2%)")
            close_all_positions()
            return

        time.sleep(10)

# ---------------------------- FLASK SERVER ----------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return 'OKX Bot is running!'

def run_bot():
    strategy_loop()

if __name__ == '__main__':
    t = threading.Thread(target=run_bot)
    t.daemon = True
    t.start()
    app.run(host='0.0.0.0', port=10000)
