import time
from config import *
from strategy import get_m15_zones
from entry import check_entry_signal
from order import open_trade, monitor_trade
from telegram import health_check
from utils import is_new_day

capital = START_CAPITAL
last_health = time.time()
has_position = False

while True:
    if not has_position:
        zones, trend = get_m15_zones()
        signal = check_entry_signal(zones, trend)
        if signal:
            capital, has_position = open_trade(signal, capital)

    has_position = monitor_trade(capital)

    if time.time() - last_health >= HEALTH_CHECK_HOURS * 3600:
        health_check(capital)
        last_health = time.time()
    time.sleep(CHECK_INTERVAL)
