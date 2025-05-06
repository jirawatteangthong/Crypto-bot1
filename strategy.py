from utils import fetch_ohlcv, detect_order_blocks, detect_bos, detect_choch, draw_fibonacci

def get_m15_zones():
    candles = fetch_ohlcv('15m')
    trend = detect_bos(candles)
    choch = detect_choch(candles)
    fibo = draw_fibonacci(candles, choch)
    ob_zones = detect_order_blocks(candles, fibo)
    return {'fibo': fibo, 'ob': ob_zones, 'trend': trend}
