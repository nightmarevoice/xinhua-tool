# 数据库迁移实战示例

本文档提供数据库迁移的实际使用案例和示例。

## 示例 1: 开发环境数据迁移到测试服务器

### 场景说明
将本地开发环境的数据库迁移到测试服务器。

### 步骤

**1. 在本地开发环境导出数据库**

```bash
cd /path/to/xinhua-tool

# 导出数据库
./db_migration.sh export

# 输出示例:
# ✅ Backend 数据库已导出
# ✅ Workflow-ctl 数据库已导出
# ✅ 数据库已打包: xinhua_db_20241209_143022.tar.gz
```

**2. 传输到测试服务器**

```bash
# 使用 SCP 传输
scp xinhua_db_20241209_143022.tar.gz user@test-server:/opt/xinhua-tool/

# 或者使用一键部署脚本（推荐）
./export_and_deploy.sh test-server user /opt/xinhua-tool docker
```

**3. 在测试服务器上部署**

```bash
# SSH 登录测试服务器
ssh user@test-server

# 进入项目目录
cd /opt/xinhua-tool

# 部署并导入数据库
./deploy.sh docker --with-db xinhua_db_20241209_143022.tar.gz
```

**4. 验证部署**

```bash
# 验证数据库完整性
./db_migration.sh verify

# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

---

## 示例 2: 生产环境数据备份和恢复

### 场景说明
生产环境定期备份，并在需要时恢复数据。

### 定期备份设置

**1. 创建备份脚本**

```bash
# 编辑 crontab
crontab -e

# 添加定时任务（每天凌晨 2 点备份）
0 2 * * * cd /opt/xinhua-tool && ./db_migration.sh export && mv xinhua_db_*.tar.gz /backup/xinhua/

# 添加清理任务（每周日清理 30 天前的备份）
0 3 * * 0 find /backup/xinhua -name "xinhua_db_*.tar.gz" -mtime +30 -delete
```

**2. 手动备份**

```bash
# 进入项目目录
cd /opt/xinhua-tool

# 导出数据库
./db_migration.sh export

# 移动到备份目录
mv xinhua_db_*.tar.gz /backup/xinhua/
```

### 数据恢复

**1. 查看可用备份**

```bash
# 列出所有备份
ls -lh /backup/xinhua/xinhua_db_*.tar.gz

# 示例输出:
# -rw-r--r-- 1 user user 15M Dec  9 02:00 xinhua_db_20241209_020000.tar.gz
# -rw-r--r-- 1 user user 14M Dec  8 02:00 xinhua_db_20241208_020000.tar.gz
```

**2. 恢复数据**

```bash
cd /opt/xinhua-tool

# 导入数据库（会自动备份当前数据）
./db_migration.sh import /backup/xinhua/xinhua_db_20241209_020000.tar.gz

# 重启服务
docker-compose restart
```

**3. 验证恢复**

```bash
# 验证数据库
./db_migration.sh verify

# 检查应用日志
docker-compose logs -f backend
docker-compose logs -f workflow-ctl
```

---

## 示例 3: 服务器迁移（完整迁移）

### 场景说明
从旧服务器完整迁移到新服务器。

### 步骤

**1. 在旧服务器上准备数据**

```bash
# 登录旧服务器
ssh user@old-server
cd /opt/xinhua-tool

# 停止服务
docker-compose down

# 导出数据库
./db_migration.sh export

# 打包整个项目（包括配置文件）
tar czf /tmp/xinhua-full-backup.tar.gz \
    xinhua_db_*.tar.gz \
    .env \
    docker-compose.yml \
    logs/

# 查看打包文件大小
ls -lh /tmp/xinhua-full-backup.tar.gz
```

**2. 传输到新服务器**

```bash
# 从旧服务器传输到新服务器
scp /tmp/xinhua-full-backup.tar.gz user@new-server:/tmp/
```

**3. 在新服务器上部署**

```bash
# 登录新服务器
ssh user@new-server

# 安装 Docker（如果未安装）
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 创建项目目录
sudo mkdir -p /opt/xinhua-tool
cd /opt/xinhua-tool

# 解压备份
tar xzf /tmp/xinhua-full-backup.tar.gz

# 克隆代码库
git clone <repository-url> /tmp/xinhua-code
cp -r /tmp/xinhua-code/* .

# 部署并导入数据库
./deploy.sh docker --with-db xinhua_db_*.tar.gz
```

**4. 配置网络和域名**

```bash
# 如果使用 Nginx 反向代理
sudo cp deploy/nginx/xinhua.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/xinhua.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 配置防火墙
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

**5. 验证迁移**

```bash
# 检查服务状态
docker-compose ps

# 检查健康端点
curl http://localhost:8888/health
curl http://localhost:8889/health
curl http://localhost/

# 验证数据库
./db_migration.sh verify
```

---

## 示例 4: 多环境数据同步

### 场景说明
定期将生产环境数据同步到测试环境。

### 自动化脚本

创建 `sync_prod_to_test.sh`:

```bash
#!/bin/bash

# 配置
PROD_SERVER="prod.example.com"
TEST_SERVER="test.example.com"
USER="deploy"
PROJECT_PATH="/opt/xinhua-tool"

echo "=========================================="
echo "生产环境 -> 测试环境数据同步"
echo "=========================================="

# 1. 从生产环境导出数据库
echo "正在从生产环境导出数据库..."
ssh $USER@$PROD_SERVER "cd $PROJECT_PATH && ./db_migration.sh export"

# 2. 获取最新的数据库文件名
DB_FILE=$(ssh $USER@$PROD_SERVER "cd $PROJECT_PATH && ls -t xinhua_db_*.tar.gz | head -1")

# 3. 从生产环境下载到本地
echo "正在下载数据库文件..."
scp $USER@$PROD_SERVER:$PROJECT_PATH/$DB_FILE /tmp/

# 4. 上传到测试环境
echo "正在上传到测试环境..."
scp /tmp/$DB_FILE $USER@$TEST_SERVER:$PROJECT_PATH/

# 5. 在测试环境导入
echo "正在测试环境导入数据库..."
ssh $USER@$TEST_SERVER "cd $PROJECT_PATH && ./db_migration.sh import $DB_FILE && docker-compose restart"

# 6. 清理临时文件
rm /tmp/$DB_FILE

echo "=========================================="
echo "数据同步完成！"
echo "=========================================="
```

使用脚本：

```bash
chmod +x sync_prod_to_test.sh
./sync_prod_to_test.sh
```

---

## 示例 5: 数据脱敏后迁移

### 场景说明
将生产数据脱敏后提供给开发环境使用。

### 步骤

**1. 导出生产数据**

```bash
# 在生产服务器
cd /opt/xinhua-tool
./db_migration.sh export
```

**2. 数据脱敏**

创建脱敏脚本 `desensitize_db.sh`:

```bash
#!/bin/bash

DB_FILE=$1

if [ -z "$DB_FILE" ]; then
    echo "使用方法: $0 <db_file.tar.gz>"
    exit 1
fi

# 解压数据库
mkdir -p /tmp/db_temp
tar xzf $DB_FILE -C /tmp/db_temp

# 脱敏 backend 数据库
if [ -f /tmp/db_temp/backend_app.db ]; then
    echo "正在脱敏 backend 数据库..."
    sqlite3 /tmp/db_temp/backend_app.db << 'EOF'
-- 脱敏用户信息
UPDATE users SET 
    password = 'desensitized_password',
    email = REPLACE(email, '@', '_desensitized@');

-- 脱敏 API Key
UPDATE apikeys SET 
    key = 'test_' || substr(key, 1, 8) || '_desensitized';

-- 删除敏感日志
DELETE FROM logs WHERE level = 'ERROR';
EOF
fi

# 脱敏 workflow-ctl 数据库
if [ -f /tmp/db_temp/workflow.db ]; then
    echo "正在脱敏 workflow-ctl 数据库..."
    sqlite3 /tmp/db_temp/workflow.db << 'EOF'
-- 脱敏敏感配置
UPDATE llm_providers SET 
    api_key = 'test_' || substr(api_key, 1, 8) || '_desensitized';
EOF
fi

# 重新打包
DESENSITIZED_FILE="${DB_FILE%.tar.gz}_desensitized.tar.gz"
cd /tmp/db_temp
tar czf $DESENSITIZED_FILE *
mv $DESENSITIZED_FILE $(dirname $DB_FILE)/

# 清理
rm -rf /tmp/db_temp

echo "脱敏完成: $DESENSITIZED_FILE"
```

**3. 使用脱敏后的数据**

```bash
# 脱敏数据
./desensitize_db.sh xinhua_db_20241209_143022.tar.gz

# 部署到开发环境
./deploy.sh docker --with-db xinhua_db_20241209_143022_desensitized.tar.gz
```

---

## 示例 6: 数据库版本回滚

### 场景说明
部署后发现问题，需要回滚到之前的版本。

### 步骤

**1. 列出可用备份**

```bash
cd /opt/xinhua-tool

# 查看导入前的自动备份
ls -la db_backup_before_import_*/

# 示例输出:
# drwxr-xr-x 2 user user 4096 Dec  9 14:30 db_backup_before_import_20241209_143000
# drwxr-xr-x 2 user user 4096 Dec  8 10:15 db_backup_before_import_20241208_101500
```

**2. 快速回滚**

```bash
# 回滚到最近的备份
./db_migration.sh rollback db_backup_before_import_20241209_143000

# 重启服务
docker-compose restart
```

**3. 验证回滚**

```bash
# 验证数据库
./db_migration.sh verify

# 检查应用
curl http://localhost:8888/health
```

**4. 如果回滚失败，使用备份目录恢复**

```bash
# 手动复制备份文件
cp db_backup_before_import_20241209_143000/backend_app.db backend/app.db
cp db_backup_before_import_20241209_143000/workflow.db workflow-ctl/data/workflow.db

# 重启服务
docker-compose restart
```

---

## 示例 7: CI/CD 自动化部署

### 场景说明
在 CI/CD 流程中自动导出和部署数据库。

### GitLab CI 示例

`.gitlab-ci.yml`:

```yaml
stages:
  - export
  - deploy

variables:
  DEPLOY_SERVER: "production.example.com"
  DEPLOY_USER: "deploy"
  DEPLOY_PATH: "/opt/xinhua-tool"

export_database:
  stage: export
  only:
    - main
  script:
    - chmod +x db_migration.sh
    - ./db_migration.sh export
  artifacts:
    paths:
      - xinhua_db_*.tar.gz
    expire_in: 7 days

deploy_to_production:
  stage: deploy
  only:
    - main
  dependencies:
    - export_database
  before_script:
    - eval $(ssh-agent -s)
    - echo "$SSH_PRIVATE_KEY" | tr -d '\r' | ssh-add -
    - mkdir -p ~/.ssh
    - chmod 700 ~/.ssh
  script:
    - DB_FILE=$(ls -t xinhua_db_*.tar.gz | head -1)
    - scp $DB_FILE $DEPLOY_USER@$DEPLOY_SERVER:$DEPLOY_PATH/
    - ssh $DEPLOY_USER@$DEPLOY_SERVER "cd $DEPLOY_PATH && ./deploy.sh docker --with-db $DB_FILE"
```

### GitHub Actions 示例

`.github/workflows/deploy.yml`:

```yaml
name: Deploy with Database

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Export Database
        run: |
          chmod +x db_migration.sh
          ./db_migration.sh export
      
      - name: Setup SSH
        uses: webfactory/ssh-agent@v0.5.3
        with:
          ssh-private-key: ${{ secrets.SSH_PRIVATE_KEY }}
      
      - name: Deploy to Server
        run: |
          DB_FILE=$(ls -t xinhua_db_*.tar.gz | head -1)
          scp $DB_FILE deploy@production.example.com:/opt/xinhua-tool/
          ssh deploy@production.example.com "cd /opt/xinhua-tool && ./deploy.sh docker --with-db $DB_FILE"
```

---

## 示例 8: Docker Swarm 集群部署

### 场景说明
在 Docker Swarm 集群中部署并共享数据库。

### 步骤

**1. 初始化 Swarm 集群**

```bash
# 在管理节点
docker swarm init --advertise-addr <MANAGER-IP>

# 在工作节点加入集群
docker swarm join --token <TOKEN> <MANAGER-IP>:2377
```

**2. 创建共享卷**

```bash
# 创建 NFS 卷或使用云存储卷
docker volume create --driver local \
  --opt type=nfs \
  --opt o=addr=<NFS-SERVER>,rw \
  --opt device=:/path/to/share \
  xinhua-db-data
```

**3. 修改 docker-compose.yml 支持 Swarm**

创建 `docker-compose.swarm.yml`:

```yaml
version: '3.8'

services:
  backend:
    image: xinhua-backend:latest
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
    volumes:
      - xinhua-db-data:/app
    networks:
      - xinhua-network

  workflow-ctl:
    image: xinhua-workflow-ctl:latest
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
    volumes:
      - xinhua-db-data:/app/data
    networks:
      - xinhua-network

volumes:
  xinhua-db-data:
    external: true

networks:
  xinhua-network:
    driver: overlay
```

**4. 部署到 Swarm**

```bash
# 导出数据库
./db_migration.sh export

# 复制数据库到共享存储
DB_FILE=$(ls -t xinhua_db_*.tar.gz | head -1)
tar xzf $DB_FILE -C /path/to/nfs/share/

# 部署 Stack
docker stack deploy -c docker-compose.swarm.yml xinhua
```

---

## 常见问题解决

### Q1: 数据库导出为空

**问题**: 导出的数据库文件很小或为空。

**解决方案**:

```bash
# 检查数据库文件是否存在
ls -lh backend/app.db workflow-ctl/data/workflow.db

# 检查数据库内容
sqlite3 backend/app.db "SELECT count(*) FROM sqlite_master WHERE type='table';"

# 如果数据库为空，可能需要先初始化
docker-compose exec backend python init_db.py
docker-compose exec workflow-ctl python init_db.py
```

### Q2: 导入后数据丢失

**问题**: 导入数据库后，发现某些表或数据丢失。

**解决方案**:

```bash
# 验证数据库完整性
./db_migration.sh verify

# 检查备份
ls -la db_backup_before_import_*/

# 尝试回滚
./db_migration.sh rollback db_backup_before_import_<timestamp>

# 如果是权限问题
chmod 644 backend/app.db workflow-ctl/data/workflow.db
chown -R 1000:1000 backend workflow-ctl/data
```

### Q3: 远程部署连接超时

**问题**: 使用 `export_and_deploy.sh` 时连接超时。

**解决方案**:

```bash
# 检查 SSH 连接
ssh -v user@remote-server

# 配置 SSH 保持连接
echo "ServerAliveInterval 60" >> ~/.ssh/config
echo "ServerAliveCountMax 3" >> ~/.ssh/config

# 或使用密钥认证
ssh-keygen -t rsa -b 4096
ssh-copy-id user@remote-server
```

---

## 最佳实践总结

1. **定期备份**: 设置 cron 任务每天自动备份
2. **多版本保留**: 至少保留最近 7 天的备份
3. **测试验证**: 导入后务必验证数据库完整性
4. **权限控制**: 数据库文件权限设置为 644
5. **加密传输**: 使用 SSH/SCP 传输数据库文件
6. **异地存储**: 将重要备份上传到云存储
7. **文档记录**: 记录每次迁移的时间、原因和结果
8. **回滚准备**: 导入前确保有可回滚的备份

---

**更多信息**: 请查看 [DATABASE_MIGRATION_GUIDE.md](DATABASE_MIGRATION_GUIDE.md) 获取完整文档。

