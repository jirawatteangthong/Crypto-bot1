from utils import connect_okx
from telegram import trade_notify

def open_trade(signal, capital):
    exchange = connect_okx()
    side = 'buy' if signal['direction'] == 'long' else 'sell'
    pos_side = 'long' if signal['direction'] == 'long' else 'short'
    amount = 0.1

    params = {
        'posSide': pos_side,
        'reduceOnly': False
    }

    # Market entry
    exchange.create_order(
        symbol='BTC/USDT:USDT',
        type='market',
        side=side,
        amount=amount,
        params=params
    )

    # TP/SL using limit and stop-market
    tp_order = {
        'type': 'take_profit_market',
        'params': {
            'tpTriggerPx': str(signal['tp']),
            'tpOrdPx': '-1',  # market
            'posSide': pos_side
        }
    }
    sl_order = {
        'type': 'stop_loss_market',
        'params': {
            'slTriggerPx': str(signal['sl']),
            'slOrdPx': '-1',
            'posSide': pos_side
        }
    }

    exchange.private_post_trade_order_algo(tp_order['params'])
    exchange.private_post_trade_order_algo(sl_order['params'])

    trade_notify(
        direction=signal['direction'],
        entry=signal['price'],
        size=amount,
        tp=signal['tp'],
        sl=signal['sl']
    )
    return capital

def monitor_trades(positions, capital):
    return positions, capital

def get_open_positions():
    return []
