# Telegram 群組熱門訊息分析工具

這個工具可以幫助您分析 Telegram 群組的聊天內容，找出表情符號反應總數最高的熱門訊息，並提供訊息統計分析。

## 主要功能

- 互動式命令列介面，輕鬆選擇要分析的群組/頻道
- 分析所有表情符號反應總和最高的熱門訊息
- 統計每個表情符號的使用頻率
- 分析使用者活躍度和訊息分佈
- 自動轉發熱門訊息到專屬儲存群組
- 支援自訂分析的訊息數量和時間範圍
- 支援自訂顯示的熱門訊息數量
- 支援自動使用上次選擇的群組
- 支援將分析結果保存為 JSON 檔案
- 提供一鍵環境設定與定時執行腳本

## 專案結構

```
TelegramReviewer/
├── README.md                          # 專案說明文件
├── requirements.txt                   # 相依套件清單
├── setup_and_schedule.sh              # 環境設定與定時執行腳本
├── telegram_reviewer_history.json     # 歷史分析記錄
├── telegram_reviewer_session.session  # Telegram 登入會話檔案
├── telegram_reviewer.py               # 主程式入口點
├── config/                            # 配置模組
│   ├── __init__.py
│   ├── settings.py                    # 系統設定
│   └── constants.py                   # 常數定義
├── data/                              # 資料模組
│   ├── __init__.py
│   ├── schemas.py                     # 資料結構定義
│   └── storage.py                     # 本地資料儲存
├── logs/                              # 日誌資料夾
│   └── telegram_reviewer_*.log        # 程式執行日誌
├── results/                           # 分析結果和媒體輸出資料夾
│   └── media/                         # 媒體文件暫存資料夾
└── src/                               # 原始碼資料夾
    ├── __init__.py
    ├── api/                           # API 互動模組
    │   ├── __init__.py
    │   └── telegram_client.py         # Telegram 客戶端管理
    ├── services/                      # 核心業務邏輯模組
    │   ├── __init__.py
    │   ├── message_analyzer.py        # 訊息分析服務
    │   ├── message_fetcher.py         # 訊息獲取服務
    │   └── message_forwarder.py       # 訊息轉發服務
    ├── ui/                            # 使用者介面模組
    │   ├── __init__.py
    │   └── cli.py                     # 命令列介面
    └── utils/                         # 工具類模組
        ├── display_utils.py           # 顯示和格式化工具
        └── logger.py                  # 日誌工具
```

## 安裝

1. 克隆此專案：
```
git clone https://github.com/yourusername/TelegramReviewer.git
cd TelegramReviewer
```

2. 安裝所需依賴：
```
pip install -r requirements.txt
```

3. 設置環境變數：
   - 在專案根目錄建立 `.env` 檔案
   - 從 [Telegram API 開發者網站](https://my.telegram.org/apps) 獲取 API_ID 和 API_HASH
   - 填入您的手機號碼 (國際格式，例如: +886912345678)

**創建 .env 檔案的方法**

在 Linux / macOS 系統：
```bash
# 使用 touch 指令建立空檔案
touch .env

# 使用文字編輯器編輯檔案，例如 nano
nano .env
# 輸入以下內容後，按 Ctrl+X, Y, Enter 保存並退出

# 或使用 echo 指令直接寫入內容
echo 'API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
PHONE=+886912345678' > .env
```

在 Windows 系統：
```cmd
# 使用 type NUL 指令建立空檔案
type NUL > .env

# 也可以使用 echo 指令直接寫入內容
echo API_ID=12345678 > .env
echo API_HASH=abcdef1234567890abcdef1234567890 >> .env
echo PHONE=+886912345678 >> .env

# 或使用記事本編輯
notepad .env
# 將下方內容複製貼上後保存
```

.env 檔案內容範例：
```
# .env 檔案內容範例
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
PHONE=+886912345678
```

獲取 Telegram API 憑證的步驟：
1. 前往 https://my.telegram.org/apps 並登入您的 Telegram 帳號
2. 點擊「API development tools」
3. 填寫表單 (App title、Short name 可以填寫 "TelegramReviewer")
4. 提交後，您將獲得 `api_id` 和 `api_hash`，將這些值複製到 `.env` 檔案中

## 使用方法

### 自動化設定與定時執行（推薦）

專案提供了一個便捷的 shell 腳本 `setup_and_schedule.sh`，可以幫助您一鍵完成環境設定並設置定時執行：

1. 賦予腳本執行權限：
```bash
chmod +x setup_and_schedule.sh
```

2. 執行腳本：
```bash
./setup_and_schedule.sh
```

3. 依照提示進行設定：
   - 選擇要分析的天數
   - 選擇要顯示的熱門訊息數量
   - 選擇是否儲存分析結果
   - 設定定時執行頻率（每天、每週或每月）
   - 選擇是否立即執行一次分析

腳本功能：
- 自動創建 Python 虛擬環境
- 安裝所需依賴套件
- 配置 cron 任務實現定時執行
- 保存配置以便將來重新設定
- 自動使用歷史群組選擇，無需重複選擇

**注意**：如果已經完成設定，再次執行腳本時會詢問是否要註銷舊的設定並重新設定，如果選擇「否」則直接結束腳本。

### 手動執行

執行主程式：
```
./telegram_reviewer.py
```
或
```
python telegram_reviewer.py
```

### 命令行參數

指定分析的訊息時間範圍：
```
python telegram_reviewer.py --days 60
```

指定分析開始日期：
```
python telegram_reviewer.py --start-date 20250410
```

指定分析的訊息數量上限：
```
python telegram_reviewer.py --limit 2000
```

指定顯示的熱門訊息數量：
```
python telegram_reviewer.py --top 10
```

保存分析結果為 JSON 檔案：
```
python telegram_reviewer.py --save
```

使用上次選擇的群組，不再詢問：
```
python telegram_reviewer.py --use-history yes
```

不使用上次選擇的群組，直接顯示群組選擇界面：
```
python telegram_reviewer.py --use-history no
```

同時指定多個參數：
```
python telegram_reviewer.py --days 14 --limit 500 --top 8 --save --use-history yes
```

## 參數說明

- `--days`: 要分析的最近天數（預設: 30）
- `--start-date`: 設定分析的起始日期，格式為 YYYYMMDD (例如: 20250410)
- `--limit`: 要分析的訊息數量上限（預設: 1000）
- `--top`: 顯示和轉發的熱門訊息數量（預設: 5）
- `--save`: 將分析結果保存為 JSON 檔案
- `--use-history`: 是否使用上次選擇的群組
  - `yes`: 直接使用上次選擇的群組，不再詢問
  - `no`: 不使用上次選擇的群組，直接顯示群組選擇界面
  - `ask`: 詢問使用者是否要使用上次選擇的群組（預設值）

## 互動式操作

1. 啟動程式後，會顯示您帳號下的所有群組和頻道
2. 使用方向鍵（↑↓）選擇要分析的群組
3. 使用空格鍵選擇或取消選擇群組（可多選）
4. 按 Enter 確認選擇，或按 q 退出程式
5. 等待程式分析並產生結果

## 輸出結果

分析完成後，程式會：
1. 在終端機中顯示分析摘要，包含：
   - 所有表情符號反應總和最高的熱門訊息
   - 使用者活躍度統計
   - 表情符號使用頻率統計
2. 自動將熱門訊息轉發到一個專屬的 Telegram 儲存群組
3. 如果使用 `--save` 參數，還會將分析結果保存為 JSON 檔案

## 熱門訊息轉發功能詳解

### 轉發機制

本工具會自動將分析出的熱門訊息轉發到一個專屬的 Telegram 儲存群組，具體流程如下：

1. **首次使用轉發功能**：
   - 程式會詢問您是否要創建一個專門用於儲存熱門訊息的群組
   - 如果您選擇「是」，程式會：
     - 請您創建一個新的私人群組（也可以使用現有群組）
     - 將您的 Telegram 機器人帳號加入該群組
     - 將該群組設定為預設的儲存目標
   - 如果您選擇「否」，程式會跳過轉發步驟

2. **轉發過程**：
   - 程式會將您設定的數量（通過 `--top` 參數指定）的熱門訊息轉發到儲存群組
   - 轉發時會保留原始訊息的格式、媒體內容和發送者資訊
   - 每則訊息前會添加排名資訊和獲得的表情符號反應數量
   - 如果訊息含有媒體（圖片、影片等），也會一併轉發

3. **轉發後的組織方式**：
   - 轉發的訊息會按照分析時間分組，每次分析會以一條日期分隔訊息作為標記
   - 標記訊息會包含分析的群組名稱、分析時間範圍和分析的訊息總數
   - 這樣可以讓您輕鬆區分不同時間和不同群組的熱門訊息

### 訊息儲存群組設定

您可以隨時更改默認的儲存群組：

1. 在程式執行過程中選擇「設定轉發目標」選項
2. 程式會顯示您的群組列表，您可以選擇一個新的儲存群組
3. 設定後，未來的熱門訊息將轉發到新選擇的群組

### 轉發功能的優點

- **資料保存**：即使原始訊息在原群組被刪除，您仍有備份
- **集中管理**：所有重要/熱門訊息集中在一個群組，便於查閱
- **定期更新**：通過定時執行，您可以獲得定期更新的熱門訊息摘要
- **訊息追溯**：支援跳轉到原始訊息的連結

### 自訂轉發設定

在 `config/settings.py` 文件中，您可以調整以下轉發相關設定：
- `FORWARD_MESSAGES`：是否啟用轉發功能（預設：True）
- `ASK_FOR_FORWARD_CHAT`：是否每次都詢問轉發目標（預設：False）
- `FORWARD_CHAT_ID`：預設轉發群組的 ID（如已設定）

## 技術細節

- 使用 Telethon 庫與 Telegram API 互動
- 使用 Pandas 進行數據分析
- 模組化設計，便於維護和擴展功能

## 注意事項

1. 首次運行時，Telegram 會要求您進行登入驗證
2. 登入資訊會保存在 `telegram_reviewer_session.session` 檔案中，下次執行時會自動使用
3. 分析結果會保存在 `results/` 資料夾中
4. 使用此工具必須遵守 Telegram 的使用條款
5. 請不要短時間內頻繁抓取大量訊息，以避免被 Telegram API 限制
6. 您必須是群組/頻道的成員才能讀取其訊息
7. 所有分析操作的日誌會記錄在 `logs/` 資料夾中

## 系統需求

- Python 3.7 或更高版本
- 必要的 Python 套件：
  - telethon >= 1.32.1
  - python-dotenv >= 1.0.0
  - pandas >= 2.0.0
- 有效的 Telegram 帳號與 API 憑證