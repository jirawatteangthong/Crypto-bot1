from strategy import get_m15_zones
from entry import check_entry_signal
from order import open_trade, monitor_trade
from telegram import health_check
import time

capital = 49.0
last_health = time.time()

while True:
    zones, trend = get_m15_zones()
    signal = check_entry_signal(zones, trend)
    if signal:
        capital, _, _ = open_trade(signal, capital)
    monitor_trade()
    if time.time() - last_health >= 3600:
        health_check(capital)
        last_health = time.time()
    time.sleep(30)
