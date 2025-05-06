from utils import fetch_ohlcv

def check_entry_signal(zones, trend):
    candles = fetch_ohlcv('15m')
    price = candles[-1][4]

    for ob in zones['ob']:
        if ob['low'] <= price <= ob['high']:
            return {'direction': trend, 'price': price, 'ob': ob}

    fibo_zone = zones['fibo']
    if fibo_zone['61.8'] <= price <= fibo_zone['78.6']:
        return {
            'direction': trend,
            'price': price,
            'ob': {'low': fibo_zone['61.8'], 'high': fibo_zone['78.6'], 'partial': True}
        }
    return None
