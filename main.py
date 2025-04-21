import time
import hmac
import hashlib
import json
import requests
import datetime
import threading

# OKX API
API_KEY = 'e8e/82c5a-6ccd-4cb3-92a9-3f10144ecd28'
API_SECRET = '3E0BDFF2AF2EF11217C2DCC7E88400C3'
API_PASS = 'Jirawat1-'
BASE_URL = 'https://www.okx.com'

# Telegram
TELEGRAM_TOKEN = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
TELEGRAM_CHAT_ID = '8104629569'

# ตั้งค่า
SYMBOL = 'BTC-USDT-SWAP'
LEVERAGE = 13
TRADE_PORTION = 0.3  # ใช้ทุน 30% ของพอร์ต
TIMEFRAME = '15m'

# ฟังก์ชันส่งข้อความ Telegram
def send_telegram(text):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    requests.post(url, json={'chat_id': TELEGRAM_CHAT_ID, 'text': text})

# ฟังก์ชันดึง server time
def get_server_timestamp():
    r = requests.get(f'{BASE_URL}/api/v5/public/time')
    return r.json()['data'][0]['ts']

# ฟังก์ชันเซ็น request
def sign(method, path, body=''):
    timestamp = str(get_server_timestamp())
    message = f'{timestamp}{method}{path}{body}'
    sign = hmac.new(API_SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()
    return {
        'OK-ACCESS-KEY': API_KEY,
        'OK-ACCESS-SIGN': sign,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': API_PASS,
        'Content-Type': 'application/json'
    }

# ฟังก์ชันดึง balance
def get_balance():
    url = '/api/v5/account/balance?ccy=USDT'
    headers = sign('GET', url)
    r = requests.get(BASE_URL + url, headers=headers)
    data = r.json()['data'][0]
    return float(data['details'][0]['availBal'])

# ฟังก์ชันวิเคราะห์แนวโน้ม (ใช้ logic ง่าย ๆ เป็นตัวอย่าง)
def get_trend():
    url = f'https://www.okx.com/api/v5/market/candles?instId={SYMBOL}&bar={TIMEFRAME}&limit=5'
    r = requests.get(url)
    data = r.json()['data']
    close_prices = [float(x[4]) for x in data][::-1]
    if close_prices[-1] > close_prices[-2] > close_prices[-3]:
        return 'long'
    elif close_prices[-1] < close_prices[-2] < close_prices[-3]:
        return 'short'
    else:
        return None

# ฟังก์ชันตั้ง leverage
def set_leverage():
    url = '/api/v5/account/set-leverage'
    body = {
        "instId": SYMBOL,
        "lever": str(LEVERAGE),
        "mgnMode": "isolated",
        "posSide": "net"
    }
    headers = sign('POST', url, json.dumps(body))
    requests.post(BASE_URL + url, headers=headers, data=json.dumps(body))

# ฟังก์ชันเปิดออเดอร์
def open_order(side, size):
    url = '/api/v5/trade/order'
    body = {
        "instId": SYMBOL,
        "tdMode": "isolated",
        "side": side,
        "ordType": "market",
        "sz": str(size)
    }
    headers = sign('POST', url, json.dumps(body))
    r = requests.post(BASE_URL + url, headers=headers, data=json.dumps(body))
    return r.json()

# ฟังก์ชันปิดออเดอร์
def close_position():
    url = '/api/v5/trade/close-position'
    body = {
        "instId": SYMBOL,
        "mgnMode": "isolated"
    }
    headers = sign('POST', url, json.dumps(body))
    requests.post(BASE_URL + url, headers=headers, data=json.dumps(body))

# ฟังก์ชันหลักของบอท
def bot():
    send_telegram('บอทเริ่มทำงานแล้ว')
    set_leverage()
    in_position = False
    position_side = ''
    entry_price = 0.0

    while True:
        try:
            trend = get_trend()
            balance = get_balance()
            mark_price = float(requests.get(f'https://www.okx.com/api/v5/market/ticker?instId={SYMBOL}').json()['data'][0]['last'])

            if not in_position and trend in ['long', 'short']:
                side = 'buy' if trend == 'long' else 'sell'
                size = round((balance * TRADE_PORTION * LEVERAGE) / mark_price, 3)
                res = open_order(side, size)
                if res.get('code') == '0':
                    in_position = True
                    position_side = side
                    entry_price = mark_price
                    send_telegram(f'เปิดออเดอร์ {side.upper()} ที่ราคา {mark_price}')
                else:
                    send_telegram(f'เปิดออเดอร์ไม่สำเร็จ: {res}')

            elif in_position:
                profit = (mark_price - entry_price) if position_side == 'buy' else (entry_price - mark_price)
                if abs(profit) / entry_price > 0.01:  # take profit 1%
                    close_position()
                    send_telegram(f'ปิดออเดอร์ {position_side.upper()} ที่ราคา {mark_price}\nกำไร: {profit:.2f} USDT')
                    in_position = False

            time.sleep(15)

        except Exception as e:
            send_telegram(f'เกิดข้อผิดพลาด: {e}')
            time.sleep(30)

# รันบอท
if __name__ == '__main__':
    bot()
