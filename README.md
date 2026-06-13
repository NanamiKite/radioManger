有人说我对AI的使用程度不足10%，但是我没有token可以烧，只能拿freeplan造个轮子玩玩了 
# RadioManager：一款多功能业余无线电日志管理工具

## 快速启动

### 前置条件
- Python 3.11+
- Node.js 18+
- MySQL 8.0+
- Redis 7+

### 本地开发

#### 1. 后端设置

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑.env文件，设置正确的数据库连接和其他参数

# 创建数据库
mysql -u root -p
CREATE DATABASE radiomanager CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 运行应用
python -m uvicorn app.main:app --reload
```

#### 2. 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 构建生产版本
npm run build
```

### Docker 开发

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 项目结构

```
radioManger/
├── backend/                 # 后端项目 (FastAPI)
│   ├── app/
│   │   ├── api/v1/         # API路由
│   │   ├── models/         # SQLAlchemy模型
│   │   ├── schemas/        # Pydantic模型
│   │   ├── services/       # 业务逻辑
│   │   ├── utils/          # 工具函数
│   │   ├── middleware/     # 中间件
│   │   ├── database/       # 数据库配置
│   │   ├── dependencies.py # 依赖注入
│   │   ├── config.py       # 配置管理
│   │   └── main.py         # FastAPI应用入口
│   ├── requirements.txt    # Python依赖
│   ├── .env.example        # 环境变量示例
│   ├── Dockerfile          # Docker镜像配置
│   └── tests/              # 测试文件
│
├── frontend/               # 前端项目 (Vue3 + TypeScript)
│   ├── src/
│   │   ├── api/            # API客户端
│   │   ├── components/     # Vue组件
│   │   ├── views/          # 页面
│   │   ├── stores/         # Pinia状态管理
│   │   ├── router/         # Vue Router
│   │   ├── utils/          # 工具函数
│   │   ├── types/          # TypeScript类型定义
│   │   ├── styles/         # 样式文件
│   │   ├── App.vue         # 根组件
│   │   └── main.ts         # 入口文件
│   ├── package.json        # 依赖配置
│   ├── vite.config.ts      # Vite配置
│   ├── tsconfig.json       # TypeScript配置
│   ├── Dockerfile          # Docker镜像配置
│   └── index.html          # HTML入口
│
├── docker-compose.yml      # Docker Compose配置
├── .gitignore              # Git忽略列表
└── README.md               # 项目说明
```

## API文档

启动后端后，访问以下地址查看API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 数据库

应用使用MySQL存储数据。数据库结构在设计文档 `02_数据库设计说明.md` 中详细说明。

## 环境变量

参考 `backend/.env.example` 配置文件。关键变量：
- `DATABASE_URL`: MySQL连接字符串
- `SECRET_KEY`: JWT加密密钥
- `REDIS_URL`: Redis连接地址
- `CORS_ORIGINS`: 允许的CORS源

## 常见问题

### 1. MySQL连接错误
确保MySQL服务运行，且环境变量中的连接信息正确。

### 2. 前端无法连接后端
检查环境变量中的API基础URL，确保后端服务正在运行。

### 3. Docker构建失败
清除构建缓存: `docker-compose build --no-cache`

## 部署

参考设计文档 `06_部署说明.md` 了解详细的部署步骤。

## 许可证

MIT License
