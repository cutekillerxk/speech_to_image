# 语音驱动图片生成 Demo

一个基于豆包大模型API的语音转图片生成应用。

## 功能特性

- 🎤 **语音输入**: 通过麦克风录制音频
- 📝 **语音转文字**: 调用豆包API将音频转换为文字
- 🎨 **文字生成图片**: 根据文字描述生成图片
- 📸 **图片展示**: 实时展示生成的图片
- 📚 **历史记录**: 保存并浏览历史生成的图片
- ⬆️⬇️ **历史切换**: 支持上一张/下一张切换

## 技术栈

### 前端
- React 18
- TypeScript
- Ant Design
- Web Audio API

### 后端
- Node.js
- Express
- 豆包大模型API

## 项目结构

```
sti/
├── frontend/          # 前端React应用
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   └── App.tsx
│   └── package.json
├── backend/           # 后端Express服务
│   ├── src/
│   │   ├── routes/
│   │   ├── services/
│   │   └── server.js
│   └── package.json
├── 可行性分析.md
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
# 安装后端依赖
cd backend
npm install

# 安装前端依赖
cd ../frontend
npm install
```

### 2. 配置API密钥

在 `backend/.env` 文件中配置豆包API密钥：

```env
DOUBAO_API_KEY=your_api_key_here
DOUBAO_API_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
```

### 3. 启动服务

```bash
# 启动后端服务（端口3001）
cd backend
npm start

# 启动前端服务（端口3000）
cd frontend
npm start
```

### 4. 访问应用

打开浏览器访问: http://localhost:3000

## 使用说明

1. **开始录音**: 点击"开始录音"按钮，允许浏览器访问麦克风
2. **停止录音**: 点击"停止录音"按钮，音频将发送到后端处理
3. **查看结果**: 等待处理完成后，图片将自动显示
4. **浏览历史**: 使用"上一张"/"下一张"按钮浏览历史记录
5. **保存图片**: 点击图片或"下载"按钮保存图片到本地

## API说明

### 后端API端点

- `POST /api/audio-to-image` - 接收音频，返回生成的图片
  - 请求: FormData (包含audio文件)
  - 响应: `{ text: string, imageUrl: string, imageData: string }`

## 注意事项

1. **API密钥**: 需要先在豆包平台申请API密钥
2. **浏览器权限**: 首次使用需要允许麦克风权限
3. **网络要求**: 需要能够访问豆包API服务
4. **存储限制**: 历史记录存储在localStorage，有大小限制

## 开发计划

- [x] 项目结构搭建
- [x] 音频录制功能
- [x] 语音转文字API调用
- [x] 文字生成图片API调用
- [x] 历史记录功能
- [ ] 错误处理和重试机制
- [ ] 录音波形可视化
- [ ] 后端数据库持久化

## 许可证

MIT

