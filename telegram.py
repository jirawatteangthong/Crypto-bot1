from utils import send_telegram_message

def notify_start(): send_telegram_message("Bot Started.")
def notify_entry(side, price): send_telegram_message(f"ENTRY: {side.upper()} at {price}")
def notify_exit(side, price, result): send_telegram_message(f"EXIT: {side.upper()} at {price} with {result}")
def notify_sl_move(new_sl): send_telegram_message(f"SL moved to breakeven: {new_sl}")
def notify_health(pairs): send_telegram_message(f"Health check: {', '.join(pairs)}")
def notify_error(err): send_telegram_message(f"ERROR: {err}")
