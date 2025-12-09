# GitHub 拉取代码快速指南

## 🎯 功能说明

在 Ubuntu 服务器上自动从 GitHub 拉取代码到 `/home` 目录。

## 📦 提供的脚本

本项目提供 3 个脚本，根据需要选择：

| 脚本 | 特点 | 适用场景 |
|------|------|---------|
| `pull_from_github.sh` | 功能完整，自动化程度高 | ✅ 推荐日常使用 |
| `pull_github_simple.sh` | 代码简洁，快速执行 | 适合快速测试 |
| `pull_from_github_secure.sh` | 使用环境变量，更安全 | ✅ 推荐生产环境 |

## 🚀 快速开始（3步）

### 第 1 步：修改配置

**方式 1：使用完整版脚本（推荐）**

编辑 `pull_from_github.sh`：

```bash
nano pull_from_github.sh
```

找到并修改：
```bash
REPO_OWNER="your-username"    # 改成你的 GitHub 用户名
REPO_NAME="xinhua-tool"       # 改成你的仓库名
```

**方式 2：使用简化版脚本**

编辑 `pull_github_simple.sh`：

```bash
nano pull_github_simple.sh
```

找到并修改：
```bash
REPO_URL="https://${GITHUB_TOKEN}@github.com/your-username/xinhua-tool.git"
#                                              ^^^^^^^^^^^^^ 改成你的用户名
```

**方式 3：使用安全版脚本（生产环境推荐）**

```bash
# 创建 Token 配置文件
echo 'export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"' > ~/.github_token
chmod 600 ~/.github_token

# 修改仓库信息
nano pull_from_github_secure.sh
# 修改 REPO_OWNER 和 REPO_NAME
```

### 第 2 步：上传到服务器

```bash
# 上传脚本
scp pull_from_github.sh ubuntu@服务器IP:/home/ubuntu/

# 或使用 SFTP
sftp ubuntu@服务器IP
put pull_from_github.sh
```

### 第 3 步：运行脚本

SSH 登录服务器后：

```bash
# 赋予执行权限
chmod +x pull_from_github.sh

# 运行脚本
./pull_from_github.sh
```

**完成！** 代码会自动下载到 `/home/xinhua-tool` 目录。

## 💻 使用示例

### 示例 1：首次克隆代码

```bash
# 在服务器上
chmod +x pull_from_github.sh
./pull_from_github.sh

# 输出：
# ========================================
# GitHub 代码拉取脚本
# ========================================
# 仓库: your-username/xinhua-tool
# 分支: main
# 目标目录: /home/xinhua-tool
# 
# 正在克隆仓库...
# ✓ 代码克隆完成！
```

### 示例 2：更新现有代码

```bash
# 再次运行相同命令即可
./pull_from_github.sh

# 脚本会自动检测并更新
```

### 示例 3：克隆到自定义目录

```bash
# 通过参数指定目录
./pull_from_github.sh your-username xinhua-tool /opt/xinhua-tool
```

### 示例 4：使用安全版本

```bash
# 加载 Token
source ~/.github_token

# 运行脚本
./pull_from_github_secure.sh

# 或一行命令
source ~/.github_token && ./pull_from_github_secure.sh
```

## 🔧 常见问题

### 问题 1：权限不足

```bash
# 错误提示：Permission denied

# 解决方法：
sudo mkdir -p /home
sudo chown $USER:$USER /home
./pull_from_github.sh
```

### 问题 2：Git 未安装

```bash
# 脚本会自动安装，如失败手动执行：
sudo apt-get update
sudo apt-get install -y git
```

### 问题 3：Token 认证失败

```bash
# 错误提示：Authentication failed

# 检查 Token 是否正确
# 在 GitHub 生成新 Token:
# https://github.com/settings/tokens
# 选择权限: repo (完整仓库访问)
```

### 问题 4：脚本无法执行

```bash
# 确保有执行权限
chmod +x pull_from_github.sh

# 确保是 Unix 格式（Windows 编辑可能有问题）
dos2unix pull_from_github.sh  # 如果需要
```

### 问题 5：修改 REPO_OWNER 忘记保存

```bash
# 方法 1：通过参数传递
./pull_from_github.sh your-actual-username xinhua-tool

# 方法 2：重新编辑并保存
nano pull_from_github.sh
```

## 📋 参数说明

### pull_from_github.sh 参数

```bash
./pull_from_github.sh [owner] [repo] [target_dir] [branch]
```

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| owner | GitHub 用户名 | 脚本中配置 | `your-username` |
| repo | 仓库名称 | `xinhua-tool` | `my-project` |
| target_dir | 目标目录 | `/home/xinhua-tool` | `/opt/myapp` |
| branch | 分支名称 | `main` | `develop` |

### 使用示例

```bash
# 使用默认配置
./pull_from_github.sh

# 指定用户和仓库
./pull_from_github.sh myusername myrepo

# 完整参数
./pull_from_github.sh myusername myrepo /opt/myapp develop
```

## 🔐 安全建议

### 1. Token 安全存储

**不推荐**：直接写在脚本里
```bash
GITHUB_TOKEN="ghp_xxx"  # ❌ 不安全
```

**推荐**：使用配置文件
```bash
# 创建配置文件
echo 'export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"' > ~/.github_token

# 设置权限（仅当前用户可读）
chmod 600 ~/.github_token

# 使用时加载
source ~/.github_token && ./pull_from_github.sh
```

### 2. 最小权限原则

生成 Token 时只授予必要权限：
- 公开仓库：选择 `public_repo`
- 私有仓库：选择 `repo`

### 3. 定期更新 Token

```bash
# 在 GitHub 设置新的过期时间
# https://github.com/settings/tokens
# 建议：30-90 天过期
```

### 4. 使用 SSH（最安全）

```bash
# 生成 SSH 密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 添加到 GitHub
cat ~/.ssh/id_ed25519.pub
# 复制到 GitHub Settings -> SSH Keys

# 修改脚本使用 SSH URL
REPO_URL="git@github.com:your-username/xinhua-tool.git"
```

## 🔄 自动更新设置

### 方法 1：定时任务（Cron）

```bash
# 编辑 crontab
crontab -e

# 每天凌晨 2 点自动更新
0 2 * * * cd /home/ubuntu && source ~/.github_token && ./pull_from_github.sh >> /var/log/github-pull.log 2>&1

# 每小时更新一次
0 * * * * cd /home/ubuntu && source ~/.github_token && ./pull_from_github.sh >> /var/log/github-pull.log 2>&1
```

### 方法 2：Systemd 定时器

```bash
# 创建服务文件
sudo nano /etc/systemd/system/github-pull.service

# 内容：
[Unit]
Description=Pull code from GitHub

[Service]
Type=oneshot
User=ubuntu
Environment="GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
ExecStart=/home/ubuntu/pull_from_github_secure.sh

# 创建定时器
sudo nano /etc/systemd/system/github-pull.timer

# 内容：
[Unit]
Description=Pull code from GitHub daily

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target

# 启用定时器
sudo systemctl enable github-pull.timer
sudo systemctl start github-pull.timer

# 查看状态
sudo systemctl status github-pull.timer
```

## 📊 完整工作流程

### 开发环境 → 测试服务器

```bash
# 1. 在开发机提交代码
git add .
git commit -m "新功能"
git push origin main

# 2. 在测试服务器拉取
ssh test-server
cd /home/ubuntu
./pull_from_github.sh

# 3. 验证代码
cd /home/xinhua-tool
ls -la
git log -1
```

### 测试通过 → 生产服务器

```bash
# 1. 在生产服务器拉取
ssh production-server
cd /home/ubuntu
source ~/.github_token
./pull_from_github_secure.sh

# 2. 部署应用
cd /home/xinhua-tool
./deploy.sh docker

# 3. 验证部署
docker-compose ps
curl http://localhost:8000/health
```

## 📚 相关命令

### 查看代码

```bash
# 进入目录
cd /home/xinhua-tool

# 查看文件
ls -la

# 查看 Git 状态
git status

# 查看提交历史
git log --oneline -10

# 查看当前分支
git branch -v
```

### 管理代码

```bash
# 切换分支
cd /home/xinhua-tool
git checkout develop

# 查看远程分支
git branch -r

# 拉取特定标签
git fetch --tags
git checkout tags/v1.0.0

# 丢弃本地修改
git reset --hard HEAD
git clean -fd
```

### 查看脚本日志

```bash
# 查看 cron 日志
tail -f /var/log/github-pull.log

# 查看系统日志
journalctl -u github-pull -f

# 查看最近的执行
grep github-pull /var/log/syslog
```

## ✅ 检查清单

部署前确认：

- [ ] 已修改 `REPO_OWNER` 为实际 GitHub 用户名
- [ ] 已修改 `REPO_NAME` 为实际仓库名称
- [ ] 已确认 GitHub Token 有效且未过期
- [ ] 已上传脚本到服务器
- [ ] 已赋予脚本执行权限 (`chmod +x`)
- [ ] 已测试网络连接到 GitHub
- [ ] 已了解目标目录位置
- [ ] （可选）已设置定时自动更新

## 🎓 最佳实践

1. **使用安全版脚本** - 生产环境使用环境变量存储 Token
2. **定期备份** - 拉取代码前备份现有版本
3. **测试先行** - 先在测试环境验证
4. **日志记录** - 记录每次拉取的时间和结果
5. **权限控制** - 限制脚本和配置文件的访问权限
6. **版本管理** - 使用 Git 标签管理发布版本

## 🆘 需要帮助？

### 查看脚本帮助

```bash
# 查看脚本内容
cat pull_from_github.sh | less

# 查看 Git 版本
git --version

# 测试 GitHub 连接
ping github.com
```

### 生成新的 Token

访问：https://github.com/settings/tokens

1. 点击 "Generate new token"
2. 选择权限：`repo` (完整仓库访问)
3. 设置过期时间（建议 90 天）
4. 复制 Token 并保存

---

## 📌 快速命令参考

```bash
# 上传脚本
scp pull_from_github.sh ubuntu@server:/home/ubuntu/

# 运行脚本
chmod +x pull_from_github.sh && ./pull_from_github.sh

# 查看代码
cd /home/xinhua-tool && ls -la

# 更新代码
./pull_from_github.sh

# 安全版本
source ~/.github_token && ./pull_from_github_secure.sh

# 设置定时任务（每天 2 点）
echo "0 2 * * * cd /home/ubuntu && ./pull_from_github.sh" | crontab -
```

**重要提示**：
- ⚠️ 首次使用前必须修改 `REPO_OWNER` 为你的 GitHub 用户名
- ⚠️ Token 是敏感信息，请妥善保管
- ⚠️ 建议使用安全版脚本或 SSH 密钥方式

**完整文档**: 查看 `GITHUB_PULL_GUIDE.md`
