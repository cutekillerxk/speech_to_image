# 后端服务

## 安装依赖

```bash
npm install
```

## 配置环境变量

复制 `.env.example` 为 `.env` 并填写你的豆包API密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
DOUBAO_API_KEY=your_api_key_here
DOUBAO_API_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
PORT=3001
FRONTEND_URL=http://localhost:3000
```

## 启动服务

```bash
# 开发模式（需要nodemon）
npm run dev

# 生产模式
npm start
```

服务将在 http://localhost:3001 启动

## API端点

### POST /api/audio-to-image

接收音频文件，返回生成的图片。

**请求**:
- Content-Type: multipart/form-data
- Body: FormData with 'audio' field

**响应**:
```json
{
  "success": true,
  "text": "识别的文字",
  "imageUrl": "图片URL（如果有）",
  "imageData": "data:image/png;base64,...",
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

## 注意事项

1. **API密钥**: 如果没有配置 `DOUBAO_API_KEY`，服务会使用模拟API进行测试
2. **音频格式**: 支持 webm, wav, mp3 等格式
3. **文件大小**: 限制为10MB

