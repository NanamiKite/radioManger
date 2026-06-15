@echo off
setlocal enabledelayedexpansion
pushd %~dp0
title RadioManager - Local Deployment

echo ================================================
echo   RadioManager - Local Deployment (SQLite)
echo ================================================
echo.

:: ============ Python Detection ============
set PY_CMD=
python --version >nul 2>&1
if %errorlevel% equ 0 (set PY_CMD=python & goto :PYTHON_FOUND)
py --version >nul 2>&1
if %errorlevel% equ 0 (set PY_CMD=py & goto :PYTHON_FOUND)

echo [ERROR] Python not found. Tried: python, py
echo   If using conda: conda activate radiomanager
echo   Or install from https://www.python.org/downloads/
pause
exit /b 1

:PYTHON_FOUND
for /f "delims=" %%v in ('%PY_CMD% --version') do set PY_VERSION=%%v
echo [OK] Python: %PY_CMD% - %PY_VERSION%

if not "%CONDA_DEFAULT_ENV%"=="" echo [INFO] Conda: %CONDA_DEFAULT_ENV%

:: ============ Node.js Detection ============
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Install from https://nodejs.org/
    pause & exit /b 1
)
for /f "delims=" %%v in ('node --version') do set NODE_VERSION=%%v
echo [OK] Node.js: %NODE_VERSION%
echo.

:: ============ Directory Check ============
if not exist "%~dp0backend" (echo [ERROR] Missing backend & pause & exit /b 1)
if not exist "%~dp0frontend" (echo [ERROR] Missing frontend & pause & exit /b 1)

if not exist "%~dp0backend\logs" mkdir "%~dp0backend\logs"
if not exist "%~dp0backend\uploads" mkdir "%~dp0backend\uploads"

:: ============ Step 1: Database ============
echo.
echo [1/4] Initializing database (SQLite)...
pushd "%~dp0backend"

if not exist venv (
    echo   Creating Python virtual environment...
    %PY_CMD% -m venv venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create venv. Try: conda deactivate
        pause & popd & exit /b 1
    )
) else (
    echo   Using existing virtual environment
)

call venv\Scripts\activate.bat

echo   Installing Python dependencies...
%PY_CMD% -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] pip install failed.
    pause & popd & exit /b 1
)

echo.
echo   Creating database tables...
%PY_CMD% -m app.scripts.init_db
if %errorlevel% neq 0 (
    echo [ERROR] Database init failed.
    pause & popd & exit /b 1
)
popd

:: ============ Step 2: Backend ============
echo.
echo [2/4] Starting backend on port 8000...
start "RadioManager-Backend" cmd /c "cd /d %~dp0backend && call venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak >nul

:: ============ Step 3: Frontend ============
echo.
echo [3/4] Building frontend...
pushd "%~dp0frontend"
if not exist node_modules (call npm install --no-audit --no-fund)
call npm run build
if %errorlevel% neq 0 (echo [ERROR] Frontend build failed & pause & popd & exit /b 1)
popd

:: ============ Step 4: Electron ============
echo.
echo [4/4] Starting Electron...
pushd "%~dp0frontend"
call npx --yes electron . 2>nul
if %errorlevel% neq 0 (
    echo   Electron unavailable, starting web on http://localhost:5173
    start cmd /c "npm run dev"
)
popd

echo.
echo ================================================
echo   Done
echo ================================================
pause
endlocal
