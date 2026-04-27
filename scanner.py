import time
from config import MIN_24H_VOLUME_USDT, ALERT_THRESHOLD_PCT, TIMEFRAME
from okx_client import get_usdt_swap_instruments, get_latest_candle, get_swap_tickers
from discord_notifier import send_discord_message

def filter_by_24h_volume(symbols):
    """
    透過 24 小時交易額篩選交易對
    """
    print(f"\n📊 正在進行 24h 交易額流動性篩選 (門檻：{MIN_24H_VOLUME_USDT:,} USDT)...")
    tickers = get_swap_tickers()
    
    filtered_symbols = []
    skipped_count = 0
    missing_vol_count = 0
    
    # 增加 Debug 檢查
    for test_symbol in ["BTC-USDT-SWAP", "ETH-USDT-SWAP"]:
        if test_symbol in tickers:
            t = tickers[test_symbol]
            print(f"\nSymbol: {test_symbol}")
            print(f"last: {t.get('last')}")
            print(f"vol24h_contracts: {t.get('vol24h')}")
            print(f"volCcy24h_base: {t.get('volCcy24h')}")
            print(f"calculated_quote_volume_usdt: {t.get('quote_volume_usdt'):,.2f}")
    print("-" * 40)
    
    for symbol in symbols:
        # 確保結尾是 -USDT-SWAP (防呆)
        if not symbol.endswith("-USDT-SWAP"):
            continue
            
        ticker = tickers.get(symbol)
        if not ticker or "quote_volume_usdt" not in ticker:
            print(f"Skip {symbol}: missing valid 24h quote volume")
            missing_vol_count += 1
            continue
            
        vol_usdt = ticker.get("quote_volume_usdt")
        
        if vol_usdt < MIN_24H_VOLUME_USDT:
            print(f"Skip {symbol}: 24h quote volume {vol_usdt:,.0f} USDT below {MIN_24H_VOLUME_USDT:,.0f} USDT")
            skipped_count += 1
        else:
            filtered_symbols.append(symbol)
            # 通過篩選時新增 debug summary
            if symbol in ["BTC-USDT-SWAP", "ETH-USDT-SWAP"]:
                print(f"{symbol} quote volume: {vol_usdt:,.0f} USDT")
            
    print("-" * 40)
    print("--- 篩選結果 ---")
    total_original = len(symbols)
    print(f"全部 USDT-SWAP 數量: {total_original}")
    print(f"因交易額不足篩除數量: {skipped_count}")
    if missing_vol_count > 0:
        print(f"因缺失資料篩除數量: {missing_vol_count}")
    print(f"通過數量: {len(filtered_symbols)}")
    print("-" * 40)
    
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
    print("🔍 開始向 OKX 獲取 USDT 永續合約列表...")
    symbols = get_usdt_swap_instruments()
    
    total_symbols = len(symbols)
    if total_symbols == 0:
        print("❌ 無法取得交易對列表，結束掃描。")
        return
        
    print(f"✅ 成功取得 {total_symbols} 個交易對，準備進行流動性篩選...")
    
    # 加入流動性篩選
    filtered_symbols = filter_by_24h_volume(symbols)
    total_filtered = len(filtered_symbols)
    
    if total_filtered == 0:
        print("❌ 沒有任何交易對通過流動性篩選，結束掃描。")
        return
        
    print(f"\n🚀 準備開始掃描 {total_filtered} 個交易對的 {TIMEFRAME} K線 (門檻：>= {ALERT_THRESHOLD_PCT}%)")
    print("-" * 40)
    
    triggered_count = 0
    
    # 遍歷篩選後的交易對
    for index, symbol in enumerate(filtered_symbols, start=1):
        # 簡單顯示掃描進度，覆蓋同一行
        print(f"\r[{index}/{total_filtered}] Scanning {symbol}...{' ' * 10}", end="", flush=True)
        
        # 取得最新一根 K 線
        candle, readable_time = get_latest_candle(symbol, timeframe=TIMEFRAME)
        
        if candle:
            try:
                # 取得各項數值並轉為浮點數
                open_price = float(candle[1])
                high_price = float(candle[2])
                low_price = float(candle[3])
                close_price = float(candle[4])
                volume = float(candle[5])
                
                # 若開盤價為 0 則略過以避免除以零的錯誤
                if open_price > 0:
                    # 計算漲幅與震盪幅度
                    change_pct = (close_price - open_price) / open_price * 100
                    volatility_pct = (high_price - low_price) / open_price * 100
                    
                    # 判斷觸發條件
                    alert_titles = []
                    if change_pct >= ALERT_THRESHOLD_PCT:
                        alert_titles.append("🚀 Pump Alert")
                    elif change_pct <= -ALERT_THRESHOLD_PCT:
                        alert_titles.append("🔻 Dump Alert")
                        
                    if volatility_pct >= ALERT_THRESHOLD_PCT:
                        alert_titles.append("⚡ Volatility Alert")
                        
                    if alert_titles:
                        # 組合標題與連結
                        combined_title = " + ".join(alert_titles)
                        okx_url = build_okx_swap_url(symbol)
                        
                        # 在 Terminal 顯示詳細警報資訊 (先換行清除進度條)
                        print(f"\n\n🔥 Alert triggered!")
                        print(f"Symbol: {symbol}")
                        print(f"Type: {combined_title}")
                        print(f"Change: {change_pct:.2f}%")
                        print(f"Volatility: {volatility_pct:.2f}%")
                        print(f"OKX Link: {okx_url}")
                        
                        # 組合 Discord 訊息內容
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
                        
                        send_discord_message(msg)
                        triggered_count += 1
            except Exception as e:
                # 數值轉換錯誤或例外
                print(f"\n⚠️ 處理 {symbol} 資料時發生錯誤：{e}")
        
        # 加上 sleep 保護機制，避免被 API 封鎖 (設定 0.2 秒算安全)
        time.sleep(0.2)
        
    print("\n" + "-" * 40)
    print(f"🎉 掃描結束！共掃描 {total_filtered} 個交易對，觸發了 {triggered_count} 次警報。")

if __name__ == "__main__":
    start_scan()
