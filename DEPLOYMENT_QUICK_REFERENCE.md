# 新华项目部署快速参考

## 📦 一键部署

### Docker 快速部署（推荐）

```bash
# 1. 下载项目
git clone <your-repository-url> /opt/xinhua
cd /opt/xinhua

# 2. 运行一键部署脚本
chmod +x quick-deploy.sh
./quick-deploy.sh

# 部署完成！访问 http://your-server-ip
```

### 手动 Docker 部署

```bash
# 1. 配置环境变量
cp env.example .env
nano .env  # 修改数据库配置等

# 2. 创建必要目录
mkdir -p logs/{backend,workflow-ctl}
mkdir -p workflow-ctl/data

# 3. 构建和启动
docker-compose build
docker-compose up -d

# 4. 初始化数据库
docker-compose exec backend python init_db.py
docker-compose exec workflow-ctl python init_db.py

# 5. 验证
curl http://localhost:8888/health
curl http://localhost:8889/health
curl http://localhost/
```

---

## 🔧 常用命令

### Docker Compose 命令

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启服务
docker-compose restart

# 重启单个服务
docker-compose restart backend

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
docker-compose logs -f backend

# 进入容器
docker-compose exec backend bash
docker-compose exec workflow-ctl bash

# 重新构建
docker-compose build --no-cache

# 清理无用镜像
docker image prune -f
docker system prune -af
```

### Systemd 命令（传统部署）

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

# 开机自启
sudo systemctl enable xinhua-backend
sudo systemctl enable xinhua-workflow-ctl
```

### Nginx 命令

```bash
# 测试配置
sudo nginx -t

# 重新加载配置
sudo systemctl reload nginx

# 重启 Nginx
sudo systemctl restart nginx

# 查看错误日志
sudo tail -f /var/log/nginx/error.log

# 查看访问日志
sudo tail -f /var/log/nginx/access.log
```

---

## 🔄 更新和维护

### 更新项目

```bash
# 使用更新脚本（推荐）
chmod +x update.sh
./update.sh

# 强制更新（不提示）
./update.sh --force

# 更新但不备份
./update.sh --no-backup
```

### 手动更新

```bash
# 1. 备份
./backup.sh full

# 2. 拉取最新代码
git pull origin main

# 3. 重新构建和部署
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# 4. 验证
./health_check.sh
```

---

## 💾 备份和恢复

### 备份

```bash
# 完整备份
./backup.sh full

# 快速备份（仅数据库和配置）
./backup.sh quick

# 查看备份列表
./backup.sh list

# 自动备份（添加到 crontab）
crontab -e
# 添加：0 2 * * * /opt/xinhua/backup.sh full
```

### 恢复

```bash
# 恢复 MySQL 数据库
./backup.sh restore /backup/xinhua/20231209/mysql_backup.sql.gz

# 恢复 SQLite 数据库
./backup.sh restore /backup/xinhua/20231209/workflow_backup.db.gz

# 手动恢复
gunzip < backup.sql.gz | mysql -h host -u user -ppass database
```

---

## 🏥 健康检查

### 运行健康检查

```bash
# 手动检查
chmod +x health_check.sh
./health_check.sh

# 自动检查（添加到 crontab）
crontab -e
# 添加：*/5 * * * * /opt/xinhua/health_check.sh

# 查看检查日志
tail -f /var/log/xinhua/health_check.log
```

### 手动健康检查

```bash
# 检查后端
curl http://localhost:8888/health

# 检查 workflow-ctl
curl http://localhost:8889/health

# 检查前端
curl http://localhost/

# 检查数据库连接
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD -e "SELECT 1"

# 检查系统资源
free -h
df -h
docker stats --no-stream
```

---

## 🔐 SSL/HTTPS 配置

### 安装 Let's Encrypt 证书

```bash
# 1. 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 2. 获取证书
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 3. 测试自动续期
sudo certbot renew --dry-run

# 证书会自动续期，无需手动操作
```

### 手动配置 SSL

```bash
# 1. 复制生产环境 Nginx 配置
sudo cp deploy/nginx/xinhua-production.conf /etc/nginx/sites-available/xinhua.conf

# 2. 修改域名和证书路径
sudo nano /etc/nginx/sites-available/xinhua.conf

# 3. 启用配置
sudo ln -s /etc/nginx/sites-available/xinhua.conf /etc/nginx/sites-enabled/

# 4. 测试和重启
sudo nginx -t
sudo systemctl reload nginx
```

---

## 📊 监控和日志

### 查看日志

```bash
# Docker 日志
docker-compose logs -f
docker-compose logs -f --tail=100 backend

# 应用日志
tail -f /opt/xinhua/logs/backend/*.log
tail -f /opt/xinhua/logs/workflow-ctl/*.log

# Nginx 日志
tail -f /var/log/nginx/xinhua_access.log
tail -f /var/log/nginx/xinhua_error.log

# 系统日志
sudo journalctl -xe
```

### 性能监控

```bash
# 查看容器资源使用
docker stats

# 查看系统资源
htop
iostat
vmstat 1

# 查看网络连接
netstat -tlnp
ss -tlnp

# 查看进程
ps aux | grep uvicorn
ps aux | grep nginx
```

---

## 🐛 故障排除

### 服务无法启动

```bash
# 1. 查看日志
docker-compose logs backend
sudo journalctl -u xinhua-backend -n 100

# 2. 检查端口占用
sudo netstat -tlnp | grep 8888
sudo lsof -i :8888

# 3. 检查配置
docker-compose config

# 4. 重新构建
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 数据库连接失败

```bash
# 1. 测试连接
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD

# 2. 检查防火墙
sudo ufw status
sudo ufw allow 3306

# 3. 检查环境变量
cat .env | grep DB_

# 4. 查看详细错误
docker-compose logs backend | grep -i database
```

### Nginx 502 错误

```bash
# 1. 检查后端服务
curl http://localhost:8888/health

# 2. 检查 Nginx 配置
sudo nginx -t

# 3. 查看 Nginx 错误日志
sudo tail -f /var/log/nginx/error.log

# 4. 检查 SELinux（CentOS）
sudo setsebool -P httpd_can_network_connect 1
```

### 内存不足

```bash
# 1. 查看内存使用
free -h
docker stats

# 2. 添加 swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 3. 减少 worker 数量
# 修改 backend/Dockerfile 中的 --workers 参数
```

### 磁盘空间不足

```bash
# 1. 查看磁盘使用
df -h
du -sh /opt/xinhua/*

# 2. 清理 Docker
docker system prune -af
docker volume prune -f

# 3. 清理日志
find /opt/xinhua/logs -name "*.log" -mtime +7 -delete
sudo journalctl --vacuum-time=7d

# 4. 清理旧备份
find /backup/xinhua -mtime +30 -delete
```

---

## 🔒 安全加固

### 防火墙配置

```bash
# Ubuntu UFW
sudo ufw enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 8888/tcp   # 禁止外部访问后端
sudo ufw deny 8889/tcp   # 禁止外部访问 workflow-ctl
sudo ufw status
```

### SSH 安全

```bash
# 禁用密码登录
sudo nano /etc/ssh/sshd_config
# 设置：
# PasswordAuthentication no
# PermitRootLogin no

sudo systemctl restart sshd
```

### Fail2ban（防暴力破解）

```bash
# 安装
sudo apt install fail2ban

# 启用
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# 查看状态
sudo fail2ban-client status
```

---

## 📝 配置文件位置

### Docker 部署

```
/opt/xinhua/
├── .env                              # 环境变量配置
├── docker-compose.yml                # Docker Compose 配置
├── docker-compose.production.yml     # 生产环境配置
├── backend/
│   ├── app.db                       # 后端数据库（SQLite）
│   └── requirements.txt             # Python 依赖
├── workflow-ctl/
│   └── data/workflow.db             # Workflow 数据库
├── frontend/
│   └── nginx.conf                   # Nginx 配置
└── logs/
    ├── backend/                     # 后端日志
    └── workflow-ctl/                # Workflow 日志
```

### 传统部署

```
/opt/xinhua/                         # 项目目录
/var/www/xinhua/                     # 前端静态文件
/etc/nginx/sites-available/          # Nginx 配置
/etc/systemd/system/                 # Systemd 服务文件
/var/log/nginx/                      # Nginx 日志
/backup/xinhua/                      # 备份目录
```

---

## 🚀 性能优化

### 数据库优化

```sql
-- 添加索引
ALTER TABLE workflows ADD INDEX idx_status (status);
ALTER TABLE apikeys ADD INDEX idx_status (status);

-- 定期优化
OPTIMIZE TABLE workflows;
OPTIMIZE TABLE apikeys;
```

### Nginx 优化

```bash
# 编辑 Nginx 配置
sudo nano /etc/nginx/nginx.conf

# 增加 worker 连接数
worker_processes auto;
worker_connections 4096;

# 启用 HTTP/2
listen 443 ssl http2;

# 启用 Gzip 压缩
gzip on;
gzip_comp_level 6;
```

### Docker 优化

```bash
# 限制容器资源
# 编辑 docker-compose.production.yml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
```

---

## 📞 获取帮助

### 查看文档

```bash
# 完整部署指南
cat PRODUCTION_DEPLOYMENT.md

# API 文档
cat docs/API.md

# 变更日志
cat CHANGES_SUMMARY.md
```

### 运行测试

```bash
# 后端测试
cd backend
python -m pytest

# 前端测试
cd frontend
npm test
```

---

## 🎯 最佳实践

1. **定期备份**: 每天自动备份数据库和配置
2. **监控服务**: 使用健康检查脚本定期检查服务状态
3. **更新策略**: 在低峰期更新，使用更新脚本自动回滚
4. **日志管理**: 定期清理旧日志，保留最近30天
5. **安全审计**: 定期检查安全更新，及时修复漏洞
6. **性能监控**: 监控系统资源使用，及时扩容
7. **灾难恢复**: 定期测试备份恢复流程

---

**最后更新**: 2025-12-09

