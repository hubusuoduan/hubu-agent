# Git 快速配置指南

## ✅ 已完成的配置

### 1. Git 仓库初始化
- ✅ 已初始化 Git 仓库
- ✅ 已创建完善的 `.gitignore` 文件
- ✅ 已完成首次提交

### 2. 敏感文件保护
以下文件已被正确忽略，**不会**被上传到 Git：

#### 🔒 环境配置文件
- `backend/.env` - 包含 API Keys、数据库密码等敏感信息
- `.env.local` - 本地环境变量

#### 📦 虚拟环境
- `.venv/` - Python 虚拟环境
- `backend/.venv/` - 后端虚拟环境
- `frontend/node_modules/` - Node.js 依赖

#### 🔐 依赖锁定文件
- `poetry.lock` - Poetry 依赖锁定文件
- `backend/poetry.lock` - 后端依赖锁定

#### 💻 IDE 配置
- `.idea/` - PyCharm/IntelliJ IDEA 配置
- `.vscode/` - VS Code 配置

#### 📝 日志和临时文件
- `*.log` - 日志文件
- `logs/` - 日志目录
- `__pycache__/` - Python 缓存文件

#### 💾 数据库文件
- `*.db`, `*.sqlite`, `*.sqlite3` - SQLite 数据库

## 📋 常用 Git 命令

### 查看状态
```bash
git status                    # 查看当前状态
git status --ignored         # 查看被忽略的文件
```

### 验证文件是否被忽略
```bash
git check-ignore -v backend/.env     # 检查 .env 是否被忽略
git check-ignore -v poetry.lock      # 检查 poetry.lock 是否被忽略
```

### 日常开发流程
```bash
# 1. 查看更改
git status

# 2. 添加所有更改
git add .

# 3. 提交更改
git commit -m "描述你的更改"

# 4. 查看历史
git log --oneline
```

### 如果不小心提交了敏感文件
```bash
# 从 Git 追踪中移除（保留本地文件）
git rm --cached backend/.env

# 提交更改
git commit -m "Remove sensitive file from tracking"

# ⚠️ 重要：立即更改所有泄露的密码和 API Keys
```

## ⚠️ 重要提醒

### 永远不要提交的内容
- ❌ 密码和密钥
- ❌ API Keys（如 LLM_API_KEY、TAVILY_API_KEY 等）
- ❌ 数据库连接字符串和密码
- ❌ 私钥文件（.pem, .key, .crt 等）
- ❌ 包含真实数据的配置文件

### 应该提交的内容
- ✅ 源代码
- ✅ 配置文件模板（如 `backend/.env.example`）
- ✅ 文档
- ✅ 构建脚本
- ✅ README 文件

## 🔍 验证配置

运行以下命令验证敏感文件是否被正确忽略：

```bash
# 应该显示被忽略的规则
git check-ignore -v backend/.env
git check-ignore -v backend/poetry.lock
git check-ignore -v .venv
git check-ignore -v frontend/node_modules
git check-ignore -v .idea
```

## 📚 更多信息

详细的 Git 配置说明请查看：`.gitignore_README.md`

## 🎯 下一步

1. **添加远程仓库**（如果需要）：
   ```bash
   git remote add origin <your-repository-url>
   git push -u origin main
   ```

2. **创建分支进行开发**：
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **定期提交**：
   - 完成一个功能点后提交
   - 提交信息要清晰描述更改内容

---

**记住**：Git 的主要目的是版本控制和协作，保护好敏感信息是首要任务！
