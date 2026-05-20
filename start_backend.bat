@echo off
echo ========================================
echo   Hubu Agent - 快速启动脚本
echo ========================================
echo.

echo [1/3] 检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.11+
    pause
    exit /b 1
)

echo.
echo [2/3] 安装后端依赖...
cd backend
poetry install
if errorlevel 1 (
    echo 错误: 后端依赖安装失败
    pause
    exit /b 1
)

echo.
echo [3/3] 启动后端服务...
echo 后端将运行在 http://localhost:8000
echo API文档: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务
echo.
poetry run python app/main.py
