#!/bin/bash

#################################################
# GitHub 代码拉取脚本
# 用途: 在 Ubuntu 服务器上拉取/更新 GitHub 代码
# 位置: /home 目录
#################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量
GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
REPO_OWNER="nightmarevoice"  # 修改为你的 GitHub 用户名或组织名
REPO_NAME="xinhua-tool"     # 修改为你的仓库名
TARGET_DIR="/home/xinhua-tool"
BRANCH="main"               # 默认分支

# 可以通过命令行参数覆盖
if [ ! -z "$1" ]; then
    REPO_OWNER="$1"
fi

if [ ! -z "$2" ]; then
    REPO_NAME="$2"
fi

if [ ! -z "$3" ]; then
    TARGET_DIR="$3"
fi

if [ ! -z "$4" ]; then
    BRANCH="$4"
fi

# 构建仓库 URL
REPO_URL="https://${GITHUB_TOKEN}@github.com/${REPO_OWNER}/${REPO_NAME}.git"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}GitHub 代码拉取脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "仓库: ${REPO_OWNER}/${REPO_NAME}"
echo "分支: ${BRANCH}"
echo "目标目录: ${TARGET_DIR}"
echo ""

# 函数: 打印成功消息
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# 函数: 打印错误消息
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# 函数: 打印警告消息
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# 检查 git 是否安装
if ! command -v git &> /dev/null; then
    print_error "Git 未安装，正在安装..."
    sudo apt-get update
    sudo apt-get install -y git
    print_success "Git 安装完成"
fi

# 检查目标目录是否存在
if [ -d "$TARGET_DIR" ]; then
    print_warning "目录已存在: $TARGET_DIR"
    
    # 检查是否是 git 仓库
    if [ -d "$TARGET_DIR/.git" ]; then
        print_warning "检测到现有 Git 仓库，正在更新..."
        
        cd "$TARGET_DIR"
        
        # 保存本地修改（如果有）
        if ! git diff-index --quiet HEAD --; then
            print_warning "检测到本地修改，正在暂存..."
            git stash save "Auto-stash before pull $(date +%Y%m%d_%H%M%S)"
            print_success "本地修改已暂存"
        fi
        
        # 拉取最新代码
        echo "正在拉取最新代码..."
        git fetch origin "$BRANCH"
        git checkout "$BRANCH"
        git pull origin "$BRANCH"
        
        print_success "代码更新完成！"
        
        # 显示最新提交
        echo ""
        echo "最新提交信息:"
        git log -1 --pretty=format:"%h - %an, %ar : %s" && echo ""
        
    else
        print_error "目录存在但不是 Git 仓库"
        read -p "是否删除现有目录并重新克隆？(y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$TARGET_DIR"
            print_success "已删除现有目录"
        else
            print_error "操作已取消"
            exit 1
        fi
    fi
fi

# 如果目录不存在，执行克隆
if [ ! -d "$TARGET_DIR" ]; then
    echo "正在克隆仓库..."
    
    # 创建父目录（如果不存在）
    PARENT_DIR=$(dirname "$TARGET_DIR")
    if [ ! -d "$PARENT_DIR" ]; then
        sudo mkdir -p "$PARENT_DIR"
        print_success "已创建父目录: $PARENT_DIR"
    fi
    
    # 克隆仓库
    git clone -b "$BRANCH" "$REPO_URL" "$TARGET_DIR"
    
    print_success "代码克隆完成！"
    
    cd "$TARGET_DIR"
    
    # 显示最新提交
    echo ""
    echo "最新提交信息:"
    git log -1 --pretty=format:"%h - %an, %ar : %s" && echo ""
fi

# 设置权限
echo ""
echo "正在设置权限..."
sudo chown -R $USER:$USER "$TARGET_DIR"
sudo chmod -R 755 "$TARGET_DIR"
print_success "权限设置完成"

# 显示仓库状态
echo ""
echo "仓库状态:"
cd "$TARGET_DIR"
git status -s

# 显示分支信息
echo ""
echo "当前分支:"
git branch -v

# 清理 git 凭证（安全措施）
echo ""
echo "正在清理 git 凭证..."
git config --local --unset credential.helper 2>/dev/null || true
print_success "Git 凭证已清理"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ 操作完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "代码位置: $TARGET_DIR"
echo ""
echo "后续步骤:"
echo "  1. cd $TARGET_DIR"
echo "  2. 查看 README.md 了解项目信息"
echo "  3. 根据需要进行部署"
echo ""

# 询问是否查看目录内容
read -p "是否查看目录内容？(y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "目录内容:"
    ls -lah "$TARGET_DIR"
fi

exit 0
