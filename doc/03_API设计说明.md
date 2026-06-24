# API设计说明文档

## API概述

RadioManager后端采用RESTful API设计模式，基于FastAPI框架实现。所有API均使用JSON格式传输，支持JWT令牌认证。

## API基本规范

### 统一响应格式
```json
{
    "code": 200,
    "message": "Success",
    "data": {}
}
```

### HTTP状态码
- `200`: 成功
- `201`: 创建成功
- `204`: 无内容
- `400`: 请求参数错误
- `401`: 未认证/令牌过期
- `404`: 资源不存在
- `422`: 数据验证失败
- `429`: 请求过于频繁
- `500`: 服务器内部错误

### 认证方式
- **令牌类型**: Bearer Token (JWT, HS256)
- **过期时间**: AccessToken 7天 / RefreshToken 30天
- **请求头**: `Authorization: Bearer <token>`
- **令牌标识**: 每个令牌包含唯一 JTI（JWT ID），用于 Token 黑名单机制（MySQL 模式）

### 分页参数
```json
{
    "page": 1,
    "page_size": 20,
    "sort_by": "qso_date",
    "sort_order": "desc"
}
```

## API端点设计

### 一、用户认证模块 (`/api/v1/auth`)

#### 1.1 用户注册
```
POST /api/v1/auth/register
Content-Type: application/json

{
    "username": "ba6zyx",
    "email": "user@example.com",
    "password": "password123",
    "confirm_password": "password123"
}

响应 201:
{
    "id": 1,
    "username": "ba6zyx",
    "email": "user@example.com",
    "role": "user",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00"
}
```

#### 1.2 用户登录
```
POST /api/v1/auth/login
Content-Type: application/json

{
    "username": "ba6zyx",
    "password": "password123"
}

响应 200:
{
    "access_token": "eyJ0eXAiOiJKV1Qi...",
    "refresh_token": "eyJ0eXAiOiJKV1Qi...",
    "token_type": "Bearer",
    "expires_in": 604800,
    "user": { "id": 1, "username": "ba6zyx", ... }
}
```

#### 1.3 获取当前用户 / 更新信息
```
GET /api/v1/auth/me
PATCH /api/v1/auth/me
Authorization: Bearer {token}

PATCH body: { "timezone": "Asia/Shanghai", "language": "zh-CN" }
```

#### 1.4 修改密码
```
POST /api/v1/auth/change-password
Authorization: Bearer {token}

{
    "old_password": "oldpass123",
    "new_password": "newpass456",
    "confirm_password": "newpass456"
}
```

---

### 二、用户信息模块 (`/api/v1/users`)
```
GET /api/v1/users/me
Authorization: Bearer {token}
```

---

### 三、台站模块 (`/api/v1/stations`)

台站仅包含呼号标识，详细配置在位置模块中。

#### 3.1 创建台站
```
POST /api/v1/stations
Authorization: Bearer {token}
Body: { "callsign": "BA7ABC" }

响应 201:
{ "id": 1, "user_id": 1, "callsign": "BA7ABC", ... }
```

#### 3.2 获取所有台站
```
GET /api/v1/stations
Authorization: Bearer {token}
```

#### 3.3 更新/删除台站
```
PATCH /api/v1/stations/{id}   Body: { "callsign": "BH8XYZ" }
DELETE /api/v1/stations/{id}
```

---

### 四、位置模块 (`/api/v1/locations`)

**核心设计**：一个台站可以有多个位置，同一用户全局只能激活一个位置。

#### 4.1 创建位置
```
POST /api/v1/locations
Authorization: Bearer {token}
Body: {
    "station_id": 1,
    "name": "Home",
    "grid_square": "OL63",
    "radio_model": "ICOM IC-7300",
    "antenna_model": "Yagi"
}

响应 201:
{
    "id": 1,
    "user_id": 1,
    "station_id": 1,
    "station_callsign": "BA7ABC",
    "name": "Home",
    "grid_square": "OL63",
    "is_active": true,      // 首个位置自动激活
    ...
}
```

#### 4.2 获取位置列表
```
GET /api/v1/locations
GET /api/v1/locations?station_id=1
Authorization: Bearer {token}
```

#### 4.3 获取当前激活位置
```
GET /api/v1/locations/active/current
Authorization: Bearer {token}
```

#### 4.4 激活位置
```
POST /api/v1/locations/{id}/activate
Authorization: Bearer {token}
// 同一用户其他位置自动取消激活
```

#### 4.5 更新/删除位置
```
PATCH /api/v1/locations/{id}  Body: { "name": "Mobile", "radio_model": "FT-991A" }
DELETE /api/v1/locations/{id}
```

---

### 五、日志管理模块 (`/api/v1/logs`)

#### 5.1 创建通联日志
```
POST /api/v1/logs
Authorization: Bearer {token}
Body: {
    "station_id": 1,         // 可选，未指定时自动使用激活台站
    "call_sign": "JA1ABC",
    "qso_date": "2024-06-15",
    "band": "20m",
    "mode": "FT8",
    "rst_sent": "-05",
    "rst_rcvd": "-03"
}

响应 201:
{
    "id": 1,
    "station_id": 1,
    "station_callsign": "BA7ABC",
    "call_sign": "JA1ABC",
    ...
}
```

#### 5.2 分页查询日志
```
GET /api/v1/logs?page=1&page_size=20&station_id=1&start_date=...&end_date=...&band=20m&mode=FT8&call_sign=JA1
Authorization: Bearer {token}

响应:
{
    "items": [ ... ],
    "total": 1500,
    "page": 1,
    "page_size": 20,
    "pages": 75
}
```

**说明**：默认展示所有台站的日志。前端可以传 `station_id` 参数过滤指定台站的日志。

#### 5.3 单条日志操作
```
GET    /api/v1/logs/{id}      # 详情（含 station_callsign）
PATCH  /api/v1/logs/{id}      # 更新
DELETE /api/v1/logs/{id}      # 逻辑删除
```

#### 5.4 导入日志
```
POST /api/v1/logs/import
Authorization: Bearer {token}
Content-Type: multipart/form-data

参数:
- file: .adi/.adif 文件
- station_id: 目标台站（可选，默认激活台站）

响应:
{
    "file_id": 1,
    "total_records": 150,
    "imported": 145,
    "skipped": 5,
    "errors": [ { "line": 10, "error": "..." } ]
}
```

#### 5.5 导出日志
```
GET /api/v1/logs/export?format=adi&station_id=1&start_date=...&end_date=...&band=20m
Authorization: Bearer {token}

响应: application/octet-stream
Content-Disposition: attachment; filename="20260614_BA7ABC.adi"
```

**说明**：导出文件名格式为 `{日期}_{台站呼号}.adi`。`station_id` 可选，未指定时导出所有台站日志（文件名使用 `AllStations`）。

#### 5.6 统计概览
```
GET /api/v1/logs/stats/overview
Authorization: Bearer {token}

{
    "data": {
        "total_qso": 1500,
        "total_dxcc": 120,
        "qsl_sent": 1200,
        "qsl_rcvd": 800,
        "lotw_confirmed": 600,
        "total_distance": 1500000
    }
}
```

#### 5.7 回收站列表
```
GET /api/v1/logs/recycle/list?page=1&page_size=20
Authorization: Bearer {token}

响应:
{
    "items": [
        {
            "id": 1,
            "log_id": 123,
            "call_sign": "JA1ABC",
            "qso_date": "2026-06-15",
            "band": "20m",
            "delete_reason": "Station #5 deleted",
            "deleted_at": "2026-06-20T10:00:00",
            "expires_at": "2026-06-27T10:00:00",
            "days_remaining": 7
        }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20,
    "pages": 1
}
```

#### 5.8 从回收站恢复日志
```
POST /api/v1/logs/recycle/{deleted_id}/restore
Authorization: Bearer {token}

响应 200:
{
    "id": 124,             // 新建的日志ID
    "call_sign": "JA1ABC",
    ...
}
```

**说明**：恢复时从备份 JSON 创建新的 QSO 记录，原回收站条目标记为已恢复。过期条目（超过 7 天）不可恢复，恢复时自动清理过期条目。

---

### 六、统计分析模块 (`/api/v1/stats`)

```
GET /api/v1/stats/overview
Authorization: Bearer {token}
```

---

### 七、呼号查询模块 (`/api/v1/callsigns`)

#### 7.1 查询单个呼号
```
GET /api/v1/callsigns/{call_sign}
Authorization: Bearer {token}

响应:
{
    "call_sign": "JA1ABC",
    "full_name": "Taro Yamada",
    "country": "Japan",
    "grid_square": "PM95",
    "latitude": 35.6762,
    "longitude": 139.6503,
    "cached": true,        // 来自缓存标记
    "offline": false,       // 是否来自离线DXCC推断
    "qrz_url": "https://www.qrz.com/db/JA1ABC"
}
```

**查询优先级**：本地缓存（30天内）→ QRZ.com API → 过期缓存 → 离线DXCC前缀推断

#### 7.2 批量查询 / 搜索
```
POST /api/v1/callsigns/batch-query
Body: { "call_signs": ["JA1ABC", "JA2DEF"] }

GET /api/v1/callsigns/search/{prefix}?country=Japan
```

#### 7.3 清除缓存
```
DELETE /api/v1/callsigns/cache/{call_sign}
```

---

### 八、数据同步模块 (`/api/v1/sync`)

| 端点 | 说明 |
|------|------|
| `POST /sync/github/config` | 配置GitHub (预留) |
| `POST /sync/github/push` | 手动推送 (预留) |
| `POST /sync/github/pull` | 手动拉取 (预留) |
| `GET /sync/history` | 同步历史 |

---

### 九、快捷链接模块 (`/api/v1/shortcuts`)
```
GET  /api/v1/shortcuts                  # 内置+自定义快捷链接
POST /api/v1/shortcuts                  # 添加链接
DELETE /api/v1/shortcuts/{id}           # 删除链接
```

---

### 十、DX Cluster 模块 (`/api/v1/dxcluster`)

连接公共 DX Cluster 节点，实时接收并推送 DX spot。

#### 10.1 获取预设节点列表
```
GET /api/v1/dxcluster/nodes
Authorization: Bearer {token}

响应:
[
    { "host": "dxc.ve7cc.net", "port": 7373, "name": "VE7CC", "country": "Canada", "remark": "北美西海岸，老牌节点" },
    { "host": "dxc.k1ttt.net", "port": 7373, "name": "K1TTT", "country": "USA", "remark": "美国东海岸" },
    ...
]
```

#### 10.2 获取连接状态
```
GET /api/v1/dxcluster/status
Authorization: Bearer {token}

响应:
{
    "connected": true,
    "connecting": false,
    "current_node": { "host": "...", "port": 7373, "name": "VE7CC", ... },
    "callsign": "BA7ABC",
    "spot_count": 42,
    "uptime_seconds": 3600.5
}
```

#### 10.3 连接到节点
```
POST /api/v1/dxcluster/connect
Authorization: Bearer {token}
Body: { "node_host": "dxc.ve7cc.net", "node_port": 7373 }

响应 200:
{ "success": true, "message": "Connected to VE7CC", "status": { ... } }

错误 502: 连接失败
错误 409: 没有激活台站（无法登录 cluster）
```

**说明**：使用当前用户激活台站的呼号登录 cluster。同一时间只能有一个连接，切换节点时自动断开旧连接。

#### 10.4 断开连接
```
POST /api/v1/dxcluster/disconnect
Authorization: Bearer {token}

响应: { "connected": false, ... }
```

#### 10.5 获取历史 spot
```
GET /api/v1/dxcluster/spots?limit=50
Authorization: Bearer {token}

响应:
[
    {
        "spotter": "VE7CC",
        "freq": "14074",
        "dx_callsign": "JA1ABC",
        "mode": "FT8",
        "comment": "CQ",
        "time_utc": "1230Z",
        "band": "20m",
        "received_at": "2026-06-20T12:30:00Z",
        "dxcc_entity": "Japan"
    },
    ...
]
```

#### 10.6 WebSocket 实时 spot
```
ws://host/api/v1/dxcluster/ws?token={jwt_token}

消息格式:
{ "type": "spot", "data": { "spotter": "VE7CC", "dx_callsign": "JA1ABC", ... } }
{ "type": "disconnect", "message": "cluster disconnected" }
```

**说明**：浏览器原生 WebSocket 不支持自定义 header，通过 query param `?token=` 传递 JWT 认证。连接后先推送历史 spot（最多 100 条），后续实时推送新 spot。

---

### 十一、梅登网格地图模块 (`/api/v1/map`)

#### 11.1 获取网格聚合数据
```
GET /api/v1/map/grids?my_grid=OL63
Authorization: Bearer {token}

参数:
  my_grid: 可选，按 my_gridsquare 前4位过滤（匹配激活台站网格）

响应:
{
    "my_grid": "OL63",
    "my_lat": 39.5,
    "my_lon": 116.5,
    "grids": [
        { "grid": "PM95", "count": 12, "confirmed": 5, "lat": 35.5, "lon": 139.5 },
        { "grid": "FN31", "count": 3, "confirmed": 1, "lat": 41.5, "lon": -73.5 }
    ]
}
```

**说明**：
- `my_grid` / `my_lat` / `my_lon`：从用户激活位置获取
- `grids`：按 `grid_square` 前 4 位分组聚合，包含 QSO 数、已确认数（`qsl_rcvd='Y' OR lotw_rcvd='Y'`）、网格中心经纬度
- 传入 `my_grid` 时仅返回 `my_gridsquare` 匹配的 QSO 聚合

---

### 十二、登出
```
POST /api/v1/auth/logout
Authorization: Bearer {token}

响应: { "message": "Logout successful" }
```

#### 1.6 申请注销账号（仅服务器模式）
```
POST /api/v1/auth/delete-account
Authorization: Bearer {token}
Content-Type: application/json

{
    "password": "user_password"
}

响应 200:
{
    "message": "Account deletion scheduled. You have 30 days to cancel.",
    "scheduled_at": "2024-02-15T10:30:00",
    "cooldown_days": 30
}
```

**说明**：账号不会立即删除，进入 30 天冷却期。冷却期内用户可取消。仅 MySQL 模式可用。

#### 1.7 撤销注销申请
```
POST /api/v1/auth/cancel-delete
Authorization: Bearer {token}

响应 200: { "message": "Account deletion cancelled" }
```

#### 1.8 确认注销账号（需验证码）
```
POST /api/v1/auth/confirm-delete
Authorization: Bearer {token}
Content-Type: application/json

{
    "code": "123456"
}

响应 200: { "message": "Account deleted successfully" }
```

**说明**：需要邮箱验证码确认。验证码通过邮件发送（当前为占位实现）。

---

### 十三、管理员 API (`/api/v1/admin`)

**访问条件**：仅 MySQL 模式挂载，需要 `role=admin` 角色。

#### 13.1 用户管理
```
GET    /api/v1/admin/users?page=1&page_size=20&keyword=&role=&is_active=
GET    /api/v1/admin/users/{user_id}
POST   /api/v1/admin/users/{user_id}/toggle          # 启用/禁用
POST   /api/v1/admin/users/{user_id}/reset-password   # 重置密码
DELETE /api/v1/admin/users/{user_id}                  # 删除用户
GET    /api/v1/admin/users/{user_id}/stats            # 用户统计
```

#### 13.2 系统状态与配置
```
GET    /api/v1/admin/system/status                    # 系统状态
GET    /api/v1/admin/system/config                    # 获取所有配置
PATCH  /api/v1/admin/system/config                    # 更新配置
```

#### 13.3 审计日志
```
GET    /api/v1/admin/audit-logs?page=1&page_size=50&action=LOGIN
```

**说明**：所有管理员操作均记录到审计日志，包含操作人、操作类型、时间、IP 地址。

---

### 十四、Token 黑名单机制

MySQL 模式下，系统实现 JWT Token 黑名单：

1. 用户登录时，生成包含 JTI（唯一令牌标识）的 JWT
2. 用户登出时，JTI 加入 Redis 黑名单（TTL = token 剩余有效期）
3. 每个请求检查 JTI 是否在黑名单中，命中则拒绝（401）
4. SQLite 模式不启用黑名单，登出仅清除前端本地令牌

| 组件 | 说明 |
|------|------|
| `security.py` | JWT 生成时注入 JTI |
| `token_blacklist_service.py` | Redis/内存 黑名单读写 |
| `dependencies.py` | 请求拦截检查黑名单 |

---

## 错误处理

### 标准错误响应
```json
{
    "code": 400,
    "message": "Bad request",
    "data": {
        "error_code": "INVALID_INPUT",
        "error_message": "Detail description"
    }
}
```

### 常见错误码
| 错误码 | 说明 |
|--------|------|
| INVALID_INPUT | 输入参数无效 |
| UNAUTHORIZED | 未授权 |
| NOT_FOUND | 资源不存在 |
| VALIDATION_ERROR | 数据验证失败 |
| RATE_LIMITED | 请求过于频繁 |
| INTERNAL_ERROR | 服务器内部错误 |

## API文档访问
- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`
