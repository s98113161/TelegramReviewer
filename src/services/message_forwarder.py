"""
訊息轉發服務
處理Telegram訊息的轉發、複製功能
"""
import os
import time
import pandas as pd
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
from pathlib import Path

from telethon.tl.functions.channels import CreateChannelRequest

# 更新導入路徑
from src.utils.logger import logger
from config.settings import RESULTS_DIR

class MessageForwarder:
    """訊息轉發服務，負責處理訊息的轉發、複製等功能"""
    
    def __init__(self, client_manager):
        """初始化訊息轉發器
        
        Args:
            client_manager: Telegram客戶端管理器實例
        """
        self.client_manager = client_manager
        
    async def find_or_create_storage_group(self, source_group) -> Optional[Dict[str, Any]]:
        """尋找或創建一個與源群組對應的儲存群組
        
        Args:
            source_group: 源群組實體
            
        Returns:
            Optional[Dict[str, Any]]: 包含儲存群組信息的字典，如果失敗則返回None
        """
        try:
            # 獲取源群組名稱
            source_name = getattr(source_group, 'title', '未知群組')
            storage_group_name = f"TG分析-{source_name}"
            
            logger.info(f"尋找儲存群組: {storage_group_name}")
            
            # 嘗試查找現有的儲存群組
            async for dialog in self.client_manager.client.iter_dialogs():
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
            result = await self.client_manager.client(CreateChannelRequest(
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
            
    async def forward_top_messages_to_storage_group(self, target_group, top_messages, time_range_days=7, all_messages=None, analysis_results=None) -> bool:
        """將熱門訊息複製到對應的儲存群組（包含媒體檔案）
        
        Args:
            target_group: 目標群組實體
            top_messages: 熱門訊息列表
            time_range_days: 時間範圍（天數）
            all_messages: 已經獲取的所有訊息數據（可選）
            analysis_results: 已經計算好的分析結果（可選）
            
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
            
            # 預設統計信息
            first_date = None
            last_date = None
            message_count = 0
            
            # 如果有提供已分析的訊息數據，則直接使用
            if all_messages and len(all_messages) > 0:
                # 使用已經獲取的訊息數據來計算時間範圍和總數
                message_count = len(all_messages)
                
                # 從提供的訊息數據中提取時間範圍
                dates = [msg['date'] for msg in all_messages if 'date' in msg]
                if dates:
                    first_date = min(dates)
                    last_date = max(dates)
                    
            # 如果有提供分析結果，則從中獲取時間範圍
            elif analysis_results and 'period' in analysis_results:
                period = analysis_results['period']
                # 注意: 這裡的日期可能是日期對象，而不是帶時區的datetime
                first_date = datetime.combine(period['start'], datetime.min.time()).replace(tzinfo=timezone.utc)
                last_date = datetime.combine(period['end'], datetime.max.time()).replace(tzinfo=timezone.utc)
                message_count = analysis_results.get('total_messages', len(top_messages))
            else:
                # 如果沒有提供訊息數據，則顯示使用默認的時間範圍
                print("\n使用預設時間範圍...")
                # 預設使用目前時間減去指定天數
                last_date = datetime.now(timezone.utc)
                first_date = last_date - pd.Timedelta(days=time_range_days)
                message_count = len(top_messages)
                
            # 計算實際天數範圍
            actual_days = (last_date - first_date).days + 1 if first_date and last_date else time_range_days
            
            # 格式化日期時間為中文年月日格式
            first_date_str = first_date.strftime("%Y年%m月%d日 %H:%M:%S") if first_date else "未知時間"
            last_date_str = last_date.strftime("%Y年%m月%d日 %H:%M:%S") if last_date else "未知時間"
            
            # 先發送標題訊息說明這是哪個群組的熱門訊息
            source_name = getattr(target_group, 'title', '未知群組')
            current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
            
            header_message = (
                f"📊 **{source_name}** 熱門訊息摘要\n\n"
                f"⏱ 分析時間: {current_time}\n"
                f"📈 共選出 {len(top_messages)} 條熱門訊息\n"
                f"📄 總訊息數: {message_count} 則\n"
                f"📅 訊息時間範圍: {first_date_str}～{last_date_str}\n"
                f"⌛ 實際天數: {actual_days} 天\n\n"
                f"-----------------------------------"
            )
            
            await self.client_manager.client.send_message(storage_group['entity'], header_message)
            
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
                    source_message = await self.client_manager.client.get_messages(target_group, ids=message_id)
                    if not source_message:
                        logger.error(f"無法獲取原始訊息")
                        continue
                    
                    await self._process_message(source_message, storage_group['entity'], idx)
                    successful_count += 1
                    
                    time.sleep(1)  # 避免過快發送
                except Exception as e:
                    logger.error(f"複製訊息時發生錯誤: {e}")
            
            # 發送結束訊息
            footer_message = f"✅ 共成功複製 {successful_count}/{len(top_messages)} 條熱門訊息"
            await self.client_manager.client.send_message(storage_group['entity'], footer_message)
            
            logger.info(f"成功將 {successful_count} 條熱門訊息複製到儲存群組")
            return True
            
        except Exception as e:
            logger.error(f"複製熱門訊息時發生錯誤: {e}")
            return False
            
    async def _process_message(self, source_message, target_entity, idx):
        """處理單條訊息的複製轉發
        
        Args:
            source_message: 源訊息對象
            target_entity: 目標實體
            idx: 訊息排名
        """
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
            await self.client_manager.client.send_message(target_entity, rank_message)
            
            # 添加原始文本內容（如果有）
            if source_message.text:
                text_content = f"📝 **訊息內容**：\n{source_message.text}"
                await self.client_manager.client.send_message(target_entity, text_content)
            
            await self._process_media(source_message, target_entity)
            
        elif source_message.text:
            # 文字訊息處理
            text_content = f"📝 **訊息內容**：\n{source_message.text}"
            
            # 發送排行訊息
            await self.client_manager.client.send_message(target_entity, rank_message)
            
            # 發送訊息內容
            await self.client_manager.client.send_message(target_entity, text_content)
        else:
            # 沒有文字也沒有媒體的訊息，跳過
            logger.warning(f"訊息ID {source_message.id} 沒有文字內容也沒有媒體檔案，跳過")
            
    async def _process_media(self, source_message, target_entity) -> bool:
        """處理媒體訊息的轉發
        
        Args:
            source_message: 源媒體訊息
            target_entity: 目標實體
            
        Returns:
            bool: 成功處理則返回True
        """
        message_id = source_message.id
        
        # 第一步：嘗試直接轉發訊息
        try:
            logger.info(f"嘗試直接轉發媒體訊息 ID: {message_id}")
            await self.client_manager.client.forward_messages(
                target_entity,
                source_message
            )
            logger.info(f"成功轉發媒體訊息 ID: {message_id}")
            return True
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
            
            # 改為放在results目錄中
            media_dir = RESULTS_DIR / "media"
            media_dir.mkdir(exist_ok=True)
            
            temp_path = str(media_dir / original_filename)
            
            # 下載媒體檔案到臨時路徑
            downloaded_path = await self.client_manager.client.download_media(source_message, temp_path)
            if downloaded_path:
                logger.info(f"媒體檔案已下載到: {downloaded_path}")
                
                # 重新上傳媒體文件，保留原始文件名
                caption = "媒體檔案"
                if original_filename:
                    caption += f" ({original_filename})"
                
                await self.client_manager.client.send_file(
                    target_entity,
                    downloaded_path,
                    caption=caption
                )
                
                # 刪除臨時檔案
                try:
                    os.remove(downloaded_path)
                except Exception as remove_error:
                    logger.warning(f"無法刪除臨時文件: {remove_error}")
                return True
            else:
                logger.warning(f"無法下載媒體檔案，訊息ID: {message_id}")
                return False
        except Exception as media_error:
            logger.error(f"處理媒體檔案時出錯: {media_error}")
            return False