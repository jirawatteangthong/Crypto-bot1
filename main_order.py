import time
from strategy import get_fibo_zone
from entry import check_entry_signal
from telegram import alert_start, alert_error, reset_flags
from utils import exchange, SYMBOL

def place_order(direction, size, tp, sl):
    side = 'buy' if direction == 'long' else 'sell'
    try:
        exchange.set_leverage(LEVERAGE, SYMBOL)
        order = exchange.create_market_order(SYMBOL, side, size)
        reduce_side = 'sell' if side == 'buy' else 'buy'
        exchange.create_order(SYMBOL, 'take_profit_market', reduce_side, size, None, {
            'triggerPrice': tp,
            'closePosition': True
        })
        exchange.create_order(SYMBOL, 'stop_market', reduce_side, size, None, {
            'triggerPrice': sl,
            'closePosition': True
        })
    except Exception as e:
        alert_error(str(e))

def run():
    alert_start()
    fibo = None
    while True:
        try:
            if not fibo:
                fibo = get_fibo_zone()
                reset_flags()
            if fibo:
                signal = check_entry_signal(fibo)
                if signal:
                    place_order(signal['direction'], signal['size'], signal['tp'], signal['sl'])
                    fibo = None  # à¸£à¸­à¸§à¸²à¸à¸£à¸­à¸à¹à¸«à¸¡à¹à¸«à¸¥à¸±à¸à¹à¸à¹à¸²à¹à¸à¸£à¸
        except Exception as e:
            alert_error(str(e))
        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    run()
