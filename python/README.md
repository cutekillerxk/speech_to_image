# 语音转图片生成器 (Python版)

一个简洁易用的图片生成应用，适合小朋友使用。输入文字描述，即可生成美丽的图片！

## 功能特点

- ✨ **文字生成图片**: 输入文字描述，调用豆包API生成图片
- 📸 **历史记录**: 自动保存生成的图片
- ⬅️➡️ **历史切换**: 简单按钮切换查看历史图片
- 💾 **图片下载**: 一键下载当前图片
- 🎨 **简洁界面**: 使用Gradio构建，操作简单直观

## 系统要求

- Windows系统
- Python 3.8+
- Conda环境（推荐）

## 快速开始

### 1. 创建Conda环境

使用environment.yml文件创建（推荐）：

```bash
conda env create -f environment.yml
conda activate ati
```

或者手动创建：

```bash
conda create -n ati python=3.10
conda activate ati
```

### 2. 安装依赖

```bash
cd python
pip install -r requirements.txt
```

### 3. 配置API密钥（可选）

复制 `.env.example` 为 `.env` 并填写你的豆包API密钥：

```bash
copy .env.example .env
```

编辑 `.env` 文件：

```env
DOUBAO_API_KEY=your_api_key_here
```

> **注意**: 如果不配置API密钥，系统会使用模拟模式（返回占位图片），可以用于测试界面功能。

### 4. 启动应用

```bash
python app.py
```

应用会自动在浏览器中打开，默认地址：http://localhost:7860

## 使用说明

1. **输入文字**: 在文本框中输入你想要生成的图片描述
   - 例如："一只可爱的小猫在花园里玩耍"
   - 例如："美丽的彩虹和白云"

2. **生成图片**: 点击"✨ 生成图片"按钮
   - 系统会调用豆包API生成图片
   - 等待几秒钟，图片就会显示出来

3. **查看历史**: 
   - 点击"⬅️ 上一张"查看之前的图片
   - 点击"➡️ 下一张"查看之后的图片

4. **下载图片**: 点击"💾 下载"按钮下载当前图片

## 项目结构

```
python/
├── app.py              # Gradio主应用
├── doubao_service.py   # 豆包API服务（文字转图片）
├── history_manager.py  # 历史记录管理
├── config.py          # 配置文件
├── requirements.txt    # Python依赖
├── .env.example       # 环境变量示例
├── .env              # 环境变量（需要自己创建）
└── history/          # 历史记录存储目录（自动创建）
    ├── history.json  # 历史记录索引
    └── *.png        # 保存的图片文件
```

## 功能解耦说明

当前版本实现了 **文字 → 图片** 功能。

**音频 → 文字** 功能已预留接口，等音频设备到位后可以轻松添加：
- 在 `doubao_service.py` 中添加 `audio_to_text()` 方法
- 在 `app.py` 中添加音频输入组件
- 将两个功能串联即可

## 配置说明

### 环境变量

- `DOUBAO_API_KEY`: 豆包API密钥（必需，用于真实功能）
- `DOUBAO_API_BASE_URL`: API基础URL（可选，有默认值）

### 历史记录

- 历史记录保存在 `history/` 目录
- 最多保存50条记录（可在 `config.py` 中修改）
- 图片以PNG格式保存
- 历史记录索引保存在 `history.json`

## 故障排查

### 1. 无法启动应用

- 检查Python版本：`python --version`（需要3.8+）
- 检查依赖是否安装：`pip list`
- 查看错误信息，根据提示解决

### 2. API调用失败

- 检查 `.env` 文件中的API密钥是否正确
- 检查网络连接
- 查看控制台错误信息
- 如果没有API密钥，系统会自动使用模拟模式

### 3. 图片无法显示

- 检查 `history/` 目录是否有写入权限
- 查看控制台是否有错误信息

### 4. 历史记录无法切换

- 确认已经生成过至少一张图片
- 检查 `history/history.json` 文件是否存在

## 后续功能

- [ ] 音频输入功能（等设备到位后添加）
- [ ] 语音转文字API集成
- [ ] 录音波形可视化
- [ ] 更多图片尺寸选项
- [ ] 图片编辑功能

## 许可证

MIT

