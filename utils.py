import ccxt
import time
from datetime import datetime

def connect_okx():
    return ccxt.okx({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'password': API_PASSWORD,
        'enableRateLimit': True,
        'options': {'defaultType': 'future'}
    })

def get_highs_lows(candles):
    highs = [c['high'] for c in candles]
    lows = [c['low'] for c in candles]
    return highs, lows

def fetch_ohlcv(symbol="BTC/USDT:USDT", timeframe="5m", limit=50):
    exchange = connect_okx()
    raw = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    return [{'timestamp': r[0], 'open': r[1], 'high': r[2], 'low': r[3], 'close': r[4]} for r in raw]

def get_current_timeframe_data(tf):
    return fetch_ohlcv(timeframe=tf)

def is_new_day():
    now = datetime.utcnow()
    return now.hour == 0 and now.minute < 5
