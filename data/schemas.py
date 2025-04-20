"""
數據結構定義
定義了程式中使用的各種數據結構
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class User:
    """用戶信息結構"""
    id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    @property
    def display_name(self) -> str:
        """獲取用於顯示的名稱"""
        if self.first_name:
            name = self.first_name
            if self.last_name:
                name += f" {self.last_name}"
            return f"{name}（{self.username or self.id}）"
        return f"未知用戶（{self.id}）"


@dataclass
class Reaction:
    """表情符號反應結構"""
    emoji: str
    count: int


@dataclass
class Message:
    """訊息結構"""
    id: int
    date: datetime
    text: str
    sender: Optional[User] = None
    reactions: List[Reaction] = None
    total_reactions: int = 0
    reply_count: int = 0
    views: int = 0
    forwards: int = 0
    
    def __post_init__(self):
        if self.reactions is None:
            self.reactions = []
            self.total_reactions = 0
        else:
            self.total_reactions = sum(r.count for r in self.reactions)


@dataclass
class GroupInfo:
    """群組信息結構"""
    id: int
    name: str
    type: str  # '群組' 或 '頻道'
    members_count: int = 0
    entity: Any = None  # Telegram API 的原始實體對象


@dataclass
class AnalysisResults:
    """分析結果結構"""
    group_name: str
    period_start: datetime
    period_end: datetime
    total_messages: int
    unique_users: int
    most_reactions: List[Message]
    messages_per_day: Dict[datetime, int]
    user_activity: Dict[str, int]
    emoji_stats: Dict[str, int]