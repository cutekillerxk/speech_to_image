# demo2.py 代码说明文档

## 📋 项目概述

`demo2.py` 是语音魔法画板的全屏展示版本，实现了**自动监听 + 全屏图片显示**的功能。用户无需点击任何按钮，页面加载后自动启动语音监听，说话后自动生成图片并全屏显示。

---

## 🏗️ 整体架构

### 技术栈

- **后端框架**: FastAPI + Gradio
- **前端**: Gradio Blocks + 自定义 JavaScript
- **音频处理**: Web Audio API + MediaRecorder API
- **语音识别**: 豆包 Whisper API
- **图片生成**: Google Gemini API
- **音频转换**: ffmpeg / pydub

### 核心组件

```
demo2.py
├── 配置层 (DISPLAY_CONFIG)
│   └── 图片显示尺寸配置
├── 业务逻辑层
│   ├── process_audio_and_generate() - 核心处理流程
│   ├── get_previous/next_image() - 历史导航（隐藏）
│   └── init_app() - 初始化加载
├── API 层 (FastAPI)
│   ├── /vad_upload - 接收前端音频上传
│   └── /get_latest_image - 获取最新图片（base64）
└── 前端层 (Gradio + JavaScript)
    ├── 全屏图片显示组件
    └── VAD 自动监听脚本
```

---

## 🔄 核心流程分析

### 1. 初始化流程

```
页面加载
  ↓
JavaScript 初始化
  ├── 初始化 VAD 状态变量
  ├── 获取当前记录ID（initRecordId）
  └── 自动启动监听（autoStartVAD）
      ↓
申请麦克风权限（浏览器自动弹出）
  ↓
监听启动成功
```

**关键代码位置**: 第 874-923 行

### 2. 语音录制流程

```
用户说话
  ↓
VAD 检测到音量 > THRESHOLD (0.08)
  ↓
自动开始录制（MediaRecorder.start()）
  ↓
VAD 检测到静音 < SILENCE_THRESHOLD (0.03)
  ↓
持续静音 > SILENCE_DURATION (1000ms)
  ↓
自动停止录制（MediaRecorder.stop()）
  ↓
触发 onstop 事件
```

**关键代码位置**: 第 678-709 行（`processor.onaudioprocess`）

**音量检测参数定义位置**: 第 645-649 行（`window.vadConfig` 对象）
```javascript
window.vadConfig = {
  THRESHOLD: 0.08,           // 开始录制的音量阈值（0-1之间）
  SILENCE_THRESHOLD: 0.03,    // 静音检测的音量阈值（0-1之间）
  SILENCE_DURATION: 1000      // 持续静音时长（毫秒），超过此时间自动停止录制
};
```

**参数说明**:
- `THRESHOLD` (0.08): 当检测到的音量超过此值时，自动开始录制。值越大，需要的声音越大才能触发录制。
- `SILENCE_THRESHOLD` (0.03): 当检测到的音量低于此值时，认为是静音。值越小，对静音的判断越严格。
- `SILENCE_DURATION` (1000): 持续静音的时长（毫秒）。当音量低于 `SILENCE_THRESHOLD` 并持续超过此时间时，自动停止录制。

### 3. 音频上传与处理流程

```
录制停止
  ↓
创建 Blob 对象（webm 格式）
  ↓
POST /vad_upload
  ↓
后端保存音频文件
  ↓
调用 process_audio_and_generate()
  ├── 阶段1: 音频处理（webm → wav 转换）
  ├── 阶段2: 音频转文字（Whisper API）
  ├── 阶段3: 文本处理
  ├── 阶段4: 文字转图片（Gemini API）
  └── 阶段5: 保存历史记录
  ↓
返回 record_id
```

**关键代码位置**: 
- 前端: 第 636-676 行（`recorder.onstop`）
- 后端: 第 428-457 行（`/vad_upload`）
- 后端: 第 61-342 行（`process_audio_and_generate`）

### 4. 图片自动更新流程

```
音频上传成功
  ↓
前端开始轮询检查（checkForNewImage）
  ├── 每 500ms 请求一次 /get_latest_image
  ├── 比较 record_id 是否变化
  └── 最多检查 60 次（30秒）
  ↓
检测到新图片
  ↓
调用 updateImageDisplay()
  ├── 查找图片元素
  ├── 更新图片 src（base64 数据）
  └── 重新应用全屏样式
```

**关键代码位置**: 
- 第 720-776 行（`checkForNewImage`）
- 第 779-872 行（`updateImageDisplay`）

---

## 🎨 前端技术细节

### 1. VAD (Voice Activity Detection) 实现

**原理**: 使用 Web Audio API 实时分析音频音量

```javascript
// 音频处理流程
AudioContext
  ↓
createMediaStreamSource(stream)  // 获取麦克风流
  ↓
createAnalyser()                  // 音频分析器
  ↓
createScriptProcessor()           // 音频处理节点
  ↓
onaudioprocess                    // 每帧处理
  ├── 计算音量（RMS）
  ├── 判断是否开始录制
  └── 判断是否停止录制
```

**关键参数**:
- `THRESHOLD = 0.08`: 开始录制的音量阈值
- `SILENCE_THRESHOLD = 0.03`: 静音检测阈值
- `SILENCE_DURATION = 1000ms`: 静音持续时间

**代码位置**: 第 678-709 行

### 2. 全屏显示实现

**方法1: CSS 全屏样式**
```css
position: fixed;
top: 0;
left: 0;
width: 100vw;
height: 100vh;
z-index: 9999;
```

**方法2: JavaScript 自动触发**
- 查找全屏按钮并自动点击
- 应用全屏样式到容器
- 使用 MutationObserver 监听 DOM 变化

**代码位置**: 
- CSS: 第 497-559 行
- JavaScript: 第 925-996 行

### 3. 图片更新机制

**问题**: FastAPI 接口无法直接更新 Gradio 组件

**解决方案**: 
1. 后端返回 base64 图片数据
2. 前端轮询检查新图片
3. 直接更新 DOM 中的图片元素

**代码位置**: 第 779-872 行

---

## 🔧 后端技术细节

### 1. 音频格式转换

**问题**: Whisper API 不支持 webm 格式

**解决方案**: 
1. 优先使用 ffmpeg 转换（最快）
2. 备用方案：pydub（需要 ffmpeg）
3. 转换失败时尝试直接使用（可能失败）

**代码位置**: 第 205-250 行

### 2. FastAPI + Gradio 集成

```python
app = FastAPI()
demo = gr.Blocks(...)
app = gr.mount_gradio_app(app, demo, path="/")
```

**优势**:
- 可以添加自定义 API 端点（`/vad_upload`, `/get_latest_image`）
- 保持 Gradio 的界面功能
- 支持异步处理

**代码位置**: 第 425-489 行

### 3. 全局状态管理

```python
current_image = None      # 当前显示的图片
current_text = ""         # 当前识别的文字
current_record_id = None  # 当前记录ID
```

**用途**:
- 图片更新时比较 ID
- 历史记录导航（隐藏功能）
- API 接口返回最新状态

**代码位置**: 第 56-58 行

---

## 📊 数据流图

```
┌─────────────┐
│  用户说话    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  VAD 检测音量    │
│  (JavaScript)    │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  自动录制音频    │
│  (MediaRecorder) │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  POST /vad_upload│
│  (webm 文件)     │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  webm → wav     │
│  (ffmpeg)       │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Whisper API    │
│  (音频转文字)    │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Gemini API     │
│  (文字转图片)    │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  保存历史记录    │
│  (history.json) │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  前端轮询检查    │
│  (checkForNewImage)│
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  更新图片显示    │
│  (updateImageDisplay)│
└─────────────────┘
```

---

## 🎯 关键技术点

### 1. Gradio JavaScript 注入

**问题**: Gradio 的 `js` 参数必须是函数表达式，不能是顶层语句

**解决方案**: 使用箭头函数包装
```javascript
js = "() => { ... }"
```

**代码位置**: 第 578-1001 行

### 2. 异步处理与状态同步

**问题**: FastAPI 接口异步处理，无法直接更新 Gradio 界面

**解决方案**: 
- 使用轮询机制（polling）
- 返回 base64 图片数据
- 前端直接更新 DOM

**代码位置**: 第 720-776 行

### 3. 音频格式兼容性

**问题**: 
- 前端录制：webm 格式
- Whisper API：需要 wav 格式

**解决方案**: 
- 使用 ffmpeg 转换
- 自动检测格式并转换
- 转换失败时给出提示

**代码位置**: 第 205-250 行

---

## 🔍 代码模块详解

### 模块1: 显示配置 (第 19-48 行)

```python
DISPLAY_CONFIG = {
    "mode": "fit_height",      # 显示模式
    "custom_height": 900,       # 自定义高度
    "custom_width": 900,        # 自定义宽度
    "screen_size": "15.6inch"   # 屏幕信息
}
```

**功能**: 配置图片显示尺寸，支持多种模式

### 模块2: 核心处理函数 (第 61-342 行)

`process_audio_and_generate()` - 完整的音频到图片流程

**阶段划分**:
1. **音频处理** (0.1): 保存/转换音频文件
2. **音频转文字** (0.3): 调用 Whisper API
3. **文本生成完毕** (0.5): 识别文字确认
4. **文字转图片** (0.6): 调用 Gemini API
5. **保存历史记录** (0.9): 保存到 history 目录
6. **完成** (1.0): 返回新图片

### 模块3: FastAPI 接口 (第 428-489 行)

**`/vad_upload`**: 
- 接收前端上传的 webm 音频
- 保存到 audio 目录
- 调用处理流程
- 返回记录ID

**`/get_latest_image`**:
- 获取最新图片的 base64 编码
- 返回记录ID和文本描述
- 供前端轮询检查使用

### 模块4: 前端 JavaScript (第 578-1001 行)

**VAD 监听**:
- `vadStartListening()`: 启动监听
- `processor.onaudioprocess`: 实时音量检测
- `recorder.onstop`: 录制停止处理

**图片更新**:
- `checkForNewImage()`: 轮询检查新图片
- `updateImageDisplay()`: 更新图片显示
- `autoFullscreenImage()`: 自动全屏

---

## 🐛 已知问题与解决方案

### 1. 图片不自动更新

**原因**: Gradio 组件更新机制限制

**解决方案**: 
- 使用轮询机制
- 直接更新 DOM 元素
- 备用方案：刷新页面

### 2. 全屏显示不完美

**原因**: 浏览器窗口限制

**解决方案**: 
- CSS `position: fixed` 模拟全屏
- JavaScript 自动触发全屏按钮
- 隐藏浏览器 UI 元素

### 3. 音频格式转换失败

**原因**: ffmpeg 未安装或路径不正确

**解决方案**: 
- 安装 ffmpeg 并添加到 PATH
- 或安装 pydub（需要 ffmpeg）
- 提供清晰的错误提示

---

## 📝 配置说明

### DISPLAY_CONFIG 参数

```python
DISPLAY_CONFIG = {
    "mode": "fit_height",  # 可选: fit_height, fit_width, fit_screen, custom
    "custom_height": 900,  # 自定义高度（像素）
    "custom_width": 900,   # 自定义宽度（像素）
    "screen_size": "15.6inch"  # 屏幕信息（可选）
}
```

### VAD 参数

```javascript
window.vadConfig = {
    THRESHOLD: 0.08,           // 开始录制阈值
    SILENCE_THRESHOLD: 0.03,   // 静音检测阈值
    SILENCE_DURATION: 1000     // 静音持续时间（ms）
}
```

---

## 🚀 运行说明

### 启动命令

```bash
python demo2.py
```

### 访问地址

```
http://127.0.0.1:7860
```

### 首次使用

1. 浏览器会自动弹出麦克风权限请求
2. 点击"允许"
3. 监听自动启动
4. 说话即可自动生成图片

---

## 📚 依赖说明

### Python 依赖

- `gradio`: Web 界面框架
- `fastapi`: API 框架
- `PIL`: 图片处理
- `requests`: HTTP 请求

### 系统依赖

- `ffmpeg`: 音频格式转换（必需）

### 可选依赖

- `pydub`: 音频处理库（需要 ffmpeg）
- `soundfile`: 音频文件读写

---

## 🔐 安全注意事项

1. **麦克风权限**: 需要用户授权，首次访问会弹出请求
2. **API 密钥**: 存储在 `.env` 文件中，不要提交到版本控制
3. **文件上传**: `/vad_upload` 接口需要验证文件大小和格式
4. **CORS**: 当前仅支持本地访问（127.0.0.1）

---

## 🎯 性能优化建议

1. **音频转换**: 使用 ffmpeg 比 pydub 更快
2. **图片更新**: 轮询间隔 500ms，可根据实际情况调整
3. **历史记录**: 定期清理旧记录，避免文件过多
4. **缓存策略**: 图片 base64 编码可考虑缓存

---

## 📖 扩展建议

1. **键盘快捷键**: 添加左右箭头键切换历史图片
2. **触摸手势**: 支持滑动切换图片
3. **多语言支持**: 支持英文、日文等语言识别
4. **图片编辑**: 添加滤镜、调整等功能
5. **导出功能**: 支持导出图片到本地

---

## 🔗 相关文件

- `auto.py`: 带按钮的版本（参考）
- `doubao_service.py`: API 服务层
- `history_manager.py`: 历史记录管理
- `config.py`: 配置管理

---

## 📅 版本历史

- **v1.0**: 初始版本，实现自动监听和全屏显示
- 支持 webm 格式音频
- 自动图片更新功能
- 全屏显示优化

---

## ❓ 常见问题

### Q: 图片不自动更新怎么办？

A: 检查浏览器控制台日志，查看是否有错误。如果轮询失败，会自动刷新页面。

### Q: 全屏显示不完美？

A: 当前使用 CSS 模拟全屏，如需真正的系统全屏，需要使用浏览器全屏 API 或外部工具。

### Q: 音频转换失败？

A: 确保已安装 ffmpeg 并添加到系统 PATH，或安装 pydub。

### Q: 麦克风权限被拒绝？

A: 在浏览器设置中允许麦克风权限，然后刷新页面。

---

## 📞 技术支持

如有问题，请查看：
1. 浏览器控制台日志（F12）
2. 后端终端输出
3. 相关配置文件

---

*文档最后更新: 2025-01-16*

