# 上传项目到GitHub指南

## 📋 准备工作

### 1. 确保敏感信息已保护

✅ `.gitignore` 文件已配置，会自动忽略：
- `.env` 文件（包含API密钥）
- `python/history/` 目录（生成的图片）
- `__pycache__/` 等临时文件
- `node_modules/` 等依赖文件

**重要**：请确认你的 `.env` 文件不会被上传！

---

## 🚀 方法一：使用GitHub网页创建（推荐新手）

### 步骤1：在GitHub上创建仓库

1. 登录 [GitHub](https://github.com)
2. 点击右上角的 **"+"** → **"New repository"**
3. 填写仓库信息：
   - **Repository name**: `sti` 或 `audio-to-image`（你喜欢的名字）
   - **Description**: "语音转图片生成器 - 基于豆包大模型API"
   - **Visibility**: 选择 Public（公开）或 Private（私有）
   - ⚠️ **不要**勾选 "Initialize this repository with a README"
4. 点击 **"Create repository"**

### 步骤2：在本地初始化Git并推送

打开 PowerShell 或 CMD，在 `D:\sti` 目录下执行：

```powershell
# 1. 初始化Git仓库
git init

# 2. 添加所有文件（.gitignore会自动排除敏感文件）
git add .

# 3. 提交文件
git commit -m "Initial commit: 语音转图片生成器"

# 4. 添加远程仓库（替换YOUR_USERNAME和YOUR_REPO_NAME）
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# 5. 推送到GitHub
git branch -M main
git push -u origin main
```

**示例**（如果你的GitHub用户名是 `zhangsan`，仓库名是 `sti`）：
```powershell
git remote add origin https://github.com/zhangsan/sti.git
```

---

## 🚀 方法二：使用GitHub CLI（如果已安装）

```powershell
# 1. 初始化Git仓库
git init

# 2. 添加文件
git add .

# 3. 提交
git commit -m "Initial commit: 语音转图片生成器"

# 4. 使用GitHub CLI创建仓库并推送
gh repo create sti --public --source=. --remote=origin --push
```

---

## 🔍 验证上传

### 检查哪些文件会被上传

在上传前，可以检查哪些文件会被Git跟踪：

```powershell
git status
```

这会显示：
- ✅ **绿色**：将被添加的文件
- ❌ **红色**：被.gitignore忽略的文件（不会上传）

### 确认敏感文件被忽略

```powershell
# 检查.env文件是否被忽略
git check-ignore python/.env

# 如果输出 python/.env，说明已被正确忽略 ✅
```

---

## 📝 后续更新

如果以后修改了代码，需要更新到GitHub：

```powershell
# 1. 查看修改的文件
git status

# 2. 添加修改的文件
git add .

# 3. 提交修改
git commit -m "更新：描述你的修改内容"

# 4. 推送到GitHub
git push
```

---

## ⚠️ 重要提醒

### 1. 不要上传敏感信息

以下文件**不会**被上传（已在.gitignore中）：
- ✅ `.env` - API密钥
- ✅ `python/history/` - 生成的图片
- ✅ `__pycache__/` - Python缓存
- ✅ `node_modules/` - Node.js依赖

### 2. 如果误上传了敏感信息

如果发现 `.env` 文件被上传了：

```powershell
# 1. 从Git历史中删除
git rm --cached python/.env
git commit -m "Remove .env file"

# 2. 推送到GitHub
git push

# 3. 如果已经推送，需要强制更新（谨慎使用）
# git push --force
```

**注意**：如果敏感信息已经公开，建议立即更换API密钥！

### 3. 添加README说明

建议在仓库中添加说明，告诉其他用户：
- 如何配置 `.env` 文件
- 如何安装依赖
- 如何使用应用

---

## 🎯 快速命令总结

```powershell
# 首次上传
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main

# 后续更新
git add .
git commit -m "更新说明"
git push
```

---

## ❓ 常见问题

### Q: 提示 "fatal: not a git repository"
A: 确保在 `D:\sti` 目录下执行命令

### Q: 提示 "remote origin already exists"
A: 删除后重新添加：
```powershell
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
```

### Q: 提示需要用户名和密码
A: GitHub已不再支持密码认证，需要：
1. 使用 Personal Access Token (PAT)
2. 或使用 SSH 密钥
3. 或使用 GitHub Desktop

### Q: 如何生成Personal Access Token？
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. 点击 "Generate new token"
3. 选择权限：至少勾选 `repo`
4. 复制生成的token，在输入密码时使用它

---

## 📚 参考资源

- [Git官方文档](https://git-scm.com/doc)
- [GitHub帮助文档](https://docs.github.com)
- [GitHub Desktop](https://desktop.github.com/) - 图形化工具（推荐新手）

