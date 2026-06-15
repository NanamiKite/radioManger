@echo off
setlocal enabledelayedexpansion
pushd %~dp0
title RadioManager - Local Deployment

echo ================================================
echo   RadioManager - Local Deployment (SQLite)
echo ================================================
echo.

:: --- Python detection ---
python --version >nul 2>&1
if %errorlevel% equ 0 (set PY_CMD=python & goto :PYTHON_FOUND)

py --version >nul 2>&1
if %errorlevel% equ 0 (set PY_CMD=py & goto :PYTHON_FOUND)

echo [ERROR] Python not found. Tried: python, py
echo   If using conda: activate your environment first (conda activate base)
echo   Or install from https://www.python.org/downloads/
pause
exit /b 1

:PYTHON_FOUND
for /f "delims=" %%v in ('%PY_CMD% --version 2^>^&1') do set PY_VERSION=%%v
echo [OK] Python: %PY_CMD% - %PY_VERSION%

:: --- Node.js detection ---
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. If using nvm, run "nvm use 18" first.
    pause
    exit /b 1
)
for /f "delims=" %%v in ('node --version 2^>^&1') do set NODE_VERSION=%%v
echo [OK] Node.js: %NODE_VERSION%

:: --- Directory check ---
if not exist "%~dp0backend" (echo [ERROR] Missing backend directory & pause & exit /b 1)
if not exist "%~dp0frontend" (echo [ERROR] Missing frontend directory & pause & exit /b 1)

:: --- Create required directories ---
if not exist "%~dp0backend\logs" mkdir "%~dp0backend\logs"
if not exist "%~dp0backend\uploads" mkdir "%~dp0backend\uploads"

echo.
echo [1/4] Initializing database (SQLite)...
pushd "%~dp0backend"
if not exist venv (
    echo   Creating Python virtual environment...
    %PY_CMD% -m venv venv
    if %errorlevel% neq 0 (echo   [INFO] venv skipped - using system Python)
)
if exist venv\Scripts\activate.bat (call venv\Scripts\activate.bat)
echo   Installing Python dependencies...
%PY_CMD% -m pip install -r requirements.txt --no-input -q >nul 2>&1
%PY_CMD% -m app.scripts.init_db
if %errorlevel% neq 0 (
    echo [ERROR] Database init failed. Run manually: cd %CD% ^& %PY_CMD% -m app.scripts.init_db
    pause & popd & exit /b 1
)
popd

echo.
echo [2/4] Starting backend on http://localhost:8000...
start "RadioManager-Backend" cmd /c "cd /d %~dp0backend && if exist venv\Scripts\activate.bat (call venv\Scripts\activate.bat) && %PY_CMD% -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak >nul

echo.
echo [3/4] Building frontend...
pushd "%~dp0frontend"
if not exist node_modules (call npm install --no-audit --no-fund)
call npm run build
if %errorlevel% neq 0 (echo [ERROR] Frontend build failed & pause & popd & exit /b 1)
popd

echo.
echo [4/4] Starting Electron...
pushd "%~dp0frontend"
call npx --yes electron . 2>nul
if %errorlevel% neq 0 (
    echo   Electron unavailable - starting web server on http://localhost:5173
    start cmd /c "npm run dev"
)
popd

echo.
echo ================================================
echo   All services stopped
echo ================================================
pause
endlocal
