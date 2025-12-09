# 🎯 新华项目部署检查清单

使用本清单确保部署过程顺利完成。

---

## 📋 部署前检查

### 服务器环境

- [ ] 服务器已准备好（推荐配置: 4GB+ 内存, 40GB+ 硬盘）
- [ ] 操作系统: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- [ ] 具有 root 或 sudo 权限
- [ ] 服务器可以访问互联网
- [ ] SSH 访问已配置

### 网络配置

- [ ] 开放端口 80 (HTTP)
- [ ] 开放端口 443 (HTTPS, 如果使用)
- [ ] 开放端口 22 (SSH)
- [ ] 防火墙规则已配置
- [ ] 域名已解析到服务器 IP（如果使用）

### 数据库准备

- [ ] MySQL 数据库已创建
- [ ] 数据库用户已创建
- [ ] 数据库权限已授予
- [ ] 数据库连接已测试
- [ ] 数据库连接信息已记录：
  ```
  主机: ___________________
  端口: ___________________
  数据库名: ______________
  用户名: ________________
  密码: __________________
  ```

---

## 🚀 部署步骤

### 1. 上传项目文件

- [ ] 项目文件已上传到服务器 `/opt/xinhua`
- [ ] 或通过 Git 克隆: `git clone <repo> /opt/xinhua`
- [ ] 切换到项目目录: `cd /opt/xinhua`

### 2. 配置环境变量

- [ ] 复制环境变量模板: `cp env.example .env`
- [ ] 编辑 `.env` 文件: `nano .env`
- [ ] 配置数据库连接信息
- [ ] 生成 SECRET_KEY: `openssl rand -hex 32`
- [ ] 设置 ALLOWED_ORIGINS（域名）
- [ ] 保存并关闭编辑器

### 3. 选择部署方式

选择以下一种方式：

#### 方式 A: 一键部署（推荐新手）

- [ ] 给脚本添加执行权限: `chmod +x quick-deploy.sh`
- [ ] 运行部署脚本: `./quick-deploy.sh`
- [ ] 按照提示输入配置信息
- [ ] 等待部署完成（约 10-15 分钟）

#### 方式 B: Docker Compose 手动部署

- [ ] 安装 Docker: `curl -fsSL https://get.docker.com | sh`
- [ ] 安装 Docker Compose
- [ ] 创建目录: `mkdir -p logs/{backend,workflow-ctl} workflow-ctl/data`
- [ ] 构建镜像: `docker-compose build`
- [ ] 启动服务: `docker-compose up -d`
- [ ] 初始化后端数据库: `docker-compose exec backend python init_db.py`
- [ ] 初始化 workflow-ctl 数据库: `docker-compose exec workflow-ctl python init_db.py`

#### 方式 C: 传统部署

- [ ] 安装 Python 3.9+
- [ ] 安装 Node.js 18+
- [ ] 安装 Nginx
- [ ] 部署后端服务（见完整指南）
- [ ] 部署 workflow-ctl 服务（见完整指南）
- [ ] 部署前端（见完整指南）
- [ ] 配置 Nginx（见完整指南）

---

## ✅ 部署后验证

### 服务状态检查

- [ ] 后端服务健康检查: `curl http://localhost:8888/health`
  - 预期响应: `{"status":"healthy"}`
  
- [ ] Workflow-ctl 服务健康检查: `curl http://localhost:8889/health`
  - 预期响应: `{"status":"healthy"}`
  
- [ ] 前端访问检查: `curl http://localhost/`
  - 预期响应: HTML 内容

- [ ] Docker 容器状态（如果使用 Docker）: `docker-compose ps`
  - 所有服务状态应为 "Up"

### 功能测试

- [ ] 浏览器访问前端: `http://your-server-ip`
- [ ] 前端页面正常加载
- [ ] 可以访问登录页面
- [ ] API 接口响应正常
- [ ] 数据库连接正常

### 日志检查

- [ ] 查看后端日志: `docker-compose logs backend` 或 `tail -f logs/backend/*.log`
- [ ] 查看 workflow-ctl 日志: `docker-compose logs workflow-ctl`
- [ ] 查看前端/Nginx 日志: `docker-compose logs frontend`
- [ ] 确认没有错误信息

---

## 🔒 安全配置

### 防火墙

- [ ] 启用防火墙: `sudo ufw enable`
- [ ] 允许 SSH: `sudo ufw allow 22`
- [ ] 允许 HTTP: `sudo ufw allow 80`
- [ ] 允许 HTTPS: `sudo ufw allow 443`
- [ ] 禁止直接访问后端端口: `sudo ufw deny 8888`
- [ ] 禁止直接访问 workflow-ctl 端口: `sudo ufw deny 8889`
- [ ] 查看防火墙状态: `sudo ufw status`

### SSH 安全

- [ ] 禁用 root 登录
- [ ] 禁用密码登录（只用密钥）
- [ ] 更改 SSH 默认端口（可选）

### SSL/HTTPS（推荐）

- [ ] 安装 Certbot: `sudo apt install certbot python3-certbot-nginx`
- [ ] 获取证书: `sudo certbot --nginx -d your-domain.com`
- [ ] 测试自动续期: `sudo certbot renew --dry-run`
- [ ] HTTPS 访问测试: `https://your-domain.com`

---

## ⚙️ 自动化配置

### 开机自启

- [ ] Docker 服务开机自启: `sudo systemctl enable docker`
- [ ] 项目服务开机自启已配置
- [ ] 测试重启: `sudo reboot`
- [ ] 重启后验证服务自动启动

### 自动备份

- [ ] 备份脚本已安装: `ls -l backup.sh`
- [ ] 添加到 crontab: `crontab -e`
  ```
  0 2 * * * /opt/xinhua/backup.sh full
  ```
- [ ] 测试备份: `./backup.sh quick`
- [ ] 确认备份文件: `ls -lh /backup/xinhua/`

### 自动健康检查

- [ ] 健康检查脚本已安装: `ls -l health_check.sh`
- [ ] 添加到 crontab: `crontab -e`
  ```
  */5 * * * * /opt/xinhua/health_check.sh
  ```
- [ ] 测试健康检查: `./health_check.sh`
- [ ] 配置告警邮箱（可选）

---

## 📊 监控配置

### 日志管理

- [ ] 日志目录已创建: `/opt/xinhua/logs`
- [ ] 日志轮转已配置
- [ ] 查看日志: `tail -f /opt/xinhua/logs/backend/*.log`

### 性能监控

- [ ] 查看系统资源: `htop` 或 `top`
- [ ] 查看 Docker 资源: `docker stats`
- [ ] 查看磁盘空间: `df -h`
- [ ] 查看内存使用: `free -h`

---

## 📝 文档和记录

### 部署信息记录

```
部署日期: ___________________
服务器 IP: __________________
域名: _______________________
部署方式: __________________
数据库类型: ________________

服务端口:
- 前端: ___________________
- 后端: ___________________
- Workflow-ctl: ___________

备份位置: _________________
SSL 证书到期: _____________
```

### 访问信息

```
前端地址: http(s)://___________________
后端 API: http(s)://___________________/api/
管理员账号: ___________________________
管理员密码: ___________________________（请妥善保管）
```

---

## 🎓 团队培训

### 运维人员需要了解

- [ ] 如何查看服务状态
- [ ] 如何查看日志
- [ ] 如何重启服务
- [ ] 如何执行备份
- [ ] 如何恢复备份
- [ ] 紧急联系方式

### 开发人员需要了解

- [ ] 如何更新代码: `./update.sh`
- [ ] 如何查看日志
- [ ] API 文档位置
- [ ] 开发环境配置

---

## 📞 后续支持

### 资源

- [ ] 完整部署指南已保存: `PRODUCTION_DEPLOYMENT.md`
- [ ] 快速参考已保存: `DEPLOYMENT_QUICK_REFERENCE.md`
- [ ] API 文档已查看: `docs/API.md`

### 联系方式

- [ ] 技术支持邮箱已记录: ___________________
- [ ] 应急联系人已记录: ___________________
- [ ] 文档网站已保存: ___________________

---

## ✨ 可选优化

### 性能优化

- [ ] 数据库索引优化
- [ ] Nginx 缓存配置
- [ ] CDN 配置（如果需要）
- [ ] 负载均衡（如果需要）

### 高可用性

- [ ] 数据库主从复制
- [ ] 服务多实例部署
- [ ] 自动故障转移
- [ ] 异地备份

### 监控告警

- [ ] 部署 Prometheus + Grafana
- [ ] 配置 Slack/钉钉告警
- [ ] 设置关键指标监控
- [ ] 配置日志聚合（ELK Stack）

---

## 🎉 部署完成

恭喜！如果以上所有项目都已勾选，说明部署已成功完成。

### 最后检查

- [ ] 所有服务正常运行
- [ ] 可以通过浏览器访问
- [ ] 备份和监控已配置
- [ ] 文档已归档
- [ ] 团队已培训

### 下一步

1. 开始使用系统
2. 定期检查备份
3. 关注健康检查告警
4. 定期更新系统
5. 优化性能配置

---

**部署日期**: ___________________  
**部署人员**: ___________________  
**审核人员**: ___________________

---

如有问题，请参考：
- 完整部署指南: `PRODUCTION_DEPLOYMENT.md`
- 故障排除: `DEPLOYMENT_QUICK_REFERENCE.md`
- 技术支持: support@your-domain.com

