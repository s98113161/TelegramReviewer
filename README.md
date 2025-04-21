# Telegram 群組熱門訊息分析工具

這個工具可協助您分析 Telegram 群組的聊天內容，找出表情符號反應總數最高的熱門訊息，並提供詳細的訊息統計分析。

## 🚀 主要功能

- ✨ 互動式命令列介面，輕鬆選擇要分析的群組/頻道
- 📊 分析所有表情符號反應總和最高的熱門訊息
- 📈 統計每個表情符號的使用頻率和分佈情況
- 👥 分析使用者活躍度和訊息時間分佈
- 🔄 自動轉發熱門訊息到專屬儲存群組
- ⏱️ 支援自訂分析的時間範圍和訊息數量
- 🔝 支援自訂顯示的熱門訊息數量
- 📂 支援將分析結果保存為 JSON 檔案
- 🤖 提供一鍵環境設定與定時執行腳本

## 📋 快速開始

### 自動化設定（推薦）

使用提供的設定腳本快速完成環境配置和定時任務設定：

```bash
# 賦予腳本執行權限
chmod +x setup_and_schedule.sh

# 執行設定腳本
./setup_and_schedule.sh
```

依照腳本提示設定分析參數、定時執行頻率，並可選擇立即執行一次分析。

### 環境設置

1. 克隆此專案：
```bash
git clone https://github.com/yourusername/TelegramReviewer.git
cd TelegramReviewer
```

2. 安裝所需依賴：
```bash
pip install -r requirements.txt
```

3. 設置環境變數：
   - 在專案根目錄建立 `.env` 檔案
   - 從 [Telegram API 開發者網站](https://my.telegram.org/apps) 獲取 API_ID 和 API_HASH
   - 填入您的 API 憑證和手機號碼

```bash
# .env 檔案內容範例
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
PHONE=+886912345678
```

## 💻 使用方法

### 手動執行

```bash
python telegram_reviewer.py [參數]
```

### 常用命令行參數

```bash
# 分析最近 14 天的訊息
python telegram_reviewer.py --days 14

# 顯示 10 條熱門訊息
python telegram_reviewer.py --top 10

# 保存分析結果為 JSON 檔案
python telegram_reviewer.py --save

# 使用上次選擇的群組，不再詢問
python telegram_reviewer.py --use-history yes

# 從特定日期開始分析
python telegram_reviewer.py --start-date 20250410

# 組合使用多個參數
python telegram_reviewer.py --days 7 --top 10 --save --use-history yes
```

### 參數完整說明

| 參數 | 說明 | 預設值 |
|------|------|--------|
| `--days` | 要分析的最近天數 | 30 |
| `--start-date` | 分析起始日期 (格式: YYYYMMDD) | 無 |
| `--limit` | 要分析的訊息數量上限 | 1000 |
| `--top` | 顯示和轉發的熱門訊息數量 | 5 |
| `--save` | 將分析結果保存為 JSON 檔案 | 否 |
| `--use-history` | 使用上次選擇的群組 (yes/no/ask) | ask |

## 🔍 使用流程

1. **初次設置**：
   - 執行 `setup_and_schedule.sh` 腳本或手動安裝依賴
   - 設置 Telegram API 憑證

2. **登入驗證**：
   - 首次運行時，系統會要求您驗證 Telegram 帳號
   - 輸入收到的驗證碼完成登入

3. **選擇群組**：
   - 程式會顯示您帳號下的所有群組和頻道
   - 使用方向鍵選擇，空格鍵選取（可多選）
   - 按 Enter 確認選擇

4. **訊息分析**：
   - 系統自動抓取並分析選定群組的訊息
   - 計算表情符號反應、活躍度和訊息分佈

5. **結果輸出**：
   - 在終端機顯示熱門訊息、統計資料和分析圖表
   - 自動轉發熱門訊息到儲存群組（如已設定）
   - 選擇性保存分析結果為 JSON 檔案

## 📱 熱門訊息轉發功能

### 轉發流程

1. **初次設定**：
   - 系統會詢問是否創建專用儲存群組
   - 可選擇現有群組或創建新群組

2. **訊息組織**：
   - 按分析時間和群組分類訊息
   - 每則訊息附帶排名和反應數量資訊
   - 保留原始媒體內容和發送者資訊

3. **自訂設定**：
   - 可隨時更改預設儲存群組
   - 在配置檔案中調整轉發行為

## 📁 專案結構

```
TelegramReviewer/
├── README.md                          # 專案說明文件
├── requirements.txt                   # 相依套件清單
├── setup_and_schedule.sh              # 環境設定與定時執行腳本
├── telegram_reviewer_history.json     # 歷史分析記錄
├── telegram_reviewer_session.session  # Telegram 登入會話檔案
├── telegram_reviewer.py               # 主程式入口點
├── config/                            # 配置模組
├── data/                              # 資料模組
├── logs/                              # 日誌資料夾
├── results/                           # 分析結果資料夾
└── src/                               # 原始碼資料夾
```

## 📌 注意事項

- 首次運行需要 Telegram 驗證登入
- 登入資訊保存在 session 檔案中，下次自動使用
- 請遵守 Telegram 使用條款
- 避免短時間內頻繁抓取大量訊息
- 您必須是群組/頻道成員才能讀取訊息
- 操作日誌記錄在 `logs/` 資料夾中

## 💻 系統需求

- Python 3.7 或更高版本
- 必要套件：
  - telethon >= 1.32.1
  - python-dotenv >= 1.0.0
  - pandas >= 2.0.0
- 有效的 Telegram 帳號與 API 憑證