---
name: radio-manager-archive
description: RadioManager 业余电台 QSO 日志管理系统 V2.1.0 项目知识归档。whenever 用户提到 radioManager、radioManger、业余电台、ham radio、QSO日志、项目背景、项目介绍、项目架构、代码结构、技术栈、数据库设计、API接口、部署方式、项目说明 时都应触发，或需要快速了解本项目的完整技术上下文时触发。
---

# RadioManager V2.1.0 — 项目知识归档

> 跨平台业余电台 (Ham Radio) QSO 联络日志管理系统。支持 ADIF 标准导入导出、呼号查询、DXCC 实体识别、QSL/eQSL/LoTW 追踪、统计分析、多平台部署。

---

## 一、项目概述

| 项 | 值 |
|---|---|
| 项目名 | RadioManager |
| 版本 | V2.1.0 |
| 作者 | Nanami Kite |
| 许可证 | MIT |
| 仓库 | `https://github.com/NanamiKite/radioManger` |
| 语言 | 中文优先（文档、注释、变量名均为中文） |

### 核心功能

- **QSO 日志 CRUD** — 完整 ADIF 标准字段（呼号、日期时间、频率、波段、模式、RST 报告、QSL 状态等 30+ 字段）
- **电台/位置管理** — 每用户多电台（呼号），每电台多位置（网格定位、设备型号、天线信息），单用户仅一个激活位置
- **ADI/ADIF 导入导出** — 兼容 WSJT-X 等电台软件，批量导入（500 条/批次），自动去重
- **三级呼号查询** — 本地缓存（30天 TTL）→ QRZ.com XML API → 离线 DXCC 前缀推断（340+ 实体前缀表）
- **回收站** — 软删除日志 JSON 备份，7 天保留，支持恢复
- **统计面板** — 总 QSO 数、DXCC 实体数、QSL/eQSL/LoTW 计数、最近联络日期，支持电台级别筛选
- **快捷链接** — 内置 QRZ.com、ARRL DXCC、LoTW、eHam、DXWatch、PSK Reporter 链接，支持用户自定义
- **国际化** — 中文（zh-CN）+ 英文（en-US），浏览器语言自动检测
- **多平台部署** — Web、Electron 桌面端（Win/Linux/Mac）、Capacitor Android APK、PWA、Docker

---

## 二、项目技术栈速记

| 层级 | 技术 | 版本/细节 |
|---|---|---|
| **前端框架** | Vue 3 + TypeScript | Composition API (`<script setup>`) |
| **构建工具** | Vite 5 | 路径别名 `@/`，dev proxy，relative base（Electron 兼容） |
| **UI 组件库** | Element Plus | 完整组件套件 |
| **状态管理** | Pinia | `auth`、`logs`、`stats`、`user` 四个 store |
| **路由** | Vue Router 4 | History 模式 + auth 守卫 |
| **国际化** | vue-i18n 9 | zh-CN + en-US |
| **HTTP 客户端** | Axios 1.6 | Bearer Token 拦截器，401 自动登出 |
| **CSS** | SCSS | CSS 变量 + 工具类 |
| **桌面端** | Electron 28 + electron-builder | NSIS 安装包 / portable / AppImage / deb / DMG |
| **移动端** | Capacitor 6 | Android APK (AAB) |
| **PWA** | Web App Manifest | Service worker ready |
| **后端框架** | FastAPI 0.136 | Python 3.10+（Dockerfile 用 3.12-slim） |
| **ORM** | SQLAlchemy 2.0 | 声明式 Base，session-per-request |
| **数据校验** | Pydantic V2 | `from_attributes` 模式 |
| **认证** | JWT (python-jose) + passlib/bcrypt | Access Token 7天 + Refresh Token 30天 |
| **ASGI 服务器** | Uvicorn 0.49 | 开发模式 reload |
| **数据库** | SQLite（本地）/ MySQL 8.0（生产） | 通过 `DATABASE_MODE` 环境变量切换 |
| **缓存** | Redis 7 | Docker Compose 中配置，应用层未深度使用 |
| **外部 API** | QRZ.com XML API | 呼号查询，session 管理 |
| **测试** | pytest + pytest-asyncio + pytest-cov | 后端测试 |
| **容器化** | Docker + Docker Compose | MySQL + Redis + Backend + Frontend |
| **反向代理** | Nginx | SSL 终止、gzip、安全头 |

---

## 三、目录结构

```
radioManger/
├── backend/                    # Python FastAPI 后端
│   ├── app/
│   │   ├── main.py             # FastAPI 应用创建、CORS、中间件、9 个路由注册
│   │   ├── config.py           # Pydantic Settings 配置（数据库、JWT、QRZ 等）
│   │   ├── dependencies.py     # get_current_user JWT 依赖注入
│   │   ├── exceptions.py       # 自定义异常层级
│   │   ├── logger.py           # RotatingFileHandler + 控制台日志
│   │   ├── api/v1/             # 9 个 API 路由模块
│   │   │   ├── auth.py         # 注册、登录、登出、修改密码、/me
│   │   │   ├── users.py        # 用户信息
│   │   │   ├── logs.py         # QSO 日志 CRUD + 导入导出 + 回收站
│   │   │   ├── stations.py     # 电台 CRUD
│   │   │   ├── locations.py    # 位置 CRUD + 激活
│   │   │   ├── callsigns.py    # 呼号查询、批量查询、搜索、缓存清除
│   │   │   ├── stats.py        # 统计概览
│   │   │   ├── sync.py         # GitHub 同步（脚手架）
│   │   │   └── shortcuts.py    # 快捷链接 CRUD
│   │   ├── models/             # 9 个 SQLAlchemy 模型
│   │   │   ├── user.py         # 用户（用户名、邮箱、角色、时区、语言）
│   │   │   ├── station.py      # 电台（呼号，用户内唯一）
│   │   │   ├── location.py     # 位置（网格、设备、天线）
│   │   │   ├── qso_log.py      # QSO 日志（30+ 字段）
│   │   │   ├── callsign_cache.py # 呼号缓存（QRZ 查询结果）
│   │   │   ├── statistics.py   # 统计（预计算，JSON 详情）
│   │   │   ├── log_file.py     # 导入文件追踪
│   │   │   ├── sync_history.py # 同步历史
│   │   │   └── deleted_log.py  # 回收站（JSON 备份，7天过期）
│   │   ├── schemas/            # Pydantic V2 请求/响应模型
│   │   ├── services/           # 业务逻辑层（静态方法）
│   │   │   ├── user_service.py
│   │   │   ├── log_service.py
│   │   │   ├── station_service.py
│   │   │   ├── location_service.py
│   │   │   ├── callsign_service.py
│   │   │   ├── import_export_service.py
│   │   │   ├── deleted_log_service.py
│   │   │   ├── sync_service.py
│   │   │   ├── github_service.py
│   │   │   ├── cache_service.py
│   │   │   └── stats_service.py
│   │   ├── utils/              # 工具函数
│   │   │   ├── security.py     # bcrypt 哈希、JWT 创建/解码
│   │   │   ├── adi_parser.py   # ADIF 文件解析器（大小写不敏感）
│   │   │   ├── dxcc.py         # 340+ DXCC 前缀 → 实体映射
│   │   │   ├── grid_utils.py   # Maidenhead 网格 ↔ 经纬度转换
│   │   │   ├── distance.py     # Haversine 距离 + 方位角计算
│   │   │   ├── formatters.py   # 频率/距离/呼号格式化
│   │   │   └── validators.py   # 输入校验
│   │   ├── middleware/          # 中间件
│   │   │   ├── error_handler.py # 全局异常 → JSON 响应
│   │   │   ├── logging.py      # 请求方法/路径/状态/耗时日志
│   │   │   └── rate_limit.py   # 内存级 IP 限速（100 req/min）
│   │   ├── database/           # 数据库基础设施
│   │   │   ├── base.py         # 引擎创建、SQLite WAL 模式、Session 工厂
│   │   │   ├── session.py      # get_db() 依赖（yield Session）
│   │   │   └── init_db.py      # 建表脚本
│   │   └── scripts/            # 管理脚本
│   │       ├── init_db.py      # 数据库初始化 + 测试账号
│   │       └── create_admin.py # 管理员创建
│   ├── tests/                  # pytest 测试
│   ├── run.py                  # Python 入口
│   ├── requirements.txt        # 62 个 Python 包
│   ├── Dockerfile              # python:3.12-slim
│   └── .env / .env.example     # 环境配置
│
├── frontend/                   # Vue 3 + TypeScript 前端
│   ├── src/
│   │   ├── main.ts             # 应用引导（Pinia、Router、i18n、ElementPlus）
│   │   ├── App.vue             # 布局：顶部栏 + 侧边栏 + router-view
│   │   ├── api/                # Axios API 客户端（按领域分文件）
│   │   │   ├── index.ts        # 主 Axios 实例 + 拦截器
│   │   │   ├── auth.ts, logs.ts, stations.ts, locations.ts
│   │   │   ├── callsigns.ts, shortcuts.ts, deleted_logs.ts, stats.ts
│   │   │   ├── http.ts         # 备用 HTTP API 工厂（已注释）
│   │   │   └── local.ts        # localStorage 离线 API（实验性）
│   │   ├── stores/             # Pinia stores
│   │   │   ├── auth.ts         # Token/用户状态、登录/登出/注册
│   │   │   ├── logs.ts         # 日志列表、电台、筛选、分页、CRUD
│   │   │   ├── stats.ts, user.ts
│   │   ├── router/index.ts     # 13 条路由 + auth 守卫
│   │   ├── views/              # 11 个页面组件
│   │   │   ├── auth/LoginView.vue, RegisterView.vue
│   │   │   ├── DashboardView.vue
│   │   │   ├── logs/LogsView.vue, LogDetailView.vue
│   │   │   ├── stations/StationsView.vue
│   │   │   ├── callsigns/CallsignSearchView.vue
│   │   │   ├── analysis/AnalysisView.vue
│   │   │   ├── shortcuts/ShortcutsView.vue
│   │   │   ├── recycle/RecycleBinView.vue
│   │   │   ├── SettingsView.vue
│   │   │   └── NotFoundView.vue
│   │   ├── locales/            # 国际化
│   │   │   ├── index.ts        # i18n 设置 + 自动检测
│   │   │   ├── zh-CN.ts        # 中文翻译
│   │   │   └── en-US.ts        # 英文翻译
│   │   ├── types/index.ts      # TypeScript 接口定义
│   │   ├── utils/              # 前端工具函数
│   │   │   ├── request.ts      # Axios + 自动 auth 拦截器
│   │   │   ├── storage.ts      # localStorage token/user 助手
│   │   │   └── validators.ts   # 呼号/网格/邮箱/频率校验
│   │   └── styles/main.scss    # CSS 变量 + 工具类
│   ├── electron/               # Electron 主进程
│   │   ├── main.js             # BrowserWindow + 菜单
│   │   ├── preload.js          # Context bridge
│   │   └── package.json        # Electron 构建配置
│   ├── capacitor.config.ts     # Android 构建配置
│   ├── public/                 # PWA 图标 + manifest.json
│   ├── package.json            # v2.1.0
│   ├── vite.config.ts          # 路径别名、dev proxy、relative base
│   ├── tsconfig.json           # strict 模式
│   ├── Dockerfile              # node:22-alpine
│   └── .env                    # VITE_APP_MODE=local
│
├── doc/                        # 设计文档（中文）
│   ├── 01_项目总文件说明.md
│   ├── 02_数据库设计说明.md
│   ├── 03_API设计说明.md
│   ├── 04_前端架构设计.md
│   ├── 05_后端架构设计.md
│   ├── 06_部署说明.md
│   └── 07_系统架构图.md
│
├── docker-compose.yml          # MySQL 8.0 + Redis 7 + Backend + Frontend
├── nginx.conf                  # SSL 反向代理（生产）
├── init-db.sh                  # MySQL 数据库/用户创建
├── start-local.sh              # Linux/macOS 本地开发（SQLite）
├── start-dev.sh                # 开发（可选数据库模式）
├── start-prod.sh               # 生产启动
├── start-windows-local.bat     # Windows 本地（Electron + SQLite）
├── start-windows-web.bat       # Windows Web（Vite + 远程后端）
└── README.md                   # 项目文档（中文）
```

---

## 四、后端架构

### 分层架构

```
API Routes (api/v1/)  →  Services (services/)  →  Models (models/)  →  Database
      ↑                        ↑
  Schemas (schemas/)     Utils (utils/)
```

- **Routes（路由层）**：薄控制器，接收请求、委托 Service、返回响应
- **Services（业务层）**：静态方法类，包含全部业务逻辑（CRUD、DXCC 推断、批处理）
- **Models（模型层）**：SQLAlchemy ORM，关系定义，软删除 (`is_deleted` 布尔字段)
- **Schemas（校验层）**：Pydantic V2 请求校验 + 响应序列化
- **Middleware（中间件栈）**：CORS → ErrorHandler → Logging（顺序叠加）

### 9 个 API 模块

| 模块 | 路由前缀 | 核心端点 |
|---|---|---|
| Auth | `/api/v1/auth` | `POST /register`、`POST /login`、`GET /me`、`PATCH /me`、`POST /change-password`、`POST /logout` |
| Users | `/api/v1/users` | `GET /me` |
| Logs | `/api/v1/logs` | `POST /`、`GET /`（排序/筛选/分页）、`GET /stats/overview`、`GET /export`、`POST /import`、`GET /{id}`、`PATCH /{id}`、`DELETE /{id}`、`GET /recycle/list`、`POST /recycle/{id}/restore` |
| Stations | `/api/v1/stations` | `POST /`、`GET /`、`GET /{id}`、`PATCH /{id}`、`DELETE /{id}` |
| Locations | `/api/v1/locations` | `POST /`、`GET /`（可筛选）、`GET /active/current`、`POST /{id}/activate`、`PATCH /{id}`、`DELETE /{id}` |
| Callsigns | `/api/v1/callsigns` | `GET /{call_sign}`、`GET /search/{prefix}`、`POST /batch-query`、`DELETE /cache/{call_sign}` |
| Stats | `/api/v1/stats` | `GET /overview`（可选 station_id 筛选） |
| Sync | `/api/v1/sync` | `POST /github/config`、`POST /github/push`、`POST /github/pull`（脚手架）、`GET /history` |
| Shortcuts | `/api/v1/shortcuts` | `GET /`、`POST /`、`DELETE /{id}` |
| Root | `/` | `GET /health`、`GET /`（根信息） |

### 认证机制

- JWT Bearer Token：`Authorization: Bearer <token>`
- 无需认证的端点：`/auth/register`、`/auth/login`、`/health`、`/`、`/docs`
- Access Token 有效期：7 天
- Refresh Token 有效期：30 天
- 前端 401 响应自动触发登出

---

## 五、前端架构

### 组成结构

- **布局**：Element Plus `el-container`，蓝色顶部栏（Logo + 语言切换 + 用户下拉）+ 侧边栏菜单
- **11 个视图页面**：Login、Register、Dashboard、Logs 列表、Log 详情、Stations 管理、Callsign 搜索、Analysis、Shortcuts、Recycle Bin、Settings、404
- **路由守卫**：未认证用户重定向到 `/login`；已认证用户访问 login/register 重定向到 Dashboard
- **Vite Proxy**：开发模式 `/api` 代理到 `http://localhost:8000`
- **Relative Base（`./`）**：兼容 Electron `file://` 协议

### Pinia Stores

| Store | 职责 |
|---|---|
| `auth` | Token/用户状态、登录/登出/注册 |
| `logs` | 日志列表、电台、筛选条件、分页、CRUD 操作 |
| `stats` | 统计数据 |
| `user` | 用户偏好设置 |

### 前端 API 客户端

每个业务领域一个 Axios 封装文件：`auth.ts`、`logs.ts`、`stations.ts`、`locations.ts`、`callsigns.ts`、`shortcuts.ts`、`deleted_logs.ts`、`stats.ts`。统一通过 `api/index.ts` 创建 Axios 实例并配置拦截器。

---

## 六、数据库设计（9 张表）

| 表名 | 用途 | 关键字段 |
|---|---|---|
| `users` | 用户账户 | username, email, password_hash, role(user/admin), timezone, language |
| `stations` | 电台标识（呼号） | user_id(FK), callsign(用户内唯一), is_deleted |
| `locations` | 电台操作位置 | user_id, station_id(FK), name, grid_square, radio_model, antenna_model, antenna_height, qth, is_active |
| `qso_logs` | QSO 联络记录 | user_id, station_id, location_id, call_sign, qso_date, freq, band, mode, RST, QSL/eQSL/LoTW 状态, DXCC, distance, comment（30+ 字段） |
| `callsign_cache` | QRZ 查询缓存 | call_sign(唯一), full_name, country, grid_square, lat/lon, license 日期, cached_at |
| `statistics` | 预计算统计 | user_id(唯一), total_qso, total_dxcc, QSL 计数, JSON detail |
| `log_files` | 导入文件追踪 | user_id, file_name, file_hash, format, qso_count, import_status |
| `sync_history` | 同步审计记录 | user_id, sync_type(push/pull/merge), source, status, 增/改/删计数 |
| `deleted_logs` | 回收站 | user_id, log_id, log_data(JSON), delete_reason, deleted_at, expires_at(7天), is_restored |

### 关系

- User 1:N → Stations, Locations, QSOLogs
- Station 1:N → Locations, QSOLogs
- Location N:1 → Station
- QSOLog N:1 → Station, Location（可空）
- 外键删除策略：`CASCADE`（stations 用 `RESTRICT` 防止 QSO 日志意外丢失）

### 双数据库模式

通过 `DATABASE_MODE` 环境变量切换：
- `sqlite`：本地 SQLite，启用 WAL 模式提升并发性能
- `mysql`：生产 MySQL 8.0，连接池管理

---

## 七、核心业务逻辑

### ADIF 导入导出
- **导入**：`import_export_service.py` 解析 ADI/ADIF 文件（大小写不敏感），500 条/批次提交，预加载去重集合提升性能
- **导出**：导出为标准 ADI 格式，包含 `station_callsign` 和 `my_gridsquare`

### 三级呼号查询（`callsign_service.py`）
1. **本地缓存**（30 天 TTL）→ 优先返回
2. **QRZ.com XML API** → 在线查询并写入缓存
3. **离线 DXCC 前缀推断**（`dxcc.py`）→ 340+ 实体前缀表匹配

### DXCC 自动推断
- 每条 QSO 创建时自动从呼号前缀推断 DXCC 实体
- 使用内置 340+ 条前缀映射表

### QSL 级联
- 设置 `qsl_rcvd=Y` 时自动将其他确认字段（eQSL、LoTW）设为 Y

### 软删除与回收站
- 主要表使用 `is_deleted` 布尔字段软删除
- 删除日志以 JSON 备份到 `deleted_logs` 表，7 天保留，支持恢复

### 单激活位置
- 激活一个位置时自动取消同一用户其他位置的激活状态

### 电台恢复
- 重新创建已软删除的电台会恢复原记录而非报错

---

## 八、部署模式速查

| 模式 | 启动方式 | 前端 | 后端 | 数据库 |
|---|---|---|---|---|
| 本地 Linux/macOS | `./start-local.sh` | Vite dev | Uvicorn | SQLite |
| 本地 Windows | `start-windows-local.bat` | Electron | Uvicorn | SQLite |
| Windows Web | `start-windows-web.bat` | Vite | 远程 | 远程 |
| 开发（可选 DB） | `./start-dev.sh` | Vite | Uvicorn | SQLite/MySQL |
| Docker/LAN | `docker-compose up` | Node dev | Uvicorn | MySQL 8.0 |
| 生产云部署 | Docker + Nginx | 构建静态文件 | Uvicorn | MySQL 8.0 |

### Docker Compose 服务
- **mysql**：MySQL 8.0，端口 3306，持久化卷
- **redis**：Redis 7 Alpine，端口 6379，持久化卷
- **backend**：python:3.12-slim，pip install + uvicorn --reload
- **frontend**：node:22-alpine，npm ci + dev server

### Electron 构建
- Windows：NSIS 安装包 + portable exe（x64）
- Linux：AppImage + deb
- macOS：DMG

---

## 九、关键约定

1. **中文优先**：所有文档、注释、变量名均为中文
2. **ADIF 标准**：严格遵循 Amateur Data Interchange Format 标准
3. **Maidenhead 网格**：使用标准的 Maidenhead Locator System（6 位网格定位）
4. **Haversine 公式**：距离和方位角计算使用球面几何
5. **软删除模式**：核心数据表使用 `is_deleted` 字段，避免物理删除
6. **环境变量驱动**：所有敏感配置（JWT 密钥、QRZ 凭证、数据库连接串）通过 `.env` 管理
7. **开发测试账号**：默认启用 `admin/admin123`（`ENABLE_TEST_ACCOUNT=True`）
8. **未完成功能**：GitHub 同步（脚手架返回 `not_implemented`）、Redis（已配置未使用）、SMTP（设置存在无发送代码）、Rate Limit（定义未注册到 main.py）

---

## 十、全局原则

1. **只读归档**：本 skill 仅用于提供项目知识上下文，不修改任何项目源代码
2. **中文语境**：回答与本项目相关的问题时，保持中文表述习惯，技术术语可中英混用
3. **遵循 ADIF 标准**：任何涉及 QSO 日志字段的修改，必须符合 ADIF 规范
4. **双库兼容**：数据库相关修改必须同时兼容 SQLite 和 MySQL 两种模式
5. **安全意识**：JWT 密钥、QRZ 凭证、数据库密码等敏感信息仅通过 `.env` 配置，不得硬编码
6. **向后兼容**：API 变更需考虑前端兼容性，数据库迁移使用 Alembic 管理
