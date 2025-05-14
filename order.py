# order.py

from utils import connect_okx
from telegram import trade_notify

def open_trade(signal, capital):
    exchange = connect_okx()
    side = 'buy' if signal['direction'] == 'long' else 'sell'
    amount = 0.1

    params = {'positionSide': 'long' if side == 'buy' else 'short'}
    order = exchange.create_order(
        symbol='BTC/USDT:USDT',
        type='market',
        side=side,
        amount=amount,
        params=params
    )

    trade_notify(
        direction=signal['direction'],
        entry=signal['price'],
        size=amount,
        tp=signal['tp'],
        sl=signal['sl']
    )
    return capital

def monitor_trades(positions, capital):
    # แนะนำให้ต่อยอดตรงนี้ด้วย unrealized pnl จาก exchange
    return positions, capital

def get_open_positions():
    return []
