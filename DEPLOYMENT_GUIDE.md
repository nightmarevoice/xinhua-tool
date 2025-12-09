# 部署指南

本文档提供了将 backend、frontend 和 workflow-ctl 三个项目部署到服务器的完整方案。

## 目录

- [环境要求](#环境要求)
- [部署方案选择](#部署方案选择)
- [方案一：Docker Compose 部署（推荐）](#方案一docker-compose-部署推荐)
- [方案二：Systemd + Nginx 部署](#方案二systemd--nginx-部署)
- [配置说明](#配置说明)
- [服务管理](#服务管理)
- [故障排查](#故障排查)

## 环境要求

### 服务器要求

- **操作系统**: Ubuntu 20.04+ / CentOS 7+ / Debian 10+
- **内存**: 至少 2GB RAM（推荐 4GB+）
- **磁盘**: 至少 10GB 可用空间
- **网络**: 可访问互联网（用于下载依赖）

### 软件依赖

#### Docker 部署方案
- Docker 20.10+
- Docker Compose 2.0+

#### Systemd 部署方案
- Python 3.9+
- Node.js 18+
- Nginx 1.18+
- MySQL 5.7+ 或 8.0+（如果使用 MySQL）

## 部署方案选择

### 方案一：Docker Compose（推荐）

**优点**:
- 环境隔离，易于管理
- 一键部署，快速启动
- 易于扩展和维护
- 适合生产环境

**适用场景**: 生产环境、需要快速部署、团队协作

### 方案二：Systemd + Nginx

**优点**:
- 资源占用更少
- 更细粒度的控制
- 适合资源受限的环境

**适用场景**: 资源受限的服务器、需要精细控制

## 方案一：Docker Compose 部署（推荐）

### 1. 准备工作

#### 1.1 安装 Docker 和 Docker Compose

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

#### 1.2 克隆项目

```bash
git clone <your-repo-url> xinhua
cd xinhua
```

#### 1.3 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑环境变量（重要！）
vim .env
```

**必须配置的环境变量**:
- `BACKEND_DATABASE_URL`: 后端数据库连接字符串
- `WORKFLOW_CTL_DATABASE_URL`: Workflow-ctl 数据库连接字符串
- `SECRET_KEY`: JWT 密钥（生产环境必须修改）
- `DB_PASSWORD`: 数据库密码

### 2. 部署步骤

#### 方式 A：使用部署脚本（推荐）

```bash
# 赋予执行权限
chmod +x deploy.sh

# 执行部署
./deploy.sh docker
```

#### 方式 B：手动部署

```bash
# 1. 构建镜像
docker-compose build

# 2. 启动服务
docker-compose up -d

# 3. 查看服务状态
docker-compose ps

# 4. 查看日志
docker-compose logs -f
```

### 3. 验证部署

```bash
# 检查服务健康状态
curl http://localhost/health          # 前端
curl http://localhost:8888/health     # 后端
curl http://localhost:8889/health     # workflow-ctl

# 检查容器状态
docker-compose ps

# 查看日志
docker-compose logs backend
docker-compose logs workflow-ctl
docker-compose logs frontend
```

### 4. 访问服务

- **前端**: http://your-server-ip 或 http://your-domain.com
- **后端 API**: http://your-server-ip:8888
- **Workflow-ctl API**: http://your-server-ip:8889

## 方案二：Systemd + Nginx 部署

### 1. 准备工作

#### 1.1 安装依赖

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv nginx mysql-client

# 安装 Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# 安装 Python 依赖
pip3 install uvicorn[standard] gunicorn
```

#### 1.2 构建前端

```bash
cd frontend
npm install
npm run build
# 构建产物在 dist/ 目录
```

#### 1.3 配置环境变量

```bash
# 后端
cd backend
cp env.example .env
vim .env

# workflow-ctl
cd ../workflow-ctl
cp .env.example .env  # 如果有的话
vim .env
```

### 2. 部署步骤

#### 2.1 创建项目目录

```bash
sudo mkdir -p /opt/xinhua/{backend,workflow-ctl,frontend}
sudo mkdir -p /var/log/xinhua
```

#### 2.2 复制文件

```bash
# 复制后端
sudo cp -r backend/* /opt/xinhua/backend/
sudo chown -R www-data:www-data /opt/xinhua/backend

# 复制 workflow-ctl
sudo cp -r workflow-ctl/* /opt/xinhua/workflow-ctl/
sudo chown -R www-data:www-data /opt/xinhua/workflow-ctl

# 复制前端构建产物
sudo cp -r frontend/dist/* /opt/xinhua/frontend/
sudo chown -R www-data:www-data /opt/xinhua/frontend
```

#### 2.3 安装 Python 依赖

```bash
# 后端
cd /opt/xinhua/backend
sudo -u www-data python3 -m venv venv
sudo -u www-data venv/bin/pip install -r requirements.txt

# workflow-ctl
cd /opt/xinhua/workflow-ctl
sudo -u www-data python3 -m venv venv
sudo -u www-data venv/bin/pip install -r requirements.txt
```

#### 2.4 安装 Systemd 服务

```bash
# 复制服务文件
sudo cp deploy/systemd/xinhua-backend.service /etc/systemd/system/
sudo cp deploy/systemd/xinhua-workflow-ctl.service /etc/systemd/system/

# 修改服务文件中的路径（如果需要）
sudo vim /etc/systemd/system/xinhua-backend.service
sudo vim /etc/systemd/system/xinhua-workflow-ctl.service

# 重新加载 systemd
sudo systemctl daemon-reload

# 启用并启动服务
sudo systemctl enable xinhua-backend
sudo systemctl enable xinhua-workflow-ctl
sudo systemctl start xinhua-backend
sudo systemctl start xinhua-workflow-ctl
```

#### 2.5 配置 Nginx

```bash
# 复制 Nginx 配置
sudo cp deploy/nginx/xinhua.conf /etc/nginx/sites-available/

# 编辑配置（修改域名等）
sudo vim /etc/nginx/sites-available/xinhua.conf

# 创建软链接
sudo ln -s /etc/nginx/sites-available/xinhua.conf /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

### 3. 验证部署

```bash
# 检查服务状态
sudo systemctl status xinhua-backend
sudo systemctl status xinhua-workflow-ctl
sudo systemctl status nginx

# 检查端口
sudo netstat -tlnp | grep -E '8888|8889|80'

# 测试 API
curl http://localhost:8888/health
curl http://localhost:8889/health
```

## 配置说明

### 环境变量配置

#### 后端 (backend)

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `DATABASE_URL` | 数据库连接字符串 | `mysql+pymysql://user:pass@host:3306/db` |
| `SECRET_KEY` | JWT 密钥 | 随机字符串（生产环境必须修改） |
| `DEBUG` | 调试模式 | `False`（生产环境） |
| `ALLOWED_ORIGINS` | CORS 允许的源 | `http://your-domain.com` |

#### Workflow-ctl

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///./data/workflow.db` 或 MySQL |
| `PORT` | 服务端口 | `8889` |
| `HOST` | 绑定地址 | `0.0.0.0` |

### 数据库配置

#### 使用 MySQL（推荐生产环境）

```bash
# 在 .env 文件中配置
BACKEND_DATABASE_URL=mysql+pymysql://user:password@host:3306/database?charset=utf8mb4
WORKFLOW_CTL_DATABASE_URL=mysql+pymysql://user:password@host:3306/workflow_db?charset=utf8mb4
```

#### 使用 SQLite（仅开发环境）

```bash
# workflow-ctl 可以使用 SQLite
WORKFLOW_CTL_DATABASE_URL=sqlite:///./data/workflow.db
```

### Nginx 配置

主要配置项：
- **前端静态文件**: `/opt/xinhua/frontend`
- **后端 API 代理**: `http://backend:8888/api/` (Docker) 或 `http://127.0.0.1:8888/api/` (Systemd)
- **Workflow-ctl API 代理**: `http://workflow-ctl:8889/api/` (Docker) 或 `http://127.0.0.1:8889/api/` (Systemd)

## 服务管理

### Docker Compose 方式

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f [service_name]

# 查看服务状态
docker-compose ps

# 更新代码后重新部署
docker-compose build --no-cache
docker-compose up -d
```

### Systemd 方式

```bash
# 启动服务
sudo systemctl start xinhua-backend
sudo systemctl start xinhua-workflow-ctl

# 停止服务
sudo systemctl stop xinhua-backend
sudo systemctl stop xinhua-workflow-ctl

# 重启服务
sudo systemctl restart xinhua-backend
sudo systemctl restart xinhua-workflow-ctl

# 查看状态
sudo systemctl status xinhua-backend
sudo systemctl status xinhua-workflow-ctl

# 查看日志
sudo journalctl -u xinhua-backend -f
sudo journalctl -u xinhua-workflow-ctl -f

# 设置开机自启
sudo systemctl enable xinhua-backend
sudo systemctl enable xinhua-workflow-ctl
```

## 故障排查

### 常见问题

#### 1. 服务无法启动

**检查日志**:
```bash
# Docker
docker-compose logs backend

# Systemd
sudo journalctl -u xinhua-backend -n 50
```

**常见原因**:
- 数据库连接失败：检查数据库配置和网络连接
- 端口被占用：检查端口是否已被使用
- 环境变量未配置：检查 `.env` 文件

#### 2. 前端无法访问后端 API

**检查项**:
- Nginx 配置是否正确
- 后端服务是否正常运行
- CORS 配置是否正确

**调试**:
```bash
# 检查 Nginx 配置
sudo nginx -t

# 检查后端服务
curl http://localhost:8888/health

# 查看 Nginx 日志
sudo tail -f /var/log/nginx/xinhua-error.log
```

#### 3. 数据库连接失败

**检查项**:
- 数据库服务是否运行
- 连接字符串是否正确
- 网络是否可达
- 用户权限是否正确

**测试连接**:
```bash
# MySQL
mysql -h host -u user -p database

# 在 Python 中测试
python3 -c "from sqlalchemy import create_engine; engine = create_engine('your_database_url'); engine.connect()"
```

#### 4. 前端页面空白或 404

**检查项**:
- 前端构建是否成功
- Nginx 配置中的 root 路径是否正确
- 文件权限是否正确

**修复**:
```bash
# 检查文件是否存在
ls -la /opt/xinhua/frontend/

# 检查权限
sudo chown -R www-data:www-data /opt/xinhua/frontend
```

### 性能优化

#### 1. 数据库连接池

已在代码中配置连接池，生产环境建议：
- `pool_size`: 10-20
- `max_overflow`: 20-40
- `pool_recycle`: 300-3600

#### 2. Gunicorn 配置（Systemd 方式）

可以修改 systemd 服务文件使用 Gunicorn：

```ini
ExecStart=/opt/xinhua/backend/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8888
```

#### 3. Nginx 缓存

可以配置 Nginx 缓存静态资源，减少后端压力。

## 安全建议

1. **修改默认密钥**: 生产环境必须修改 `SECRET_KEY`
2. **使用 HTTPS**: 配置 SSL 证书，启用 HTTPS
3. **防火墙配置**: 只开放必要端口（80, 443）
4. **数据库安全**: 使用强密码，限制访问 IP
5. **定期更新**: 保持系统和依赖包更新
6. **日志监控**: 配置日志监控和告警

## 更新部署

### Docker 方式

```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建镜像
docker-compose build --no-cache

# 3. 重启服务
docker-compose up -d

# 4. 清理旧镜像（可选）
docker image prune -f
```

### Systemd 方式

```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建前端
cd frontend && npm run build

# 3. 复制新文件
sudo cp -r backend/* /opt/xinhua/backend/
sudo cp -r workflow-ctl/* /opt/xinhua/workflow-ctl/
sudo cp -r frontend/dist/* /opt/xinhua/frontend/

# 4. 重启服务
sudo systemctl restart xinhua-backend
sudo systemctl restart xinhua-workflow-ctl
sudo systemctl reload nginx
```

## 联系支持

如遇到问题，请检查：
1. 日志文件
2. 服务状态
3. 网络连接
4. 配置文件

更多信息请参考项目文档或联系技术支持。

