"""
Telegram Reviewer 顯示工具模組
此模組包含與顯示分析結果相關的類別和函數
"""
import re
import sys
import time
import logging
from datetime import datetime

# 設定日誌
logger = logging.getLogger(__name__)

# ANSI 顏色代碼
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    
    # 前景色
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # 亮色
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # 背景色
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


# 檢查系統是否支持彩色輸出
def supports_color():
    """檢查當前環境是否支持彩色輸出"""
    # macOS 通常支持顏色輸出
    import os
    if os.getenv('TERM'):
        return True
    return False


class ProgressBar:
        
    def __init__(self, total=None, prefix='', suffix='', decimals=1, length=50, fill='█', print_end='\r'):
        """初始化計數器"""
        self.total = total
        self.prefix = prefix
        self.suffix = suffix
        self.iteration = 0
        self.start_time = time.time()
        self._print_progress()
    
    def update(self, increment=1):
        """更新計數器"""
        self.iteration += increment
        self._print_progress()
    
    def finish(self):
        """完成計數"""
        self._print_progress(is_final=True)
        print()  # 添加換行，使後續輸出在新行
    
    def _print_progress(self, is_final=False):
        """顯示進度"""
        elapsed_time = time.time() - self.start_time
        
        if is_final:
            message = f"\r{self.prefix} 已取得 {self.iteration} 則訊息 ({elapsed_time:.1f} 秒){self.suffix}"
        else:
            message = f"\r{self.prefix} 已取得 {self.iteration} 則訊息...{self.suffix}"
        
        sys.stdout.write(message)
        sys.stdout.flush()


class MessageFormatter:
    """訊息格式化類別，負責將訊息內容格式化為美觀易讀的方式"""
    
    def __init__(self, use_colors=True):
        """初始化格式化器"""
        self.use_colors = use_colors
        self.c = Colors if use_colors else type('NoColors', (), {
            attr: '' for attr in dir(Colors) if not attr.startswith('__')
        })
    
    def format_message_content(self, text):
        """格式化訊息內容，以引用風格顯示"""
        return self.format_message_content_quote_style(text).split("\n")
        
    def format_message_content_quote_style(self, text):
        """以引用風格格式化訊息內容，更好地處理各種符號和特殊格式"""
        # 預處理 URL 和特殊格式
        processed_text = re.sub(r'\[(.*?)\]\((https?://\S+)\)', r'\1 (\2)', text)
        
        # 將內容分行
        lines = []
        for line in processed_text.split('\n'):
            # 跳過空行但保留一個換行
            if not line.strip():
                lines.append("")
                continue
                
            # 處理長行，每行最多70個字符
            current_line = ""
            words = re.findall(r'\S+|\s+', line)  # 按單詞和空格切分
            
            for word in words:
                # 如果添加這個單詞會超出長度，換行
                if len(current_line) + len(word) > 70:
                    lines.append(current_line)
                    current_line = word
                else:
                    current_line += word
            
            if current_line:  # 添加最後一行
                lines.append(current_line)
        
        # 轉換為引用風格的格式
        formatted_lines = []
        
        for i, line in enumerate(lines):
            if not line:  # 處理空行
                formatted_lines.append("")
            else:
                # 使用引用風格，左側有醒目標記
                formatted_lines.append(f"{self.c.BRIGHT_BLUE}│{self.c.RESET} {self.c.WHITE}{line}{self.c.RESET}")
        
        # 返回格式化後的內容
        return "\n".join(formatted_lines)
        

class AnalysisResultsDisplay:
    """分析結果顯示類別，負責將分析結果以美觀的方式呈現給用戶"""
    
    def __init__(self, use_colors=True):
        """初始化顯示器"""
        self.use_colors = use_colors
        self.c = Colors if use_colors else type('NoColors', (), {
            attr: '' for attr in dir(Colors) if not attr.startswith('__')
        })
        self.formatter = MessageFormatter(use_colors)
        
    def print_analysis_results(self, analysis_results, group_name, top_count=5):
        """印出分析結果摘要
        
        Args:
            analysis_results: 分析結果字典
            group_name: 群組名稱
            top_count: 顯示的熱門訊息數量，預設為5
        """
        if not analysis_results:
            print("\n❌ 沒有分析結果可供顯示")
            return
        
        self._print_header(analysis_results, group_name)
        self._print_reactions_ranking(analysis_results, top_count)
        self._print_footer()
    
    def _print_header(self, analysis_results, group_name):
        """印出分析結果標題和基本資訊"""
        period = analysis_results['period']
        total_msgs = analysis_results['total_messages']
        unique_users = analysis_results['unique_users']
        
        print(f"\n{'='*60}")
        print(f"{self.c.BRIGHT_CYAN}📊 {group_name} 訊息分析結果{self.c.RESET}")
        print(f"{'='*60}")
        print(f"📅 分析期間: {self.c.YELLOW}{period['start']} 至 {period['end']}{self.c.RESET}")
        print(f"📝 總訊息數: {self.c.YELLOW}{total_msgs}{self.c.RESET} | 參與用戶數: {self.c.YELLOW}{unique_users}{self.c.RESET}")
        print(f"{'='*60}")
    
    def _print_reactions_ranking(self, analysis_results, top_count):
        """印出表情符號反應排行榜"""
        print(f"\n{self.c.BRIGHT_CYAN}📱 所有表情符號反應總和最高的訊息 TOP {top_count}{self.c.RESET}")
        print(f"{'='*60}")
        
        if not analysis_results['most_reactions'].empty:
            try:
                for i, (_, row) in enumerate(analysis_results['most_reactions'].head(top_count).iterrows(), 1):
                    self._print_message_item(i, row, is_reaction=True)
            except Exception as e:
                print(f"\n❌ 在顯示反應最高訊息時發生錯誤: {str(e)}")
                logger.error(f"顯示反應最高訊息時發生錯誤: {e}")
        else:
            print(f"{self.c.RED}(沒有表情符號反應資料){self.c.RESET}")
    
    def _print_footer(self):
        """印出分析結果頁尾"""
        print(f"\n{self.c.BRIGHT_CYAN}{'='*60}{self.c.RESET}")
    
    def _print_message_item(self, index, row, is_reaction=True):
        """印出單條訊息項目，包含排名、內容和相關統計"""
        # 根據排名獲取不同的顏色
        rank_colors = [self.c.BRIGHT_RED, self.c.BRIGHT_MAGENTA, 
                       self.c.BRIGHT_YELLOW, self.c.BRIGHT_GREEN, self.c.BRIGHT_CYAN]
        rank_color = rank_colors[min(index - 1, len(rank_colors) - 1)]
        
        # 只顯示排名標題，不再顯示使用者名稱
        print(f"\n{rank_color}{'━' * 20} 第 {index} 名 {'━' * 20}{self.c.RESET}")
        
        # 訊息內容部分
        formatted_content = self.formatter.format_message_content_quote_style(row['text'])
        print(f"\n{formatted_content}")
        
        # 統計資訊區塊
        print(f"\n{self.c.BRIGHT_BLACK}{'─' * 50}{self.c.RESET}")
        date_str = row['date'].strftime('%Y-%m-%d %H:%M')
        
        # 準備統計資訊 (已移除回覆相關的條件判斷)
        stats = [
            f"{self.c.CYAN}表情符號{self.c.RESET}: {row['reactions_detail'] if row['reactions_detail'] else '無'}",
            f"{self.c.MAGENTA}反應總數{self.c.RESET}: {row['total_reactions']}"
        ]
        
        # 顯示回覆數
        if 'reply_count' in row:
            stats.append(f"{self.c.MAGENTA}回覆數{self.c.RESET}: {row['reply_count']}")
            
        # 顯示瀏覽數（如果有）
        if 'views' in row and row['views'] is not None and row['views'] > 0:
            stats.append(f"{self.c.BLUE}瀏覽數{self.c.RESET}: {row['views']}")
        
        # 加入使用者資訊和發布時間
        stats.append(f"{self.c.YELLOW}使用者{self.c.RESET}: {row['display_name']}")
        stats.append(f"{self.c.BRIGHT_BLACK}發布時間{self.c.RESET}: {date_str}")
        
        # 每行一個統計項目
        for stat in stats:
            print(f"  {stat}")
        
        # 底部分隔線
        print(f"{self.c.BRIGHT_BLACK}{'─' * 50}{self.c.RESET}")