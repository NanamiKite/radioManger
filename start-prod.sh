#!/bin/bash

# RadioManager 生产环境部署脚本

set -e

echo "================================================"
echo "RadioManager - 生产环境部署"
echo "================================================"

# 检查Docker
if ! command -v docker &> /dev/null; then
  echo "错误: Docker未安装"
  exit 1
fi

# 检查Docker Compose
if ! command -v docker-compose &> /dev/null; then
  echo "错误: Docker Compose未安装"
  exit 1
fi

echo ""
echo "1. 构建Docker镜像..."
docker-compose build

echo ""
echo "2. 启动容器..."
docker-compose up -d

echo ""
echo "3. 显示服务状态..."
docker-compose ps

echo ""
echo "================================================"
echo "✅ 生产环境已部署"
echo "================================================"
echo ""
echo "后端 API: http://localhost:8000"
echo "前端应用: http://localhost:5173"
echo ""
echo "查看日志: docker-compose logs -f"
echo "停止服务: docker-compose down"
echo ""
