import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

flags = {
    'choch_alerted': False,
    'zone_alerted': False,
    'fibo_alerted': False,
    'started': False
}

def send_telegram_message(text):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': text}
    requests.post(url, data=data)

def alert_start():
    if not flags['started']:
        send_telegram_message('บอทเริ่มทำงานแล้ว')
        flags['started'] = True

def alert_choch_m15():
    if not flags['choch_alerted']:
        send_telegram_message('[CHoCH] เกิด CHoCH ใน M15')
        flags['choch_alerted'] = True

def alert_fibo_drawn(low, high):
    if not flags['fibo_alerted']:
        send_telegram_message(f'[FIBO] วาด Fibonacci ใหม่: Low={low}, High={high}')
        flags['fibo_alerted'] = True

def alert_price_in_zone():
    if not flags['zone_alerted']:
        send_telegram_message('[ZONE] ราคาเข้าโซน Fibonacci แล้ว รอ CHoCH ใน M1')
        flags['zone_alerted'] = True

def alert_error(e):
    send_telegram_message(f'[ERROR] {e}')

def reset_flags():
    flags['choch_alerted'] = False
    flags['zone_alerted'] = False
    flags['fibo_alerted'] = False
