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

def is_new_day(last_date):
    return last_date != datetime.datetime.utcnow().date()

def should_health_check(last, hours):
    return (datetime.datetime.utcnow() - last).total_seconds() >= hours * 3600

def detect_bos(candles):
    return 'long' if candles[-1][4] > candles[-10][4] else 'short'

def detect_choch(candles):
    return candles[-2][4] < candles[-10][4] if candles[-1][4] > candles[-2][4] else False

def draw_fibonacci(candles, choch):
    high = max(c[2] for c in candles[-20:])
    low = min(c[3] for c in candles[-20:])
    zone = (low + 0.618 * (high - low), low + 0.786 * (high - low))
    return {'zone_61_78': zone, 'current_price': candles[-1][4]}

def detect_order_blocks(candles, fibo):
    # Placeholder: fake OB inside fibo zone
    return [{'high': fibo['zone_61_78'][1], 'low': fibo['zone_61_78'][0]}]
