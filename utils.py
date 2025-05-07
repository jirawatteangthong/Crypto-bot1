import ccxt
import datetime
from config import *

exchange = ccxt.okx({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSPHRASE,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

def fetch_ohlcv(tf):
    return exchange.fetch_ohlcv(SYMBOL, timeframe=tf, limit=100)

def detect_order_blocks(candles):
    return [{'high': candles[-10][2], 'low': candles[-10][3], 'price': candles[-10][4], 'type': 'bullish'}]

def detect_bos(candles):
    if candles[-1][4] > candles[-2][4]:
        return 'bullish'
    else:
        return 'bearish'

def is_new_day():
    return datetime.datetime.utcnow().hour == 0
