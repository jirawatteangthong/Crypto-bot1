from datetime import datetime

def get_today():
    return datetime.now().strftime('%Y-%m-%d')

def sleep_until_next_candle(timeframe='5m'):
    tf_sec = {'5m': 300, '1m': 60}
    t = tf_sec.get(timeframe, 300)
    now = time.time()
    sleep_sec = t - (now % t)
    time.sleep(sleep_sec)
