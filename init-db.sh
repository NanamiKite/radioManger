#!/bin/bash

# RadioManager 数据库初始化脚本

set -e

echo "================================================"
echo "RadioManager - 数据库初始化"
echo "================================================"

# 检查MySQL
if ! command -v mysql &> /dev/null; then
  echo "错误: MySQL客户端未安装"
  exit 1
fi

read -p "请输入MySQL root密码: " -s MYSQL_ROOT_PASSWORD
echo ""

# 创建数据库和用户
mysql -u root -p"$MYSQL_ROOT_PASSWORD" <<EOF
CREATE DATABASE IF NOT EXISTS radiomanager 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'radiomanager'@'localhost' 
IDENTIFIED BY 'password123';

GRANT ALL PRIVILEGES ON radiomanager.* 
TO 'radiomanager'@'localhost';

GRANT ALL PRIVILEGES ON radiomanager.* 
TO 'radiomanager'@'%';

FLUSH PRIVILEGES;
EOF

echo ""
echo "✅ 数据库初始化完成"
echo "数据库: radiomanager"
echo "用户: radiomanager@localhost"
echo "密码: password123"
echo ""
echo "现在运行: python app/database/init_db.py"
echo "来创建表结构"
