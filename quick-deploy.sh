#!/bin/bash

#############################################
# 新华项目一键部署脚本
# 使用方法: ./quick-deploy.sh
#############################################

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为 root 用户
check_root() {
    if [ "$EUID" -eq 0 ]; then
        log_warn "不建议使用 root 用户运行此脚本"
        read -p "是否继续？(y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 检查系统要求
check_system() {
    log_info "检查系统要求..."
    
    # 检查操作系统
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VERSION=$VERSION_ID
        log_info "操作系统: $OS $VERSION"
    else
        log_error "无法识别的操作系统"
        exit 1
    fi
    
    # 检查内存
    TOTAL_MEM=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    if [ $TOTAL_MEM -lt 2048 ]; then
        log_warn "系统内存不足 2GB，建议至少 4GB"
    else
        log_info "内存: ${TOTAL_MEM}MB"
    fi
    
    # 检查磁盘空间
    FREE_SPACE=$(df -BG . | awk 'NR==2{print $4}' | sed 's/G//')
    if [ $FREE_SPACE -lt 20 ]; then
        log_warn "磁盘空间不足 20GB，建议至少 40GB"
    else
        log_info "可用空间: ${FREE_SPACE}GB"
    fi
}

# 安装 Docker
install_docker() {
    if command -v docker &> /dev/null; then
        log_info "Docker 已安装: $(docker --version)"
        return
    fi
    
    log_info "安装 Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    log_info "Docker 安装完成"
}

# 安装 Docker Compose
install_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        log_info "Docker Compose 已安装: $(docker-compose --version)"
        return
    fi
    
    log_info "安装 Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    log_info "Docker Compose 安装完成"
}

# 导入数据库
import_database() {
    log_info "检查是否需要导入数据库..."
    
    # 查找数据库备份文件
    DB_BACKUPS=($(ls -t xinhua_db_*.tar.gz 2>/dev/null))
    
    if [ ${#DB_BACKUPS[@]} -eq 0 ]; then
        log_info "未找到数据库备份文件，将使用空数据库"
        return
    fi
    
    echo ""
    echo "发现以下数据库备份文件:"
    for i in "${!DB_BACKUPS[@]}"; do
        SIZE=$(du -h "${DB_BACKUPS[$i]}" | cut -f1)
        echo "  [$i] ${DB_BACKUPS[$i]} ($SIZE)"
    done
    echo ""
    
    read -p "是否导入数据库？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "请选择要导入的备份 (输入编号): " -r
        if [ "$REPLY" -ge 0 ] && [ "$REPLY" -lt ${#DB_BACKUPS[@]} ]; then
            DB_FILE="${DB_BACKUPS[$REPLY]}"
            log_info "正在导入数据库: $DB_FILE"
            chmod +x db_migration.sh
            ./db_migration.sh import "$DB_FILE"
            log_info "数据库导入完成"
        else
            log_warn "无效的选择，跳过数据库导入"
        fi
    else
        log_info "跳过数据库导入"
    fi
}

# 配置环境变量
setup_env() {
    log_info "配置环境变量..."
    
    if [ -f .env ]; then
        log_warn "检测到现有 .env 文件"
        read -p "是否覆盖？(y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "跳过环境变量配置"
            return
        fi
    fi
    
    cp env.example .env
    
    # 生成随机密钥
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i "s/your-secret-key-here-change-in-production-use-random-string/$SECRET_KEY/" .env
    
    # 提示用户配置数据库
    log_warn "请配置数据库连接信息"
    echo ""
    read -p "数据库主机 (默认: localhost): " DB_HOST
    DB_HOST=${DB_HOST:-localhost}
    
    read -p "数据库端口 (默认: 3306): " DB_PORT
    DB_PORT=${DB_PORT:-3306}
    
    read -p "数据库名称 (默认: xinhua_prod): " DB_NAME
    DB_NAME=${DB_NAME:-xinhua_prod}
    
    read -p "数据库用户名: " DB_USER
    read -sp "数据库密码: " DB_PASSWORD
    echo ""
    
    # 更新 .env 文件
    sed -i "s/DB_HOST=.*/DB_HOST=$DB_HOST/" .env
    sed -i "s/DB_PORT=.*/DB_PORT=$DB_PORT/" .env
    sed -i "s/DB_NAME=.*/DB_NAME=$DB_NAME/" .env
    sed -i "s/DB_USER=.*/DB_USER=$DB_USER/" .env
    sed -i "s/DB_PASSWORD=.*/DB_PASSWORD=$DB_PASSWORD/" .env
    
    # 更新 DATABASE_URL
    sed -i "s|BACKEND_DATABASE_URL=.*|BACKEND_DATABASE_URL=mysql+pymysql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?charset=utf8mb4|" .env
    
    # 配置域名
    read -p "请输入域名 (留空则使用 localhost): " DOMAIN
    if [ -n "$DOMAIN" ]; then
        sed -i "s|ALLOWED_ORIGINS=.*|ALLOWED_ORIGINS=http://$DOMAIN,https://$DOMAIN|" .env
    fi
    
    log_info "环境变量配置完成"
}

# 创建必要目录
setup_directories() {
    log_info "创建必要目录..."
    sudo mkdir -p logs/{backend,workflow-ctl}
    sudo mkdir -p backend
    sudo mkdir -p workflow-ctl/data
    sudo mkdir -p /backup/xinhua
    sudo chmod -R 755 logs
    sudo chmod -R 755 backend
    sudo chmod -R 755 workflow-ctl/data
    
    # 确保数据库文件存在（如果没有导入）
    if [ ! -f backend/app.db ]; then
        log_info "创建空的 backend 数据库文件"
        touch backend/app.db
    fi
    
    if [ ! -f workflow-ctl/data/workflow.db ]; then
        log_info "创建空的 workflow-ctl 数据库文件"
        touch workflow-ctl/data/workflow.db
    fi
}

# 构建和启动服务
deploy_services() {
    log_info "构建 Docker 镜像..."
    docker-compose build --no-cache
    
    log_info "启动服务..."
    docker-compose up -d
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 15
    
    # 初始化数据库
    log_info "初始化数据库..."
    docker-compose exec -T backend python init_db.py || log_warn "后端数据库初始化失败，请手动执行"
    docker-compose exec -T workflow-ctl python init_db.py || log_warn "Workflow-ctl 数据库初始化失败，请手动执行"
}

# 验证部署
verify_deployment() {
    log_info "验证部署..."
    
    # 检查容器状态
    if ! docker-compose ps | grep -q "Up"; then
        log_error "某些服务未正常启动"
        docker-compose ps
        return 1
    fi
    
    # 检查后端健康
    sleep 5
    if curl -f http://localhost:8888/health &> /dev/null; then
        log_info "✓ 后端服务正常"
    else
        log_error "✗ 后端服务异常"
        return 1
    fi
    
    # 检查 workflow-ctl 健康
    if curl -f http://localhost:8889/health &> /dev/null; then
        log_info "✓ Workflow-ctl 服务正常"
    else
        log_error "✗ Workflow-ctl 服务异常"
        return 1
    fi
    
    # 检查前端
    if curl -f http://localhost/ &> /dev/null; then
        log_info "✓ 前端服务正常"
    else
        log_error "✗ 前端服务异常"
        return 1
    fi
    
    return 0
}

# 设置开机自启
setup_autostart() {
    log_info "配置开机自启..."
    
    sudo tee /etc/systemd/system/xinhua.service > /dev/null <<EOF
[Unit]
Description=Xinhua Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$(pwd)
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable xinhua.service
    log_info "开机自启配置完成"
}

# 安装备份脚本
install_backup_script() {
    log_info "安装备份脚本..."
    
    # 复制项目自带的备份脚本
    if [ -f backup.sh ]; then
        sudo cp backup.sh /opt/xinhua-backup.sh
        sudo chmod +x /opt/xinhua-backup.sh
    else
        # 创建简单的备份脚本
        sudo tee /opt/xinhua-backup.sh > /dev/null <<'EOF'
#!/bin/bash
BACKUP_DIR="/backup/xinhua"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# 备份 backend SQLite 数据库
if [ -f /opt/xinhua/backend/app.db ]; then
    cp /opt/xinhua/backend/app.db $BACKUP_DIR/backend_app_$DATE.db
fi

# 备份 workflow-ctl SQLite 数据库
if [ -f /opt/xinhua/workflow-ctl/data/workflow.db ]; then
    cp /opt/xinhua/workflow-ctl/data/workflow.db $BACKUP_DIR/workflow_db_$DATE.db
fi

# 备份日志
tar czf $BACKUP_DIR/logs_$DATE.tar.gz /opt/xinhua/logs/ 2>/dev/null || true

# 备份配置
if [ -f /opt/xinhua/.env ]; then
    cp /opt/xinhua/.env $BACKUP_DIR/env_$DATE.txt
fi

# 删除30天前的备份
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: $DATE"
EOF
        sudo chmod +x /opt/xinhua-backup.sh
    fi
    
    sudo chmod +x /opt/xinhua-backup.sh
    
    # 添加到 crontab
    (crontab -l 2>/dev/null; echo "0 2 * * * /opt/xinhua-backup.sh") | crontab -
    log_info "备份脚本已安装（每天凌晨2点自动备份）"
}

# 显示部署信息
show_deployment_info() {
    echo ""
    echo "=========================================="
    log_info "部署完成！"
    echo "=========================================="
    echo ""
    echo "访问地址:"
    echo "  前端: http://localhost 或 http://$(hostname -I | awk '{print $1}')"
    echo "  后端 API: http://localhost:8888"
    echo "  Workflow-ctl API: http://localhost:8889"
    echo ""
    echo "常用命令:"
    echo "  查看服务状态: docker-compose ps"
    echo "  查看日志: docker-compose logs -f"
    echo "  重启服务: docker-compose restart"
    echo "  停止服务: docker-compose down"
    echo ""
    echo "文档:"
    echo "  完整部署指南: PRODUCTION_DEPLOYMENT.md"
    echo "  数据库迁移指南: DATABASE_MIGRATION_GUIDE.md"
    echo "  API 文档: docs/API.md"
    echo ""
    echo "备份:"
    echo "  自动备份位置: /backup/xinhua/"
    echo "  手动备份: /opt/xinhua-backup.sh"
    echo "  导出数据库: ./db_migration.sh export"
    echo ""
    echo "数据库管理:"
    echo "  导出数据库: ./db_migration.sh export"
    echo "  导入数据库: ./db_migration.sh import <file>"
    echo "  验证数据库: ./db_migration.sh verify"
    echo ""
    echo "=========================================="
}

# 主流程
main() {
    echo "=========================================="
    echo "      新华项目一键部署脚本"
    echo "=========================================="
    echo ""
    
    check_root
    check_system
    
    # 安装依赖
    install_docker
    install_docker_compose
    
    # 配置项目
    setup_env
    import_database
    setup_directories
    
    # 部署服务
    deploy_services
    
    # 验证部署
    if verify_deployment; then
        setup_autostart
        install_backup_script
        show_deployment_info
    else
        log_error "部署验证失败，请检查日志"
        echo "查看日志: docker-compose logs"
        exit 1
    fi
}

# 运行主流程
main

