import time
from config import *
from strategy import get_fibo_zone
from entry import check_entries
from order import open_trade, monitor_trades, reset_daily_counter
from telegram import health_check
from utils import is_new_day

capital = START_CAPITAL
last_health = time.time()
daily_trades = 0

while True:
    if is_new_day():
        daily_trades = 0
        reset_daily_counter()

    if daily_trades < 2:
        fibo, trend = get_fibo_zone()
        if fibo:
            entries = check_entries(fibo)
            for signal in entries:
                capital = open_trade(signal, capital)
                daily_trades += 1
                if daily_trades >= 2:
                    break

    monitor_trades(capital)

    if time.time() - last_health >= HEALTH_CHECK_HOURS * 3600:
        health_check(capital)
        last_health = time.time()

    time.sleep(CHECK_INTERVAL)
