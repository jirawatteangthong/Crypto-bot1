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

def detect_order_blocks(candles, swing, trend):
    return [{'high': candles[-10][2], 'low': candles[-10][3]}]

def detect_bos(candles):
    high = max(c[2] for c in candles[-20:])
    low = min(c[3] for c in candles[-20:])
    close = candles[-1][4]
    trend = 'long' if close > candles[-10][4] else 'short'
    return trend, {'high': high, 'low': low, 'close': close}

def draw_fibo(swing, trend):
    if trend == 'long':
        diff = swing['high'] - swing['low']
        return {
            'high': swing['high'] - diff * 0.618,
            'low': swing['high'] - diff * 0.786
        }
    else:
        diff = swing['high'] - swing['low']
        return {
            'high': swing['low'] + diff * 0.786,
            'low': swing['low'] + diff * 0.618
        }
