def check_entry_signal(zones, trend):
    price = zones['swing']['close']
    entry = None

    for ob in zones['ob']:
        if ob['low'] <= price <= ob['high']:
            entry = ob
            break

    if entry:
        return {'direction': trend, 'price': price, 'ob': entry}

    fibo = zones['fibo']
    if fibo['low'] <= price <= fibo['high']:
        fibo_entry = {'high': fibo['high'], 'low': fibo['low']}
        return {'direction': trend, 'price': price, 'ob': fibo_entry}

    return None
