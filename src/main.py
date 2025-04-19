#!/usr/bin/env python3
import os
import sys
import asyncio
import argparse
import logging
import shutil
import json
from datetime import datetime
from pathlib import Path

from telegram_analyzer import TelegramAnalyzer

# 取得程式根目錄的路徑
ROOT_DIR = Path(__file__).parent.parent.absolute()
# 群組記錄文件路徑 - 保存在程式根目錄
GROUP_HISTORY_FILE = ROOT_DIR / "telegram_reviewer_history.json"
# 日誌目錄
LOG_DIR = ROOT_DIR / "logs"

# 確保日誌目錄存在
if not LOG_DIR.exists():
    LOG_DIR.mkdir(exist_ok=True)

# 設定日誌文件名稱，按日期命名
log_file = LOG_DIR / f"telegram_reviewer_{datetime.now().strftime('%Y-%m-%d')}.log"

# 設定日誌格式
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 創建檔案處理器
file_handler = logging.FileHandler(filename=log_file, encoding='utf-8')
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

# 創建控制台處理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

# 設定根日誌記錄器
logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])
logger = logging.getLogger(__name__)

logger.info(f"程式啟動 - 日誌將保存在: {log_file}")

class CommandLineInterface:
    """命令列互動介面，用於選擇群組查看熱門訊息"""

    def __init__(self):
        """初始化命令列介面"""
        self.analyzer = TelegramAnalyzer(session_name='telegram_reviewer_session')
        # 獲取終端寬度
        self.terminal_width = shutil.get_terminal_size().columns
        # 確保最小寬度
        self.terminal_width = max(self.terminal_width, 40)
        # 儲存使用者選擇的群組
        self.selected_groups = []
        # 上次選擇的群組紀錄
        self.history_groups = self.load_group_history()

    async def setup(self):
        """連接到 Telegram API"""
        try:
            await self.analyzer.connect()
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

    def load_group_history(self):
        """載入上次選擇的群組記錄"""
        if GROUP_HISTORY_FILE.exists():
            try:
                with open(GROUP_HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"載入群組歷史記錄失敗: {e}")
        return []

    def save_group_history(self, groups):
        """儲存選擇的群組"""
        try:
            # 只保存必要信息，避免存儲過多數據
            simplified_groups = []
            for group in groups:
                simplified_groups.append({
                    'id': group['id'],
                    'name': group['name'],
                    'type': group['type']
                })
                
            with open(GROUP_HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(simplified_groups, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存群組歷史記錄失敗: {e}")

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
        
    def ask_use_history(self):
        """詢問是否使用歷史記錄的群組"""
        if not self.history_groups:
            return False
            
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
        """分析單個群組並顯示結果"""
        print(f"\n正在分析 {group['name']} 的近 {args.days} 天訊息...")
        print(f"(最多分析 {args.limit} 則訊息，請稍候...)")
        
        # 獲取實體信息
        entity = None
        try:
            # 如果是從歷史記錄載入的，需要重新獲取實體
            if 'entity' in group:
                entity = group['entity']
            else:
                entity = await self.analyzer.client.get_entity(group['id'])
        except Exception as e:
            print(f"\n❌ 無法獲取群組 {group['name']} 的資訊: {e}")
            return
        
        # 獲取訊息
        messages = await self.analyzer.get_recent_messages(
            entity,
            days=args.days,
            limit=args.limit
        )
        
        if not messages:
            print(f"\n⚠️ 在 {group['name']} 中沒有找到任何近 {args.days} 天的訊息。")
            return
        
        # 分析訊息
        print(f"正在分析 {len(messages)} 則訊息...")
        analysis_results = self.analyzer.analyze_messages(messages)
        
        # 顯示分析結果
        self.clear_screen()
        self.print_header()
        self.analyzer.print_analysis_results(analysis_results, group['name'], args.top)
        
        # 取得要轉發的熱門訊息清單
        top_messages = []
        if 'most_reactions' in analysis_results and len(analysis_results['most_reactions']) > 0:
            # 取得最多反應的訊息
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
        success = await self.analyzer.forward_top_messages_to_storage_group(
            entity,  # 目標群組
            top_messages,  # 熱門訊息列表
            args.days  # 時間範圍
        )
        
        if success:
            storage_name = f"TG分析-{entity.title}" if hasattr(entity, 'title') else "儲存群組"
            print(f"\n✅ 成功將熱門訊息轉發到 {storage_name}!")
        else:
            print("\n❌ 轉發失敗。請檢查是否有足夠權限創建或使用儲存群組。")

    async def run(self):
        """運行主程式流程"""
        parser = argparse.ArgumentParser(description='Telegram 群組熱門訊息分析工具')
        parser.add_argument('--days', type=int, default=30, help='分析最近幾天的訊息 (預設: 30)')
        parser.add_argument('--limit', type=int, default=1000, help='分析的訊息數量上限 (預設: 1000)')
        parser.add_argument('--top', type=int, default=5, help='顯示和轉發的熱門訊息數量 (預設: 5)')
        args = parser.parse_args()
        
        try:
            # 連接到 Telegram
            self.print_header()
            print("\n正在連接到 Telegram API...")
            await self.setup()
            
            # 檢查是否有歷史記錄，如果有則詢問是否使用
            if self.history_groups and self.ask_use_history():
                self.selected_groups = self.history_groups
                print("\n使用歷史記錄中的群組...")
            else:
                # 獲取所有群組和頻道
                print("正在獲取群組列表...")
                dialogs = await self.analyzer.get_all_dialogs()
                
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
            
            # 所有群組分析完成後，直接結束程式
            print("\n✅ 所有群組分析完成！")
            print("程式結束。")
            
        except KeyboardInterrupt:
            print("\n\n操作已取消。")
        except Exception as e:
            print(f"\n❌ 發生錯誤: {str(e)}")


def main():
    """主程式入口點"""
    cli = CommandLineInterface()
    asyncio.run(cli.run())


if __name__ == "__main__":
    main()