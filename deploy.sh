#!/bin/bash

# 部署脚本
# 使用方法: ./deploy.sh [docker|systemd] [--with-db <db_archive>]

set -e

DEPLOY_METHOD=${1:-docker}
PROJECT_NAME="xinhua"
DB_ARCHIVE=""

# 解析参数
shift
while [[ $# -gt 0 ]]; do
    case $1 in
        --with-db)
            DB_ARCHIVE="$2"
            shift 2
            ;;
        *)
            echo "未知参数: $1"
            shift
            ;;
    esac
done

echo "=========================================="
echo "开始部署 $PROJECT_NAME 项目"
echo "部署方式: $DEPLOY_METHOD"
if [ -n "$DB_ARCHIVE" ]; then
    echo "数据库包: $DB_ARCHIVE"
fi
echo "=========================================="

# 检查环境变量文件
if [ ! -f .env ]; then
    echo "⚠️  未找到 .env 文件，从 .env.example 创建..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件配置环境变量后重新运行部署脚本"
    exit 1
fi

# 加载环境变量
source .env

if [ "$DEPLOY_METHOD" = "docker" ]; then
    echo "🐳 使用 Docker Compose 部署..."
    
    # 检查 Docker 和 Docker Compose
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    # 检查 Docker 守护进程是否运行
    if ! docker info &> /dev/null; then
        echo "❌ Docker 守护进程未运行，请先启动 Docker"
        exit 1
    fi
    
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
    
    # 确保数据库目录存在
    echo "📁 创建必要的目录..."
    mkdir -p backend
    mkdir -p workflow-ctl/data
    mkdir -p logs/backend
    mkdir -p logs/workflow-ctl
    
    # 如果数据库文件不存在，创建空文件（将在启动时初始化）
    if [ ! -f backend/app.db ]; then
        echo "⚠️  Backend 数据库不存在，将在启动时初始化"
        touch backend/app.db
    fi
    
    if [ ! -f workflow-ctl/data/workflow.db ]; then
        echo "⚠️  Workflow-ctl 数据库不存在，将在启动时初始化"
        touch workflow-ctl/data/workflow.db
    fi
    
    # 停止旧容器
    echo "🛑 停止旧容器..."
    docker-compose down || true
    
    # 清理旧的前端镜像（避免缓存问题）
    echo "🧹 清理旧的镜像缓存..."
    docker rmi xinhua-tool-frontend 2>/dev/null || true
    
    # 构建镜像
    echo "🔨 构建 Docker 镜像（这可能需要几分钟）..."
    echo "   - Backend: Python FastAPI 应用"
    echo "   - Workflow-ctl: Node.js 应用"
    echo "   - Frontend: React + Vite 应用 (使用 node:18-slim)"
    echo ""
    
    if docker-compose build --no-cache; then
        echo "✅ 镜像构建成功"
    else
        echo "❌ 镜像构建失败，请检查错误日志"
        exit 1
    fi
    
    # 启动服务
    echo "🚀 启动服务..."
    if docker-compose up -d; then
        echo "✅ 服务启动成功"
    else
        echo "❌ 服务启动失败"
        docker-compose logs
        exit 1
    fi
    
    # 等待服务启动
    echo "⏳ 等待服务健康检查（最多60秒）..."
    TIMEOUT=60
    ELAPSED=0
    while [ $ELAPSED -lt $TIMEOUT ]; do
        if docker-compose ps | grep -q "Up (healthy)"; then
            echo "✅ 服务健康检查通过"
            break
        fi
        sleep 2
        ELAPSED=$((ELAPSED + 2))
        echo -n "."
    done
    echo ""
    
    # 检查服务状态
    echo "📊 检查服务状态..."
    docker-compose ps
    echo ""
    
    # 验证服务可访问性
    echo "🔍 验证服务端点..."
    sleep 3
    
    # 检查后端健康
    if curl -sf http://localhost:8888/health > /dev/null 2>&1; then
        echo "✅ Backend 健康检查通过"
    else
        echo "⚠️  Backend 健康检查失败，请查看日志"
    fi
    
    # 检查 workflow-ctl 健康
    if curl -sf http://localhost:8889/health > /dev/null 2>&1; then
        echo "✅ Workflow-ctl 健康检查通过"
    else
        echo "⚠️  Workflow-ctl 健康检查失败，请查看日志"
    fi
    
    # 检查前端
    if curl -sf http://localhost/ > /dev/null 2>&1; then
        echo "✅ Frontend 健康检查通过"
    else
        echo "⚠️  Frontend 健康检查失败，请查看日志"
    fi
    
    echo ""
    echo "=========================================="
    echo "✅ 部署完成！"
    echo "=========================================="
    echo "📱 访问地址:"
    echo "   前端界面: http://localhost"
    echo "   后端 API: http://localhost:8888"
    echo "   Workflow API: http://localhost:8889"
    echo ""
    echo "📋 常用命令:"
    echo "   查看日志: docker-compose logs -f"
    echo "   查看特定服务: docker-compose logs -f frontend"
    echo "   停止服务: docker-compose down"
    echo "   重启服务: docker-compose restart"
    echo "   查看状态: docker-compose ps"
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

