"""
语音魔法画板 - 全屏展示版
自动监听，图片全屏显示
"""
import gradio as gr
from PIL import Image
import os
import time
import shutil
import json
import requests
from fastapi import FastAPI, Request, UploadFile, File
from starlette.responses import JSONResponse
import tempfile
from doubao_service import doubao_service
from history_manager import history_manager


# ========== 显示配置参数 ==========
DISPLAY_CONFIG = {
    # 显示模式: "fit_height", "fit_width", "fit_screen", "custom"
    "mode": "fit_height",
    # 自定义尺寸（当 mode="custom" 时使用）
    "custom_height": 900,  # 像素
    "custom_width": 900,  # 像素
    # 屏幕信息（可选，用于预设）
    "screen_size": "15.6inch",  # 15.6英寸，344mm*194mm
}

# 根据配置计算图片显示尺寸
def get_image_size():
    """根据配置返回图片显示尺寸"""
    mode = DISPLAY_CONFIG.get("mode", "fit_height")
    
    if mode == "custom":
        return DISPLAY_CONFIG.get("custom_height", 900), DISPLAY_CONFIG.get("custom_width", 900)
    elif mode == "fit_height":
        # 以高度为准，适合 15.6 英寸屏幕（通常 1920x1080）
        # 使用 90% 的屏幕高度，保持 1:1 比例
        return 900, 900  # 可以根据实际屏幕调整
    elif mode == "fit_width":
        # 以宽度为准
        return 1200, 1200
    else:  # fit_screen
        # 填满屏幕
        return 1000, 1000
    
    return 900, 900  # 默认值

# 目录配置
BASE_DIR = os.path.dirname(__file__)
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

# 全局状态
current_image = None
current_text = ""
current_record_id = None


def process_audio_and_generate(audio, progress=gr.Progress()):
    """
    处理音频并自动生成图片（完整流程）
    
    Args:
        audio: Gradio Audio组件返回的音频数据
        progress: Gradio进度条对象（自动注入）
        
    Returns:
        gr.update: 使用 gr.update() 保持当前图片，只在成功时更新
    """
    global current_image, current_text, current_record_id
    
    if audio is None:
        print("⚠️ 未检测到音频数据")
        # 使用 gr.update() 保持当前图片
        return gr.update(value=current_image) if current_image else None
    
    try:
        # 记录总开始时间
        total_start_time = time.time()
        # 初始化时间统计变量
        stt_duration = 0.0
        tti_duration = 0.0
        
        # ========== 阶段1: 音频处理 ==========
        if progress:
            progress(0.1, desc="开始生成")
        progress_status = "开始生成"
        print("=" * 60)
        print("🚀 开始处理流程")
        print("=" * 60)
        
        audio_path = None
        
        # 处理音频数据
        if isinstance(audio, str):
            if os.path.exists(audio):
                audio_abs = os.path.abspath(audio)
                audio_dir_abs = os.path.abspath(AUDIO_DIR)
                
                # 检查文件是否已经在 audio 目录下
                if audio_abs.startswith(audio_dir_abs):
                    # 文件已经在 audio 目录下，直接使用
                    audio_path = audio_abs
                    print(f"📁 音频文件已在 audio 目录: {audio_path}")
                else:
                    # 文件不在 audio 目录下，需要复制
                    filename = os.path.basename(audio)
                    dest_path = os.path.join(AUDIO_DIR, filename)
                    dest_abs = os.path.abspath(dest_path)
                    
                    # 如果源文件和目标文件是同一个文件，跳过复制
                    if audio_abs != dest_abs:
                        shutil.copyfile(audio, dest_path)
                    audio_path = dest_path
                    print(f"📁 音频文件已复制到: {audio_path}")
        elif isinstance(audio, tuple):
            sample_rate, audio_data = audio
            # 先保存为临时 wav 文件，然后转换为 webm
            temp_wav_path = os.path.join(AUDIO_DIR, f"temp_{int(time.time() * 1000)}.wav")
            audio_path = os.path.join(AUDIO_DIR, f"audio_{int(time.time() * 1000)}.webm")
            print(f"📁 保存音频到: {audio_path}")
            print(f"📊 采样率: {sample_rate}, 数据形状: {audio_data.shape if hasattr(audio_data, 'shape') else 'N/A'}")
            
            # 先保存为 wav 文件
            try:
                import soundfile as sf
                sf.write(temp_wav_path, audio_data, sample_rate)
                print("✅ 使用 soundfile 保存临时 wav 成功")
            except ImportError:
                try:
                    import wave
                    import numpy as np
                    if audio_data.dtype != np.int16:
                        if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
                            audio_data = (audio_data * 32767).astype(np.int16)
                        else:
                            audio_data = audio_data.astype(np.int16)
                    with wave.open(temp_wav_path, 'wb') as wf:
                        wf.setnchannels(1 if len(audio_data.shape) == 1 else audio_data.shape[1])
                        wf.setsampwidth(2)
                        wf.setframerate(int(sample_rate))
                        wf.writeframes(audio_data.tobytes())
                    print("✅ 使用 wave 保存临时 wav 成功")
                except Exception as e:
                    print(f"❌ 音频保存失败: {e}")
                    import traceback
                    traceback.print_exc()
                    return gr.update(value=current_image) if current_image else None
            
            # 尝试转换为 webm 格式
            try:
                from pydub import AudioSegment
                # 加载 wav 文件并导出为 webm
                audio_segment = AudioSegment.from_wav(temp_wav_path)
                audio_segment.export(audio_path, format="webm")
                # 删除临时 wav 文件
                if os.path.exists(temp_wav_path):
                    os.remove(temp_wav_path)
                print("✅ 转换为 webm 格式成功")
            except ImportError:
                # 如果没有 pydub，尝试使用 ffmpeg
                try:
                    import subprocess
                    subprocess.run([
                        "ffmpeg", "-i", temp_wav_path, "-c:a", "libopus", 
                        "-b:a", "64k", audio_path, "-y"
                    ], check=True, capture_output=True)
                    # 删除临时 wav 文件
                    if os.path.exists(temp_wav_path):
                        os.remove(temp_wav_path)
                    print("✅ 使用 ffmpeg 转换为 webm 格式成功")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # 如果无法转换为 webm，直接使用 wav 文件
                    print("⚠️ 无法转换为 webm，使用 wav 格式")
                    audio_path = temp_wav_path
                    # 重命名为 webm（虽然实际是 wav，但 API 应该能处理）
                    webm_path = audio_path.replace('.wav', '.webm')
                    shutil.move(audio_path, webm_path)
                    audio_path = webm_path
            except Exception as e:
                # 如果转换失败，使用 wav 文件
                print(f"⚠️ 转换为 webm 失败: {e}，使用 wav 格式")
                audio_path = temp_wav_path
                # 重命名为 webm（虽然实际是 wav，但 API 应该能处理）
                webm_path = audio_path.replace('.wav', '.webm')
                if os.path.exists(audio_path):
                    shutil.move(audio_path, webm_path)
                    audio_path = webm_path
        else:
            print(f"❌ 不支持的音频格式: {type(audio)}")
            return gr.update(value=current_image) if current_image else None
        
        if not audio_path or not os.path.exists(audio_path):
            print("❌ 音频文件不存在")
            return gr.update(value=current_image) if current_image else None
        
        # ========== 阶段2: 音频转文字 ==========
        if progress:
            progress(0.3, desc="音频处理中")
        progress_status = "音频处理中"
        print("-" * 60)
        print("🎤 开始语音识别")
        print(f"📁 音频文件: {audio_path}")
        
        # 如果音频文件是 webm 格式，需要转换为 wav（Whisper API 需要）
        actual_audio_path = audio_path
        temp_wav_path = None
        
        if audio_path.lower().endswith('.webm'):
            print("🔄 检测到 webm 格式，转换为 wav 格式以适配 Whisper API...")
            conversion_success = False
            temp_wav_path = os.path.join(AUDIO_DIR, f"temp_{int(time.time() * 1000)}.wav")
            
            # 方法1：优先尝试直接使用 ffmpeg（最直接的方法）
            try:
                import subprocess
                # 使用 ffmpeg 转换：webm -> wav (16kHz, 单声道, PCM 16位)
                result = subprocess.run([
                    "ffmpeg", "-i", audio_path, "-acodec", "pcm_s16le",
                    "-ar", "16000", "-ac", "1", temp_wav_path, "-y"
                ], check=True, capture_output=True, timeout=30)
                actual_audio_path = temp_wav_path
                conversion_success = True
                print("✅ 使用 ffmpeg 转换为 wav 成功")
            except FileNotFoundError:
                # ffmpeg 未找到，尝试使用 pydub（pydub 也需要 ffmpeg，但可能路径不同）
                try:
                    from pydub import AudioSegment
                    audio_segment = AudioSegment.from_file(audio_path, format="webm")
                    audio_segment.export(temp_wav_path, format="wav")
                    actual_audio_path = temp_wav_path
                    conversion_success = True
                    print("✅ 使用 pydub 转换为 wav 成功")
                except (ImportError, Exception) as e:
                    print(f"⚠️ pydub 转换失败: {e}")
                    conversion_success = False
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                print(f"⚠️ ffmpeg 转换失败: {e}")
                conversion_success = False
            
            # 如果转换失败，给出清晰的错误提示
            if not conversion_success:
                error_msg = (
                    "❌ 无法将 webm 转换为 wav 格式\n"
                    "💡 解决方案：\n"
                    "   1. 安装 ffmpeg：\n"
                    "      - Windows: 下载 https://ffmpeg.org/download.html\n"
                    "      - 或使用: choco install ffmpeg (需要 Chocolatey)\n"
                    "   2. 将 ffmpeg 添加到系统 PATH 环境变量\n"
                    "   3. 重启终端后重试\n"
                    "⚠️ 尝试直接使用 webm 文件（可能失败）"
                )
                print(error_msg)
                # 仍然尝试使用原始文件（可能失败）
        
        # 开始计时：音频转文字
        stt_start_time = time.time()
        try:
            recognized_text = doubao_service.audio_to_text(actual_audio_path)
            stt_end_time = time.time()
            stt_duration = stt_end_time - stt_start_time
            
            print(f"✅ 识别成功: {recognized_text}")
            print(f"⏱️ 音频转文字耗时: {stt_duration:.2f} 秒")
            
            if not recognized_text or not recognized_text.strip():
                print("❌ 识别结果为空")
                return gr.update(value=current_image) if current_image else None
            
            current_text = recognized_text.strip()
            
        except Exception as e:
            stt_end_time = time.time()
            stt_duration = stt_end_time - stt_start_time
            print(f"❌ 语音识别错误: {e}")
            print(f"⏱️ 音频转文字耗时: {stt_duration:.2f} 秒（失败）")
            import traceback
            traceback.print_exc()
            return gr.update(value=current_image) if current_image else None
        finally:
            # 清理临时 wav 文件
            if temp_wav_path and os.path.exists(temp_wav_path):
                try:
                    os.remove(temp_wav_path)
                    print(f"🗑️ 已清理临时文件: {temp_wav_path}")
                except Exception as e:
                    print(f"⚠️ 清理临时文件失败: {e}")
        
        # ========== 阶段3: 文本生成完毕 ==========
        if progress:
            progress(0.5, desc="文本生成完毕")
        progress_status = "文本生成完毕"
        print("-" * 60)
        print(f"📝 识别文字: {current_text}")
        
        # ========== 阶段4: 文字转图片 ==========
        if progress:
            progress(0.6, desc="文本处理中")
        progress_status = "文本处理中"
        print("-" * 60)
        print("🎨 开始生成图片")
        print(f"📝 提示词: {current_text}")
        
        # 开始计时：文字转图片
        tti_start_time = time.time()
        try:
            image, recognized_text = doubao_service.text_to_image_gemini(
                current_text,
                aspect_ratio="1:1",
                image_size="1K"
            )
            tti_end_time = time.time()
            tti_duration = tti_end_time - tti_start_time
            
            print(f"✅ 图片生成成功")
            print(f"🖼️ 图片尺寸: {image.size if image else 'N/A'}")
            print(f"⏱️ 文字转图片耗时: {tti_duration:.2f} 秒")
            
        except Exception as e:
            tti_end_time = time.time()
            tti_duration = tti_end_time - tti_start_time
            print(f"❌ 图片生成错误: {e}")
            print(f"⏱️ 文字转图片耗时: {tti_duration:.2f} 秒（失败）")
            import traceback
            traceback.print_exc()
            return gr.update(value=current_image) if current_image else None
        
        # ========== 阶段5: 保存到历史记录 ==========
        if progress:
            progress(0.9, desc="图片生成完毕")
        progress_status = "图片生成完毕"
        print("-" * 60)
        print("💾 保存到历史记录")
        
        try:
            record = history_manager.add_record(image, recognized_text)
            current_image = image
            current_text = recognized_text
            current_record_id = record['id']
            print(f"✅ 保存成功，记录ID: {current_record_id}")
        except Exception as e:
            print(f"⚠️ 保存历史记录失败: {e}")
            import traceback
            traceback.print_exc()
        
        # ========== 完成 ==========
        if progress:
            progress(1.0, desc="完成")
        
        # 计算总耗时
        total_end_time = time.time()
        total_duration = total_end_time - total_start_time
        
        print("=" * 60)
        print("✅ 流程完成！")
        print(f"📝 文字: {recognized_text}")
        print(f"🖼️ 图片ID: {current_record_id}")
        print("-" * 60)
        print("⏱️ 时间统计:")
        print(f"   - 音频转文字: {stt_duration:.2f} 秒")
        print(f"   - 文字转图片: {tti_duration:.2f} 秒")
        print(f"   - 总耗时: {total_duration:.2f} 秒")
        print("=" * 60)
        
        # 成功时返回新图片
        return gr.update(value=image)
        
    except Exception as e:
        # 计算总耗时（即使失败）
        total_end_time = time.time()
        total_duration = total_end_time - total_start_time
        
        error_msg = f"❌ 处理失败: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        
        # 输出时间统计（即使失败）
        print("-" * 60)
        print("⏱️ 时间统计（失败）:")
        if stt_duration > 0:
            print(f"   - 音频转文字: {stt_duration:.2f} 秒")
        else:
            print(f"   - 音频转文字: 未完成")
        if tti_duration > 0:
            print(f"   - 文字转图片: {tti_duration:.2f} 秒")
        else:
            print(f"   - 文字转图片: 未完成")
        print(f"   - 总耗时: {total_duration:.2f} 秒")
        print("=" * 60)
        
        # 保持当前图片不变，使用 gr.update() 避免清空
        return gr.update(value=current_image) if current_image else None


def get_previous_image():
    """获取上一张图片"""
    global current_image, current_text, current_record_id
    
    if current_record_id is None:
        print("⚠️ 没有当前图片")
        return None
    
    current_idx = history_manager.get_current_index(current_record_id)
    if current_idx <= 0:
        print("⚠️ 已经是第一张")
        return current_image
    
    prev_record = history_manager.get_record(current_idx - 1)
    if prev_record:
        try:
            image = Image.open(prev_record['image_path'])
            current_image = image
            current_text = prev_record['text']
            current_record_id = prev_record['id']
            print(f"📸 切换到上一张: {prev_record['text']}")
            return image
        except Exception as e:
            print(f"❌ 加载失败: {e}")
            return current_image
    
    return current_image


def get_next_image():
    """获取下一张图片"""
    global current_image, current_text, current_record_id
    
    if current_record_id is None:
        print("⚠️ 没有当前图片")
        return None
    
    current_idx = history_manager.get_current_index(current_record_id)
    history = history_manager.get_history()
    
    if current_idx >= len(history) - 1:
        print("⚠️ 已经是最后一张")
        return current_image
    
    next_record = history_manager.get_record(current_idx + 1)
    if next_record:
        try:
            image = Image.open(next_record['image_path'])
            current_image = image
            current_text = next_record['text']
            current_record_id = next_record['id']
            print(f"📸 切换到下一张: {next_record['text']}")
            return image
        except Exception as e:
            print(f"❌ 加载失败: {e}")
            return current_image
    
    return current_image


def init_app():
    """初始化应用，加载最后一张历史记录"""
    global current_image, current_text, current_record_id
    
    history = history_manager.get_history()
    if history:
        last_record = history[-1]
        try:
            current_image = Image.open(last_record['image_path'])
            current_text = last_record['text']
            current_record_id = last_record['id']
            print(f"📸 加载历史记录: {last_record['text']}")
            return current_image
        except Exception as e:
            print(f"⚠️ 加载历史记录失败: {e}")
    
    print("👋 应用初始化完成")
    return None


app = FastAPI()


@app.post("/vad_upload")
async def vad_upload(file: UploadFile = File(...)):
    """
    接收前端 VAD 录音（webm/wav），保存临时文件，复用现有处理逻辑
    """
    try:
        print("🛰️ /vad_upload 收到请求")
        suffix = ".webm"
        filename = f"vad_{int(time.time() * 1000)}{suffix}"
        temp_path = os.path.join(AUDIO_DIR, filename)
        # 保存文件
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        print(f"💾 VAD 音频已保存: {temp_path}")
        # 直接用文件路径进入现有流程（process_audio_and_generate 支持路径）
        process_audio_and_generate(temp_path, progress=None)
        print("✅ VAD 音频处理完成")
        # 返回当前图片信息，供前端更新
        global current_record_id
        return {
            "status": "ok",
            "record_id": current_record_id,
            "timestamp": int(time.time() * 1000)
        }
    except Exception as e:
        print(f"❌ VAD 上传处理失败: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({"status": "error", "msg": str(e)}, status_code=500)


@app.get("/get_latest_image")
async def get_latest_image():
    """
    获取最新的图片信息，用于前端更新显示
    返回图片的 base64 编码，方便前端直接显示
    """
    global current_image, current_record_id
    if current_image and current_record_id:
        try:
            import base64
            from io import BytesIO
            
            # 将图片转换为 base64
            buffer = BytesIO()
            current_image.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            history = history_manager.get_history()
            if history:
                last_record = history[-1]
                return {
                    "status": "ok",
                    "record_id": last_record['id'],
                    "image_data": f"data:image/png;base64,{img_base64}",
                    "text": last_record['text']
                }
        except Exception as e:
            print(f"❌ 获取图片失败: {e}")
            return {"status": "error", "msg": str(e)}
    return {"status": "no_image"}


# 创建Gradio界面（全屏图片显示）
# 获取图片显示尺寸
img_height, img_width = get_image_size()

# 自定义 CSS 样式，让图片全屏显示（模拟 Gradio 全屏效果）
custom_css = """
/* 移除 Gradio 默认的边距和填充 */
.gradio-container {
    padding: 0 !important;
    margin: 0 !important;
    max-width: 100% !important;
    height: 100vh !important;
    overflow: hidden !important;
}

/* 隐藏导航栏和标题 */
header, footer, .gradio-header {
    display: none !important;
}

/* 主容器全屏 */
.main {
    padding: 0 !important;
    margin: 0 !important;
    height: 100vh !important;
    width: 100vw !important;
    overflow: hidden !important;
}

/* 图片容器全屏（模拟 Gradio 全屏模式） */
.image-container,
.image-container > div,
.image-container .image-preview,
.image-container .image-preview > div {
    width: 100vw !important;
    height: 100vh !important;
    max-width: 100vw !important;
    max-height: 100vh !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background-color: #000 !important;
    margin: 0 !important;
    padding: 0 !important;
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    z-index: 9999 !important;
}

/* 图片本身居中显示，保持比例 */
.image-container img,
.image-container canvas {
    max-width: 100vw !important;
    max-height: 100vh !important;
    width: auto !important;
    height: auto !important;
    object-fit: contain !important;
    margin: auto !important;
}

/* 隐藏全屏按钮（因为已经是全屏了） */
.image-container button[aria-label*="fullscreen"],
.image-container button[title*="fullscreen"],
.image-container .fullscreen-button {
    display: none !important;
}
"""

with gr.Blocks(title="语音魔法画板", css=custom_css, theme=gr.themes.Monochrome()) as demo:
    # 只显示图片，全屏展示
    image_output = gr.Image(
        label="",
        type="pil",
        height=img_height,
        width=img_width,
        show_label=False,
        container=False,
        elem_classes="image-container"
    )
    
    # 注意：导航功能函数（get_previous_image, get_next_image）已保留
    # 但不显示按钮，如需使用可通过键盘快捷键等方式触发
    
    # 注入前端JS，自动启动 VAD 监听（无需按钮）
    # Gradio 的 js 参数必须是函数表达式，不能是顶层语句
    vad_js = """
() => {
  // 所有变量挂到 window，避免 Gradio AsyncFunction 解析问题
  window.vadState = window.vadState || {};
  window.vadState.audioContext = null;
  window.vadState.mediaStream = null;
  window.vadState.analyser = null;
  window.vadState.processor = null;
  window.vadState.recorder = null;
  window.vadState.isListening = false;
  window.vadState.isRecording = false;
  window.vadState.chunks = [];
  window.vadState.silenceStart = null;

  window.vadConfig = {
    THRESHOLD: 0.08,
    SILENCE_THRESHOLD: 0.03,
    SILENCE_DURATION: 3000
  };

  window.vadStartListening = function () {
    if (window.vadState.isListening) {
      console.log('[VAD] 已经在监听中');
      return;
    }

    console.log('[VAD] 自动启动监听，申请麦克风权限...');
    navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
      window.vadState.mediaStream = stream;

      window.vadState.audioContext = new AudioContext();
      window.vadState.audioContext.resume();

      var sourceNode =
        window.vadState.audioContext.createMediaStreamSource(stream);
      window.vadState.analyser =
        window.vadState.audioContext.createAnalyser();
      window.vadState.analyser.fftSize = 2048;

      window.vadState.processor =
        window.vadState.audioContext.createScriptProcessor(2048, 1, 1);

      sourceNode.connect(window.vadState.analyser);
      window.vadState.analyser.connect(window.vadState.processor);
      window.vadState.processor.connect(
        window.vadState.audioContext.destination
      );

      window.vadState.recorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm'
      });

      window.vadState.recorder.ondataavailable = function (e) {
        if (e.data && e.data.size > 0) {
          window.vadState.chunks.push(e.data);
        }
      };

      window.vadState.recorder.onstop = function () {
        if (window.vadState.chunks.length === 0) {
          console.log('[VAD] 未录到音频');
          return;
        }

        var blob = new Blob(window.vadState.chunks, { type: 'audio/webm' });
        window.vadState.chunks = [];

        console.log('[VAD] 上传音频，大小:', blob.size, 'bytes');
        var formData = new FormData();
        formData.append('file', blob, 'audio.webm');

        var uploadStartTime = Date.now();
        var lastRecordId = window.vadState.lastRecordId || null;
        
        fetch('/vad_upload', { method: 'POST', body: formData })
          .then(function (response) {
            if (!response.ok) {
              throw new Error('HTTP ' + response.status);
            }
            return response.json();
          })
          .then(function (data) {
            console.log('[VAD] 上传成功，响应:', data);
            // 保存当前记录ID
            if (data.record_id) {
              window.vadState.lastRecordId = data.record_id;
            }
            // 开始轮询检查新图片
            if (window.checkForNewImage) {
              console.log('[VAD] 开始检查新图片，上次ID:', lastRecordId);
              window.checkForNewImage(uploadStartTime, lastRecordId);
            } else {
              console.error('[VAD] checkForNewImage 函数不存在');
            }
          })
          .catch(function (error) {
            console.error('[VAD] 上传失败:', error);
          });
      };

      window.vadState.processor.onaudioprocess = function () {
        var data = new Uint8Array(window.vadState.analyser.fftSize);
        window.vadState.analyser.getByteTimeDomainData(data);

        var sum = 0;
        for (var i = 0; i < data.length; i++) {
          var v = data[i] / 128 - 1;
          sum += v * v;
        }
        var vol = Math.sqrt(sum / data.length);

        if (!window.vadState.isRecording && vol > window.vadConfig.THRESHOLD) {
          window.vadState.recorder.start();
          window.vadState.isRecording = true;
          window.vadState.silenceStart = null;
          console.log('[VAD] 开始录制，音量:', vol.toFixed(3));
        } else if (window.vadState.isRecording && vol < window.vadConfig.SILENCE_THRESHOLD) {
          if (window.vadState.silenceStart === null) {
            window.vadState.silenceStart = performance.now();
          } else if (
            performance.now() - window.vadState.silenceStart >
            window.vadConfig.SILENCE_DURATION
          ) {
            window.vadState.recorder.stop();
            window.vadState.isRecording = false;
            window.vadState.silenceStart = null;
            console.log('[VAD] 停止录制（检测到静音）');
          }
        } else {
          window.vadState.silenceStart = null;
        }
      };

      window.vadState.isListening = true;
      console.log('[VAD] 监听已启动，等待语音输入...');
    }).catch(function (error) {
      console.error('[VAD] 获取麦克风权限失败:', error);
      console.log('[VAD] 请在浏览器中允许麦克风权限，然后刷新页面');
    });
  };

  // 检查并更新新图片
  window.checkForNewImage = function (startTime, lastRecordId) {
    console.log('[Image] 开始检查新图片，上次ID:', lastRecordId);
    var checkCount = 0;
    var maxChecks = 60; // 最多检查60次（约30秒）
    var checkInterval = 500; // 每500ms检查一次

    var checkIntervalId = setInterval(function () {
      checkCount++;
      console.log('[Image] 检查第', checkCount, '次，上次ID:', lastRecordId);
      
      fetch('/get_latest_image')
        .then(function (response) {
          if (!response.ok) {
            throw new Error('HTTP ' + response.status);
          }
          return response.json();
        })
        .then(function (data) {
          console.log('[Image] API 返回:', data.status, '记录ID:', data.record_id);
          
          if (data.status === 'ok' && data.record_id && data.image_data) {
            // 如果图片ID变化了，说明有新图片生成
            if (!lastRecordId || data.record_id !== lastRecordId) {
              console.log('[Image] ✅ 检测到新图片！ID:', data.record_id, '（上次:', lastRecordId, '）');
              clearInterval(checkIntervalId);
              
              // 更新图片显示（使用 base64 图片数据）
              if (window.updateImageDisplay) {
                window.updateImageDisplay(data.image_data);
              } else {
                console.error('[Image] updateImageDisplay 函数不存在');
              }
              return;
            } else {
              console.log('[Image] 图片ID未变化，继续等待...');
            }
          } else if (data.status === 'no_image') {
            console.log('[Image] 暂无图片');
          } else {
            console.log('[Image] 数据不完整:', data);
          }

          // 如果超过最大检查次数，停止检查
          if (checkCount >= maxChecks) {
            console.log('[Image] ⏰ 超时，停止检查新图片（已检查', checkCount, '次）');
            clearInterval(checkIntervalId);
          }
        })
        .catch(function (error) {
          console.error('[Image] ❌ 检查图片失败:', error);
          if (checkCount >= maxChecks) {
            console.log('[Image] 达到最大检查次数，停止检查');
            clearInterval(checkIntervalId);
          }
        });
    }, checkInterval);
  };

  // 更新图片显示
  window.updateImageDisplay = function (imageData) {
    console.log('[Image] 开始更新图片显示，数据长度:', imageData ? imageData.length : 0);
    
    // 方法1: 查找所有可能的图片元素
    var selectors = [
      '.image-container img',
      '[data-testid="image"] img',
      'img[src*="data:image"]',
      'img[src*="history"]',
      'img',
      'canvas'
    ];
    
    var imageElements = [];
    selectors.forEach(function (selector) {
      var elements = document.querySelectorAll(selector);
      elements.forEach(function (el) {
        if (imageElements.indexOf(el) === -1) {
          imageElements.push(el);
        }
      });
    });
    
    console.log('[Image] 找到', imageElements.length, '个图片元素');
    
    if (imageElements.length > 0) {
      var updated = false;
      // 更新所有图片元素
      imageElements.forEach(function (element) {
        try {
          if (element.tagName === 'IMG') {
            console.log('[Image] 更新 IMG 元素，当前 src:', element.src.substring(0, 50));
            element.src = imageData; // 直接使用 base64 数据
            element.style.display = 'block';
            updated = true;
          } else if (element.tagName === 'CANVAS') {
            console.log('[Image] 更新 CANVAS 元素');
            // 如果是 canvas，需要重新绘制
            var img = new Image();
            img.onload = function () {
              var ctx = element.getContext('2d');
              var maxWidth = element.width || window.innerWidth;
              var maxHeight = element.height || window.innerHeight;
              var scale = Math.min(maxWidth / img.width, maxHeight / img.height);
              var drawWidth = img.width * scale;
              var drawHeight = img.height * scale;
              var x = (maxWidth - drawWidth) / 2;
              var y = (maxHeight - drawHeight) / 2;
              ctx.clearRect(0, 0, element.width, element.height);
              ctx.drawImage(img, x, y, drawWidth, drawHeight);
              updated = true;
            };
            img.src = imageData;
          }
        } catch (e) {
          console.error('[Image] 更新元素失败:', e);
        }
      });
      
      if (updated) {
        console.log('[Image] 图片已更新');
        
        // 重新应用全屏样式
        setTimeout(function () {
          if (window.autoFullscreenImage) {
            window.autoFullscreenImage();
          }
        }, 200);
      }
    } else {
      console.warn('[Image] 未找到图片元素，3秒后刷新页面');
      // 如果找不到图片元素，尝试刷新页面
      setTimeout(function () {
        console.log('[Image] 刷新页面以显示新图片');
        window.location.reload();
      }, 3000);
    }
    
    // 备用方案：如果3秒后图片还没更新，强制刷新页面
    setTimeout(function () {
      var currentImages = document.querySelectorAll('img[src*="data:image"]');
      var hasNewImage = false;
      currentImages.forEach(function (img) {
        if (img.src === imageData || img.src.indexOf(imageData.substring(0, 50)) >= 0) {
          hasNewImage = true;
        }
      });
      
      if (!hasNewImage) {
        console.log('[Image] 备用方案：强制刷新页面');
        window.location.reload();
      }
    }, 3000);
  };

  // 初始化：获取当前记录ID
  function initRecordId() {
    fetch('/get_latest_image')
      .then(function (response) {
        return response.json();
      })
      .then(function (data) {
        if (data.status === 'ok' && data.record_id) {
          window.vadState.lastRecordId = data.record_id;
          console.log('[Image] 初始化记录ID:', data.record_id);
        }
      })
      .catch(function (error) {
        console.error('[Image] 获取初始记录ID失败:', error);
      });
  }

  // 页面加载完成后自动启动监听
  function autoStartVAD() {
    // 先初始化记录ID
    initRecordId();
    
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
      // 稍微延迟，确保 DOM 完全就绪
      setTimeout(function () {
        console.log('[VAD] 页面加载完成，自动启动监听...');
        window.vadStartListening();
      }, 1000);
    } else {
      window.addEventListener('load', function () {
        setTimeout(function () {
          console.log('[VAD] 页面加载完成，自动启动监听...');
          window.vadStartListening();
        }, 1000);
      });
    }
  }

  // 立即尝试启动（如果 DOM 已就绪）
  autoStartVAD();
  
  // 也监听 DOMContentLoaded 事件
  document.addEventListener('DOMContentLoaded', function () {
    setTimeout(function () {
      if (!window.vadState.isListening) {
        console.log('[VAD] DOM 就绪，自动启动监听...');
        window.vadStartListening();
      }
    }, 1000);
  });

  // 自动触发图片全屏显示（挂到 window 对象，供外部调用）
  window.autoFullscreenImage = function () {
    function tryFullscreen() {
      // 方法1: 查找并点击全屏按钮
      var fullscreenButtons = document.querySelectorAll(
        'button[aria-label*="fullscreen"], button[title*="fullscreen"], button[aria-label*="全屏"]'
      );
      if (fullscreenButtons.length > 0) {
        console.log('[Fullscreen] 找到全屏按钮，自动点击');
        fullscreenButtons[0].click();
        return true;
      }

      // 方法2: 查找图片容器并应用全屏样式
      var imageContainers = document.querySelectorAll('.image-container, [data-testid="image"]');
      imageContainers.forEach(function (container) {
        if (container) {
          container.style.position = 'fixed';
          container.style.top = '0';
          container.style.left = '0';
          container.style.width = '100vw';
          container.style.height = '100vh';
          container.style.zIndex = '9999';
          container.style.backgroundColor = '#000';
          container.style.display = 'flex';
          container.style.alignItems = 'center';
          container.style.justifyContent = 'center';
          console.log('[Fullscreen] 应用全屏样式到图片容器');
        }
      });

      // 方法3: 查找图片并确保全屏显示
      var images = document.querySelectorAll('.image-container img, [data-testid="image"] img');
      images.forEach(function (img) {
        if (img) {
          img.style.maxWidth = '100vw';
          img.style.maxHeight = '100vh';
          img.style.width = 'auto';
          img.style.height = 'auto';
          img.style.objectFit = 'contain';
          console.log('[Fullscreen] 应用全屏样式到图片');
        }
      });

      return false;
    }

    // 页面加载后尝试全屏
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
      setTimeout(tryFullscreen, 500);
    } else {
      window.addEventListener('load', function () {
        setTimeout(tryFullscreen, 500);
      });
    }

    // 监听图片更新事件（Gradio 更新图片时）
    var observer = new MutationObserver(function (mutations) {
      setTimeout(tryFullscreen, 100);
    });

    // 观察整个文档的变化
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    // 也监听 DOMContentLoaded
    document.addEventListener('DOMContentLoaded', function () {
      setTimeout(tryFullscreen, 500);
    });
  }

  // 启动自动全屏
  window.autoFullscreenImage();
}
"""
    
    # 初始化并注入 JavaScript（使用 js 参数）
    demo.load(
        fn=init_app,
        inputs=[],
        outputs=[image_output],
        js=vad_js
    )


if __name__ == "__main__":
    # 检查API密钥
    if not doubao_service.has_api_key:
        print("⚠️  未配置API_KEY，将使用模拟模式")
        print("📝 请在 .env 文件中配置API_KEY以使用真实功能")
    
    # 将 Gradio 挂载到 FastAPI
    app = gr.mount_gradio_app(app, demo, path="/")
    print("🚀 全屏展示版启动中 (端口 7860)...")
    print(f"📐 图片显示尺寸: {img_width}x{img_height} (模式: {DISPLAY_CONFIG['mode']})")
    print("🎙️ 监听功能将在页面加载时自动启动")
    print("💡 首次访问需要在浏览器中允许麦克风权限")
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=7860)
