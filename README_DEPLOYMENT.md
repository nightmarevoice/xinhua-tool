# 新华工具 - 部署指南

> 📦 完整优化的 Docker 部署方案 - 生产就绪

---

## 🎯 快速开始

### Linux / macOS

```bash
# 1. 运行设置脚本
chmod +x setup.sh
./setup.sh

# 2. 部署
./deploy.sh docker --production

# 3. 验证
./manage.sh status
```

### Windows

```batch
# 1. 运行设置脚本
setup.bat

# 2. 在 Git Bash 中部署
bash -c "./deploy.sh docker --production"

# 或直接使用 Docker Compose
docker-compose up -d
```

---

## 📁 项目文件说明

### 核心文件

| 文件 | 说明 | 用途 |
|------|------|------|
| `docker-compose.yml` | Docker Compose 配置 | ✅ 已优化 (RDS + 健康检查) |
| `deploy.sh` | 自动化部署脚本 | ✅ 增强功能 (彩色输出 + 错误处理) |
| `manage.sh` | 服务管理脚本 | ✅ 20+ 管理命令 |
| `setup.sh` | 一键环境设置 | 自动完成部署前准备 |
| `setup.bat` | Windows 设置脚本 | Windows 用户使用 |

### 配置文件

| 文件 | 说明 | 状态 |
|------|------|------|
| `env.example` | 开发环境配置模板 | 新增 |
| `env.production` | 生产环境配置模板 | 新增 |
| `.env` | 实际配置文件 | 运行时生成 (不提交到 Git) |

### 依赖文件

| 文件 | 说明 | 修改 |
|------|------|------|
| `backend/requirements.txt` | 后端依赖 | ✅ 添加 requests |
| `workflow-ctl/requirements.txt` | 工作流依赖 | ✅ 添加 requests, httpx |
| `frontend/nginx.conf` | Nginx 配置 | ✅ 配置正确 |

### 文档文件

| 文件 | 说明 | 内容 |
|------|------|------|
| `DEPLOYMENT.md` | 完整部署文档 | 详细的部署指南和故障排查 |
| `QUICK_REFERENCE.md` | 快速参考卡 | 常用命令和配置速查 |
| `DEPLOYMENT_OPTIMIZATION.md` | 优化说明 | 本次优化的详细说明 |
| `README_DEPLOYMENT.md` | 本文件 | 文件清单和使用指南 |

---

## 🔧 关键配置

### 1. Docker 网络

```yaml
networks:
  xinhua-network:
    name: xinhua-tool_xinhua-network  # 固定网络名
    driver: bridge
```

**服务别名**:
- `backend` → `xinhua-backend:8888`
- `workflow-ctl` → `xinhua-workflow-ctl:8889`
- `frontend` → `xinhua-frontend:80` (映射到主机 8787)

### 2. 数据库配置

**阿里云 RDS MySQL**:
```bash
DB_HOST=rm-bp1jldp727lmxq1m57o.mysql.rds.aliyuncs.com
DB_PORT=3306
DB_NAME=xinhua_dev
DB_USER=xuanfeng_dev
DB_PASSWORD=xuanfengkeji2025%

# 注意: 密码中的 % 在 URL 中编码为 %25
BACKEND_DATABASE_URL=mysql+pymysql://xuanfeng_dev:xuanfengkeji2025%25@rm-bp1jldp727lmxq1m57o.mysql.rds.aliyuncs.com:3306/xinhua_dev?charset=utf8mb4
```

### 3. Nginx 代理

```nginx
# 容器内部使用服务名
location /api/ {
    proxy_pass http://backend:8888/api/;
}

location /workflow-api/ {
    proxy_pass http://workflow-ctl:8889/api/;
}
```

### 4. 健康检查

```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:8888/health || exit 1"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### 5. 日志管理

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"    # 单文件最大 10MB
    max-file: "3"      # 保留 3 个文件
```

---

## 📋 部署流程

### 完整流程

```bash
# 1. 环境设置
./setup.sh

# 2. 检查配置
cat .env

# 3. 部署
./deploy.sh docker --production

# 4. 等待服务启动 (约 1-2 分钟)

# 5. 验证部署
./manage.sh status
./manage.sh health
./manage.sh test-network
./manage.sh test-db

# 6. 查看日志
./manage.sh logs

# 7. 访问服务
# http://服务器IP:8787
```

### 更新部署

```bash
# 方式 1: 使用管理脚本 (推荐)
./manage.sh backup    # 先备份
./manage.sh update    # 自动更新

# 方式 2: 手动更新
./manage.sh backup
./deploy.sh docker --no-cache
```

---

## 🎮 管理命令速查

### 服务控制
```bash
./manage.sh start              # 启动
./manage.sh stop               # 停止
./manage.sh restart            # 重启
./manage.sh status             # 状态
./manage.sh health             # 健康检查
```

### 日志管理
```bash
./manage.sh logs               # 实时日志
./manage.sh logs backend       # 特定服务
./manage.sh logs-tail 100      # 最后 N 行
./manage.sh logs-error         # 错误日志
```

### 容器操作
```bash
./manage.sh ps                 # 容器状态
./manage.sh top                # 资源占用
./manage.sh exec backend       # 进入容器
./manage.sh rebuild            # 重新构建
```

### 诊断工具
```bash
./manage.sh test-network       # 网络测试
./manage.sh test-db            # 数据库测试
./manage.sh test-api           # API 测试
```

### 数据维护
```bash
./manage.sh backup             # 备份
./manage.sh clean-logs         # 清理日志
./manage.sh db-migrate         # 数据库迁移
```

---

## 🚨 常见问题

### 1. 端口冲突

**症状**: 无法启动服务，提示端口被占用

**解决**:
```bash
# 查找占用端口的进程
lsof -i :8787
lsof -i :8888
lsof -i :8889

# 停止占用进程或修改端口
```

### 2. 数据库连接失败

**症状**: 日志显示数据库连接错误

**解决**:
```bash
# 1. 检查密码编码
# 确保 .env 中密码的 % 编码为 %25

# 2. 测试连接
./manage.sh test-db

# 3. 检查网络
docker exec xinhua-backend ping rm-bp1jldp727lmxq1m57o.mysql.rds.aliyuncs.com
```

### 3. 前端无法访问后端

**症状**: 前端页面显示 API 错误

**解决**:
```bash
# 测试容器网络
./manage.sh test-network

# 测试 API
./manage.sh test-api

# 查看 Nginx 日志
./manage.sh logs frontend
```

### 4. 健康检查失败

**症状**: 容器状态 unhealthy

**解决**:
```bash
# 查看详细状态
docker inspect xinhua-backend | grep -A 10 Health

# 手动测试健康端点
curl http://localhost:8888/health

# 查看服务日志
./manage.sh logs backend
```

---

## 🔒 安全建议

### 部署前检查清单

- [ ] 修改默认 `SECRET_KEY`
- [ ] 设置 `.env` 文件权限 (`chmod 600 .env`)
- [ ] 设置 `DEBUG=False`
- [ ] 配置正确的 `ALLOWED_ORIGINS`
- [ ] 使用强数据库密码
- [ ] 配置 RDS 白名单
- [ ] 配置防火墙规则
- [ ] 启用 HTTPS (生产环境)

### 生成新密钥

```bash
# 生成 SECRET_KEY
openssl rand -hex 32

# 更新 .env
SECRET_KEY=<生成的密钥>
```

### 配置防火墙

```bash
# Ubuntu
sudo ufw allow 8787/tcp
sudo ufw allow 8888/tcp
sudo ufw allow 8889/tcp
sudo ufw enable

# CentOS
sudo firewall-cmd --permanent --add-port=8787/tcp
sudo firewall-cmd --permanent --add-port=8888/tcp
sudo firewall-cmd --permanent --add-port=8889/tcp
sudo firewall-cmd --reload
```

---

## 📊 目录结构

```
xinhua-tool/
├── backend/                     # 后端服务
│   ├── Dockerfile
│   ├── requirements.txt         # ✅ 已添加 requests
│   └── ...
├── workflow-ctl/                # 工作流服务
│   ├── Dockerfile
│   ├── requirements.txt         # ✅ 已添加 requests, httpx
│   └── ...
├── frontend/                    # 前端服务
│   ├── Dockerfile
│   ├── nginx.conf               # ✅ 代理配置正确
│   └── ...
├── logs/                        # 日志目录
│   ├── backend/
│   └── workflow-ctl/
├── backups/                     # 备份目录
├── docker-compose.yml           # ✅ Docker Compose 配置
├── deploy.sh                    # ✅ 部署脚本
├── manage.sh                    # ✅ 管理脚本
├── setup.sh                     # 环境设置脚本 (Linux/macOS)
├── setup.bat                    # 环境设置脚本 (Windows)
├── env.example                  # 开发环境配置模板
├── env.production               # 生产环境配置模板
├── .env                         # 实际配置 (运行时生成)
├── DEPLOYMENT.md                # 完整部署文档
├── QUICK_REFERENCE.md           # 快速参考
├── DEPLOYMENT_OPTIMIZATION.md   # 优化说明
└── README_DEPLOYMENT.md         # 本文件
```

---

## 🌐 访问地址

部署完成后，可通过以下地址访问：

| 服务 | 本地访问 | 远程访问 |
|------|----------|----------|
| **前端界面** | http://localhost:8787 | http://服务器IP:8787 |
| **后端 API** | http://localhost:8888 | http://服务器IP:8888 |
| **API 文档** | http://localhost:8888/docs | http://服务器IP:8888/docs |
| **工作流 API** | http://localhost:8889 | http://服务器IP:8889 |
| **工作流文档** | http://localhost:8889/docs | http://服务器IP:8889/docs |

---

## 📞 获取帮助

### 命令帮助

```bash
# 部署脚本帮助
./deploy.sh --help

# 管理脚本帮助
./manage.sh help
```

### 文档

- **完整文档**: `DEPLOYMENT.md`
- **快速参考**: `QUICK_REFERENCE.md`
- **优化说明**: `DEPLOYMENT_OPTIMIZATION.md`

### 在线资源

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [阿里云 RDS 文档](https://help.aliyun.com/product/26090.html)

---

## ✨ 优化亮点

### 1. 依赖完整性
- ✅ 修复 `requirements.txt` 缺失的依赖
- ✅ 确保容器运行时所需库完整

### 2. 网络配置
- ✅ 固定 Docker 网络名
- ✅ 配置服务别名
- ✅ 正确的 Nginx 代理配置

### 3. 数据库集成
- ✅ 支持阿里云 RDS MySQL
- ✅ 正确的密码编码处理
- ✅ 完整的连接字符串配置

### 4. 健康监控
- ✅ 完整的健康检查机制
- ✅ 服务依赖管理
- ✅ 启动顺序控制

### 5. 日志管理
- ✅ 日志文件大小限制
- ✅ 日志文件数量控制
- ✅ 持久化日志存储

### 6. 用户体验
- ✅ 彩色日志输出
- ✅ 详细的进度提示
- ✅ 完善的错误处理
- ✅ 便捷的管理命令

### 7. 文档完善
- ✅ 完整的部署文档
- ✅ 快速参考卡片
- ✅ 故障排查指南
- ✅ 安全建议

---

## 🎉 部署完成

**恭喜！** 你已经拥有一套完整优化的生产级部署方案。

### 下一步

1. ✅ 部署服务: `./deploy.sh docker --production`
2. ✅ 验证运行: `./manage.sh status`
3. ✅ 访问界面: `http://服务器IP:8787`
4. ✅ 定期备份: `./manage.sh backup`
5. ✅ 监控日志: `./manage.sh logs`

---

**版本**: v2.0  
**更新日期**: 2025-12-10  
**状态**: ✅ 生产就绪


