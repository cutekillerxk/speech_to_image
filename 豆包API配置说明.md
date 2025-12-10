# 豆包API配置说明

## 获取API密钥

1. 访问豆包开放平台：https://console.volcengine.com/
2. 注册/登录账号
3. 创建应用并获取API密钥

## 配置步骤

### 1. 后端配置

在 `backend` 目录下创建 `.env` 文件：

```env
# 豆包API配置
DOUBAO_API_KEY=your_api_key_here
DOUBAO_API_BASE_URL=https://ark.cn-beijing.volces.com/api/v3

# 服务器配置
PORT=3001
NODE_ENV=development

# CORS配置
FRONTEND_URL=http://localhost:3000
```

### 2. API端点说明

#### 语音转文字API

根据豆包官方文档，语音识别API端点可能是：
- `POST /v1/audio/transcriptions`
- 或 `POST /api/v3/audio/transcriptions`

**请求格式**:
```javascript
FormData {
  file: audio_file,
  model: "doubao-asr" // 或其他模型名称
}
```

**响应格式**:
```json
{
  "text": "识别的文字内容"
}
```

#### 文字生成图片API

根据豆包官方文档，文生图API端点可能是：
- `POST /v1/images/generations`
- 或 `POST /api/v3/images/generations`

**请求格式**:
```json
{
  "model": "doubao-image",
  "prompt": "文字描述",
  "n": 1,
  "size": "1024x1024"
}
```

**响应格式**:
```json
{
  "data": [
    {
      "url": "图片URL",
      "b64_json": "base64编码的图片数据"
    }
  ]
}
```

## 注意事项

1. **API版本**: 不同版本的豆包API可能有不同的端点，请参考最新官方文档
2. **认证方式**: 通常使用 Bearer Token 认证，格式为 `Authorization: Bearer {API_KEY}`
3. **模型名称**: 需要根据实际可用的模型名称调整代码中的 `model` 参数
4. **测试模式**: 如果没有配置API密钥，代码会使用模拟API进行测试

## 修改API调用代码

如果豆包API的实际接口与代码中的不同，需要修改以下文件：

- `backend/src/services/doubaoService.js` - 修改 `audioToText()` 和 `textToImage()` 方法

## 常见问题

### Q: 如何查看API的实际端点？
A: 查看豆包开放平台的API文档，或联系技术支持

### Q: API调用失败怎么办？
A: 
1. 检查API密钥是否正确
2. 检查网络连接
3. 查看后端控制台的错误日志
4. 确认API配额是否充足

### Q: 支持哪些音频格式？
A: 通常支持 wav, mp3, webm 等常见格式，具体请查看API文档

