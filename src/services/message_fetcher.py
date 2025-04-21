"""
訊息獲取服務
處理從 Telegram 獲取訊息的相關功能
"""
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

# 更新導入路徑
from src.utils.logger import logger
from src.utils.display_utils import Colors, ProgressBar
from data.schemas import User, Reaction, Message

class MessageFetcher:
    """訊息獲取服務，負責從 Telegram 群組獲取訊息"""
    
    def __init__(self, client_manager, use_colors=True):
        """初始化訊息獲取器
        
        Args:
            client_manager: Telegram 客戶端管理器實例
            use_colors: 是否使用顏色輸出
        """
        self.client_manager = client_manager
        self.use_colors = use_colors
        
    async def get_recent_messages(self, group_entity, days=None, start_date=None, end_date=None):
        """獲取群組/頻道的最近訊息
        
        Args:
            group_entity: 群組/頻道實體
            days: 獲取最近幾天的訊息，如果為 None 則不限制天數
            start_date: 開始日期，優先使用
            end_date: 結束日期，優先使用
            
        Returns:
            list: 訊息列表
        """
        await self.client_manager.connect()
        
        # 獲取群組名稱
        group_title = getattr(group_entity, 'title', '未知群組')
        
        # 處理日期參數
        if start_date is not None and end_date is not None:
            # 如果提供了明確的日期範圍，使用它們
            # 確保帶有時區信息
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)
            
            logger.info(f"正在從 {group_title} 獲取 {start_date.strftime('%Y-%m-%d %H:%M')} 至 {end_date.strftime('%Y-%m-%d %H:%M')} 期間的訊息...")
            print(f"\n正在從 {group_title} 獲取 {start_date.strftime('%Y-%m-%d %H:%M')} 至 {end_date.strftime('%Y-%m-%d %H:%M')} 期間的訊息，請稍候...")
        elif days is not None:
            # 根據天數計算日期範圍
            end_date = datetime.now(timezone.utc)
            
            # 關鍵修改：確保完整計算指定天數對應的小時數
            hours_to_subtract = days * 24
            start_date = end_date - timedelta(hours=hours_to_subtract)
            
            # 記錄詳細的日期時間範圍，包含小時和分鐘
            logger.info(f"正在從 {group_title} 獲取近 {days} 天的訊息 ({start_date.strftime('%Y-%m-%d %H:%M')} 至 {end_date.strftime('%Y-%m-%d %H:%M')})，總計 {hours_to_subtract} 小時...")
            print(f"\n正在從 {group_title} 獲取近 {days} 天的訊息 ({start_date.strftime('%Y-%m-%d %H:%M')} 至 {end_date.strftime('%Y-%m-%d %H:%M')})，總計 {hours_to_subtract} 小時，請稍候...")
        else:
            # 沒有指定日期範圍，視為錯誤
            logger.error(f"未指定日期範圍")
            print(f"\n錯誤：必須指定日期範圍")
            return []
        
        messages = []
        c = Colors if self.use_colors else type('NoColors', (), {attr: '' for attr in dir(Colors) if not attr.startswith('__')})
        
        # 準備 Telegram API 過濾參數
        # Telegram API 的 iter_messages 只支持 end_date 參數，不支持 start_date
        kwargs = {}
        
        # 使用 end_date 而不是 start_date 來獲取訊息
        # Telegram 會返回「早於或等於」end_date 的訊息
        kwargs['offset_date'] = end_date
        
        # 初始化計數器
        counter = ProgressBar(prefix=f"{c.BRIGHT_CYAN}獲取進度:{c.RESET}", suffix=f"{c.YELLOW}完成{c.RESET}")
        
        try:
            # 獲取訊息並計數
            async for message in self.client_manager.client.iter_messages(group_entity, **kwargs):
                # 確保訊息日期包含時區資訊
                message_date = message.date
                if message_date.tzinfo is None:
                    message_date = message_date.replace(tzinfo=timezone.utc)
                
                # 詳細記錄訊息處理過程
                logger.info(f"檢查訊息: {message_date}, 範圍: {start_date} 至 {end_date}, ID: {message.id}")
                
                # 只處理在指定時間範圍內的訊息
                # 訊息日期必須在開始日期和結束日期之間 (包含兩端)
                if message_date < start_date:
                    # 由於 Telegram API 按時間倒序返回訊息，一旦發現訊息早於 start_date，後續訊息都會更早，可以直接結束
                    logger.info(f"訊息日期 {message_date} 早於開始日期 {start_date}，停止獲取訊息")
                    break
                elif message_date > end_date:
                    # 訊息晚於 end_date，繼續查找更早的訊息
                    logger.info(f"訊息日期 {message_date} 晚於結束日期 {end_date}，跳過此訊息")
                    continue
                
                # 跳過沒有文字內容的訊息
                if not message.text:
                    continue
                
                # 獲取發送者資訊
                sender_info = await self._get_sender_info(message)
                
                # 獲取反應 (按讚) 資訊
                reactions, reactions_count = self._get_reactions_info(message)
                
                # 獲取回覆數量
                reply_count = self._get_reply_count(message)
                
                # 構建訊息資料
                msg_data = {
                    'id': message.id,
                    'date': message_date,
                    'text': message.text,
                    'sender': sender_info,
                    'reactions': reactions,
                    'total_reactions': reactions_count,
                    'reply_count': reply_count,
                    'views': getattr(message, 'views', 0),
                    'forwards': getattr(message, 'forwards', 0)
                }
                messages.append(msg_data)
                
                # 每10條訊息更新一次計數器顯示
                if len(messages) % 10 == 0:
                    counter.update(10)
                
                # 如果訊息數量達到 100000 條，則停止獲取
                if len(messages) >= 100000:
                    logger.info(f"已達到 100000 條訊息上限，停止獲取")
                    break
            
            # 完成計數並顯示最終結果
            counter.finish()
            logger.info(f"成功獲取 {len(messages)} 條訊息")
            return messages
        
        except Exception as e:
            # 確保出錯時也會顯示完整訊息
            counter.finish()
            logger.error(f"獲取訊息時發生錯誤: {e}")
            return []
    
    async def _get_sender_info(self, message) -> dict:
        """獲取訊息發送者信息
        
        Args:
            message: Telethon的訊息對象
            
        Returns:
            dict: 發送者信息
        """
        sender_info = None
        if message.sender_id:
            try:
                sender = await message.get_sender()
                if hasattr(sender, 'first_name'):  # 是User類型
                    # 組合暱稱和帳號
                    nickname = sender.first_name
                    if sender.last_name:
                        nickname += f" {sender.last_name}"
                    
                    username = sender.username or str(sender.id)
                    
                    # 使用「暱稱（帳號）」格式
                    display_name = f"{nickname}（{username}）"
                    
                    sender_info = {
                        'id': sender.id,
                        'username': username,
                        'nickname': nickname,
                        'display_name': display_name,
                        'first_name': sender.first_name,
                        'last_name': sender.last_name
                    }
            except Exception as e:
                sender_info = {
                    'id': message.sender_id, 
                    'display_name': f"未知用戶（{message.sender_id}）",
                    'username': '未知用戶',
                    'nickname': '未知用戶'
                }
        return sender_info
    
    def _get_reactions_info(self, message) -> tuple:
        """獲取訊息反應信息
        
        Args:
            message: Telethon的訊息對象
            
        Returns:
            tuple: (反應列表, 反應總數)
        """
        reactions = []
        total_reactions = 0
        
        if hasattr(message, 'reactions') and message.reactions:
            for reaction in message.reactions.results:
                emoji = None
                # 檢查是標準表情符號還是自訂表情符號
                if hasattr(reaction.reaction, 'emoticon'):
                    # 標準表情符號
                    emoji = reaction.reaction.emoticon
                elif hasattr(reaction.reaction, 'document_id'):
                    # 自訂表情符號 - 使用文檔ID作為標識
                    emoji = f"自訂表情:{reaction.reaction.document_id}"
                else:
                    # 未知類型表情符號
                    emoji = "未知表情符號"
                
                reactions.append({
                    'emoji': emoji,
                    'count': reaction.count
                })
                total_reactions += reaction.count
        
        return reactions, total_reactions
    
    def _get_reply_count(self, message) -> int:
        """獲取訊息回覆數
        
        Args:
            message: Telethon的訊息對象
            
        Returns:
            int: 回覆數
        """
        reply_count = 0
        if hasattr(message, 'replies') and message.replies:
            reply_count = message.replies.replies
        return reply_count