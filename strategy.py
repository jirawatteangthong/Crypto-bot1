from utils import fetch_ohlcv, detect_bos, detect_choch
from telegram import notify

def get_fibo_zone():
    candles_m15 = fetch_ohlcv('15m')[-70:]
    candles_h1 = fetch_ohlcv('1h')[-50:]
    
    trend_h1 = detect_bos(candles_h1)
    choch = detect_choch(candles_m15)

    if not choch or choch != trend_h1:
        if choch and choch != trend_h1:
            notify(f"[SKIP TRADE] CHoCH: {choch}, H1 Trend: {trend_h1}")
        return None, trend_h1

    highs = [c[2] for c in candles_m15]
    lows = [c[3] for c in candles_m15]
    swing_high = max(highs)
    swing_low = min(lows)

    if choch == 'bullish':
        return {
            'low': swing_low,
            'high': swing_high,
            'levels': {
                '61.8': swing_low + 0.618 * (swing_high - swing_low),
                '78.6': swing_low + 0.786 * (swing_high - swing_low)
            },
            'tp': swing_high,
            'sl': swing_low,
            'direction': 'long'
        }, trend_h1
    else:
        return {
            'low': swing_low,
            'high': swing_high,
            'levels': {
                '61.8': swing_high - 0.618 * (swing_high - swing_low),
                '78.6': swing_high - 0.786 * (swing_high - swing_low)
            },
            'tp': swing_low,
            'sl': swing_high,
            'direction': 'short'
        }, trend_h1
