#!/usr/bin/env python3
"""
Telegram群組熱門訊息分析工具主程式
"""
import os
import sys
import asyncio
import argparse
import logging
from datetime import datetime, timedelta

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

def valid_date(date_string):
    """驗證日期格式是否為YYYYMMDD
    
    Args:
        date_string: 待驗證的日期字符串
        
    Returns:
        datetime: 解析後的日期對象
        
    Raises:
        ArgumentTypeError: 當日期格式不正確時
    """
    try:
        return datetime.strptime(date_string, "%Y%m%d")
    except ValueError:
        msg = f"'{date_string}' 不是有效的日期格式，請使用 YYYYMMDD 格式"
        raise argparse.ArgumentTypeError(msg)

def parse_arguments():
    """解析命令行參數
    
    Returns:
        argparse.Namespace: 解析後的參數
    """
    parser = argparse.ArgumentParser(description='Telegram 群組熱門訊息分析工具')
    parser.add_argument('--days', type=int, default=None, 
                        help=f'分析多少天的訊息 (預設: {DEFAULT_DAYS})')
    parser.add_argument('--start-date', type=valid_date, default=None,
                        help='設定分析的起始日期，格式為 YYYYMMDD (例如: 20250410)')
    parser.add_argument('--limit', type=int, default=None, 
                        help=f'分析的訊息數量上限 (預設: {DEFAULT_MESSAGE_LIMIT})')
    parser.add_argument('--top', type=int, default=DEFAULT_TOP_COUNT, 
                        help=f'顯示和轉發的熱門訊息數量 (預設: {DEFAULT_TOP_COUNT})')
    parser.add_argument('--use-history', dest='use_history', action='store', 
                        choices=['yes', 'no', 'ask'],
                        default='ask' if DEFAULT_USE_HISTORY is None else 'yes' if DEFAULT_USE_HISTORY else 'no',
                        help='是否使用上次選擇的群組 (預設: ask - 詢問用戶)')
    
    args = parser.parse_args()
    
    # 處理起始日期與天數的關係
    if args.start_date is not None and args.days is not None:
        # 如果同時指定了起始日期和天數，使用起始日期和天數計算結束日期
        args.end_date = args.start_date + timedelta(days=args.days)
    elif args.start_date is not None:
        # 如果只指定了起始日期，但沒有指定天數，才使用預設天數
        if args.days is None:
            args.days = DEFAULT_DAYS
        args.end_date = args.start_date + timedelta(days=args.days)
    elif args.days is not None:
        # 如果只指定了天數，從今天往前推
        args.start_date = datetime.now() - timedelta(days=args.days)
        args.end_date = datetime.now()
    else:
        # 如果兩者都沒指定，使用預設值
        args.days = DEFAULT_DAYS
        args.start_date = datetime.now() - timedelta(days=args.days)
        args.end_date = datetime.now()
    
    # 只有在用戶沒有指定 limit 時，才使用預設值
    if args.limit is None:
        args.limit = DEFAULT_MESSAGE_LIMIT
        
    return args

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