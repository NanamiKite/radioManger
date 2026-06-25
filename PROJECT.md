# RadioManager — 项目架构与实现文档

> 本文档供 AI 助手快速理解项目全貌。阅读后应能回答架构、数据流、模块职责等问题。

---

## 1. 项目概述

RadioManager 是一个业余无线电 QSO 日志管理系统，支持桌面端（Electron）和 Web 端。核心功能包括：QSO 日志 CRUD、ADIF 3.1.0 格式导入导出、DXCC 实体推断、DX Cluster 实时 spot 监控、梅登网格地图热力图、回收站软删除、统计分析。

**定位：** 离线优先的个人日志工具，同时支持服务器部署多用户协作。

---

## 2. 技术栈

| 层级 | 技术 |
|------|------|
| 桌面端 | Electron（contextIsolation + sandbox） |
| 前端 | Vue 3 + TypeScript + Pinia + Element Plus + vue-i18n + Leaflet |
| 后端 | FastAPI + SQLAlchemy 2.0 + Pydantic v2 |
| 数据库 | SQLite（离线）/ MySQL（服务器），通过 `DATABASE_MODE` 环境变量切换 |
| 缓存/黑名单 | Redis（仅 MySQL 模式），SQLite 模式用内存 set |
| 数据库迁移 | Alembic（`render_as_batch=True` 兼容 SQLite） |
| 容器化 | Docker（非 root 用户，health check） |
| 认证 | JWT（access + refresh token），bcrypt 密码哈希 |

---

## 3. 目录结构

```
radioManger/
├── backend/
│   ├── app/
│   │   ├── api/v1/           # 12 个路由模块
│   │   ├── database/         # session.py, base.py, init_db.py
│   │   ├── middleware/        # rate_limit, logging, error_handler
│   │   ├── models/           # SQLAlchemy ORM 模型
│   │   ├── schemas/          # Pydantic 请求/响应模型
│   │   ├── services/         # 16 个业务服务模块
│   │   ├── utils/            # adi_parser, dxcc, grid_utils, security
│   │   ├── config.py         # Settings（pydantic-settings）
│   │   ├── dependencies.py   # get_current_user 依赖注入
│   │   ├── dependencies_admin.py  # get_current_admin（仅 MySQL）
│   │   ├── exceptions.py     # 自定义异常体系
│   │   └── main.py           # FastAPI 应用入口
│   ├── alembic/              # 数据库迁移
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/              # Axios 封装 + 各模块 API
│   │   ├── stores/           # Pinia store（auth, logs）
│   │   ├── views/            # 页面组件
│   │   ├── utils/            # theme, constants, storage
│   │   ├── locales/          # i18n（zh-CN, en-US）
│   │   └── types/            # TypeScript 类型定义
│   ├── electron/
│   │   ├── main.js           # Electron 主进程
│   │   └── preload.js        # 预加载脚本
│   └── package.json
└── PROJECT.md                # 本文件
```

---

## 4. 双数据库架构

这是项目最核心的架构决策。

```
DATABASE_MODE=sqlite  →  SQLITE_URL（本地文件）
DATABASE_MODE=mysql   →  DATABASE_URL（MySQL 连接串）+ REDIS_URL
```

**实现方式：**
- `config.py`：`ACTIVE_DATABASE_URL` 属性根据 `DATABASE_MODE` 返回对应 URL
- `database/base.py`：`engine` 和 `SessionLocal` 使用 `ACTIVE_DATABASE_URL`
- `main.py:79`：admin 路由仅在 MySQL 模式下注册
- `dependencies.py:43`：token 黑名单检查仅在 MySQL 模式下执行
- `dependencies_admin.py:13`：SQLite 模式跳过权限检查（路由本身不注册，此为防御性代码）
- `token_blacklist_service.py`：SQLite 模式用 `MemoryBlacklist`（内存 set），MySQL 模式用 `RedisBlacklist`
- `session_service.py:17`：会话追踪仅 MySQL 模式启用
- `alembic/env.py`：`render_as_batch=True` 解决 SQLite 不支持 `ALTER TABLE` 的问题

---

## 5. 认证与鉴权

```
登录 → UserService.authenticate_user → SecurityUtils.create_token → (access_token, refresh_token)
请求 → get_current_user → decode_token → 检查黑名单 → 查询用户 → 返回 User 对象
登出 → token 加入黑名单 + 移除会话记录
改密码 → SessionService.remove_all_sessions → 所有旧 token 失效
```

**关键实现：**
- `security.py`：自定义 `TokenExpiredError` / `InvalidTokenError` 异常类
- `dependencies.py`：`get_current_user` 是 FastAPI 依赖注入，所有需认证端点共用
- `dependencies_admin.py`：`get_current_admin` 在 `get_current_user` 基础上检查 `role == "admin"`
- `rate_limit.py`：内存速率限制，登录/注册 5 次/分钟，全局 100 次/分钟

---

## 6. 数据模型关系

```
User (1) ──→ (N) Station (1) ──→ (N) Location
  │                                      │
  │                                      ↓
  └──────── (N) QSOLog ←──────────────┘ (location_id, SET NULL on delete)
                 │
                 ↓ (soft delete + backup)
            DeletedLog（回收站，7 天过期）
```

**核心模型：**
- `User`：用户，`role` 字段（String，非 Enum），`is_deleted` 软删除
- `Station`：台站（仅呼号容器），一个用户可有多个
- `Location`：位置（网格、电台、天线），归属台站，全局只能激活一个
- `QSOLog`：QSO 日志，归属用户 + 台站 + 位置，包含 ADIF 3.1.0 全部字段
- `DeletedLog`：回收站条目，存储 JSON 格式的日志快照

**外键策略：**
- `QSOLog.station_id` → `Station.id`，`ondelete="RESTRICT"`（防止误删有日志的台站）
- `QSOLog.location_id` → `Location.id`，`ondelete="SET NULL"`（位置删了日志保留）

---

## 7. 服务层职责

| 服务 | 职责 |
|------|------|
| `LogService` | 日志 CRUD、统计聚合（4 条 SQL）、自动推断 DXCC/location/UTC 时间 |
| `ImportExportService` | ADIF 导入（6 字段去重 + 只填空合并 + QSL 单向流转 + 批量提交）、导出（yield_per） |
| `UserService` | 注册、认证（失败返回 None 防枚举）、改密码 |
| `StationService` | 台站 CRUD，删除时级联软删除关联日志和位置 |
| `LocationService` | 位置 CRUD，激活/取消激活（全局互斥） |
| `DeletedLogService` | 回收站：备份、恢复（恢复原记录）、清理过期、批量删除 |
| `StatsService` | 波段/模式/DXCC 统计、DXCC 图表、波段×模式矩阵 |
| `SessionService` | 会话追踪（仅 MySQL），在线用户统计 |
| `TokenBlacklistService` | token 黑名单（MemoryBlacklist / RedisBlacklist） |
| `AdminService` | 用户管理（列表、启禁用、重置密码、软删除） |
| `AuditService` | 审计日志写入（带 try/except 容错） |
| `ConfigService` | 系统配置 CRUD（预置默认值） |
| `CallsignService` | 呼号查询（缓存 + DXCC 推断） |
| `DXClusterManager` | DX Cluster telnet 连接管理（asyncio，单例，环形缓冲，WebSocket 广播） |
| `EmailService` | 邮箱验证码（预留接口，当前内存存储） |
| `SyncService` | GitHub 同步（预留接口） |

---

## 8. API 路由总览

```
/api/v1/auth         POST /register, /login, /logout, /change-password, /delete-account, /cancel-delete, /confirm-delete
                     GET  /me
                     PATCH /me

/api/v1/logs         POST /, /import, /recycle/{id}/restore, /recycle/batch-delete, /recycle/clear-all
                     GET  /, /{id}, /stats/overview, /export, /recycle/list
                     PATCH /{id}
                     DELETE /{id}

/api/v1/stations     POST /
                     GET  /, /{id}
                     PATCH /{id}
                     DELETE /{id}

/api/v1/locations    POST /, /{id}/activate
                     GET  /, /active/current
                     PATCH /{id}
                     DELETE /{id}

/api/v1/stats        GET /overview, /band-mode, /dxcc, /dxcc-chart, /band-mode-matrix

/api/v1/callsigns    POST /batch-query
                     GET  /search/{prefix}, /{call_sign}
                     DELETE /cache/{call_sign}

/api/v1/dxcluster    POST /connect, /disconnect
                     GET  /nodes, /status, /spots
                     WS   /ws

/api/v1/udp          POST /start, /stop, /save-to-log
                     GET  /status
                     WS   /ws

/api/v1/map          GET /grids

/api/v1/shortcuts    POST /
                     GET  /
                     DELETE /{id}

/api/v1/sync         POST /github/config, /github/push, /github/pull
                     GET  /history

/api/v1/admin        GET  /users, /users/{id}, /users/{id}/stats, /audit-logs, /system/config, /system/status
                     POST /users/{id}/toggle, /users/{id}/reset-password
                     PATCH /system/config
                     DELETE /users/{id}

/api/v1/users        GET /me

/health              GET  （健康检查：数据库 + Redis 连接状态）
```

---

## 9. 关键数据流

### 9.1 日志创建

```
前端 logsApi.create(data)
  → POST /api/v1/logs
    → LogService.create_log(db, user_id, QSOLogCreate)
      → 未指定 station_id？查询激活 Location → 填入 station_id + location_id + my_gridsquare
      → 未指定 time_on？填入 UTC 当前时间
      → 未指定 qso_date？填入 UTC 当前日期
      → 有 call_sign？自动推断 DXCC（lookup_dxcc）
      → QSL 联动：qsl_rcvd=="Y" → qsl_sent/lotw_sent/lotw_rcvd/eqsl_sent/eqsl_rcvd 全部置 "Y"
      → db.add + commit + refresh
    → _enrich_log(log, station_cache, location_cache)  # 填充台站呼号和位置名称
    → 返回 QSOLogResponse
```

### 9.2 ADIF 导入

```
前端 logsApi.importLogs(file, station_id)
  → POST /api/v1/logs/import（multipart/form-data）
    → 流式读取（1MB/块，50MB 上限）
    → ImportExportService.import_adi(db, user_id, content, filename, station_id)
      → ADIParser.parse_adi_file(content)  # length-based 字段提取
      → ADIParser.map_adi_fields(records)  # ADIF 字段名 → 应用字段名
      → 预加载现有日志 6 字段到 existing_map（dict，key=(call_sign,date,time,band,mode,freq) → id）
      → 遍历导入记录：
        - 去重键命中？→ 加载完整 ORM 对象 → 只填空合并 + QSL 单向更新
        - 去重键未命中？→ 创建新记录 → 加入 existing_map（本批次内也去重）
        - 每 500 条 commit 一次
      → 记录导入元数据到 LogFile 表
      → 返回 {imported, skipped, duplicates, merged, errors}
```

### 9.3 统计查询

```
LogService.get_stats(db, user_id, station_id?)
  → 1 条聚合 SQL：func.sum(case(...)) 取 total_qso, qsl_sent, qsl_rcvd, eqsl_*, lotw_*, monthly, yearly, confirmed
  → 2 条 COUNT DISTINCT：total_dxcc, confirmed_dxcc
  → 1 条 station count
  → 共 4 条 SQL，返回 13 个指标
```

### 9.4 DX Cluster 实时推送

```
前端 WebSocket 连接 /api/v1/dxcluster/ws?token=xxx
  → _authenticate_ws(ws)  # 解析 JWT → 检查黑名单 → 查询用户 → 预加载字段 → 关闭 session
  → ws.accept()
  → 推送历史 spot（deque 中的 100 条）
  → dxcluster_manager.subscribe() → 返回 asyncio.Queue
  → 循环：queue.get() → ws.send_json({type: "spot", data: spot_dict})
  → 断连时：unsubscribe(queue) + ws.close()

后端 DXClusterManager 生命周期：
  connect(node, callsign) → asyncio.open_connection → _do_login → _listen_task
  _listen_loop → readline → _strip_telnet_commands → parse_spot → _spots.append → _broadcast
  disconnect → cancel listen_task → close writer
```

---

## 10. 前端架构

### 状态管理（Pinia）
- `auth` store：用户信息、token、登录/登出/注册、数据库模式检测
- `logs` store：日志列表、分页、过滤、排序、台站管理、请求 ID 守卫（防旧响应覆盖新数据）

### API 层
- `api/index.ts`：Axios 实例，请求拦截器自动附加 token，响应拦截器 401 自动登出
- `api/logs.ts`：`exportLogs` 使用原生 `fetch`（Axios 的 `response.data` 自动解包会破坏 blob）
- `api/health.ts`：独立 Axios 实例（绕过 `/api/v1` 拦截器）

### i18n
- `locales/index.ts`：`getLanguage()` 不依赖 i18n 实例（防止初始化顺序导致白屏）
- `setLanguage()` 通过 `(i18n.global.locale as any).value` 赋值

### 主题
- `utils/theme.ts`：`light` / `dark` / `system` 三模式，`matchMedia` 监听系统变化
- `getThemeLabel()` 返回 i18n key（如 `settings.lightMode`），由调用方 `$t()` 翻译

---

## 11. Electron 安全配置

```javascript
// frontend/electron/main.js
webPreferences: {
  preload: path.join(__dirname, 'preload.js'),
  contextIsolation: true,   // 渲染进程无法直接访问 Node API
  nodeIntegration: false,    // 禁止 require/import
  sandbox: true,             // 沙箱隔离
}
```

- 单实例锁：`app.requestSingleInstanceLock()` 防止重复启动导致 SQLite 锁冲突
- 部署模式：`auto`（从环境变量读取）/ `local` / `lan` / `cloud`

---

## 12. 设计决策备忘

| 决策 | 原因 |
|------|------|
| `role` 用 String 而非 Enum | 双数据库兼容，SQLite 的 Enum 支持有限 |
| token 黑名单 SQLite 模式用内存 | SQLite 是离线单用户，黑名单无意义 |
| `dependencies_admin.py` SQLite 跳过权限 | SQLite 模式下 admin 路由不注册，此为防御性代码 |
| `sync_service.py` 推送逻辑为空壳 | 预留接口，框架已搭好 |
| `email_service.py` 内存存储 | 预留接口，等 SMTP 服务接入 |
| `shortcuts.py` 内存存储 | 轻量功能，重启丢失可接受 |
| `QSOLog.station_id` 用 `RESTRICT` | 防止误删有日志的台站 |
| `QSOLog.location_id` 用 `SET NULL` | 位置删了日志保留 |
| ADIF 解析用 length-based | 正则匹配在值含 `<` 时会误匹配 |
| 统计用 `func.sum(case(...))` | 13 条查询压到 4 条，减少数据库往返 |
| `exportLogs` 用原生 fetch | Axios 的 `response.data` 自动解包破坏 blob |
| WebSocket token 放 query string | 浏览器原生 WebSocket 不支持自定义 header |

---

## 13. 常量与工具

- `utils/dxcc.py`：530+ 条正则前缀映射，`lookup_dxcc(callsign)` 返回 DXCC 实体名称
- `utils/grid_utils.py`：梅登网格验证、经纬度转换、距离计算（Haversine）
- `utils/adi_parser.py`：ADIF 3.1.0 解析器，length-based 字段提取
- `utils/security.py`：bcrypt 密码哈希、JWT 创建/解码
- `frontend/src/utils/constants.ts`：波段频率映射、天线计算表、SWR 参考表
- `frontend/src/data/dxcc-entities.json`：340 个 DXCC 实体名称列表

---

## 14. 中间件执行顺序

```
请求 → RateLimitMiddleware → LoggingMiddleware → ErrorHandlerMiddleware → CORSMiddleware → 路由处理
```

后添加的中间件先执行（FastAPI/Starlette 的洋葱模型）。

---

## 15. 已知限制

- DX Cluster 管理器是进程内单例，多 worker 下每个 worker 独立连接（当前部署单 worker）
- WebSocket token 在 URL query 中，会记录在 access log（已有安全提示注释）
- `shortcuts.py` 和 `email_service.py` 使用内存存储，进程重启丢失
- `sync_service.py` 的 GitHub 推送逻辑为预留空壳
