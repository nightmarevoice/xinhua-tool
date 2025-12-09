#!/bin/bash

#############################################
# 数据库迁移脚本
# 使用方法: ./db_migration.sh [export|import]
#############################################

set -e

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPORT_DIR="$SCRIPT_DIR/db_export"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_NAME="xinhua_db_${TIMESTAMP}.tar.gz"

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

# 检查文件是否存在
check_file() {
    local file=$1
    local desc=$2
    
    if [ -f "$file" ]; then
        local size=$(du -h "$file" | cut -f1)
        log_info "$desc 存在 (大小: $size)"
        return 0
    else
        log_warn "$desc 不存在: $file"
        return 1
    fi
}

# 导出数据库
export_databases() {
    log_step "开始导出数据库..."
    
    # 创建导出目录
    mkdir -p "$EXPORT_DIR"
    
    # 1. 导出 backend SQLite 数据库
    log_info "正在导出 backend 数据库..."
    if [ -f "$SCRIPT_DIR/backend/app.db" ]; then
        cp "$SCRIPT_DIR/backend/app.db" "$EXPORT_DIR/backend_app.db"
        log_info "✅ Backend 数据库已导出"
    else
        log_warn "⚠️  Backend 数据库不存在，将创建新的空数据库"
        touch "$EXPORT_DIR/backend_app.db.empty"
    fi
    
    # 2. 导出 workflow-ctl SQLite 数据库
    log_info "正在导出 workflow-ctl 数据库..."
    if [ -f "$SCRIPT_DIR/workflow-ctl/data/workflow.db" ]; then
        cp "$SCRIPT_DIR/workflow-ctl/data/workflow.db" "$EXPORT_DIR/workflow.db"
        log_info "✅ Workflow-ctl 数据库已导出"
    else
        log_warn "⚠️  Workflow-ctl 数据库不存在，将创建新的空数据库"
        mkdir -p "$SCRIPT_DIR/workflow-ctl/data"
        touch "$EXPORT_DIR/workflow.db.empty"
    fi
    
    # 3. 创建导出信息文件
    cat > "$EXPORT_DIR/export_info.txt" <<EOF
数据库导出信息
================
导出时间: $(date '+%Y-%m-%d %H:%M:%S')
导出主机: $(hostname)
导出用户: $(whoami)

文件列表:
EOF
    
    ls -lh "$EXPORT_DIR" >> "$EXPORT_DIR/export_info.txt"
    
    # 4. 打包数据库文件
    log_info "正在打包数据库文件..."
    cd "$SCRIPT_DIR"
    tar czf "$ARCHIVE_NAME" -C "$EXPORT_DIR" .
    
    if [ -f "$ARCHIVE_NAME" ]; then
        local size=$(du -h "$ARCHIVE_NAME" | cut -f1)
        log_info "✅ 数据库已打包: $ARCHIVE_NAME (大小: $size)"
        log_info "📦 导出包位置: $SCRIPT_DIR/$ARCHIVE_NAME"
    else
        log_error "❌ 打包失败"
        exit 1
    fi
    
    # 5. 生成部署说明
    cat > "db_deploy_instructions.txt" <<EOF
数据库部署说明
================

1. 将数据库包传输到目标服务器：
   scp $ARCHIVE_NAME user@target-server:/path/to/xinhua-tool/

2. 在目标服务器上解压并导入：
   cd /path/to/xinhua-tool
   ./db_migration.sh import $ARCHIVE_NAME

3. 或者使用自动部署脚本：
   ./deploy.sh docker --with-db $ARCHIVE_NAME

注意事项：
- 导入前会自动备份现有数据库
- 如果目标服务器已有数据，请先确认是否需要合并
- 建议在非高峰期进行数据库迁移

导出时间: $(date '+%Y-%m-%d %H:%M:%S')
导出文件: $ARCHIVE_NAME
文件大小: $(du -h "$ARCHIVE_NAME" | cut -f1)
EOF
    
    log_info "✅ 数据库导出完成！"
    echo ""
    echo "=============================================="
    echo "  📊 导出摘要"
    echo "=============================================="
    cat "$EXPORT_DIR/export_info.txt"
    echo ""
    echo "=============================================="
    echo "  📝 部署说明已生成: db_deploy_instructions.txt"
    echo "=============================================="
}

# 导入数据库
import_databases() {
    local archive_file=$1
    
    if [ -z "$archive_file" ]; then
        log_error "请指定要导入的数据库包文件"
        echo "使用方法: $0 import <archive_file>"
        exit 1
    fi
    
    if [ ! -f "$archive_file" ]; then
        log_error "数据库包文件不存在: $archive_file"
        exit 1
    fi
    
    log_step "开始导入数据库..."
    
    # 1. 备份现有数据库
    log_info "正在备份现有数据库..."
    local backup_dir="$SCRIPT_DIR/db_backup_before_import_${TIMESTAMP}"
    mkdir -p "$backup_dir"
    
    if [ -f "$SCRIPT_DIR/backend/app.db" ]; then
        cp "$SCRIPT_DIR/backend/app.db" "$backup_dir/backend_app.db"
        log_info "✅ Backend 数据库已备份"
    fi
    
    if [ -f "$SCRIPT_DIR/workflow-ctl/data/workflow.db" ]; then
        cp "$SCRIPT_DIR/workflow-ctl/data/workflow.db" "$backup_dir/workflow.db"
        log_info "✅ Workflow-ctl 数据库已备份"
    fi
    
    # 2. 解压数据库包
    log_info "正在解压数据库包..."
    local temp_dir="$SCRIPT_DIR/db_import_temp"
    mkdir -p "$temp_dir"
    tar xzf "$archive_file" -C "$temp_dir"
    
    # 3. 导入 backend 数据库
    log_info "正在导入 backend 数据库..."
    if [ -f "$temp_dir/backend_app.db" ]; then
        mkdir -p "$SCRIPT_DIR/backend"
        cp "$temp_dir/backend_app.db" "$SCRIPT_DIR/backend/app.db"
        log_info "✅ Backend 数据库已导入"
    elif [ -f "$temp_dir/backend_app.db.empty" ]; then
        log_warn "⚠️  导入的是空数据库，将初始化新数据库"
        touch "$SCRIPT_DIR/backend/app.db"
    fi
    
    # 4. 导入 workflow-ctl 数据库
    log_info "正在导入 workflow-ctl 数据库..."
    if [ -f "$temp_dir/workflow.db" ]; then
        mkdir -p "$SCRIPT_DIR/workflow-ctl/data"
        cp "$temp_dir/workflow.db" "$SCRIPT_DIR/workflow-ctl/data/workflow.db"
        log_info "✅ Workflow-ctl 数据库已导入"
    elif [ -f "$temp_dir/workflow.db.empty" ]; then
        log_warn "⚠️  导入的是空数据库，将初始化新数据库"
        mkdir -p "$SCRIPT_DIR/workflow-ctl/data"
        touch "$SCRIPT_DIR/workflow-ctl/data/workflow.db"
    fi
    
    # 5. 清理临时文件
    rm -rf "$temp_dir"
    
    # 6. 显示导入信息
    if [ -f "$backup_dir/../db_export/export_info.txt" ]; then
        cat "$backup_dir/../db_export/export_info.txt"
    fi
    
    log_info "✅ 数据库导入完成！"
    echo ""
    echo "=============================================="
    echo "  📊 导入摘要"
    echo "=============================================="
    echo "备份位置: $backup_dir"
    echo ""
    echo "Backend 数据库: $(check_file "$SCRIPT_DIR/backend/app.db" "backend/app.db" && echo "✅" || echo "❌")"
    echo "Workflow-ctl 数据库: $(check_file "$SCRIPT_DIR/workflow-ctl/data/workflow.db" "workflow-ctl/data/workflow.db" && echo "✅" || echo "❌")"
    echo ""
    echo "=============================================="
    echo "  ⚠️  重要提示"
    echo "=============================================="
    echo "1. 原有数据已备份到: $backup_dir"
    echo "2. 请重启应用以使数据库生效"
    echo "3. 如需回滚，请运行: ./db_migration.sh rollback $backup_dir"
    echo "=============================================="
}

# 回滚数据库
rollback_databases() {
    local backup_dir=$1
    
    if [ -z "$backup_dir" ]; then
        log_error "请指定备份目录"
        echo "使用方法: $0 rollback <backup_dir>"
        exit 1
    fi
    
    if [ ! -d "$backup_dir" ]; then
        log_error "备份目录不存在: $backup_dir"
        exit 1
    fi
    
    log_step "开始回滚数据库..."
    log_warn "这将恢复到备份时的数据状态"
    read -p "是否继续？(yes/no) " -r
    
    if [ "$REPLY" != "yes" ]; then
        log_info "取消回滚"
        exit 0
    fi
    
    # 回滚 backend 数据库
    if [ -f "$backup_dir/backend_app.db" ]; then
        cp "$backup_dir/backend_app.db" "$SCRIPT_DIR/backend/app.db"
        log_info "✅ Backend 数据库已回滚"
    fi
    
    # 回滚 workflow-ctl 数据库
    if [ -f "$backup_dir/workflow.db" ]; then
        cp "$backup_dir/workflow.db" "$SCRIPT_DIR/workflow-ctl/data/workflow.db"
        log_info "✅ Workflow-ctl 数据库已回滚"
    fi
    
    log_info "✅ 数据库回滚完成！"
    echo "请重启应用以使数据库生效"
}

# 验证数据库
verify_databases() {
    log_step "验证数据库完整性..."
    
    local status=0
    
    # 验证 backend 数据库
    if [ -f "$SCRIPT_DIR/backend/app.db" ]; then
        if sqlite3 "$SCRIPT_DIR/backend/app.db" "PRAGMA integrity_check;" | grep -q "ok"; then
            log_info "✅ Backend 数据库完整性检查通过"
        else
            log_error "❌ Backend 数据库损坏"
            status=1
        fi
    else
        log_warn "⚠️  Backend 数据库文件不存在"
    fi
    
    # 验证 workflow-ctl 数据库
    if [ -f "$SCRIPT_DIR/workflow-ctl/data/workflow.db" ]; then
        if sqlite3 "$SCRIPT_DIR/workflow-ctl/data/workflow.db" "PRAGMA integrity_check;" | grep -q "ok"; then
            log_info "✅ Workflow-ctl 数据库完整性检查通过"
        else
            log_error "❌ Workflow-ctl 数据库损坏"
            status=1
        fi
    else
        log_warn "⚠️  Workflow-ctl 数据库文件不存在"
    fi
    
    return $status
}

# 显示帮助信息
show_help() {
    cat <<EOF
数据库迁移脚本 - Xinhua Tool

使用方法: $0 [command] [options]

命令:
  export              导出当前数据库到打包文件
  import <file>       从打包文件导入数据库
  rollback <dir>      回滚到指定备份
  verify              验证数据库完整性
  help                显示此帮助信息

示例:
  # 1. 在源服务器上导出数据库
  $0 export

  # 2. 传输到目标服务器
  scp xinhua_db_*.tar.gz user@target-server:/path/to/xinhua-tool/

  # 3. 在目标服务器上导入
  $0 import xinhua_db_*.tar.gz

  # 4. 如需回滚
  $0 rollback db_backup_before_import_*

  # 5. 验证数据库
  $0 verify

注意事项:
  - 导入前会自动备份现有数据库
  - SQLite 数据库文件会被直接复制
  - 导入后需要重启应用
  - 支持部分数据恢复（只恢复存在的数据库）

EOF
}

# 主函数
main() {
    echo "=============================================="
    echo "        Xinhua 数据库迁移工具"
    echo "=============================================="
    echo ""
    
    case "${1:-help}" in
        export)
            export_databases
            ;;
        import)
            import_databases "$2"
            ;;
        rollback)
            rollback_databases "$2"
            ;;
        verify)
            verify_databases
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

