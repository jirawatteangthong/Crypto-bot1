import time, schedule
from okx.MarketData import Market
from okx.Account import Account
from okx.Trade import Trade
from config import *
from strategy import detect_bos_choc, get_fibo_zone
from order import set_leverage, place_entry_order, place_tp_sl_algo, check_open_positions
from telegram import notify_start, notify_entry, notify_sl_move, notify_exit, notify_error, notify_health
from utils import log

market = Market(API_KEY, API_SECRET, PASSPHRASE)
account = Account(API_KEY, API_SECRET, PASSPHRASE)
trade = Trade(API_KEY, API_SECRET, PASSPHRASE)

orders_today = 0
entry_price = 0
breakeven_sl_set = False

notify_start():print("Bot started and notify_start() called")
set_leverage(account)

def run_bot():
    global orders_today, entry_price, breakeven_sl_set

    try:
        pos = check_open_positions(account)
        if pos:
            # Check for breakeven SL
            current_price = float(market.get_ticker(SYMBOL)['last'])
            if not breakeven_sl_set and abs(current_price - entry_price) >= abs(entry_price - float(pos['liqPx'])) / 2:
                new_sl = entry_price
                place_tp_sl_algo(trade, pos['side'], pos['upl'], new_sl)
                breakeven_sl_set = True
                notify_sl_move(new_sl)
            return

        if orders_today >= 2:
            return

        candles = market.get_candlesticks(instId=SYMBOL, bar=TIMEFRAME, limit=CANDLE_LIMIT)['data']
        candles = [{'open': float(c[1]), 'high': float(c[2]), 'low': float(c[3]), 'close': float(c[4])} for c in candles]
        
        bos, choc, trend, swing = detect_bos_choc(candles)
        if bos and choc:
            fibo_618, fibo_786, tp, sl = get_fibo_zone(trend, swing)
            price = float(candles[-1]['close'])

            if fibo_618 < price < fibo_786:
                side = 'buy' if trend == 'up' else 'sell'
                entry_price = price
                place_entry_order(trade, side, POSITION_SIZE)
                place_tp_sl_algo(trade, side, tp, sl)
                notify_entry(side, price)
                orders_today += 1
                breakeven_sl_set = False
    except Exception as e:
        notify_error(str(e))
        log(f"ERROR: {str(e)}")

def reset_day():
    global orders_today
    orders_today = 0

def health():
    notify_health([SYMBOL])

schedule.every(1).hours.do(run_bot)
schedule.every().day.at("00:00").do(reset_day)
schedule.every(6).hours.do(health)

while True:
    schedule.run_pending()
    time.sleep(1)
