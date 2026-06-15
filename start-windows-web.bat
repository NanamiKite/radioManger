@echo off
cd /d "%~dp0"
title RadioManager - Web Frontend Deployment

echo ================================================
echo   RadioManager - Web Frontend Deployment
echo   Mode: Frontend only (connect to remote backend)
echo ================================================
echo.
echo Select deployment mode:
echo   [1] LAN mode - Connect to local network backend
echo   [2] Cloud mode - Connect to cloud backend
echo   [3] Electron desktop app
echo.

set /p MODE_CHOICE="Enter option (1/2/3): "

if "%MODE_CHOICE%"=="1" (
    set RADIOMANAGER_MODE=lan
    set /p API_URL="Enter backend API URL (default: http://192.168.1.100:8000): "
    if "%API_URL%"=="" set API_URL=http://192.168.1.100:8000
    echo.
    echo LAN mode - API: %API_URL%
    set RADIOMANAGER_API_URL=%API_URL%
)

if "%MODE_CHOICE%"=="2" (
    set RADIOMANAGER_MODE=cloud
    set /p API_URL="Enter cloud API URL (e.g. https://api.example.com): "
    if "%API_URL%"=="" (
        echo [ERROR] API URL is required
        pause
        exit /b 1
    )
    echo.
    echo Cloud mode - API: %API_URL%
    set RADIOMANAGER_API_URL=%API_URL%
)

if "%MODE_CHOICE%"=="3" (
    set RADIOMANAGER_MODE=local
    goto start_electron
)

:: Web mode
echo.
echo [1/2] Installing frontend dependencies...
pushd frontend
if not exist node_modules (
    call npm install
)

echo.
echo [2/2] Starting frontend dev server...
echo   Visit: http://localhost:5173
echo.
call npm run dev
popd
goto end

:start_electron
echo.
echo [1/2] Building frontend...
pushd frontend
if not exist node_modules call npm install
call npm run build

echo.
echo [2/2] Starting Electron desktop app...
echo   Deployment mode: %RADIOMANAGER_MODE%
echo.
call npx electron .
popd

:end
pause
