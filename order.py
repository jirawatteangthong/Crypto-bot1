import ccxt
from config import SYMBOL
from telegram import trade_notify
from utils import connect_okx

def open_trade(signal, capital):
    exchange = connect_okx()
    side = 'buy' if signal['direction'] == 'long' else 'sell'
    amount = 0.1
    params = {'posSide': signal['direction']}

    exchange.create_order(
        symbol=SYMBOL,
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
    return positions
