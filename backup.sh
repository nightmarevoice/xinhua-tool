#!/bin/bash

#############################################
# 数据备份脚本
# 使用方法: ./backup.sh [full|quick]
# 配合 crontab 使用: 0 2 * * * /opt/xinhua/backup.sh full
#############################################

# 配置
BACKUP_DIR="/backup/xinhua"
RETENTION_DAYS=30  # 保留天数
S3_BUCKET=""  # 可选：S3 存储桶名称
OSS_BUCKET=""  # 可选：阿里云 OSS 存储桶名称

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# 检查依赖
check_dependencies() {
    local missing_deps=()
    
    if ! command -v mysqldump &> /dev/null; then
        missing_deps+=("mysqldump")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_warn "缺少依赖: ${missing_deps[*]}"
        log_info "安装: sudo apt install mysql-client"
    fi
}

# 创建备份目录
prepare_backup_dir() {
    local date_dir="$BACKUP_DIR/$(date +%Y%m%d)"
    mkdir -p "$date_dir"
    echo "$date_dir"
}

# 备份 MySQL 数据库
backup_mysql() {
    local backup_dir="$1"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    
    log_info "开始备份 MySQL 数据库..."
    
    # 从 .env 读取配置
    if [ ! -f .env ]; then
        log_error ".env 文件不存在"
        return 1
    fi
    
    source .env
    
    if [ -z "$DB_HOST" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ] || [ -z "$DB_NAME" ]; then
        log_warn "数据库配置不完整，跳过 MySQL 备份"
        return 0
    fi
    
    # 备份数据库
    local backup_file="$backup_dir/mysql_${DB_NAME}_${timestamp}.sql"
    
    if mysqldump -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" \
        --single-transaction --quick --lock-tables=false \
        "$DB_NAME" > "$backup_file" 2>/dev/null; then
        
        # 压缩备份文件
        gzip "$backup_file"
        log_info "MySQL 备份完成: ${backup_file}.gz"
        
        # 计算备份文件大小
        local size=$(du -h "${backup_file}.gz" | cut -f1)
        log_info "备份文件大小: $size"
        
        return 0
    else
        log_error "MySQL 备份失败"
        rm -f "$backup_file"
        return 1
    fi
}

# 备份 SQLite 数据库
backup_sqlite() {
    local backup_dir="$1"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    
    log_info "开始备份 SQLite 数据库..."
    
    # 备份后端 SQLite（如果存在）
    if [ -f backend/app.db ]; then
        cp backend/app.db "$backup_dir/backend_app_${timestamp}.db"
        gzip "$backup_dir/backend_app_${timestamp}.db"
        log_info "后端 SQLite 备份完成"
    fi
    
    # 备份 workflow-ctl SQLite
    if [ -f workflow-ctl/data/workflow.db ]; then
        cp workflow-ctl/data/workflow.db "$backup_dir/workflow_${timestamp}.db"
        gzip "$backup_dir/workflow_${timestamp}.db"
        log_info "Workflow-ctl SQLite 备份完成"
    else
        log_warn "未找到 workflow-ctl 数据库文件"
    fi
}

# 备份配置文件
backup_config() {
    local backup_dir="$1"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    
    log_info "开始备份配置文件..."
    
    local config_backup="$backup_dir/config_${timestamp}.tar.gz"
    
    tar czf "$config_backup" \
        .env \
        docker-compose.yml \
        backend/env.example \
        frontend/nginx.conf \
        2>/dev/null || true
    
    if [ -f "$config_backup" ]; then
        log_info "配置文件备份完成: $config_backup"
    else
        log_warn "配置文件备份失败"
    fi
}

# 备份日志文件
backup_logs() {
    local backup_dir="$1"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    
    log_info "开始备份日志文件..."
    
    if [ ! -d logs ]; then
        log_warn "日志目录不存在，跳过日志备份"
        return 0
    fi
    
    local logs_backup="$backup_dir/logs_${timestamp}.tar.gz"
    
    # 只备份最近7天的日志
    find logs -type f -mtime -7 -print0 | \
        tar czf "$logs_backup" --null -T - 2>/dev/null || true
    
    if [ -f "$logs_backup" ]; then
        local size=$(du -h "$logs_backup" | cut -f1)
        log_info "日志文件备份完成: $logs_backup ($size)"
    else
        log_warn "日志文件备份失败"
    fi
}

# 备份 Docker 卷（如果使用 Docker）
backup_docker_volumes() {
    local backup_dir="$1"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    
    if ! command -v docker &> /dev/null; then
        return 0
    fi
    
    log_info "开始备份 Docker 卷..."
    
    # 获取所有卷
    local volumes=$(docker volume ls -q | grep xinhua 2>/dev/null)
    
    if [ -z "$volumes" ]; then
        log_info "未找到 Docker 卷"
        return 0
    fi
    
    for volume in $volumes; do
        local volume_backup="$backup_dir/volume_${volume}_${timestamp}.tar.gz"
        
        docker run --rm \
            -v "$volume":/volume \
            -v "$backup_dir":/backup \
            alpine tar czf "/backup/$(basename $volume_backup)" -C /volume . 2>/dev/null
        
        if [ -f "$volume_backup" ]; then
            log_info "Docker 卷备份完成: $volume"
        fi
    done
}

# 上传到云存储
upload_to_cloud() {
    local backup_dir="$1"
    
    # 上传到 S3
    if [ -n "$S3_BUCKET" ] && command -v aws &> /dev/null; then
        log_info "上传备份到 S3..."
        aws s3 sync "$backup_dir" "s3://$S3_BUCKET/xinhua-backup/$(basename $backup_dir)/" \
            --storage-class STANDARD_IA \
            --quiet
        
        if [ $? -eq 0 ]; then
            log_info "S3 上传完成"
        else
            log_error "S3 上传失败"
        fi
    fi
    
    # 上传到阿里云 OSS
    if [ -n "$OSS_BUCKET" ] && command -v ossutil &> /dev/null; then
        log_info "上传备份到阿里云 OSS..."
        ossutil cp -r "$backup_dir" "oss://$OSS_BUCKET/xinhua-backup/$(basename $backup_dir)/" \
            --quiet
        
        if [ $? -eq 0 ]; then
            log_info "OSS 上传完成"
        else
            log_error "OSS 上传失败"
        fi
    fi
}

# 清理旧备份
cleanup_old_backups() {
    log_info "清理 $RETENTION_DAYS 天前的备份..."
    
    if [ -d "$BACKUP_DIR" ]; then
        local deleted_count=$(find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete -print | wc -l)
        local deleted_dirs=$(find "$BACKUP_DIR" -type d -empty -delete -print | wc -l)
        
        log_info "已删除 $deleted_count 个旧备份文件和 $deleted_dirs 个空目录"
    fi
}

# 生成备份报告
generate_report() {
    local backup_dir="$1"
    local report_file="$backup_dir/backup_report.txt"
    
    {
        echo "============================================"
        echo "           Xinhua 备份报告"
        echo "============================================"
        echo ""
        echo "备份时间: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "备份目录: $backup_dir"
        echo ""
        echo "备份文件列表:"
        echo "----------------------------------------"
        ls -lh "$backup_dir" | grep -v "^total" | grep -v "backup_report"
        echo ""
        echo "============================================"
        echo "总大小: $(du -sh $backup_dir | cut -f1)"
        echo "============================================"
    } > "$report_file"
    
    cat "$report_file"
}

# 快速备份（只备份数据库和配置）
quick_backup() {
    log_info "执行快速备份..."
    
    local backup_dir=$(prepare_backup_dir)
    
    backup_mysql "$backup_dir"
    backup_sqlite "$backup_dir"
    backup_config "$backup_dir"
    
    generate_report "$backup_dir"
    cleanup_old_backups
    
    log_info "快速备份完成！"
}

# 完整备份（包括日志和 Docker 卷）
full_backup() {
    log_info "执行完整备份..."
    
    local backup_dir=$(prepare_backup_dir)
    
    backup_mysql "$backup_dir"
    backup_sqlite "$backup_dir"
    backup_config "$backup_dir"
    backup_logs "$backup_dir"
    backup_docker_volumes "$backup_dir"
    
    generate_report "$backup_dir"
    
    # 上传到云存储
    upload_to_cloud "$backup_dir"
    
    cleanup_old_backups
    
    log_info "完整备份完成！"
}

# 恢复备份
restore_backup() {
    local backup_path="$1"
    
    if [ -z "$backup_path" ]; then
        log_error "请指定备份文件路径"
        echo "使用方法: $0 restore <backup_file>"
        exit 1
    fi
    
    if [ ! -f "$backup_path" ]; then
        log_error "备份文件不存在: $backup_path"
        exit 1
    fi
    
    log_warn "准备恢复备份..."
    log_warn "这将覆盖现有数据！"
    read -p "是否继续？(yes/no) " -r
    
    if [ "$REPLY" != "yes" ]; then
        log_info "取消恢复"
        exit 0
    fi
    
    # 根据文件类型恢复
    if [[ "$backup_path" == *".sql"* ]]; then
        # MySQL 恢复
        source .env
        
        if [[ "$backup_path" == *.gz ]]; then
            gunzip -c "$backup_path" | mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME"
        else
            mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$backup_path"
        fi
        
        log_info "MySQL 数据库恢复完成"
        
    elif [[ "$backup_path" == *".db"* ]]; then
        # SQLite 恢复
        if [[ "$backup_path" == *.gz ]]; then
            gunzip -c "$backup_path" > /tmp/restore.db
            cp /tmp/restore.db workflow-ctl/data/workflow.db
            rm /tmp/restore.db
        else
            cp "$backup_path" workflow-ctl/data/workflow.db
        fi
        
        log_info "SQLite 数据库恢复完成"
        
    else
        log_error "未知的备份文件类型"
        exit 1
    fi
}

# 显示帮助信息
show_help() {
    cat <<EOF
使用方法: $0 [command] [options]

命令:
  quick         执行快速备份（仅数据库和配置）
  full          执行完整备份（包括日志和 Docker 卷）
  restore FILE  恢复指定的备份文件
  list          列出所有可用备份
  help          显示此帮助信息

示例:
  $0 quick                              # 快速备份
  $0 full                               # 完整备份
  $0 restore /backup/xinhua/backup.sql  # 恢复备份
  $0 list                               # 列出备份

配置:
  备份目录: $BACKUP_DIR
  保留天数: $RETENTION_DAYS

EOF
}

# 列出可用备份
list_backups() {
    if [ ! -d "$BACKUP_DIR" ]; then
        log_warn "备份目录不存在: $BACKUP_DIR"
        exit 1
    fi
    
    echo "可用备份："
    echo "=========================================="
    
    find "$BACKUP_DIR" -type f \( -name "*.sql.gz" -o -name "*.db.gz" -o -name "*.tar.gz" \) \
        -printf "%T+ %p %s\n" | \
        sort -r | \
        head -20 | \
        awk '{
            size=$3
            if (size > 1073741824) printf "%s  %.2fGB  %s\n", $1, size/1073741824, $2
            else if (size > 1048576) printf "%s  %.2fMB  %s\n", $1, size/1048576, $2
            else printf "%s  %.2fKB  %s\n", $1, size/1024, $2
        }'
}

# 主函数
main() {
    echo "=========================================="
    echo "        Xinhua 备份脚本"
    echo "=========================================="
    echo ""
    
    check_dependencies
    
    case "${1:-full}" in
        quick)
            quick_backup
            ;;
        full)
            full_backup
            ;;
        restore)
            restore_backup "$2"
            ;;
        list)
            list_backups
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"

