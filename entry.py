def get_entry_signals(fibo, trend, orders_today):
    signals = []

    if orders_today == 0:
        signals.append({
            'direction': 'long' if trend == 'bullish' else 'short',
            'entry_price': fibo['61.8'],
            'tp': fibo['high'] if trend == 'bullish' else fibo['low'],
            'sl': fibo['low'] if trend == 'bullish' else fibo['high']
        })
    elif orders_today == 1:
        signals.append({
            'direction': 'long' if trend == 'bullish' else 'short',
            'entry_price': fibo['78.6'],
            'tp': fibo['high'] if trend == 'bullish' else fibo['low'],
            'sl': fibo['low'] if trend == 'bullish' else fibo['high']
        })

    return signals
