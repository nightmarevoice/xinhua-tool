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

- [API 文档](docs/API.md)
- [部署指南](docs/DEPLOYMENT.md)
- [数据库迁移指南](DATABASE_MIGRATION_GUIDE.md)
- [数据库迁移快速参考](DB_MIGRATION_QUICK_REFERENCE.md)
- [部署检查清单](DEPLOYMENT_CHECKLIST.md)
