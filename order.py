def set_leverage(account):
    account.set_leverage(instId=SYMBOL, lever='20', mgnMode='cross')

def place_entry_order(trade, side, size):
    trade.place_order(
        instId=SYMBOL,
        tdMode='cross',
        side=side,
        ordType='market',
        sz=str(size)
    )

def place_tp_sl_algo(trade, side, tp, sl):
    trade.place_algo_order(
        instId=SYMBOL,
        tdMode='cross',
        side='sell' if side == 'buy' else 'buy',
        ordType='conditional',
        sz=str(POSITION_SIZE),
        tpTriggerPx=str(tp),
        slTriggerPx=str(sl)
    )

def check_open_positions(account):
    pos = account.get_positions()['data']
    for p in pos:
        if p['instId'] == SYMBOL and float(p['pos']) != 0:
            return p
    return None
