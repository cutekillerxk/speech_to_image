# 🎨 语音转图片生成器

一个基于语音识别和 AI 图像生成的智能应用，支持自动语音检测（VAD）、实时录音、语音转文字、文字转图片，并具备全屏展示、历史记录管理等完整功能。

## ✨ 核心功能

- 🎤 **自动语音检测（VAD）**：无需手动点击，自动检测语音并开始录音
- 🗣️ **语音转文字（STT）**：使用豆包 API 将语音转换为文字描述
- 🎨 **文字转图片（TTI）**：使用 Gemini API 或豆包 API 将文字描述生成图片
- 🖼️ **全屏展示**：生成的图片自动全屏显示，适合展览和演示
- 📊 **圆形进度条**：实时显示图片生成进度（0-99% 30秒，完成后跳转100%）
- 📚 **历史记录**：自动保存所有生成的图片和文字描述
- 🖨️ **右键打印**：支持右键点击图片直接打印
- 🔄 **自动更新**：新图片生成后自动更新显示

## 🛠️ 技术栈

- **后端框架**：FastAPI + Uvicorn
- **Web UI**：Gradio 6.1.0
- **语音处理**：Web Audio API + VAD（Voice Activity Detection）
- **AI 服务**：
  - 豆包 API（语音转文字、文字转图片）
  - Gemini API（文字转图片，可选）
- **前端技术**：JavaScript + CSS + HTML
- **图片处理**：Pillow (PIL)
- **数据存储**：JSON 文件

## 📋 系统要求

- Python 3.10+
- 现代浏览器（Chrome、Edge、Firefox 等，支持 Web Audio API）
- 麦克风设备（用于录音）
- API 密钥（豆包 API 或 Gemini API）

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

**Windows 用户额外安装 FFmpeg**（可选，用于音频格式转换）：

```bash
choco install ffmpeg
pip install pydub
```

### 4. 配置 API 密钥

创建 `.env` 文件（在 `python` 目录下）：

```env
# 豆包 API 密钥（推荐）
DMX_API_KEY=your_api_key_here

# 或者使用通用 API_KEY
API_KEY=your_api_key_here

# API 基础 URL（可选，默认使用豆包 API）
BASE_URL=https://ark.cn-beijing.volces.com/api/v3

# 语音转文字 API URL（可选）
STT_URL=https://www.dmxapi.com/v1/audio/transcriptions

# 文字转图片 API URL（可选）
TTI_URL=https://www.dmxapi.com/v1/images/generations

# Gemini API 配置（可选）
GEMINI_BASE_URL=https://www.dmxapi.com
GEMINI_MODEL=gemini-3-pro-image-preview
```

> **注意**：如果没有配置 API 密钥，应用会使用模拟模式（显示占位图片），可以用于测试界面功能。

### 5. 启动应用

**全屏展示版（推荐，带自动 VAD 监听）**：

```bash
python demo6.py
```

**简化版（手动录音）**：

```bash
python app.py
```

应用会自动在浏览器中打开：`http://localhost:7860`

## 📖 使用说明

### 全屏展示版（demo6.py）

1. **首次访问**：浏览器会请求麦克风权限，请点击"允许"
2. **自动监听**：页面加载后会自动启动语音检测
3. **开始说话**：系统会自动检测到语音并开始录音
4. **停止说话**：静音 2 秒后自动停止录音并上传
5. **生成图片**：
   - 显示圆形进度条（0-99%，30秒）
   - 图片生成完成后自动更新显示
   - 进度条跳转 100% 后消失
6. **查看历史**：所有生成的图片自动保存到 `python/history/` 目录

### 简化版（app.py）

1. 点击录音按钮开始录音
2. 再次点击停止录音
3. 点击"识别语音"按钮进行语音识别
4. 识别完成后，文字自动填入输入框
5. 点击"生成图片"按钮生成图片
6. 使用"上一张"/"下一张"按钮浏览历史记录

## 📁 项目结构

```
speech_to_image/
├── README.md                 # 项目说明文档
├── requirements.txt          # Python 依赖包
├── 快速开始.md               # 快速开始指南（中文）
├── python/                   # Python 源代码目录
│   ├── demo6.py             # 主程序（全屏展示版，带 VAD）
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

在 `demo6.py` 中可以修改 `DISPLAY_CONFIG` 来调整图片显示尺寸：

```python
DISPLAY_CONFIG = {
    "mode": "fit_height",  # 显示模式: "fit_height", "fit_width", "fit_screen", "custom"
    "custom_height": 900,   # 自定义高度（当 mode="custom" 时使用）
    "custom_width": 900,   # 自定义宽度（当 mode="custom" 时使用）
}
```

### VAD 参数配置

在 `demo6.py` 的 JavaScript 代码中可以调整 VAD 参数：

```javascript
window.vadState = {
    threshold: 30,        // 音量阈值（0-255）
    silenceDuration: 2000, // 静音持续时间（毫秒）后停止录音
    minRecordDuration: 500 // 最小录音时长（毫秒）
};
```

### 进度条配置

进度条动画时长可以在 JavaScript 中修改：

```javascript
maxDuration: 30000  // 30 秒（从 0% 到 99%）
```

## 🎯 核心特性详解

### 1. 自动语音检测（VAD）

- 使用 Web Audio API 实时分析音频音量
- 当音量超过阈值时自动开始录音
- 静音超过设定时长后自动停止录音
- 无需手动操作，实现"说话即生成"

### 2. 圆形进度条

- 使用 SVG 绘制圆形进度条
- 0-30 秒：从 0% 平滑增长到 99%
- 图片生成完成：立即跳转到 100% 并消失
- 超过 30 秒未完成：卡在 99%，等待图片生成

### 3. 全屏展示

- 图片自动全屏显示，隐藏所有 UI 元素
- 支持右键打印功能
- 隐藏图片工具栏（全屏、下载、分享按钮）
- 适合展览、演示等场景

### 4. 历史记录管理

- 自动保存所有生成的图片和文字描述
- 支持浏览上一张/下一张图片
- 最多保存 50 条历史记录（可配置）
- 历史记录以 JSON 格式存储

## 🔧 常见问题

### Q: 提示"conda不是内部或外部命令"

A: 需要先安装 Anaconda 或 Miniconda，并添加到系统 PATH。

### Q: 提示"找不到模块"

A: 运行 `pip install -r requirements.txt` 安装依赖。

### Q: 端口被占用

A: 修改 `demo6.py` 或 `app.py` 中的端口号：

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

## 📝 开发说明

### 主要文件说明

- **demo6.py**：全屏展示版主程序，包含完整的 VAD 自动监听功能
- **app.py**：简化版主程序，适合手动操作
- **doubao_service.py**：封装豆包 API 和 Gemini API 调用
- **history_manager.py**：管理图片生成历史记录
- **config.py**：读取环境变量和配置

### 扩展开发

1. **添加新的 AI 服务**：在 `doubao_service.py` 中添加新的服务类
2. **修改 UI 样式**：在 `demo6.py` 的 `custom_css` 中修改 CSS
3. **调整 VAD 参数**：在 JavaScript 代码中修改 `window.vadState`
4. **添加新功能**：在 FastAPI 路由中添加新的端点

## 📄 许可证

本项目采用 MIT 许可证。

## 🙏 致谢

- [Gradio](https://gradio.app/) - 优秀的 Web UI 框架
- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Python Web 框架
- [豆包 API](https://www.volcengine.com/product/doubao) - AI 服务支持
- [Gemini API](https://ai.google.dev/) - AI 图像生成支持

## 📞 联系方式

如有问题或建议，欢迎提交 Issue 或 Pull Request。

---

**享受创作的乐趣！** 🎨✨

