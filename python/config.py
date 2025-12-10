"""
配置文件
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 豆包API配置
# 支持两种方式：DMX_API_KEY（推荐）或 API_KEY
DOUBAO_API_KEY = os.getenv('DMX_API_KEY') or os.getenv('API_KEY', '')
DOUBAO_API_BASE_URL = os.getenv('BASE_URL', 'https://ark.cn-beijing.volces.com/api/v3')

# 音频转文字API URL
STT_URL = os.getenv('STT_URL', '')

# 文字生成图片API URL（DMX API）
TTI_URL = os.getenv('TTI_URL', 'https://www.dmxapi.cn/v1/images/generations')

# 应用配置
HISTORY_DIR = os.path.join(os.path.dirname(__file__), 'history')
MAX_HISTORY = 50  # 最多保存50条历史记录

# 确保历史记录目录存在
os.makedirs(HISTORY_DIR, exist_ok=True)

