import requests
import time
import logging
from datetime import datetime

# OKX API 基礎網址
BASE_URL = "https://www.okx.com/api/v5"

def get_usdt_swap_instruments(retries=3):
    """
    取得所有 OKX 上結算幣種為 USDT 的永續合約 (SWAP) 列表。
    """
    url = f"{BASE_URL}/public/instruments"
    params = {
        "instType": "SWAP"
    }
    
    symbols = []
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == "0" and "data" in data:
                    for item in data["data"]:
                        if item.get("settleCcy") == "USDT":
                            symbols.append(item.get("instId"))
                    return symbols
                else:
                    logging.warning(f"取得 Instruments 失敗。API 回應：{data.get('msg')}")
            else:
                logging.warning(f"取得 Instruments 失敗。狀態碼：{response.status_code}")
        except requests.exceptions.RequestException as e:
            logging.warning(f"取得 Instruments 發生網路錯誤：{e}")
        except Exception as e:
            logging.error(f"取得 Instruments 發生意外錯誤：{e}")
            
        if attempt < retries - 1:
            time.sleep(1)
            
    return symbols

def get_swap_tickers(retries=3):
    """
    取得所有 SWAP 合約的 24h Ticker 資料。
    回傳字典格式: {"BTC-USDT-SWAP": {"instId": "...", "last": ..., "vol24h": ..., "volCcy24h": ..., "quote_volume_usdt": ...}, ...}
    """
    url = f"{BASE_URL}/market/tickers"
    params = {
        "instType": "SWAP"
    }
    
    tickers = {}
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == "0" and "data" in data:
                    for item in data["data"]:
                        inst_id = item.get("instId", "")
                        if inst_id.endswith("-USDT-SWAP"):
                            try:
                                last = float(item.get("last", 0))
                                vol24h = float(item.get("vol24h", 0))
                                volCcy24h = float(item.get("volCcy24h", 0))
                                quote_volume_usdt = volCcy24h * last
                                
                                tickers[inst_id] = {
                                    "instId": inst_id,
                                    "last": last,
                                    "vol24h": vol24h,
                                    "volCcy24h": volCcy24h,
                                    "quote_volume_usdt": quote_volume_usdt
                                }
                            except ValueError:
                                pass
                    return tickers
                else:
                    logging.warning(f"取得 Tickers 失敗。API 回應：{data.get('msg')}")
            else:
                logging.warning(f"取得 Tickers 失敗。狀態碼：{response.status_code}")
        except requests.exceptions.RequestException as e:
            logging.warning(f"取得 Tickers 發生網路錯誤：{e}")
        except Exception as e:
            logging.error(f"取得 Tickers 發生意外錯誤：{e}")
            
        if attempt < retries - 1:
            time.sleep(1)
            
    return tickers

def get_latest_candle(symbol, timeframe="5m", retries=3):
    """
    取得指定交易對的最新一根 K 線資料。
    回傳格式: (candle_data_list, readable_time_string) 或 (None, None)
    """
    url = f"{BASE_URL}/market/candles"
    params = {
        "instId": symbol,
        "bar": timeframe,
        "limit": "1"
    }
    
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == "0" and data.get("data"):
                    # OKX 格式: [ts, o, h, l, c, vol, volCcy, volCcyQuote, confirm]
                    candle = data["data"][0]
                    
                    # 將時間戳(毫秒)轉換為可讀格式
                    ts_ms = int(candle[0])
                    dt_obj = datetime.fromtimestamp(ts_ms / 1000)
                    readable_time = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
                    
                    return candle, readable_time
                else:
                    return None, None
            else:
                pass # 可能是限速或網路錯誤
                
        except requests.exceptions.RequestException as e:
            if attempt == retries - 1:
                logging.warning(f"取得 {symbol} K 線網路錯誤：{e}")
        except Exception as e:
            if attempt == retries - 1:
                logging.error(f"取得 {symbol} K 線時發生意外錯誤：{e}")
                
        if attempt < retries - 1:
            time.sleep(1)
            
    return None, None
