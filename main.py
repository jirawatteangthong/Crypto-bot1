import time, datetime
from config import *
from telegram import notify, health_check, trade_notify
from strategy import get_h1_zones
from entry import check_entry_signal
from order import open_trade, monitor_trade
from utils import is_new_day, should_health_check

last_trade_date = None
trade_count = 0
last_health_check = datetime.datetime.utcnow()
capital = START_CAPITAL
win_streak = 0

notify("BOT STARTED")

while True:
    now = datetime.datetime.utcnow()

    if is_new_day(last_trade_date):
        trade_count = 0
        last_trade_date = now.date()
        notify("New day: trade counter reset")

    if should_health_check(last_health_check, HEALTH_CHECK_HOURS):
        last_health_check = now
        health_check(capital)

    if trade_count < DAILY_MAX_TRADES:
        zones = get_h1_zones()
        signal = check_entry_signal(zones)

        if signal:
            capital, result, moved_sl = open_trade(signal, capital)
            monitor_trade(result, moved_sl, capital)
            trade_count += 1
    time.sleep(CHECK_INTERVAL)
