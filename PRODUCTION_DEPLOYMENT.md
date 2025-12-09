# 新华项目生产环境部署方案

## 📋 目录
- [系统架构](#系统架构)
- [环境要求](#环境要求)
- [部署方案](#部署方案)
  - [方案一：Docker Compose 部署（推荐）](#方案一docker-compose-部署推荐)
  - [方案二：传统部署](#方案二传统部署)
- [SSL/HTTPS 配置](#sslhttps-配置)
- [监控和日志](#监控和日志)
- [备份策略](#备份策略)
- [性能优化](#性能优化)
- [故障排除](#故障排除)

---

## 系统架构

```
┌─────────────────────────────────────────────────────┐
│                   Nginx (Port 80/443)                │
│              前端 + API 反向代理                      │
└─────────────────────┬───────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Frontend │  │ Backend  │  │Workflow  │
│  (React) │  │  :8888   │  │   -ctl   │
│          │  │          │  │  :8889   │
└──────────┘  └─────┬────┘  └─────┬────┘
                    │             │
                    ▼             ▼
              ┌──────────┐  ┌──────────┐
              │  MySQL   │  │ SQLite/  │
              │   RDS    │  │  MySQL   │
              └──────────┘  └──────────┘
```

## 环境要求

### 服务器配置建议

| 环境 | CPU | 内存 | 硬盘 | 带宽 |
|------|-----|------|------|------|
| 小型（<1000用户） | 2核 | 4GB | 40GB | 5Mbps |
| 中型（1000-5000用户） | 4核 | 8GB | 100GB | 10Mbps |
| 大型（>5000用户） | 8核+ | 16GB+ | 200GB+ | 20Mbps+ |

### 软件要求

#### Docker 部署（推荐）
- OS: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- Docker: 20.10+
- Docker Compose: 2.0+

#### 传统部署
- OS: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- Python: 3.9+
- Node.js: 18+
- Nginx: 1.18+
- MySQL Client: 8.0+

---

## 部署方案

### 方案一：Docker Compose 部署（推荐）

#### 1. 准备服务器

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

#### 2. 上传项目代码

```bash
# 在服务器上创建项目目录
sudo mkdir -p /opt/xinhua
cd /opt/xinhua

# 方式1: 使用 git 克隆（推荐）
git clone <your-repository-url> .

# 方式2: 使用 scp 上传
# 在本地执行：
# cd /path/to/xinhua
# tar czf xinhua.tar.gz backend frontend workflow-ctl docker-compose.yml env.example deploy.sh
# scp xinhua.tar.gz user@server:/opt/xinhua/
# 在服务器上解压：
# tar xzf xinhua.tar.gz
```

#### 3. 配置环境变量

```bash
cd /opt/xinhua

# 复制环境变量模板
cp env.example .env

# 编辑环境变量（重要！）
nano .env
```

**必须修改的环境变量：**

```bash
# ==================== 后端服务配置 ====================
# Backend Database (使用你的MySQL配置)
BACKEND_DATABASE_URL=mysql+pymysql://username:password@host:3306/database?charset=utf8mb4
DB_HOST=your-mysql-host
DB_PORT=3306
DB_NAME=xinhua_prod
DB_USER=xinhua_user
DB_PASSWORD=your-strong-password

# 安全密钥（生成随机字符串）
SECRET_KEY=$(openssl rand -hex 32)
DEBUG=False

# 允许的来源（添加你的域名）
ALLOWED_ORIGINS=http://your-domain.com,https://your-domain.com

# ==================== Workflow Control 服务配置 ====================
# 生产环境建议使用 MySQL
WORKFLOW_CTL_DATABASE_URL=mysql+pymysql://username:password@host:3306/workflow_db?charset=utf8mb4
# 或使用 SQLite（小型应用）
# WORKFLOW_CTL_DATABASE_URL=sqlite:///./data/workflow.db

# ==================== 服务端口配置 ====================
BACKEND_PORT=8888
WORKFLOW_CTL_PORT=8889
FRONTEND_PORT=80
```

#### 4. 创建必要目录

```bash
# 创建日志目录
sudo mkdir -p /opt/xinhua/logs/{backend,workflow-ctl}

# 创建数据目录
sudo mkdir -p /opt/xinhua/workflow-ctl/data

# 设置权限
sudo chmod -R 755 /opt/xinhua/logs
sudo chmod -R 755 /opt/xinhua/workflow-ctl/data
```

#### 5. 构建和启动服务

```bash
cd /opt/xinhua

# 构建镜像（首次部署或代码更新后）
docker-compose build --no-cache

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

#### 6. 初始化数据库

```bash
# 初始化后端数据库
docker-compose exec backend python init_db.py

# 初始化 workflow-ctl 数据库
docker-compose exec workflow-ctl python init_db.py
```

#### 7. 验证部署

```bash
# 检查后端健康
curl http://localhost:8888/health

# 检查 workflow-ctl 健康
curl http://localhost:8889/health

# 检查前端
curl http://localhost/
```

#### 8. 配置开机自启

```bash
# 创建 systemd 服务
sudo nano /etc/systemd/system/xinhua.service
```

添加以下内容：

```ini
[Unit]
Description=Xinhua Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/xinhua
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

启用服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable xinhua.service
sudo systemctl start xinhua.service
```

---

### 方案二：传统部署

#### 1. 安装系统依赖

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.9 python3-pip python3-venv nginx mysql-client git curl

# CentOS/RHEL
sudo yum install -y python39 python39-pip nginx mysql git curl

# 安装 Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

#### 2. 部署后端服务

```bash
# 创建项目目录
sudo mkdir -p /opt/xinhua/backend
cd /opt/xinhua/backend

# 上传或克隆代码
# git clone <repository-url> .

# 创建虚拟环境
python3.9 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp env.example .env
nano .env

# 初始化数据库
python init_db.py

# 测试启动
uvicorn main:app --host 0.0.0.0 --port 8888
```

**创建 Systemd 服务：**

```bash
sudo nano /etc/systemd/system/xinhua-backend.service
```

```ini
[Unit]
Description=Xinhua Backend API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/xinhua/backend
Environment="PATH=/opt/xinhua/backend/venv/bin"
ExecStart=/opt/xinhua/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8888 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable xinhua-backend
sudo systemctl start xinhua-backend
sudo systemctl status xinhua-backend
```

#### 3. 部署 Workflow-ctl 服务

```bash
# 创建项目目录
sudo mkdir -p /opt/xinhua/workflow-ctl
cd /opt/xinhua/workflow-ctl

# 创建虚拟环境
python3.9 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python init_db.py
```

**创建 Systemd 服务：**

```bash
sudo nano /etc/systemd/system/xinhua-workflow-ctl.service
```

```ini
[Unit]
Description=Xinhua Workflow Control API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/xinhua/workflow-ctl
Environment="PATH=/opt/xinhua/workflow-ctl/venv/bin"
Environment="DATABASE_URL=sqlite:///./data/workflow.db"
ExecStart=/opt/xinhua/workflow-ctl/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8889 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable xinhua-workflow-ctl
sudo systemctl start xinhua-workflow-ctl
sudo systemctl status xinhua-workflow-ctl
```

#### 4. 部署前端

```bash
# 创建项目目录
sudo mkdir -p /opt/xinhua/frontend
cd /opt/xinhua/frontend

# 安装依赖并构建
npm install
npm run build

# 将构建产物移动到 Nginx 目录
sudo mkdir -p /var/www/xinhua
sudo cp -r dist/* /var/www/xinhua/
```

#### 5. 配置 Nginx

```bash
sudo nano /etc/nginx/sites-available/xinhua.conf
```

```nginx
# HTTP Server
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # 重定向到 HTTPS（可选，配置 SSL 后启用）
    # return 301 https://$server_name$request_uri;
    
    # 前端静态文件
    root /var/www/xinhua;
    index index.html;
    
    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript 
               application/x-javascript application/xml+rss 
               application/json application/javascript;
    
    # 前端路由
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
    
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 后端 API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8888/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # Workflow-ctl API 代理
    location /workflow-api/ {
        proxy_pass http://127.0.0.1:8889/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # 代理路由
    location /proxy/ {
        proxy_pass http://127.0.0.1:8888/proxy/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

启用站点：

```bash
# 启用配置
sudo ln -s /etc/nginx/sites-available/xinhua.conf /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

---

## SSL/HTTPS 配置

### 使用 Let's Encrypt 免费证书

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取证书
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 自动续期测试
sudo certbot renew --dry-run
```

### HTTPS Nginx 配置

```nginx
# HTTPS Server
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL 证书
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # 其他配置同 HTTP...
}

# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## 监控和日志

### 日志位置

#### Docker 部署
```bash
# 查看容器日志
docker-compose logs -f backend
docker-compose logs -f workflow-ctl
docker-compose logs -f frontend

# 日志文件位置
/opt/xinhua/logs/backend/
/opt/xinhua/logs/workflow-ctl/
```

#### 传统部署
```bash
# Systemd 日志
sudo journalctl -u xinhua-backend -f
sudo journalctl -u xinhua-workflow-ctl -f

# Nginx 日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 日志轮转配置

```bash
sudo nano /etc/logrotate.d/xinhua
```

```
/opt/xinhua/logs/*/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload xinhua-backend
        systemctl reload xinhua-workflow-ctl
    endscript
}
```

### 监控服务

使用 **Prometheus + Grafana** 或简单的健康检查脚本：

```bash
#!/bin/bash
# /opt/xinhua/health_check.sh

# 检查后端
if ! curl -f http://localhost:8888/health > /dev/null 2>&1; then
    echo "Backend is down!" | mail -s "Alert: Backend Down" admin@example.com
fi

# 检查 workflow-ctl
if ! curl -f http://localhost:8889/health > /dev/null 2>&1; then
    echo "Workflow-ctl is down!" | mail -s "Alert: Workflow-ctl Down" admin@example.com
fi

# 检查前端
if ! curl -f http://localhost/ > /dev/null 2>&1; then
    echo "Frontend is down!" | mail -s "Alert: Frontend Down" admin@example.com
fi
```

添加到 crontab：

```bash
# 每5分钟检查一次
*/5 * * * * /opt/xinhua/health_check.sh
```

---

## 备份策略

### 自动备份脚本

```bash
#!/bin/bash
# /opt/xinhua/backup.sh

BACKUP_DIR="/backup/xinhua"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库（MySQL）
mysqldump -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME > $BACKUP_DIR/backend_db_$DATE.sql

# 备份 SQLite（如果使用）
cp /opt/xinhua/workflow-ctl/data/workflow.db $BACKUP_DIR/workflow_db_$DATE.db

# 备份日志
tar czf $BACKUP_DIR/logs_$DATE.tar.gz /opt/xinhua/logs/

# 备份配置文件
cp /opt/xinhua/.env $BACKUP_DIR/env_$DATE.txt

# 删除30天前的备份
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: $DATE"
```

设置自动备份：

```bash
chmod +x /opt/xinhua/backup.sh

# 每天凌晨2点备份
crontab -e
0 2 * * * /opt/xinhua/backup.sh
```

### 远程备份

```bash
# 同步到远程服务器
rsync -avz /backup/xinhua/ user@backup-server:/backup/xinhua/

# 或上传到对象存储（阿里云 OSS）
# 安装 ossutil
# 配置后使用：
ossutil cp -r /backup/xinhua/ oss://your-bucket/xinhua-backup/
```

---

## 性能优化

### 1. 数据库优化

```sql
-- 创建必要的索引
ALTER TABLE workflows ADD INDEX idx_status (status);
ALTER TABLE apikeys ADD INDEX idx_status (status);
ALTER TABLE prompts ADD INDEX idx_model_type (modelType);

-- 定期优化表
OPTIMIZE TABLE workflows;
OPTIMIZE TABLE apikeys;
OPTIMIZE TABLE prompts;
```

### 2. 应用层优化

**后端优化：**

```python
# backend/main.py
# 增加 worker 数量
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8888,
        workers=4,  # CPU核心数
        reload=False
    )
```

### 3. Nginx 优化

```nginx
# /etc/nginx/nginx.conf
worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    # 连接池
    keepalive_timeout 65;
    keepalive_requests 100;
    
    # 缓冲区
    client_body_buffer_size 128k;
    client_max_body_size 10m;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 4k;
    
    # 缓存
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=1g inactive=60m;
    proxy_cache_key "$scheme$request_method$host$request_uri";
}
```

### 4. Docker 优化

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

---

## 故障排除

### 常见问题

#### 1. 容器无法启动

```bash
# 查看详细日志
docker-compose logs backend

# 检查端口占用
sudo netstat -tlnp | grep 8888

# 重新构建
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### 2. 数据库连接失败

```bash
# 测试数据库连接
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD -e "SELECT 1"

# 检查防火墙
sudo ufw status
sudo ufw allow 3306

# 检查 MySQL 远程访问权限
GRANT ALL PRIVILEGES ON database.* TO 'user'@'%' IDENTIFIED BY 'password';
FLUSH PRIVILEGES;
```

#### 3. Nginx 502 错误

```bash
# 检查后端服务状态
curl http://localhost:8888/health

# 检查 Nginx 配置
sudo nginx -t

# 查看 Nginx 错误日志
sudo tail -f /var/log/nginx/error.log

# 检查 SELinux（CentOS）
sudo setsebool -P httpd_can_network_connect 1
```

#### 4. 前端白屏

```bash
# 检查构建产物
ls -la /var/www/xinhua/

# 重新构建前端
cd /opt/xinhua/frontend
npm run build

# 检查浏览器控制台
# F12 -> Console 查看错误
```

#### 5. 内存不足

```bash
# 查看内存使用
free -h
docker stats

# 增加 swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 更新和维护

### 代码更新流程

```bash
# 1. 备份当前版本
./backup.sh

# 2. 拉取最新代码
cd /opt/xinhua
git pull origin main

# 3. Docker 部署更新
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# 4. 传统部署更新
# 后端
sudo systemctl stop xinhua-backend
cd /opt/xinhua/backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl start xinhua-backend

# 前端
cd /opt/xinhua/frontend
npm install
npm run build
sudo cp -r dist/* /var/www/xinhua/

# workflow-ctl
sudo systemctl stop xinhua-workflow-ctl
cd /opt/xinhua/workflow-ctl
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl start xinhua-workflow-ctl

# 5. 验证更新
curl http://localhost:8888/health
curl http://localhost:8889/health
curl http://localhost/
```

### 数据库迁移

```bash
# 如果有数据库结构变更
cd /opt/xinhua/backend
docker-compose exec backend alembic upgrade head

# 或传统部署
cd /opt/xinhua/backend
source venv/bin/activate
alembic upgrade head
```

---

## 安全加固

### 1. 防火墙配置

```bash
# Ubuntu UFW
sudo ufw enable
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw deny 8888/tcp  # 禁止外部直接访问后端
sudo ufw deny 8889/tcp  # 禁止外部直接访问 workflow-ctl
```

### 2. SSH 安全

```bash
# 禁用密码登录，只用密钥
sudo nano /etc/ssh/sshd_config
```

```
PasswordAuthentication no
PermitRootLogin no
```

### 3. 自动安全更新

```bash
# Ubuntu
sudo apt install unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

### 4. Fail2ban 防暴力破解

```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## 快速部署命令

### Docker 一键部署

```bash
# 下载部署脚本
curl -fsSL https://your-domain.com/quick-deploy.sh -o quick-deploy.sh
chmod +x quick-deploy.sh

# 运行部署
./quick-deploy.sh
```

---

## 联系和支持

- 技术支持: support@your-domain.com
- 文档: https://docs.your-domain.com
- Issue: https://github.com/your-repo/issues

---

## 附录

### 常用命令速查

```bash
# Docker Compose
docker-compose up -d                 # 启动所有服务
docker-compose down                  # 停止所有服务
docker-compose restart               # 重启所有服务
docker-compose logs -f [service]     # 查看日志
docker-compose ps                    # 查看服务状态
docker-compose exec [service] bash   # 进入容器

# Systemd
sudo systemctl start xinhua-backend        # 启动服务
sudo systemctl stop xinhua-backend         # 停止服务
sudo systemctl restart xinhua-backend      # 重启服务
sudo systemctl status xinhua-backend       # 查看状态
sudo systemctl enable xinhua-backend       # 开机自启
sudo journalctl -u xinhua-backend -f       # 查看日志

# Nginx
sudo nginx -t                        # 测试配置
sudo systemctl reload nginx          # 重新加载配置
sudo systemctl restart nginx         # 重启 Nginx

# 数据库
docker-compose exec backend python init_db.py       # 初始化数据库
mysqldump -h host -u user -ppass db > backup.sql    # 备份数据库
mysql -h host -u user -ppass db < backup.sql        # 恢复数据库
```

### 端口说明

| 服务 | 默认端口 | 说明 |
|------|---------|------|
| Frontend | 80 | 前端 Web 服务 |
| Frontend (HTTPS) | 443 | HTTPS Web 服务 |
| Backend | 8888 | 后端 API（内部） |
| Workflow-ctl | 8889 | 工作流控制 API（内部） |
| MySQL | 3306 | 数据库（如果本地部署） |

---

**最后更新时间:** 2025-12-09

