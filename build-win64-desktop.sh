#!/bin/bash
# RadioManager v2.5.0 Win64 Desktop 构建脚本
# 使用 pywebview + Edge WebView2 原生窗口，不是浏览器
# 用法: ./build-win64-desktop.sh

set -e

VERSION="2.5.0"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
RELEASES_DIR="$PROJECT_DIR/releases"
BUILD_NAME="RadioManager-${VERSION}-win64-desktop"
BUILD_DIR="$RELEASES_DIR/$BUILD_NAME"
PYTHON_VERSION="3.12.10"

echo "================================================"
echo "  RadioManager v${VERSION} Win64 Desktop 构建"
echo "  (pywebview + Edge WebView2 原生窗口)"
echo "================================================"

# ── 0. 清理 ──
echo ""
echo "[0/6] 清理旧构建..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# ── 1. 构建前端 ──
echo ""
echo "[1/6] 构建前端..."
cd "$PROJECT_DIR/frontend"
npm run build
echo "  ✅ 前端构建完成"

# ── 2. 准备后端代码 ──
echo ""
echo "[2/6] 准备后端代码..."
mkdir -p "$BUILD_DIR/backend"
cp -r "$PROJECT_DIR/backend/app" "$BUILD_DIR/backend/"
cp "$PROJECT_DIR/backend/release_server.py" "$BUILD_DIR/backend/"
cp "$PROJECT_DIR/backend/desktop_launcher.py" "$BUILD_DIR/backend/"
cp "$PROJECT_DIR/backend/requirements.txt" "$BUILD_DIR/backend/"
cp -r "$PROJECT_DIR/frontend/dist" "$BUILD_DIR/backend/frontend_dist"
cat > "$BUILD_DIR/backend/.env" << 'EOF'
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
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE=104857600
EOF
find "$BUILD_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find "$BUILD_DIR" -name "*.pyc" -delete 2>/dev/null
sed -i 's/v2\.4\.1/v2.5.0/g' "$BUILD_DIR/backend/release_server.py"
echo "  ✅ 后端代码就绪"

# ── 3. 下载 Python embeddable ──
echo ""
echo "[3/6] 下载 Python ${PYTHON_VERSION} embeddable..."
PYTHON_ZIP="python-${PYTHON_VERSION}-embed-amd64.zip"
if [ ! -f "/tmp/$PYTHON_ZIP" ]; then
    wget -q --show-progress -O "/tmp/$PYTHON_ZIP" \
        "https://www.python.org/ftp/python/${PYTHON_VERSION}/${PYTHON_ZIP}"
fi
mkdir -p "$BUILD_DIR/python"
unzip -qo "/tmp/$PYTHON_ZIP" -d "$BUILD_DIR/python/"
# 不取消注释 import site（会读到系统 Python），改为直接写入嵌入式 site-packages 路径
PTH_FILE="$BUILD_DIR/python/python312._pth"
cat > "$PTH_FILE" << 'PTHEOF'
python312.zip
.
Lib/site-packages
PTHEOF
echo "  ✅ Python 就绪"

# ── 4. 下载 Python wheels ──
echo ""
echo "[4/6] 下载 Python 依赖 (win64 wheels)..."
TEMP_REQ=$(mktemp)
grep -v -E "pytest|coverage|uvloop|alembic|redis|mysql-connector|PyMySQL" \
    "$PROJECT_DIR/backend/requirements.txt" > "$TEMP_REQ"
echo "uvicorn==0.49.0" >> "$TEMP_REQ"
echo "pywebview==6.2.1" >> "$TEMP_REQ"
echo "bottle==0.13.4" >> "$TEMP_REQ"

mkdir -p "$BUILD_DIR/wheels"
# 第一步：下载带 C 扩展的包的 win64 wheels
pip download -d "$BUILD_DIR/wheels" \
    --platform win_amd64 --python-version 3.12 --only-binary=:all: \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    pydantic-core bcrypt watchfiles greenlet Mako MarkupSafe cffi cryptography PyYAML \
    httptools pydantic SQLAlchemy httpx requests pythonnet 2>&1 | tail -3
# 第二步：下载全部依赖的纯 Python 包（不限平台）
pip download -d "$BUILD_DIR/wheels" \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    -r "$TEMP_REQ" 2>&1 | tail -3
# pywebview 及其依赖（pythonnet 是 Windows 上 pywebview 的必需依赖）
pip download -d "$BUILD_DIR/wheels" \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    pywebview==6.2.1 bottle==0.13.4 proxy_tools pythonnet 2>&1 | tail -3
rm -f "$TEMP_REQ"

SITE="$BUILD_DIR/python/Lib/site-packages"
mkdir -p "$SITE"
# 先提取 win64 二进制 wheels（带平台标识的优先）
for whl in "$BUILD_DIR/wheels"/*win_amd64*.whl "$BUILD_DIR/wheels"/*win32*.whl; do
    [ -f "$whl" ] && unzip -qo "$whl" -d "$SITE" 2>/dev/null
done
# 再提取通用 wheels 和纯 Python 包
for whl in "$BUILD_DIR/wheels"/*.whl; do
    [ -f "$whl" ] && unzip -qo "$whl" -d "$SITE" 2>/dev/null
done
# tar.gz 用 pip install --target 安装（正确处理 setup.py）
for tarball in "$BUILD_DIR/wheels"/*.tar.gz; do
    [ -f "$tarball" ] && pip install --target="$SITE" --no-deps "$tarball" 2>&1 | tail -1
done
rm -rf "$BUILD_DIR/wheels"

# 验证关键依赖
MISSING=""
for pkg in uvicorn fastapi sqlalchemy starlette pydantic sniffio anyio webview proxy_tools; do
    [ ! -d "$SITE/$pkg" ] && [ ! -f "$SITE/$pkg.py" ] && MISSING="$MISSING $pkg"
done
if [ -n "$MISSING" ]; then
    echo "  ❌ 缺少依赖:$MISSING"
    exit 1
fi
echo "  ✅ Python 依赖就绪 ($(ls "$SITE" | wc -l) 个包)"

# ── 5. 创建启动器 ──
echo ""
echo "[5/6] 创建启动器..."

# .bat 启动器（双击运行，使用 pythonw 无控制台窗口）
cat > "$BUILD_DIR/RadioManager.bat" << 'BATEOF'
@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
start "" python\pythonw.exe backend\desktop_launcher.py
BATEOF

# .vbs 启动器（完全无窗口，双击此文件启动）
cat > "$BUILD_DIR/RadioManager.vbs" << 'VBSEOF'
Set fso = CreateObject("Scripting.FileSystemObject")
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.Run fso.BuildPath(WshShell.CurrentDirectory, "python\pythonw.exe") & " backend\desktop_launcher.py", 0, False
VBSEOF

# README
cat > "$BUILD_DIR/README.txt" << READEOF
RadioManager v${VERSION} - Windows 64-bit 桌面版
================================================

启动方式（任选一种）:
  方式1: 双击 RadioManager.bat
  方式2: 双击 RadioManager.vbs（完全无窗口）

启动后会打开一个原生桌面窗口，不是浏览器。
数据库保存在 data/ 文件夹中。

默认账号: admin / admin123

技术说明:
  - 使用 Edge WebView2（Windows 10/11 自带）
  - 无需安装浏览器或任何依赖
  - Python 运行时已内置

目录结构:
  RadioManager.bat  - 启动器（有命令行闪现）
  RadioManager.vbs  - 启动器（无窗口）
  python/           - Python 3.12 运行时
  backend/          - 应用代码 + 前端产物
  data/             - 数据库文件（自动创建）
READEOF

echo "  ✅ 启动器就绪"

# ── 6. 打包 ──
echo ""
echo "[6/6] 打包..."
cd "$RELEASES_DIR"
rm -f "${BUILD_NAME}.zip"
zip -qr "${BUILD_NAME}.zip" "$BUILD_NAME/"

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
echo "    - Python 3.12.10 embeddable"
echo "    - pywebview + 后端全部依赖 (预装)"
echo "    - 后端代码 + 前端构建产物"
echo "    - 启动器 (RadioManager.bat / .vbs)"
echo ""
echo "  原生桌面窗口，不是浏览器"
echo "  Windows 10/11 自带 Edge WebView2"
echo "================================================"
