def check_entry_signal(zones):
    last_price = zones['fibo']['current_price']
    for ob in zones['ob']:
        if ob['low'] <= last_price <= ob['high']:
            return {'direction': zones['trend'], 'price': last_price, 'ob': ob, 'full_size': True}
    if zones['fibo']['zone_61_78'][0] <= last_price <= zones['fibo']['zone_61_78'][1]:
        return {'direction': zones['trend'], 'price': last_price, 'ob': None, 'full_size': False}
    return None
