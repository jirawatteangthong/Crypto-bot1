import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

sent_start_alert = False

def alert_start():
    global sent_start_alert
    if not sent_start_alert:
        send_telegram("✅ บอทเริ่มทำงานแล้ว")
        sent_start_alert = True

sent_flags = {
    'start': False,
    'choch_m15': None,
    'fibo_drawn': None,
    'zone_alert': False,
    'error': False
}

def notify(message):
    try:
        requests.post(
            f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage',
            json={'chat_id': TELEGRAM_CHAT_ID, 'text': message}
        )
    except:
        pass

def alert_start():
    if not sent_flags['start']:
        notify("[START] Bot started")
        sent_flags['start'] = True

def alert_choch_m15(direction):
    if sent_flags['choch_m15'] != direction:
        notify(f"[M15 CHoCH] Detected: {direction.upper()}")
        sent_flags['choch_m15'] = direction

def alert_fibo_drawn(low, high):
    key = f"{low}-{high}"
    if sent_flags['fibo_drawn'] != key:
        notify(f"[FIBO DRAWN]
Low = {low}
High = {high}")
        sent_flags['fibo_drawn'] = key

def alert_price_in_zone():
    if not sent_flags['zone_alert']:
        notify("[ALERT] Price entered Fibo zone - Waiting for M1 CHoCH")
        sent_flags['zone_alert'] = True

def alert_error(msg):
    if not sent_flags['error']:
        notify(f"[ERROR] {msg}")
        sent_flags['error'] = True

def reset_flags():
    sent_flags['zone_alert'] = False
    sent_flags['error'] = False
