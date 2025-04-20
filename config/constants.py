#!/usr/bin/env python3
"""
Telegram Reviewer 常數定義
此模組包含程式中使用的所有常數
"""

# 預設分析參數
DEFAULT_DAYS = 30
DEFAULT_MESSAGE_LIMIT = 1000
DEFAULT_TOP_COUNT = 5
DEFAULT_USE_HISTORY = None  # None 表示會詢問用戶，True 表示默認使用歷史記錄，False 表示默認不使用

# 訊息類型定義
MESSAGE_TYPE_TEXT = 'text'
MESSAGE_TYPE_PHOTO = 'photo'
MESSAGE_TYPE_VIDEO = 'video'
MESSAGE_TYPE_DOCUMENT = 'document'
MESSAGE_TYPE_AUDIO = 'audio'
MESSAGE_TYPE_ANIMATION = 'animation'
MESSAGE_TYPE_STICKER = 'sticker'
MESSAGE_TYPE_UNKNOWN = 'unknown'

# 分析結果類型
ANALYSIS_TYPE_REACTIONS = 'reactions'
ANALYSIS_TYPE_REPLIES = 'replies'
ANALYSIS_TYPE_FORWARDS = 'forwards'
ANALYSIS_TYPE_VIEWS = 'views'