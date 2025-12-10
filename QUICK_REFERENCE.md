# 新华工具 - 快速参考卡

---

## ⚡ 快速部署

```bash
# 1. 准备环境
cp env.production .env    # 生产环境
# 或
cp env.example .env       # 开发环境

# 2. 编辑配置 (如需要)
vim .env

# 3. 部署
./deploy.sh docker --production

# 4. 验证
./manage.sh status
```

---

## 🌐 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| **前端** | `http://服务器IP:8787` | Web 界面 |
| **后端 API** | `http://服务器IP:8888` | API 服务 |
| **API 文档** | `http://服务器IP:8888/docs` | Swagger 文档 |
| **工作流 API** | `http://服务器IP:8889` | 工作流服务 |
| **工作流文档** | `http://服务器IP:8889/docs` | Swagger 文档 |

---

## 🎮 常用命令

### 服务管理
```bash
./manage.sh start           # 启动所有服务
./manage.sh stop            # 停止所有服务
./manage.sh restart         # 重启所有服务
./manage.sh restart backend # 重启指定服务
./manage.sh status          # 查看服务状态
./manage.sh health          # 健康检查
```

### 日志查看
```bash
./manage.sh logs                # 实时查看所有日志
./manage.sh logs backend        # 查看后端日志
./manage.sh logs workflow-ctl   # 查看工作流日志
./manage.sh logs frontend       # 查看前端日志
./manage.sh logs-tail 100       # 查看最后 100 行
./manage.sh logs-error          # 查看错误日志
```

### 容器操作
```bash
./manage.sh ps                  # 查看容器状态
./manage.sh top                 # 查看资源占用
./manage.sh exec backend        # 进入后端容器
./manage.sh rebuild             # 重新构建所有镜像
./manage.sh rebuild frontend    # 重新构建前端
```

### 数据维护
```bash
./manage.sh backup              # 备份数据
./manage.sh clean-logs          # 清理旧日志
./manage.sh db-migrate          # 数据库迁移
```

### 诊断工具
```bash
./manage.sh test-network        # 测试容器网络
./manage.sh test-db             # 测试数据库连接
./manage.sh test-api            # 测试 API 端点
```

### 更新维护
```bash
./manage.sh update              # 更新部署
./manage.sh clean               # 清理 Docker 资源
```

---

## 🔧 关键配置

### 环境变量 (.env)

```bash
# 数据库 (阿里云 RDS)
DB_HOST=rm-bp1jldp727lmxq1m57o.mysql.rds.aliyuncs.com
DB_PORT=3306
DB_NAME=xinhua_dev
DB_USER=xuanfeng_dev
DB_PASSWORD=xuanfengkeji2025%

# Backend 连接 (注意 % 编码为 %25)
BACKEND_DATABASE_URL=mysql+pymysql://xuanfeng_dev:xuanfengkeji2025%25@rm-bp1jldp727lmxq1m57o.mysql.rds.aliyuncs.com:3306/xinhua_dev?charset=utf8mb4

# 安全
SECRET_KEY=79e978b8fc5cfd3166db9b270f486045ccfd6b4c2e49f12426f9819da5fe4ab2
DEBUG=False

# CORS
ALLOWED_ORIGINS=http://69.5.14.25:8787,http://69.5.14.25
```

⚠️ **重要**: 密码中的 `%` 必须编码为 `%25`！

### Docker 网络

- **网络名**: `xinhua-tool_xinhua-network`
- **服务别名**:
  - `backend` → `xinhua-backend:8888`
  - `workflow-ctl` → `xinhua-workflow-ctl:8889`
  - `frontend` → `xinhua-frontend:80` (映射到主机 8787)

### Nginx 代理

```nginx
# 在容器内部
location /api/ {
    proxy_pass http://backend:8888/api/;  # 使用服务名
}

location /workflow-api/ {
    proxy_pass http://workflow-ctl:8889/api/;
}
```

---

## 🚨 故障排查速查

### 服务无法启动
```bash
docker-compose logs               # 查看日志
docker-compose config             # 验证配置
netstat -tlnp | grep 8787         # 检查端口
```

### 健康检查失败
```bash
./manage.sh health                # 健康检查
curl http://localhost:8888/health # 测试后端
curl http://localhost:8889/health # 测试工作流
curl http://localhost:8787        # 测试前端
```

### 数据库连接失败
```bash
./manage.sh test-db               # 测试连接
# 检查 .env 中密码编码是否正确 (% → %25)
```

### 网络问题
```bash
./manage.sh test-network          # 网络测试
docker network ls                 # 查看网络
docker network inspect xinhua-tool_xinhua-network
```

### 端口冲突
```bash
lsof -i :8787                     # 查看占用
lsof -i :8888
lsof -i :8889
# 修改 docker-compose.yml 端口映射
```

---

## 📊 Docker Compose 命令

### 基本操作
```bash
docker-compose up -d              # 启动 (后台)
docker-compose down               # 停止并删除
docker-compose restart            # 重启
docker-compose ps                 # 查看状态
```

### 日志查看
```bash
docker-compose logs -f            # 实时日志
docker-compose logs -f backend    # 特定服务
docker-compose logs --tail=100    # 最后 100 行
```

### 构建相关
```bash
docker-compose build              # 构建镜像
docker-compose build --no-cache   # 强制重建
docker-compose up -d --build      # 构建并启动
```

### 服务管理
```bash
docker-compose start backend      # 启动服务
docker-compose stop backend       # 停止服务
docker-compose restart backend    # 重启服务
```

---

## 🔐 安全检查清单

- [ ] 修改默认 `SECRET_KEY`
- [ ] 设置 `.env` 文件权限 (`chmod 600 .env`)
- [ ] 配置防火墙规则
- [ ] 使用强数据库密码
- [ ] 配置 RDS 白名单
- [ ] 设置 `DEBUG=False`
- [ ] 配置正确的 `ALLOWED_ORIGINS`
- [ ] 启用 HTTPS (生产环境)
- [ ] 定期备份数据
- [ ] 监控日志文件大小

---

## 📦 文件结构

```
xinhua-tool/
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt        # ✅ 已添加 requests
│   └── ...
├── workflow-ctl/
│   ├── Dockerfile
│   ├── requirements.txt        # ✅ 已添加 requests
│   └── ...
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf              # ✅ 代理配置正确
│   └── ...
├── docker-compose.yml          # ✅ 已优化 (RDS + 健康检查)
├── deploy.sh                   # ✅ 优化的部署脚本
├── manage.sh                   # ✅ 便捷管理脚本
├── env.example                 # 开发环境模板
├── env.production              # 生产环境模板
├── .env                        # 实际配置 (不提交到 Git)
├── DEPLOYMENT.md               # 完整部署文档
└── QUICK_REFERENCE.md          # 本文件
```

---

## 🆘 获取帮助

```bash
./deploy.sh --help        # 部署帮助
./manage.sh help          # 管理帮助
```

详细文档: [DEPLOYMENT.md](DEPLOYMENT.md)

---

**提示**: 将此文件保存为快速参考，或打印出来放在手边！


