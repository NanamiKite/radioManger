#!/bin/bash
# RadioManager v2.4.1 Release Builder
# 构建 Windows 和 macOS 本地部署包
set -e

VERSION="2.4.1"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_VERSION="3.12.10"

echo "================================================"
echo "  RadioManager v${VERSION} Release Builder"
echo "================================================"

# ── 前端构建（共用） ──
echo ""
echo "[1/4] Building frontend..."
cd "$PROJECT_DIR/frontend"
npm run build
echo "  ✓ Frontend built"

# ── 创建共享的后端目录结构 ──
prepare_backend() {
    local target="$1"
    mkdir -p "$target/backend"
    cp -r "$PROJECT_DIR/backend/app" "$target/backend/"
    cp "$PROJECT_DIR/backend/release_server.py" "$target/backend/"
    cp "$PROJECT_DIR/backend/.env.release" "$target/backend/.env"
    cp "$PROJECT_DIR/backend/requirements.txt" "$target/backend/"
    cp -r "$PROJECT_DIR/frontend/dist" "$target/backend/frontend_dist"
    find "$target" -name "__pycache__" -exec rm -rf {} + 2>/dev/null
    find "$target" -name "*.pyc" -delete 2>/dev/null
}

# ═══════════════════════════════════════════
#  Windows 版本
# ═══════════════════════════════════════════
build_windows() {
    echo ""
    echo "[2/4] Building Windows package..."
    local WIN_DIR="$PROJECT_DIR/releases/RadioManager-${VERSION}-win64"
    rm -rf "$WIN_DIR"
    mkdir -p "$WIN_DIR/python" "$WIN_DIR/backend"

    # 后端文件
    prepare_backend "$WIN_DIR"

    # Python embeddable
    local PYTHON_ZIP="python-${PYTHON_VERSION}-embed-amd64.zip"
    if [ ! -f "/tmp/$PYTHON_ZIP" ]; then
        echo "  Downloading Python ${PYTHON_VERSION} for Windows..."
        wget -q --show-progress -O "/tmp/$PYTHON_ZIP" \
            "https://www.python.org/ftp/python/${PYTHON_VERSION}/${PYTHON_ZIP}"
    fi
    unzip -qo "/tmp/$PYTHON_ZIP" -d "$WIN_DIR/python/"
    sed -i 's/^#import site/import site/' "$WIN_DIR/python/python312._pth"

    # 下载 Windows wheels
    echo "  Downloading Windows dependencies..."
    local TEMP_REQ=$(mktemp)
    grep -v -E "pytest|coverage|uvloop|alembic|redis|mysql-connector|PyMySQL" \
        "$PROJECT_DIR/backend/requirements.txt" > "$TEMP_REQ"
    echo "uvicorn==0.49.0" >> "$TEMP_REQ"

    mkdir -p "$WIN_DIR/wheels"
    pip download -d "$WIN_DIR/wheels" \
        --platform win_amd64 --python-version 3.12 --only-binary=:all: \
        -i https://pypi.tuna.tsinghua.edu.cn/simple \
        -r "$TEMP_REQ" 2>&1 | tail -3
    rm -f "$TEMP_REQ"

    # 解压 wheel
    local SITE="$WIN_DIR/python/Lib/site-packages"
    mkdir -p "$SITE"
    for whl in "$WIN_DIR/wheels"/*.whl; do
        [ -f "$whl" ] && unzip -qo "$whl" -d "$SITE" 2>/dev/null
    done
    rm -rf "$WIN_DIR/wheels"

    # 启动脚本
    cat > "$WIN_DIR/start.bat" << 'BATEOF'
@echo off
chcp 65001 >nul 2>&1
title RadioManager v2.4.1
cd /d "%~dp0"
echo ==================================================
echo   RadioManager v2.4.1 - Amateur Radio QSO Log
echo ==================================================
echo   http://localhost:8000
echo   Press Ctrl+C to stop
echo ==================================================
set PYTHONPATH=%~dp0backend
set DATABASE_MODE=sqlite
set SQLITE_URL=sqlite:///./radiomanager.db
python\python.exe backend\release_server.py
if errorlevel 1 (
    echo.
    echo ERROR: Install Visual C++ Redistributable if DLL missing:
    echo https://aka.ms/vs/17/release/vc_redist.x64.exe
)
pause
BATEOF

    # README
    cat > "$WIN_DIR/README.txt" << 'READEOF'
RadioManager v2.4.1 - Windows 本地部署版
==========================================
1. 解压到任意目录
2. 双击 start.bat 启动
3. 浏览器打开 http://localhost:8000
4. 默认账号: admin / admin123

数据库文件: radiomanager.db (自动创建)
配置文件: backend/.env
READEOF

    # 打包
    cd "$PROJECT_DIR/releases"
    rm -f "RadioManager-${VERSION}-win64.zip"
    zip -qr "RadioManager-${VERSION}-win64.zip" "RadioManager-${VERSION}-win64/"
    echo "  ✓ Windows: releases/RadioManager-${VERSION}-win64.zip ($(du -h "RadioManager-${VERSION}-win64.zip" | cut -f1))"
}

# ═══════════════════════════════════════════
#  macOS 版本
# ═══════════════════════════════════════════
build_macos() {
    echo ""
    echo "[3/4] Building macOS package..."
    local MAC_DIR="$PROJECT_DIR/releases/RadioManager-${VERSION}-macos"
    rm -rf "$MAC_DIR"
    mkdir -p "$MAC_DIR"

    # 后端文件
    prepare_backend "$MAC_DIR"

    # macOS 启动脚本（自动检测/安装 Python，创建 venv）
    cat > "$MAC_DIR/start.sh" << 'SHEOF'
#!/bin/bash
# RadioManager v2.4.1 macOS 启动脚本
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "  RadioManager v2.4.1 - Amateur Radio QSO Log"
echo "=================================================="
echo "  http://localhost:8000"
echo "  Press Ctrl+C to stop"
echo "=================================================="

# 检查 Python
PYTHON=""
for cmd in python3.12 python3.11 python3; do
    if command -v "$cmd" &>/dev/null; then
        version=$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
        major=$(echo "$version" | cut -d. -f1)
        minor=$(echo "$version" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "ERROR: Python 3.10+ not found."
    echo "Install with: brew install python@3.12"
    echo "Or download from: https://www.python.org/downloads/"
    exit 1
fi

echo "  Using: $($PYTHON --version)"

# 创建 venv（首次）
if [ ! -d "venv" ]; then
    echo "  Creating virtual environment..."
    $PYTHON -m venv venv
    source venv/bin/activate
    pip install --upgrade pip -q
    pip install -r backend/requirements.txt -q
    echo "  ✓ Dependencies installed"
else
    source venv/bin/activate
fi

# 启动
export PYTHONPATH="$SCRIPT_DIR/backend"
export DATABASE_MODE=sqlite
export SQLITE_URL="sqlite:///./radiomanager.db"

python backend/release_server.py
SHEOF

    chmod +x "$MAC_DIR/start.sh"

    # README
    cat > "$MAC_DIR/README.txt" << 'READEOF'
RadioManager v2.4.1 - macOS 本地部署版
======================================
1. 解压到任意目录
2. 终端执行: ./start.sh
3. 浏览器打开 http://localhost:8000
4. 默认账号: admin / admin123

前置要求: Python 3.10+ (brew install python@3.12)
首次运行会自动创建 venv 并安装依赖

数据库文件: radiomanager.db (自动创建)
配置文件: backend/.env
READEOF

    # 打包
    cd "$PROJECT_DIR/releases"
    rm -f "RadioManager-${VERSION}-macos.tar.gz"
    tar czf "RadioManager-${VERSION}-macos.tar.gz" "RadioManager-${VERSION}-macos/"
    echo "  ✓ macOS: releases/RadioManager-${VERSION}-macos.tar.gz ($(du -h "RadioManager-${VERSION}-macos.tar.gz" | cut -f1))"
}

# ═══════════════════════════════════════════
#  执行
# ═══════════════════════════════════════════
mkdir -p "$PROJECT_DIR/releases"

# 支持选择性构建
case "${1:-all}" in
    win)   build_windows ;;
    mac)   build_macos ;;
    all)   build_windows; build_macos ;;
    *)     echo "Usage: $0 [win|mac|all]" ;;
esac

echo ""
echo "[4/4] Done!"
echo "================================================"
ls -lh "$PROJECT_DIR/releases/"*.zip "$PROJECT_DIR/releases/"*.tar.gz 2>/dev/null
echo "================================================"
