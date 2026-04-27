import sys
from scanner import start_scan

def main():
    print("=" * 40)
    print("🚀 OKX 全市場掃描警報機器人啟動")
    print(f"🐍 Python version: {sys.version.split(' ')[0]}")
    print("=" * 40)
    
    # 執行掃描邏輯
    start_scan()
    
    print("✅ 程式執行完畢。")

if __name__ == "__main__":
    main()
