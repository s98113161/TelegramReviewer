#!/usr/bin/env python3
"""
Telegram Reviewer 主程式執行入口點
此檔案設置正確的路徑環境並啟動應用程式
"""
import os
import sys
import asyncio

# 將項目根目錄加入 Python 路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 導入主程式
from src.main import main

if __name__ == "__main__":
    # 運行主程式
    asyncio.run(main())