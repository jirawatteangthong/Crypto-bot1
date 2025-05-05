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

def calculate_macd(closes, fast=12, slow=26, signal=9):
    def ema(values, period):
        k = 2 / (period + 1)
        ema_val = values[0]
        result = []
        for price in values:
            ema_val = price * k + ema_val * (1 - k)
            result.append(ema_val)
        return result
    macd = [f - s for f, s in zip(ema(closes, fast), ema(closes, slow))]
    signal_line = ema(macd, signal)
    hist = [m - s for m, s in zip(macd, signal_line)]
    return macd, signal_line, hist

def detect_order_blocks(candles):
    # Placeholder: เพิ่ม logic SMC OB จริงตาม swing H1
    return [{'high': candles[-10][2], 'low': candles[-10][3]}]

def detect_fvg(candles):
    # Placeholder
    return []

def detect_bos(candles):
    # Placeholder
    return []

def is_new_day(last_date):
    return last_date != datetime.datetime.utcnow().date()

def should_health_check(last, hours):
    return (datetime.datetime.utcnow() - last).total_seconds() >= hours * 3600
