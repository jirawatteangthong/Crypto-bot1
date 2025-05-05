from utils import fetch_ohlcv, detect_order_blocks, detect_fvg, detect_bos

def get_h1_zones():
    candles = fetch_ohlcv('1h')
    ob_zones = detect_order_blocks(candles)
    fvg_zones = detect_fvg(candles)
    bos = detect_bos(candles)
    return {'ob': ob_zones, 'fvg': fvg_zones, 'bos': bos}
