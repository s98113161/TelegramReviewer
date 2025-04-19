#!/usr/bin/env python3
"""
Telegram Reviewer 配置模組
此模組包含整個應用程式的配置項和常數
"""
import os
import logging
from pathlib import Path
from datetime import datetime

# 取得程式根目錄的路徑
ROOT_DIR = Path(__file__).parent.parent.absolute()

# 群組記錄文件路徑 - 保存在程式根目錄
GROUP_HISTORY_FILE = ROOT_DIR / "telegram_reviewer_history.json"

# 日誌相關設定
LOG_DIR = ROOT_DIR / "logs"
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = LOG_DIR / f"telegram_reviewer_{datetime.now().strftime('%Y-%m-%d')}.log"

# 預設分析參數
DEFAULT_DAYS = 30
DEFAULT_MESSAGE_LIMIT = 1000
DEFAULT_TOP_COUNT = 5
DEFAULT_USE_HISTORY = None  # None 表示會詢問用戶，True 表示默認使用歷史記錄，False 表示默認不使用

# 建立必要的目錄
if not LOG_DIR.exists():
    LOG_DIR.mkdir(exist_ok=True)

# Telegram 設定
SESSION_NAME = 'telegram_reviewer_session'