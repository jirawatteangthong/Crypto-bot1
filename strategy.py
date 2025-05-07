from utils import fetch_ohlcv, detect_order_blocks, detect_bos

def get_m15_zones():
    candles = fetch_ohlcv('15m')
    ob_zones = detect_order_blocks(candles)
    trend = detect_bos(candles)
    return {'ob': ob_zones}, trend
