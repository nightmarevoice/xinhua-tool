# 数据库迁移功能总结

## 📋 新增文件清单

本次更新为项目添加了完整的数据库迁移功能。以下是新增和修改的文件：

### 新增文件

1. **`db_migration.sh`** - 核心数据库迁移脚本
   - 导出数据库到压缩包
   - 从压缩包导入数据库
   - 数据库回滚功能
   - 数据库完整性验证

2. **`export_and_deploy.sh`** - 一键远程部署脚本
   - 自动导出本地数据库
   - 传输文件到远程服务器
   - 远程自动部署
   - 部署后验证

3. **`DATABASE_MIGRATION_GUIDE.md`** - 完整迁移指南
   - 详细步骤说明
   - 常见场景示例
   - 故障排查方案
   - 回滚操作指南

4. **`DB_MIGRATION_QUICK_REFERENCE.md`** - 快速参考文档
   - 命令速查表
   - 典型工作流程
   - 常见问题解决
   - 最佳实践建议

5. **`DB_MIGRATION_EXAMPLES.md`** - 实战示例文档
   - 8 个典型使用场景
   - CI/CD 集成示例
   - 数据脱敏方案
   - Docker Swarm 部署

6. **`DATABASE_MIGRATION_SUMMARY.md`** - 本文档
   - 功能总览
   - 使用说明
   - 快速开始指南

### 修改文件

1. **`deploy.sh`** - 部署脚本
   - ✅ 添加 `--with-db` 参数支持数据库导入
   - ✅ 自动创建数据库目录
   - ✅ 数据库文件检查和初始化
   - ✅ 增强错误处理

2. **`quick-deploy.sh`** - 快速部署脚本
   - ✅ 添加交互式数据库导入功能
   - ✅ 自动检测数据库备份文件
   - ✅ 改进备份脚本集成
   - ✅ 更新部署信息显示

3. **`backup.sh`** - 备份脚本（已存在）
   - ✅ 已包含 SQLite 数据库备份功能
   - ✅ 支持完整备份和快速备份
   - ✅ 自动清理旧备份

4. **`README.md`** - 主文档
   - ✅ 添加数据库迁移章节
   - ✅ 更新文档链接
   - ✅ 添加快速示例

## 🚀 功能特性

### 核心功能

1. **数据库导出**
   - SQLite 数据库完整导出
   - 自动压缩打包
   - 包含导出信息和校验

2. **数据库导入**
   - 导入前自动备份现有数据
   - 支持部分数据恢复
   - 完整性验证

3. **自动化部署**
   - 一键导出并远程部署
   - SSH 密钥和密码认证支持
   - 部署后自动验证

4. **回滚机制**
   - 导入前自动备份
   - 快速回滚到任意备份点
   - 备份版本管理

5. **数据验证**
   - SQLite 完整性检查
   - 文件大小和权限验证
   - 服务健康检查

### 支持的部署方式

- ✅ Docker Compose 部署
- ✅ Systemd 服务部署
- ✅ 本地开发环境
- ✅ 远程服务器部署
- ✅ CI/CD 自动化部署
- ✅ Docker Swarm 集群

## 📖 快速开始

### 场景 1: 本地导出数据库

```bash
# Linux/Mac
./db_migration.sh export

# Windows
bash db_migration.sh export

# 输出: xinhua_db_YYYYMMDD_HHMMSS.tar.gz
```

### 场景 2: 部署并导入数据库

```bash
# Docker 部署
./deploy.sh docker --with-db xinhua_db_20241209_143022.tar.gz

# Systemd 部署
sudo ./deploy.sh systemd --with-db xinhua_db_20241209_143022.tar.gz
```

### 场景 3: 远程自动部署

```bash
# 基本用法
./export_and_deploy.sh 192.168.1.100

# 完整参数
./export_and_deploy.sh 192.168.1.100 ubuntu /opt/xinhua-tool docker
```

### 场景 4: 验证和回滚

```bash
# 验证数据库
./db_migration.sh verify

# 查看备份
ls -la db_backup_before_import_*/

# 回滚
./db_migration.sh rollback db_backup_before_import_20241209_143022
```

## 📂 目录结构

数据库迁移相关的文件和目录：

```
xinhua-tool/
├── db_migration.sh                    # 数据库迁移主脚本
├── export_and_deploy.sh               # 一键远程部署脚本
├── deploy.sh                          # 部署脚本（已增强）
├── quick-deploy.sh                    # 快速部署脚本（已增强）
├── backup.sh                          # 备份脚本
├── DATABASE_MIGRATION_GUIDE.md        # 完整迁移指南
├── DB_MIGRATION_QUICK_REFERENCE.md    # 快速参考
├── DB_MIGRATION_EXAMPLES.md           # 实战示例
├── DATABASE_MIGRATION_SUMMARY.md      # 本文档
├── backend/
│   └── app.db                         # Backend SQLite 数据库
├── workflow-ctl/
│   └── data/
│       └── workflow.db                # Workflow-ctl SQLite 数据库
├── db_export/                         # 导出临时目录（自动创建）
├── db_backup_before_import_*/         # 导入前备份（自动创建）
├── xinhua_db_*.tar.gz                 # 数据库压缩包
└── db_deploy_instructions.txt         # 部署说明（自动生成）
```

## 🔧 命令参考

### db_migration.sh 命令

```bash
# 导出数据库
./db_migration.sh export

# 导入数据库
./db_migration.sh import <archive_file>

# 回滚数据库
./db_migration.sh rollback <backup_dir>

# 验证数据库
./db_migration.sh verify

# 查看帮助
./db_migration.sh help
```

### deploy.sh 命令

```bash
# Docker 部署（不导入数据库）
./deploy.sh docker

# Docker 部署并导入数据库
./deploy.sh docker --with-db <db_archive>

# Systemd 部署
sudo ./deploy.sh systemd

# Systemd 部署并导入数据库
sudo ./deploy.sh systemd --with-db <db_archive>
```

### export_and_deploy.sh 命令

```bash
# 基本用法
./export_and_deploy.sh <remote_host>

# 指定用户
./export_and_deploy.sh <remote_host> <user>

# 指定路径
./export_and_deploy.sh <remote_host> <user> <path>

# 指定部署方式
./export_and_deploy.sh <remote_host> <user> <path> <docker|systemd>

# 查看帮助
./export_and_deploy.sh help
```

## 💡 使用建议

### 日常开发

1. **本地测试**: 使用 `./deploy.sh docker` 快速部署
2. **数据导出**: 定期导出开发数据备份
3. **快速切换**: 使用不同的数据库包测试不同场景

### 生产部署

1. **自动备份**: 设置 cron 定时任务每天备份
2. **版本管理**: 保留至少 7 天的数据库备份
3. **测试验证**: 在测试环境先验证后再部署生产
4. **灰度发布**: 使用蓝绿部署或金丝雀发布

### 数据迁移

1. **提前准备**: 在非业务高峰期进行数据迁移
2. **完整备份**: 迁移前做好完整备份
3. **验证测试**: 导入后进行完整性验证
4. **回滚准备**: 确保有可用的回滚方案

## 🔒 安全建议

1. **传输加密**: 使用 SSH/SCP 传输数据库文件
2. **访问控制**: 限制数据库文件权限（644 或 600）
3. **密钥管理**: 使用 SSH 密钥认证替代密码
4. **敏感数据**: 开发环境使用脱敏数据
5. **审计日志**: 记录所有数据库操作

## 📊 性能优化

### 数据库优化

```bash
# 压缩 SQLite 数据库
sqlite3 backend/app.db "VACUUM;"
sqlite3 workflow-ctl/data/workflow.db "VACUUM;"

# 重建索引
sqlite3 backend/app.db "REINDEX;"
```

### 传输优化

```bash
# 使用压缩传输
rsync -avz --compress-level=9 xinhua_db_*.tar.gz user@remote:/path/

# 使用增量传输
rsync -avz --partial --progress xinhua_db_*.tar.gz user@remote:/path/
```

## 🐛 故障排查

### 常见问题

1. **权限问题**
   ```bash
   chmod +x *.sh
   chmod 644 backend/app.db workflow-ctl/data/workflow.db
   ```

2. **数据库损坏**
   ```bash
   ./db_migration.sh verify
   ./db_migration.sh rollback <backup_dir>
   ```

3. **SSH 连接失败**
   ```bash
   ssh-keygen -t rsa -b 4096
   ssh-copy-id user@remote-host
   ```

4. **Docker 卷挂载问题**
   ```bash
   docker-compose down
   docker volume prune
   ./deploy.sh docker
   ```

### 日志查看

```bash
# Docker 日志
docker-compose logs -f backend
docker-compose logs -f workflow-ctl

# Systemd 日志
journalctl -u xinhua-backend -f
journalctl -u xinhua-workflow-ctl -f
```

## 📚 文档索引

### 核心文档

- [DATABASE_MIGRATION_GUIDE.md](DATABASE_MIGRATION_GUIDE.md) - 完整迁移指南
- [DB_MIGRATION_QUICK_REFERENCE.md](DB_MIGRATION_QUICK_REFERENCE.md) - 快速参考
- [DB_MIGRATION_EXAMPLES.md](DB_MIGRATION_EXAMPLES.md) - 实战示例

### 部署文档

- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - 通用部署指南
- [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) - 生产环境部署
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - 部署检查清单

### API 文档

- [docs/API.md](docs/API.md) - API 接口文档

## 🎯 下一步

1. **测试环境验证**
   - 在测试环境测试所有迁移功能
   - 验证回滚机制
   - 性能测试

2. **生产环境准备**
   - 配置自动备份任务
   - 设置监控告警
   - 准备应急预案

3. **团队培训**
   - 分享数据库迁移最佳实践
   - 演示常用操作
   - 建立操作规范

## ✅ 功能检查清单

- [x] 数据库导出功能
- [x] 数据库导入功能
- [x] 自动备份机制
- [x] 回滚功能
- [x] 完整性验证
- [x] 远程部署支持
- [x] Docker 集成
- [x] Systemd 集成
- [x] 错误处理
- [x] 日志记录
- [x] 文档完善
- [x] 使用示例

## 🙏 反馈与支持

如有问题或建议，请：

1. 查看相关文档
2. 检查日志输出
3. 验证配置正确性
4. 联系技术支持

---

**版本**: 1.0.0  
**更新日期**: 2024-12-09  
**作者**: Xinhua Tool Team

