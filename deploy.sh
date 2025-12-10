#!/bin/bash

# ========================================
# 新华工具 - 优化部署脚本
# ========================================
# 使用方法: 
#   ./deploy.sh [docker|systemd] [options]
#
# 选项:
#   --with-db <file>      导入数据库备份
#   --no-cache            强制重新构建镜像
#   --production          使用生产环境配置
#   --help                显示帮助信息
# ========================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
新华工具部署脚本

使用方法:
  ./deploy.sh [docker|systemd] [options]

部署方式:
  docker          使用 Docker Compose 部署 (推荐)
  systemd         使用 Systemd 服务部署

选项:
  --with-db FILE        导入数据库备份文件
  --no-cache           强制重新构建 Docker 镜像
  --production         使用生产环境配置 (env.production)
  --skip-build         跳过镜像构建步骤
  --help               显示此帮助信息

示例:
  # Docker 部署 (开发环境)
  ./deploy.sh docker

  # Docker 部署 (生产环境)
  ./deploy.sh docker --production

  # Docker 部署并导入数据库
  ./deploy.sh docker --with-db backup.tar.gz

  # 强制重新构建
  ./deploy.sh docker --no-cache

环境配置:
  - 开发环境: 使用 env.example 创建 .env
  - 生产环境: 使用 env.production 或 --production 参数

更多信息: 查看 DEPLOYMENT.md

EOF
    exit 0
}

# 默认参数
DEPLOY_METHOD=${1:-docker}
PROJECT_NAME="xinhua-tool"
DB_ARCHIVE=""
NO_CACHE=""
USE_PRODUCTION=false
SKIP_BUILD=false

# 解析参数
shift || true
while [[ $# -gt 0 ]]; do
    case $1 in
        --with-db)
            DB_ARCHIVE="$2"
            shift 2
            ;;
        --no-cache)
            NO_CACHE="--no-cache"
            shift
            ;;
        --production)
            USE_PRODUCTION=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
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

# 显示部署信息
echo "=========================================="
log_info "开始部署 $PROJECT_NAME"
echo "部署方式: $DEPLOY_METHOD"
echo "生产模式: $USE_PRODUCTION"
[ -n "$DB_ARCHIVE" ] && echo "数据库包: $DB_ARCHIVE"
[ -n "$NO_CACHE" ] && echo "强制重建: 是"
echo "=========================================="
echo ""

# 检查环境变量文件
if [ ! -f .env ]; then
    log_warning "未找到 .env 文件"
    
    if [ "$USE_PRODUCTION" = true ] && [ -f env.production ]; then
        log_info "使用生产环境配置..."
        cp env.production .env
        log_success "已从 env.production 创建 .env"
    elif [ -f env.example ]; then
        log_info "使用开发环境配置..."
        cp env.example .env
        log_success "已从 env.example 创建 .env"
    else
        log_error "未找到环境配置模板文件 (env.example 或 env.production)"
        exit 1
    fi
    
    log_warning "请检查 .env 文件配置是否正确"
    echo ""
    sleep 2
fi

# 加载环境变量
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    log_success "已加载环境变量"
else
    log_error "无法加载 .env 文件"
    exit 1
fi

if [ "$DEPLOY_METHOD" = "docker" ]; then
    log_info "使用 Docker Compose 部署"
    echo ""
    
    # 检查 Docker 和 Docker Compose
    log_info "检查依赖..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装"
        echo "请访问: https://docs.docker.com/get-docker/"
        exit 1
    fi
    log_success "Docker 已安装"
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装"
        echo "请访问: https://docs.docker.com/compose/install/"
        exit 1
    fi
    log_success "Docker Compose 已安装"
    
    # 检查 Docker 守护进程是否运行
    if ! docker info &> /dev/null; then
        log_error "Docker 守护进程未运行"
        echo "请先启动 Docker 服务"
        exit 1
    fi
    log_success "Docker 服务运行正常"
    echo ""
    
    # 如果指定了数据库包，先导入数据库
    if [ -n "$DB_ARCHIVE" ]; then
        log_info "导入数据库..."
        if [ -f "$DB_ARCHIVE" ]; then
            if [ -f "db_migration.sh" ]; then
                chmod +x db_migration.sh
                ./db_migration.sh import "$DB_ARCHIVE"
                log_success "数据库导入完成"
            else
                log_warning "未找到 db_migration.sh 脚本，跳过数据库导入"
            fi
        else
            log_error "数据库包文件不存在: $DB_ARCHIVE"
            exit 1
        fi
        echo ""
    fi
    
    # 确保必要的目录存在
    log_info "创建必要的目录..."
    mkdir -p backend
    mkdir -p workflow-ctl/data
    mkdir -p logs/backend
    mkdir -p logs/workflow-ctl
    log_success "目录创建完成"
    echo ""
    
    # 显示数据库配置信息
    log_info "数据库配置:"
    if [[ "$BACKEND_DATABASE_URL" == *"mysql"* ]]; then
        echo "  Backend: MySQL (RDS) - ${DB_HOST}"
        echo "  Workflow-Ctl: MySQL (RDS) - ${DB_HOST}"
        log_success "使用阿里云 RDS 数据库"
    else
        echo "  Backend: SQLite - backend/app.db"
        echo "  Workflow-Ctl: SQLite - workflow-ctl/data/workflow.db"
        log_warning "使用本地 SQLite 数据库"
    fi
    echo ""
    
    # 停止旧容器并清理网络
    log_info "停止旧容器..."
    docker-compose down 2>/dev/null || true
    
    # 清理可能存在的网络冲突
    NETWORK_NAME="xinhua-tool_xinhua-network"
    if docker network ls --filter "name=${NETWORK_NAME}" -q | grep -q .; then
        log_info "清理旧网络..."
        # 获取所有连接的容器并断开
        NETWORK_ID=$(docker network ls --filter "name=${NETWORK_NAME}" -q)
        if [ -n "$NETWORK_ID" ]; then
            CONNECTED=$(docker network inspect "$NETWORK_ID" --format '{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null || echo "")
            for container in $CONNECTED; do
                docker network disconnect -f "$NETWORK_NAME" "$container" 2>/dev/null || true
            done
            docker network rm "$NETWORK_NAME" 2>/dev/null || true
        fi
    fi
    log_success "旧容器已停止，网络已清理"
    echo ""
    
    # 清理旧镜像（可选）
    if [ -n "$NO_CACHE" ]; then
        log_info "清理旧镜像..."
        docker rmi xinhua-tool-frontend:latest 2>/dev/null || true
        docker rmi xinhua-tool-backend:latest 2>/dev/null || true
        docker rmi xinhua-tool-workflow-ctl:latest 2>/dev/null || true
        log_success "镜像清理完成"
        echo ""
    fi
    
    # 构建镜像
    if [ "$SKIP_BUILD" = false ]; then
        log_info "构建 Docker 镜像（这可能需要几分钟）..."
        echo "  📦 Backend: Python 3.9 + FastAPI"
        echo "  📦 Workflow-Ctl: Python 3.9 + FastAPI"
        echo "  📦 Frontend: Node.js 18 + React + Vite"
        echo ""
        
        # 设置构建时间
        export BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
        
        if docker-compose build $NO_CACHE; then
            log_success "镜像构建成功"
        else
            log_error "镜像构建失败"
            echo "请检查错误日志或使用 --skip-build 跳过构建"
            exit 1
        fi
        echo ""
    else
        log_warning "跳过镜像构建步骤"
        echo ""
    fi
    
    # 启动服务
    log_info "启动服务..."
    if docker-compose up -d; then
        log_success "服务启动成功"
    else
        log_error "服务启动失败"
        echo ""
        log_info "显示错误日志:"
        docker-compose logs --tail=50
        exit 1
    fi
    echo ""
    
    # 等待服务启动
    log_info "等待服务健康检查（最多90秒）..."
    TIMEOUT=90
    ELAPSED=0
    HEALTHY_COUNT=0
    
    while [ $ELAPSED -lt $TIMEOUT ]; do
        HEALTHY_COUNT=$(docker-compose ps | grep -c "healthy" || echo "0")
        if [ "$HEALTHY_COUNT" -ge 3 ]; then
            log_success "所有服务健康检查通过"
            break
        fi
        sleep 3
        ELAPSED=$((ELAPSED + 3))
        echo -n "."
    done
    echo ""
    
    if [ "$HEALTHY_COUNT" -lt 3 ]; then
        log_warning "部分服务健康检查超时"
    fi
    echo ""
    
    # 检查服务状态
    log_info "服务状态:"
    docker-compose ps
    echo ""
    
    # 验证服务端点
    log_info "验证服务端点..."
    sleep 2
    
    # 检查后端健康
    if curl -sf http://localhost:8888/health > /dev/null 2>&1; then
        log_success "Backend (8888) 运行正常"
    else
        log_warning "Backend (8888) 无响应，请查看日志"
    fi
    
    # 检查 workflow-ctl 健康
    if curl -sf http://localhost:8889/health > /dev/null 2>&1; then
        log_success "Workflow-Ctl (8889) 运行正常"
    else
        log_warning "Workflow-Ctl (8889) 无响应，请查看日志"
    fi
    
    # 检查前端
    if curl -sf http://localhost:8787 > /dev/null 2>&1; then
        log_success "Frontend (8787) 运行正常"
    else
        log_warning "Frontend (8787) 无响应，请查看日志"
    fi
    
    echo ""
    echo "=========================================="
    log_success "部署完成！"
    echo "=========================================="
    echo ""
    
    # 获取服务器 IP
    SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")
    
    echo "📱 访问地址:"
    echo "  🌐 前端界面:"
    echo "     http://localhost:8787"
    echo "     http://${SERVER_IP}:8787"
    echo ""
    echo "  🔌 后端 API:"
    echo "     http://localhost:8888"
    echo "     http://localhost:8888/docs (API 文档)"
    echo ""
    echo "  ⚙️  Workflow-Ctl API:"
    echo "     http://localhost:8889"
    echo "     http://localhost:8889/docs (API 文档)"
    echo ""
    echo "📋 常用管理命令:"
    echo "  查看所有日志:    docker-compose logs -f"
    echo "  查看服务日志:    docker-compose logs -f [backend|workflow-ctl|frontend]"
    echo "  查看服务状态:    docker-compose ps"
    echo "  重启服务:        docker-compose restart"
    echo "  停止服务:        docker-compose down"
    echo "  进入容器:        docker exec -it xinhua-backend bash"
    echo ""
    echo "🔍 快捷管理脚本:"
    echo "  ./manage.sh status    - 查看服务状态"
    echo "  ./manage.sh logs      - 查看实时日志"
    echo "  ./manage.sh restart   - 重启所有服务"
    echo "  ./manage.sh backup    - 备份数据"
    echo ""
    echo "📚 更多信息: 查看 DEPLOYMENT.md"
    echo "=========================================="
    
elif [ "$DEPLOY_METHOD" = "systemd" ]; then
    echo "⚙️  使用 Systemd 部署..."
    
    # 检查是否为 root 用户
    if [ "$EUID" -ne 0 ]; then 
        echo "❌ 请使用 sudo 运行此脚本以安装 systemd 服务"
        exit 1
    fi
    
    # 检查必要的依赖
    echo "🔍 检查系统依赖..."
    MISSING_DEPS=()
    
    if ! command -v node &> /dev/null; then
        MISSING_DEPS+=("Node.js")
    fi
    
    if ! command -v npm &> /dev/null; then
        MISSING_DEPS+=("npm")
    fi
    
    if ! command -v python3 &> /dev/null; then
        MISSING_DEPS+=("Python 3")
    fi
    
    if ! command -v nginx &> /dev/null; then
        MISSING_DEPS+=("Nginx")
    fi
    
    if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
        echo "❌ 缺少以下依赖: ${MISSING_DEPS[*]}"
        echo "请先安装这些依赖后再运行部署脚本"
        exit 1
    fi
    
    echo "✅ 系统依赖检查通过"
    
    # 如果指定了数据库包，先导入数据库
    if [ -n "$DB_ARCHIVE" ]; then
        echo "📦 导入数据库..."
        if [ -f "$DB_ARCHIVE" ]; then
            chmod +x db_migration.sh
            ./db_migration.sh import "$DB_ARCHIVE"
            echo "✅ 数据库导入完成"
        else
            echo "❌ 数据库包文件不存在: $DB_ARCHIVE"
            exit 1
        fi
    fi
    
    # 构建前端
    echo "🔨 构建前端应用..."
    cd frontend
    
    if [ ! -d "node_modules" ]; then
        echo "📦 安装前端依赖..."
        npm ci --legacy-peer-deps || npm install --legacy-peer-deps
    fi
    
    echo "🏗️  编译前端代码..."
    if npm run build; then
        echo "✅ 前端构建成功"
    else
        echo "❌ 前端构建失败"
        exit 1
    fi
    
    cd ..
    
    # 检查构建产物
    if [ ! -d "frontend/dist" ]; then
        echo "❌ 前端构建产物不存在: frontend/dist"
        exit 1
    fi
    
    # 创建目录
    echo "📁 创建部署目录..."
    mkdir -p /var/log/xinhua
    mkdir -p /opt/xinhua/{backend,workflow-ctl,frontend}
    
    # 安装 Python 依赖
    echo "📦 安装后端依赖..."
    cd backend
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt
    fi
    cd ..
    
    # 安装 workflow-ctl 依赖
    echo "📦 安装 workflow-ctl 依赖..."
    cd workflow-ctl
    if [ -f "package.json" ]; then
        npm ci || npm install
    fi
    cd ..
    
    # 复制文件（包括数据库）
    echo "📦 复制应用文件..."
    cp -r backend/* /opt/xinhua/backend/
    cp -r workflow-ctl/* /opt/xinhua/workflow-ctl/
    cp -r frontend/dist/* /opt/xinhua/frontend/
    
    # 确保数据库文件已复制
    if [ -f backend/app.db ]; then
        cp backend/app.db /opt/xinhua/backend/app.db
        echo "✅ Backend 数据库已复制"
    fi
    
    if [ -f workflow-ctl/data/workflow.db ]; then
        mkdir -p /opt/xinhua/workflow-ctl/data
        cp workflow-ctl/data/workflow.db /opt/xinhua/workflow-ctl/data/workflow.db
        echo "✅ Workflow-ctl 数据库已复制"
    fi
    
    # 安装 systemd 服务文件
    echo "📝 安装 systemd 服务..."
    if [ -f "deploy/systemd/xinhua-backend.service" ]; then
        cp deploy/systemd/xinhua-backend.service /etc/systemd/system/
    else
        echo "⚠️  未找到 backend service 文件"
    fi
    
    if [ -f "deploy/systemd/xinhua-workflow-ctl.service" ]; then
        cp deploy/systemd/xinhua-workflow-ctl.service /etc/systemd/system/
    else
        echo "⚠️  未找到 workflow-ctl service 文件"
    fi
    
    # 配置 Nginx
    echo "🌐 配置 Nginx..."
    if [ -f "deploy/nginx/xinhua.conf" ]; then
        cp deploy/nginx/xinhua.conf /etc/nginx/sites-available/
        ln -sf /etc/nginx/sites-available/xinhua.conf /etc/nginx/sites-enabled/
        
        # 测试 Nginx 配置
        if nginx -t; then
            echo "✅ Nginx 配置验证通过"
        else
            echo "❌ Nginx 配置验证失败"
            exit 1
        fi
    else
        echo "⚠️  未找到 Nginx 配置文件"
    fi
    
    # 重载 systemd
    echo "🔄 重载 systemd..."
    systemctl daemon-reload
    
    # 启用并启动服务
    echo "🚀 启动服务..."
    systemctl enable xinhua-backend
    systemctl enable xinhua-workflow-ctl
    
    systemctl restart xinhua-backend
    systemctl restart xinhua-workflow-ctl
    systemctl reload nginx
    
    # 等待服务启动
    sleep 3
    
    # 检查服务状态
    echo ""
    echo "📊 检查服务状态..."
    systemctl is-active --quiet xinhua-backend && echo "✅ Backend 运行中" || echo "❌ Backend 启动失败"
    systemctl is-active --quiet xinhua-workflow-ctl && echo "✅ Workflow-ctl 运行中" || echo "❌ Workflow-ctl 启动失败"
    systemctl is-active --quiet nginx && echo "✅ Nginx 运行中" || echo "❌ Nginx 启动失败"
    
    echo ""
    echo "=========================================="
    echo "✅ 部署完成！"
    echo "=========================================="
    echo "📋 服务管理命令:"
    echo "   查看状态: systemctl status xinhua-backend xinhua-workflow-ctl"
    echo "   查看日志: journalctl -u xinhua-backend -f"
    echo "   重启服务: systemctl restart xinhua-backend"
    echo "   停止服务: systemctl stop xinhua-backend xinhua-workflow-ctl"
    echo ""
    echo "📱 访问地址:"
    echo "   前端界面: http://your-server-ip"
    echo "   后端 API: http://your-server-ip:8888"
    echo "   Workflow API: http://your-server-ip:8889"
    echo "=========================================="
    
else
    echo "❌ 未知的部署方式: $DEPLOY_METHOD"
    echo "使用方法: ./deploy.sh [docker|systemd] [--with-db <db_archive>]"
    echo ""
    echo "示例:"
    echo "  ./deploy.sh docker                           # Docker 部署（不导入数据库）"
    echo "  ./deploy.sh docker --with-db db_backup.tar.gz  # Docker 部署并导入数据库"
    echo "  ./deploy.sh systemd --with-db db_backup.tar.gz # Systemd 部署并导入数据库"
    exit 1
fi

