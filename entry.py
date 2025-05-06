from utils import fetch_ohlcv, calculate_macd

def check_entry_signal(zones):
    candles = fetch_ohlcv('5m')
    price = candles[-1][4]
    fibo = zones.get('fibo')

    if not fibo:
        return None

    if fibo['low'] <= price <= fibo['high']:
        macd, signal, hist = calculate_macd([c[4] for c in candles])
        if fibo['direction'] == 'long' and macd[-2] < signal[-2] and macd[-1] > signal[-1]:
            return {'direction': 'long', 'price': price, 'ob': fibo['swing']}
        if fibo['direction'] == 'short' and macd[-2] > signal[-2] and macd[-1] < signal[-1]:
            return {'direction': 'short', 'price': price, 'ob': fibo['swing']}
    return None
