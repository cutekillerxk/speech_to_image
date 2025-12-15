"""
Gradio应用主程序
简洁的界面，适合小朋友使用
"""
import gradio as gr
from PIL import Image
import os
import time
import shutil
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


def generate_image(text: str):
    """
    生成图片（使用 Gemini 模型，与 ttest.py 一致）
    
    Args:
        text: 文字描述
        
    Returns:
        (Image, str): 生成的图片和状态信息
    """
    global current_image, current_text, current_record_id
    
    if not text or not text.strip():
        return None, "❌ 请输入文字描述"
    
    try:
        # 调用 Gemini 服务生成图片（默认使用 1:1 宽高比，1K 分辨率）
        image, recognized_text = doubao_service.text_to_image_gemini(
            text.strip(),
            aspect_ratio="1:1",
            image_size="1K"
        )
        
        # 保存到历史记录
        record = history_manager.add_record(image, recognized_text)
        current_image = image
        current_text = recognized_text
        current_record_id = record['id']
        
        status = f"✅ 图片生成成功！\n📝 描述：{recognized_text}"
        return image, status
        
    except Exception as e:
        error_msg = f"❌ 生成失败：{str(e)}"
        print(error_msg)
        return None, error_msg


def get_previous_image():
    """获取上一张图片"""
    global current_image, current_text, current_record_id
    
    if current_record_id is None:
        return None, "❌ 没有当前图片"
    
    current_idx = history_manager.get_current_index(current_record_id)
    if current_idx <= 0:
        return current_image, "⚠️ 已经是第一张了"
    
    prev_record = history_manager.get_record(current_idx - 1)
    if prev_record:
        try:
            image = Image.open(prev_record['image_path'])
            current_image = image
            current_text = prev_record['text']
            current_record_id = prev_record['id']
            status = f"📸 第 {current_idx} / {len(history_manager.get_history())} 张\n📝 {prev_record['text']}"
            return image, status
        except Exception as e:
            return current_image, f"❌ 加载失败：{str(e)}"
    
    return current_image, "❌ 无法加载上一张"


def get_next_image():
    """获取下一张图片"""
    global current_image, current_text, current_record_id
    
    if current_record_id is None:
        return None, "❌ 没有当前图片"
    
    current_idx = history_manager.get_current_index(current_record_id)
    history = history_manager.get_history()
    
    if current_idx >= len(history) - 1:
        return current_image, "⚠️ 已经是最后一张了"
    
    next_record = history_manager.get_record(current_idx + 1)
    if next_record:
        try:
            image = Image.open(next_record['image_path'])
            current_image = image
            current_text = next_record['text']
            current_record_id = next_record['id']
            status = f"📸 第 {current_idx + 2} / {len(history)} 张\n📝 {next_record['text']}"
            return image, status
        except Exception as e:
            return current_image, f"❌ 加载失败：{str(e)}"
    
    return current_image, "❌ 无法加载下一张"


def download_image() -> str:
    """下载当前图片"""
    global current_image, current_text
    
    if current_image is None:
        return "❌ 没有可下载的图片"
    
    try:
        # Gradio会自动处理图片下载
        # 这里返回图片路径或提示信息
        return f"✅ 图片已准备好下载\n📝 描述：{current_text}"
    except Exception as e:
        return f"❌ 下载失败：{str(e)}"


def process_audio(audio):
    """
    处理音频，转换为文字
    
    Args:
        audio: Gradio Audio组件返回的文件路径字符串
        
    Returns:
        (str, str): 识别的文字和状态信息
    """
    global current_text
    
    if audio is None:
        return "", "❌ 请先录制音频"
    
    try:
        # Gradio Audio组件（type="numpy"）返回 (sample_rate, data)；兼容字符串路径
        audio_path = None
        
        if isinstance(audio, str):
            # 如果是文件路径，复制到 audio 目录
            if os.path.exists(audio):
                filename = os.path.basename(audio)
                dest_path = os.path.join(AUDIO_DIR, filename)
                shutil.copyfile(audio, dest_path)
                audio_path = dest_path
        elif isinstance(audio, tuple):
            # (sample_rate, audio_data)
            sample_rate, audio_data = audio
            audio_path = os.path.join(AUDIO_DIR, f"audio_{int(time.time() * 1000)}.wav")
            
            # 尝试使用soundfile保存
            try:
                import soundfile as sf
                sf.write(audio_path, audio_data, sample_rate)
            except ImportError:
                # 如果没有soundfile，使用wave
                try:
                    import wave
                    import numpy as np
                    # 转换为int16格式
                    if audio_data.dtype != np.int16:
                        # 归一化到[-1, 1]范围，然后转换为int16
                        if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
                            audio_data = (audio_data * 32767).astype(np.int16)
                        else:
                            audio_data = audio_data.astype(np.int16)
                    with wave.open(audio_path, 'wb') as wf:
                        wf.setnchannels(1 if len(audio_data.shape) == 1 else audio_data.shape[1])
                        wf.setsampwidth(2)  # 16位
                        wf.setframerate(int(sample_rate))
                        wf.writeframes(audio_data.tobytes())
                except Exception as e:
                    print(f"⚠️ 音频保存失败: {e}")
                    return "", f"❌ 音频处理失败: {str(e)}"
        else:
            return "", "❌ 不支持的音频格式"
        
        if not audio_path or not os.path.exists(audio_path):
            return "", "❌ 音频文件不存在"
        
        # 调用语音转文字API
        print(f"🎤 开始识别音频: {audio_path}")
        recognized_text = doubao_service.audio_to_text(audio_path)
        
        # 更新全局文字
        current_text = recognized_text
        
        if recognized_text and recognized_text.strip():
            status = f"✅ 语音识别成功！\n📝 识别文字：{recognized_text}"
            return recognized_text, status
        else:
            return "", "❌ 识别失败，未返回文字"
            
    except Exception as e:
        error_msg = f"❌ 语音识别失败：{str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return "", error_msg


# 初始化：加载最后一张图片
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
            return current_image, f"📸 第 {len(history)} / {len(history)} 张\n📝 {last_record['text']}"
        except Exception as e:
            print(f"⚠️ 加载历史记录失败: {e}")
    
    return None, "👋 欢迎使用！输入文字描述，点击生成按钮开始吧～"


# 创建Gradio界面
with gr.Blocks(title="语音转图片生成器") as app:
    gr.Markdown(
        """
        # 🎨 语音转图片生成器
        
        输入文字描述，生成美丽的图片！
        """
    )
    
    with gr.Row():
        with gr.Column(scale=1):
            # 语音输入区域
            gr.Markdown("### 🎤 语音输入")
            gr.Markdown("点击下方录音按钮开始录音，再次点击结束录音，然后点击“识别语音”按钮")
            
            audio_input = gr.Audio(
                label="🎙️ 录音（点击开始/结束）",
                sources=["microphone"],
                type="numpy",   # 返回 (sample_rate, data)，避免依赖ffmpeg
                format="wav"
            )
            
            recognize_btn = gr.Button(
                "🎯 识别语音",
                variant="secondary",
                size="lg"
            )
            
            recognized_text_output = gr.Textbox(
                label="📝 识别的文字",
                placeholder="识别的文字将显示在这里，并自动填入下方文字输入框...",
                lines=3,
                interactive=True
            )
            
            gr.Markdown("---")
            gr.Markdown("### ✍️ 文字输入（或使用上方识别的文字）")
            
            # 文字输入区域
            text_input = gr.Textbox(
                label="📝 输入文字描述",
                placeholder="例如：一只可爱的小猫在花园里玩耍",
                lines=3,
                max_lines=5
            )
            
            generate_btn = gr.Button(
                "✨ 生成图片",
                variant="primary",
                size="lg"
            )
            
            status_text = gr.Textbox(
                label="状态",
                interactive=False,
                lines=2
            )
        
        with gr.Column(scale=1):
            # 图片显示区域
            image_output = gr.Image(
                label="🎨 生成的图片",
                type="pil",
                height=500
            )
            
            # 控制按钮
            with gr.Row():
                prev_btn = gr.Button("⬅️ 上一张", size="lg")
                next_btn = gr.Button("➡️ 下一张", size="lg")
                download_btn = gr.Button("💾 下载", size="lg")
    
    # 绑定事件
    # 语音识别事件
    recognize_btn.click(
        fn=process_audio,
        inputs=[audio_input],
        outputs=[recognized_text_output, status_text]
    ).then(
        # 识别完成后，自动将文字填入输入框
        fn=lambda x: x if x else "",
        inputs=[recognized_text_output],
        outputs=[text_input]
    )
    
    # 生成图片事件
    generate_btn.click(
        fn=generate_image,
        inputs=[text_input],
        outputs=[image_output, status_text]
    )
    
    prev_btn.click(
        fn=get_previous_image,
        inputs=[],
        outputs=[image_output, status_text]
    )
    
    next_btn.click(
        fn=get_next_image,
        inputs=[],
        outputs=[image_output, status_text]
    )
    
    download_btn.click(
        fn=download_image,
        inputs=[],
        outputs=[status_text]
    )
    
    # 初始化
    app.load(
        fn=init_app,
        inputs=[],
        outputs=[image_output, status_text]
    )


if __name__ == "__main__":
    # 检查API密钥
    if not doubao_service.has_api_key:
        print("⚠️  未配置API_KEY，将使用模拟模式")
        print("📝 请在 .env 文件中配置API_KEY以使用真实功能")
    
    # 启动应用
    print("🚀 启动应用...")
    print("📱 界面将在浏览器中自动打开")
    app.launch(
        # 如遇到本地代理拦截 localhost，可改为 127.0.0.1
        server_name="127.0.0.1",
        server_port=7860,        # Gradio默认端口
        share=False,             # 不创建公共链接
        inbrowser=True,         # 自动打开浏览器
        theme=gr.themes.Soft()  # 主题设置移到launch方法
    )

