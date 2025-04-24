import ccxt
import time
import pandas as pd
import numpy as np
import logging
import requests
from telegram import Bot
from datetime import datetime

# ====== CONFIG ======
API_KEY = '0659b6f2-c86a-466a-82ec-f1a52979bc33'
API_SECRET = 'CCB0A67D53315671F599050FCD712CD1'
API_PASSPHRASE = 'Jirawat1-'
TELEGRAM_TOKEN = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
TELEGRAM_CHAT_ID = '8104629569'
SYMBOL = 'BTC-USDT-SWAP'
LEVERAGE = 20
START_CAPITAL = 20  # USDT
RISK_REWARD = 2
TP_REACHED_BE_PERCENT = 0.5  # 50%
TIMEFRAMES = {'H4': '4h', 'M15': '15m', 'M1': '1m'}

# ====== INIT ======
bot = Bot(token=TELEGRAM_TOKEN)

okx = ccxt.okx({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSPHRASE,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ====== UTILS ======
def send_telegram(msg):
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
    except Exception as e:
        print(f"Telegram error: {e}")

def get_ohlcv_safe(symbol, timeframe, limit=100):
    for _ in range(5):
        try:
            data = okx.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logger.warning(f"fetch_ohlcv error: {e}, retrying...")
            time.sleep(2)
    raise Exception(f"Failed to get OHLCV for {symbol}")

def get_macd(df, fast=12, slow=26, signal=9):
    df['ema_fast'] = df['close'].ewm(span=fast, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=slow, adjust=False).mean()
    df['macd'] = df['ema_fast'] - df['ema_slow']
    df['signal'] = df['macd'].ewm(span=signal, adjust=False).mean()
    return df

def calculate_std_channel(df, mult=2):
    mean = df['close'].rolling(20).mean()
    std = df['close'].rolling(20).std()
    df['upper'] = mean + mult * std
    df['lower'] = mean - mult * std
    return df

def set_leverage(leverage):
    try:
        okx.set_leverage(leverage, SYMBOL, {'marginMode': 'cross'})
    except Exception as e:
        send_telegram(f"Error setting leverage: {e}")

# ====== STRATEGY CHECK ======
def check_h4_trend():
    df = get_ohlcv_safe(SYMBOL, TIMEFRAMES['H4'], 100)
    return 'bullish' if df['close'].iloc[-1] > df['close'].iloc[-2] else 'bearish'

def find_poi(df):
    return df['low'].iloc[-5] if check_h4_trend() == 'bullish' else df['high'].iloc[-5]

def check_entry():
    trend = check_h4_trend()
    df_15 = get_ohlcv_safe(SYMBOL, TIMEFRAMES['M15'], 50)
    df_1 = get_ohlcv_safe(SYMBOL, TIMEFRAMES['M1'], 50)
    poi = find_poi(df_15)
    df_1 = get_macd(df_1)
    df_1 = calculate_std_channel(df_1)

    price = df_1['close'].iloc[-1]
    macd_cross = df_1['macd'].iloc[-2] < df_1['signal'].iloc[-2] and df_1['macd'].iloc[-1] > df_1['signal'].iloc[-1]
    in_std_range = df_1['lower'].iloc[-1] < price < df_1['upper'].iloc[-1]

    if trend == 'bullish' and price <= poi and macd_cross and in_std_range:
        return 'buy', price, poi
    elif trend == 'bearish' and price >= poi and macd_cross and in_std_range:
        return 'sell', price, poi
    return None, None, None

# ====== ORDER MANAGER ======
def place_order(direction, entry_price, capital):
    size = round((capital * LEVERAGE) / entry_price, 3)
    sl = round(entry_price * (0.99 if direction == 'buy' else 1.01), 2)
    tp = round(entry_price * (1 + 0.02) if direction == 'buy' else entry_price * (1 - 0.02), 2)
    side = 'buy' if direction == 'buy' else 'sell'

    try:
        order = okx.create_market_order(SYMBOL, side, size)
        time.sleep(1)
        okx.private_post_trade_order_algo({
            'instId': SYMBOL,
            'tdMode': 'cross',
            'side': 'sell' if side == 'buy' else 'buy',
            'ordType': 'oco',
            'sz': size,
            'tpTriggerPx': str(tp),
            'tpOrdPx': '-1',
            'slTriggerPx': str(sl),
            'slOrdPx': '-1'
        })
        send_telegram(f"à¹à¸à¹à¸²à¸­à¸­à¹à¸à¸­à¸£à¹: {side.upper()}\nSize: {size}\nEntry: {entry_price}\nTP: {tp}\nSL: {sl}")
        return True
    except Exception as e:
        send_telegram(f"Error placing order: {e}")
        return False

# ====== MAIN LOOP ======
def run_bot():
    send_telegram("à¸à¸­à¸à¹à¸£à¸´à¹à¸¡à¸à¸³à¸à¸²à¸à¹à¸¥à¹à¸§")
    capital = START_CAPITAL
    win_count = 0

    while True:
        try:
            positions = okx.fetch_positions([SYMBOL])
            open_pos = [p for p in positions if float(p['contracts']) > 0]
            if not open_pos:
                direction, entry_price, poi = check_entry()
                if direction:
                    send_telegram(f"Trend H4: {check_h4_trend()}\nPOI: {poi}\nEntry M15: {entry_price}")
                    placed = place_order(direction, entry_price, capital)
                    if placed:
                        time.sleep(30)
                else:
                    send_telegram("à¸£à¸­à¸à¸±à¸à¸«à¸§à¸°à¹à¸à¹à¸²à¸­à¸­à¹à¸à¸­à¸£à¹...")
            else:
                logger.info("à¸­à¸­à¹à¸à¸­à¸£à¹à¸¢à¸±à¸à¹à¸à¸´à¸à¸­à¸¢à¸¹à¹")
            time.sleep(60)
        except Exception as e:
            send_telegram(f"Bot Error: {e}")
            time.sleep(60)

if __name__ == '__main__':
    set_leverage(LEVERAGE)
    run_bot()
