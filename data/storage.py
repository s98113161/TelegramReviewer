"""
數據存儲模組
處理本地數據的讀取和存儲功能
"""

import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# 從配置中導入
from config.settings import GROUP_HISTORY_FILE

# 設定日誌
logger = logging.getLogger(__name__)


class GroupHistoryManager:
    """群組歷史記錄管理器
    負責讀取和保存用戶選擇的群組歷史
    """
    
    @staticmethod
    def load_group_history() -> List[Dict[str, Any]]:
        """載入群組歷史記錄
        
        Returns:
            List[Dict[str, Any]]: 群組信息列表
        """
        if GROUP_HISTORY_FILE.exists():
            try:
                with open(GROUP_HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"載入群組歷史記錄失敗: {e}")
        return []
    
    @staticmethod
    def save_group_history(groups: List[Dict[str, Any]]) -> bool:
        """保存群組歷史記錄
        
        Args:
            groups: 群組信息列表
            
        Returns:
            bool: 是否保存成功
        """
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
            return True
        except Exception as e:
            logger.error(f"保存群組歷史記錄失敗: {e}")
            return False


class ResultsStorage:
    """分析結果存儲管理器
    用於保存和讀取分析結果
    """
    
    def __init__(self, results_dir: Path):
        """初始化結果存儲管理器
        
        Args:
            results_dir: 結果存儲目錄
        """
        self.results_dir = results_dir
        self.results_dir.mkdir(exist_ok=True)
    
    def save_analysis_results(self, group_name: str, results: Dict[str, Any]) -> Optional[Path]:
        """保存分析結果到文件
        
        Args:
            group_name: 群組名稱
            results: 分析結果數據
            
        Returns:
            Optional[Path]: 保存的文件路徑
        """
        from datetime import datetime
        
        # 創建安全的文件名
        safe_name = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in group_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"analysis_{safe_name}_{timestamp}.json"
        file_path = self.results_dir / file_name
        
        try:
            # 轉換日期對象為字符串
            serializable_results = self._prepare_for_serialization(results)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"分析結果已保存到 {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"保存分析結果失敗: {e}")
            return None
    
    def _prepare_for_serialization(self, data: Any) -> Any:
        """將數據準備為可序列化的格式
        
        Args:
            data: 待序列化的數據
            
        Returns:
            Any: 可序列化的數據
        """
        from datetime import datetime
        import pandas as pd
        
        if isinstance(data, dict):
            return {k: self._prepare_for_serialization(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._prepare_for_serialization(item) for item in data]
        elif isinstance(data, pd.DataFrame):
            return data.to_dict('records')
        elif isinstance(data, datetime):
            return data.isoformat()
        elif hasattr(data, '__dict__'):
            return self._prepare_for_serialization(data.__dict__)
        else:
            return data