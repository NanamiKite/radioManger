#!/bin/bash

# RadioManager 开发环境启动脚本
# 数据库: 自动选择 SQLite（默认）或 MySQL
#
# 用法:
#   ./start-dev.sh             # 使用 SQLite (默认)
#   DATABASE_MODE=mysql ./start-dev.sh  # 使用 MySQL

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================"
echo "RadioManager - 开发环境启动"
echo "================================================"

# 创建必要目录
mkdir -p backend/logs backend/uploads

echo ""
echo "1. 设置数据库模式..."
DB_MODE="${DATABASE_MODE:-sqlite}"
echo "   数据库模式: $DB_MODE"
export DATABASE_MODE=$DB_MODE

echo ""
echo "2. 检查Python虚拟环境..."
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

echo ""
echo "3. 初始化数据库..."
cd backend
python -m app.scripts.init_db
cd ..

echo ""
echo "4. 启动后端服务..."
cd backend
PYTHONPATH="$SCRIPT_DIR/backend" uvicorn app.main:app \
  --reload \
  --host 0.0.0.0 \
  --port 8000 &
BACKEND_PID=$!
cd ..

echo ""
echo "5. 启动前端开发服务器..."
cd frontend
if [ ! -d "node_modules" ]; then
  npm install
fi
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "================================================"
echo "✅ 开发环境已启动"
echo "================================================"
echo ""
echo "后端 API: http://localhost:8000"
echo "API 文档: http://localhost:8000/docs"
echo "前端应用: http://localhost:5173"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo ""

cleanup() {
  echo "正在停止服务..."
  kill $BACKEND_PID 2>/dev/null || true
  kill $FRONTEND_PID 2>/dev/null || true
  wait
}
trap cleanup EXIT INT TERM

wait $BACKEND_PID $FRONTEND_PID
