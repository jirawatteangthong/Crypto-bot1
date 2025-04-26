# === config.py ===

# API OKX
API_KEY = '0659b6f2-c86a-466a-82ec-f1a52979bc33'
API_SECRET = 'CCB0A67D53315671F599050FCD712CD1'
API_PASSPHRASE = 'Jirawat1-'

# Telegram
TELEGRAM_TOKEN = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
TELEGRAM_CHAT_ID = '8104629569'

# Trading Setup
SYMBOL = 'BTC-USDT-SWAP'
BASE_CAPITAL = 20  # เริ่มต้น 20 USDT
WITHDRAW_THRESHOLD = 3  # ถอนกำไรทุก 3 ไม้
TP_SL_RISK_REWARD = 2  # Risk : Reward 1:2
DAILY_TRADE_LIMIT = 1  # จำกัดเข้าแค่ 1 ไม้ต่อวัน

# Leverage (จะปรับตาม Risk Management ใน main.py)
DEFAULT_LEVERAGE = 20

# EMA Settings
EMA_TF = '1h'    # ใช้ H1
EMA_PERIOD = 50  # EMA50 ไว้ดูเทรนด์

# Timeframes สำหรับหา Order Block / POI
SWING_TF = '15m'  # ใช้ M15 หา Swing High/Low
ENTRY_TF = '1m'   # ใช้ M1 หา Entry ที่แม่นยำ

# Risk Settings
RISK_PER_TRADE_PCT = 0.03  # เสี่ยงต่อไม้แค่ 3%

# config.py
BOT_TOKEN = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
CHAT_ID = '8104629569'

DAILY_MAX_TRADES = 1  # เทรดได้ 1 ไม้ต่อวัน
CHECK_INTERVAL = 60   # เช็กสัญญาณทุกๆ 60 วินาที

