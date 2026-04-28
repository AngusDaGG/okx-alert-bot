import requests
import logging
from config import DISCORD_WEBHOOK_URL

def send_discord_message(content):
    """
    發送訊息到 Discord Webhook
    """
    if not DISCORD_WEBHOOK_URL:
        logging.warning("尚未設定 DISCORD_WEBHOOK_URL，無法發送訊息。")
        return False
        
    payload = {"content": content}
    try:
        # 使用 requests.post 發送 JSON 資料
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        
        # Discord Webhook 成功通常會回傳 204 No Content
        if response.status_code == 204:
            logging.info("Discord 訊息發送成功！")
            return True
        else:
            logging.warning(f"Discord 發送失敗。狀態碼：{response.status_code}")
            logging.warning(f"錯誤內容：{response.text}")
            return False
    except Exception as e:
        logging.error(f"發送 Discord 發生意外錯誤：{e}")
        return False
