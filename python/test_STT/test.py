import requests
import os
import json
from dotenv import load_dotenv


load_dotenv()

api_key =  os.getenv("DMX_API_KEY", "")

url = "https://www.dmxapi.com/v1/audio/transcriptions"

headers = {
    "Authorization": f"Bearer {api_key}"
}

audio_file_path = r"E:\sti\speech_to_image\python\audio\audio_1765460967778.wav"

with open(audio_file_path, "rb") as audio_file:
    files = {
        "file": audio_file,              
        "model": (None, "whisper-1"),  
    }
    
    response = requests.post(url, headers=headers, files=files)

print(f"📊 HTTP 状态码: {response.status_code}")
print("=" * 60)
print("📄 响应内容:")
print("=" * 60)

if response.status_code == 200:
    try:
        # 解析 JSON 响应数据
        response_data = response.json()
        # 格式化输出,保留中文字符,缩进 2 个空格
        print(json.dumps(response_data, ensure_ascii=False, indent=2))
    except requests.exceptions.JSONDecodeError:
        # 如果响应不是有效的 JSON 格式,输出原始文本
        print("⚠️ 响应不是 JSON 格式:")
        print(response.text)
else:
    # 【错误响应处理】
    # 如果请求失败,尝试格式化输出错误信息
    try:
        error_data = response.json()
        print("❌ 错误详情:")
        print(json.dumps(error_data, ensure_ascii=False, indent=2))
    except:
        # 如果错误响应也不是 JSON 格式,直接输出原始文本
        print("❌ 请求失败,原始响应:")
        print(response.text)