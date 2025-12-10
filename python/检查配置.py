"""
配置检查脚本
用于检查API配置是否正确
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

print("=" * 60)
print("配置检查")
print("=" * 60)

# 检查.env文件
env_file = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_file):
    print(f"✅ .env 文件存在: {env_file}")
else:
    print(f"❌ .env 文件不存在: {env_file}")
    print("   请创建 .env 文件并配置API密钥")

print()

# 检查API密钥
dmx_key = os.getenv('DMX_API_KEY', '')
api_key = os.getenv('API_KEY', '')

if dmx_key:
    masked = dmx_key[:10] + "..." if len(dmx_key) > 10 else dmx_key
    print(f"✅ DMX_API_KEY: {masked}")
    if not dmx_key.startswith('sk-'):
        print("   ⚠️  警告: API密钥应该以 'sk-' 开头")
elif api_key:
    masked = api_key[:10] + "..." if len(api_key) > 10 else api_key
    print(f"✅ API_KEY: {masked}")
    if not api_key.startswith('sk-'):
        print("   ⚠️  警告: API密钥应该以 'sk-' 开头")
else:
    print("❌ 未找到API密钥")
    print("   请在 .env 文件中配置 DMX_API_KEY 或 API_KEY")

print()

# 检查URL配置
stt_url = os.getenv('STT_URL', '')
tti_url = os.getenv('TTI_URL', '')

if tti_url:
    print(f"✅ TTI_URL: {tti_url}")
else:
    print("ℹ️  TTI_URL: 未配置，将使用默认值")
    print("   默认值: https://www.dmxapi.cn/v1/images/generations")

if stt_url:
    print(f"✅ STT_URL: {stt_url}")
else:
    print("ℹ️  STT_URL: 未配置")

print()
print("=" * 60)

