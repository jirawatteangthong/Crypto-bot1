from strategy import get_m15_zones
from entry import check_entry_signal
from order import open_trade, monitor_trade, has_open_position
from telegram import health_check, notify
import time

capital = 49.0
last_health = time.time()
last_5h_check = time.time()

print("=== BOT STARTED ===")

while True:
    try:
        print("[LOOP] Checking for trade setup...")

        if has_open_position():
            print("[INFO] Already in position. Skipping new entries.")
        else:
            zones, trend = get_m15_zones()
            print(f"[STRATEGY] Trend: {trend}, Zones: {zones}")

            signal = check_entry_signal(zones, trend)
            if signal:
                print(f"[ENTRY SIGNAL] {signal}")
                capital, _, _ = open_trade(signal, capital)
            else:
                print("[ENTRY] No valid signal")

        monitor_trade()

        if time.time() - last_health >= 3600:
            print("[HEALTH] Sending health check...")
            health_check(capital)
            last_health = time.time()

        if time.time() - last_5h_check >= 5 * 3600:
            print("[ALERT] 5-hour check")
            notify("[STATUS] BOT STILL RUNNING after 5 hours")
            last_5h_check = time.time()

        time.sleep(30)

    except Exception as e:
        print("[ERROR]", e)
        notify(f"[ERROR] BOT crash: {str(e)}")
        time.sleep(60)
