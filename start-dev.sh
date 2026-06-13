#!/bin/bash

# RadioManager 本地开发启动脚本

set -e

echo "================================================"
echo "RadioManager - 本地开发环境启动"
echo "================================================"

# 创建logs目录
mkdir -p logs

echo ""
echo "1. 创建Python虚拟环境..."
if [ ! -d "backend/venv" ]; then
  cd backend
  python3 -m venv venv
  source venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
  cd ..
else
  source backend/venv/bin/activate
fi

echo ""
echo "2. 检查MySQL连接..."
if ! command -v mysql &> /dev/null; then
  echo "警告: MySQL客户端未安装，跳过连接检查"
else
  echo "MySQL检查通过"
fi

echo ""
echo "3. 启动后端服务..."
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

echo ""
echo "4. 启动前端开发服务器..."
cd frontend
npm install
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

# 等待
wait $BACKEND_PID $FRONTEND_PID
