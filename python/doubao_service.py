"""
豆包大模型API服务
实现文字转图片和音频转文字功能
"""
import requests
import base64
from io import BytesIO
from PIL import Image
import config

# 尝试导入 Gemini SDK（可选）
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ google-genai 未安装，Gemini 图像生成功能不可用")


class DoubaoService:
    """豆包API服务类"""
    
    def __init__(self):
        self.api_key = config.DOUBAO_API_KEY
        self.base_url = config.DOUBAO_API_BASE_URL
        self.stt_url = config.STT_URL  # 音频转文字API URL
        self.tti_url = config.TTI_URL  # 文字生成图片API URL
        self.gemini_base_url = config.GEMINI_BASE_URL
        self.gemini_model = config.GEMINI_MODEL
        self.has_api_key = bool(self.api_key)
        
        # 初始化 Gemini 客户端（如果可用）
        self.gemini_client = None
        if GEMINI_AVAILABLE and self.has_api_key:
            try:
                self.gemini_client = genai.Client(
                    api_key=self.api_key,
                    http_options={'base_url': self.gemini_base_url}
                )
                print(f"✅ Gemini 客户端已初始化")
            except Exception as e:
                print(f"⚠️ Gemini 客户端初始化失败: {e}")
        
        # 调试信息：检查API密钥（只显示前10个字符，保护隐私）
        if self.has_api_key:
            masked_key = self.api_key[:10] + "..." if len(self.api_key) > 10 else self.api_key
            print(f"✅ API密钥已加载: {masked_key}")
            print(f"📡 TTI URL: {self.tti_url}")
        else:
            print("⚠️  未检测到API密钥，将使用模拟模式")
    
    def audio_to_text(self, audio_file_path: str):
        """
        音频转文字
        
        Args:
            audio_file_path: 音频文件路径
            
        Returns:
            str: 识别的文字
        """
        if not self.has_api_key:
            # 模拟模式
            return "这是一段测试文字，用于生成图片"
        
        try:
            # 使用配置的STT_URL（根据 test.py，使用 .com 域名）
            api_url = self.stt_url if self.stt_url else 'https://www.dmxapi.com/v1/audio/transcriptions'
            
            # 调试信息
            print(f"🔗 STT请求URL: {api_url}")
            print(f"📁 音频文件: {audio_file_path}")
            
            # 读取音频文件
            with open(audio_file_path, 'rb') as audio_file:
                # 按照网站示例格式：file 直接是文件对象，model 作为表单字段放在 files 中
                files = {
                    "file": audio_file,              # 音频文件二进制流
                    "model": (None, "whisper-1"),   # 指定使用 Whisper-1 模型（表单字段格式）
                }
                
                headers = {"Authorization": f"Bearer {self.api_key}"}
                
                # 发送请求（只使用 files 参数，不需要 data 参数）
                response = requests.post(
                    api_url,
                    headers=headers,
                    files=files,
                    timeout=60
                )
                
                response.raise_for_status()
                result = response.json()
                
                # 根据API响应格式解析（返回 {"text": "..."}）
                voice_text = result.get("text", "")
                if voice_text:
                    print(f"✅ 识别成功: {voice_text}")
                    return voice_text
                else:
                    print(f"⚠️ API返回空文本: {result}")
                    return "音频识别失败，未返回文本"
                
        except requests.exceptions.HTTPError as e:
            error_detail = ""
            if e.response is not None:
                try:
                    error_data = e.response.json()
                    error_detail = f" - {error_data}"
                    if e.response.status_code == 401:
                        print("=" * 60)
                        print("❌ API密钥验证失败 (401 Unauthorized)")
                        print("请检查 .env 文件中的 DMX_API_KEY 是否正确")
                        print("=" * 60)
                except:
                    error_detail = f" - {e.response.text}"
            print(f"❌ 音频转文字HTTP错误 ({e.response.status_code if e.response else 'N/A'}): {e}{error_detail}")
            return "音频识别失败，请检查API密钥和网络连接"
        except requests.exceptions.RequestException as e:
            print(f"❌ 音频转文字网络错误: {e}")
            return "音频识别失败，网络连接错误"
        except Exception as e:
            print(f"❌ 音频转文字错误: {e}")
            import traceback
            traceback.print_exc()
            return f"音频识别失败: {str(e)}"
    
    def text_to_image_gemini(self, text: str, aspect_ratio: str = "1:1", image_size: str = "1K"):
        """
        使用 Gemini 模型生成图片
        
        Args:
            text: 文字描述
            aspect_ratio: 图片宽高比，默认 "1:1"
            image_size: 图片尺寸，默认 "1K"（支持 "1K", "2K", "4K"）
            
        Returns:
            (PIL.Image, str): 生成的图片对象和原始文字
        """
        if not self.has_api_key:
            return self._mock_text_to_image(text)
        
        if not GEMINI_AVAILABLE:
            print("⚠️ Gemini SDK 未安装，回退到 Doubao 模型")
            return self.text_to_image(text, use_gemini=False)
        
        if not self.gemini_client:
            print("⚠️ Gemini 客户端未初始化，回退到 Doubao 模型")
            return self.text_to_image(text, use_gemini=False)
        
        try:
            print(f"🎨 使用 Gemini 模型生成图片")
            print(f"📝 提示词: {text[:50]}..." if len(text) > 50 else f"📝 提示词: {text}")
            
            # 调用 Gemini API
            # 构建 image_config
            image_config_dict = {"aspect_ratio": aspect_ratio}
            # 只有非 1K 时才设置 image_size（1K 是默认值）
            if image_size != "1K":
                image_config_dict["image_size"] = image_size
            
            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=[text],
                config=types.GenerateContentConfig(
                    response_modalities=['Image'],
                    image_config=types.ImageConfig(**image_config_dict),
                )
            )
            
            # 处理响应
            for part in response.parts:
                if part.inline_data is not None:
                    # 将响应数据转换为 PIL Image 对象
                    image = part.as_image()
                    # 确保返回的是标准的 PIL Image 对象
                    # part.as_image() 应该已经返回 PIL Image，但为了安全起见进行验证
                    if not isinstance(image, Image.Image):
                        # 如果返回的不是 PIL Image，尝试从数据创建
                        from io import BytesIO
                        if hasattr(part.inline_data, 'data'):
                            image = Image.open(BytesIO(part.inline_data.data))
                        elif hasattr(part.inline_data, 'mime_type') and 'image' in part.inline_data.mime_type:
                            # 尝试从 base64 数据创建
                            import base64
                            image_data = base64.b64decode(part.inline_data.data)
                            image = Image.open(BytesIO(image_data))
                        else:
                            raise ValueError(f"无法将响应转换为 PIL Image，类型: {type(image)}")
                    
                    # 确保图片是 RGB 模式（避免保存时的问题）
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    
                    return image, text
            
            # 如果没有找到图片，返回错误
            raise ValueError("Gemini API 响应中未找到图片数据")
            
        except Exception as e:
            print(f"❌ Gemini 图片生成错误: {e}")
            import traceback
            traceback.print_exc()
            # 回退到 Doubao 模型
            print("🔄 回退到 Doubao 模型")
            return self.text_to_image(text, use_gemini=False)
    
    def text_to_image(self, text: str, use_gemini: bool = False, aspect_ratio: str = "1:1", image_size: str = "1K"):
        """
        文字生成图片
        
        Args:
            text: 文字描述
            use_gemini: 是否使用 Gemini 模型，默认 False（使用 Doubao）
            aspect_ratio: 图片宽高比（仅 Gemini 使用）
            image_size: 图片尺寸（仅 Gemini 使用）
            
        Returns:
            (PIL.Image, str): 生成的图片对象和原始文字
        """
        # 如果选择使用 Gemini
        if use_gemini:
            return self.text_to_image_gemini(text, aspect_ratio, image_size)
        
        if not self.has_api_key:
            # 模拟模式：返回占位图片
            return self._mock_text_to_image(text)
        
        try:
            # 使用配置的TTI_URL，确保使用正确的DMX API端点（与tttest.py保持一致）
            # 默认使用 https://www.dmxapi.com/v1/images/generations
            api_url = self.tti_url if self.tti_url else "https://www.dmxapi.com/v1/images/generations"
            
            # 构建请求参数（根据DMX API格式，与tttest.py保持一致）
            request_data = {
                "model": "doubao-seedream-4-0-250828",  # 使用4.0模型
                "prompt": text,
                "size": "2K",  # 支持 "1K", "2K", "4K" 或具体像素值如 "2048x2048"
                "stream": False,
                "response_format": "url",  # 或 "b64_json"
                "watermark": False
            }
            
            # 构建请求头（与tttest.py保持一致）
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # 调试信息
            print(f"🔗 请求URL: {api_url}")
            print(f"📝 提示词: {text[:50]}..." if len(text) > 50 else f"📝 提示词: {text}")
            print(f"🤖 使用模型: {request_data['model']}")
            
            # 调用豆包文生图API（与tttest.py的请求方式保持一致）
            response = requests.post(
                api_url,
                headers=headers,
                json=request_data,
                timeout=120  # 图片生成可能需要更长时间
            )
            
            response.raise_for_status()
            data = response.json()
            
            # 调试信息：输出响应状态
            print(f"✅ API响应成功，状态码: {response.status_code}")
            
            # 根据DMX API响应格式解析（与tttest.py的响应格式一致）
            # 响应格式：{"data": [{"url": "..."}]} 或 {"data": [{"b64_json": "..."}]}
            if 'data' in data and len(data['data']) > 0:
                image_data_item = data['data'][0]
                image_url = image_data_item.get('url', '')
                image_b64 = image_data_item.get('b64_json', '')
                
                if image_b64:
                    # 从base64解码图片
                    print("📥 从base64数据解码图片")
                    image_data = base64.b64decode(image_b64)
                    image = Image.open(BytesIO(image_data))
                    print(f"✅ 图片解码成功，尺寸: {image.size}")
                    return image, text
                elif image_url:
                    # 从URL下载图片
                    print(f"📥 从URL下载图片: {image_url[:80]}...")
                    img_response = requests.get(image_url, timeout=30)
                    img_response.raise_for_status()
                    image = Image.open(BytesIO(img_response.content))
                    print(f"✅ 图片下载成功，尺寸: {image.size}")
                    return image, text
                else:
                    print(f"❌ API响应中未找到图片数据，响应内容: {data}")
                    raise ValueError("API响应中未找到图片数据")
            else:
                # 兼容其他可能的响应格式
                image_url = data.get('url', '')
                image_b64 = data.get('b64_json', '')
                
                if image_b64:
                    image_data = base64.b64decode(image_b64)
                    image = Image.open(BytesIO(image_data))
                    return image, text
                elif image_url:
                    img_response = requests.get(image_url, timeout=30)
                    img_response.raise_for_status()
                    image = Image.open(BytesIO(img_response.content))
                    return image, text
                else:
                    raise ValueError(f"API响应格式异常: {data}")
                
        except requests.exceptions.HTTPError as e:
            error_detail = ""
            if e.response is not None:
                try:
                    error_data = e.response.json()
                    error_detail = f" - {error_data}"
                    # 如果是401错误，给出更详细的提示
                    if e.response.status_code == 401:
                        print("=" * 60)
                        print("❌ API密钥验证失败 (401 Unauthorized)")
                        print("请检查以下事项：")
                        print("1. .env 文件中的 DMX_API_KEY 或 API_KEY 是否正确")
                        print("2. API密钥格式是否正确（应该是 sk- 开头）")
                        print("3. API密钥是否有效（未过期或被撤销）")
                        print("4. .env 文件是否在 python/ 目录下")
                        print("=" * 60)
                except:
                    error_detail = f" - {e.response.text}"
            print(f"❌ API调用HTTP错误 ({e.response.status_code if e.response else 'N/A'}): {e}{error_detail}")
            # API调用失败时返回占位图片
            return self._mock_text_to_image(text)
        except requests.exceptions.RequestException as e:
            print(f"❌ API调用错误: {e}")
            # API调用失败时返回占位图片
            return self._mock_text_to_image(text)
        except Exception as e:
            print(f"❌ 图片生成错误: {e}")
            import traceback
            traceback.print_exc()
            return self._mock_text_to_image(text)
    
    def _mock_text_to_image(self, text: str):
        """
        模拟图片生成（用于测试）
        
        Args:
            text: 文字描述
            
        Returns:
            (PIL.Image, str): 占位图片和文字
        """
        # 创建一个简单的占位图片
        img = Image.new('RGB', (1024, 1024), color='#f0f0f0')
        from PIL import ImageDraw, ImageFont
        
        draw = ImageDraw.Draw(img)
        
        # 尝试使用系统字体
        try:
            # Windows系统字体
            font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 60)
        except:
            try:
                # 备用字体
                font = ImageFont.truetype("arial.ttf", 60)
            except:
                font = ImageFont.load_default()
        
        # 在图片上绘制文字
        text_lines = self._wrap_text(text, 20)  # 每行20个字符
        y_offset = 400
        for line in text_lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (1024 - text_width) // 2
            draw.text((x, y_offset), line, fill='#666666', font=font)
            y_offset += 80
        
        # 添加提示文字
        hint = "（测试模式 - 请配置API密钥）"
        bbox = draw.textbbox((0, 0), hint, font=font)
        text_width = bbox[2] - bbox[0]
        x = (1024 - text_width) // 2
        draw.text((x, y_offset + 40), hint, fill='#999999', font=font)
        
        return img, text
    
    def _wrap_text(self, text: str, max_chars: int) -> list:
        """将文字按最大字符数换行"""
        lines = []
        current_line = ""
        
        for char in text:
            if len(current_line) >= max_chars:
                lines.append(current_line)
                current_line = char
            else:
                current_line += char
        
        if current_line:
            lines.append(current_line)
        
        return lines if lines else [text]


# 创建全局服务实例
doubao_service = DoubaoService()
