#!/bin/bash

# =============================================================================
# 数据库连接配置修复脚本
# =============================================================================
# 用途：自动检测和修复 Docker 部署中的数据库连接问题
# 作者：AI Assistant
# 最后更新：2025-12-10
# =============================================================================

set -e

echo "=========================================="
echo "  数据库连接配置修复工具"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 步骤 1: 检查 .env 文件
echo -e "${BLUE}步骤 1/4:${NC} 检查环境配置文件..."
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env 文件不存在${NC}"
    echo "正在从 env.example 创建 .env 文件..."
    
    if [ -f "env.example" ]; then
        cp env.example .env
        echo -e "${GREEN}✅ 已创建 .env 文件${NC}"
    else
        echo -e "${RED}❌ 错误: env.example 文件不存在${NC}"
        echo "请手动创建 .env 文件或联系管理员"
        exit 1
    fi
else
    echo -e "${GREEN}✅ .env 文件存在${NC}"
fi
echo ""

# 步骤 2: 验证数据库配置
echo -e "${BLUE}步骤 2/4:${NC} 验证数据库配置..."

# 检查必需的环境变量
REQUIRED_VARS=(
    "DB_HOST"
    "DB_PORT"
    "DB_NAME"
    "DB_USER"
    "DB_PASSWORD"
    "BACKEND_DATABASE_URL"
)

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if ! grep -q "^${var}=" .env; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠️  缺少以下配置项:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "请编辑 .env 文件并添加缺少的配置项"
    echo "参考 env.example 或 backend/env.example"
else
    echo -e "${GREEN}✅ 所有必需配置项都存在${NC}"
fi
echo ""

# 步骤 3: 检查数据库连接字符串格式
echo -e "${BLUE}步骤 3/4:${NC} 检查数据库连接字符串..."

if grep -q "localhost" .env; then
    echo -e "${RED}❌ 发现 'localhost' 配置${NC}"
    echo ""
    echo "Docker 容器中不能使用 'localhost' 连接数据库！"
    echo ""
    echo "请修改 .env 文件中的数据库配置："
    echo "  - 如果使用外部数据库（如阿里云 RDS），使用实际的主机地址"
    echo "  - 如果使用 Docker 内的 MySQL 容器，使用容器名称（如 'mysql'）"
    echo ""
    
    # 提供自动修复建议
    read -p "是否查看当前的 DATABASE_URL 配置？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "当前配置："
        grep "DATABASE_URL" .env || echo "未找到 DATABASE_URL"
        echo ""
    fi
elif grep -q "rm-bp1jldp727lmxq1m57o.mysql.rds.aliyuncs.com" .env; then
    echo -e "${GREEN}✅ 使用阿里云 RDS 数据库${NC}"
else
    echo -e "${GREEN}✅ 数据库连接字符串格式正常${NC}"
fi
echo ""

# 步骤 4: 测试数据库连接
echo -e "${BLUE}步骤 4/4:${NC} 测试数据库连接..."
echo "正在尝试连接数据库..."

# 加载环境变量
set -a
source .env
set +a

# 使用 Python 测试连接
TEST_RESULT=$(docker-compose run --rm backend python -c "
import sys
import pymysql
from urllib.parse import urlparse

try:
    # 解析数据库 URL
    db_url = '$BACKEND_DATABASE_URL'
    parsed = urlparse(db_url)
    
    # 提取连接参数
    host = parsed.hostname
    port = parsed.port or 3306
    user = parsed.username
    password = parsed.password
    database = parsed.path.lstrip('/')
    
    # 尝试连接
    connection = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        connect_timeout=10
    )
    connection.close()
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
" 2>&1 | tail -1)

if [[ "$TEST_RESULT" == *"SUCCESS"* ]]; then
    echo -e "${GREEN}✅ 数据库连接成功！${NC}"
elif [[ "$TEST_RESULT" == *"ERROR"* ]]; then
    echo -e "${RED}❌ 数据库连接失败${NC}"
    echo ""
    echo "错误信息："
    echo "$TEST_RESULT"
    echo ""
    echo "可能的原因："
    echo "  1. 数据库主机地址错误"
    echo "  2. 数据库用户名或密码错误"
    echo "  3. 数据库不存在"
    echo "  4. 防火墙阻止连接"
    echo "  5. 密码包含特殊字符未正确编码（% 应编码为 %25）"
else
    echo -e "${YELLOW}⚠️  无法测试数据库连接${NC}"
    echo "请确保 Docker 服务正在运行"
fi
echo ""

# 总结
echo "=========================================="
echo "  修复完成"
echo "=========================================="
echo ""
echo "接下来的步骤："
echo ""
echo "1. 如果数据库连接成功，重新部署："
echo -e "   ${GREEN}docker-compose down && docker-compose up -d${NC}"
echo ""
echo "2. 如果数据库连接失败，请检查："
echo "   - .env 文件中的数据库配置是否正确"
echo "   - 数据库服务器是否可访问"
echo "   - 防火墙规则是否允许连接"
echo ""
echo "3. 查看实时日志："
echo -e "   ${GREEN}docker-compose logs -f backend${NC}"
echo ""
echo "4. 测试后端健康状态："
echo -e "   ${GREEN}curl http://localhost:8888/health${NC}"
echo ""

# 提供快速修复命令
echo "快速修复命令："
echo -e "   ${GREEN}./fix-database-connection.sh && docker-compose down && docker-compose up -d${NC}"
echo ""

