# Docker 部署故障排查指南

## 🔧 常见问题及解决方案

### 1. 网络冲突错误

**错误信息:**
```
Error response from daemon: error while removing network: network xinhua-tool_xinhua-network id xxx has active endpoints
```

**原因:** Docker 网络仍有容器端点连接，无法删除

**解决方案:**

#### 方案 A: 使用自动修复脚本（推荐）
```bash
chmod +x fix-docker-network.sh
./fix-docker-network.sh
```

脚本会自动：
- 停止所有项目容器
- 断开网络连接
- 删除旧网络
- 清理悬空资源
- 更新 docker-compose.yml

#### 方案 B: 手动修复
```bash
# 1. 停止所有容器
docker-compose down

# 2. 强制删除项目容器
docker rm -f $(docker ps -a --filter "name=xinhua" -q)

# 3. 查看网络连接
docker network inspect xinhua-tool_xinhua-network

# 4. 断开所有端点（替换 CONTAINER_NAME）
docker network disconnect -f xinhua-tool_xinhua-network CONTAINER_NAME

# 5. 删除网络
docker network rm xinhua-tool_xinhua-network

# 6. 重新部署
./deploy.sh docker
```

---

### 2. version 字段过时警告

**警告信息:**
```
WARN[0000] the attribute `version` is obsolete, it will be ignored
```

**原因:** Docker Compose v2 不再需要 version 字段

**解决方案:**

已自动修复！最新的 `docker-compose.yml` 已移除 `version` 字段。

如果仍有警告，手动删除第一行：
```bash
sed -i '/^version:/d' docker-compose.yml
```

---

### 3. 端口占用

**错误信息:**
```
bind: address already in use
```

**解决方案:**
```bash
# 查看占用端口的进程
netstat -tulpn | grep 8888
netstat -tulpn | grep 8889
netstat -tulpn | grep 8787

# 停止占用端口的进程（替换 PID）
kill -9 PID

# 或停止 Docker 容器
docker stop $(docker ps -q --filter "publish=8888")
```

---

### 4. 镜像构建失败

**解决方案:**
```bash
# 查看详细构建日志
docker-compose build --no-cache --progress=plain

# 清理旧镜像后重建
docker rmi xinhua-tool-frontend xinhua-tool-backend xinhua-tool-workflow-ctl
./deploy.sh docker --no-cache
```

---

### 5. 容器健康检查失败

**症状:** 容器启动后显示 unhealthy

**检查步骤:**
```bash
# 查看容器状态
docker-compose ps

# 查看容器日志
docker-compose logs backend
docker-compose logs workflow-ctl
docker-compose logs frontend

# 进入容器调试
docker exec -it xinhua-backend bash
curl http://localhost:8888/health
```

---

### 6. 数据库连接失败

**检查配置:**
```bash
# 查看环境变量
docker exec xinhua-backend env | grep DB

# 测试数据库连接（MySQL）
docker exec xinhua-backend python -c "
from sqlalchemy import create_engine
import os
engine = create_engine(os.getenv('DATABASE_URL'))
print('Database connected!')
"
```

---

## 🚀 完整清理和重新部署流程

当遇到严重问题需要完全重置时：

```bash
# 1. 停止并删除所有容器
docker-compose down -v

# 2. 清理项目相关资源
docker rm -f $(docker ps -a --filter "name=xinhua" -q) 2>/dev/null || true
docker rmi $(docker images --filter "reference=xinhua-tool-*" -q) 2>/dev/null || true
docker network rm xinhua-tool_xinhua-network 2>/dev/null || true

# 3. 清理 Docker 系统（谨慎使用）
docker system prune -af
docker volume prune -f

# 4. 重新部署
./deploy.sh docker --no-cache
```

---

## 📊 监控和调试命令

### 查看实时日志
```bash
# 所有服务
docker-compose logs -f

# 单个服务
docker-compose logs -f backend
docker-compose logs -f workflow-ctl
docker-compose logs -f frontend
```

### 检查资源使用
```bash
# 容器资源使用
docker stats

# 磁盘使用
docker system df
```

### 网络调试
```bash
# 查看所有网络
docker network ls

# 查看网络详情
docker network inspect xinhua-tool_xinhua-network

# 测试容器间连接
docker exec xinhua-frontend ping backend
docker exec xinhua-backend ping workflow-ctl
```

---

## 🆘 紧急救援

如果所有方法都失败，使用终极清理：

```bash
# ⚠️ 警告：这会删除所有 Docker 资源！
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)
docker rmi $(docker images -q)
docker network prune -f
docker volume prune -f
docker system prune -af --volumes

# 重新部署
./deploy.sh docker --no-cache
```

---

## 📞 获取帮助

1. **查看部署日志**
   ```bash
   docker-compose logs --tail=100
   ```

2. **检查容器状态**
   ```bash
   docker-compose ps
   docker inspect xinhua-backend
   ```

3. **验证配置**
   ```bash
   docker-compose config
   ```

4. **测试服务端点**
   ```bash
   curl http://localhost:8888/health
   curl http://localhost:8889/health
   curl http://localhost:8787
   ```

---

## ✅ 最佳实践

1. **定期清理**
   ```bash
   # 每周清理一次悬空资源
   docker system prune -f
   ```

2. **使用专用网络**
   - 已在 docker-compose.yml 中配置
   - 网络名: `xinhua-tool_xinhua-network`
   - 子网: `172.25.0.0/16`

3. **健康检查**
   - 所有服务都配置了健康检查
   - 启动前等待依赖服务就绪

4. **日志管理**
   - 日志自动轮换
   - 最大大小: 10MB
   - 保留文件: 3 个

5. **数据持久化**
   - 数据库: `./backend/app.db`, `./workflow-ctl/data/`
   - 日志: `./logs/`

---

## 🔗 相关文档

- [DEPLOYMENT.md](DEPLOYMENT.md) - 完整部署指南
- [README.md](README.md) - 项目说明
- [docker-compose.yml](docker-compose.yml) - Docker 配置


