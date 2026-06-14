# RadioManager — 业余无线电日志管理工具

一款基于 FastAPI + Vue3 的跨平台业余无线电日志管理系统。支持 SQLite 本地部署与 MySQL 云端部署，提供日志管理、台站与位置管理、呼号查询、统计分析等功能。

## 快速启动（本地开发，SQLite）

```bash
# 一键启动
./start-local.sh
```

或手动：

```bash
# 后端
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.scripts.init_db
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端
cd frontend
npm install
npm run dev
```

- 前端: http://localhost:5173
- API 文档: http://localhost:8000/docs
- 测试账号: `admin` / `admin123`

## 项目结构

```
radioManger/
├── backend/                          # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/                  # 9 个路由模块
│   │   │   ├── auth.py              # 认证
│   │   │   ├── users.py             # 用户
│   │   │   ├── logs.py              # 日志 (含导入导出)
│   │   │   ├── stations.py          # 台站
│   │   │   ├── locations.py         # 位置
│   │   │   ├── stats.py             # 统计
│   │   │   ├── callsigns.py         # 呼号查询
│   │   │   ├── sync.py              # 数据同步
│   │   │   └── shortcuts.py         # 快捷链接
│   │   ├── models/                  # 9 个 SQLAlchemy 模型
│   │   ├── schemas/                 # Pydantic V2 模式
│   │   ├── services/                # 10 个业务服务
│   │   ├── utils/                   # 7 个工具模块
│   │   ├── middleware/              # 3 个中间件
│   │   ├── database/                # 数据库引擎与会话
│   │   ├── scripts/                 # 初始化与部署脚本
│   │   ├── config.py                # 配置管理
│   │   ├── dependencies.py          # 依赖注入
│   │   └── main.py                  # FastAPI 入口
│   ├── tests/                       # 测试套件
│   └── requirements.txt
│
├── frontend/                         # Vue 3 + TypeScript
│   ├── src/
│   │   ├── api/                     # 10 个 API 客户端模块
│   │   ├── views/                   # 10 个页面视图
│   │   ├── stores/                  # Pinia 状态管理
│   │   ├── router/                  # Vue Router 路由
│   │   ├── types/                   # TypeScript 类型定义
│   │   ├── locales/                 # i18n 国际化 (zh-CN + en-US)
│   │   ├── utils/                   # 工具函数
│   │   ├── styles/                  # 样式文件
│   │   ├── App.vue                  # 根组件
│   │   └── main.ts                  # 入口文件
│   ├── electron/                    # Electron 主进程
│   ├── package.json
│   └── vite.config.ts
│
├── doc/                             # 设计文档
├── start-local.sh                   # 本地一键启动脚本
├── start-dev.sh                     # 开发环境启动脚本
├── docker-compose.yml               # Docker 编排
└── nginx.conf                       # Nginx 反向代理配置
```

## 技术栈

| 层 | 技术 |
|---|------|
| **前端** | Vue 3 + TypeScript + Vite + Element Plus + Pinia + Vue Router |
| **后端** | FastAPI + SQLAlchemy + Pydantic V2 |
| **数据库** | SQLite（本地）/ MySQL 8.0+（生产） |
| **桌面端** | Electron（可选） |
| **容器化** | Docker + Docker Compose |

## 数据库模式

支持 `DATABASE_MODE=sqlite`（默认）和 `DATABASE_MODE=mysql`：

```bash
# 使用 SQLite（默认，无需安装 MySQL）
DATABASE_MODE=sqlite ./start-dev.sh

# 使用 MySQL
DATABASE_MODE=mysql ./start-dev.sh
```

## 部署方式

- **纯本地部署**：SQLite + 可选后端，`./start-local.sh`
- **局域网部署**：Docker + MySQL，`docker-compose up -d`
- **云服务器部署**：Docker + Nginx + SSL，参考 `doc/06_部署说明.md`

## 文档

设计文档位于 `doc/` 目录，包含：项目总说明、数据库设计、API 设计、前后端架构、部署说明、系统架构图。

## 许可证

MIT License
