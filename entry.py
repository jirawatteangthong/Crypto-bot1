from utils import fetch_current_price, fetch_ohlcv, detect_choch
from telegram import notify

def check_entry_signal(fibo):
    price = fetch_current_price()
    if fibo['direction'] == 'long' and fibo['levels']['61.8'] <= price <= fibo['levels']['78.6']:
        candles_m1 = fetch_ohlcv('1m')[-50:]
        if detect_choch(candles_m1) == 'bullish':
            notify("[ENTRY SIGNAL] Price in zone, CHoCH on M1 bullish")
            return {'direction': 'long', 'entry': price, 'tp': fibo['tp'], 'sl': fibo['sl']}
    elif fibo['direction'] == 'short' and fibo['levels']['78.6'] <= price <= fibo['levels']['61.8']:
        candles_m1 = fetch_ohlcv('1m')[-50:]
        if detect_choch(candles_m1) == 'bearish':
            notify("[ENTRY SIGNAL] Price in zone, CHoCH on M1 bearish")
            return {'direction': 'short', 'entry': price, 'tp': fibo['tp'], 'sl': fibo['sl']}
    return None
