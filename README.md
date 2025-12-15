# 语音魔法画板（Python 版）

基于 Gradio 的语音转图片 Demo：点击录制，自动完成“音频 → 文字 → 图片”，并保存历史记录。

## 功能
- 🎤 录音：麦克风采集音频（点击录制/结束）
- 📝 语音转文字：Whisper-1（DMXAPI STT）
- 🎨 文生图：默认 Gemini 3 Pro（可回退到豆包文生图）
- 📚 历史记录：自动保存、上一张/下一张浏览

## 目录
```
speech_to_image/
├── python/
│   ├── onlyimg.py          # 简化版前端（录制+图片+上下张）
│   ├── app.py              # 原始多控件版前端
│   ├── doubao_service.py   # 语音转文字 & 文生图服务
│   ├── history_manager.py  # 历史记录与图片持久化
│   ├── config.py           # 配置与环境变量
│   ├── requirements.txt    # 依赖
│   └── history/            # 历史图片与索引
└── README.md
```

## 环境与依赖
```bash
conda create -n ati python=3.10
conda activate ati
pip install -r speech_to_image/python/requirements.txt
```

## 环境变量（python/.env）
```env
DMX_API_KEY=你的_API_KEY          # 或 API_KEY
STT_URL=https://www.dmxapi.com/v1/audio/transcriptions
TTI_URL=https://www.dmxapi.cn/v1/images/generations
GEMINI_BASE_URL=https://www.dmxapi.com
GEMINI_MODEL=gemini-3-pro-image-preview
```

## 运行
```bash
cd speech_to_image/python
python onlyimg.py   # 简化版：录制+上一张/下一张+图片展示
# 或 python app.py  # 原始多控件版
```

## 使用流程（onlyimg.py）
1. 点击录制（Audio 组件按钮开始录音，再次点击结束）
2. 自动执行：保存音频 → 语音转文字 → 文生图 → 保存历史
3. 图片区域更新为新图；可用“上一张/下一张”浏览历史

## 关键模块
- `onlyimg.py`：Gradio 前端布局、事件绑定；录制完成触发 `process_audio_and_generate`
- `doubao_service.py`：`audio_to_text`(Whisper-1)，`text_to_image_gemini`(Gemini)，`text_to_image`(豆包文生图)；失败时回退占位图
- `history_manager.py`：保存 PNG、写入 `history.json`，最多 50 条；支持上一张/下一张
- `config.py`：统一读取 API、路径、模型配置

## 注意
- 如果 Gemini 或豆包文生图 API 返回 401，请确认 `.env` 中的密钥有对应权限。
- 录制或生成失败时，界面保持上一张图片，不会清空。***

