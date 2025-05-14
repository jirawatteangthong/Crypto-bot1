from utils import exchange
from telegram import alert_choch_m15, alert_fibo_drawn

def fetch_ohlcv(tf, limit):
    return exchange.fetch_ohlcv('BTC-USDT-SWAP', timeframe=tf, limit=limit)

def detect_choch(candles):
    highs = [x[2] for x in candles]
    lows = [x[3] for x in candles]
    close = candles[-1][4]
    prev_close = candles[-2][4]

    if prev_close < max(highs[:-1]) and close > max(highs[:-1]):
        return 'bullish'
    elif prev_close > min(lows[:-1]) and close < min(lows[:-1]):
        return 'bearish'
    return None

def detect_bos(candles):
    highs = [x[2] for x in candles]
    lows = [x[3] for x in candles]
    close = candles[-1][4]

    if close > max(highs[:-1]):
        return 'bullish'
    elif close < min(lows[:-1]):
        return 'bearish'
    return None

def get_fibo_zone():
    h1 = fetch_ohlcv('1h', 100)
    m15 = fetch_ohlcv('15m', 70)

    trend = detect_bos(h1)
    choch_m15 = detect_choch(m15)

    if not trend or choch_m15 == trend or choch_m15 is None:
        return None

    alert_choch_m15()

    highs = [x[2] for x in h1[-20:]]
    lows = [x[3] for x in h1[-20:]]

    if trend == 'bullish':
        low = min(lows)
        high = max(highs)
        fibo_10 = low + (high - low) * 0.1
        fibo_110 = low + (high - low) * 1.1
        alert_fibo_drawn(low, high)
        return {
            'trend': 'long',
            'entry_zone': (low + (high - low) * 0.618, low + (high - low) * 0.786),
            'tp': fibo_10,
            'sl': fibo_110,
            'low': low,
            'high': high
        }

    elif trend == 'bearish':
        high = max(highs)
        low = min(lows)
        fibo_10 = high - (high - low) * 0.1
        fibo_110 = high - (high - low) * 1.1
        alert_fibo_drawn(high, low)
        return {
            'trend': 'short',
            'entry_zone': (high - (high - low) * 0.786, high - (high - low) * 0.618),
            'tp': fibo_10,
            'sl': fibo_110,
            'low': high,
            'high': low
        }

    return None
