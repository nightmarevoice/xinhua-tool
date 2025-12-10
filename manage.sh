#!/bin/bash

# ========================================
# 新华工具 - 服务管理脚本
# ========================================
# 快捷管理 Docker Compose 服务
# ========================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 显示帮助
show_help() {
    cat << EOF
${CYAN}新华工具服务管理脚本${NC}

${GREEN}使用方法:${NC}
  ./manage.sh <command> [options]

${GREEN}命令列表:${NC}

  ${CYAN}服务控制:${NC}
    start              启动所有服务
    stop               停止所有服务
    restart [service]  重启服务 (不指定则重启所有)
    status             查看服务状态
    health             健康检查

  ${CYAN}日志管理:${NC}
    logs [service]     查看实时日志 (不指定则查看所有)
    logs-tail N        查看最后 N 行日志
    logs-error         查看错误日志

  ${CYAN}容器管理:${NC}
    ps                 查看容器状态
    top                查看容器资源占用
    exec <service>     进入容器 Shell
    rebuild [service]  重新构建镜像

  ${CYAN}数据管理:${NC}
    backup             备份数据库和日志
    clean-logs         清理旧日志文件
    db-migrate         运行数据库迁移

  ${CYAN}网络诊断:${NC}
    test-network       测试容器网络连接
    test-db            测试数据库连接
    test-api           测试 API 端点

  ${CYAN}构建缓存:${NC}
    cache-info         查看 Docker 构建缓存使用情况
    cache-clean        清理 Docker 构建缓存
    cache-prune        智能清理（保留最近使用的缓存）

  ${CYAN}其他:${NC}
    update             拉取最新代码并重新部署
    clean              清理未使用的镜像和容器
    help               显示此帮助信息

${GREEN}示例:${NC}
  ./manage.sh status              # 查看服务状态
  ./manage.sh logs backend        # 查看后端日志
  ./manage.sh restart frontend    # 重启前端服务
  ./manage.sh exec backend        # 进入后端容器
  ./manage.sh backup              # 备份数据

EOF
    exit 0
}

# 检查 Docker Compose 是否可用
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker 守护进程未运行"
        exit 1
    fi
}

# 启动服务
cmd_start() {
    log_info "启动所有服务..."
    docker-compose up -d
    log_success "服务启动成功"
    sleep 3
    cmd_status
}

# 停止服务
cmd_stop() {
    log_info "停止所有服务..."
    docker-compose down
    log_success "服务已停止"
}

# 重启服务
cmd_restart() {
    local service=$1
    if [ -z "$service" ]; then
        log_info "重启所有服务..."
        docker-compose restart
        log_success "所有服务已重启"
    else
        log_info "重启服务: $service"
        docker-compose restart "$service"
        log_success "$service 已重启"
    fi
    sleep 2
    cmd_status
}

# 查看服务状态
cmd_status() {
    echo ""
    log_info "服务状态:"
    echo "----------------------------------------"
    docker-compose ps
    echo ""
    
    log_info "健康状态:"
    echo "----------------------------------------"
    for service in backend workflow-ctl frontend; do
        container="xinhua-${service}"
        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            health=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "unknown")
            if [ "$health" = "healthy" ]; then
                echo -e "  ${service}: ${GREEN}✅ healthy${NC}"
            elif [ "$health" = "unhealthy" ]; then
                echo -e "  ${service}: ${RED}❌ unhealthy${NC}"
            else
                echo -e "  ${service}: ${YELLOW}⏳ starting${NC}"
            fi
        else
            echo -e "  ${service}: ${RED}⚠️  stopped${NC}"
        fi
    done
    echo ""
}

# 健康检查
cmd_health() {
    log_info "执行健康检查..."
    echo ""
    
    # 检查后端
    if curl -sf http://localhost:8888/health > /dev/null 2>&1; then
        echo -e "  Backend (8888):      ${GREEN}✅ OK${NC}"
    else
        echo -e "  Backend (8888):      ${RED}❌ FAIL${NC}"
    fi
    
    # 检查 workflow-ctl
    if curl -sf http://localhost:8889/health > /dev/null 2>&1; then
        echo -e "  Workflow-Ctl (8889): ${GREEN}✅ OK${NC}"
    else
        echo -e "  Workflow-Ctl (8889): ${RED}❌ FAIL${NC}"
    fi
    
    # 检查前端
    if curl -sf http://localhost:8787 > /dev/null 2>&1; then
        echo -e "  Frontend (8787):     ${GREEN}✅ OK${NC}"
    else
        echo -e "  Frontend (8787):     ${RED}❌ FAIL${NC}"
    fi
    echo ""
}

# 查看日志
cmd_logs() {
    local service=$1
    if [ -z "$service" ]; then
        log_info "查看所有服务日志 (Ctrl+C 退出)"
        docker-compose logs -f
    else
        log_info "查看 $service 日志 (Ctrl+C 退出)"
        docker-compose logs -f "$service"
    fi
}

# 查看最后 N 行日志
cmd_logs_tail() {
    local lines=${1:-100}
    log_info "查看最后 $lines 行日志"
    docker-compose logs --tail="$lines"
}

# 查看错误日志
cmd_logs_error() {
    log_info "查看错误日志"
    docker-compose logs | grep -i "error\|exception\|fail" || echo "未发现错误"
}

# 查看容器状态
cmd_ps() {
    docker-compose ps
}

# 查看资源占用
cmd_top() {
    log_info "容器资源占用:"
    docker stats --no-stream xinhua-backend xinhua-workflow-ctl xinhua-frontend 2>/dev/null || log_warning "部分容器未运行"
}

# 进入容器
cmd_exec() {
    local service=$1
    if [ -z "$service" ]; then
        log_error "请指定服务名: backend, workflow-ctl, frontend"
        exit 1
    fi
    
    local container="xinhua-${service}"
    log_info "进入容器: $container"
    docker exec -it "$container" /bin/bash || docker exec -it "$container" /bin/sh
}

# 重新构建镜像
cmd_rebuild() {
    local service=$1
    if [ -z "$service" ]; then
        log_info "重新构建所有镜像..."
        docker-compose build --no-cache
    else
        log_info "重新构建 $service 镜像..."
        docker-compose build --no-cache "$service"
    fi
    log_success "镜像构建完成"
    log_info "重启服务..."
    cmd_restart "$service"
}

# 备份数据
cmd_backup() {
    log_info "开始备份..."
    
    BACKUP_DIR="./backups"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.tar.gz"
    
    mkdir -p "$BACKUP_DIR"
    
    # 备份日志和数据
    tar -czf "$BACKUP_FILE" \
        logs/ \
        backend/app.db \
        workflow-ctl/data/ \
        .env \
        2>/dev/null || true
    
    if [ -f "$BACKUP_FILE" ]; then
        log_success "备份完成: $BACKUP_FILE"
        ls -lh "$BACKUP_FILE"
    else
        log_error "备份失败"
        exit 1
    fi
}

# 清理日志
cmd_clean_logs() {
    log_warning "清理旧日志文件..."
    
    # 保留最近7天的日志
    find logs/ -type f -name "*.log" -mtime +7 -delete 2>/dev/null || true
    
    # 清理 Docker 日志
    docker-compose logs --tail=0 > /dev/null 2>&1 || true
    
    log_success "日志清理完成"
}

# 数据库迁移
cmd_db_migrate() {
    log_info "运行数据库迁移..."
    
    # Backend 迁移
    docker exec xinhua-backend alembic upgrade head 2>/dev/null || log_warning "Backend 迁移失败或无需迁移"
    
    # Workflow-ctl 迁移
    docker exec xinhua-workflow-ctl alembic upgrade head 2>/dev/null || log_warning "Workflow-ctl 迁移失败或无需迁移"
    
    log_success "数据库迁移完成"
}

# 测试网络
cmd_test_network() {
    log_info "测试容器网络连接..."
    echo ""
    
    # 测试前端到后端
    docker exec xinhua-frontend wget -q -O- http://backend:8888/health > /dev/null 2>&1 && \
        echo -e "  Frontend -> Backend:      ${GREEN}✅${NC}" || \
        echo -e "  Frontend -> Backend:      ${RED}❌${NC}"
    
    # 测试前端到 workflow-ctl
    docker exec xinhua-frontend wget -q -O- http://workflow-ctl:8889/health > /dev/null 2>&1 && \
        echo -e "  Frontend -> Workflow-Ctl: ${GREEN}✅${NC}" || \
        echo -e "  Frontend -> Workflow-Ctl: ${RED}❌${NC}"
    
    echo ""
}

# 测试数据库连接
cmd_test_db() {
    log_info "测试数据库连接..."
    
    # 从环境变量读取数据库配置
    if [ -f .env ]; then
        export $(grep -v '^#' .env | xargs)
    fi
    
    if [[ "$BACKEND_DATABASE_URL" == *"mysql"* ]]; then
        echo "  数据库类型: MySQL (RDS)"
        echo "  主机: $DB_HOST"
        echo "  数据库: $DB_NAME"
        echo ""
        
        # 测试后端数据库连接
        docker exec xinhua-backend python -c "
import pymysql
import os
try:
    conn = pymysql.connect(
        host='$DB_HOST',
        port=int('$DB_PORT'),
        user='$DB_USER',
        password='$DB_PASSWORD',
        database='$DB_NAME'
    )
    conn.close()
    print('✅ Backend 数据库连接成功')
except Exception as e:
    print(f'❌ Backend 数据库连接失败: {e}')
" 2>/dev/null || log_error "无法测试数据库连接"
    else
        echo "  数据库类型: SQLite"
        echo "  Backend: backend/app.db"
        echo "  Workflow-Ctl: workflow-ctl/data/workflow.db"
    fi
    echo ""
}

# 测试 API
cmd_test_api() {
    log_info "测试 API 端点..."
    echo ""
    
    # 测试后端 API
    echo "📡 Backend API:"
    curl -s http://localhost:8888/health | head -n 5 || log_error "Backend API 无响应"
    echo ""
    
    # 测试 Workflow-Ctl API
    echo "📡 Workflow-Ctl API:"
    curl -s http://localhost:8889/health | head -n 5 || log_error "Workflow-Ctl API 无响应"
    echo ""
}

# 更新部署
cmd_update() {
    log_info "更新部署..."
    
    # 备份当前数据
    cmd_backup
    
    # 停止服务
    cmd_stop
    
    # 拉取最新代码 (如果是 git 仓库)
    if [ -d .git ]; then
        log_info "拉取最新代码..."
        git pull
    fi
    
    # 重新构建并启动
    log_info "重新构建镜像..."
    docker-compose build --no-cache
    
    log_info "启动服务..."
    cmd_start
    
    log_success "更新完成"
}

# 清理
# 查看构建缓存信息
cmd_cache_info() {
    log_info "Docker 磁盘使用情况:"
    echo ""
    docker system df -v
    echo ""
    
    log_info "构建缓存详情:"
    echo ""
    if command -v docker buildx &> /dev/null; then
        docker buildx du
    else
        log_warning "未安装 docker buildx，无法查看构建缓存详情"
    fi
    echo ""
    
    log_info "镜像列表:"
    echo ""
    docker images | grep -E "xinhua-tool|REPOSITORY"
}

# 清理构建缓存
cmd_cache_clean() {
    log_warning "即将清理所有 Docker 构建缓存"
    echo "这将删除:"
    echo "  - 所有构建缓存层"
    echo "  - pip 和 npm 缓存挂载"
    echo "  - 未使用的构建镜像"
    echo ""
    read -p "确认清理？[y/N] " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "清理构建缓存..."
        
        # 清理构建缓存
        docker builder prune -a -f
        
        # 清理构建缓存目录
        rm -rf .build_cache
        
        log_success "构建缓存清理完成"
        echo ""
        log_info "下次构建将重新下载所有依赖"
    else
        log_info "已取消清理操作"
    fi
}

# 智能清理缓存（保留最近使用的）
cmd_cache_prune() {
    log_info "智能清理构建缓存..."
    echo "将保留最近使用的缓存（10GB）"
    echo ""
    
    # 查看当前缓存大小
    log_info "当前缓存使用:"
    if command -v docker buildx &> /dev/null; then
        docker buildx du
    fi
    echo ""
    
    read -p "继续清理？[Y/n] " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        log_info "执行智能清理..."
        
        # 保留 10GB 的缓存
        docker builder prune --keep-storage 10GB -f
        
        log_success "智能清理完成"
        echo ""
        
        log_info "清理后缓存使用:"
        if command -v docker buildx &> /dev/null; then
            docker buildx du
        fi
    else
        log_info "已取消清理操作"
    fi
}

cmd_clean() {
    log_warning "清理未使用的 Docker 资源..."
    
    # 清理停止的容器
    docker container prune -f
    
    # 清理未使用的镜像
    docker image prune -f
    
    # 清理未使用的网络
    docker network prune -f
    
    # 清理未使用的卷
    docker volume prune -f
    
    log_success "清理完成"
}

# 主函数
main() {
    if [ $# -eq 0 ]; then
        show_help
    fi
    
    check_docker
    
    case "$1" in
        start)
            cmd_start
            ;;
        stop)
            cmd_stop
            ;;
        restart)
            cmd_restart "$2"
            ;;
        status)
            cmd_status
            ;;
        health)
            cmd_health
            ;;
        logs)
            cmd_logs "$2"
            ;;
        logs-tail)
            cmd_logs_tail "$2"
            ;;
        logs-error)
            cmd_logs_error
            ;;
        ps)
            cmd_ps
            ;;
        top)
            cmd_top
            ;;
        exec)
            cmd_exec "$2"
            ;;
        rebuild)
            cmd_rebuild "$2"
            ;;
        backup)
            cmd_backup
            ;;
        clean-logs)
            cmd_clean_logs
            ;;
        db-migrate)
            cmd_db_migrate
            ;;
        test-network)
            cmd_test_network
            ;;
        test-db)
            cmd_test_db
            ;;
        test-api)
            cmd_test_api
            ;;
        cache-info)
            cmd_cache_info
            ;;
        cache-clean)
            cmd_cache_clean
            ;;
        cache-prune)
            cmd_cache_prune
            ;;
        update)
            cmd_update
            ;;
        clean)
            cmd_clean
            ;;
        help|-h|--help)
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            echo "使用 './manage.sh help' 查看帮助"
            exit 1
            ;;
    esac
}

main "$@"

