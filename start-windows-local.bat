@echo off
cd /d "%~dp0"
title RadioManager - Local Deployment (SQLite)

echo ================================================
echo   RadioManager - Local Deployment (SQLite)
echo   Architecture: Frontend(Electron) + Backend(FastAPI)
echo ================================================
echo.

:: Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

:: Check Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Please install Node.js 18+
    pause
    exit /b 1
)

:: Create required directories
if not exist backend\logs mkdir backend\logs
if not exist backend\uploads mkdir backend\uploads

echo.
echo [1/4] Initializing database (SQLite)...
pushd backend
if not exist venv (
    echo   Creating Python virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt -q >nul 2>&1
python -m app.scripts.init_db
if %errorlevel% neq 0 (
    echo [ERROR] Database initialization failed
    pause
    popd
    exit /b 1
)
popd

echo.
echo [2/4] Starting backend...
pushd backend
start "RadioManager-Backend" cmd /c "call venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000"
popd
echo   Backend started: http://localhost:8000
timeout /t 3 /nobreak >nul

echo.
echo [3/4] Building frontend...
pushd frontend
if not exist node_modules (
    echo   Installing frontend dependencies...
    call npm install
)
call npm run build
popd

echo.
echo [4/4] Starting Electron desktop app...
echo   Deployment mode: Local
echo.
pushd frontend

where npx >nul 2>&1
if %errorlevel% neq 0 (
    echo   npx not found, starting web server instead
    echo   Visit: http://localhost:5173
    start cmd /c "npm run dev"
) else (
    call npx electron .
)

popd

echo.
echo ================================================
echo   Services stopped
echo ================================================
pause
