#!/bin/bash

echo "🚀 启动 Admin Manage System"
echo "================================"

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装 Python 3.8+"
    exit 1
fi

# 检查 Node.js 环境
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装，请先安装 Node.js 16+"
    exit 1
fi

echo "📦 安装后端依赖..."
cd backend
pip install -r requirements.txt

echo "🗄️ 初始化数据库..."
python init_db.py

echo "🔧 启动后端服务..."
python main.py &
BACKEND_PID=$!

# 等待后端启动
sleep 3

echo "📦 安装前端依赖..."
cd ../frontend
npm install

echo "🎨 启动前端服务..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ 服务启动完成！"
echo "🌐 前端地址: http://localhost:3000"
echo "🔗 后端地址: http://localhost:8888"
echo "📚 API 文档: http://localhost:8888/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
trap "echo '🛑 正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
