# 数据库迁移部署指南

本指南介绍如何在部署 Xinhua Tool 时迁移现有数据库数据。

## 目录

- [快速开始](#快速开始)
- [详细步骤](#详细步骤)
- [常见场景](#常见场景)
- [故障排查](#故障排查)
- [回滚操作](#回滚操作)

## 快速开始

### 完整的数据库迁移部署流程

```bash
# 1. 在源服务器上导出数据库
./db_migration.sh export

# 2. 传输到目标服务器
scp xinhua_db_*.tar.gz user@target-server:/path/to/xinhua-tool/

# 3. 在目标服务器上部署并导入数据库
./deploy.sh docker --with-db xinhua_db_*.tar.gz
```

## 详细步骤

### 步骤 1: 导出现有数据库

在**源服务器**或**开发环境**上：

```bash
# 确保脚本有执行权限
chmod +x db_migration.sh

# 导出数据库
./db_migration.sh export
```

这将创建：
- `xinhua_db_YYYYMMDD_HHMMSS.tar.gz` - 数据库打包文件
- `db_deploy_instructions.txt` - 部署说明文件
- `db_export/` - 临时导出目录

导出内容包括：
- ✅ Backend SQLite 数据库 (`backend/app.db`)
- ✅ Workflow-ctl SQLite 数据库 (`workflow-ctl/data/workflow.db`)
- ✅ 导出信息文件

### 步骤 2: 传输数据库包

将数据库包传输到目标服务器：

**方法 1: 使用 SCP**
```bash
scp xinhua_db_*.tar.gz user@target-server:/path/to/xinhua-tool/
```

**方法 2: 使用 rsync**
```bash
rsync -avz xinhua_db_*.tar.gz user@target-server:/path/to/xinhua-tool/
```

**方法 3: 使用 FTP/SFTP**
```bash
# 使用你喜欢的 FTP 客户端上传
```

### 步骤 3: 在目标服务器部署

在**目标服务器**上：

#### Docker 部署（推荐）

```bash
# 部署并自动导入数据库
./deploy.sh docker --with-db xinhua_db_YYYYMMDD_HHMMSS.tar.gz
```

#### Systemd 部署

```bash
# 部署并自动导入数据库（需要 root 权限）
sudo ./deploy.sh systemd --with-db xinhua_db_YYYYMMDD_HHMMSS.tar.gz
```

#### 手动导入数据库

如果想单独导入数据库：

```bash
# 1. 导入数据库
./db_migration.sh import xinhua_db_YYYYMMDD_HHMMSS.tar.gz

# 2. 然后正常部署
./deploy.sh docker
```

## 常见场景

### 场景 1: 开发环境到生产环境

```bash
# === 在开发环境 ===
./db_migration.sh export
scp xinhua_db_*.tar.gz user@production:/opt/xinhua-tool/

# === 在生产环境 ===
cd /opt/xinhua-tool
./deploy.sh docker --with-db xinhua_db_*.tar.gz
```

### 场景 2: 只迁移部分数据库

如果只需要迁移某个数据库，可以手动编辑导出的包：

```bash
# 1. 导出数据库
./db_migration.sh export

# 2. 解压
mkdir temp && tar xzf xinhua_db_*.tar.gz -C temp/

# 3. 删除不需要的数据库文件
cd temp
rm backend_app.db  # 只保留 workflow.db

# 4. 重新打包
tar czf ../xinhua_db_custom.tar.gz *
cd .. && rm -rf temp

# 5. 部署
./deploy.sh docker --with-db xinhua_db_custom.tar.gz
```

### 场景 3: 定期备份自动化

设置 cron 定时任务自动备份数据库：

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每天凌晨 2 点备份）
0 2 * * * cd /opt/xinhua-tool && ./db_migration.sh export && ./backup.sh quick
```

### 场景 4: 服务器迁移

完整的服务器迁移流程：

```bash
# === 在旧服务器 ===
# 1. 导出数据库
./db_migration.sh export

# 2. 打包整个项目（可选）
tar czf xinhua-full-backup.tar.gz \
    xinhua_db_*.tar.gz \
    .env \
    docker-compose.yml \
    logs/

# 3. 传输到新服务器
scp xinhua-full-backup.tar.gz user@new-server:/opt/

# === 在新服务器 ===
# 1. 解压项目
cd /opt
tar xzf xinhua-full-backup.tar.gz

# 2. 克隆代码库（或复制代码）
git clone <repository-url> xinhua-tool
cd xinhua-tool

# 3. 部署并导入数据库
./deploy.sh docker --with-db ../xinhua_db_*.tar.gz
```

## 数据库验证

导入数据库后，建议进行验证：

```bash
# 验证数据库完整性
./db_migration.sh verify
```

验证内容包括：
- 数据库文件是否存在
- SQLite 数据库完整性检查
- 文件大小和权限

## 回滚操作

如果导入后发现问题，可以回滚到之前的数据：

```bash
# 1. 查看备份目录
ls -la db_backup_before_import_*/

# 2. 回滚到指定备份
./db_migration.sh rollback db_backup_before_import_YYYYMMDD_HHMMSS

# 3. 重启服务
docker-compose restart
# 或
sudo systemctl restart xinhua-backend xinhua-workflow-ctl
```

## 故障排查

### 问题 1: 数据库文件不存在

**错误信息:**
```
⚠️  Backend 数据库不存在，将在启动时初始化
```

**解决方法:**
- 这是正常的，如果是全新部署，数据库会自动初始化
- 如果需要导入数据，确保先运行 `db_migration.sh export`

### 问题 2: 权限问题

**错误信息:**
```
Permission denied
```

**解决方法:**
```bash
# 1. 给脚本添加执行权限
chmod +x db_migration.sh deploy.sh

# 2. 检查数据库文件权限
chmod 644 backend/app.db
chmod 644 workflow-ctl/data/workflow.db

# 3. 如果是 Docker，确保目录权限正确
chmod 755 backend workflow-ctl/data
```

### 问题 3: 数据库损坏

**错误信息:**
```
❌ Backend 数据库损坏
```

**解决方法:**
```bash
# 1. 尝试修复 SQLite 数据库
sqlite3 backend/app.db "PRAGMA integrity_check;"

# 2. 如果无法修复，使用备份恢复
./db_migration.sh rollback <backup_dir>

# 3. 或者从最新的备份导入
./db_migration.sh import <latest_backup.tar.gz>
```

### 问题 4: Docker 卷挂载问题

**错误信息:**
```
Error response from daemon: invalid mount config
```

**解决方法:**
```bash
# 1. 停止所有容器
docker-compose down

# 2. 清理卷
docker volume prune

# 3. 确保数据库文件存在
mkdir -p backend workflow-ctl/data
touch backend/app.db workflow-ctl/data/workflow.db

# 4. 重新部署
./deploy.sh docker
```

## 高级选项

### 自定义导出目录

修改 `db_migration.sh` 中的 `EXPORT_DIR` 变量：

```bash
# 编辑脚本
vim db_migration.sh

# 修改这行
EXPORT_DIR="/custom/backup/path"
```

### 压缩级别调整

如果数据库很大，可以调整压缩级别：

```bash
# 在 export_databases 函数中修改 tar 命令
# 使用最大压缩（慢但文件小）
tar czf9 "$ARCHIVE_NAME" -C "$EXPORT_DIR" .

# 使用最小压缩（快但文件大）
tar czf1 "$ARCHIVE_NAME" -C "$EXPORT_DIR" .
```

### 远程自动部署

结合 SSH 自动化部署：

```bash
#!/bin/bash
# auto_deploy.sh

# 1. 导出数据库
./db_migration.sh export

# 2. 获取最新的数据库包
DB_FILE=$(ls -t xinhua_db_*.tar.gz | head -1)

# 3. 传输到远程服务器并部署
ssh user@remote-server << EOF
    cd /opt/xinhua-tool
    # 接收文件
EOF

scp $DB_FILE user@remote-server:/opt/xinhua-tool/

ssh user@remote-server << EOF
    cd /opt/xinhua-tool
    # 部署
    ./deploy.sh docker --with-db $DB_FILE
EOF
```

## 安全建议

1. **加密传输**: 始终使用 SSH/SCP 传输数据库文件
2. **备份验证**: 定期验证备份的完整性
3. **访问控制**: 限制数据库文件的访问权限
4. **定期备份**: 建议每天自动备份一次
5. **异地备份**: 将备份存储到不同的服务器或云存储

## 性能优化

### 大型数据库

如果数据库很大（>1GB），建议：

1. 使用增量备份
2. 压缩后传输
3. 在低峰期进行迁移
4. 使用更快的网络连接

### 最小化停机时间

```bash
# 1. 提前准备好数据库包
./db_migration.sh export

# 2. 传输到目标服务器
scp xinhua_db_*.tar.gz user@target:/opt/xinhua-tool/

# 3. 在目标服务器上预先导入数据库（不重启）
./db_migration.sh import xinhua_db_*.tar.gz

# 4. 快速重启服务
docker-compose restart
```

## 相关文档

- [部署指南](DEPLOYMENT_GUIDE.md)
- [备份恢复指南](backup.sh)
- [Docker Compose 配置](docker-compose.yml)
- [API 文档](docs/API.md)

## 支持

如有问题，请：
1. 查看日志: `docker-compose logs -f`
2. 验证数据库: `./db_migration.sh verify`
3. 查看备份: `ls -la db_backup_*`

---

**最后更新时间:** 2024-12-09

