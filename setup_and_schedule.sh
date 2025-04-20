#!/bin/bash
#
# Telegram Reviewer 自動設定與定時執行腳本
# 用途：設置 Python 虛擬環境並創建 cron 任務定時執行分析工具
#

# 顏色設定
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# 腳本所在目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"
CONFIG_FILE="${SCRIPT_DIR}/.telegram_reviewer_config"

# 顯示歡迎信息
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}     Telegram Reviewer 自動設置工具     ${NC}"
echo -e "${BLUE}========================================${NC}"
echo
echo -e "${YELLOW}注意：此腳本將自動使用歷史群組選擇設定。${NC}"
echo

# 檢查是否已經設定過
if [ -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}檢測到先前的設定。${NC}"
    read -p "是否要註銷舊的設定並重新設定？(yes/no，預設: no): " RESET_CONFIG
    RESET_CONFIG=${RESET_CONFIG:-no}
    
    if [[ "$RESET_CONFIG" != "yes" ]]; then
        echo -e "${GREEN}保留現有設定，腳本結束。${NC}"
        exit 0
    else
        echo -e "${YELLOW}將重置所有設定...${NC}"
        # 移除定時任務
        TEMP_CRON=$(mktemp)
        crontab -l > "$TEMP_CRON" 2>/dev/null
        grep -v "Telegram Reviewer 自動分析" "$TEMP_CRON" | grep -v "telegram_reviewer.py" > "${TEMP_CRON}.new"
        crontab "${TEMP_CRON}.new"
        rm "$TEMP_CRON" "${TEMP_CRON}.new"
        echo -e "${GREEN}已移除現有的定時任務。${NC}"
    fi
fi

# 檢查 Python 和 virtualenv
echo -e "${YELLOW}檢查 Python 環境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}錯誤：找不到 python3 命令。請先安裝 Python 3。${NC}"
    exit 1
fi

# 創建虛擬環境
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}正在創建 Python 虛擬環境...${NC}"
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo -e "${RED}錯誤：無法創建虛擬環境。請檢查 Python 安裝。${NC}"
        exit 1
    fi
    echo -e "${GREEN}虛擬環境創建成功！${NC}"
else
    echo -e "${GREEN}虛擬環境已存在，跳過創建步驟。${NC}"
fi

# 激活虛擬環境並安裝依賴
echo -e "${YELLOW}正在安裝必要的套件...${NC}"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$SCRIPT_DIR/requirements.txt"
if [ $? -ne 0 ]; then
    echo -e "${RED}錯誤：安裝套件失敗。請檢查 requirements.txt 文件。${NC}"
    exit 1
fi
echo -e "${GREEN}套件安裝完成！${NC}"

# 提示用戶輸入分析參數
echo
echo -e "${BLUE}設定 Telegram 分析參數：${NC}"
read -p "要分析多少天的訊息？(預設: 7): " DAYS
DAYS=${DAYS:-7}

read -p "要顯示多少熱門訊息？(預設: 10): " TOP_COUNT
TOP_COUNT=${TOP_COUNT:-10}

# 固定使用歷史群組選擇，不再詢問
USE_HISTORY="yes"
echo -e "${YELLOW}已自動設定：使用歷史群組選擇${NC}"

read -p "是否儲存分析結果？(yes/no，預設: yes): " SAVE_RESULT
SAVE_RESULT=${SAVE_RESULT:-yes}

# 構建執行命令
CMD="cd \"$SCRIPT_DIR\" && \"$VENV_DIR/bin/python3\" telegram_reviewer.py --days $DAYS --top $TOP_COUNT --use-history $USE_HISTORY"
if [[ "$SAVE_RESULT" == "yes" ]]; then
    CMD="$CMD --save"
fi

# 詢問是否設定定時任務
echo
echo -e "${BLUE}設定定時執行：${NC}"
read -p "是否需要定時執行此工具？(yes/no，預設: yes): " SCHEDULE
SCHEDULE=${SCHEDULE:-yes}

if [[ "$SCHEDULE" == "yes" ]]; then
    echo -e "${YELLOW}請選擇執行頻率：${NC}"
    echo "1) 每天執行一次"
    echo "2) 每週執行一次"
    echo "3) 每月執行一次"
    echo "4) 自定義時間"
    read -p "請選擇 (1-4): " FREQUENCY_CHOICE
    
    case $FREQUENCY_CHOICE in
        1)
            read -p "每天幾點執行？(0-23，預設: 8): " HOUR
            HOUR=${HOUR:-8}
            CRON_SCHEDULE="0 $HOUR * * *"
            SCHEDULE_DESC="每天 $HOUR:00"
            ;;
        2)
            read -p "每週幾執行？(0-6，0=週日，預設: 1): " DOW
            DOW=${DOW:-1}
            read -p "每週幾點執行？(0-23，預設: 8): " HOUR
            HOUR=${HOUR:-8}
            CRON_SCHEDULE="0 $HOUR * * $DOW"
            SCHEDULE_DESC="每週 $DOW $HOUR:00"
            ;;
        3)
            read -p "每月幾號執行？(1-28，預設: 1): " DOM
            DOM=${DOM:-1}
            read -p "幾點執行？(0-23，預設: 8): " HOUR
            HOUR=${HOUR:-8}
            CRON_SCHEDULE="0 $HOUR $DOM * *"
            SCHEDULE_DESC="每月 $DOM 號 $HOUR:00"
            ;;
        4)
            read -p "請輸入 cron 表達式 (分 時 日 月 星期，例如 '0 8 * * 1'): " CRON_SCHEDULE
            SCHEDULE_DESC="自定義排程 ($CRON_SCHEDULE)"
            ;;
        *)
            echo -e "${RED}無效選擇，使用每日排程。${NC}"
            CRON_SCHEDULE="0 8 * * *"
            SCHEDULE_DESC="每天 8:00"
            ;;
    esac
    
    # 創建臨時 crontab 文件
    TEMP_CRON=$(mktemp)
    crontab -l > "$TEMP_CRON" 2>/dev/null
    
    # 檢查是否已經有相同的 cron 任務
    if grep -qF "$CMD" "$TEMP_CRON"; then
        echo -e "${YELLOW}已存在相同的定時任務，跳過添加。${NC}"
    else
        echo "# Telegram Reviewer 自動分析 - $SCHEDULE_DESC" >> "$TEMP_CRON"
        echo "$CRON_SCHEDULE $CMD" >> "$TEMP_CRON"
        crontab "$TEMP_CRON"
        if [ $? -ne 0 ]; then
            echo -e "${RED}設置定時任務失敗。請手動添加 crontab 項。${NC}"
        else
            echo -e "${GREEN}定時任務設置成功！將在 $SCHEDULE_DESC 自動執行。${NC}"
        fi
    fi
    
    rm "$TEMP_CRON"
fi

# 詢問是否立即執行
echo
read -p "是否立即執行一次分析？(yes/no，預設: yes): " RUN_NOW
RUN_NOW=${RUN_NOW:-yes}

if [[ "$RUN_NOW" == "yes" ]]; then
    echo -e "${YELLOW}正在執行 Telegram 訊息分析...${NC}"
    eval "$CMD"
    echo -e "${GREEN}分析完成！${NC}"
fi

# 保存設定資訊到配置檔案
cat > "$CONFIG_FILE" << EOF
# Telegram Reviewer 配置 - 創建於 $(date)
DAYS=$DAYS
TOP_COUNT=$TOP_COUNT
USE_HISTORY=$USE_HISTORY
SAVE_RESULT=$SAVE_RESULT
SCHEDULE=$SCHEDULE
SCHEDULE_DESC="$SCHEDULE_DESC"
LAST_SETUP=$(date +%Y-%m-%d)
EOF

echo
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}設置完成！${NC}"
echo -e "${BLUE}如需手動執行，可以運行：${NC}"
echo "cd \"$SCRIPT_DIR\" && source \"$VENV_DIR/bin/activate\" && python telegram_reviewer.py [參數]"
echo -e "${BLUE}========================================${NC}"

# 退出虛擬環境
deactivate