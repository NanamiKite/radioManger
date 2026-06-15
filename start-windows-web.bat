@echo off
chcp 65001 >nul
title RadioManager - Web前端部署

echo ================================================
echo   RadioManager - Web前端部署
echo   模式: 仅前端 (连接远程后端)
echo   适用: 局域网/云服务器前端访问
echo ================================================
echo.
echo 请选择部署模式:
echo   [1] 局域网模式 - 连接局域网内的后端服务器
echo   [2] 云服务器模式 - 连接云端后端服务器
echo   [3] Electron桌面应用
echo.

set /p MODE_CHOICE="请输入选项 (1/2/3): "

if "%MODE_CHOICE%"=="1" (
    set RADIOMANAGER_MODE=lan
    set /p API_URL="请输入后端API地址 (默认 http://192.168.1.100:8000): "
    if "%API_URL%"=="" set API_URL=http://192.168.1.100:8000
    echo.
    echo 局域网模式 - API: %API_URL%
    set RADIOMANAGER_API_URL=%API_URL%
)

if "%MODE_CHOICE%"=="2" (
    set RADIOMANAGER_MODE=cloud
    set /p API_URL="请输入云服务器API地址 (例如 https://api.example.com): "
    if "%API_URL%"=="" (
        echo [错误] 必须输入API地址
        pause
        exit /b 1
    )
    echo.
    echo 云服务器模式 - API: %API_URL%
    set RADIOMANAGER_API_URL=%API_URL%
)

if "%MODE_CHOICE%"=="3" (
    set RADIOMANAGER_MODE=local
    goto start_electron
)

:: Web模式 - 构建并启动前端
echo.
echo [1/2] 安装前端依赖...
cd frontend
if not exist node_modules (
    call npm install
)

echo.
echo [2/2] 启动前端开发服务器...
echo   访问地址: http://localhost:5173
echo.
call npm run dev
cd ..
goto end

:start_electron
echo.
echo [1/2] 构建前端...
cd frontend
if not exist node_modules call npm install
call npm run build

echo.
echo [2/2] 启动 Electron 桌面应用...
echo   部署模式: %RADIOMANAGER_MODE%
echo.
call npx electron .
cd ..

:end
pause
