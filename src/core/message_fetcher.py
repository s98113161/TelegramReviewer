"""
訊息獲取模組
處理從Telegram獲取訊息的相關功能
"""
from datetime import datetime, timedelta, timezone

# 將相對導入改為絕對導入
from src.utils.logger import logger
from src.utils.display_utils import Colors, ProgressBar

class MessageFetcher:
    """訊息獲取類，負責從Telegram群組獲取訊息"""
    
    def __init__(self, client_manager, use_colors=True):
        """初始化訊息獲取器
        
        Args:
            client_manager: Telegram客戶端管理器實例
            use_colors: 是否使用顏色輸出
        """
        self.client_manager = client_manager
        self.use_colors = use_colors
        
    async def get_recent_messages(self, group_entity, days=30, limit=1000):
        """獲取群組/頻道的最近訊息
        
        Args:
            group_entity: 群組/頻道實體
            days: 獲取最近幾天的訊息
            limit: 最大訊息數量限制
            
        Returns:
            list: 訊息列表
        """
        await self.client_manager.connect()
        
        # 獲取群組名稱
        group_title = getattr(group_entity, 'title', '未知群組')
        logger.info(f"正在從 {group_title} 獲取近 {days} 天的訊息...")
        print(f"\n正在從 {group_title} 獲取近 {days} 天的訊息，請稍候...")
        
        # 計算起始日期 (UTC 時區)
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        messages = []
        c = Colors if self.use_colors else type('NoColors', (), {attr: '' for attr in dir(Colors) if not attr.startswith('__')})
        
        # 預取一些訊息來估計總數
        estimate_count = 0
        async for _ in self.client_manager.client.iter_messages(group_entity, limit=min(100, limit)):
            estimate_count += 1
        
        # 估計總數
        estimated_total = min(limit, estimate_count * (limit / 100) if estimate_count > 0 else limit)
        progress = ProgressBar(
            total=estimated_total, 
            prefix=f"{c.BRIGHT_CYAN}獲取進度:{c.RESET}", 
            suffix=f"{c.YELLOW}完成{c.RESET}", 
            length=40,
            fill=f"{c.GREEN}█{c.RESET}"
        )
        
        try:
            count = 0
            async for message in self.client_manager.client.iter_messages(group_entity, limit=limit):
                count += 1
                if count % 10 == 0:  # 每10條訊息更新一次進度條
                    progress.update(10)
                elif count == limit:  # 達到上限
                    progress.finish()
                
                # 確保訊息日期包含時區資訊
                message_date = message.date
                if message_date.tzinfo is None:
                    message_date = message_date.replace(tzinfo=timezone.utc)
                
                # 只保留指定天數內的訊息
                if message_date < start_date:
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
            
            # 完成進度條
            progress.finish()
            logger.info(f"成功獲取 {len(messages)} 條訊息")
            return messages
        
        except Exception as e:
            progress.finish()  # 確保進度條結束，不會影響後續輸出
            logger.error(f"獲取訊息時發生錯誤: {e}")
            return []
    
    async def _get_sender_info(self, message):
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
    
    def _get_reactions_info(self, message):
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
                reactions.append({
                    'emoji': reaction.reaction.emoticon,
                    'count': reaction.count
                })
                total_reactions += reaction.count
        
        return reactions, total_reactions
    
    def _get_reply_count(self, message):
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