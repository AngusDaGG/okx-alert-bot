import sys
import logging
import os
from logging.handlers import RotatingFileHandler
from scanner import start_scan
from dotenv import load_dotenv

def setup_logging():
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # 限制 log 大小最大為 5MB，並保留一個備份
    file_handler = RotatingFileHandler('bot.log', maxBytes=5*1024*1024, backupCount=1)
    file_handler.setFormatter(log_formatter)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

def get_lock():
    lock_file = 'bot.lock'
    try:
        # 使用 os.O_CREAT | os.O_EXCL，如果檔案存在會直接丟出 FileExistsError
        fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        return fd, lock_file
    except FileExistsError:
        return None, lock_file

def release_lock(fd, lock_file):
    if fd is not None:
        os.close(fd)
        try:
            os.remove(lock_file)
        except OSError:
            pass

def main():
    # 讀取環境變數
    load_dotenv()
    setup_logging()
    
    # 獲取 lock 確保不會有兩個 process 同時執行
    fd, lock_file = get_lock()
    if fd is None:
        logging.warning("⚠️ 另一輪掃描正在進行中，或者有 lock file 卡住，本次任務將被跳過。")
        sys.exit(0)
        
    try:
        logging.info("=" * 40)
        logging.info("🚀 OKX 全市場掃描警報機器人啟動 (Cron Mode)")
        logging.info(f"🐍 Python version: {sys.version.split(' ')[0]}")
        logging.info("=" * 40)
        
        # 執行掃描邏輯
        start_scan()
        
        logging.info("✅ 程式執行完畢，釋放資源。")
    except Exception as e:
        logging.error(f"程式執行發生錯誤: {e}", exc_info=True)
    finally:
        release_lock(fd, lock_file)

if __name__ == "__main__":
    main()
