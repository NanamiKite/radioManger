#!/bin/bash
# RadioManager - 服务器模式本地测试启动脚本
# 使用系统已有的 MySQL，后端本地运行
# 用法: ./start-server-mode.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

DB_USER="radiomanager"
DB_PASS="password123"
DB_NAME="radiomanager"
ADMIN_USER="admin"
ADMIN_PASS="admin123"
ADMIN_EMAIL="admin@radiomanager.local"

echo "================================================"
echo "  RadioManager - 服务器模式本地测试"
echo "  MySQL + (Redis 可选，无则降级内存)"
echo "================================================"
echo ""

# ── 1. 检查 MySQL ──
echo "1. 检查 MySQL..."
if ! mysql -u $DB_USER -p$DB_PASS -e "SELECT 1" &>/dev/null; then
    echo -e "${RED}❌ 无法连接 MySQL (user=$DB_USER)${NC}"
    echo "   请先创建用户:"
    echo "   sudo mysql -e \"CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS';\""
    echo "   sudo mysql -e \"GRANT ALL ON $DB_NAME.* TO '$DB_USER'@'localhost'; FLUSH PRIVILEGES;\""
    exit 1
fi
echo -e "${GREEN}✅ MySQL 连接成功${NC}"

# 确保数据库存在
mysql -u $DB_USER -p$DB_PASS -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null

# ── 2. 检查 Redis（可选）──
echo ""
echo "2. 检查 Redis..."
if command -v redis-cli &>/dev/null && redis-cli ping &>/dev/null 2>&1; then
    REDIS_URL="redis://localhost:6379"
    echo -e "${GREEN}✅ Redis 可用${NC}"
else
    REDIS_URL=""
    echo -e "${YELLOW}⚠️  Redis 不可用，Token 黑名单和缓存将使用内存（重启后失效）${NC}"
fi

# ── 3. 配置后端 .env ──
echo ""
echo "3. 写入 backend/.env..."
ENV_FILE="backend/.env"

cat > $ENV_FILE << EOF
# RadioManager 服务器模式本地测试配置
APP_NAME=RadioManager
DEBUG=true
WORKERS=1

DATABASE_MODE=mysql
DATABASE_URL=mysql+pymysql://${DB_USER}:${DB_PASS}@localhost:3306/${DB_NAME}
SQLALCHEMY_ECHO=false

SECRET_KEY=radioManager-local-test-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
REFRESH_TOKEN_EXPIRE_DAYS=30

CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","http://localhost:7777"]

REDIS_URL=${REDIS_URL:-redis://localhost:6379}

QRZ_USERNAME=
QRZ_PASSWORD=

ADMIN_USERNAME=${ADMIN_USER}
ADMIN_PASSWORD=${ADMIN_PASS}
ADMIN_EMAIL=${ADMIN_EMAIL}

ENABLE_TEST_ACCOUNT=false

SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
FROM_EMAIL=noreply@radiomanager.local

LOG_LEVEL=DEBUG
LOG_FILE=logs/app.log

MAX_UPLOAD_SIZE=104857600
UPLOAD_DIR=uploads
EOF

echo -e "${GREEN}✅ backend/.env 已写入${NC}"

# ── 4. Python 虚拟环境 ──
echo ""
echo "4. 检查 Python 虚拟环境..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt -q
    echo -e "${GREEN}   ✅ 虚拟环境已创建${NC}"
else
    source venv/bin/activate
    echo "   虚拟环境已存在"
fi

# ── 5. 初始化数据库 + 创建管理员 ──
echo ""
echo "5. 初始化 MySQL 数据库..."
python -m app.scripts.init_db
echo -e "${GREEN}✅ 数据库初始化完成${NC}"

# ── 6. 启动后端 ──
echo ""
echo "================================================"
echo -e "  ${CYAN}启动后端 (MySQL 服务器模式)...${NC}"
echo ""
echo -e "  管理员账号:  ${YELLOW}${ADMIN_USER} / ${ADMIN_PASS}${NC}"
echo "  数据库:      MySQL (localhost:3306/$DB_NAME)"
if [ -n "$REDIS_URL" ]; then
    echo "  Redis:       localhost:6379"
else
    echo "  Redis:       未安装 (降级内存模式)"
fi
echo ""
echo "  后端 API:    http://localhost:8000"
echo "  API 文档:    http://localhost:8000/docs"
echo ""
echo "  前端请另开终端运行:"
echo "    cd frontend && npm run dev"
echo ""
echo "  停止: Ctrl+C"
echo "================================================"
echo ""

cd ..
cd backend
source venv/bin/activate
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
