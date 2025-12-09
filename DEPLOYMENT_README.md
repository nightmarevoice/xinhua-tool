# 新华项目部署方案总结

## 📖 概述

本文档为新华项目（backend + frontend + workflow-ctl）的完整部署方案总结。

### 项目架构

- **Backend**: FastAPI 后端服务 (端口 8888)
- **Frontend**: React + Vite 前端 (端口 80/443)
- **Workflow-ctl**: 工作流控制服务 (端口 8889)
- **Database**: MySQL (生产环境) / SQLite (开发环境)

---

## 📁 文档结构

### 主要文档

1. **PRODUCTION_DEPLOYMENT.md** - 完整的生产环境部署指南
   - 详细的部署步骤
   - 两种部署方案（Docker / 传统）
   - SSL/HTTPS 配置
   - 监控、备份、性能优化
   - 故障排除

2. **DEPLOYMENT_QUICK_REFERENCE.md** - 快速参考手册
   - 常用命令速查
   - 日常维护操作
   - 故障排除快速指南

3. **本文档** - 部署方案总结和快速入门

---

## 🚀 快速开始

### 方式一：一键部署（推荐）

适合快速部署和测试环境。

```bash
# 1. 克隆项目到服务器
git clone <your-repository> /opt/xinhua
cd /opt/xinhua

# 2. 运行一键部署脚本
chmod +x quick-deploy.sh
./quick-deploy.sh

# 完成！访问 http://your-server-ip
```

**说明**: 
- 自动安装 Docker 和 Docker Compose
- 自动配置环境变量
- 自动初始化数据库
- 自动设置开机自启
- 自动配置备份任务

**时间**: 约 10-15 分钟

---

### 方式二：Docker Compose 手动部署

适合需要自定义配置的生产环境。

```bash
# 1. 准备环境
cd /opt/xinhua
cp env.example .env
nano .env  # 修改配置

# 2. 创建目录
mkdir -p logs/{backend,workflow-ctl}
mkdir -p workflow-ctl/data

# 3. 部署
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d

# 4. 初始化数据库
docker-compose exec backend python init_db.py
docker-compose exec workflow-ctl python init_db.py

# 5. 验证
curl http://localhost:8888/health
curl http://localhost:8889/health
```

**时间**: 约 15-20 分钟

---

### 方式三：传统部署

适合不使用 Docker 的环境。

详见 [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md#方案二传统部署)

**时间**: 约 30-40 分钟

---

## 📋 部署前准备清单

### 服务器要求

- [ ] Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- [ ] 最低 2 核 CPU, 4GB 内存, 40GB 硬盘
- [ ] 开放端口: 80, 443 (可选: 22 for SSH)
- [ ] Root 或 sudo 权限

### 准备信息

- [ ] 数据库连接信息 (MySQL 推荐)
  - 主机地址
  - 端口
  - 数据库名
  - 用户名和密码
- [ ] 域名 (可选，用于 HTTPS)
- [ ] SSL 证书 (可选，或使用 Let's Encrypt)

### 环境变量配置

编辑 `.env` 文件，必须配置以下内容：

```bash
# 数据库配置
DB_HOST=your-mysql-host
DB_PORT=3306
DB_NAME=xinhua_prod
DB_USER=your-user
DB_PASSWORD=your-password

# 安全密钥（生成随机字符串）
SECRET_KEY=$(openssl rand -hex 32)

# 允许的来源
ALLOWED_ORIGINS=http://your-domain.com,https://your-domain.com
```

---

## 📦 部署脚本说明

### 1. quick-deploy.sh - 一键部署脚本

全自动部署脚本，适合首次部署。

```bash
./quick-deploy.sh
```

**功能**:
- ✅ 检查系统要求
- ✅ 安装 Docker 和 Docker Compose
- ✅ 配置环境变量（交互式）
- ✅ 构建和启动服务
- ✅ 初始化数据库
- ✅ 验证部署
- ✅ 配置开机自启
- ✅ 安装备份任务

---

### 2. deploy.sh - 标准部署脚本

支持 Docker 和 Systemd 两种部署方式。

```bash
# Docker 部署
./deploy.sh docker

# Systemd 部署
sudo ./deploy.sh systemd
```

---

### 3. update.sh - 更新脚本

用于更新已部署的服务。

```bash
# 正常更新（会提示）
./update.sh

# 强制更新（不提示）
./update.sh --force

# 不备份的更新
./update.sh --no-backup
```

**功能**:
- ✅ 自动备份当前版本
- ✅ 拉取最新代码
- ✅ 滚动更新服务
- ✅ 验证更新
- ✅ 失败自动回滚

---

### 4. backup.sh - 备份脚本

数据备份和恢复。

```bash
# 完整备份
./backup.sh full

# 快速备份（仅数据库和配置）
./backup.sh quick

# 恢复备份
./backup.sh restore /backup/xinhua/backup.sql.gz

# 列出备份
./backup.sh list
```

**备份内容**:
- 📦 MySQL/SQLite 数据库
- 📦 配置文件 (.env, docker-compose.yml)
- 📦 日志文件（最近7天）
- 📦 Docker 卷（如果使用）

**自动备份**: 默认每天凌晨 2 点自动备份，保留 30 天

---

### 5. health_check.sh - 健康检查脚本

监控服务健康状态。

```bash
./health_check.sh
```

**检查项目**:
- ✅ 后端 API 服务
- ✅ Workflow-ctl 服务
- ✅ 前端服务
- ✅ 数据库连接
- ✅ 磁盘空间
- ✅ 内存使用
- ✅ Docker 容器状态
- ✅ 日志文件大小

**自动检查**: 默认每 5 分钟检查一次，异常时发送告警

---

## 🔧 日常维护

### 启动/停止服务

```bash
# Docker 部署
docker-compose up -d      # 启动
docker-compose down       # 停止
docker-compose restart    # 重启

# Systemd 部署
sudo systemctl start xinhua-backend
sudo systemctl stop xinhua-backend
```

### 查看日志

```bash
# Docker 日志
docker-compose logs -f backend

# Systemd 日志
sudo journalctl -u xinhua-backend -f

# 应用日志
tail -f /opt/xinhua/logs/backend/*.log
```

### 更新服务

```bash
./update.sh
```

### 备份数据

```bash
./backup.sh full
```

### 健康检查

```bash
./health_check.sh
```

---

## 🔐 SSL/HTTPS 配置

### 使用 Let's Encrypt（推荐）

```bash
# 1. 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 2. 获取证书
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 3. 自动续期已配置好
sudo certbot renew --dry-run
```

### 手动配置 SSL

```bash
# 1. 复制生产配置
sudo cp deploy/nginx/xinhua-production.conf /etc/nginx/sites-available/xinhua.conf

# 2. 修改域名和证书路径
sudo nano /etc/nginx/sites-available/xinhua.conf

# 3. 启用配置
sudo ln -s /etc/nginx/sites-available/xinhua.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 📊 监控和告警

### 配置邮件告警

编辑 `health_check.sh`，设置告警邮箱：

```bash
EMAIL_ALERT="admin@example.com"
```

### 配置 Slack 告警

编辑 `health_check.sh`，设置 Webhook URL：

```bash
SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

### 查看监控日志

```bash
tail -f /var/log/xinhua/health_check.log
```

---

## 🐛 故障排除

### 服务无法启动

```bash
# 查看日志
docker-compose logs backend

# 检查端口占用
sudo netstat -tlnp | grep 8888

# 重新构建
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 数据库连接失败

```bash
# 测试连接
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD

# 检查环境变量
cat .env | grep DB_
```

### Nginx 502 错误

```bash
# 检查后端服务
curl http://localhost:8888/health

# 查看 Nginx 日志
sudo tail -f /var/log/nginx/error.log
```

详细故障排除指南: [DEPLOYMENT_QUICK_REFERENCE.md](DEPLOYMENT_QUICK_REFERENCE.md#故障排除)

---

## 📁 文件和目录结构

```
/opt/xinhua/                              # 项目根目录
├── .env                                  # 环境变量配置 ⚠️ 重要
├── docker-compose.yml                    # Docker Compose 配置
├── docker-compose.production.yml         # 生产环境配置
├── quick-deploy.sh                       # 一键部署脚本
├── deploy.sh                             # 标准部署脚本
├── update.sh                             # 更新脚本
├── backup.sh                             # 备份脚本
├── health_check.sh                       # 健康检查脚本
├── backend/                              # 后端服务
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── app/
├── frontend/                             # 前端服务
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── src/
├── workflow-ctl/                         # 工作流控制服务
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── app/
├── logs/                                 # 日志目录
│   ├── backend/
│   └── workflow-ctl/
├── deploy/                               # 部署配置
│   ├── nginx/
│   │   ├── xinhua.conf
│   │   └── xinhua-production.conf
│   └── systemd/
│       ├── xinhua-backend.service
│       └── xinhua-workflow-ctl.service
└── docs/                                 # 文档
    ├── PRODUCTION_DEPLOYMENT.md          # 完整部署指南
    ├── DEPLOYMENT_QUICK_REFERENCE.md     # 快速参考
    ├── DEPLOYMENT_README.md              # 本文档
    └── API.md                            # API 文档
```

---

## 🎯 最佳实践

### 1. 安全性

- ✅ 使用强密码和随机 SECRET_KEY
- ✅ 启用 HTTPS
- ✅ 配置防火墙（只开放 80, 443, 22 端口）
- ✅ 禁用 SSH 密码登录
- ✅ 定期更新系统和依赖

### 2. 可靠性

- ✅ 每天自动备份
- ✅ 定期健康检查
- ✅ 使用 Docker restart 策略
- ✅ 配置日志轮转
- ✅ 测试备份恢复流程

### 3. 性能

- ✅ 使用生产环境配置（docker-compose.production.yml）
- ✅ 启用 Nginx Gzip 压缩
- ✅ 配置静态资源缓存
- ✅ 优化数据库索引
- ✅ 监控系统资源使用

### 4. 维护

- ✅ 在低峰期更新
- ✅ 更新前备份
- ✅ 使用更新脚本自动回滚
- ✅ 保留日志 30 天
- ✅ 定期清理旧数据

---

## 📞 获取帮助

### 文档

- **完整部署指南**: [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)
- **快速参考**: [DEPLOYMENT_QUICK_REFERENCE.md](DEPLOYMENT_QUICK_REFERENCE.md)
- **API 文档**: [docs/API.md](docs/API.md)

### 命令帮助

```bash
./quick-deploy.sh --help
./backup.sh help
./update.sh --help
```

### 技术支持

- 📧 Email: support@your-domain.com
- 📚 文档: https://docs.your-domain.com
- 🐛 Issues: https://github.com/your-repo/issues

---

## ⚡ 常见问题

### 1. 如何更改端口？

编辑 `.env` 文件：

```bash
BACKEND_PORT=8888
WORKFLOW_CTL_PORT=8889
FRONTEND_PORT=80
```

### 2. 如何切换数据库？

编辑 `.env` 文件中的 `DATABASE_URL`：

```bash
# MySQL
BACKEND_DATABASE_URL=mysql+pymysql://user:pass@host:3306/db

# SQLite
BACKEND_DATABASE_URL=sqlite:///./app.db
```

### 3. 如何增加 worker 数量？

编辑 `backend/Dockerfile` 和 `workflow-ctl/Dockerfile`：

```dockerfile
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8888", "--workers", "8"]
```

### 4. 如何配置多域名？

编辑 Nginx 配置文件，添加新的 server 块。

### 5. 如何迁移到其他服务器？

```bash
# 1. 在旧服务器备份
./backup.sh full

# 2. 复制备份文件到新服务器
scp -r /backup/xinhua new-server:/backup/

# 3. 在新服务器部署
./quick-deploy.sh

# 4. 恢复数据
./backup.sh restore /backup/xinhua/backup.sql.gz
```

---

## 📅 版本历史

- **v1.0.0** (2025-12-09)
  - ✨ 初始版本
  - ✨ 一键部署脚本
  - ✨ 自动备份和健康检查
  - ✨ Docker 和传统两种部署方式
  - ✨ 完整的文档和脚本

---

## 📝 下一步

部署完成后，建议：

1. ✅ 配置 SSL/HTTPS
2. ✅ 设置自动备份和健康检查
3. ✅ 配置告警（邮件或 Slack）
4. ✅ 测试备份恢复流程
5. ✅ 添加监控（Prometheus + Grafana）
6. ✅ 优化性能配置
7. ✅ 阅读 API 文档，开始使用

---

**祝你部署顺利！🎉**

如有问题，请查阅完整部署指南或联系技术支持。

---

**最后更新**: 2025-12-09  
**维护者**: Xuanfeng Tech Team

