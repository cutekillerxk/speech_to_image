"""
历史记录管理器
管理生成的图片历史记录
"""
import os
import json
import time
from datetime import datetime
from PIL import Image
import config


class HistoryManager:
    """历史记录管理类"""
    
    def __init__(self):
        self.history_dir = config.HISTORY_DIR
        self.max_history = config.MAX_HISTORY
        self.history_file = os.path.join(self.history_dir, 'history.json')
        self.history = self._load_history()
    
    def _load_history(self) -> list:
        """加载历史记录"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 加载历史记录失败: {e}")
                return []
        return []
    
    def _save_history(self):
        """保存历史记录"""
        try:
            # 限制历史记录数量
            limited_history = self.history[-self.max_history:]
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(limited_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 保存历史记录失败: {e}")
    
    def add_record(self, image: Image.Image, text: str) -> dict:
        """
        添加新记录
        
        Args:
            image: PIL图片对象
            text: 文字描述
            
        Returns:
            dict: 新添加的记录
        """
        # 生成唯一ID
        record_id = int(time.time() * 1000)
        
        # 保存图片
        image_filename = f"{record_id}.png"
        image_path = os.path.join(self.history_dir, image_filename)
        # 确保图片是 RGB 模式
        if image.mode != 'RGB':
            image = image.convert('RGB')
        # 保存图片（不指定格式参数，让 PIL 自动识别）
        image.save(image_path)
        
        # 创建记录
        record = {
            'id': record_id,
            'text': text,
            'image_path': image_path,
            'timestamp': datetime.now().isoformat()
        }
        
        # 添加到历史记录
        self.history.append(record)
        self._save_history()
        
        return record
    
    def get_history(self) -> list:
        """获取所有历史记录"""
        return self.history
    
    def get_record(self, index: int) -> dict:
        """
        根据索引获取记录
        
        Args:
            index: 记录索引（负数表示从后往前）
            
        Returns:
            dict: 记录信息，如果索引无效返回None
        """
        if not self.history:
            return None
        
        if index < 0:
            index = len(self.history) + index
        
        if 0 <= index < len(self.history):
            return self.history[index]
        
        return None
    
    def get_current_index(self, record_id: int) -> int:
        """
        根据记录ID获取索引
        
        Args:
            record_id: 记录ID
            
        Returns:
            int: 索引，如果未找到返回-1
        """
        for i, record in enumerate(self.history):
            if record['id'] == record_id:
                return i
        return -1
    
    def clear_history(self):
        """清空历史记录"""
        self.history = []
        self._save_history()
        
        # 删除所有图片文件
        for filename in os.listdir(self.history_dir):
            if filename.endswith('.png'):
                try:
                    os.remove(os.path.join(self.history_dir, filename))
                except Exception as e:
                    print(f"⚠️ 删除图片失败: {e}")


# 创建全局历史管理器实例
history_manager = HistoryManager()

