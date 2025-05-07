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

def fetch_current_price():
    ticker = exchange.fetch_ticker(SYMBOL)
    return ticker['last']

def detect_choch(candles):
    highs = [c[2] for c in candles]
    lows = [c[3] for c in candles]
    closes = [c[4] for c in candles]

    recent_high = max(highs[-20:])
    recent_low = min(lows[-20:])
    prev_high = max(highs[-40:-20])
    prev_low = min(lows[-40:-20])

    if closes[-1] > prev_high:
        return 'bullish'
    elif closes[-1] < prev_low:
        return 'bearish'
    return None

def is_new_day():
    return datetime.datetime.utcnow().hour == 0
