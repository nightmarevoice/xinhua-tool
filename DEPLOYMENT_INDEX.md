# 📚 新华项目部署文档索引

本文档提供了新华项目所有部署相关文档和脚本的索引。

---

## 🎯 快速导航

### 我是新手，想快速部署
👉 阅读 [DEPLOYMENT_README.md](DEPLOYMENT_README.md) → 运行 `./quick-deploy.sh`

### 我需要详细的部署步骤
👉 阅读 [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)

### 我需要常用命令速查
👉 查看 [DEPLOYMENT_QUICK_REFERENCE.md](DEPLOYMENT_QUICK_REFERENCE.md)

### 我需要按步骤检查部署
👉 使用 [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)

---

## 📖 文档列表

### 核心文档

| 文档 | 说明 | 适用场景 |
|------|------|---------|
| [DEPLOYMENT_README.md](DEPLOYMENT_README.md) | 部署方案总结和快速入门 | ⭐ 首次部署必读 |
| [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) | 完整的生产环境部署指南 | 详细部署步骤 |
| [DEPLOYMENT_QUICK_REFERENCE.md](DEPLOYMENT_QUICK_REFERENCE.md) | 命令和操作快速参考 | 日常运维参考 |
| [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) | 部署检查清单 | 确保部署完整性 |
| [本文档](DEPLOYMENT_INDEX.md) | 文档索引 | 查找相关资源 |

### 项目文档

| 文档 | 说明 |
|------|------|
| [README.md](README.md) | 项目总体说明 |
| [docs/API.md](docs/API.md) | API 接口文档 |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | 原有部署文档 |
| [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md) | 项目变更记录 |

---

## 🛠️ 脚本列表

### 部署脚本

| 脚本 | 说明 | 使用方法 |
|------|------|---------|
| [quick-deploy.sh](quick-deploy.sh) | ⭐ 一键部署脚本 | `./quick-deploy.sh` |
| [deploy.sh](deploy.sh) | 标准部署脚本 | `./deploy.sh docker` |
| [update.sh](update.sh) | 服务更新脚本 | `./update.sh` |

### 维护脚本

| 脚本 | 说明 | 使用方法 |
|------|------|---------|
| [backup.sh](backup.sh) | 数据备份和恢复 | `./backup.sh full` |
| [health_check.sh](health_check.sh) | 服务健康检查 | `./health_check.sh` |

### 启动脚本（开发环境）

| 脚本 | 说明 |
|------|------|
| [start.sh](start.sh) | Linux/Mac 启动脚本 |
| [start.bat](start.bat) | Windows 启动脚本 |

---

## ⚙️ 配置文件

### Docker 配置

| 文件 | 说明 |
|------|------|
| [docker-compose.yml](docker-compose.yml) | 标准 Docker Compose 配置 |
| [docker-compose.production.yml](docker-compose.production.yml) | ⭐ 生产环境 Docker Compose 配置 |
| [backend/Dockerfile](backend/Dockerfile) | 后端 Docker 配置 |
| [frontend/Dockerfile](frontend/Dockerfile) | 前端 Docker 配置 |
| [workflow-ctl/Dockerfile](workflow-ctl/Dockerfile) | Workflow-ctl Docker 配置 |

### Nginx 配置

| 文件 | 说明 |
|------|------|
| [frontend/nginx.conf](frontend/nginx.conf) | 前端 Nginx 配置（Docker 内） |
| [deploy/nginx/xinhua.conf](deploy/nginx/xinhua.conf) | 标准 Nginx 配置 |
| [deploy/nginx/xinhua-production.conf](deploy/nginx/xinhua-production.conf) | ⭐ 生产环境 Nginx 配置（含 SSL） |

### Systemd 配置

| 文件 | 说明 |
|------|------|
| [deploy/systemd/xinhua-backend.service](deploy/systemd/xinhua-backend.service) | 后端系统服务配置 |
| [deploy/systemd/xinhua-workflow-ctl.service](deploy/systemd/xinhua-workflow-ctl.service) | Workflow-ctl 系统服务配置 |

### 环境配置

| 文件 | 说明 |
|------|------|
| [env.example](env.example) | ⭐ 环境变量模板 |
| `.env` | 实际环境变量（部署时创建） |

---

## 📂 目录结构

```
新华项目/
├── 📄 部署文档
│   ├── DEPLOYMENT_README.md              ⭐ 部署总结（推荐起点）
│   ├── PRODUCTION_DEPLOYMENT.md          完整部署指南
│   ├── DEPLOYMENT_QUICK_REFERENCE.md     快速参考手册
│   ├── DEPLOYMENT_CHECKLIST.md           部署检查清单
│   └── DEPLOYMENT_INDEX.md               本文档
│
├── 🔧 部署脚本
│   ├── quick-deploy.sh                   ⭐ 一键部署
│   ├── deploy.sh                         标准部署
│   ├── update.sh                         更新脚本
│   ├── backup.sh                         备份脚本
│   └── health_check.sh                   健康检查
│
├── ⚙️ 配置文件
│   ├── docker-compose.yml                开发环境
│   ├── docker-compose.production.yml     ⭐ 生产环境
│   ├── env.example                       环境变量模板
│   └── deploy/                           部署配置
│       ├── nginx/                        Nginx 配置
│       └── systemd/                      Systemd 服务
│
├── 🔨 项目代码
│   ├── backend/                          后端服务
│   ├── frontend/                         前端服务
│   └── workflow-ctl/                     工作流控制
│
├── 📚 其他文档
│   ├── README.md                         项目说明
│   ├── docs/                             详细文档
│   └── CHANGES_SUMMARY.md                变更记录
│
└── 📊 运行时目录
    ├── logs/                             日志目录
    │   ├── backend/
    │   └── workflow-ctl/
    └── workflow-ctl/data/                数据目录
```

---

## 🎓 使用指南

### 场景 1: 首次部署

1. ✅ 阅读 [DEPLOYMENT_README.md](DEPLOYMENT_README.md)
2. ✅ 准备服务器和数据库
3. ✅ 运行 `./quick-deploy.sh`
4. ✅ 使用 [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) 验证

### 场景 2: 手动部署（需要自定义）

1. ✅ 阅读 [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)
2. ✅ 选择部署方式（Docker / 传统）
3. ✅ 按步骤执行
4. ✅ 配置 SSL/HTTPS
5. ✅ 设置备份和监控

### 场景 3: 日常运维

1. ✅ 参考 [DEPLOYMENT_QUICK_REFERENCE.md](DEPLOYMENT_QUICK_REFERENCE.md)
2. ✅ 使用运维脚本
   - 更新: `./update.sh`
   - 备份: `./backup.sh full`
   - 检查: `./health_check.sh`

### 场景 4: 故障排查

1. ✅ 查看 [DEPLOYMENT_QUICK_REFERENCE.md](DEPLOYMENT_QUICK_REFERENCE.md#故障排除)
2. ✅ 检查日志
3. ✅ 运行健康检查
4. ✅ 参考完整部署指南

### 场景 5: 更新服务

1. ✅ 执行备份: `./backup.sh full`
2. ✅ 运行更新: `./update.sh`
3. ✅ 验证服务: `./health_check.sh`

---

## 🔗 快速链接

### 命令速查

```bash
# 部署
./quick-deploy.sh                    # 一键部署
./deploy.sh docker                   # Docker 部署
./deploy.sh systemd                  # Systemd 部署

# 维护
docker-compose up -d                 # 启动服务
docker-compose down                  # 停止服务
docker-compose restart               # 重启服务
docker-compose logs -f               # 查看日志

# 更新
./update.sh                          # 更新服务
./update.sh --force                  # 强制更新

# 备份
./backup.sh full                     # 完整备份
./backup.sh quick                    # 快速备份
./backup.sh restore <file>           # 恢复备份
./backup.sh list                     # 列出备份

# 监控
./health_check.sh                    # 健康检查
docker stats                         # 资源监控
df -h                                # 磁盘空间
free -h                              # 内存使用
```

### 关键端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Frontend | 80 | HTTP |
| Frontend | 443 | HTTPS（可选） |
| Backend | 8888 | API（内部） |
| Workflow-ctl | 8889 | API（内部） |
| MySQL | 3306 | 数据库（如需要） |

### 重要路径

| 路径 | 说明 |
|------|------|
| `/opt/xinhua/` | 项目根目录 |
| `/opt/xinhua/.env` | 环境变量配置 |
| `/opt/xinhua/logs/` | 日志目录 |
| `/backup/xinhua/` | 备份目录 |
| `/var/www/xinhua/` | 前端静态文件（传统部署） |
| `/etc/nginx/sites-available/` | Nginx 配置 |

---

## 🎯 最佳实践

### 部署前

- ✅ 阅读 [DEPLOYMENT_README.md](DEPLOYMENT_README.md)
- ✅ 准备好数据库和服务器
- ✅ 使用 [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)

### 部署中

- ✅ 使用 `./quick-deploy.sh` 快速部署
- ✅ 或参考 [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) 手动部署
- ✅ 逐项检查部署结果

### 部署后

- ✅ 配置 SSL/HTTPS
- ✅ 设置自动备份
- ✅ 配置健康检查
- ✅ 测试所有功能
- ✅ 培训运维团队

### 日常运维

- ✅ 定期备份: `./backup.sh full`
- ✅ 监控服务: `./health_check.sh`
- ✅ 查看日志: `docker-compose logs -f`
- ✅ 定期更新: `./update.sh`

---

## 📞 获取帮助

### 文档

- **部署总结**: [DEPLOYMENT_README.md](DEPLOYMENT_README.md)
- **完整指南**: [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)
- **快速参考**: [DEPLOYMENT_QUICK_REFERENCE.md](DEPLOYMENT_QUICK_REFERENCE.md)
- **API 文档**: [docs/API.md](docs/API.md)

### 支持渠道

- 📧 Email: support@your-domain.com
- 📚 文档: https://docs.your-domain.com
- 🐛 Issues: https://github.com/your-repo/issues

---

## 🔄 文档更新

所有部署文档都会持续更新，请关注：

- **最后更新**: 2025-12-09
- **文档版本**: v1.0.0
- **项目版本**: 根据实际项目版本

如发现文档问题，请提交 Issue 或联系技术支持。

---

## ⭐ 推荐阅读顺序

### 首次部署人员

1. [DEPLOYMENT_README.md](DEPLOYMENT_README.md) - 了解整体方案
2. [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - 准备部署
3. `./quick-deploy.sh` - 执行部署
4. [DEPLOYMENT_QUICK_REFERENCE.md](DEPLOYMENT_QUICK_REFERENCE.md) - 日常参考

### 经验丰富的运维人员

1. [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) - 详细部署方案
2. 选择部署方式并执行
3. [DEPLOYMENT_QUICK_REFERENCE.md](DEPLOYMENT_QUICK_REFERENCE.md) - 运维参考

### 开发人员

1. [README.md](README.md) - 项目概览
2. [docs/API.md](docs/API.md) - API 文档
3. [DEPLOYMENT_README.md](DEPLOYMENT_README.md) - 了解部署

---

**祝你部署顺利！🎉**

有问题？查看相应文档或联系技术支持。

---

**最后更新**: 2025-12-09  
**维护者**: Xuanfeng Tech Team

