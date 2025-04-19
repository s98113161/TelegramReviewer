"""
訊息分析模組
處理訊息的分析相關功能
"""
import pandas as pd
from datetime import datetime

# 將相對導入改為絕對導入
from src.utils.logger import logger
from src.utils.display_utils import AnalysisResultsDisplay

class MessageAnalyzer:
    """訊息分析類，負責分析Telegram訊息數據"""
    
    def __init__(self, use_colors=True):
        """初始化訊息分析器
        
        Args:
            use_colors: 是否使用顏色輸出
        """
        self.use_colors = use_colors
        self.display = AnalysisResultsDisplay(use_colors)
    
    def analyze_messages(self, messages):
        """分析訊息數據
        
        Args:
            messages: 訊息列表
            
        Returns:
            dict: 分析結果字典
        """
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
        
        # 使用者活躍度分析
        user_activity = df.groupby('display_name').size().reset_index(name='count')
        user_activity = user_activity.sort_values('count', ascending=False).head(10)
        
        # 表情符號使用統計
        emoji_usage = {}
        for reactions in df['reactions']:
            if reactions:
                for reaction in reactions:
                    emoji = reaction['emoji']
                    count = reaction['count']
                    emoji_usage[emoji] = emoji_usage.get(emoji, 0) + count
        
        emoji_stats = pd.DataFrame([{'emoji': k, 'count': v} for k, v in emoji_usage.items()])
        if not emoji_stats.empty:
            emoji_stats = emoji_stats.sort_values('count', ascending=False).head(10)
        
        # 整合分析結果
        analysis_results = {
            'most_reactions': most_reactions,  # 所有表情符號反應總和最高的訊息
            'most_replied': most_replied,      # 回覆數最多的訊息
            'messages_per_day': messages_per_day,  # 每日訊息統計
            'user_activity': user_activity,    # 使用者活躍度
            'emoji_stats': emoji_stats,        # 表情符號使用統計
            'total_messages': len(df),         # 總訊息數
            'unique_users': df['display_name'].nunique(),  # 獨立使用者數
            'period': {
                'start': df['date'].min().date(),
                'end': df['date'].max().date()
            }
        }
        
        logger.info("訊息分析完成")
        return analysis_results
    
    def print_analysis_results(self, analysis_results, group_name, top_count=5):
        """印出分析結果摘要
        
        Args:
            analysis_results: 分析結果字典
            group_name: 群組名稱
            top_count: 顯示的熱門訊息數量，預設為5
        """
        self.display.print_analysis_results(analysis_results, group_name, top_count)