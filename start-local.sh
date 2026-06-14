#!/bin/bash
#
# RadioManager 纯本地部署启动脚本
# 数据库: SQLite（无需MySQL）
# 架构: 前端(Vite) + 后端(FastAPI)
#
# 用法:
#   ./start-local.sh          # 启动开发环境
#   ./start-local.sh --build  # 先安装依赖再启动
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================"
echo "  RadioManager - 本地开发环境启动 (SQLite)"
echo "================================================"

# 创建必要目录
mkdir -p backend/logs backend/uploads

# --- 后端 ---
echo ""
echo "1. 检查Python虚拟环境..."
if [ ! -d "backend/venv" ]; then
  echo "   创建虚拟环境..."
  cd backend
  python3 -m venv venv
  source venv/bin/activate
  pip install --upgrade pip -q
  pip install -r requirements.txt -q
  cd ..
else
  source backend/venv/bin/activate
fi

# 安装 aiofiles（如果缺失）
pip install aiofiles -q 2>/dev/null || true

echo ""
echo "2. 初始化数据库 (SQLite)..."
cd backend
python -m app.scripts.init_db
cd ..

echo ""
echo "3. 启动后端服务 (FastAPI + Uvicorn)..."
cd backend
PYTHONPATH="$SCRIPT_DIR/backend" uvicorn app.main:app \
  --reload \
  --host 0.0.0.0 \
  --port 8000 &
BACKEND_PID=$!
cd ..

echo ""
echo "4. 启动前端开发服务器 (Vite)..."
cd frontend
if [ ! -d "node_modules" ]; then
  echo "   安装前端依赖..."
  npm install
fi
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "================================================"
echo "  ✅ RadioManager 本地环境已启动"
echo "================================================"
echo ""
echo "  前端应用:  http://localhost:5173"
echo "  后端 API:   http://localhost:8000"
echo "  API 文档:   http://localhost:8000/docs"
echo ""
echo "  测试账号:   admin / admin123"
echo ""
echo "  按 Ctrl+C 停止所有服务"
echo "================================================"

# 捕获退出信号
cleanup() {
  echo ""
  echo "正在停止服务..."
  kill $BACKEND_PID 2>/dev/null || true
  kill $FRONTEND_PID 2>/dev/null || true
  wait
  echo "所有服务已停止"
}

trap cleanup EXIT INT TERM

# 等待任意一个进程退出
wait $BACKEND_PID $FRONTEND_PID
