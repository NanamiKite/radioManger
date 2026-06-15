有人说我对AI的使用程度不足10%，但是我没有token可以烧，只能拿freeplan造个轮子玩玩了

# RadioManager — 业余无线电日志管理工具 V2.1.0

一款基于 FastAPI + Vue3 + Electron 的跨平台业余无线电日志管理系统。支持 **Windows** / **Linux** / **Android** 三端部署，提供 SQLite 本地部署与 MySQL 云端部署，具备日志管理、台站与位置管理、呼号查询、回收站、统计分析等功能。

## 快速启动

### Linux / macOS 本地开发 (SQLite)
```bash
./start-local.sh
```

### Windows 本地部署
```batch
双击 start-windows-local.bat
```

### Windows Web 前端 (连接远程后端)
```batch
双击 start-windows-web.bat
```

## 手动启动

```bash
# 后端
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
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
├── backend/                          # FastAPI 后端 (Python 3.10+)
│   └── app/
│       ├── api/v1/                  # 9 个路由模块
│       ├── models/                  # 9 个 SQLAlchemy 模型
│       ├── schemas/                 # Pydantic V2 模式
│       ├── services/                # 业务服务层
│       ├── utils/                   # 工具模块
│       ├── middleware/              # 中间件
│       ├── database/                # 数据库引擎
│       └── scripts/                 # 部署脚本
│
├── frontend/                         # Vue 3 + TypeScript
│   ├── src/                         # 前端源码
│   │   ├── api/                     # API 客户端
│   │   ├── views/                   # 11 个页面视图
│   │   ├── stores/                  # Pinia 状态管理
│   │   ├── router/                  # Vue Router
│   │   └── locales/                 # i18n (zh-CN + en-US)
│   ├── electron/                    # Electron 主进程
│   ├── public/                      # PWA 资源
│   ├── capacitor.config.ts          # Android 打包配置
│   └── package.json                 # 含 Electron/Capacitor 构建脚本
│
├── doc/                             # 设计文档
├── start-local.sh                   # Linux/macOS 本地启动
├── start-windows-local.bat          # Windows 本地启动
├── start-windows-web.bat            # Windows Web 启动
├── docker-compose.yml               # Docker 编排
└── nginx.conf                       # Nginx 反向代理
```

## 技术栈

| 层 | 技术 |
|---|------|
| **前端** | Vue 3 + TypeScript + Vite + Element Plus + Pinia |
| **桌面端** | Electron (Win/Linux/Mac) |
| **移动端** | PWA / Capacitor Android |
| **后端** | FastAPI + SQLAlchemy + Pydantic V2 |
| **数据库** | SQLite（本地）/ MySQL 8.0+（生产） |
| **容器化** | Docker + Docker Compose |

## 部署方式

| 模式 | 前端 | 后端 | 启动方式 |
|------|------|------|---------|
| **本地 (Linux)** | Vite | SQLite | `./start-local.sh` |
| **本地 (Windows)** | Electron | SQLite | `start-windows-local.bat` |
| **Web 前端 (Windows)** | Web | 远程后端 | `start-windows-web.bat` |
| **局域网** | Web | Docker | `docker-compose up` |
| **云服务器** | Nginx | Docker | `docker-compose up` |
| **Android** | APK/PWA | 远程后端 | `npm run android:build` |

## 构建命令

```bash
cd frontend

# Electron 打包
npm run electron:win            # Windows 安装程序
npm run electron:win-portable   # Windows 便携版
npm run electron:linux          # Linux AppImage/deb
npm run electron:mac            # macOS DMG

# Android APK (需要 Android SDK)
npm run android:init            # 首次初始化
npm run android:build           # 构建 APK
```

## 许可证

MIT License
