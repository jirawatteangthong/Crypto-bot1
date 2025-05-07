import time
from strategy import get_m15_zones
from entry import check_entry_signal
from order import open_trade, monitor_trade, has_any_order
from telegram import health_check
from config import *

capital = START_CAPITAL
last_health = time.time()

while True:
    if not has_any_order():
        zones, trend = get_m15_zones()
        signal = check_entry_signal(zones, trend)
        if signal:
            capital, _, _ = open_trade(signal, capital)
    monitor_trade()
    if time.time() - last_health >= HEALTH_CHECK_HOURS * 3600:
        health_check(capital)
        last_health = time.time()
    time.sleep(CHECK_INTERVAL)
