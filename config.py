import os
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

# Discord Webhook 設定
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# 最小 24 小時交易額門檻 (USDT)
MIN_24H_VOLUME_USDT = 5_000_000

# 檢查必要的設定是否存在
if not DISCORD_WEBHOOK_URL:
    print("❌ 錯誤：找不到 DISCORD_WEBHOOK_URL。請檢查 .env 檔案中是否已設定。")
    # 不在這裡中斷程式，讓其他模組自行決定如何處理

# 警報門檻與時間週期
ALERT_THRESHOLD_PCT = 2.0
TIMEFRAME = "5m"
