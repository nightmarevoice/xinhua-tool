#!/bin/bash

#############################################
# 一键导出数据库并远程部署脚本
# 使用方法: ./export_and_deploy.sh [remote_host]
#############################################

set -e

# 配置
REMOTE_HOST="${1}"
REMOTE_USER="${2:-root}"
REMOTE_PATH="${3:-/opt/xinhua-tool}"
DEPLOY_METHOD="${4:-docker}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} [$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} [$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} [$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat <<EOF
一键导出数据库并远程部署脚本

使用方法: 
  $0 <remote_host> [remote_user] [remote_path] [deploy_method]

参数说明:
  remote_host    远程服务器地址 (必需)
  remote_user    远程服务器用户 (默认: root)
  remote_path    远程部署路径 (默认: /opt/xinhua-tool)
  deploy_method  部署方式 (docker|systemd, 默认: docker)

示例:
  $0 192.168.1.100                           # 使用默认参数
  $0 192.168.1.100 ubuntu /home/ubuntu/app   # 自定义用户和路径
  $0 192.168.1.100 root /opt/app systemd     # 使用 systemd 部署

注意:
  - 需要配置 SSH 密钥认证或在执行时输入密码
  - 远程服务器需要已安装 Docker 或相关依赖
  - 建议先在测试环境验证

EOF
}

# 检查参数
check_params() {
    if [ -z "$REMOTE_HOST" ]; then
        log_error "请指定远程服务器地址"
        show_help
        exit 1
    fi
    
    log_info "部署配置:"
    echo "  远程主机: $REMOTE_HOST"
    echo "  远程用户: $REMOTE_USER"
    echo "  部署路径: $REMOTE_PATH"
    echo "  部署方式: $DEPLOY_METHOD"
    echo ""
    
    read -p "确认以上配置？(yes/no) " -r
    if [ "$REPLY" != "yes" ]; then
        log_info "取消部署"
        exit 0
    fi
}

# 检查 SSH 连接
check_ssh() {
    log_step "检查 SSH 连接..."
    
    if ! ssh -o ConnectTimeout=5 -o BatchMode=yes "$REMOTE_USER@$REMOTE_HOST" "echo 'SSH connection OK'" &>/dev/null; then
        log_warn "SSH 密钥认证失败，将需要输入密码"
        
        # 测试密码登录
        if ! ssh -o ConnectTimeout=5 "$REMOTE_USER@$REMOTE_HOST" "echo 'SSH connection OK'" </dev/null; then
            log_error "无法连接到远程服务器"
            exit 1
        fi
    fi
    
    log_info "✅ SSH 连接正常"
}

# 导出数据库
export_database() {
    log_step "正在导出数据库..."
    
    # 给脚本添加执行权限
    chmod +x db_migration.sh
    
    # 导出数据库
    ./db_migration.sh export
    
    # 获取最新的数据库包文件
    DB_FILE=$(ls -t xinhua_db_*.tar.gz | head -1)
    
    if [ -z "$DB_FILE" ]; then
        log_error "数据库导出失败"
        exit 1
    fi
    
    log_info "✅ 数据库已导出: $DB_FILE"
    
    # 显示文件信息
    local size=$(du -h "$DB_FILE" | cut -f1)
    log_info "文件大小: $size"
    
    echo "$DB_FILE"
}

# 传输文件到远程服务器
transfer_files() {
    local db_file=$1
    
    log_step "正在传输文件到远程服务器..."
    
    # 在远程服务器上创建目录
    ssh "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_PATH"
    
    # 传输数据库包
    log_info "传输数据库包..."
    scp "$db_file" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
    
    # 传输必要的脚本
    log_info "传输部署脚本..."
    scp db_migration.sh "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
    scp deploy.sh "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
    
    # 如果存在 .env 文件，也传输过去
    if [ -f .env ]; then
        log_info "传输环境配置文件..."
        scp .env "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
    fi
    
    log_info "✅ 文件传输完成"
}

# 在远程服务器上执行部署
remote_deploy() {
    local db_file=$1
    
    log_step "在远程服务器上执行部署..."
    
    ssh "$REMOTE_USER@$REMOTE_HOST" << EOF
        set -e
        cd $REMOTE_PATH
        
        echo "=========================================="
        echo "开始远程部署"
        echo "=========================================="
        
        # 给脚本添加执行权限
        chmod +x db_migration.sh deploy.sh
        
        # 导入数据库并部署
        ./deploy.sh $DEPLOY_METHOD --with-db $(basename $db_file)
        
        echo "=========================================="
        echo "远程部署完成"
        echo "=========================================="
EOF
    
    if [ $? -eq 0 ]; then
        log_info "✅ 远程部署成功"
    else
        log_error "❌ 远程部署失败"
        exit 1
    fi
}

# 验证部署
verify_remote_deployment() {
    log_step "验证远程部署..."
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 10
    
    # 检查服务状态
    if [ "$DEPLOY_METHOD" = "docker" ]; then
        ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_PATH && docker-compose ps"
    elif [ "$DEPLOY_METHOD" = "systemd" ]; then
        ssh "$REMOTE_USER@$REMOTE_HOST" "systemctl status xinhua-backend xinhua-workflow-ctl --no-pager"
    fi
    
    # 检查健康端点
    log_info "检查服务健康状态..."
    
    # 后端健康检查
    if ssh "$REMOTE_USER@$REMOTE_HOST" "curl -f http://localhost:8888/health" &>/dev/null; then
        log_info "✅ 后端服务正常"
    else
        log_warn "⚠️  后端服务可能未正常启动"
    fi
    
    # Workflow-ctl 健康检查
    if ssh "$REMOTE_USER@$REMOTE_HOST" "curl -f http://localhost:8889/health" &>/dev/null; then
        log_info "✅ Workflow-ctl 服务正常"
    else
        log_warn "⚠️  Workflow-ctl 服务可能未正常启动"
    fi
    
    # 前端健康检查
    if ssh "$REMOTE_USER@$REMOTE_HOST" "curl -f http://localhost/" &>/dev/null; then
        log_info "✅ 前端服务正常"
    else
        log_warn "⚠️  前端服务可能未正常启动"
    fi
}

# 显示部署结果
show_result() {
    echo ""
    echo "=========================================="
    echo "          部署完成！"
    echo "=========================================="
    echo ""
    echo "远程服务器信息:"
    echo "  主机: $REMOTE_HOST"
    echo "  路径: $REMOTE_PATH"
    echo ""
    echo "访问地址:"
    echo "  前端: http://$REMOTE_HOST"
    echo "  后端 API: http://$REMOTE_HOST:8888"
    echo "  Workflow-ctl API: http://$REMOTE_HOST:8889"
    echo ""
    echo "管理命令:"
    echo "  登录服务器: ssh $REMOTE_USER@$REMOTE_HOST"
    echo "  查看日志: ssh $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_PATH && docker-compose logs -f'"
    echo "  重启服务: ssh $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_PATH && docker-compose restart'"
    echo ""
    echo "本地数据库备份: $(ls -t xinhua_db_*.tar.gz | head -1)"
    echo ""
    echo "=========================================="
}

# 主函数
main() {
    echo "=========================================="
    echo "  一键导出数据库并远程部署"
    echo "=========================================="
    echo ""
    
    # 检查参数
    check_params
    
    # 检查 SSH 连接
    check_ssh
    
    # 导出数据库
    DB_FILE=$(export_database)
    
    # 传输文件
    transfer_files "$DB_FILE"
    
    # 远程部署
    remote_deploy "$DB_FILE"
    
    # 验证部署
    verify_remote_deployment
    
    # 显示结果
    show_result
    
    log_info "✅ 所有操作完成！"
}

# 运行主函数
if [ "$1" = "help" ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

main

