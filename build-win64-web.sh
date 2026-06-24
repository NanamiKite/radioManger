#!/bin/bash
# RadioManager v2.5.0 Win64 Web 本地部署包构建脚本
# 用法: ./build-win64-web.sh
# 不修改任何项目源码，仅在 releases/ 输出打包文件

set -e

VERSION="2.5.0"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
RELEASES_DIR="$PROJECT_DIR/releases"
BUILD_NAME="RadioManager-${VERSION}-win64-web"
BUILD_DIR="$RELEASES_DIR/$BUILD_NAME"
PYTHON_VERSION="3.12.10"
NODE_VERSION="22.16.0"

echo "================================================"
echo "  RadioManager v${VERSION} Win64 Web 构建"
echo "================================================"

# ── 0. 清理旧构建 ──
echo ""
echo "[0/6] 清理旧构建..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# ── 1. 构建前端 ──
echo ""
echo "[1/6] 构建前端 (npm run build)..."
cd "$PROJECT_DIR/frontend"
npm run build
echo "  ✅ 前端构建完成"

# ── 2. 复制后端代码 ──
echo ""
echo "[2/6] 复制后端代码..."
mkdir -p "$BUILD_DIR/backend"
cp -r "$PROJECT_DIR/backend/app" "$BUILD_DIR/backend/"
cp "$PROJECT_DIR/backend/release_server.py" "$BUILD_DIR/backend/"
# 版本号替换（仅修改构建产物，不动源码）
sed -i 's/v2\.4\.1/v2.5.0/g' "$BUILD_DIR/backend/release_server.py"
cp "$PROJECT_DIR/backend/requirements.txt" "$BUILD_DIR/backend/"
cp -r "$PROJECT_DIR/frontend/dist" "$BUILD_DIR/backend/frontend_dist"
# 清理缓存
find "$BUILD_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find "$BUILD_DIR" -name "*.pyc" -delete 2>/dev/null
echo "  ✅ 后端代码已复制"

# ── 3. 写入 release .env ──
echo ""
echo "[3/6] 写入配置文件..."
cat > "$BUILD_DIR/backend/.env" << 'ENVEOF'
# RadioManager v2.5.0 Release Configuration
DATABASE_MODE=sqlite
SQLITE_URL=sqlite:///./radiomanager.db
SECRET_KEY=CHANGE_THIS_TO_A_RANDOM_STRING
ENABLE_TEST_ACCOUNT=true
TEST_ACCOUNT_USERNAME=admin
TEST_ACCOUNT_PASSWORD=admin123
TEST_ACCOUNT_EMAIL=admin@radiomanager.dev
DEBUG=false
ENVIRONMENT=production
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE=104857600
ENVEOF
echo "  ✅ .env 已写入"

# ── 4. 下载 Python embeddable ──
echo ""
echo "[4/6] 下载 Python ${PYTHON_VERSION} embeddable (win64)..."
PYTHON_ZIP="python-${PYTHON_VERSION}-embed-amd64.zip"
if [ ! -f "/tmp/$PYTHON_ZIP" ]; then
    wget -q --show-progress -O "/tmp/$PYTHON_ZIP" \
        "https://www.python.org/ftp/python/${PYTHON_VERSION}/${PYTHON_ZIP}"
fi
mkdir -p "$BUILD_DIR/python"
unzip -qo "/tmp/$PYTHON_ZIP" -d "$BUILD_DIR/python/"
# 启用 import site（pip 需要）
sed -i 's/^#import site/import site/' "$BUILD_DIR/python/python312._pth"
echo "  ✅ Python embeddable 已解压"

# ── 5. 下载 Node.js portable ──
echo ""
echo "[5/6] 下载 Node.js v${NODE_VERSION} portable (win64)..."
NODE_ZIP="node-v${NODE_VERSION}-win-x64.zip"
NODE_DIR_NAME="node-v${NODE_VERSION}-win-x64"
if [ ! -f "/tmp/$NODE_ZIP" ]; then
    wget -q --show-progress -O "/tmp/$NODE_ZIP" \
        "https://nodejs.org/dist/v${NODE_VERSION}/${NODE_ZIP}"
fi
unzip -qo "/tmp/$NODE_ZIP" -d "/tmp/" 2>/dev/null
mv "/tmp/$NODE_DIR_NAME" "$BUILD_DIR/node"
echo "  ✅ Node.js portable 已解压"

# ── 6. 下载 Python wheels (win64) ──
echo ""
echo "[6/6] 下载 Python 依赖 (win64 wheels)..."
TEMP_REQ=$(mktemp)
grep -v -E "pytest|coverage|uvloop|alembic|redis|mysql-connector|PyMySQL" \
    "$PROJECT_DIR/backend/requirements.txt" > "$TEMP_REQ"
echo "uvicorn==0.49.0" >> "$TEMP_REQ"

mkdir -p "$BUILD_DIR/wheels"
pip download -d "$BUILD_DIR/wheels" \
    --platform win_amd64 --python-version 3.12 --only-binary=:all: \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    -r "$TEMP_REQ" 2>&1 | tail -3
rm -f "$TEMP_REQ"

# 解压 wheel 到 site-packages
SITE="$BUILD_DIR/python/Lib/site-packages"
mkdir -p "$SITE"
for whl in "$BUILD_DIR/wheels"/*.whl; do
    [ -f "$whl" ] && unzip -qo "$whl" -d "$SITE" 2>/dev/null
done
rm -rf "$BUILD_DIR/wheels"
echo "  ✅ Python 依赖已安装"

# ── 创建启动脚本 ──
echo ""
echo "创建启动脚本..."

# start.bat - 启动后端 (release_server.py 内嵌前端)
cat > "$BUILD_DIR/start.bat" << 'BATEOF'
@echo off
chcp 65001 >nul 2>&1
title RadioManager v2.5.0
cd /d "%~dp0"

echo ==================================================
echo   RadioManager v2.5.0 - Amateur Radio QSO Log
echo ==================================================
echo.
echo   Web UI:  http://localhost:8000
echo   API Doc: http://localhost:8000/docs
echo.
echo   Default: admin / admin123
echo   Press Ctrl+C to stop
echo ==================================================
echo.

set PYTHONPATH=%~dp0backend
set DATABASE_MODE=sqlite
set SQLITE_URL=sqlite:///./radiomanager.db

python\python.exe backend\release_server.py
if errorlevel 1 (
    echo.
    echo ERROR: If DLL missing, install VC++ Redistributable:
    echo https://aka.ms/vs/17/release/vc_redist.x64.exe
)
pause
BATEOF

# start-dev.bat - 开发模式 (前端热更新)
cat > "$BUILD_DIR/start-dev.bat" << 'BATEOF'
@echo off
chcp 65001 >nul 2>&1
title RadioManager v2.5.0 [DEV]
cd /d "%~dp0"

echo ==================================================
echo   RadioManager v2.5.0 - Development Mode
echo ==================================================
echo.
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000
echo   API Doc:  http://localhost:8000/docs
echo.
echo   Default: admin / admin123
echo   Press Ctrl+C to stop both
echo ==================================================
echo.

set PYTHONPATH=%~dp0backend
set DATABASE_MODE=sqlite
set SQLITE_URL=sqlite:///./radiomanager.db

:: 启动后端
start "RadioManager Backend" /D "%~dp0backend" python\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

:: 等待后端启动
timeout /t 3 /nobreak >nul

:: 启动前端
cd /d "%~dp0"
node\npm.cmd run --prefix frontend dev

:: 停止后端
taskkill /FI "WINDOWTITLE eq RadioManager Backend*" /F >nul 2>&1
pause
BATEOF

# README
cat > "$BUILD_DIR/README.txt" << 'READEOF'
RadioManager v2.5.0 - Windows 64-bit 本地部署版
================================================

快速启动（推荐）:
  1. 解压到任意目录
  2. 双击 start.bat
  3. 浏览器打开 http://localhost:8000
  4. 默认账号: admin / admin123

开发模式（前端热更新）:
  1. 双击 start-dev.bat
  2. 浏览器打开 http://localhost:5173

目录结构:
  start.bat          - 生产模式启动（内嵌前端）
  start-dev.bat      - 开发模式启动（前端热更新）
  python/            - Python 3.12 运行时
  node/              - Node.js 22 运行时
  backend/           - 后端代码 + 前端构建产物
  backend/.env       - 配置文件
  backend/app/       - 应用代码

数据文件（自动创建）:
  radiomanager.db    - SQLite 数据库
  backend/uploads/   - 上传文件
  backend/logs/      - 日志文件

如遇 DLL 缺失错误，请安装:
  https://aka.ms/vs/17/release/vc_redist.x64.exe
READEOF

echo "  ✅ 启动脚本已创建"

# ── 打包 ──
echo ""
echo "打包中..."
cd "$RELEASES_DIR"
rm -f "${BUILD_NAME}.zip"
zip -qr "${BUILD_NAME}.zip" "$BUILD_NAME/"

# 统计
ZIP_SIZE=$(du -h "${BUILD_NAME}.zip" | cut -f1)
DIR_SIZE=$(du -sh "$BUILD_DIR" | cut -f1)

echo ""
echo "================================================"
echo "  ✅ 构建完成!"
echo ""
echo "  包名: ${BUILD_NAME}.zip"
echo "  大小: ${ZIP_SIZE} (压缩) / ${DIR_SIZE} (解压)"
echo "  路径: releases/${BUILD_NAME}.zip"
echo ""
echo "  包含:"
echo "    - Python ${PYTHON_VERSION} embeddable"
echo "    - Node.js v${NODE_VERSION} portable"
echo "    - 后端代码 + Python 依赖 (wheels)"
echo "    - 前端构建产物 (dist)"
echo "    - 启动脚本 (start.bat / start-dev.bat)"
echo "================================================"
