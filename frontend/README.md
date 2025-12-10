# 前端应用

## 安装依赖

```bash
npm install
```

## 配置

在 `package.json` 中已配置代理，将 `/api` 请求代理到后端服务。

如需修改后端地址，可以：
1. 修改 `package.json` 中的 `proxy` 字段
2. 或创建 `.env` 文件设置 `REACT_APP_API_URL`

## 启动应用

```bash
npm start
```

应用将在 http://localhost:3000 启动

## 功能说明

- **音频录制**: 使用 Web Audio API 录制音频
- **图片展示**: 使用 Ant Design Image 组件展示图片
- **历史记录**: 使用 localStorage 存储历史记录（最多50条）
- **历史切换**: 支持上一张/下一张切换

## 浏览器要求

- 支持 MediaRecorder API
- 支持 getUserMedia API
- 现代浏览器（Chrome, Firefox, Edge, Safari）

