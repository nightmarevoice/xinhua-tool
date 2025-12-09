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
    echo "📁 检查数据库目录..."
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
    
    # 构建镜像
    echo "🔨 构建 Docker 镜像..."
    docker-compose build --no-cache
    
    # 启动服务
    echo "🚀 启动服务..."
    docker-compose up -d
    
    # 等待服务启动
    echo "⏳ 等待服务启动..."
    sleep 10
    
    # 检查服务状态
    echo "📊 检查服务状态..."
    docker-compose ps
    
    echo "✅ 部署完成！"
    echo "前端访问: http://localhost"
    echo "后端 API: http://localhost:8888"
    echo "Workflow-ctl API: http://localhost:8889"
    echo ""
    echo "查看日志: docker-compose logs -f"
    echo "停止服务: docker-compose down"
    
elif [ "$DEPLOY_METHOD" = "systemd" ]; then
    echo "⚙️  使用 Systemd 部署..."
    
    # 检查是否为 root 用户
    if [ "$EUID" -ne 0 ]; then 
        echo "❌ 请使用 sudo 运行此脚本以安装 systemd 服务"
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
    
    # 创建日志目录
    mkdir -p /var/log/xinhua
    mkdir -p /opt/xinhua/{backend,workflow-ctl,frontend}
    
    # 复制文件（包括数据库）
    echo "📦 复制文件..."
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
    cp deploy/systemd/xinhua-backend.service /etc/systemd/system/
    cp deploy/systemd/xinhua-workflow-ctl.service /etc/systemd/system/
    cp deploy/nginx/xinhua.conf /etc/nginx/sites-available/
    
    # 启用服务
    systemctl daemon-reload
    systemctl enable xinhua-backend
    systemctl enable xinhua-workflow-ctl
    
    # 启动服务
    systemctl start xinhua-backend
    systemctl start xinhua-workflow-ctl
    
    # 配置 Nginx
    ln -sf /etc/nginx/sites-available/xinhua.conf /etc/nginx/sites-enabled/
    nginx -t && systemctl reload nginx
    
    echo "✅ 部署完成！"
    echo "查看服务状态: systemctl status xinhua-backend xinhua-workflow-ctl"
    echo "查看日志: journalctl -u xinhua-backend -f"
    
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

