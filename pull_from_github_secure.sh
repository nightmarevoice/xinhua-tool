#!/bin/bash

#################################################
# GitHub 代码拉取脚本 - 安全版本
# 使用环境变量存储 Token，更加安全
#################################################

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 从环境变量读取 Token
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

# 配置变量（请修改）
REPO_OWNER="${REPO_OWNER:-your-username}"  # 修改为你的 GitHub 用户名
REPO_NAME="${REPO_NAME:-xinhua-tool}"      # 修改为你的仓库名
TARGET_DIR="${TARGET_DIR:-/home/xinhua-tool}"
BRANCH="${BRANCH:-main}"

# 命令行参数覆盖
[ ! -z "$1" ] && REPO_OWNER="$1"
[ ! -z "$2" ] && REPO_NAME="$2"
[ ! -z "$3" ] && TARGET_DIR="$3"
[ ! -z "$4" ] && BRANCH="$4"

# 检查 Token
if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}错误: 未设置 GITHUB_TOKEN 环境变量${NC}"
    echo ""
    echo "请使用以下方式之一设置 Token:"
    echo ""
    echo "方式 1: 临时设置（推荐用于测试）"
    echo "  export GITHUB_TOKEN='your-token-here'"
    echo "  $0"
    echo ""
    echo "方式 2: 从配置文件读取（推荐用于生产）"
    echo "  创建配置文件:"
    echo "    echo 'export GITHUB_TOKEN=\"your-token-here\"' > ~/.github_token"
    echo "    chmod 600 ~/.github_token"
    echo "  使用:"
    echo "    source ~/.github_token && $0"
    echo ""
    echo "方式 3: 内联使用（一次性）"
    echo "  GITHUB_TOKEN='your-token-here' $0"
    echo ""
    exit 1
fi

# 检查配置
if [ "$REPO_OWNER" = "your-username" ]; then
    echo -e "${YELLOW}警告: 请修改 REPO_OWNER 为实际的 GitHub 用户名${NC}"
    echo ""
    read -p "请输入 GitHub 用户名: " input_owner
    if [ ! -z "$input_owner" ]; then
        REPO_OWNER="$input_owner"
    else
        echo -e "${RED}错误: 必须提供 GitHub 用户名${NC}"
        exit 1
    fi
fi

# 构建仓库 URL
REPO_URL="https://${GITHUB_TOKEN}@github.com/${REPO_OWNER}/${REPO_NAME}.git"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}GitHub 代码拉取脚本 (安全版)${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "仓库: ${REPO_OWNER}/${REPO_NAME}"
echo "分支: ${BRANCH}"
echo "目标: ${TARGET_DIR}"
echo ""

# 安装 git
if ! command -v git &> /dev/null; then
    echo "安装 Git..."
    sudo apt-get update && sudo apt-get install -y git
    echo -e "${GREEN}✓ Git 安装完成${NC}"
fi

# 克隆或更新
if [ -d "$TARGET_DIR/.git" ]; then
    echo "更新现有代码..."
    cd "$TARGET_DIR"
    
    # 暂存本地修改
    if ! git diff-index --quiet HEAD --; then
        echo -e "${YELLOW}⚠ 检测到本地修改，正在暂存...${NC}"
        git stash save "Auto-stash $(date +%Y%m%d_%H%M%S)"
    fi
    
    # 拉取更新
    git fetch origin "$BRANCH"
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
    
    echo -e "${GREEN}✓ 代码更新完成${NC}"
    echo ""
    echo "最新提交:"
    git log -1 --pretty=format:"%h - %an, %ar : %s" && echo ""
    
elif [ -d "$TARGET_DIR" ]; then
    echo -e "${RED}错误: 目录存在但不是 Git 仓库: $TARGET_DIR${NC}"
    read -p "是否删除并重新克隆？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo rm -rf "$TARGET_DIR"
    else
        exit 1
    fi
fi

# 克隆新仓库
if [ ! -d "$TARGET_DIR" ]; then
    echo "克隆仓库..."
    
    PARENT_DIR=$(dirname "$TARGET_DIR")
    if [ ! -d "$PARENT_DIR" ]; then
        sudo mkdir -p "$PARENT_DIR"
    fi
    
    git clone -b "$BRANCH" "$REPO_URL" "$TARGET_DIR"
    
    echo -e "${GREEN}✓ 代码克隆完成${NC}"
    
    cd "$TARGET_DIR"
    echo ""
    echo "最新提交:"
    git log -1 --pretty=format:"%h - %an, %ar : %s" && echo ""
fi

# 设置权限
echo ""
echo "设置权限..."
sudo chown -R $USER:$USER "$TARGET_DIR"
sudo chmod -R 755 "$TARGET_DIR"
echo -e "${GREEN}✓ 权限设置完成${NC}"

# 清理凭证
cd "$TARGET_DIR"
git config --local --unset credential.helper 2>/dev/null || true

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ 操作完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "代码位置: $TARGET_DIR"
echo ""
echo "下一步:"
echo "  cd $TARGET_DIR"
echo "  ls -la"
echo ""

exit 0

