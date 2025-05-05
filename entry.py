from utils import fetch_ohlcv, calculate_macd

def check_entry_signal(zones):
    candles = fetch_ohlcv('5m')
    price = candles[-1][4]

    for ob in zones['ob']:
        if ob['low'] <= price <= ob['high']:
            macd, signal, hist = calculate_macd([c[4] for c in candles])
            if macd[-2] < signal[-2] and macd[-1] > signal[-1]:
                return {'direction': 'long', 'price': price, 'ob': ob}
            if macd[-2] > signal[-2] and macd[-1] < signal[-1]:
                return {'direction': 'short', 'price': price, 'ob': ob}
    return None
