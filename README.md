# Telegram 群組熱門訊息分析工具

這個工具可以幫助您分析 Telegram 群組的聊天內容，找出表情符號反應總數最高和回覆次數最多的熱門訊息。

## 主要功能

- 互動式命令列介面，輕鬆選擇要分析的群組/頻道
- 分析所有表情符號反應總和最高的熱門訊息（Top 5）
- 分析回覆次數最多的討論熱門訊息（Top 5）
- 統計每個表情符號的使用頻率
- 產生完整的視覺化圖表分析
- 顯示群組活躍度與使用者參與度分析
- 支援自訂分析的訊息數量和時間範圍
- 支援自訂顯示的熱門訊息數量
- 支援自動使用上次選擇的群組

## 專案結構

```
TelegramReviewer/
├── README.md                         # 專案說明文件
├── requirements.txt                  # 相依套件清單
├── telegram_reviewer_history.json    # 歷史分析紀錄
├── telegram_reviewer_session.session # Telegram 登入資訊
├── telegram_reviewer.py              # 主程式啟動點
├── logs/                             # 日誌資料夾
│   └── telegram_reviewer_*.log       # 程式執行日誌
├── results/                          # 分析結果和圖表輸出資料夾
└── src/                              # 原始碼資料夾
    ├── config.py                     # 設定檔
    ├── main.py                       # 主程式邏輯
    ├── telegram_analyzer.py          # Telegram 訊息分析主模組
    ├── core/                         # 核心功能模組
    │   ├── message_analyzer.py       # 訊息分析功能
    │   ├── message_fetcher.py        # 訊息獲取功能
    │   └── telegram_client.py        # Telegram 客戶端管理
    ├── message_handling/             # 訊息處理模組
    │   └── forwarder.py              # 訊息轉發功能
    ├── ui/                           # 使用者介面模組
    │   └── cli.py                    # 命令列介面
    └── utils/                        # 工具類模組
        ├── display_utils.py          # 顯示和格式化工具
        └── logger.py                 # 日誌工具
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
   - 創建 `.env` 檔案
   - 從 [Telegram API](https://my.telegram.org/auth) 獲取 API_ID 和 API_HASH
   - 填入您的手機號碼

```
# .env 檔案範例
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
PHONE=+8861234567890
```

## 使用方法

基本用法（互動式選擇群組）：
```
python telegram_reviewer.py
```

或者使用 src 中的主模組：
```
python src/main.py
```

指定分析的訊息時間範圍：
```
python src/main.py --days 60
```

指定分析的訊息數量上限：
```
python src/main.py --limit 2000
```

指定顯示的熱門訊息數量：
```
python src/main.py --top 10
```

使用上次選擇的群組，不再詢問：
```
python src/main.py --use-history yes
```

不使用上次選擇的群組，直接顯示群組選擇界面：
```
python src/main.py --use-history no
```

同時指定多個參數：
```
python src/main.py --days 14 --limit 500 --top 8 --use-history yes
```

## 參數說明

- `--days`: 要分析的最近天數（預設: 30）
- `--limit`: 要分析的訊息數量上限（預設: 1000）
- `--top`: 顯示和轉發的熱門訊息數量（預設: 5）
- `--use-history`: 是否使用上次選擇的群組
  - `yes`: 直接使用上次選擇的群組，不再詢問
  - `no`: 不使用上次選擇的群組，直接顯示群組選擇界面
  - `ask`: 詢問使用者是否要使用上次選擇的群組（預設值）

## 互動式操作

1. 啟動程式後，會顯示您帳號下的所有群組和頻道
2. 使用方向鍵（↑↓）選擇要分析的群組
3. 按 Enter 確認選擇，或按 q 退出程式
4. 等待程式分析並產生結果

## 輸出結果

分析完成後，程式會：
1. 在終端機中顯示分析摘要：
   - 所有表情符號反應總和最高的訊息 Top N
   - 回覆數最多的熱門討論訊息 Top N
   - 最活躍的使用者排行
   - 最常使用的表情符號統計

2. 在 `results/` 資料夾中產生視覺化圖表：
   - `most_reactions.png`: 表情符號反應總和最高的訊息
   - `most_replied.png`: 回覆數最多的訊息
   - `messages_per_day.png`: 每日訊息量趨勢
   - `messages_per_user.png`: 最活躍使用者分析
   - `top_reactions.png`: 最常用表情符號統計

## 技術細節

- 使用 Telethon 庫與 Telegram API 互動
- 使用 Matplotlib 和 Pandas 進行數據可視化和分析
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
  - telethon 1.32.1
  - python-dotenv 1.0.1
  - matplotlib 3.8.3
  - pandas 2.2.1
- 有效的 Telegram 帳號與 API 憑證