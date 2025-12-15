"""
独立图片查看服务（端口 7861）
- 主动推送方案：仅读取 current_display.json / history.json
- 7860 侧写入 current_display.json，并调用 /notify 推送
- 7861 侧 /notify 将置脏位，定时器立即刷新
"""
import json
import os
from typing import Optional

import gradio as gr
from PIL import Image
from fastapi import FastAPI

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "history", "history.json")
CURRENT_DISPLAY_FILE = os.path.join(os.path.dirname(__file__), "history", "current_display.json")

# 脏位，用于通知触发刷新
dirty_flag = {"need_refresh": True}


def load_history() -> list:
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_current_display_id() -> Optional[int]:
    if not os.path.exists(CURRENT_DISPLAY_FILE):
        return None
    try:
        with open(CURRENT_DISPLAY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("current_display_id")
    except Exception as e:
        print(f"⚠️ 读取 current_display.json 失败: {e}")
        return None


def find_image_by_id(record_id: int, history: list):
    for rec in history:
        if rec.get("id") == record_id:
            path = rec.get("image_path", "")
            if path and os.path.exists(path):
                return Image.open(path)
    return None


def load_display_image():
    """读取 current_display_id 指向的图片；若无则用最新一条"""
    try:
        history = load_history()
        if not history:
            return None
        current_id = load_current_display_id()
        if current_id:
            img = find_image_by_id(current_id, history)
            if img:
                return img
        # fallback: 最新一条
        last = history[-1]
        path = last.get("image_path", "")
        if path and os.path.exists(path):
            return Image.open(path)
        return None
    except Exception as e:
        print(f"⚠️ 加载展示图片失败: {e}")
        return None


# Gradio 界面
with gr.Blocks(title="图片查看") as demo:
    gr.Markdown("## 当前展示图片", elem_classes="title")
    image_output = gr.Image(label="", type="pil", show_label=False, height=700)
    refresh_btn = gr.Button("刷新", variant="primary")

    # 初始化加载
    demo.load(fn=load_display_image, inputs=[], outputs=[image_output])
    refresh_btn.click(fn=load_display_image, inputs=[], outputs=[image_output])

    # 定时刷新：若收到 notify 则刷新，否则保持
    def conditional_refresh():
        if dirty_flag.get("need_refresh"):
            dirty_flag["need_refresh"] = False
            return load_display_image()
        return gr.update()

    gr.Timer(1.0).tick(fn=conditional_refresh, inputs=[], outputs=[image_output])


# FastAPI 包装以支持 /notify
api = FastAPI()


@api.post("/notify")
def notify():
    dirty_flag["need_refresh"] = True
    return {"status": "ok"}


# 将 Gradio 挂载到 FastAPI
api = gr.mount_gradio_app(api, demo, path="/")


if __name__ == "__main__":
    import uvicorn

    print("🚀 图片查看服务启动中 (端口 7861)...")
    uvicorn.run(api, host="127.0.0.1", port=7861)

