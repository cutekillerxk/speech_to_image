# 文字转图片（TTI - Text to Image）流程文档

## 📋 概述

本文档详细说明文字转图片功能的完整流程，包括API调用、错误处理、历史记录管理等各个环节。

## 🔄 完整流程

### 1. 用户输入阶段

**位置**: `app.py` - `generate_image()` 函数

```
用户输入文字描述
    ↓
验证输入（非空检查）
    ↓
调用 doubao_service.text_to_image()
```

**代码位置**: `app.py:17-48`

```python
def generate_image(text: str):
    if not text or not text.strip():
        return None, "❌ 请输入文字描述"
    
    # 调用豆包服务生成图片
    image, recognized_text = doubao_service.text_to_image(text.strip())
```

---

### 2. API服务调用阶段

**位置**: `doubao_service.py` - `text_to_image()` 方法

#### 2.1 配置检查

**代码位置**: `doubao_service.py:15-28`

- 检查API密钥是否存在（`config.DOUBAO_API_KEY`）
- 加载TTI API URL（默认：`https://www.dmxapi.cn/v1/images/generations`）
- 如果无API密钥，进入模拟模式

#### 2.2 API请求构建

**代码位置**: `doubao_service.py:89-107`

**请求参数**:
```python
{
    "model": "doubao-seedream-4-0-250828",  # 豆包4.0模型
    "prompt": text,                          # 用户输入的文字描述
    "size": "2K",                           # 图片尺寸：1K/2K/4K
    "stream": False,                        # 非流式返回
    "response_format": "url",               # 返回格式：url 或 b64_json
    "watermark": False                      # 不添加水印
}
```

**请求头**:
```python
{
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}
```

#### 2.3 API调用

**代码位置**: `doubao_service.py:114-119`

```python
response = requests.post(
    api_url,
    json=request_data,
    headers=headers,
    timeout=120  # 120秒超时
)
```

#### 2.4 响应解析

**代码位置**: `doubao_service.py:121-159`

**响应格式**:
```json
{
    "data": [
        {
            "url": "https://...",        // 图片URL（response_format="url"时）
            "b64_json": "base64..."      // Base64编码（response_format="b64_json"时）
        }
    ]
}
```

**处理逻辑**:
1. 优先检查 `data[0].b64_json`，如果存在则Base64解码
2. 其次检查 `data[0].url`，如果存在则下载图片
3. 兼容其他响应格式（直接包含 `url` 或 `b64_json`）
4. 将响应转换为PIL Image对象

---

### 3. 错误处理阶段

**代码位置**: `doubao_service.py:161-190`

#### 3.1 HTTP错误处理

- **401 Unauthorized**: API密钥验证失败
  - 输出详细错误提示
  - 返回模拟图片
  
- **其他HTTP错误**: 网络请求失败
  - 记录错误信息
  - 返回模拟图片

#### 3.2 异常处理

- **RequestException**: 网络连接问题
- **其他异常**: 记录完整堆栈信息
- **统一降级**: 所有错误都返回模拟图片，保证界面可用

#### 3.3 模拟模式

**代码位置**: `doubao_service.py:192-236`

当API调用失败或未配置API密钥时：
- 生成1024x1024的占位图片
- 在图片上绘制用户输入的文字
- 添加"测试模式"提示

---

### 4. 历史记录保存阶段

**位置**: `app.py` - `generate_image()` 函数

**代码位置**: `app.py:36-40`

```python
# 保存到历史记录
record = history_manager.add_record(image, recognized_text)
current_image = image
current_text = recognized_text
current_record_id = record['id']
```

#### 4.1 历史记录管理

**位置**: `history_manager.py` - `add_record()` 方法

**流程**:
1. 生成唯一ID（时间戳毫秒）
2. 保存图片到 `history/{id}.png`
3. 创建记录对象：
   ```python
   {
       'id': record_id,
       'text': text,
       'image_path': image_path,
       'timestamp': datetime.now().isoformat()
   }
   ```
4. 添加到历史记录列表
5. 保存到 `history/history.json`
6. 限制最多50条记录（自动删除最旧的）

---

### 5. 界面更新阶段

**位置**: `app.py` - `generate_image()` 函数

**返回结果**:
```python
status = f"✅ 图片生成成功！\n📝 描述：{recognized_text}"
return image, status
```

Gradio自动更新：
- `image_output`: 显示生成的图片
- `status_text`: 显示状态信息

---

## 📊 数据流图

```
┌─────────────┐
│  用户输入   │
│  文字描述   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ generate_image() │
│  (app.py)        │
└──────┬───────────┘
       │
       ▼
┌──────────────────────┐
│ text_to_image()      │
│ (doubao_service.py)  │
└──────┬───────────────┘
       │
       ├─── 检查API密钥 ───┐
       │                  │
       ▼                  ▼
┌─────────────┐    ┌──────────────┐
│ 调用真实API │    │  模拟模式    │
└──────┬──────┘    └──────┬───────┘
       │                  │
       └────────┬─────────┘
                │
                ▼
        ┌───────────────┐
        │ 返回PIL Image │
        └──────┬────────┘
               │
               ▼
        ┌───────────────┐
        │ add_record()  │
        │ 保存历史记录  │
        └──────┬────────┘
               │
               ▼
        ┌───────────────┐
        │ 更新界面显示  │
        └───────────────┘
```

---

## 🔧 配置说明

### 环境变量

**位置**: `config.py`

- `DMX_API_KEY` 或 `API_KEY`: API密钥（必需）
- `TTI_URL`: 文字转图片API地址（可选，默认：`https://www.dmxapi.cn/v1/images/generations`）

### 模型参数

**位置**: `doubao_service.py:95`

- **模型**: `doubao-seedream-4-0-250828`（豆包4.0模型）
- **备选模型**: `doubao-seedream-3-0-t2i-250415`（豆包3.0模型）
- **图片尺寸**: `"2K"`（可改为 `"1K"`、`"4K"` 或具体像素值如 `"2048x2048"`）

---

## ✅ 功能验证

### 正常流程验证

1. **输入文字**: "一只可爱的小猫"
2. **点击生成**: 等待API响应
3. **检查结果**:
   - ✅ 图片正常显示
   - ✅ 状态显示"图片生成成功"
   - ✅ 历史记录已保存
   - ✅ 可以切换查看历史

### 错误场景验证

1. **无API密钥**:
   - ✅ 显示占位图片
   - ✅ 图片上显示输入文字
   - ✅ 显示"测试模式"提示

2. **API调用失败**:
   - ✅ 自动降级到模拟模式
   - ✅ 控制台输出错误信息
   - ✅ 界面仍然可用

3. **空输入**:
   - ✅ 返回错误提示
   - ✅ 不调用API

---

## 🐛 常见问题

### Q1: API返回401错误

**原因**: API密钥无效或过期

**解决**:
1. 检查 `.env` 文件中的 `DMX_API_KEY`
2. 确认密钥格式正确（`sk-` 开头）
3. 验证密钥是否有效

### Q2: 图片生成很慢

**原因**: 网络延迟或API处理时间较长

**解决**:
- 当前超时设置为120秒
- 可以调整 `timeout` 参数（`doubao_service.py:118`）

### Q3: 历史记录丢失

**原因**: `history/` 目录被删除或权限问题

**解决**:
- 检查 `history/` 目录是否存在
- 确认有写入权限
- 检查 `history.json` 文件是否正常

---

## 📝 代码关键位置

| 功能 | 文件 | 行号 |
|------|------|------|
| 用户输入处理 | `app.py` | 17-48 |
| API服务调用 | `doubao_service.py` | 75-190 |
| 响应解析 | `doubao_service.py` | 121-159 |
| 错误处理 | `doubao_service.py` | 161-190 |
| 模拟模式 | `doubao_service.py` | 192-236 |
| 历史记录保存 | `history_manager.py` | 43-74 |
| 配置管理 | `config.py` | 1-28 |

---

## 🔄 后续优化建议

1. **异步处理**: 使用异步请求提升响应速度
2. **进度显示**: 添加生成进度条
3. **批量生成**: 支持一次生成多张图片
4. **图片编辑**: 支持图片尺寸、风格等参数调整
5. **缓存机制**: 相同提示词复用已生成的图片

---

## 📅 更新记录

- **2024-XX-XX**: 初始版本，完成基础文字转图片功能
- **2024-XX-XX**: 添加错误处理和模拟模式
- **2024-XX-XX**: 完善历史记录管理

