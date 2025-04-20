#!/usr/bin/env python3
"""
Telegram Reviewer 配置模組
此模組包含整個應用程式的可配置項和路徑設定
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

# 結果輸出目錄
RESULTS_DIR = ROOT_DIR / "results"

# 建立必要的目錄
for directory in [LOG_DIR, RESULTS_DIR]:
    if not directory.exists():
        directory.mkdir(exist_ok=True)

# Telegram 設定
SESSION_NAME = 'telegram_reviewer_session'