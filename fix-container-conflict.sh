#!/bin/bash

# ========================================
# 修复 Docker 容器名称冲突
# ========================================

echo "🔧 开始修复 Docker 容器冲突问题..."
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 停止所有相关容器
echo "📦 步骤 1/5: 停止所有 xinhua 相关容器..."
docker-compose down 2>/dev/null || true
echo -e "${GREEN}✓ 完成${NC}"
echo ""

# 2. 强制删除所有相关容器
echo "🗑️  步骤 2/5: 删除冲突的容器..."
CONTAINERS=$(docker ps -a -q --filter "name=xinhua")
if [ -n "$CONTAINERS" ]; then
    echo "找到以下容器:"
    docker ps -a --filter "name=xinhua" --format "table {{.ID}}\t{{.Names}}\t{{.Status}}"
    echo ""
    docker rm -f $CONTAINERS
    echo -e "${GREEN}✓ 已删除所有冲突容器${NC}"
else
    echo -e "${YELLOW}ℹ️  没有找到冲突容器${NC}"
fi
echo ""

# 3. 清理悬空容器
echo "🧹 步骤 3/5: 清理悬空容器..."
DANGLING=$(docker ps -a -q -f status=exited -f status=created)
if [ -n "$DANGLING" ]; then
    docker rm $DANGLING 2>/dev/null || true
    echo -e "${GREEN}✓ 已清理悬空容器${NC}"
else
    echo -e "${YELLOW}ℹ️  没有悬空容器${NC}"
fi
echo ""

# 4. 清理网络（如果存在）
echo "🌐 步骤 4/5: 清理 Docker 网络..."
NETWORK="xinhua-tool_xinhua-network"
if docker network inspect $NETWORK >/dev/null 2>&1; then
    docker network rm $NETWORK 2>/dev/null || true
    echo -e "${GREEN}✓ 已删除网络: $NETWORK${NC}"
else
    echo -e "${YELLOW}ℹ️  网络不存在，跳过${NC}"
fi
echo ""

# 5. 显示清理结果
echo "📊 步骤 5/5: 检查清理结果..."
echo ""
echo "当前容器状态:"
REMAINING=$(docker ps -a --filter "name=xinhua" --format "table {{.Names}}\t{{.Status}}")
if [ -z "$REMAINING" ] || [ "$REMAINING" = "NAMES	STATUS" ]; then
    echo -e "${GREEN}✓ 所有 xinhua 容器已清理${NC}"
else
    echo "$REMAINING"
fi
echo ""

echo "当前网络状态:"
docker network ls | grep xinhua || echo -e "${GREEN}✓ xinhua 网络已清理${NC}"
echo ""

# 完成提示
echo "════════════════════════════════════════"
echo -e "${GREEN}✅ 修复完成！${NC}"
echo "════════════════════════════════════════"
echo ""
echo "现在可以重新部署了，运行:"
echo -e "${YELLOW}./deploy.sh docker${NC}"
echo ""

