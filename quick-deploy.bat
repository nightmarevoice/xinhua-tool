@echo off
REM ========================================
REM 新华工具 - Windows 快速部署脚本
REM ========================================
setlocal enabledelayedexpansion

echo.
echo ================================================
echo         新华工具 - 快速部署 (智能构建)
echo ================================================
echo.

REM 检查是否安装 Git Bash
where bash >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] 检测到 Git Bash，使用 Linux 脚本...
    echo.
    
    REM 确保脚本有执行权限
    if exist quick-deploy.sh (
        bash -c "chmod +x quick-deploy.sh && ./quick-deploy.sh %*"
        exit /b %errorlevel%
    ) else (
        echo [ERROR] 未找到 quick-deploy.sh 脚本
        exit /b 1
    )
)

REM 如果没有 Git Bash，使用简化的 Windows 方式
echo [INFO] 未检测到 Git Bash，使用简化部署...
echo.

REM 检查 Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker 未安装或未启动
    echo 请先安装 Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM 检查 Docker 守护进程
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker 守护进程未运行
    echo 请先启动 Docker Desktop
    pause
    exit /b 1
)

echo [OK] Docker 环境检查通过
echo.

REM 启用 BuildKit
set DOCKER_BUILDKIT=1
set COMPOSE_DOCKER_CLI_BUILD=1
echo [INFO] 已启用 Docker BuildKit (构建加速)
echo.

REM 检查环境配置
if not exist .env (
    if exist env.example (
        echo [INFO] 复制环境配置文件...
        copy env.example .env
        echo [OK] 已创建 .env 文件
    ) else (
        echo [ERROR] 未找到环境配置文件
        pause
        exit /b 1
    )
)
echo.

REM 停止旧容器
echo [INFO] 停止旧容器...
docker-compose down 2>nul
echo [OK] 已停止旧容器
echo.

REM 启动服务（不重新构建，使用缓存）
echo [INFO] 启动服务（使用缓存镜像）...
echo 说明: 如果是首次运行或需要重新构建，请使用 deploy.bat
echo.
docker-compose up -d

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] 服务启动失败
    echo 提示: 如果镜像不存在，请先运行完整部署: deploy.bat
    pause
    exit /b 1
)

echo.
echo [OK] 服务启动中...
echo.

REM 等待服务就绪
echo [INFO] 等待服务就绪 (约 30 秒)...
timeout /t 30 /nobreak >nul

REM 检查容器状态
echo.
echo [INFO] 检查服务状态...
docker-compose ps

echo.
echo ================================================
echo                 部署完成！
echo ================================================
echo.
echo 访问地址:
echo   前端:     http://localhost:8787
echo   后端 API: http://localhost:8888/docs
echo   工作流:   http://localhost:8889/docs
echo.
echo 管理命令:
echo   查看状态: manage.bat status
echo   查看日志: manage.bat logs
echo   停止服务: manage.bat stop
echo.
echo 提示:
echo   本次部署使用了缓存镜像，速度很快
echo   如需重新构建镜像，请使用: deploy.bat
echo.

pause


