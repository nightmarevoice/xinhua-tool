# 数据库迁移快速参考

## 🚀 快速开始

### 场景 1: 本地导出数据库

```bash
# 导出数据库
./db_migration.sh export

# 输出文件: xinhua_db_YYYYMMDD_HHMMSS.tar.gz
```

### 场景 2: 本地部署并导入数据库

```bash
# 部署并导入数据库
./deploy.sh docker --with-db xinhua_db_20241209_143022.tar.gz
```

### 场景 3: 远程自动部署（推荐）

```bash
# 一键导出并远程部署
./export_and_deploy.sh 192.168.1.100

# 或指定详细参数
./export_and_deploy.sh 192.168.1.100 ubuntu /opt/xinhua-tool docker
```

## 📋 命令速查表

### db_migration.sh

| 命令 | 说明 | 示例 |
|------|------|------|
| `export` | 导出数据库到压缩包 | `./db_migration.sh export` |
| `import <file>` | 从压缩包导入数据库 | `./db_migration.sh import xinhua_db_*.tar.gz` |
| `rollback <dir>` | 回滚到指定备份 | `./db_migration.sh rollback db_backup_*` |
| `verify` | 验证数据库完整性 | `./db_migration.sh verify` |

### deploy.sh

| 命令 | 说明 | 示例 |
|------|------|------|
| `docker` | Docker 部署 | `./deploy.sh docker` |
| `docker --with-db <file>` | Docker 部署并导入数据库 | `./deploy.sh docker --with-db db.tar.gz` |
| `systemd` | Systemd 部署 | `sudo ./deploy.sh systemd` |
| `systemd --with-db <file>` | Systemd 部署并导入数据库 | `sudo ./deploy.sh systemd --with-db db.tar.gz` |

### export_and_deploy.sh

| 命令 | 说明 | 示例 |
|------|------|------|
| `<host>` | 自动导出并远程部署 | `./export_and_deploy.sh 192.168.1.100` |
| `<host> <user>` | 指定用户 | `./export_and_deploy.sh 192.168.1.100 ubuntu` |
| `<host> <user> <path>` | 指定路径 | `./export_and_deploy.sh 192.168.1.100 ubuntu /opt/app` |

### backup.sh

| 命令 | 说明 | 示例 |
|------|------|------|
| `quick` | 快速备份（数据库+配置） | `./backup.sh quick` |
| `full` | 完整备份（包括日志） | `./backup.sh full` |
| `restore <file>` | 恢复备份 | `./backup.sh restore backup.sql.gz` |
| `list` | 列出所有备份 | `./backup.sh list` |

## 📂 数据库文件位置

```
xinhua-tool/
├── backend/
│   └── app.db                    # Backend SQLite 数据库
├── workflow-ctl/
│   └── data/
│       └── workflow.db           # Workflow-ctl SQLite 数据库
├── db_export/                    # 导出临时目录
├── db_backup_before_import_*/    # 导入前自动备份
└── xinhua_db_*.tar.gz           # 数据库压缩包
```

## 🔄 典型工作流程

### 开发环境 → 生产环境

```bash
# === 开发环境 ===
# 1. 导出数据库
./db_migration.sh export

# === 生产环境 ===
# 2. 上传数据库包
scp xinhua_db_*.tar.gz user@production:/opt/xinhua-tool/

# 3. 在生产环境部署
ssh user@production
cd /opt/xinhua-tool
./deploy.sh docker --with-db xinhua_db_*.tar.gz
```

### 服务器迁移

```bash
# === 旧服务器 ===
# 1. 导出数据库
./db_migration.sh export

# 2. 传输到新服务器
scp xinhua_db_*.tar.gz user@new-server:/opt/xinhua-tool/

# === 新服务器 ===
# 3. 克隆代码
git clone <repository> xinhua-tool
cd xinhua-tool

# 4. 部署并导入数据库
./deploy.sh docker --with-db /opt/xinhua_db_*.tar.gz
```

### 定期备份

```bash
# 添加 cron 定时任务（每天凌晨 2 点）
crontab -e

# 添加以下行
0 2 * * * cd /opt/xinhua-tool && ./db_migration.sh export && ./backup.sh quick
```

## ⚠️ 重要提示

1. **导入前自动备份**: 导入数据库时会自动备份现有数据到 `db_backup_before_import_*/`
2. **权限问题**: 确保脚本有执行权限 `chmod +x *.sh`
3. **Docker 卷挂载**: Docker 部署时，数据库文件通过卷挂载，修改会立即生效
4. **数据验证**: 导入后建议运行 `./db_migration.sh verify` 验证数据库完整性
5. **回滚操作**: 如果导入后有问题，可以使用 `rollback` 命令快速回滚

## 🛠️ 故障排查

### 问题：权限被拒绝

```bash
chmod +x db_migration.sh deploy.sh export_and_deploy.sh backup.sh
```

### 问题：数据库文件不存在

```bash
# 创建空数据库文件
mkdir -p backend workflow-ctl/data
touch backend/app.db workflow-ctl/data/workflow.db
```

### 问题：Docker 卷挂载失败

```bash
# 停止容器并清理卷
docker-compose down
docker volume prune

# 重新部署
./deploy.sh docker
```

### 问题：SSH 连接失败

```bash
# 配置 SSH 密钥
ssh-copy-id user@remote-host

# 或使用密码登录
./export_and_deploy.sh remote-host
# 按提示输入密码
```

## 📊 数据库大小优化

### 压缩 SQLite 数据库

```bash
# Backend 数据库
sqlite3 backend/app.db "VACUUM;"

# Workflow-ctl 数据库
sqlite3 workflow-ctl/data/workflow.db "VACUUM;"
```

### 清理旧数据

```bash
# 清理 30 天前的日志
find logs -type f -mtime +30 -delete

# 清理旧备份
find /backup/xinhua -type f -mtime +30 -delete
```

## 🔒 安全建议

1. **加密传输**: 使用 SSH/SCP 传输数据库文件
2. **限制访问**: 数据库文件权限设置为 600 或 644
3. **定期备份**: 建议每天自动备份
4. **异地存储**: 将重要备份上传到云存储

## 📚 相关文档

- [完整数据库迁移指南](DATABASE_MIGRATION_GUIDE.md)
- [部署指南](DEPLOYMENT_GUIDE.md)
- [备份恢复指南](backup.sh)

## 💡 最佳实践

1. **部署前验证**: 在测试环境先验证数据库导入
2. **保留多个备份**: 至少保留最近 7 天的备份
3. **记录变更**: 记录每次数据库迁移的时间和原因
4. **监控告警**: 设置数据库大小和备份失败的告警
5. **版本控制**: 重要的数据库结构变更要有迁移脚本

## 🎯 使用示例

### 示例 1: 快速本地导入

```bash
./db_migration.sh export
./db_migration.sh import xinhua_db_20241209_143022.tar.gz
```

### 示例 2: 生产环境部署

```bash
# 在本地导出
./db_migration.sh export

# 传输到生产环境
scp xinhua_db_*.tar.gz prod:/opt/xinhua-tool/

# 在生产环境部署
ssh prod
cd /opt/xinhua-tool
./deploy.sh docker --with-db xinhua_db_*.tar.gz
```

### 示例 3: 自动化部署

```bash
# 创建自动化脚本
cat > auto_deploy.sh << 'EOF'
#!/bin/bash
./db_migration.sh export
DB_FILE=$(ls -t xinhua_db_*.tar.gz | head -1)
scp $DB_FILE prod:/opt/xinhua-tool/
ssh prod "cd /opt/xinhua-tool && ./deploy.sh docker --with-db $DB_FILE"
EOF

chmod +x auto_deploy.sh
./auto_deploy.sh
```

---

**提示**: 所有脚本都支持 `--help` 参数查看详细帮助信息。

```bash
./db_migration.sh --help
./deploy.sh --help
./export_and_deploy.sh --help
./backup.sh --help
```

