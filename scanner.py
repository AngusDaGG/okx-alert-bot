import time
import json
import os
import logging
from datetime import datetime
from config import MIN_24H_VOLUME_USDT, ALERT_THRESHOLD_PCT, TIMEFRAME, ALERT_COOLDOWN_MINUTES
from okx_client import get_usdt_swap_instruments, get_latest_candle, get_swap_tickers
from discord_notifier import send_discord_message

STATE_FILE = "state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"讀取 state.json 失敗: {e}")
            return {}
    return {}

def save_state(state):
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
    except Exception as e:
        logging.error(f"儲存 state.json 失敗: {e}")

def filter_by_24h_volume(symbols):
    """
    透過 24 小時交易額篩選交易對
    """
    logging.info(f"正在進行 24h 交易額流動性篩選 (門檻：{MIN_24H_VOLUME_USDT:,} USDT)...")
    tickers = get_swap_tickers()
    
    filtered_symbols = []
    skipped_count = 0
    missing_vol_count = 0
    
    for symbol in symbols:
        if not symbol.endswith("-USDT-SWAP"):
            continue
            
        ticker = tickers.get(symbol)
        if not ticker or "quote_volume_usdt" not in ticker:
            missing_vol_count += 1
            continue
            
        vol_usdt = ticker.get("quote_volume_usdt")
        
        if vol_usdt < MIN_24H_VOLUME_USDT:
            skipped_count += 1
        else:
            filtered_symbols.append(symbol)
            
    logging.info("--- 篩選結果 ---")
    total_original = len(symbols)
    logging.info(f"全部 USDT-SWAP 數量: {total_original}")
    logging.info(f"因交易額不足篩除數量: {skipped_count}")
    if missing_vol_count > 0:
        logging.info(f"因缺失資料篩除數量: {missing_vol_count}")
    logging.info(f"通過數量: {len(filtered_symbols)}")
    logging.info("-" * 40)
    
    return filtered_symbols

def build_okx_swap_url(symbol):
    """
    產生 OKX 永續合約交易頁面連結
    """
    return f"https://www.okx.com/trade-swap/{symbol.lower()}"

def start_scan():
    """
    開始執行全市場掃描流程。
    """
    logging.info("開始向 OKX 獲取 USDT 永續合約列表...")
    symbols = get_usdt_swap_instruments()
    
    total_symbols = len(symbols)
    if total_symbols == 0:
        logging.error("無法取得交易對列表，結束掃描。")
        return
        
    logging.info(f"成功取得 {total_symbols} 個交易對，準備進行流動性篩選...")
    
    filtered_symbols = filter_by_24h_volume(symbols)
    total_filtered = len(filtered_symbols)
    
    if total_filtered == 0:
        logging.warning("沒有任何交易對通過流動性篩選，結束掃描。")
        return
        
    logging.info(f"準備開始掃描 {total_filtered} 個交易對的 {TIMEFRAME} K線 (門檻：>= {ALERT_THRESHOLD_PCT}%)")
    
    triggered_count = 0
    state = load_state()
    current_time = time.time()
    
    for symbol in filtered_symbols:
        # Check cooldown
        last_alert = state.get(symbol, 0)
        if current_time - last_alert < ALERT_COOLDOWN_MINUTES * 60:
            # 仍在冷卻期，略過
            continue
            
        candle, readable_time = get_latest_candle(symbol, timeframe=TIMEFRAME)
        
        if candle:
            try:
                open_price = float(candle[1])
                high_price = float(candle[2])
                low_price = float(candle[3])
                close_price = float(candle[4])
                volume = float(candle[5])
                
                if open_price > 0:
                    change_pct = (close_price - open_price) / open_price * 100
                    volatility_pct = (high_price - low_price) / open_price * 100
                    
                    alert_titles = []
                    if change_pct >= ALERT_THRESHOLD_PCT:
                        alert_titles.append("🚀 Pump Alert")
                    elif change_pct <= -ALERT_THRESHOLD_PCT:
                        alert_titles.append("🔻 Dump Alert")
                        
                    if volatility_pct >= ALERT_THRESHOLD_PCT:
                        alert_titles.append("⚡ Volatility Alert")
                        
                    if alert_titles:
                        combined_title = " + ".join(alert_titles)
                        okx_url = build_okx_swap_url(symbol)
                        
                        logging.info(f"🔥 Alert triggered! Symbol: {symbol}, Type: {combined_title}, Change: {change_pct:.2f}%, Volatility: {volatility_pct:.2f}%")
                        
                        msg = (
                            f"{combined_title}\n\n"
                            f"Symbol: {symbol}\n"
                            f"Timeframe: {TIMEFRAME}\n"
                            f"Change: {change_pct:.2f}%\n"
                            f"Volatility: {volatility_pct:.2f}%\n\n"
                            f"Open: {open_price}\n"
                            f"High: {high_price}\n"
                            f"Low: {low_price}\n"
                            f"Close: {close_price}\n"
                            f"Volume: {volume}\n\n"
                            f"OKX Link: {okx_url}"
                        )
                        
                        if send_discord_message(msg):
                            state[symbol] = current_time
                            save_state(state)
                            triggered_count += 1
            except Exception as e:
                logging.error(f"處理 {symbol} 資料時發生錯誤：{e}")
        
        # 增加極短的間隔避免過度密集呼叫，減少 Rate Limit
        time.sleep(0.05)
        
    logging.info(f"掃描結束！共掃描 {total_filtered} 個交易對，觸發了 {triggered_count} 次警報。")

if __name__ == "__main__":
    # If run directly for testing
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    start_scan()
