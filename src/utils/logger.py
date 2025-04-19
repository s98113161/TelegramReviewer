"""
Telegram Reviewer 日誌模組
此模組處理所有日誌相關功能
"""
import logging
import sys
from pathlib import Path

# 從src正確導入
from src.config import LOG_FORMAT, LOG_LEVEL, LOG_FILE

def setup_logger(name='telegram_reviewer'):
    """設置和配置日誌記錄器

    Args:
        name: 日誌記錄器名稱

    Returns:
        logging.Logger: 配置好的日誌記錄器
    """
    # 創建日誌格式器
    log_formatter = logging.Formatter(LOG_FORMAT)

    # 創建檔案處理器
    file_handler = logging.FileHandler(filename=LOG_FILE, encoding='utf-8')
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(LOG_LEVEL)

    # 創建控制台處理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(LOG_LEVEL)

    # 設定根日誌記錄器
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    
    # 避免重複添加處理器
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

# 創建一個默認日誌記錄器
logger = setup_logger()