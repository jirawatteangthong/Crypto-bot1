import ccxt
from config import *
import datetime

exchange = ccxt.okx({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSPHRASE,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

def fetch_ohlcv(tf='15m'):
    return exchange.fetch_ohlcv(SYMBOL, timeframe=tf, limit=100)

def detect_order_blocks(candles, fibo):
    obs = []
    for i in range(-20, -1):
        low, high = candles[i][3], candles[i][2]
        if fibo['61.8'] <= low <= fibo['78.6'] or fibo['61.8'] <= high <= fibo['78.6']:
            obs.append({'low': low, 'high': high})
    return obs

def detect_bos(candles):
    if candles[-1][4] > candles[-5][4]:
        return 'long', False
    elif candles[-1][4] < candles[-5][4]:
        return 'short', False
    return 'long', True  # default

def draw_fibonacci(candles, trend, choch):
    if trend == 'long':
        swing_low = min([c[3] for c in candles[-30:]])
        swing_high = max([c[2] for c in candles[-30:]])
    else:
        swing_high = max([c[2] for c in candles[-30:]])
        swing_low = min([c[3] for c in candles[-30:]])
    return {
        '0.0': swing_high if trend == 'short' else swing_low,
        '100.0': swing_low if trend == 'short' else swing_high,
        '61.8': swing_low + 0.618 * (swing_high - swing_low),
        '78.6': swing_low + 0.786 * (swing_high - swing_low)
    }
