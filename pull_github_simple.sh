#!/bin/bash

#################################################
# GitHub 代码拉取脚本 - 简化版
# 快速拉取 xinhua-tool 项目到 /home 目录
#################################################

# GitHub 配置
GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
REPO_URL="https://${GITHUB_TOKEN}@github.com/your-username/xinhua-tool.git"
TARGET_DIR="/home/xinhua-tool"

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "========================================="
echo "GitHub 代码拉取"
echo "========================================="

# 安装 git（如果需要）
if ! command -v git &> /dev/null; then
    echo "安装 Git..."
    sudo apt-get update && sudo apt-get install -y git
fi

# 克隆或更新
if [ -d "$TARGET_DIR/.git" ]; then
    echo "更新现有代码..."
    cd "$TARGET_DIR"
    git stash
    git pull origin main
    echo -e "${GREEN}✓ 代码更新完成${NC}"
else
    echo "克隆新代码..."
    sudo mkdir -p /home
    git clone "$REPO_URL" "$TARGET_DIR"
    echo -e "${GREEN}✓ 代码克隆完成${NC}"
fi

# 设置权限
sudo chown -R $USER:$USER "$TARGET_DIR"

echo ""
echo "代码位置: $TARGET_DIR"
echo "使用: cd $TARGET_DIR"

