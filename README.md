# Admin-Manage System

一个基于 React + TypeScript + Vite + Ant Design 前端和 Python FastAPI 后端的管理系统。

## 项目结构

```
admin-manage-system/
├── frontend/                    # React 前端
│   ├── src/
│   │   ├── components/         # 通用组件
│   │   ├── pages/              # 页面组件
│   │   │   ├── apikey/         # API Key 管理
│   │   │   ├── workflow/       # 流程配置
│   │   │   ├── prompt/         # Prompt 配置
│   │   │   └── model/          # 模型参数配置
│   │   ├── services/           # API 服务
│   │   ├── types/              # TypeScript 类型
│   │   └── utils/               # 工具函数
│   └── package.json
├── backend/                     # Python 后端
│   ├── app/
│   │   ├── api/                # API 路由
│   │   ├── models/             # 数据模型
│   │   ├── services/           # 业务逻辑
│   │   └── database/           # 数据库配置
│   ├── requirements.txt
│   └── main.py
└── README.md
```

## 功能模块

### 1. API Key 管理
- 创建、编辑、删除 API Key
- 设置权限和有效期
- 查看 API Key 列表

### 2. 流程配置
- 专有模型流程
- 专有模型 → 通用模型流程
- 流程参数设置

### 3. Prompt 配置
- 专有模型提示词
- 通用模型提示词
- 提示词分类管理

### 4. 模型参数配置
- 专有模型参数
- 通用模型参数
- 参数模板管理

## 技术栈

### 前端
- React 18 + TypeScript
- Vite
- Ant Design
- React Router
- Axios

### 后端
- Python 3.8+
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic

## 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd admin-manage-system
```

### 2. 后端启动
```bash
cd backend
pip install -r requirements.txt
python init_db.py  # 初始化数据库表
python main.py
```
后端服务将在 `http://localhost:8888` 启动

> **注意**: 项目已配置为使用 MySQL 数据库，连接信息已预设在配置文件中。

### 3. 前端启动
```bash
cd frontend
npm install
npm run dev
```
前端服务将在 `http://localhost:9000` 启动

## 项目特性

- ✅ 现代化的 React + TypeScript 前端
- ✅ 高性能的 FastAPI 后端
- ✅ MySQL 数据库支持
- ✅ 完整的 CRUD 操作
- ✅ 响应式设计
- ✅ 类型安全
- ✅ 模块化架构
- ✅ 一键启动脚本

## 快速启动

### 使用启动脚本 (推荐)

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

### 手动启动

详见上述快速开始部分。

## 数据库配置

项目已预配置 MySQL 数据库连接：
- **主机**: rm-bp1jldp727lmxq1m57o.mysql.rds.aliyuncs.com
- **端口**: 3306
- **数据库**: xinhua_dev
- **用户名**: xuanfeng_dev

## 从 GitHub 拉取代码到服务器

项目提供了 3 个脚本用于在 Ubuntu 服务器上从 GitHub 拉取代码：

- **`pull_from_github.sh`** - 功能完整版（推荐日常使用）
- **`pull_github_simple.sh`** - 快速简化版
- **`pull_from_github_secure.sh`** - 安全版本（推荐生产环境）

### 快速开始

#### 1. 修改配置

编辑 `pull_from_github.sh`，修改以下变量：
```bash
REPO_OWNER="your-username"    # 改为你的 GitHub 用户名
REPO_NAME="xinhua-tool"       # 改为你的仓库名
```

#### 2. 运行脚本

```bash
# 上传到服务器
scp pull_from_github.sh ubuntu@server-ip:/home/ubuntu/

# SSH 登录服务器后运行
chmod +x pull_from_github.sh
./pull_from_github.sh
```

代码会自动下载到 `/home/xinhua-tool` 目录。

### 高级用法

```bash
# 通过参数指定配置
./pull_from_github.sh your-username xinhua-tool /home/xinhua-tool main

# 更新现有代码（再次运行即可）
./pull_from_github.sh

# 使用安全版本（通过环境变量）
source ~/.github_token && ./pull_from_github_secure.sh
```

### 完整部署流程

```bash
# 1. 拉取代码
./pull_from_github.sh

# 2. 进入目录
cd /home/xinhua-tool

# 3. 部署应用
./deploy.sh docker
```

### 🔧 Docker 故障排查

#### 数据库连接失败 🔥 最关键

如果看到数据库连接错误：
```
Can't connect to MySQL server on 'localhost'
```

**一键修复：**
```bash
cp env.example .env
docker-compose down
docker-compose up -d
```

**原因：** 缺少 `.env` 文件导致无法读取数据库配置

**详细指南：** [DATABASE_CONNECTION_FIX.md](DATABASE_CONNECTION_FIX.md) ⭐

---

#### 容器/网络冲突

如果部署遇到问题（容器冲突、网络冲突、端口占用等），使用快速修复工具：

```bash
# 🚑 一键修复 90% 的问题
chmod +x fix-container-conflict.sh
./fix-container-conflict.sh
./deploy.sh docker
```

**Windows 用户：**
```powershell
.\fix-container-conflict.bat
bash deploy.sh docker
```

常见错误及快速解决：
- 🔥 **数据库连接失败** (`Can't connect to MySQL on localhost`) → 运行 `cp env.example .env`
- ❌ **容器名称冲突** (`container name is already in use`) → 运行 `./fix-container-conflict.sh`
- ❌ **网络冲突** (`network has active endpoints`) → 运行 `./fix-container-conflict.sh`
- 🔥 **端口占用** (`address already in use`) → 查看下方文档
- ⚠️  **version 过时** (`version is obsolete`) → 已自动修复（最新代码）

快速参考文档：
- 🔥 [数据库连接修复](DATABASE_CONNECTION_FIX.md) ⭐ **最常见问题**
- 📖 [Docker 完整故障排查](DOCKER_TROUBLESHOOTING.md) - 详细指南

### 自动化部署

```bash
# 设置定时任务（每天凌晨 2 点更新）
crontab -e

# 添加：
0 2 * * * cd /home/ubuntu && ./pull_from_github.sh >> /var/log/github-pull.log 2>&1
```

更多详细信息请查看：
- [GitHub 拉取代码使用说明](GitHub拉取代码说明.md) ⭐ 快速上手
- [GitHub 拉取代码完整指南](GITHUB_PULL_GUIDE.md) - 完整文档

### 数据库迁移

项目支持完整的数据库迁移功能，可以轻松地在不同环境间迁移数据。

#### 快速导出数据库
```bash
# Linux/Mac
./db_migration.sh export

# Windows
bash db_migration.sh export
```

#### 部署时导入数据库
```bash
# Docker 部署并导入数据库
./deploy.sh docker --with-db xinhua_db_YYYYMMDD_HHMMSS.tar.gz

# Systemd 部署并导入数据库
sudo ./deploy.sh systemd --with-db xinhua_db_YYYYMMDD_HHMMSS.tar.gz
```

#### 远程自动部署
```bash
# 一键导出并远程部署
./export_and_deploy.sh 192.168.1.100

# 指定用户和路径
./export_and_deploy.sh 192.168.1.100 ubuntu /opt/xinhua-tool
```

#### 数据库验证
```bash
# 验证数据库完整性
./db_migration.sh verify
```

#### 回滚操作
```bash
# 查看备份
ls -la db_backup_before_import_*/

# 回滚到指定备份
./db_migration.sh rollback db_backup_before_import_YYYYMMDD_HHMMSS
```

更多详细信息请查看：
- [数据库迁移完整指南](DATABASE_MIGRATION_GUIDE.md)
- [数据库迁移快速参考](DB_MIGRATION_QUICK_REFERENCE.md)

## 文档

### 部署相关
- [部署指南](docs/DEPLOYMENT.md)
- [部署检查清单](DEPLOYMENT_CHECKLIST.md)

### Docker 故障排查
- 🔥 [数据库连接修复](DATABASE_CONNECTION_FIX.md) ⭐ **最常见问题**
- 📖 [Docker 完整故障排查](DOCKER_TROUBLESHOOTING.md) - 所有问题汇总

### GitHub 代码拉取
- [GitHub 拉取快速开始](QUICK_START_GITHUB_PULL.md) ⭐ 快速参考卡
- [GitHub 拉取代码说明](GitHub拉取代码说明.md) ⭐ 中文指南
- [GitHub 拉取完整指南](GITHUB_PULL_GUIDE.md) - 完整文档
- [GitHub 拉取功能总结](GITHUB_PULL_SUMMARY.md) - 功能总结

### 数据库相关
- [数据库迁移使用说明](数据库迁移使用说明.md) ⭐ 中文指南
- [数据库迁移完整指南](DATABASE_MIGRATION_GUIDE.md) - 完整文档
- [数据库迁移快速参考](DB_MIGRATION_QUICK_REFERENCE.md) - 命令速查
- [数据库迁移实战示例](DB_MIGRATION_EXAMPLES.md) - 8 个示例
- [数据库迁移功能总结](DATABASE_MIGRATION_SUMMARY.md) - 功能总结

### API 文档
- [API 文档](docs/API.md)

