"""
Telegram API 客戶端模組
處理 Telegram API 連接和基本功能
"""
import os
import logging
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, User
from dotenv import load_dotenv

# 更新導入路徑
from config.settings import SESSION_NAME
from src.utils.logger import logger
from data.schemas import GroupInfo

class TelegramClientManager:
    """Telegram 客戶端管理類，負責處理與 Telegram API 的連接"""
    
    def __init__(self, session_name=SESSION_NAME):
        """初始化 Telegram 客戶端管理器
        
        Args:
            session_name: 會話名稱，用於保存認證信息
        """
        # 載入環境變數
        load_dotenv()
        
        # 取得 API 憑證
        self.api_id = os.environ.get('API_ID')
        self.api_hash = os.environ.get('API_HASH')
        self.phone = os.environ.get('PHONE')
        
        # 檢查是否有必要的憑證
        if not all([self.api_id, self.api_hash]):
            logger.error("API 憑證缺失，請在 .env 檔案中設置 API_ID 和 API_HASH")
            raise ValueError("API 憑證缺失")
        
        # 初始化 Telegram 客戶端
        self.client = TelegramClient(session_name, self.api_id, self.api_hash)
        self.me = None  # 儲存登入用戶資訊
        
    async def connect(self):
        """連接到 Telegram API
        
        Returns:
            bool: 是否連接成功
        """
        if not self.client.is_connected():
            await self.client.start(phone=self.phone)
            self.me = await self.client.get_me()
            logger.info(f"成功連線到 Telegram，登入用戶: {self.me.first_name} (@{self.me.username})")
            return True
        return False
        
    async def get_all_dialogs(self):
        """獲取所有對話（群組和頻道）
        
        Returns:
            list: 群組和頻道的字典列表
        """
        logger.info("正在獲取所有群組和頻道...")
        dialogs = []
        
        try:
            # 獲取所有對話
            async for dialog in self.client.iter_dialogs():
                entity = dialog.entity
                
                # 只保留群組和頻道
                if isinstance(entity, (Chat, Channel)):
                    # 區分頻道和群組
                    is_channel = isinstance(entity, Channel) and entity.broadcast
                    # 獲取成員數量 (若可用)
                    members_count = getattr(entity, 'participants_count', 0)
                    
                    dialog_info = {
                        'id': dialog.id,
                        'name': dialog.name,
                        'entity': entity,
                        'type': '頻道' if is_channel else '群組',
                        'members_count': members_count
                    }
                    dialogs.append(dialog_info)
        
            logger.info(f"成功獲取 {len(dialogs)} 個群組和頻道")
            return dialogs
        
        except Exception as e:
            logger.error(f"獲取對話列表時發生錯誤: {e}")
            return []
    
    async def get_entity(self, entity_id):
        """根據 ID 獲取實體
        
        Args:
            entity_id: 實體 ID
            
        Returns:
            Entity: Telegram 實體對象
        """
        try:
            return await self.client.get_entity(entity_id)
        except Exception as e:
            logger.error(f"獲取實體失敗: {e}")
            return None
            
    async def close(self):
        """關閉客戶端連接"""
        if self.client.is_connected():
            await self.client.disconnect()
            logger.info("已關閉 Telegram 客戶端連接")