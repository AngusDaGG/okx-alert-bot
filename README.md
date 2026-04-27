# Alert Bot

這是一個基於 Python 的通知機器人專案。

## 如何啟動虛擬環境

如果你使用 Windows（PowerShell）：
```powershell
.\.venv\Scripts\activate
```

如果你使用 Mac / Linux：
```bash
source .venv/bin/activate
```

*(啟動後你的命令提示字元前面會出現 `(.venv)`)*

## 如何安裝套件

啟動虛擬環境後，執行以下指令安裝所需套件：
```powershell
pip install -r requirements.txt
```

## 如何設定環境變數

1. 複製 `.env.example` 並將新檔案命名為 `.env`
2. 在 `.env` 檔案中填寫你的 API Keys 和 Webhook URL

## 如何執行

啟動虛擬環境並安裝好套件後，執行：
```powershell
python main.py
```
