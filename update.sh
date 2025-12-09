#!/bin/bash

#############################################
# 项目更新脚本
# 使用方法: ./update.sh [--no-backup] [--force]
#############################################

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 参数
NO_BACKUP=false
FORCE_UPDATE=false

# 解析参数
for arg in "$@"; do
    case $arg in
        --no-backup)
            NO_BACKUP=true
            shift
            ;;
        --force)
            FORCE_UPDATE=true
            shift
            ;;
        *)
            ;;
    esac
done

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} [$(date '+%H:%M:%S')] $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} [$(date '+%H:%M:%S')] $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} [$(date '+%H:%M:%S')] $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} [$(date '+%H:%M:%S')] $1"
}

# 检查 git 仓库
check_git_repo() {
    if [ ! -d .git ]; then
        log_error "当前目录不是 Git 仓库"
        log_info "请使用 git clone 部署项目"
        exit 1
    fi
}

# 检查更新
check_updates() {
    log_step "检查更新..."
    
    # 获取当前分支
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    log_info "当前分支: $current_branch"
    
    # 获取远程更新
    git fetch origin
    
    # 检查是否有更新
    local local_commit=$(git rev-parse HEAD)
    local remote_commit=$(git rev-parse origin/$current_branch)
    
    if [ "$local_commit" = "$remote_commit" ]; then
        log_info "已是最新版本"
        
        if [ "$FORCE_UPDATE" = false ]; then
            read -p "是否强制重新部署？(y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 0
            fi
        fi
    else
        log_info "发现新版本"
        log_info "本地: ${local_commit:0:7}"
        log_info "远程: ${remote_commit:0:7}"
        
        # 显示更新内容
        echo ""
        log_info "更新内容:"
        git log --oneline $local_commit..$remote_commit
        echo ""
    fi
}

# 备份当前版本
backup_current() {
    if [ "$NO_BACKUP" = true ]; then
        log_info "跳过备份"
        return
    fi
    
    log_step "备份当前版本..."
    
    # 执行备份脚本
    if [ -f ./backup.sh ]; then
        ./backup.sh quick
    else
        log_warn "备份脚本不存在，跳过备份"
    fi
}

# 检查服务状态
check_services() {
    log_step "检查服务状态..."
    
    if command -v docker-compose &> /dev/null; then
        docker-compose ps
    else
        systemctl status xinhua-backend xinhua-workflow-ctl --no-pager || true
    fi
}

# 拉取最新代码
pull_code() {
    log_step "拉取最新代码..."
    
    # 保存本地修改
    if [ -n "$(git status --porcelain)" ]; then
        log_warn "检测到本地修改，保存中..."
        git stash push -m "Auto stash before update $(date '+%Y-%m-%d %H:%M:%S')"
    fi
    
    # 拉取代码
    git pull origin $(git rev-parse --abbrev-ref HEAD)
    
    log_info "代码更新完成"
}

# Docker 方式更新
update_docker() {
    log_step "使用 Docker Compose 更新..."
    
    # 选择使用的 compose 文件
    local compose_file="docker-compose.yml"
    if [ -f "docker-compose.production.yml" ]; then
        log_info "使用生产环境配置"
        compose_file="docker-compose.production.yml"
    fi
    
    # 重新构建镜像
    log_info "重新构建镜像..."
    docker-compose -f $compose_file build --no-cache
    
    # 滚动更新服务（一次更新一个服务以减少停机时间）
    log_info "更新后端服务..."
    docker-compose -f $compose_file up -d --no-deps backend
    sleep 5
    
    log_info "更新 workflow-ctl 服务..."
    docker-compose -f $compose_file up -d --no-deps workflow-ctl
    sleep 5
    
    log_info "更新前端服务..."
    docker-compose -f $compose_file up -d --no-deps frontend
    sleep 5
    
    # 清理旧镜像
    log_info "清理旧镜像..."
    docker image prune -f
    
    log_info "Docker 服务更新完成"
}

# 传统方式更新后端
update_backend_traditional() {
    log_step "更新后端服务..."
    
    cd backend
    
    # 更新依赖
    source venv/bin/activate
    pip install -r requirements.txt
    
    # 数据库迁移
    if [ -f alembic.ini ]; then
        log_info "执行数据库迁移..."
        alembic upgrade head
    fi
    
    cd ..
    
    # 重启服务
    sudo systemctl restart xinhua-backend
    sleep 5
    
    # 检查服务状态
    if systemctl is-active --quiet xinhua-backend; then
        log_info "后端服务启动成功"
    else
        log_error "后端服务启动失败"
        sudo journalctl -u xinhua-backend -n 50 --no-pager
        return 1
    fi
}

# 传统方式更新 workflow-ctl
update_workflow_traditional() {
    log_step "更新 workflow-ctl 服务..."
    
    cd workflow-ctl
    
    # 更新依赖
    source venv/bin/activate
    pip install -r requirements.txt
    
    cd ..
    
    # 重启服务
    sudo systemctl restart xinhua-workflow-ctl
    sleep 5
    
    # 检查服务状态
    if systemctl is-active --quiet xinhua-workflow-ctl; then
        log_info "Workflow-ctl 服务启动成功"
    else
        log_error "Workflow-ctl 服务启动失败"
        sudo journalctl -u xinhua-workflow-ctl -n 50 --no-pager
        return 1
    fi
}

# 传统方式更新前端
update_frontend_traditional() {
    log_step "更新前端..."
    
    cd frontend
    
    # 安装依赖
    npm install
    
    # 构建
    log_info "构建前端..."
    npm run build
    
    # 部署
    log_info "部署前端文件..."
    sudo rm -rf /var/www/xinhua/*
    sudo cp -r dist/* /var/www/xinhua/
    
    cd ..
    
    # 重启 Nginx
    sudo nginx -t
    sudo systemctl reload nginx
    
    log_info "前端更新完成"
}

# 传统方式更新
update_traditional() {
    log_step "使用传统方式更新..."
    
    update_backend_traditional
    update_workflow_traditional
    update_frontend_traditional
    
    log_info "传统方式更新完成"
}

# 验证更新
verify_update() {
    log_step "验证更新..."
    
    local failed=0
    
    # 检查后端
    if curl -f -s http://localhost:8888/health > /dev/null; then
        log_info "✓ 后端服务正常"
    else
        log_error "✗ 后端服务异常"
        failed=1
    fi
    
    # 检查 workflow-ctl
    if curl -f -s http://localhost:8889/health > /dev/null; then
        log_info "✓ Workflow-ctl 服务正常"
    else
        log_error "✗ Workflow-ctl 服务异常"
        failed=1
    fi
    
    # 检查前端
    if curl -f -s http://localhost/ > /dev/null; then
        log_info "✓ 前端服务正常"
    else
        log_error "✗ 前端服务异常"
        failed=1
    fi
    
    if [ $failed -eq 0 ]; then
        log_info "所有服务验证通过"
        return 0
    else
        log_error "部分服务验证失败"
        return 1
    fi
}

# 回滚
rollback() {
    log_error "更新失败，准备回滚..."
    
    if [ "$NO_BACKUP" = true ]; then
        log_error "未创建备份，无法回滚"
        return 1
    fi
    
    # Git 回滚
    git reset --hard HEAD~1
    
    # Docker 回滚
    if command -v docker-compose &> /dev/null; then
        docker-compose down
        docker-compose up -d
    else
        # 传统方式回滚
        sudo systemctl restart xinhua-backend
        sudo systemctl restart xinhua-workflow-ctl
        sudo systemctl reload nginx
    fi
    
    log_info "回滚完成"
}

# 显示更新结果
show_result() {
    local status=$1
    
    echo ""
    echo "=========================================="
    
    if [ $status -eq 0 ]; then
        echo -e "${GREEN}✓ 更新成功！${NC}"
        echo "=========================================="
        echo ""
        log_info "当前版本: $(git rev-parse --short HEAD)"
        log_info "更新时间: $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""
        log_info "访问地址:"
        echo "  前端: http://$(hostname -I | awk '{print $1}')"
        echo "  后端: http://$(hostname -I | awk '{print $1}'):8888"
        echo ""
    else
        echo -e "${RED}✗ 更新失败！${NC}"
        echo "=========================================="
        echo ""
        log_error "请查看日志排查问题"
        echo ""
        log_info "查看日志:"
        echo "  Docker: docker-compose logs -f"
        echo "  后端: sudo journalctl -u xinhua-backend -f"
        echo "  workflow-ctl: sudo journalctl -u xinhua-workflow-ctl -f"
        echo ""
    fi
    
    echo "=========================================="
}

# 主流程
main() {
    echo "=========================================="
    echo "        新华项目更新脚本"
    echo "=========================================="
    echo ""
    
    # 检查环境
    check_git_repo
    
    # 显示当前状态
    check_services
    echo ""
    
    # 检查更新
    check_updates
    echo ""
    
    # 确认更新
    if [ "$FORCE_UPDATE" = false ]; then
        read -p "是否继续更新？(y/n) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "取消更新"
            exit 0
        fi
    fi
    
    # 开始更新
    log_info "开始更新..."
    echo ""
    
    # 备份
    backup_current
    echo ""
    
    # 拉取代码
    pull_code
    echo ""
    
    # 更新服务
    if command -v docker-compose &> /dev/null; then
        update_docker
    else
        update_traditional
    fi
    
    echo ""
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 10
    
    # 验证更新
    if verify_update; then
        show_result 0
        exit 0
    else
        show_result 1
        
        # 询问是否回滚
        read -p "是否回滚到上一版本？(y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rollback
        fi
        
        exit 1
    fi
}

# 运行主流程
main

