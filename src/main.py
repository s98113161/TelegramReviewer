#!/usr/bin/env python3
"""
Telegram群組熱門訊息分析工具主程式
"""
import os
import sys
import asyncio
import argparse
import logging

# 將當前目錄的上層目錄加入到 Python 路徑中，確保可以導入所有模組
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 直接使用相對路徑導入
from src.config import DEFAULT_DAYS, DEFAULT_MESSAGE_LIMIT, DEFAULT_TOP_COUNT, DEFAULT_USE_HISTORY, SESSION_NAME
from src.utils.logger import setup_logger
from src.core.telegram_client import TelegramClientManager
from src.core.message_fetcher import MessageFetcher
from src.core.message_analyzer import MessageAnalyzer
from src.message_handling.forwarder import MessageForwarder
from src.ui.cli import CommandLineInterface

# 獲取日誌器
logger = setup_logger("telegram_reviewer")

def parse_arguments():
    """解析命令行參數
    
    Returns:
        argparse.Namespace: 解析後的參數
    """
    parser = argparse.ArgumentParser(description='Telegram 群組熱門訊息分析工具')
    parser.add_argument('--days', type=int, default=DEFAULT_DAYS, 
                        help=f'分析最近幾天的訊息 (預設: {DEFAULT_DAYS})')
    parser.add_argument('--limit', type=int, default=DEFAULT_MESSAGE_LIMIT, 
                        help=f'分析的訊息數量上限 (預設: {DEFAULT_MESSAGE_LIMIT})')
    parser.add_argument('--top', type=int, default=DEFAULT_TOP_COUNT, 
                        help=f'顯示和轉發的熱門訊息數量 (預設: {DEFAULT_TOP_COUNT})')
    parser.add_argument('--use-history', dest='use_history', action='store', 
                        choices=['yes', 'no', 'ask'],
                        default='ask' if DEFAULT_USE_HISTORY is None else 'yes' if DEFAULT_USE_HISTORY else 'no',
                        help='是否使用上次選擇的群組 (預設: ask - 詢問用戶)')
    return parser.parse_args()

async def main():
    """主程式入口點"""
    try:
        # 解析命令行參數
        args = parse_arguments()
        
        # 初始化模組
        client_manager = TelegramClientManager(session_name=SESSION_NAME)
        message_fetcher = MessageFetcher(client_manager)
        message_analyzer = MessageAnalyzer()
        message_forwarder = MessageForwarder(client_manager)
        
        # 初始化命令行介面
        cli = CommandLineInterface(
            client_manager=client_manager,
            message_fetcher=message_fetcher,
            message_analyzer=message_analyzer,
            message_forwarder=message_forwarder
        )
        
        # 運行主流程
        await cli.run(args)
        
    except KeyboardInterrupt:
        print("\n\n操作已取消。")
    except Exception as e:
        logger.error(f"程式執行出錯: {e}", exc_info=True)
        print(f"\n❌ 發生錯誤: {str(e)}")
    finally:
        # 確保關閉客戶端連接
        if 'client_manager' in locals() and client_manager.client.is_connected():
            await client_manager.close()
            
if __name__ == "__main__":
    asyncio.run(main())