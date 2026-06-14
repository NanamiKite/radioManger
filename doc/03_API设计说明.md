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

**说明**：导出文件名格式为 `{日期}_{台站呼号}.adi`。`station_id` 必选。

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
    "qrz_url": "https://www.qrz.com/db/JA1ABC"
}
```

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
