# Telegram 群組熱門訊息分析工具

這個工具可以幫助您分析 Telegram 群組的聊天內容，找出表情符號反應總數最高和回覆次數最多的熱門訊息。

## 主要功能

- 互動式命令列介面，輕鬆選擇要分析的群組/頻道
- 分析所有表情符號反應總和最高的熱門訊息（Top 5）
- 分析回覆次數最多的討論熱門訊息（Top 5）
- 統計每個表情符號的使用頻率
- 產生完整的視覺化圖表分析
- 顯示群組活躍度與使用者參與度分析

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

同時指定時間範圍和訊息數量：
```
python src/main.py --days 14 --limit 500
```

## 參數說明

- `--days`: 要分析的最近天數（預設: 30）
- `--limit`: 要分析的訊息數量上限（預設: 1000）

## 互動式操作

1. 啟動程式後，會顯示您帳號下的所有群組和頻道
2. 使用方向鍵（↑↓）選擇要分析的群組
3. 按 Enter 確認選擇，或按 q 退出程式
4. 等待程式分析並產生結果

## 輸出結果

分析完成後，程式會：
1. 在終端機中顯示分析摘要：
   - 所有表情符號反應總和最高的訊息 Top 5
   - 回覆數最多的熱門討論訊息 Top 5
   - 最活躍的使用者排行
   - 最常使用的表情符號統計

2. 在 `results/` 資料夾中產生視覺化圖表：
   - `most_reactions.png`: 表情符號反應總和最高的訊息
   - `most_replied.png`: 回覆數最多的訊息
   - `messages_per_day.png`: 每日訊息量趨勢
   - `messages_per_user.png`: 最活躍使用者分析
   - `top_reactions.png`: 最常用表情符號統計

## 注意事項

1. 首次運行時，Telegram 會要求您進行登入驗證
2. 登入資訊會保存在 `telegram_reviewer_session.session` 檔案中，下次執行時會自動使用
3. 使用此工具必須遵守 Telegram 的使用條款
4. 請不要短時間內頻繁抓取大量訊息，以避免被 Telegram API 限制
5. 您必須是群組/頻道的成員才能讀取其訊息

## 系統需求

- Python 3.7 或更高版本
- 必要的 Python 套件（見 requirements.txt）
- 有效的 Telegram 帳號與 API 憑證