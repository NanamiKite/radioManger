@echo off
chcp 65001 >nul
title RadioManager - 纯本地部署启动 (SQLite)

echo ================================================
echo   RadioManager - 纯本地部署启动
echo   数据库: SQLite
echo   架构: 前端(Electron) + 后端(FastAPI)
echo ================================================
echo.

:: 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请安装 Python 3.10+
    pause
    exit /b 1
)

:: 检查Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Node.js，请安装 Node.js 18+
    pause
    exit /b 1
)

:: 创建必要目录
if not exist backend\logs mkdir backend\logs
if not exist backend\uploads mkdir backend\uploads

echo.
echo [1/4] 初始化数据库 (SQLite)...
cd backend
if not exist venv (
    echo   创建Python虚拟环境...
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt -q >nul 2>&1
python -m app.scripts.init_db
if %errorlevel% neq 0 (
    echo [错误] 数据库初始化失败
    pause
    exit /b 1
)
cd ..

echo.
echo [2/4] 启动后端服务...
cd backend
start "RadioManager-Backend" cmd /c "call venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000"
cd ..
echo   后端已启动: http://localhost:8000
timeout /t 3 /nobreak >nul

echo.
echo [3/4] 构建前端...
cd frontend
if not exist node_modules (
    echo   安装前端依赖...
    call npm install
)
call npm run build
cd ..

echo.
echo [4/4] 启动 Electron 桌面应用...
echo   部署模式: Local (本地后端)
echo.
set RADIOMANAGER_MODE=local
cd frontend

:: 检查是否安装了 Electron
call npx electron --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] Electron 未安装，将启动 Web 模式
    echo   请访问: http://localhost:5173
    start npm run dev
) else (
    call npx electron .
)

cd ..

echo.
echo ================================================
echo   服务已停止
echo ================================================
pause
