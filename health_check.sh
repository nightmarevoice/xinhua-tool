#!/bin/bash

#############################################
# 服务健康检查脚本
# 使用方法: ./health_check.sh
# 配合 crontab 使用: */5 * * * * /opt/xinhua/health_check.sh
#############################################

# 配置
EMAIL_ALERT="admin@example.com"  # 告警邮箱
SLACK_WEBHOOK=""  # Slack Webhook URL（可选）
LOG_FILE="/var/log/xinhua/health_check.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 创建日志目录
mkdir -p "$(dirname $LOG_FILE)"

# 日志函数
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 发送邮件告警
send_email_alert() {
    local subject="$1"
    local message="$2"
    
    if [ -n "$EMAIL_ALERT" ]; then
        echo "$message" | mail -s "$subject" "$EMAIL_ALERT" 2>/dev/null || true
    fi
}

# 发送 Slack 告警
send_slack_alert() {
    local message="$1"
    
    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\"}" \
            "$SLACK_WEBHOOK" 2>/dev/null || true
    fi
}

# 检查服务
check_service() {
    local service_name="$1"
    local url="$2"
    local timeout=5
    
    if curl -f -s --max-time $timeout "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $service_name is healthy"
        log_message "OK: $service_name is healthy"
        return 0
    else
        echo -e "${RED}✗${NC} $service_name is down!"
        log_message "ERROR: $service_name is down!"
        
        # 发送告警
        local alert_message="🚨 Alert: $service_name is down at $(date)"
        send_email_alert "Alert: $service_name Down" "$alert_message"
        send_slack_alert "$alert_message"
        
        return 1
    fi
}

# 检查 Docker 容器状态
check_docker_containers() {
    echo "Checking Docker containers..."
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${YELLOW}⚠${NC} Docker Compose not installed"
        return 0
    fi
    
    # 获取容器状态
    local containers=$(docker-compose ps --services 2>/dev/null)
    
    if [ -z "$containers" ]; then
        echo -e "${YELLOW}⚠${NC} No Docker containers found"
        return 0
    fi
    
    local all_healthy=true
    
    for container in $containers; do
        local status=$(docker-compose ps $container | grep -v "Name" | awk '{print $3}')
        
        if echo "$status" | grep -q "Up"; then
            echo -e "${GREEN}✓${NC} Container $container is running"
        else
            echo -e "${RED}✗${NC} Container $container is not running"
            log_message "ERROR: Container $container is not running"
            all_healthy=false
            
            # 尝试重启容器
            echo "Attempting to restart $container..."
            docker-compose restart $container
        fi
    done
    
    if [ "$all_healthy" = false ]; then
        send_email_alert "Alert: Docker Container Down" "One or more containers are not running"
        return 1
    fi
    
    return 0
}

# 检查磁盘空间
check_disk_space() {
    echo "Checking disk space..."
    
    local threshold=80
    local usage=$(df -h / | awk 'NR==2{print $5}' | sed 's/%//')
    
    if [ $usage -gt $threshold ]; then
        echo -e "${RED}✗${NC} Disk usage is ${usage}% (threshold: ${threshold}%)"
        log_message "WARNING: Disk usage is ${usage}%"
        send_email_alert "Alert: High Disk Usage" "Disk usage is ${usage}%"
        return 1
    else
        echo -e "${GREEN}✓${NC} Disk usage is ${usage}%"
        return 0
    fi
}

# 检查内存使用
check_memory() {
    echo "Checking memory usage..."
    
    local threshold=90
    local usage=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
    
    if [ $usage -gt $threshold ]; then
        echo -e "${RED}✗${NC} Memory usage is ${usage}% (threshold: ${threshold}%)"
        log_message "WARNING: Memory usage is ${usage}%"
        send_email_alert "Alert: High Memory Usage" "Memory usage is ${usage}%"
        return 1
    else
        echo -e "${GREEN}✓${NC} Memory usage is ${usage}%"
        return 0
    fi
}

# 检查数据库连接
check_database() {
    echo "Checking database connection..."
    
    # 从 .env 读取数据库配置
    if [ -f .env ]; then
        source .env
        
        if [ -n "$DB_HOST" ] && [ -n "$DB_USER" ] && [ -n "$DB_PASSWORD" ]; then
            if mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1" &> /dev/null; then
                echo -e "${GREEN}✓${NC} Database connection is healthy"
                return 0
            else
                echo -e "${RED}✗${NC} Database connection failed"
                log_message "ERROR: Database connection failed"
                send_email_alert "Alert: Database Connection Failed" "Cannot connect to database"
                return 1
            fi
        fi
    fi
    
    echo -e "${YELLOW}⚠${NC} Database check skipped (no config found)"
    return 0
}

# 检查日志大小
check_log_size() {
    echo "Checking log file sizes..."
    
    local log_dir="./logs"
    local max_size=1048576  # 1GB in KB
    local large_files=()
    
    if [ -d "$log_dir" ]; then
        while IFS= read -r -d '' file; do
            local size=$(du -k "$file" | cut -f1)
            if [ $size -gt $max_size ]; then
                large_files+=("$file ($((size/1024))MB)")
            fi
        done < <(find "$log_dir" -type f -name "*.log" -print0)
        
        if [ ${#large_files[@]} -gt 0 ]; then
            echo -e "${YELLOW}⚠${NC} Large log files found:"
            printf '%s\n' "${large_files[@]}"
            log_message "WARNING: Large log files detected"
            return 1
        else
            echo -e "${GREEN}✓${NC} Log file sizes are normal"
            return 0
        fi
    fi
    
    return 0
}

# 主检查流程
main() {
    echo "=========================================="
    echo "   Xinhua Health Check - $(date)"
    echo "=========================================="
    echo ""
    
    local failed_checks=0
    
    # 检查各个服务
    check_service "Backend API" "http://localhost:8888/health" || ((failed_checks++))
    check_service "Workflow-ctl API" "http://localhost:8889/health" || ((failed_checks++))
    check_service "Frontend" "http://localhost/" || ((failed_checks++))
    
    echo ""
    
    # 检查系统资源
    check_disk_space || ((failed_checks++))
    check_memory || ((failed_checks++))
    
    echo ""
    
    # 检查 Docker 容器
    check_docker_containers || ((failed_checks++))
    
    echo ""
    
    # 检查数据库
    check_database || ((failed_checks++))
    
    echo ""
    
    # 检查日志大小
    check_log_size || ((failed_checks++))
    
    echo ""
    echo "=========================================="
    
    if [ $failed_checks -eq 0 ]; then
        echo -e "${GREEN}All checks passed!${NC}"
        log_message "All health checks passed"
        exit 0
    else
        echo -e "${RED}$failed_checks check(s) failed!${NC}"
        log_message "$failed_checks health check(s) failed"
        exit 1
    fi
}

# 运行主流程
main

