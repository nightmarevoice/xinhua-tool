#!/bin/bash

# ========================================
# 新华工具 - 一键设置脚本
# ========================================
# 自动完成部署前的所有准备工作
# ========================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
cat << "EOF"
╔═══════════════════════════════════════════╗
║                                           ║
║       新华工具 - 部署环境设置             ║
║                                           ║
╚═══════════════════════════════════════════╝
EOF
echo -e "${NC}"

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

# 步骤 1: 设置脚本执行权限
echo ""
log_info "步骤 1/5: 设置脚本执行权限..."
chmod +x deploy.sh manage.sh db_migration.sh backup.sh 2>/dev/null || true
log_success "脚本权限设置完成"

# 步骤 2: 创建必要的目录
echo ""
log_info "步骤 2/5: 创建必要的目录..."
mkdir -p backend
mkdir -p workflow-ctl/data
mkdir -p logs/backend
mkdir -p logs/workflow-ctl
mkdir -p backups
log_success "目录创建完成"

# 步骤 3: 选择环境配置
echo ""
log_info "步骤 3/5: 配置环境变量..."

if [ -f .env ]; then
    log_warning ".env 文件已存在"
    read -p "是否覆盖? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "保留现有 .env 文件"
    else
        OVERWRITE=true
    fi
else
    OVERWRITE=true
fi

if [ "$OVERWRITE" = true ]; then
    echo ""
    echo "请选择环境:"
    echo "  1) 生产环境 (使用阿里云 RDS)"
    echo "  2) 开发环境"
    echo ""
    read -p "请选择 (1/2): " -n 1 -r ENV_CHOICE
    echo ""
    
    case $ENV_CHOICE in
        1)
            if [ -f env.production ]; then
                cp env.production .env
                log_success "已创建生产环境配置"
            else
                log_error "env.production 文件不存在"
                exit 1
            fi
            ;;
        2)
            if [ -f env.example ]; then
                cp env.example .env
                log_success "已创建开发环境配置"
            else
                log_error "env.example 文件不存在"
                exit 1
            fi
            ;;
        *)
            log_error "无效的选择"
            exit 1
            ;;
    esac
fi

# 步骤 4: 检查配置
echo ""
log_info "步骤 4/5: 检查配置..."

if [ -f .env ]; then
    # 加载环境变量
    export $(grep -v '^#' .env | xargs)
    
    # 检查数据库配置
    if [[ -z "$DB_HOST" ]]; then
        log_warning "数据库配置未完成"
        echo "请编辑 .env 文件配置数据库连接"
    else
        log_success "数据库配置: $DB_HOST"
    fi
    
    # 检查 SECRET_KEY
    if [[ "$SECRET_KEY" == "79e978b8fc5cfd3166db9b270f486045ccfd6b4c2e49f12426f9819da5fe4ab2" ]]; then
        log_warning "使用默认 SECRET_KEY (生产环境请修改!)"
    else
        log_success "SECRET_KEY 已自定义"
    fi
    
    # 检查 CORS
    if [[ -n "$ALLOWED_ORIGINS" ]]; then
        log_success "CORS 配置: $ALLOWED_ORIGINS"
    else
        log_warning "CORS 未配置"
    fi
else
    log_error ".env 文件不存在"
    exit 1
fi

# 步骤 5: Docker 环境检查
echo ""
log_info "步骤 5/5: 检查 Docker 环境..."

if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | cut -d ' ' -f3 | cut -d ',' -f1)
    log_success "Docker 已安装: $DOCKER_VERSION"
    
    if docker info &> /dev/null; then
        log_success "Docker 服务运行正常"
    else
        log_error "Docker 服务未运行"
        echo "请先启动 Docker 服务"
        exit 1
    fi
else
    log_error "Docker 未安装"
    echo "请访问: https://docs.docker.com/get-docker/"
    exit 1
fi

if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version | cut -d ' ' -f4 | cut -d ',' -f1)
    log_success "Docker Compose 已安装: $COMPOSE_VERSION"
elif docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version | cut -d ' ' -f4)
    log_success "Docker Compose (plugin) 已安装: $COMPOSE_VERSION"
else
    log_error "Docker Compose 未安装"
    echo "请访问: https://docs.docker.com/compose/install/"
    exit 1
fi

# 完成
echo ""
echo "=========================================="
log_success "环境设置完成！"
echo "=========================================="
echo ""

echo -e "${GREEN}📋 配置摘要:${NC}"
echo "  环境配置: .env"
echo "  数据库: ${DB_HOST:-未配置}"
echo "  日志目录: ./logs/"
echo "  备份目录: ./backups/"
echo ""

echo -e "${CYAN}🚀 下一步操作:${NC}"
echo ""
echo "1. 检查配置 (可选):"
echo "   ${YELLOW}vim .env${NC}"
echo ""
echo "2. 开始部署:"
echo "   ${YELLOW}./deploy.sh docker${NC}"
echo ""
echo "   或生产环境部署:"
echo "   ${YELLOW}./deploy.sh docker --production${NC}"
echo ""
echo "3. 查看服务状态:"
echo "   ${YELLOW}./manage.sh status${NC}"
echo ""
echo "4. 查看帮助:"
echo "   ${YELLOW}./deploy.sh --help${NC}"
echo "   ${YELLOW}./manage.sh help${NC}"
echo ""

echo -e "${BLUE}📚 文档资源:${NC}"
echo "  完整文档: ${YELLOW}DEPLOYMENT.md${NC}"
echo "  快速参考: ${YELLOW}QUICK_REFERENCE.md${NC}"
echo "  优化说明: ${YELLOW}DEPLOYMENT_OPTIMIZATION.md${NC}"
echo ""

echo "=========================================="
echo -e "${GREEN}准备就绪，祝部署顺利！🎉${NC}"
echo "=========================================="


