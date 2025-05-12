import okx.Trade as Trade
import okx.Account as Account
from config import SYMBOL, LEVERAGE
from utils import log

def set_leverage(account_client):
    account_client.set_leverage(
        lever=str(LEVERAGE), mgnMode='isolated', instId=SYMBOL
    )
    log(f"Set Leverage: {LEVERAGE}x")

def place_entry_order(client, side, size):
    result = client.place_order(
        instId=SYMBOL, tdMode='isolated', side=side, ordType='market', sz=str(size)
    )
    log(f"Entry Order: {side} {size} result: {result}")
    return result['data'][0]['ordId']

def place_tp_sl_algo(client, side, tp, sl):
    algo = client.place_algo_order(
        instId=SYMBOL,
        tdMode='isolated',
        side='sell' if side == 'buy' else 'buy',
        ordType='oco',
        sz='0.5',
        tpTriggerPx=str(tp),
        tpOrdPx=str(tp),
        slTriggerPx=str(sl),
        slOrdPx=str(sl),
        triggerPxType='last'
    )
    log(f"OCO Order TP:{tp} SL:{sl} result: {algo}")
    return algo

def check_open_positions(account_client):
    pos = account_client.get_positions(instType='SWAP')
    for p in pos['data']:
        if p['instId'] == SYMBOL and float(p['pos']) > 0:
            return p
    return None
