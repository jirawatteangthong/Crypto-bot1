def check_entry_signal(zones, trend):
    price = zones['ob'][-1]['price']
    last_ob = zones['ob'][-1]

    if trend == 'bullish' and last_ob['type'] == 'bullish':
        return {'direction': 'long', 'price': price, 'ob': last_ob}
    if trend == 'bearish' and last_ob['type'] == 'bearish':
        return {'direction': 'short', 'price': price, 'ob': last_ob}
    return None
