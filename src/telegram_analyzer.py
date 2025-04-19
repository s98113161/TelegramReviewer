import os
import sys
import time
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from collections import Counter
from inspect import signature  # 添加這行來導入 signature 函數

import pandas as pd
import telethon  # 添加這行來導入完整的telethon包
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, User
from telethon.tl.functions.messages import CreateChatRequest  # 添加這行來導入創建群組的API
from telethon.tl.functions.channels import CreateChannelRequest  # 添加這行來導入創建頻道的API
from dotenv import load_dotenv

# 引入新的顯示工具模組
from utils.display_utils import (
    Colors, supports_color, ProgressBar,
    MessageFormatter, AnalysisResultsDisplay
)

# 設定日誌
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramAnalyzer:
    """Telegram 訊息分析工具類別"""
    
    def __init__(self, session_name='telegram_session'):
        """初始化 Telegram 分析器"""
        # 載入環境變數
        load_dotenv()
        
        # 取得 API 憑證
        self.api_id = os.environ.get('API_ID')
        self.api_hash = os.environ.get('API_HASH')
        self.phone = os.environ.get('PHONE')
        
        # 檢查是否支持顏色輸出
        self.use_colors = supports_color()
        
        # 檢查是否有必要的憑證
        if not all([self.api_id, self.api_hash]):
            logger.error("API 憑證缺失，請在 .env 檔案中設置 API_ID 和 API_HASH")
            raise ValueError("API 憑證缺失")
        
        # 初始化 Telegram 客戶端
        self.client = TelegramClient(session_name, self.api_id, self.api_hash)
        self.me = None  # 儲存登入用戶資訊
        
        # 初始化顯示相關物件
        self.display = AnalysisResultsDisplay(self.use_colors)
        
    async def connect(self):
        """連接到 Telegram API"""
        if not self.client.is_connected():
            await self.client.start(phone=self.phone)
            self.me = await self.client.get_me()
            logger.info(f"成功連線到 Telegram，登入用戶: {self.me.first_name} (@{self.me.username})")
    
    async def get_all_dialogs(self):
        """獲取所有對話（群組和頻道）"""
        await self.connect()
        
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
    
    async def get_recent_messages(self, group_entity, days=30, limit=1000):
        """獲取群組/頻道的最近訊息"""
        await self.connect()
        
        group_title = getattr(group_entity, 'title', '未知群組')
        logger.info(f"正在從 {group_title} 獲取近 {days} 天的訊息...")
        print(f"\n正在從 {group_title} 獲取近 {days} 天的訊息，請稍候...")
        
        # 計算起始日期 (UTC 時區)
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        messages = []
        c = Colors if self.use_colors else type('NoColors', (), {attr: '' for attr in dir(Colors) if not attr.startswith('__')})
        
        # 預取一些訊息來估計總數
        estimate_count = 0
        async for _ in self.client.iter_messages(group_entity, limit=min(100, limit)):
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
        
        # 實際獲取訊息
        try:
            count = 0
            async for message in self.client.iter_messages(group_entity, limit=limit):
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
                sender_info = None
                if message.sender_id:
                    try:
                        sender = await message.get_sender()
                        if isinstance(sender, User):
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
                
                # 獲取反應 (按讚) 資訊
                reactions = []
                if hasattr(message, 'reactions') and message.reactions:
                    for reaction in message.reactions.results:
                        reactions.append({
                            'emoji': reaction.reaction.emoticon,
                            'count': reaction.count
                        })
                
                # 獲取回覆數量
                reply_count = 0
                if hasattr(message, 'replies') and message.replies:
                    reply_count = message.replies.replies
                
                # 構建訊息資料
                msg_data = {
                    'id': message.id,
                    'date': message_date,
                    'text': message.text,
                    'sender': sender_info,
                    'reactions': reactions,
                    'total_reactions': sum(r['count'] for r in reactions),
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
    
    def analyze_messages(self, messages):
        """分析訊息數據"""
        if not messages:
            logger.warning("沒有訊息可供分析")
            return None
        
        logger.info(f"開始分析 {len(messages)} 條訊息...")
        
        # 轉換為 DataFrame 以方便分析
        df = pd.DataFrame(messages)
        
        # 提取發送者顯示名稱 (暱稱（帳號）格式)
        df['display_name'] = df['sender'].apply(
            lambda x: x.get('display_name', '未知用戶') if x else '未知用戶'
        )
        
        # 保留原始 username 欄位以供兼容
        df['username'] = df['sender'].apply(
            lambda x: x.get('username', '未知用戶') if x else '未知用戶'
        )
        
        # 為訊息添加反應詳情欄位
        df['reactions_detail'] = df['reactions'].apply(
            lambda reactions: ' '.join([f"{r['emoji']}×{r['count']}" for r in reactions]) if reactions else ''
        )
        
        # 熱門訊息分析 (所有表情符號反應總數最多)
        most_reactions = df.sort_values('total_reactions', ascending=False).head(10)
        
        # 回覆最多訊息分析
        most_replied = df.sort_values('reply_count', ascending=False).head(10)
        
        # 每日訊息統計
        df['date_day'] = df['date'].dt.date
        messages_per_day = df.groupby('date_day').size().reset_index(name='count')
        
        analysis_results = {
            'most_reactions': most_reactions,  # 所有表情符號反應總和最高的訊息
            'most_replied': most_replied,
            'messages_per_day': messages_per_day,
            'total_messages': len(df),
            'unique_users': df['display_name'].nunique(),
            'period': {
                'start': df['date'].min().date(),
                'end': df['date'].max().date()
            }
        }
        
        logger.info("訊息分析完成")
        return analysis_results
    
    def print_analysis_results(self, analysis_results, group_name, top_count=5):
        """使用顯示模組印出分析結果摘要
        
        Args:
            analysis_results: 分析結果字典
            group_name: 群組名稱
            top_count: 顯示的熱門訊息數量，預設為5
        """
        self.display.print_analysis_results(analysis_results, group_name, top_count)
        
    async def find_test_group(self):
        """尋找名稱包含 'Test' 的群組
        
        Returns:
            dict: 含有 'entity' 和 'name' 的群組字典，若未找到則返回 None
        """
        try:
            dialogs = await self.get_all_dialogs()
            for dialog in dialogs:
                if 'Test' in dialog['name']:
                    return dialog
            return None
        except Exception as e:
            logger.error(f"尋找 Test 群組時發生錯誤: {e}")
            return None

    async def find_or_create_storage_group(self, source_group):
        """尋找或創建一個與源群組對應的儲存群組
        
        Args:
            source_group: 源群組實體
            
        Returns:
            dict: 包含儲存群組信息的字典，如果失敗則返回None
        """
        try:
            # 獲取源群組名稱
            source_name = getattr(source_group, 'title', '未知群組')
            storage_group_name = f"TG分析-{source_name}"
            
            logger.info(f"尋找儲存群組: {storage_group_name}")
            
            # 嘗試查找現有的儲存群組
            async for dialog in self.client.iter_dialogs():
                if dialog.is_channel and dialog.title == storage_group_name:
                    logger.info(f"找到現有儲存群組: {dialog.title}")
                    return {
                        'name': dialog.title,
                        'entity': dialog.entity,
                        'id': dialog.id
                    }
            
            # 如果找不到現有的儲存群組，則創建一個新的
            logger.info(f"未找到儲存群組，將創建新群組: {storage_group_name}")
            
            # 創建新頻道
            result = await self.client(CreateChannelRequest(
                title=storage_group_name,
                about=f"自動創建的儲存群組，用於存儲「{source_name}」的分析結果",
                megagroup=True  # 設為超級群組以便更好地管理
            ))
            
            new_channel = result.chats[0]
            logger.info(f"成功創建新儲存群組: {new_channel.title}")
            
            return {
                'name': new_channel.title,
                'entity': new_channel,
                'id': new_channel.id
            }
            
        except Exception as e:
            logger.error(f"尋找或創建儲存群組時發生錯誤: {e}")
            return None

    async def forward_top_messages_to_storage_group(self, target_group, top_messages, time_range_days=7):
        """將熱門訊息複製到對應的儲存群組（包含媒體檔案）
        
        Args:
            target_group: 目標群組實體
            top_messages: 熱門訊息列表
            time_range_days: 時間範圍（天數）
            
        Returns:
            bool: 成功複製則返回 True，否則返回 False
        """
        try:
            # 獲取或創建與目標群組對應的儲存群組
            storage_group = await self.find_or_create_storage_group(target_group)
            
            if not storage_group:
                logger.error("無法找到或創建儲存群組，取消操作")
                return False
                
            logger.info(f"開始將熱門訊息複製到儲存群組: {storage_group['name']}")
            
            # 先發送標題訊息說明這是哪個群組的熱門訊息
            source_name = getattr(target_group, 'title', '未知群組')
            current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
            
            header_message = (
                f"📊 **{source_name}** 最近 {time_range_days} 天熱門訊息摘要\n\n"
                f"⏱ 分析時間: {current_time}\n"
                f"📈 共選出 {len(top_messages)} 條熱門訊息\n\n"
                f"-----------------------------------"
            )
            
            await self.client.send_message(storage_group['entity'], header_message)
            
            # 複製熱門訊息内容（包含媒體文件）
            successful_count = 0
            for idx, msg in enumerate(top_messages, 1):
                try:
                    source_message = None
                    message_id = None
                    
                    # 檢查 msg 是否為 pandas Series 類型
                    if isinstance(msg, pd.Series):
                        # 如果是 pandas Series，取出 id 字段用於獲取原始訊息
                        if 'id' in msg:
                            message_id = msg['id']
                    # 檢查 msg 是否為字典，且包含 id 或 message 字段
                    elif isinstance(msg, dict) and ('id' in msg or 'message' in msg):
                        message_id = msg.get('id') or msg.get('message')
                    else:
                        logger.error(f"無法識別的訊息格式: {type(msg)}")
                        continue
                    
                    # 獲取原始訊息
                    source_message = await self.client.get_messages(target_group, ids=message_id)
                    if not source_message:
                        logger.error(f"無法獲取原始訊息")
                        continue
                    
                    # 準備發送者信息
                    sender_info = ""
                    sender_id = ""
                    if hasattr(source_message, 'sender') and source_message.sender:
                        sender_name = getattr(source_message.sender, 'first_name', '')
                        if hasattr(source_message.sender, 'last_name') and source_message.sender.last_name:
                            sender_name += f" {source_message.sender.last_name}"
                        sender_username = getattr(source_message.sender, 'username', '')
                        sender_id = str(getattr(source_message.sender, 'id', ''))
                        if sender_username:
                            sender_info = f"{sender_name} (@{sender_username})"
                        else:
                            sender_info = sender_name
                    
                    # 訊息日期格式化
                    message_date = source_message.date.strftime("%Y-%m-%d %H:%M") if hasattr(source_message, 'date') else "未知時間"
                    
                    # 生成原始訊息的超連結
                    original_message_link = f"https://t.me/c/{str(source_message.chat_id)[4:]}/{source_message.id}"
                    
                    # 獲取反應和回覆數 - 直接從原始訊息獲取
                    reactions_count = 0
                    reactions_detail = ""
                    reply_count = 0
                    
                    # 從原始訊息中直接獲取回覆數
                    if hasattr(source_message, 'replies') and source_message.replies:
                        reply_count = source_message.replies.replies
                    
                    # 從原始訊息中直接獲取反應詳情和總數
                    if hasattr(source_message, 'reactions') and source_message.reactions:
                        # 計算反應總數
                        reactions_count = sum(reaction.count for reaction in source_message.reactions.results)
                        
                        # 格式化反應詳情
                        reactions_detail = ' '.join([
                            f"{reaction.reaction.emoticon}×{reaction.count}" 
                            for reaction in source_message.reactions.results
                        ])
                    
                    # 打印調試信息到控制台，用於確認獲取到的數值
                    print(f"\n  表情符號: {reactions_detail}")
                    print(f"  反應總數: {reactions_count}")
                    print(f"  回覆數: {reply_count}")
                    
                    # 格式化新的排行訊息，包含超連結
                    rank_message = (
                        f"💥 **第 {idx} 名排行**\n"
                        f"回覆數: {reply_count}\n"
                        f"反應總數: {reactions_count}\n"
                    )
                    
                    if reactions_detail:
                        rank_message += f"表情符號: {reactions_detail}\n"
                    
                    rank_message += (
                        f"使用者: {sender_info}"
                    )
                    
                    if sender_id:
                        rank_message += f"（{sender_id}）"
                    
                    rank_message += f"\n發布時間: {message_date}\n"
                    rank_message += f"[點擊此處查看原始訊息]({original_message_link})"
                    
                    # 處理媒體檔案和文字訊息
                    if source_message.media:
                        # 發送排行訊息
                        await self.client.send_message(storage_group['entity'], rank_message)
                        
                        # 添加原始文本內容（如果有）
                        if source_message.text:
                            text_content = f"📝 **訊息內容**：\n{source_message.text}"
                            await self.client.send_message(storage_group['entity'], text_content)
                        
                        # 第一步：嘗試直接轉發訊息
                        forward_success = False
                        try:
                            logger.info(f"嘗試直接轉發媒體訊息 ID: {message_id}")
                            await self.client.forward_messages(
                                storage_group['entity'],
                                source_message
                            )
                            logger.info(f"成功轉發媒體訊息 ID: {message_id}")
                            forward_success = True
                        except Exception as forward_error:
                            logger.warning(f"直接轉發媒體訊息失敗: {forward_error}，將嘗試下載後重新上傳")
                            
                            # 第二步：如果轉發失敗，嘗試下載後重新上傳
                            try:
                                # 獲取原始文件名
                                original_filename = None
                                if hasattr(source_message.media, 'document') and hasattr(source_message.media.document, 'attributes'):
                                    for attr in source_message.media.document.attributes:
                                        if hasattr(attr, 'file_name') and attr.file_name:
                                            original_filename = attr.file_name
                                            break
                                
                                # 如果沒有找到原始文件名，生成一個臨時文件名
                                if not original_filename:
                                    # 根據媒體類型生成臨時文件名
                                    file_ext = ""
                                    if hasattr(source_message.media, 'photo'):
                                        file_ext = ".jpg"
                                    elif hasattr(source_message.media, 'document'):
                                        mime_type = getattr(source_message.media.document, 'mime_type', '')
                                        if 'video' in mime_type:
                                            file_ext = ".mp4"
                                        elif 'audio' in mime_type:
                                            file_ext = ".mp3"
                                        elif 'image' in mime_type:
                                            if 'png' in mime_type:
                                                file_ext = ".png"
                                            elif 'gif' in mime_type:
                                                file_ext = ".gif"
                                            elif 'webp' in mime_type:
                                                file_ext = ".webp"
                                            else:
                                                file_ext = ".jpg"
                                        else:
                                            file_ext = ".bin"
                                    
                                    original_filename = f"media_{message_id}{file_ext}"
                                
                                temp_path = f"/tmp/{original_filename}"
                                
                                # 下載媒體檔案到臨時路徑
                                downloaded_path = await self.client.download_media(source_message, temp_path)
                                if downloaded_path:
                                    logger.info(f"媒體檔案已下載到: {downloaded_path}")
                                    
                                    # 重新上傳媒體文件，保留原始文件名
                                    caption = "媒體檔案"
                                    if original_filename:
                                        caption += f" ({original_filename})"
                                    
                                    await self.client.send_file(
                                        storage_group['entity'],
                                        downloaded_path,
                                        caption=caption
                                    )
                                    
                                    # 刪除臨時檔案
                                    try:
                                        os.remove(downloaded_path)
                                    except Exception as remove_error:
                                        logger.warning(f"無法刪除臨時文件: {remove_error}")
                                else:
                                    logger.warning(f"無法下載媒體檔案，訊息ID: {message_id}")
                            except Exception as media_error:
                                logger.error(f"處理媒體檔案時出錯: {media_error}")
                    elif source_message.text:
                        # 文字訊息處理
                        text_content = f"📝 **訊息內容**：\n{source_message.text}"
                        
                        # 發送排行訊息
                        await self.client.send_message(storage_group['entity'], rank_message)
                        
                        # 發送訊息內容
                        await self.client.send_message(storage_group['entity'], text_content)
                    else:
                        # 沒有文字也沒有媒體的訊息，跳過
                        logger.warning(f"訊息ID {message_id} 沒有文字內容也沒有媒體檔案，跳過")
                        continue
                        
                    successful_count += 1
                    
                    time.sleep(1)  # 避免過快發送
                except Exception as e:
                    logger.error(f"複製訊息時發生錯誤: {e}")
            
            # 發送結束訊息
            footer_message = f"✅ 共成功複製 {successful_count}/{len(top_messages)} 條熱門訊息"
            await self.client.send_message(storage_group['entity'], footer_message)
            
            logger.info(f"成功將 {successful_count} 條熱門訊息複製到儲存群組")
            return True
            
        except Exception as e:
            logger.error(f"複製熱門訊息時發生錯誤: {e}")
            return False

    async def forward_analysis_to_group(self, analysis_results, source_group_name, target_group):
        """將分析結果轉發到指定的 Telegram 群組
        
        Args:
            analysis_results: 分析結果字典
            source_group_name: 被分析的群組名稱
            target_group: 目標群組實體
        
        Returns:
            bool: 是否成功發送
        """
        if not analysis_results:
            logger.warning("沒有分析結果可供轉發")
            return False
        
        try:
            # 準備訊息內容
            period = analysis_results['period']
            total_msgs = analysis_results['total_messages']
            unique_users = analysis_results['unique_users']
            
            header = f"📊 {source_group_name} 訊息分析結果\n"
            header += f"📅 分析期間: {period['start']} 至 {period['end']}\n"
            header += f"📝 總訊息數: {total_msgs} | 參與用戶數: {unique_users}\n"
            header += "=" * 30
            
            # 發送標題訊息
            await self.client.send_message(target_group, header)
            
            # 發送表情符號反應排行榜
            if not analysis_results['most_reactions'].empty:
                reaction_msg = "📱 所有表情符號反應總和最高的訊息 TOP 5\n" + "=" * 30
                await self.client.send_message(target_group, reaction_msg)
                
                # 發送每條熱門反應訊息
                for i, (_, row) in enumerate(analysis_results['most_reactions'].head(5).iterrows(), 1):
                    await self._send_message_item(target_group, i, row, is_reaction=True)
            
            # 發送回覆數排行榜
            if not analysis_results['most_replied'].empty:
                reply_msg = "\n💬 回覆數最多的訊息 TOP 5\n" + "=" * 30
                await self.client.send_message(target_group, reply_msg)
                
                # 發送每條熱門回覆訊息
                for i, (_, row) in enumerate(analysis_results['most_replied'].head(5).iterrows(), 1):
                    await self._send_message_item(target_group, i, row, is_reaction=False)
            
            # 發送頁尾
            footer = "\n✅ 分析完成！"
            await self.client.send_message(target_group, footer)
            
            return True
            
        except Exception as e:
            logger.error(f"轉發分析結果時發生錯誤: {e}")
            return False
    
    async def _send_message_item(self, target_group, index, row, is_reaction=True):
        """發送單條訊息項目到目標群組"""
        try:
            # 訊息標頭
            header = f"\n{'━' * 10} 第 {index} 名 {'━' * 10}"
            await self.client.send_message(target_group, header)
            
            # 訊息內容
            content = row['text']
            await self.client.send_message(target_group, content)
            
            # 統計資訊區塊
            stats = []
            if is_reaction:
                if row['reactions_detail']:
                    stats.append(f"表情符號: {row['reactions_detail']}")
                stats.append(f"反應總數: {row['total_reactions']}")
                stats.append(f"回覆數: {row['reply_count']}")
            else:
                stats.append(f"回覆數: {row['reply_count']}")
                stats.append(f"反應總數: {row['total_reactions']}")
                if row['reactions_detail']:
                    stats.append(f"表情符號: {row['reactions_detail']}")
            
            # 顯示瀏覽數（如果有）
            if 'views' in row and row['views'] is not None and row['views'] > 0:
                stats.append(f"瀏覽數: {row['views']}")
            
            # 加入使用者資訊和發布時間
            date_str = row['date'].strftime('%Y-%m-%d %H:%M')
            stats.append(f"使用者: {row['display_name']}")
            stats.append(f"發布時間: {date_str}")
            
            # 發送統計資訊
            stats_text = "\n".join(stats)
            await self.client.send_message(target_group, f"{'─' * 30}\n{stats_text}\n{'─' * 30}")
            
        except Exception as e:
            logger.error(f"發送訊息項目時發生錯誤: {e}")
            await self.client.send_message(target_group, f"❌ 發送此條訊息時發生錯誤")


async def main():
    analyzer = TelegramAnalyzer()
    await analyzer.connect()
    
    # 獲取所有群組和頻道
    dialogs = await analyzer.get_all_dialogs()
    if not dialogs:
        print("❌ 沒有找到任何群組或頻道")
        return
    
    # 選擇第一個群組進行分析
    group_entity = dialogs[0]['entity']
    group_name = dialogs[0]['name']
    
    # 獲取訊息並分析
    messages = await analyzer.get_recent_messages(group_entity, days=30, limit=1000)
    analysis_results = analyzer.analyze_messages(messages)
    
    # 只印出結果，不再產生視覺化圖表
    analyzer.print_analysis_results(analysis_results, group_name)
    
    # 自動轉發熱門訊息到專屬儲存群組
    success_count, target_name = await analyzer.forward_top_messages_to_storage_group(group_entity, analysis_results['most_reactions'].to_dict('records'), time_range_days=30)
    if success_count:
        logger.info(f"成功轉發 {success_count} 條熱門訊息到 {target_name}")
    else:
        logger.warning("未成功轉發任何訊息")

if __name__ == '__main__':
    asyncio.run(main())