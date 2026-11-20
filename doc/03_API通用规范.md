# API 通用规范

本文约定所有端点共用的规则：响应格式、状态码、认证、分页、错误处理和文档访问。各模块的端点明细见[API 端点说明](04_API端点说明.md)。

## API 概述

REST API 默认前缀为 `/api/v1`，由 [`main.py`](../backend/app/main.py) 注册。端点说明中的路径与 [`api/v1/`](../backend/app/api/v1/) 和 [`schemas/`](../backend/app/schemas/) 一致。`/health`、`/` 和 OpenAPI 位于版本前缀之外。

## 响应格式

成功响应按端点定义返回，没有统一的 `{code, message, data}` 包装：

| 端点类型 | 响应 |
| --- | --- |
| 登录 | 顶层 `access_token`、`refresh_token`、`token_type`、`expires_in`、`user` |
| 台站、位置、单条日志 | 对象 |
| 台站、位置、DX 节点列表 | 数组 |
| 日志列表、回收站、同步历史 | `{items, total, page, page_size, pages}` |
| 统计 API | `{data: ...}` |
| 日志导入 | 顶层计数、文件 ID 和错误数组 |
| 日志导出 | 文件响应，`application/octet-stream` |
| DELETE 成功 | 通常为 204，无响应体 |

Axios 公共客户端只解包 HTTP 的 `response.data`，不会继续提取业务层的 `data`。

## HTTP 状态码

| 状态码 | 含义 |
| --- | --- |
| 200 / 201 / 204 | 成功 / 创建成功 / 无内容 |
| 400 | 业务条件不满足、文件类型错误等 |
| 401 / 403 | 认证失败 / 权限不足 |
| 404 | 资源不存在 |
| 409 | DX Cluster 缺少可用激活台站等冲突 |
| 413 | 导入文件超过大小限制 |
| 422 | 参数校验失败或注册信息冲突 |
| 429 | 触发 IP 限流 |
| 500 / 502 | 服务端异常 / DX 节点连接失败 |

## 认证方式

除注册、登录及公共状态接口外，REST 业务端点要求：

```http
Authorization: Bearer <access_token>
```

WebSocket 使用 `?token=<access_token>`。令牌有效期默认分别为 7 天和 30 天，但没有 `/auth/refresh` 接口，也没有前端自动续期流程。MySQL 管理接口另要求 `role="admin"`。

## 分页参数

普通分页默认 `page=1`、`page_size=20`，页码从 1 开始，页大小上限 100。管理审计列表默认 50、上限 200；管理员用户列表与审计列表不返回 `pages`。

日期使用 `YYYY-MM-DD`，时间使用 `HH:MM:SS`。QSO 日期和时间按 UTC 使用，频率单位为 MHz，功率单位为瓦，天线高度单位为米。

## 错误处理

### 错误响应格式

FastAPI 处理的 HTTP 异常通常返回 `{"detail":"..."}`，请求校验错误的 `detail` 为数组。自定义业务异常、未处理异常和限流使用：

```json
{"code":429,"message":"Too many requests. Please try again later.","data":null}
```

客户端应同时识别 `detail`、`message` 及端点专用的错误字段，不能假定所有错误格式一致。

### 限流

按客户端 IP 使用 60 秒窗口。普通请求上限 100；登录、注册、改密、确认注销共用更严格的 5 次窗口。状态存于单进程内存。`/health`、`/` 及 `/docs` 前缀跳过限流。

## API 文档访问

`DEBUG=true` 时开放 `/docs` 和 `/redoc`。`/openapi.json` 未随 `DEBUG=false` 关闭。服务器默认关闭交互文档；部署状态使用 `/health` 查询。

`GET /health` 报告 `status`、`version`、`database`、`subsystems`，SQLite 额外返回 `db_path`、`db_dir`。数据库或 Redis 检查失败时 `status="degraded"`，HTTP 状态仍为 200。`GET /` 返回应用名、版本、文档路径和数据库模式。
