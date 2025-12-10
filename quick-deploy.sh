#!/bin/bash

# ========================================
# 新华工具 - 快速部署脚本 (智能构建)
# ========================================
# 此脚本会检测代码变化，只在必要时重新构建镜像
# 适用于日常开发和快速迭代
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
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_step() { echo -e "${CYAN}➜ $1${NC}"; }

# 帮助信息
show_help() {
    cat << EOF
快速部署脚本 - 智能构建

使用方法:
  ./quick-deploy.sh [options]

选项:
  --force, -f          强制重新构建所有镜像
  --rebuild SERVICE    只重新构建指定服务 (backend/frontend/workflow-ctl)
  --skip-build         跳过构建，直接启动
  --production, -p     使用生产环境配置
  --help, -h           显示此帮助信息

示例:
  # 智能部署（推荐）
  ./quick-deploy.sh

  # 只重新构建前端
  ./quick-deploy.sh --rebuild frontend

  # 强制重新构建所有服务
  ./quick-deploy.sh --force

  # 跳过构建，快速重启
  ./quick-deploy.sh --skip-build

特性:
  ✅ 智能检测依赖文件变化（requirements.txt, package.json）
  ✅ 利用 Docker BuildKit 缓存加速构建
  ✅ 支持选择性重新构建单个服务
  ✅ 自动检查服务健康状态

EOF
    exit 0
}

# 默认参数
FORCE_BUILD=false
SKIP_BUILD=false
USE_PRODUCTION=false
REBUILD_SERVICE=""
BUILD_SERVICES=""

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --force|-f)
            FORCE_BUILD=true
            shift
            ;;
        --rebuild)
            REBUILD_SERVICE="$2"
            shift 2
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --production|-p)
            USE_PRODUCTION=true
            shift
            ;;
        --help|-h)
            show_help
            ;;
        *)
            log_error "未知参数: $1"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

# 检查环境变量文件
if [ ! -f .env ]; then
    if [ "$USE_PRODUCTION" = true ] && [ -f env.production ]; then
        log_info "使用生产环境配置"
        cp env.production .env
    elif [ -f env.example ]; then
        log_info "使用开发环境配置"
        cp env.example .env
    else
        log_error "未找到环境配置文件"
        exit 1
    fi
fi

# 显示标题
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║     新华工具 - 快速部署 (智能构建)      ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# 检查 Docker
log_step "检查 Docker 环境..."
if ! command -v docker &> /dev/null; then
    log_error "Docker 未安装"
    exit 1
fi

if ! docker info &> /dev/null; then
    log_error "Docker 守护进程未运行"
    exit 1
fi
log_success "Docker 环境正常"
echo ""

# 启用 BuildKit（加速构建）
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
log_info "已启用 Docker BuildKit (构建加速)"
echo ""

# 函数：检查文件是否变化
file_changed() {
    local file=$1
    local cache_file=".build_cache/${file//\//_}.md5"
    
    mkdir -p .build_cache
    
    if [ ! -f "$file" ]; then
        return 1  # 文件不存在
    fi
    
    local current_md5=$(md5sum "$file" 2>/dev/null | awk '{print $1}')
    
    if [ ! -f "$cache_file" ]; then
        echo "$current_md5" > "$cache_file"
        return 0  # 首次构建
    fi
    
    local cached_md5=$(cat "$cache_file")
    
    if [ "$current_md5" != "$cached_md5" ]; then
        echo "$current_md5" > "$cache_file"
        return 0  # 文件已变化
    fi
    
    return 1  # 文件未变化
}

# 函数：检查服务是否需要重新构建
should_rebuild() {
    local service=$1
    
    # 强制构建
    if [ "$FORCE_BUILD" = true ]; then
        return 0
    fi
    
    # 指定服务重建
    if [ -n "$REBUILD_SERVICE" ] && [ "$REBUILD_SERVICE" = "$service" ]; then
        return 0
    fi
    
    # 检查依赖文件
    case $service in
        backend)
            if file_changed "backend/requirements.txt" || file_changed "backend/Dockerfile"; then
                log_info "检测到 backend 依赖或配置变化"
                return 0
            fi
            ;;
        workflow-ctl)
            if file_changed "workflow-ctl/requirements.txt" || file_changed "workflow-ctl/Dockerfile"; then
                log_info "检测到 workflow-ctl 依赖或配置变化"
                return 0
            fi
            ;;
        frontend)
            if file_changed "frontend/package.json" || file_changed "frontend/Dockerfile"; then
                log_info "检测到 frontend 依赖或配置变化"
                return 0
            fi
            ;;
    esac
    
    # 检查镜像是否存在
    if ! docker images | grep -q "xinhua-tool-${service}"; then
        log_info "${service} 镜像不存在，需要构建"
        return 0
    fi
    
    return 1  # 不需要重新构建
}

# 确定需要构建的服务
if [ "$SKIP_BUILD" = false ]; then
    log_step "分析构建需求..."
    
    if [ "$FORCE_BUILD" = true ]; then
        log_warning "强制重新构建所有服务"
        BUILD_SERVICES="backend frontend workflow-ctl"
    elif [ -n "$REBUILD_SERVICE" ]; then
        log_info "指定重新构建服务: $REBUILD_SERVICE"
        BUILD_SERVICES="$REBUILD_SERVICE"
    else
        # 智能检测
        for service in backend frontend workflow-ctl; do
            if should_rebuild "$service"; then
                BUILD_SERVICES="$BUILD_SERVICES $service"
            fi
        done
        
        if [ -z "$BUILD_SERVICES" ]; then
            log_success "所有服务都是最新的，无需重新构建"
        else
            log_info "需要重新构建的服务: $BUILD_SERVICES"
        fi
    fi
    echo ""
fi

# 停止旧容器
log_step "停止旧容器..."
docker-compose down 2>/dev/null || true
log_success "已停止旧容器"
echo ""

# 构建服务
if [ "$SKIP_BUILD" = false ] && [ -n "$BUILD_SERVICES" ]; then
    log_step "开始构建服务..."
    
    for service in $BUILD_SERVICES; do
        log_info "正在构建 $service..."
        
        # 记录开始时间
        START_TIME=$(date +%s)
        
        # 构建镜像
        docker-compose build $service
        
        # 计算耗时
        END_TIME=$(date +%s)
        DURATION=$((END_TIME - START_TIME))
        
        log_success "$service 构建完成 (耗时: ${DURATION}s)"
    done
    
    echo ""
else
    log_info "跳过构建步骤"
    echo ""
fi

# 启动服务
log_step "启动服务..."
docker-compose up -d

log_success "服务启动中..."
echo ""

# 等待服务就绪
log_step "等待服务就绪..."
echo "这可能需要 30-60 秒，请稍候..."
echo ""

sleep 15  # 初始等待

# 检查服务健康状态
check_health() {
    local max_attempts=20
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        attempt=$((attempt + 1))
        
        # 检查容器状态
        backend_status=$(docker inspect -f '{{.State.Health.Status}}' xinhua-backend 2>/dev/null || echo "unknown")
        workflow_status=$(docker inspect -f '{{.State.Health.Status}}' xinhua-workflow-ctl 2>/dev/null || echo "unknown")
        frontend_status=$(docker inspect -f '{{.State.Status}}' xinhua-frontend 2>/dev/null || echo "unknown")
        
        echo -ne "\r尝试 $attempt/$max_attempts: Backend[$backend_status] WorkflowCtl[$workflow_status] Frontend[$frontend_status]"
        
        # 检查是否所有服务都健康
        if [ "$backend_status" = "healthy" ] && \
           [ "$workflow_status" = "healthy" ] && \
           [ "$frontend_status" = "running" ]; then
            echo ""
            return 0
        fi
        
        sleep 3
    done
    
    echo ""
    return 1
}

if check_health; then
    echo ""
    log_success "所有服务已就绪！"
else
    echo ""
    log_warning "部分服务可能未就绪，请检查日志"
    echo ""
    log_info "查看日志: ./manage.sh logs"
fi

    echo ""
echo "╔══════════════════════════════════════════╗"
echo "║            部署完成！                     ║"
echo "╚══════════════════════════════════════════╝"
    echo ""
echo "📌 访问地址:"
echo "   前端:     http://localhost:8787"
echo "   后端 API: http://localhost:8888/docs"
echo "   工作流:   http://localhost:8889/docs"
    echo ""
echo "🔧 管理命令:"
echo "   查看状态: ./manage.sh status"
echo "   查看日志: ./manage.sh logs"
echo "   健康检查: ./manage.sh health"
    echo ""
echo "💡 提示:"
if [ -n "$BUILD_SERVICES" ]; then
    echo "   本次重新构建了: $BUILD_SERVICES"
else
    echo "   本次使用了缓存的镜像，构建速度很快"
fi
echo "   下次部署会自动检测变化，只在必要时重新构建"
echo ""


