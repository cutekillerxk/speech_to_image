"""
语音魔法画板 - 简化版
一键录音，自动生成图片
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
        
        try:
            recognized_text = doubao_service.audio_to_text(actual_audio_path)
            print(f"✅ 识别成功: {recognized_text}")
            
            if not recognized_text or not recognized_text.strip():
                print("❌ 识别结果为空")
                return gr.update(value=current_image) if current_image else None
            
            current_text = recognized_text.strip()
            
        except Exception as e:
            print(f"❌ 语音识别错误: {e}")
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
        
        try:
            image, recognized_text = doubao_service.text_to_image_gemini(
                current_text,
                aspect_ratio="1:1",
                image_size="1K"
            )
            print(f"✅ 图片生成成功")
            print(f"🖼️ 图片尺寸: {image.size if image else 'N/A'}")
            
        except Exception as e:
            print(f"❌ 图片生成错误: {e}")
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
        print("=" * 60)
        print("✅ 流程完成！")
        print(f"📝 文字: {recognized_text}")
        print(f"🖼️ 图片ID: {current_record_id}")
        print("=" * 60)
        
        # 成功时返回新图片
        return gr.update(value=image)
        
    except Exception as e:
        error_msg = f"❌ 处理失败: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
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


@app.post("/listen_click")
async def listen_click():
    print("🛰️ 前端触发开启监听按钮")
    return {"status": "ok"}


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
        return {"status": "ok"}
    except Exception as e:
        print(f"❌ VAD 上传处理失败: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({"status": "error", "msg": str(e)}, status_code=500)


# 创建Gradio界面（左右布局：左侧标题+按钮，右侧图片）
with gr.Blocks(title="语音魔法画板") as demo:
    with gr.Row():
        # 左侧列：标题 + 按钮
        with gr.Column(scale=1):
            gr.Markdown("## 语音魔法画板", elem_classes="title")
            prev_btn = gr.Button("⬅️ 上一张", size="lg")
            next_btn = gr.Button("➡️ 下一张", size="lg")
            listen_btn = gr.Button("🎙️ 开启监听", variant="primary", size="lg", elem_id="listen-btn")
            gr.Markdown(
                "<div id='vad-status'>未监听</div>",
                elem_id="vad-status-container"
            )
        # 右侧列：图片展示区域（占据主要宽度）
        with gr.Column(scale=4):
            image_output = gr.Image(
                label="",
                type="pil",
                height=700,
                show_label=False
            )
    
    # 上一张/下一张按钮
    prev_btn.click(
        fn=get_previous_image,
        inputs=[],
        outputs=[image_output]
    )
    
    next_btn.click(
        fn=get_next_image,
        inputs=[],
        outputs=[image_output]
    )
    
    # 注入前端JS，完成 VAD 自动录制与上传
    # Gradio 的 js 参数必须是函数表达式，不能是顶层语句
    vad_js = """
() => {
  // 所有变量挂到 window，避免 Gradio AsyncFunction 解析问题
  window.vadState = window.vadState || {};
  window.vadState.statusDiv = null;
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
    SILENCE_DURATION: 1000
  };

  window.vadSetStatus = function (text) {
    if (window.vadState.statusDiv) {
      window.vadState.statusDiv.innerText = text;
    }
    console.log('[VAD]', text);
  };

  window.vadBindButton = function () {
    window.vadState.statusDiv = document.getElementById('vad-status');
    var btn = document.getElementById('listen-btn');

    if (!btn) {
      console.warn('[VAD] listen-btn not found');
      return;
    }
    if (btn._vad_bound) return;

    btn.addEventListener('click', function () {
      fetch('/listen_click', { method: 'POST' }).catch(function () {});
      window.vadStartListening();
    });
    btn._vad_bound = true;
    window.vadSetStatus('点击开启监听');
  };

  window.vadStartListening = function () {
    if (window.vadState.isListening) return;

    window.vadSetStatus('申请麦克风权限...');
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
        if (window.vadState.chunks.length === 0) return;

        var blob = new Blob(window.vadState.chunks, { type: 'audio/webm' });
        window.vadState.chunks = [];

        var formData = new FormData();
        formData.append('file', blob, 'audio.webm');

        fetch('/vad_upload', { method: 'POST', body: formData });
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
          }
        } else {
          window.vadState.silenceStart = null;
        }
      };

      window.vadState.isListening = true;
      window.vadSetStatus('监听中...');
    });
  };

  setTimeout(window.vadBindButton, 500);
  setTimeout(window.vadBindButton, 1500);
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
    print("🚀 自动监听版启动中 (端口 7860)...")
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=7860)
