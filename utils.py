import ccxt
import time
from datetime import datetime
from config import OKX_API_KEY, OKX_API_SECRET, OKX_API_PASSWORD, SYMBOL

def connect_okx():
    return ccxt.okx({
        'apiKey': OKX_API_KEY,
        'secret': OKX_API_SECRET,
        'password': OKX_API_PASSWORD,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future'
        }
    })

def fetch_ohlcv(tf='5m'):
    exchange = connect_okx()
    return exchange.fetch_ohlcv(SYMBOL, timeframe=tf, limit=50)

def fetch_current_price():
    exchange = connect_okx()
    ticker = exchange.fetch_ticker(SYMBOL)
    return ticker['last']

def detect_bos(candles):
    if candles[-1][4] > candles[-2][4] > candles[-3][4]:
        return 'bullish'
    elif candles[-1][4] < candles[-2][4] < candles[-3][4]:
        return 'bearish'
    return None

def is_new_day():
    now = datetime.utcnow()
    return now.hour == 0 and now.minute < 5
