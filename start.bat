@echo off
echo 🚀 启动 Admin Manage System
echo ================================

REM 检查 Python 环境
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安装，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 检查 Node.js 环境
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js 未安装，请先安装 Node.js 16+
    pause
    exit /b 1
)

echo 📦 安装后端依赖...
cd backend
pip install -r requirements.txt

echo 🗄️ 初始化数据库...
python init_db.py

echo 🔧 启动后端服务...
start "Backend" cmd /k "python main.py"

REM 等待后端启动
timeout /t 3 /nobreak >nul

echo 📦 安装前端依赖...
cd ..\frontend
npm install

echo 🎨 启动前端服务...
start "Frontend" cmd /k "npm run dev"

echo.
echo ✅ 服务启动完成！
echo 🌐 前端地址: http://localhost:3000
echo 🔗 后端地址: http://localhost:8000
echo 📚 API 文档: http://localhost:8000/docs
echo.
echo 按任意键退出...
pause >nul
