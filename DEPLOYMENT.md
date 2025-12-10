# 新华工具 - 部署文档

完整的部署指南，包含 Docker 和 Systemd 两种部署方式。

---

## 📋 目录

- [快速开始](#快速开始)
- [环境要求](#环境要求)
- [配置说明](#配置说明)
- [Docker 部署](#docker-部署)
- [网络架构](#网络架构)
- [数据库配置](#数据库配置)
- [故障排查](#故障排查)
- [日常维护](#日常维护)
- [安全建议](#安全建议)

---

## 🚀 快速开始

### 1. 准备环境文件

```bash
# 开发环境
cp env.example .env

# 生产环境
cp env.production .env
```

### 2. 修改配置

编辑 `.env` 文件，配置数据库和其他参数。

### 3. 部署

```bash
# 开发环境部署
./deploy.sh docker

# 生产环境部署
./deploy.sh docker --production

# 强制重新构建
./deploy.sh docker --no-cache
```

### 4. 验证部署

```bash
# 使用管理脚本检查
./manage.sh status
./manage.sh health
```

---

## 📦 环境要求

### 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 2 核 | 4 核 |
| 内存 | 2GB | 4GB |
| 硬盘 | 10GB | 20GB+ |
| 网络 | 10Mbps | 100Mbps |

### 软件要求

#### Docker 部署

- **Docker**: 20.10+ 
- **Docker Compose**: 2.0+
- **操作系统**: Ubuntu 20.04+, CentOS 7+, Debian 10+

#### Systemd 部署

- **Python**: 3.9+
- **Node.js**: 18+
- **Nginx**: 1.18+
- **操作系统**: Ubuntu 20.04+, CentOS 7+

### 端口需求

| 服务 | 端口 | 说明 |
|------|------|------|
| Frontend | 8787 | Web 界面 |
| Backend | 8888 | 后端 API |
| Workflow-Ctl | 8889 | 工作流 API |

---

## ⚙️ 配置说明

### 环境变量详解

#### 数据库配置

```bash
# 阿里云 RDS MySQL
DB_HOST=rm-bp1jldp727lmxq1m57o.mysql.rds.aliyuncs.com
DB_PORT=3306
DB_NAME=xinhua_dev
DB_USER=xuanfeng_dev
DB_PASSWORD=xuanfengkeji2025%    # % 在 URL 中编码为 %25

# Backend 连接字符串
BACKEND_DATABASE_URL=mysql+pymysql://xuanfeng_dev:xuanfengkeji2025%25@rm-bp1jldp727lmxq1m57o.mysql.rds.aliyuncs.com:3306/xinhua_dev?charset=utf8mb4

# Workflow-Ctl 连接字符串
WORKFLOW_CTL_DATABASE_URL=mysql+pymysql://xuanfeng_dev:xuanfengkeji2025%25@rm-bp1jldp727lmxq1m57o.mysql.rds.aliyuncs.com:3306/xinhua_dev?charset=utf8mb4
```

⚠️ **重要提示**: 密码中的 `%` 必须编码为 `%25`！

#### 安全配置

```bash
# JWT 密钥 (生产环境必须修改!)
SECRET_KEY=your_random_secret_key_here

# 生成新密钥
openssl rand -hex 32
```

#### CORS 配置

```bash
# 开发环境
ALLOWED_ORIGINS=http://localhost:8787,http://localhost:3000

# 生产环境 (修改为实际 IP/域名)
ALLOWED_ORIGINS=http://69.5.14.25:8787,http://your-domain.com
```

---

## 🐳 Docker 部署

### 部署步骤

#### 1. 初次部署

```bash
# 使用生产环境配置
./deploy.sh docker --production

# 或使用默认配置
./deploy.sh docker
```

#### 2. 带数据库导入

```bash
./deploy.sh docker --with-db backup.tar.gz
```

#### 3. 强制重新构建

```bash
./deploy.sh docker --no-cache
```

### Docker Compose 配置

#### 关键配置点

**网络配置:**
```yaml
networks:
  xinhua-network:
    name: xinhua-tool_xinhua-network  # 固定网络名
    driver: bridge
```

**服务别名:**
- `backend` → `xinhua-backend:8888`
- `workflow-ctl` → `xinhua-workflow-ctl:8889`
- `frontend` → `xinhua-frontend:80` (映射到主机 8787)

**健康检查:**
```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:8888/health || exit 1"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

**日志管理:**
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 容器管理

#### 查看状态

```bash
# 使用管理脚本
./manage.sh status

# 或直接使用 docker-compose
docker-compose ps
```

#### 查看日志

```bash
# 所有服务
./manage.sh logs

# 特定服务
./manage.sh logs backend
./manage.sh logs workflow-ctl
./manage.sh logs frontend

# 最后 100 行
./manage.sh logs-tail 100
```

#### 重启服务

```bash
# 重启所有
./manage.sh restart

# 重启特定服务
./manage.sh restart backend
```

#### 进入容器

```bash
# 进入后端容器
./manage.sh exec backend

# 或直接使用 docker
docker exec -it xinhua-backend bash
```

---

## 🌐 网络架构

### 外部访问流程

```
浏览器
   ↓
http://服务器IP:8787 (主机端口)
   ↓
Docker 端口映射 (8787:80)
   ↓
Nginx 容器 (端口 80)
   ↓ (反向代理)
   ├─→ http://backend:8888/api/        → Backend 容器
   ├─→ http://workflow-ctl:8889/api/   → Workflow-Ctl 容器
   └─→ /                                → 前端静态文件
```

### Docker 内部网络

容器间通信使用 Docker 内部网络 `xinhua-tool_xinhua-network`:

```
┌─────────────────────────────────────────┐
│   xinhua-tool_xinhua-network (bridge)   │
│                                          │
│   ┌──────────────────────────────┐     │
│   │  frontend (xinhua-frontend)  │     │
│   │  - Nginx 监听 80 端口         │     │
│   │  - 代理到 backend:8888       │     │
│   │  - 代理到 workflow-ctl:8889  │     │
│   └──────────┬───────────────────┘     │
│              │                          │
│   ┌──────────▼───────────┐             │
│   │  backend              │             │
│   │  (xinhua-backend)     │             │
│   │  - FastAPI @ 8888     │             │
│   └───────────────────────┘             │
│                                          │
│   ┌──────────────────────┐              │
│   │  workflow-ctl         │              │
│   │  (xinhua-workflow-ctl)│              │
│   │  - FastAPI @ 8889     │              │
│   └───────────────────────┘              │
│                                          │
└─────────────────────────────────────────┘
         │
         ▼
   阿里云 RDS MySQL
   rm-bp1jldp727lmxq1m57o.mysql.rds.aliyuncs.com:3306
```

### Nginx 代理配置

在 `frontend/nginx.conf`:

```nginx
# 代理后端 API
location /api/ {
    proxy_pass http://backend:8888/api/;  # 使用服务名
    # ... proxy 配置
}

# 代理 workflow-ctl API
location /workflow-api/ {
    proxy_pass http://workflow-ctl:8889/api/;  # 使用服务名
    # ... proxy 配置
}
```

⚠️ **注意**: 容器间通信使用**服务名**和**容器端口**，不是主机端口！

---

## 🗄️ 数据库配置

### 阿里云 RDS MySQL (推荐)

#### 配置方式

在 `.env` 文件中:

```bash
# 基本配置
DB_HOST=rm-bp1jldp727lmxq1m57o.mysql.rds.aliyuncs.com
DB_PORT=3306
DB_NAME=xinhua_dev
DB_USER=xuanfeng_dev
DB_PASSWORD=xuanfengkeji2025%

# 完整连接字符串 (注意 % 编码为 %25)
BACKEND_DATABASE_URL=mysql+pymysql://xuanfeng_dev:xuanfengkeji2025%25@rm-bp1jldp727lmxq1m57o.mysql.rds.aliyuncs.com:3306/xinhua_dev?charset=utf8mb4
```

#### 测试连接

```bash
# 使用管理脚本
./manage.sh test-db

# 手动测试
docker exec xinhua-backend python -c "
import pymysql
conn = pymysql.connect(
    host='rm-bp1jldp727lmxq1m57o.mysql.rds.aliyuncs.com',
    port=3306,
    user='xuanfeng_dev',
    password='xuanfengkeji2025%',
    database='xinhua_dev'
)
print('✅ 连接成功')
conn.close()
"
```

### SQLite (本地开发)

```bash
# Backend
DATABASE_URL=sqlite:///./app.db

# Workflow-Ctl
DATABASE_URL=sqlite:///./data/workflow.db
```

### 数据库迁移

```bash
# 运行迁移
./manage.sh db-migrate

# 手动迁移
docker exec xinhua-backend alembic upgrade head
docker exec xinhua-workflow-ctl alembic upgrade head
```

---

## 🔧 故障排查

### 常见问题

#### 1. 服务无法启动

**症状**: `docker-compose up -d` 失败

**排查步骤**:

```bash
# 查看详细日志
docker-compose logs

# 检查端口占用
netstat -tlnp | grep -E '8787|8888|8889'

# 检查环境变量
cat .env

# 测试配置文件
docker-compose config
```

#### 2. 健康检查失败

**症状**: 容器状态显示 `unhealthy`

**排查步骤**:

```bash
# 查看健康检查日志
docker inspect xinhua-backend | grep -A 10 Health

# 手动测试健康端点
curl http://localhost:8888/health
curl http://localhost:8889/health
curl http://localhost:8787

# 查看服务日志
./manage.sh logs backend
```

#### 3. 数据库连接失败

**症状**: 日志显示数据库连接错误

**排查步骤**:

```bash
# 测试数据库连接
./manage.sh test-db

# 检查密码编码
# 确保 % 编码为 %25

# 检查网络连接
docker exec xinhua-backend ping -c 3 rm-bp1jldp727lmxq1m57o.mysql.rds.aliyuncs.com

# 检查防火墙
# 确保容器可以访问 RDS (端口 3306)
```

#### 4. 前端无法访问后端

**症状**: 前端页面显示 API 错误

**排查步骤**:

```bash
# 测试容器网络
./manage.sh test-network

# 检查 Nginx 配置
docker exec xinhua-frontend cat /etc/nginx/conf.d/default.conf

# 测试代理
curl -v http://localhost:8787/api/health
```

#### 5. 端口冲突

**症状**: 端口已被占用

**解决方案**:

```bash
# 查找占用端口的进程
lsof -i :8787
lsof -i :8888
lsof -i :8889

# 停止占用进程或修改端口
# 修改 docker-compose.yml 中的端口映射
```

### 日志查看

```bash
# 实时查看所有日志
./manage.sh logs

# 查看错误日志
./manage.sh logs-error

# 查看特定服务日志
./manage.sh logs backend

# 查看最后 N 行
./manage.sh logs-tail 200
```

### 网络诊断

```bash
# 完整网络测试
./manage.sh test-network

# API 端点测试
./manage.sh test-api

# 健康检查
./manage.sh health
```

---

## 🔄 日常维护

### 备份

```bash
# 创建备份
./manage.sh backup

# 备份文件位置
./backups/backup_YYYYMMDD_HHMMSS.tar.gz
```

### 更新部署

```bash
# 完整更新流程 (包含备份)
./manage.sh update

# 或手动更新
./manage.sh backup
./deploy.sh docker --no-cache
```

### 日志管理

```bash
# 清理旧日志 (保留最近7天)
./manage.sh clean-logs

# 查看日志大小
du -sh logs/
```

### 资源清理

```bash
# 清理未使用的 Docker 资源
./manage.sh clean

# 手动清理
docker system prune -af
```

### 监控

```bash
# 查看资源占用
./manage.sh top

# 持续监控
watch -n 5 './manage.sh status'
```

---

## 🔒 安全建议

### 1. 环境变量保护

```bash
# 设置正确的文件权限
chmod 600 .env

# 不要提交到 Git
echo ".env" >> .gitignore
```

### 2. 修改默认密钥

```bash
# 生成新的 SECRET_KEY
openssl rand -hex 32

# 更新 .env 文件
SECRET_KEY=<生成的新密钥>
```

### 3. 数据库安全

- 使用强密码
- 限制 RDS 访问 IP 白名单
- 定期更新密码
- 启用 SSL 连接

### 4. 网络安全

```bash
# 配置防火墙 (Ubuntu)
sudo ufw allow 8787/tcp
sudo ufw allow 8888/tcp
sudo ufw allow 8889/tcp
sudo ufw enable

# 或使用 iptables (CentOS)
sudo firewall-cmd --permanent --add-port=8787/tcp
sudo firewall-cmd --permanent --add-port=8888/tcp
sudo firewall-cmd --permanent --add-port=8889/tcp
sudo firewall-cmd --reload
```

### 5. HTTPS (推荐)

使用 Nginx 反向代理添加 SSL:

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

### 6. 容器安全

- 定期更新基础镜像
- 使用非 root 用户运行 (已配置)
- 限制容器资源

---

## 📞 获取帮助

### 查看帮助

```bash
# 部署脚本帮助
./deploy.sh --help

# 管理脚本帮助
./manage.sh help
```

### 常用命令速查

```bash
# 服务管理
./manage.sh start           # 启动服务
./manage.sh stop            # 停止服务
./manage.sh restart         # 重启服务
./manage.sh status          # 查看状态

# 日志查看
./manage.sh logs            # 查看所有日志
./manage.sh logs backend    # 查看后端日志

# 维护操作
./manage.sh backup          # 备份数据
./manage.sh update          # 更新部署
./manage.sh clean           # 清理资源

# 诊断工具
./manage.sh health          # 健康检查
./manage.sh test-network    # 网络测试
./manage.sh test-db         # 数据库测试
```

---

## 📚 相关文档

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [Nginx 配置指南](https://nginx.org/en/docs/)
- [阿里云 RDS 文档](https://help.aliyun.com/product/26090.html)

---

**最后更新**: 2025-12-10


