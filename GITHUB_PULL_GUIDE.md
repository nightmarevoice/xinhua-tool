# GitHub 代码拉取脚本使用指南

## 📋 脚本说明

本项目提供了两个脚本用于在 Ubuntu 服务器上拉取 GitHub 代码：

1. **`pull_from_github.sh`** - 完整功能版本（推荐）
2. **`pull_github_simple.sh`** - 简化快速版本

## 🚀 快速开始

### 步骤 1: 上传脚本到服务器

```bash
# 使用 SCP 上传
scp pull_from_github.sh user@server-ip:/tmp/

# 或使用 SFTP
sftp user@server-ip
put pull_from_github.sh
```

### 步骤 2: 修改配置

在运行脚本前，需要修改以下配置：

```bash
# 编辑脚本
nano pull_from_github.sh

# 修改这些变量：
REPO_OWNER="your-username"    # 改为你的 GitHub 用户名
REPO_NAME="xinhua-tool"       # 改为你的仓库名
TARGET_DIR="/home/xinhua-tool" # 目标目录（可选）
BRANCH="main"                 # 分支名称（可选）
```

### 步骤 3: 运行脚本

```bash
# 赋予执行权限
chmod +x pull_from_github.sh

# 运行脚本
./pull_from_github.sh

# 或者通过参数指定
./pull_from_github.sh your-username xinhua-tool /home/xinhua-tool main
```

## 📖 详细使用说明

### 方式 1: 使用完整版脚本（推荐）

#### 基本用法

```bash
# 使用脚本内配置
./pull_from_github.sh

# 通过命令行参数
./pull_from_github.sh <owner> <repo> <target_dir> <branch>
```

#### 示例

```bash
# 克隆到默认位置 /home/xinhua-tool
./pull_from_github.sh your-username xinhua-tool

# 克隆到自定义位置
./pull_from_github.sh your-username xinhua-tool /opt/xinhua-tool

# 指定分支
./pull_from_github.sh your-username xinhua-tool /home/xinhua-tool develop
```

#### 功能特性

✅ 自动检测并安装 Git  
✅ 首次克隆 + 后续更新支持  
✅ 自动暂存本地修改  
✅ 权限自动设置  
✅ 显示最新提交信息  
✅ 安全清理 Git 凭证  
✅ 交互式确认操作  

### 方式 2: 使用简化版脚本

#### 修改配置

```bash
nano pull_github_simple.sh

# 修改这一行
REPO_URL="https://${GITHUB_TOKEN}@github.com/your-username/xinhua-tool.git"
#                                              ^^^^^^^^^^^^^
#                                              改为你的用户名
```

#### 运行

```bash
chmod +x pull_github_simple.sh
./pull_github_simple.sh
```

## 🔧 配置说明

### 1. GitHub Token

脚本中已包含 Personal Access Token：
```bash
GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 2. 仓库信息

需要修改为实际的仓库信息：
```bash
REPO_OWNER="your-username"  # GitHub 用户名或组织名
REPO_NAME="xinhua-tool"     # 仓库名称
```

### 3. 目标目录

```bash
TARGET_DIR="/home/xinhua-tool"  # 代码存放位置
```

### 4. 分支

```bash
BRANCH="main"  # 或 "master", "develop" 等
```

## 📝 完整示例

### 示例 1: 首次克隆代码

```bash
# 1. 上传脚本
scp pull_from_github.sh ubuntu@192.168.1.100:/tmp/

# 2. SSH 登录服务器
ssh ubuntu@192.168.1.100

# 3. 修改脚本配置
cd /tmp
nano pull_from_github.sh
# 修改 REPO_OWNER 为实际用户名

# 4. 运行脚本
chmod +x pull_from_github.sh
./pull_from_github.sh

# 5. 查看结果
cd /home/xinhua-tool
ls -la
```

### 示例 2: 更新现有代码

```bash
# 直接运行脚本即可
./pull_from_github.sh

# 脚本会自动检测现有仓库并更新
```

### 示例 3: 切换分支

```bash
# 拉取 develop 分支
./pull_from_github.sh your-username xinhua-tool /home/xinhua-tool develop
```

## 🔐 安全建议

### 1. Token 安全

**重要**: Personal Access Token 是敏感信息，建议：

#### 方式 1: 使用环境变量（推荐）

```bash
# 修改脚本，从环境变量读取
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

if [ -z "$GITHUB_TOKEN" ]; then
    echo "错误: 请设置 GITHUB_TOKEN 环境变量"
    exit 1
fi

# 运行时提供 token
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
./pull_from_github.sh
```

#### 方式 2: 使用配置文件

```bash
# 创建配置文件
cat > ~/.github_config << EOF
GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
EOF

# 设置权限
chmod 600 ~/.github_config

# 在脚本中加载
source ~/.github_config
```

#### 方式 3: 使用 SSH 密钥（最安全）

```bash
# 生成 SSH 密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 添加到 GitHub
cat ~/.ssh/id_ed25519.pub
# 复制内容到 GitHub Settings -> SSH Keys

# 修改脚本使用 SSH
REPO_URL="git@github.com:your-username/xinhua-tool.git"
```

### 2. 文件权限

```bash
# 限制脚本访问权限
chmod 700 pull_from_github.sh

# 限制配置文件权限
chmod 600 ~/.github_config
```

### 3. Token 管理

- 🔒 定期更新 Token
- 🔒 使用最小权限 Token（只读即可）
- 🔒 不要将 Token 提交到版本控制
- 🔒 使用后及时清理历史记录

## 🛠️ 故障排查

### 问题 1: 权限不足

```bash
# 错误: Permission denied
# 解决: 使用 sudo 或修改目录权限

sudo ./pull_from_github.sh

# 或
sudo mkdir -p /home
sudo chown $USER:$USER /home
./pull_from_github.sh
```

### 问题 2: Git 未安装

```bash
# 脚本会自动安装，如果失败手动安装
sudo apt-get update
sudo apt-get install -y git
```

### 问题 3: Token 无效

```bash
# 错误: Authentication failed
# 解决: 检查 Token 是否正确，是否过期

# 在 GitHub 生成新的 Token:
# Settings -> Developer settings -> Personal access tokens -> Generate new token
# 权限: repo (完整仓库访问)
```

### 问题 4: 网络问题

```bash
# 错误: Failed to connect
# 解决: 检查网络连接

# 测试连接
ping github.com

# 使用代理（如果需要）
export https_proxy=http://proxy:port
./pull_from_github.sh
```

### 问题 5: 目录已存在但不是 Git 仓库

```bash
# 脚本会提示是否删除，或手动处理
sudo rm -rf /home/xinhua-tool
./pull_from_github.sh
```

### 问题 6: 本地有未提交的修改

```bash
# 脚本会自动 stash，也可以手动处理
cd /home/xinhua-tool
git status
git stash
git pull
```

## 🔄 自动化部署

### 方式 1: 创建系统服务

```bash
# 创建服务文件
sudo nano /etc/systemd/system/github-sync.service

# 内容：
[Unit]
Description=GitHub Code Sync
After=network.target

[Service]
Type=oneshot
User=ubuntu
ExecStart=/home/ubuntu/pull_from_github.sh
WorkingDirectory=/home/ubuntu

[Install]
WantedBy=multi-user.target
```

### 方式 2: 定时任务

```bash
# 每天凌晨 2 点自动更新
crontab -e

# 添加：
0 2 * * * /home/ubuntu/pull_from_github.sh >> /var/log/github-pull.log 2>&1
```

### 方式 3: Git Hook

```bash
# 配置 GitHub Webhook 触发更新
# 需要配置 Web 服务器接收 webhook 请求
```

## 📊 使用场景

### 场景 1: 开发服务器

```bash
# 定期同步最新代码
*/30 * * * * /home/ubuntu/pull_from_github.sh
```

### 场景 2: 生产环境

```bash
# 手动拉取特定标签
cd /home/xinhua-tool
git fetch --tags
git checkout v1.0.0
```

### 场景 3: CI/CD 集成

```bash
# 在 CI/CD 流程中使用
- name: Pull latest code
  run: |
    chmod +x pull_from_github.sh
    ./pull_from_github.sh
```

## 📚 相关命令

### Git 常用命令

```bash
# 查看状态
git status

# 查看提交历史
git log --oneline -10

# 查看远程信息
git remote -v

# 切换分支
git checkout develop

# 更新代码
git pull origin main

# 查看标签
git tag -l

# 检出标签
git checkout tags/v1.0.0
```

### 清理操作

```bash
# 清理未跟踪的文件
git clean -fd

# 重置所有修改
git reset --hard HEAD

# 删除本地分支
git branch -D branch-name
```

## ✅ 检查清单

使用脚本前确认：

- [ ] 已修改 `REPO_OWNER` 为实际 GitHub 用户名
- [ ] 已修改 `REPO_NAME` 为实际仓库名
- [ ] 已确认 Personal Access Token 有效
- [ ] 已确认目标目录路径正确
- [ ] 已确认分支名称正确
- [ ] 已赋予脚本执行权限
- [ ] 已测试网络连接到 GitHub
- [ ] 已了解脚本功能和影响范围

## 🆘 获取帮助

### 脚本帮助

```bash
# 查看脚本用法
./pull_from_github.sh --help

# 或直接阅读脚本
cat pull_from_github.sh | less
```

### GitHub Token 帮助

访问: https://github.com/settings/tokens

生成新 Token 时选择权限：
- `repo` - 完整仓库访问（克隆私有仓库）
- `public_repo` - 仅公开仓库（克隆公开仓库）

---

## 📌 快速参考

```bash
# 完整版 - 首次运行
./pull_from_github.sh your-username xinhua-tool

# 完整版 - 更新代码
./pull_from_github.sh

# 简化版
./pull_github_simple.sh

# 查看代码
cd /home/xinhua-tool && ls -la

# 查看 Git 状态
cd /home/xinhua-tool && git status
```

**提示**: 记得修改脚本中的 `REPO_OWNER` 为你的实际 GitHub 用户名！
