# 🎨 语音魔法画板 - 全屏展示版

一个基于语音识别和 AI 图像生成的智能应用，支持自动语音检测（VAD）、实时录音、语音转文字、文字转图片，并具备全屏展示、历史记录管理、手动刷新等完整功能。

## ✨ 核心功能

- 🎤 **自动语音检测（VAD）**：无需手动点击，自动检测语音并开始录音
- 🗣️ **语音转文字（STT）**：使用豆包 API 将语音转换为文字描述
- 🎨 **文字转图片（TTI）**：使用豆包 API 将文字描述生成图片（1:1 比例，1K 尺寸）
- 🖼️ **全屏展示**：生成的图片自动全屏显示，适合展览和演示
- 📊 **圆形进度条**：实时显示图片生成进度（0-99% 30秒，完成后跳转100%）
- 📚 **历史记录**：自动保存所有生成的图片和文字描述到 `history/history.json`
- 🔄 **自动更新**：新图片生成后通过轮询机制自动更新显示
- 🔧 **手动刷新按钮**：右下角极小按钮，可手动刷新获取最新图片（容错功能）
- 🔒 **状态锁机制**：防止并发上传和处理，确保同一时间只处理一个任务

## 🛠️ 技术栈

- **后端框架**：FastAPI + Uvicorn
- **Web UI**：Gradio 6.1.0
- **语音处理**：Web Audio API + VAD（Voice Activity Detection）
- **AI 服务**：豆包 API（语音转文字、文字转图片）
- **前端技术**：JavaScript + CSS + HTML
- **图片处理**：Pillow (PIL)
- **数据存储**：JSON 文件

## 📋 系统要求

- Python 3.10+
- 现代浏览器（Chrome、Edge、Firefox 等，支持 Web Audio API）
- 麦克风设备（用于录音）
- API 密钥（豆包 API）
- FFmpeg（可选，用于音频格式转换）

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd speech_to_image
```

### 2. 创建 Conda 环境

```bash
conda env create -f python/environment.yml
```

或者手动创建：

```bash
conda create -n ati python=3.10
conda activate ati
```

### 3. 安装依赖

```bash
cd python
pip install -r ../requirements.txt
```

**Windows 用户额外安装 FFmpeg**（推荐，用于音频格式转换）：

```bash
# 使用 Chocolatey
choco install ffmpeg

# 或手动下载安装
# https://ffmpeg.org/download.html
# 将 ffmpeg 添加到系统 PATH 环境变量
```

### 4. 配置 API 密钥

创建 `.env` 文件（在 `python` 目录下）：

```env
# 豆包 API 密钥（必需）
DMX_API_KEY=your_api_key_here

# 或者使用通用 API_KEY
API_KEY=your_api_key_here

# API 基础 URL（可选，默认使用豆包 API）
BASE_URL=https://ark.cn-beijing.volces.com/api/v3

# 语音转文字 API URL（可选）
STT_URL=https://www.dmxapi.com/v1/audio/transcriptions

# 文字转图片 API URL（可选）
TTI_URL=https://www.dmxapi.com/v1/images/generations
```

> **注意**：如果没有配置 API 密钥，应用会使用模拟模式（显示占位图片），可以用于测试界面功能。

### 5. 启动应用

**全屏展示版（demo7.py，推荐）**：

```bash
python demo7.py
```

应用会自动在浏览器中打开：`http://localhost:7860`

## 📖 使用说明

### 基本使用流程

1. **首次访问**：浏览器会请求麦克风权限，请点击"允许"
2. **自动监听**：页面加载后会自动启动语音检测（VAD）
3. **开始说话**：系统会自动检测到语音（音量 > 0.08）并开始录音
4. **停止说话**：静音 3 秒后自动停止录音并上传
5. **生成图片**：
   - 显示圆形进度条（0-99%，30秒）
   - 前端轮询检查新图片（每 500ms 检查一次，最多 60 次）
   - 图片生成完成后自动更新显示
   - 进度条跳转 100% 后消失
6. **查看历史**：所有生成的图片自动保存到 `python/history/` 目录

### 刷新按钮功能

- **位置**：页面右下角，极小按钮（24x24px）
- **功能**：手动刷新获取最新图片
- **使用场景**：
  - 前端参数紊乱时手动修复
  - 手动修改 `history.json` 后刷新显示
  - 测试和调试时使用
- **工作原理**：
  - 重新加载 `history.json` 文件
  - 获取最后一条记录
  - 更新前端图片显示

## 📁 项目结构

```
speech_to_image/
├── README.md                 # 项目说明文档
├── requirements.txt          # Python 依赖包
├── python/                   # Python 源代码目录
│   ├── demo7.py             # 主程序（全屏展示版，带 VAD 和刷新按钮）
│   ├── demo6.py             # 全屏展示版（无刷新按钮）
│   ├── app.py               # 简化版（手动录音）
│   ├── config.py            # 配置文件
│   ├── doubao_service.py    # 豆包 API 服务封装
│   ├── history_manager.py   # 历史记录管理器
│   ├── audio/               # 音频文件存储目录
│   └── history/             # 图片和历史记录存储目录
│       ├── history.json     # 历史记录 JSON 文件
│       └── *.png            # 生成的图片文件
└── ...
```

## ⚙️ 配置说明

### 图片显示配置

在 `demo7.py` 中可以修改 `DISPLAY_CONFIG` 来调整图片显示尺寸：

```python
DISPLAY_CONFIG = {
    "mode": "fit_height",  # 显示模式: "fit_height", "fit_width", "fit_screen", "custom"
    "custom_height": 900,   # 自定义高度（当 mode="custom" 时使用）
    "custom_width": 900,    # 自定义宽度（当 mode="custom" 时使用）
    "screen_size": "15.6inch"  # 屏幕信息（可选）
}
```

### VAD 参数配置

在 `demo7.py` 的 JavaScript 代码中可以调整 VAD 参数（第 787-789 行）：

```javascript
window.vadConfig = {
    THRESHOLD: 0.08,           // 音量阈值，超过此值开始录音
    SILENCE_THRESHOLD: 0.03,   // 静音阈值，低于此值视为静音
    SILENCE_DURATION: 3000     // 静音持续时间（毫秒），超过此时间停止录音
};
```

### 轮询配置

在 `demo7.py` 的 JavaScript 代码中可以调整轮询参数（第 1162-1163 行）：

```javascript
var maxChecks = 60;        // 最多检查次数（默认 60 次）
var checkInterval = 500;    // 检查间隔（毫秒，默认 500ms）
// 总超时时间 = 60 × 500ms = 30 秒
```

### 进度条配置

进度条动画时长可以在 JavaScript 中修改（第 761 行）：

```javascript
maxDuration: 30000  // 30 秒（从 0% 到 99%）
```

## 🎯 核心特性详解

### 1. 自动语音检测（VAD）

- 使用 Web Audio API 实时分析音频音量
- 当音量超过阈值（0.08）时自动开始录音
- 静音超过设定时长（3 秒）后自动停止录音
- 无需手动操作，实现"说话即生成"
- 支持状态锁机制，防止并发处理

### 2. 圆形进度条

- 使用 SVG 绘制圆形进度条
- 0-30 秒：从 0% 平滑增长到 99%
- 图片生成完成：立即跳转到 100% 并消失
- 超过 30 秒未完成：卡在 99%，等待图片生成
- z-index: 99999，确保在最上层显示

### 3. 全屏展示

- 图片自动全屏显示，隐藏所有 UI 元素
- 使用 CSS + JavaScript 实现全屏效果
- 图片居中显示，保持比例
- 适合展览、演示等场景

### 4. 轮询更新机制

- 音频上传成功后启动轮询
- 每 500ms 调用 `/get_latest_image` API
- 检测 `record_id` 变化来判断是否有新图片
- 最多轮询 60 次（30 秒）
- 检测到新图片后立即更新显示并停止轮询

### 5. 状态锁机制

- **加锁时机**：音频上传成功后
- **解锁时机**：
  - 检测到新图片生成完成
  - 上传失败
  - 轮询超时
- **检查点**：
  - 录音停止时检查
  - 音频处理回调中检查
  - 开始录制前再次检查（双重保险）
- **作用**：防止在处理过程中触发新的录音和上传

### 6. 历史记录管理

- 自动保存所有生成的图片和文字描述
- 图片保存为 PNG 格式，文件名使用时间戳 ID
- 历史记录以 JSON 格式存储在 `history/history.json`
- 每条记录包含：`id`、`text`、`image_path`、`timestamp`
- 最多保存 50 条历史记录（可在 `history_manager.py` 中配置）

### 7. 手动刷新按钮

- **位置**：页面右下角（bottom: 10px, right: 10px）
- **大小**：24x24px，极小按钮
- **样式**：半透明黑色背景，白色边框，刷新图标（↻）
- **功能**：
  - 重新加载 `history.json` 文件
  - 获取最后一条记录
  - 更新前端图片显示
- **容错机制**：用于修复前端参数紊乱问题

## 🔧 API 端点

### POST /vad_upload

接收前端 VAD 录音（webm/wav），保存临时文件，在后台线程中处理。

**请求**：
- Content-Type: multipart/form-data
- Body: 音频文件（file）

**响应**：
```json
{
    "status": "ok",
    "record_id": 1766982737867,
    "timestamp": 1703846400000
}
```

### GET /get_latest_image

获取最新的图片信息，用于前端更新显示。

**响应**：
```json
{
    "status": "ok",
    "record_id": 1766982737867,
    "image_data": "data:image/png;base64,...",
    "text": "图片描述文本"
}
```

## 🔧 常见问题

### Q: 提示"conda不是内部或外部命令"

A: 需要先安装 Anaconda 或 Miniconda，并添加到系统 PATH。

### Q: 提示"找不到模块"

A: 运行 `pip install -r requirements.txt` 安装依赖。

### Q: 端口被占用

A: 修改 `demo7.py` 中的端口号：

```python
uvicorn.run(app, host="127.0.0.1", port=7860)  # 改为其他端口，如 7861
```

### Q: 浏览器没有自动打开

A: 手动访问 `http://localhost:7860`

### Q: API 调用失败

A: 
- 检查 `.env` 文件中的 API 密钥是否正确
- 如果没有 API 密钥，这是正常的，系统会使用模拟模式
- 检查网络连接是否正常

### Q: 麦克风权限被拒绝

A: 
- 在浏览器设置中允许麦克风权限
- 刷新页面后重新授权

### Q: 进度条不显示

A: 
- 检查浏览器控制台是否有 JavaScript 错误
- 确保 CSS 样式正确加载
- 检查 `z-index` 是否被其他元素覆盖

### Q: 图片不自动更新

A: 
- 检查后端日志是否有错误
- 确认 `history_manager` 正确保存了记录
- 检查前端轮询是否正常工作
- 尝试点击右下角刷新按钮手动刷新

### Q: 刷新按钮不显示

A: 
- 检查浏览器控制台是否有 `[Refresh]` 相关的日志
- 确认按钮是否被其他元素遮挡
- 检查 CSS 样式是否正确加载

### Q: webm 格式转换失败

A: 
- 安装 FFmpeg 并添加到系统 PATH
- 或安装 `pydub` 库（也需要 FFmpeg）
- 如果无法转换，系统会尝试直接使用原始格式

## 📝 开发说明

### 主要文件说明

- **demo7.py**：全屏展示版主程序，包含完整的 VAD 自动监听功能和刷新按钮
- **demo6.py**：全屏展示版（无刷新按钮）
- **app.py**：简化版主程序，适合手动操作
- **doubao_service.py**：封装豆包 API 调用（语音转文字、文字转图片）
- **history_manager.py**：管理图片生成历史记录
- **config.py**：读取环境变量和配置

### 工作流程

```
用户说话
    ↓
VAD 检测到语音 → 开始录制
    ↓
检测到静音 → 停止录制
    ↓
上传音频 → POST /vad_upload
    ↓
后台处理 → process_audio_and_generate()
    ↓
音频转文字 → doubao_service.audio_to_text()
    ↓
文字转图片 → doubao_service.text_to_image()
    ↓
保存历史 → history_manager.add_record()
    ↓
轮询检测 → GET /get_latest_image (每 500ms，最多 60 次)
    ↓
检测到新图片 → updateImageDisplay()
    ↓
前端显示新图片
```

### 扩展开发

1. **添加新的 AI 服务**：在 `doubao_service.py` 中添加新的服务类
2. **修改 UI 样式**：在 `demo7.py` 的 `custom_css` 中修改 CSS
3. **调整 VAD 参数**：在 JavaScript 代码中修改 `window.vadConfig`
4. **调整轮询参数**：修改 `maxChecks` 和 `checkInterval`
5. **添加新功能**：在 FastAPI 路由中添加新的端点

## 📄 许可证

本项目采用 MIT 许可证。

## 🙏 致谢

- [Gradio](https://gradio.app/) - 优秀的 Web UI 框架
- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Python Web 框架
- [豆包 API](https://www.volcengine.com/product/doubao) - AI 服务支持

## 📞 联系方式

如有问题或建议，欢迎提交 Issue 或 Pull Request。

---

**享受创作的乐趣！** 🎨✨
