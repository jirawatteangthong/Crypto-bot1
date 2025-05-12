import requests
import datetime
import time
from config import SYMBOL

# ดึงแท่งเทียนจาก OKX
def fetch_candles(timeframe='1h', limit=200):
    url = f"https://www.okx.com/api/v5/market/candles"
    params = {
        'instId': SYMBOL,
        'bar': timeframe,
        'limit': limit
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    raw = r.json()['data']
    candles = [
        {
            'timestamp': int(c[0]),
            'open': float(c[1]),
            'high': float(c[2]),
            'low': float(c[3]),
            'close': float(c[4])
        }
        for c in raw[::-1]
    ]
    return candles

# ดึงราคาปัจจุบัน
def fetch_current_price():
    url = f"https://www.okx.com/api/v5/market/ticker"
    params = {'instId': SYMBOL}
    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()['data'][0]
    return float(data['last'])

# เช็คว่าเป็นวันใหม่หรือยัง (เริ่มใหม่ตอน 00:00 UTC)
def is_new_day():
    now = datetime.datetime.utcnow()
    return now.hour == 0 and now.minute < 5
