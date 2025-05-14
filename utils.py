# utils.py

import ccxt
import time
from datetime import datetime

from config import API_KEY, API_SECRET, API_PASSPHRASE

def connect_okx():
    return ccxt.okx({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'password': API_PASSPHRASE,
        'enableRateLimit': True,
        'options': {'defaultType': 'future'},
    })

def fetch_ohlcv(tf='5m', limit=100):
    exchange = connect_okx()
    bars = exchange.fetch_ohlcv('BTC/USDT:USDT', tf, limit=limit)
    return bars

def fetch_current_price():
    exchange = connect_okx()
    ticker = exchange.fetch_ticker('BTC/USDT:USDT')
    return ticker['last']

def detect_bos(candles):
    if candles[-1][4] > candles[-5][4]:
        return 'bullish'
    elif candles[-1][4] < candles[-5][4]:
        return 'bearish'
    return None

def detect_choch(candles):
    if candles[-1][4] > candles[-2][4] and candles[-2][4] < candles[-3][4]:
        return 'bullish'
    elif candles[-1][4] < candles[-2][4] and candles[-2][4] > candles[-3][4]:
        return 'bearish'
    return None

def is_new_day():
    now = datetime.utcnow()
    return now.hour == 0 and now.minute < 5
