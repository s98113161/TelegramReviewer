"""
命令行介面模組
處理使用者的命令行互動功能
"""
import os
import sys
import json
import shutil
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

# 更新導入路徑
from config.settings import GROUP_HISTORY_FILE
from src.utils.logger import logger
from data.storage import GroupHistoryManager

class CommandLineInterface:
    """命令列互動介面，用於選擇群組查看熱門訊息"""

    def __init__(self, client_manager, message_fetcher, message_analyzer, message_forwarder, results_storage=None):
        """初始化命令列介面
        
        Args:
            client_manager: Telegram客戶端管理器實例
            message_fetcher: 訊息獲取器實例
            message_analyzer: 訊息分析器實例
            message_forwarder: 訊息轉發器實例
            results_storage: 結果儲存管理器實例（可選）
        """
        self.client_manager = client_manager
        self.message_fetcher = message_fetcher
        self.message_analyzer = message_analyzer
        self.message_forwarder = message_forwarder
        self.results_storage = results_storage
        
        # 獲取終端寬度
        self.terminal_width = shutil.get_terminal_size().columns
        # 確保最小寬度
        self.terminal_width = max(self.terminal_width, 40)
        # 儲存使用者選擇的群組
        self.selected_groups = []
        # 上次選擇的群組紀錄
        self.history_manager = GroupHistoryManager()
        self.history_groups = self.history_manager.load_group_history()

    async def setup(self):
        """連接到 Telegram API"""
        try:
            await self.client_manager.connect()
        except Exception as e:
            print(f"❌ 無法連接到 Telegram: {e}")
            raise

    def clear_screen(self):
        """清除終端畫面"""
        os.system('cls' if sys.platform == 'win32' else 'clear')

    def print_header(self):
        """印出應用程式標頭"""
        self.clear_screen()
        print("=" * 60)
        print("🔍 Telegram 群組熱門訊息分析工具 🔍".center(58))
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}".center(58))
        print("=" * 60)

    def save_group_history(self, groups):
        """儲存選擇的群組
        
        Args:
            groups: 群組列表
        """
        self.history_manager.save_group_history(groups)

    def select_groups_by_keyboard(self, groups):
        """使用鍵盤方向鍵選擇多個群組"""
        if not groups:
            print("❌ 沒有找到任何群組或頻道")
            return []

        import termios
        import tty
        
        # 設定初始值
        selected_index = 0
        total_options = len(groups)
        selected_groups_indices = set()
        
        # 紀錄當前終端設定
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        
        try:
            # 進入原始模式
            tty.setraw(sys.stdin.fileno())
            
            while True:
                # 清除終端畫面並回復終端設定以正確輸出文字
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                self.print_header()
                
                print("\n👉 請使用方向鍵選擇要分析的群組:")
                print("   空白鍵: 選擇/取消選擇當前群組")
                print("   Enter: 確認選擇並開始分析")
                print("   q: 退出\n")
                
                # 計算可用於顯示群組名稱的最大寬度
                max_name_length = self.terminal_width - 30
                
                # 顯示選單項目
                for i, group in enumerate(groups):
                    group_type_icon = "📢" if group['type'] == '頻道' else "👥"
                    
                    # 截短群組名稱以防跑版
                    name = group['name']
                    if len(name) > max_name_length:
                        name = name[:max_name_length-3] + "..."
                    
                    members_info = f" - {group['members_count']}人" if group['members_count'] > 0 else ""
                    
                    # 顯示選擇狀態和當前指標位置
                    is_selected = i in selected_groups_indices
                    prefix = "▶️ " if i == selected_index else "  "
                    checkbox = "[✓]" if is_selected else "[ ]"
                    
                    print(f"{prefix}{checkbox} {i+1}. {group_type_icon} {name}{members_info}")
                
                # 顯示已選擇的群組數量
                if selected_groups_indices:
                    print(f"\n已選擇 {len(selected_groups_indices)} 個群組")
                
                # 返回原始模式以讀取按鍵
                tty.setraw(sys.stdin.fileno())
                
                # 取得使用者輸入
                key = ord(sys.stdin.read(1))
                
                # 退出程式 (q 鍵)
                if key == 113:  # q
                    return []
                    
                # 空格選擇/取消選擇
                if key == 32:  # Space
                    if selected_index in selected_groups_indices:
                        selected_groups_indices.remove(selected_index)
                    else:
                        selected_groups_indices.add(selected_index)
                
                # Enter 確認選擇
                if key == 13:  # Enter
                    if selected_groups_indices:
                        # 將選中的群組轉換為列表並返回
                        return [groups[i] for i in sorted(selected_groups_indices)]
                    else:
                        # 如果沒有選擇任何群組，則選擇當前指標所在的群組
                        return [groups[selected_index]]
                    
                # 方向鍵
                if key == 27:  # ESC (方向鍵開頭)
                    next_char = ord(sys.stdin.read(1))
                    if next_char == 91:  # [
                        direction = ord(sys.stdin.read(1))
                        if direction == 65:  # 上鍵
                            selected_index = (selected_index - 1) % total_options
                        elif direction == 66:  # 下鍵
                            selected_index = (selected_index + 1) % total_options
                
        except Exception as e:
            print(f"發生錯誤: {e}")
            return []
            
        finally:
            # 恢復終端設定
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    def display_loading_animation(self, message):
        """顯示載入動畫"""
        print(f"\n{message}", end="", flush=True)
        
    def ask_use_history(self, use_history_option='ask'):
        """詢問是否使用歷史記錄的群組
        
        Args:
            use_history_option: 命令行參數指定的選項 ('yes', 'no', 'ask')
        
        Returns:
            bool: 是否使用歷史群組
        """
        if not self.history_groups:
            return False
            
        # 根據命令行參數決定是否直接返回結果，不詢問用戶
        if use_history_option == 'yes':
            return True
        elif use_history_option == 'no':
            return False
            
        # 使用 'ask' 選項 - 詢問用戶
        self.print_header()
        
        # 顯示歷史群組
        print("\n上次您分析了以下群組：")
        for i, group in enumerate(self.history_groups):
            group_type_icon = "📢" if group['type'] == '頻道' else "👥"
            print(f"{i+1}. {group_type_icon} {group['name']}")
            
        # 詢問是否使用上次的選擇
        while True:
            answer = input("\n是否要使用上次選擇的群組進行分析？(y/n): ").strip().lower()
            if answer in ['y', 'yes', '是', 'n', 'no', '否']:
                return answer in ['y', 'yes', '是']
            print("請輸入 y 或 n")
            
    async def analyze_group(self, group, args):
        """分析單個群組並顯示結果
        
        Args:
            group: 群組信息
            args: 命令行參數
        """
        # 根據參數顯示不同的訊息提示
        if args.start_date is not None:
            # 顯示指定日期範圍
            start_date_str = args.start_date.strftime("%Y-%m-%d")
            end_date_str = args.end_date.strftime("%Y-%m-%d")
            print(f"\n正在分析 {group['name']} 的 {start_date_str} 至 {end_date_str} 期間訊息...")
        elif args.days is not None:
            # 只指定天數
            print(f"\n正在分析 {group['name']} 的近 {args.days} 天訊息...")
        
        # 獲取實體信息
        entity = None
        try:
            # 如果是從歷史記錄載入的，需要重新獲取實體
            if 'entity' in group:
                entity = group['entity']
            else:
                entity = await self.client_manager.get_entity(group['id'])
        except Exception as e:
            print(f"\n❌ 無法獲取群組 {group['name']} 的資訊: {e}")
            return
        
        # 獲取訊息
        messages = await self.message_fetcher.get_recent_messages(
            entity,
            days=args.days,
            start_date=args.start_date,
            end_date=args.end_date
        )
        
        if not messages:
            # 根據不同條件顯示不同的提示訊息
            if args.start_date is not None:
                print(f"\n⚠️ 在 {group['name']} 中沒有找到 {args.start_date.strftime('%Y-%m-%d')} 至 {args.end_date.strftime('%Y-%m-%d')} 期間的訊息。")
            elif args.days is not None:
                print(f"\n⚠️ 在 {group['name']} 中沒有找到近 {args.days} 天的訊息。")
            else:
                print(f"\n⚠️ 在 {group['name']} 中沒有找到任何訊息。")
            return
        
        # 分析訊息 - 將 args.top 參數傳遞給 analyze_messages 函數
        print(f"正在分析 {len(messages)} 則訊息...")
        analysis_results = self.message_analyzer.analyze_messages(messages, top_limit=args.top)
        
        # 顯示分析結果
        self.clear_screen()
        self.print_header()
        self.message_analyzer.print_analysis_results(analysis_results, group['name'], args.top)
        
        # 保存分析結果（如果需要）
        if hasattr(args, 'save') and args.save and self.results_storage:
            saved_path = self.message_analyzer.save_analysis_results(
                analysis_results, 
                group['name'],
                self.results_storage
            )
            if saved_path:
                print(f"\n✅ 分析結果已保存到: {saved_path}")
        
        # 取得要轉發的熱門訊息清單
        top_messages = []
        if 'most_reactions' in analysis_results and len(analysis_results['most_reactions']) > 0:
            # 取得最多反應的訊息，使用 args.top 參數限制數量
            top_df = analysis_results['most_reactions'].head(args.top)
            
            # 尋找原始訊息對象
            for _, row in top_df.iterrows():
                msg_id = row['id']
                for orig_msg in messages:
                    if orig_msg['id'] == msg_id:
                        # 將完整的原始訊息添加到列表中
                        top_messages.append({
                            'id': msg_id,
                            'text': orig_msg['text'],
                            'message': msg_id  # 只保存訊息ID，稍後使用ID在目標群組中找到對應訊息
                        })
                        break
        
        # 將熱門訊息轉發到專屬的儲存群組
        print("\n正在將熱門訊息轉發到專屬儲存群組...")
        
        # 決定要傳遞的時間範圍參數
        days_for_forwarding = None
        if args.start_date is not None and args.end_date is not None:
            # 如果指定了起始日期，計算日期範圍
            days_for_forwarding = (args.end_date - args.start_date).days + 1
        elif args.days is not None:
            days_for_forwarding = args.days
        else:
            # 如果沒有指定天數，則使用分析結果中的時間範圍
            if 'period' in analysis_results:
                from datetime import datetime
                period = analysis_results['period']
                start_date = period['start']
                end_date = period['end']
                days_for_forwarding = (end_date - start_date).days + 1
            else:
                days_for_forwarding = 30  # 預設值
        
        success = await self.message_forwarder.forward_top_messages_to_storage_group(
            entity,                # 目標群組
            top_messages,          # 熱門訊息列表
            days_for_forwarding,   # 時間範圍
            all_messages=messages, # 傳入已獲取的訊息集合
            analysis_results=analysis_results  # 傳入分析結果
        )
        
        if success:
            storage_name = f"TG分析-{entity.title}" if hasattr(entity, 'title') else "儲存群組"
            print(f"\n✅ 成功將熱門訊息轉發到 {storage_name}!")
        else:
            print("\n❌ 轉發失敗。請檢查是否有足夠權限創建或使用儲存群組。")

    async def run(self, args):
        """運行主程式流程
        
        Args:
            args: 解析後的命令行參數
        """
        try:
            # 連接到 Telegram
            self.print_header()
            print("\n正在連接到 Telegram API...")
            await self.setup()
            
            # 檢查是否有歷史記錄，如果有則詢問是否使用
            if self.history_groups and self.ask_use_history(args.use_history):
                self.selected_groups = self.history_groups
                print("\n使用歷史記錄中的群組...")
            else:
                # 獲取所有群組和頻道
                print("正在獲取群組列表...")
                dialogs = await self.client_manager.get_all_dialogs()
                
                if not dialogs:
                    print("\n❌ 沒有找到任何群組或頻道，請確認您的帳號已加入至少一個群組或頻道。")
                    return
                
                # 使用鍵盤介面讓用戶選擇多個群組
                self.selected_groups = self.select_groups_by_keyboard(dialogs)
                
                if not self.selected_groups:
                    print("\n已取消操作。")
                    return
                
                # 保存選擇的群組到歷史記錄
                self.save_group_history(self.selected_groups)
            
            # 逐個分析選擇的群組
            for i, group in enumerate(self.selected_groups):
                self.clear_screen()
                self.print_header()
                print(f"\n[{i+1}/{len(self.selected_groups)}] 正在處理群組: {group['name']}")
                await self.analyze_group(group, args)
            
            # 所有群組分析完成後，顯示完成訊息並直接退出程式
            print("\n✅ 所有群組分析完成！")
            sys.exit(0)  # 直接退出程式，返回狀態碼0表示正常結束
            
        except KeyboardInterrupt:
            print("\n\n操作已取消。")
        except Exception as e:
            print(f"\n❌ 發生錯誤: {str(e)}")
            logger.error(f"執行錯誤: {str(e)}", exc_info=True)