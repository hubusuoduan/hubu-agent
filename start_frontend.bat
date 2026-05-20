@echo off
echo ========================================
echo   Hubu Agent Frontend - 快速启动脚本
echo ========================================
echo.

echo [1/2] 检查Node.js环境...
node --version
if errorlevel 1 (
    echo 错误: 未找到Node.js，请先安装Node.js 18+
    pause
    exit /b 1
)

echo.
echo [2/2] 安装前端依赖并启动...
cd frontend

if not exist "node_modules" (
    echo 首次运行，正在安装依赖...
    npm install
    if errorlevel 1 (
        echo 错误: 前端依赖安装失败
        pause
        exit /b 1
    )
)

echo.
echo 前端将运行在 http://localhost:5173
echo.
echo 按 Ctrl+C 停止服务
echo.
npm run dev
