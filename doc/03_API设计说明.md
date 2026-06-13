# API设计说明文档

## API概述

RadioManager后端采用RESTful API设计模式，基于FastAPI框架实现。所有API均使用JSON格式传输，支持JWT令牌认证。

## API基本规范

### 请求/响应格式

**统一响应格式**：
```json
{
    "code": 200,
    "message": "Success",
    "data": {
        // 具体数据
    },
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### HTTP状态码
- `200`: 成功
- `201`: 创建成功
- `204`: 无内容
- `400`: 请求参数错误
- `401`: 未认证/令牌过期
- `403`: 禁止访问
- `404`: 资源不存在
- `409`: 资源冲突
- `422`: 数据验证失败
- `429`: 请求过于频繁
- `500`: 服务器内部错误

### 认证方式
- **令牌类型**: Bearer Token (JWT)
- **过期时间**: 7天
- **刷新令牌**: 30天
- **请求头**: `Authorization: Bearer <token>`

### 公共请求头
```
Content-Type: application/json
Authorization: Bearer {jwt_token}
X-Request-ID: {uuid}
User-Agent: {client_info}
```

### 分页参数
```json
{
    "page": 1,           // 页码(从1开始)
    "page_size": 20,     // 每页数量(1-100)
    "sort_by": "created_at",  // 排序字段
    "sort_order": "desc" // asc或desc
}
```

## API端点设计

### 一、用户认证模块 (/api/v1/auth)

#### 1.1 用户注册
```
POST /api/v1/auth/register
Content-Type: application/json

请求体:
{
    "username": "ba6zyx",
    "email": "user@example.com",
    "password": "password123",
    "confirm_password": "password123"
}

响应(201):
{
    "code": 201,
    "message": "User registered successfully",
    "data": {
        "user_id": 1,
        "username": "ba6zyx",
        "email": "user@example.com",
        "created_at": "2024-01-15T10:30:00Z"
    }
}

错误响应(422):
{
    "code": 422,
    "message": "Validation error",
    "data": {
        "errors": [
            {
                "field": "username",
                "message": "Username already exists"
            }
        ]
    }
}
```

**验证规则**：
- 用户名：3-50字符，字母数字下划线
- 邮箱：有效的邮箱格式
- 密码：至少8个字符，包含大小写字母和数字
- 密码确认：必须与密码相同

#### 1.2 用户登录
```
POST /api/v1/auth/login
Content-Type: application/json

请求体:
{
    "username": "ba6zyx",
    "password": "password123",
    "remember_me": true
}

响应(200):
{
    "code": 200,
    "message": "Login successful",
    "data": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "token_type": "Bearer",
        "expires_in": 604800,
        "user": {
            "id": 1,
            "username": "ba6zyx",
            "email": "user@example.com",
            "role": "user",
            "timezone": "Asia/Shanghai"
        }
    }
}
```

#### 1.3 刷新令牌
```
POST /api/v1/auth/refresh
Content-Type: application/json

请求体:
{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

响应(200):
{
    "code": 200,
    "message": "Token refreshed",
    "data": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "expires_in": 604800
    }
}
```

#### 1.4 登出
```
POST /api/v1/auth/logout
Authorization: Bearer {token}

响应(200):
{
    "code": 200,
    "message": "Logout successful"
}
```

#### 1.5 忘记密码
```
POST /api/v1/auth/forgot-password
Content-Type: application/json

请求体:
{
    "email": "user@example.com"
}

响应(200):
{
    "code": 200,
    "message": "Password reset email sent",
    "data": {
        "message": "Check your email for password reset link"
    }
}
```

---

### 二、用户信息模块 (/api/v1/users)

#### 2.1 获取当前用户信息
```
GET /api/v1/users/me
Authorization: Bearer {token}

响应(200):
{
    "code": 200,
    "message": "Success",
    "data": {
        "id": 1,
        "username": "ba6zyx",
        "email": "user@example.com",
        "full_name": "xxx",
        "avatar_url": "https://...",
        "role": "user",
        "timezone": "Asia/Shanghai",
        "language": "zh-CN",
        "created_at": "2024-01-15T10:30:00Z"
    }
}
```

#### 2.2 更新用户信息
```
PATCH /api/v1/users/me
Authorization: Bearer {token}
Content-Type: application/json

请求体:
{
    "full_name": "xxx",
    "timezone": "Asia/Shanghai",
    "language": "zh-CN"
}

响应(200):
{
    "code": 200,
    "message": "User profile updated",
    "data": { ... }
}
```

#### 2.3 修改密码
```
POST /api/v1/users/change-password
Authorization: Bearer {token}
Content-Type: application/json

请求体:
{
    "old_password": "oldpass123",
    "new_password": "newpass456",
    "confirm_password": "newpass456"
}

响应(200):
{
    "code": 200,
    "message": "Password changed successfully"
}
```

---

### 三、台站信息模块 (/api/v1/stations)

#### 3.1 创建台站
```
POST /api/v1/stations
Authorization: Bearer {token}
Content-Type: application/json

请求体:
{
    "callsign": "B7/ba6zyx",
    "grid_square": "OL63",
    "radio_model": "ICOM IC-7300",
    "antenna_model": "Yagi",
    "antenna_height": 10.5,
    "qth": "Shanghai, China",
    "is_primary": true
}

响应(201):
{
    "code": 201,
    "message": "Station created successfully",
    "data": {
        "id": 1,
        "user_id": 1,
        "callsign": "B7/ba6zyx",
        "grid_square": "OL63",
        "radio_model": "ICOM IC-7300",
        "antenna_model": "Yagi",
        "antenna_height": 10.5,
        "qth": "Shanghai, China",
        "is_primary": true,
        "created_at": "2024-01-15T10:30:00Z"
    }
}
```

**验证规则**：
- `callsign`: 符合业余无线电编码规则，如 ba6zyx
- `grid_square`: 4位或6位梅登网格坐标
- 必填项：callsign、grid_square

#### 3.2 获取所有台站
```
GET /api/v1/stations
Authorization: Bearer {token}

响应(200):
{
    "code": 200,
    "message": "Success",
    "data": [
        { ... },
        { ... }
    ]
}
```

#### 3.3 获取单个台站
```
GET /api/v1/stations/{station_id}
Authorization: Bearer {token}

响应(200):
{
    "code": 200,
    "message": "Success",
    "data": { ... }
}
```

#### 3.4 更新台站信息
```
PATCH /api/v1/stations/{station_id}
Authorization: Bearer {token}
Content-Type: application/json

请求体:
{
    "radio_model": "YAESU FT-991A",
    "antenna_height": 15.0
}

响应(200):
{
    "code": 200,
    "message": "Station updated successfully",
    "data": { ... }
}
```

#### 3.5 删除台站
```
DELETE /api/v1/stations/{station_id}
Authorization: Bearer {token}

响应(204):
{
    "code": 204,
    "message": "Station deleted successfully"
}
```

---

### 四、日志管理模块 (/api/v1/logs)

#### 4.1 创建通联日志
```
POST /api/v1/logs
Authorization: Bearer {token}
Content-Type: application/json

请求体:
{
    "station_id": 1,
    "call_sign": "JA1ABC",
    "qso_date": "2024-01-15",
    "time_on": "10:30:00",
    "time_off": "10:45:00",
    "band": "20m",
    "freq": 14.075,
    "mode": "FT8",
    "rst_sent": "-05",
    "rst_rcvd": "-03",
    "grid_square": "PM95",
    "qsl_sent": "N",
    "qsl_rcvd": "N",
    "comment": "Good signal"
}

响应(201):
{
    "code": 201,
    "message": "Log created successfully",
    "data": {
        "id": 1001,
        "user_id": 1,
        "station_id": 1,
        "call_sign": "JA1ABC",
        ... 其他字段
        "created_at": "2024-01-15T10:30:00Z"
    }
}
```

#### 4.2 分页查询日志
```
GET /api/v1/logs?page=1&page_size=20&sort_by=qso_date&sort_order=desc
Authorization: Bearer {token}

查询参数:
- page: 页码(默认1)
- page_size: 每页数量(默认20,最大100)
- sort_by: 排序字段(qso_date, call_sign, band, mode)
- sort_order: 排序方向(asc, desc)
- start_date: 起始日期(YYYY-MM-DD)
- end_date: 结束日期(YYYY-MM-DD)
- band: 波段过滤
- mode: 模式过滤
- call_sign: 呼号搜索(模糊匹配)

响应(200):
{
    "code": 200,
    "message": "Success",
    "data": {
        "items": [
            { ... },
            { ... }
        ],
        "total": 1500,
        "page": 1,
        "page_size": 20,
        "pages": 75
    }
}
```

#### 4.3 获取单条日志详情
```
GET /api/v1/logs/{log_id}
Authorization: Bearer {token}

响应(200):
{
    "code": 200,
    "message": "Success",
    "data": { ... }
}
```

#### 4.4 更新日志
```
PATCH /api/v1/logs/{log_id}
Authorization: Bearer {token}
Content-Type: application/json

请求体:
{
    "qsl_sent": "Y",
    "comment": "Updated comment"
}

响应(200):
{
    "code": 200,
    "message": "Log updated successfully",
    "data": { ... }
}
```

#### 4.5 删除日志
```
DELETE /api/v1/logs/{log_id}
Authorization: Bearer {token}

请求体:
{
    "reason": "Duplicate entry"
}

响应(204):
{
    "code": 204,
    "message": "Log deleted successfully"
}
```

#### 4.6 批量删除日志
```
POST /api/v1/logs/batch-delete
Authorization: Bearer {token}
Content-Type: application/json

请求体:
{
    "log_ids": [1001, 1002, 1003],
    "reason": "Clean up old entries",
    "require_confirmation": true
}

响应(200):
{
    "code": 200,
    "message": "Logs deleted successfully",
    "data": {
        "deleted_count": 3
    }
}
```

#### 4.7 导出日志
```
GET /api/v1/logs/export?format=adi&start_date=2024-01-01&end_date=2024-01-31
Authorization: Bearer {token}

查询参数:
- format: 导出格式(adi, adif, csv, json)
- start_date: 起始日期
- end_date: 结束日期
- band: 可选，按波段过滤

响应(200):
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="logs_2024_01.adi"

[ADI文件内容]
```

#### 4.8 批量导入日志
```
POST /api/v1/logs/import
Authorization: Bearer {token}
Content-Type: multipart/form-data

参数:
- file: 上传的.adi/.adif文件
- station_id: 所属台站ID(可选，使用主台站)
- auto_merge: 是否自动合并重复(布尔值)
- skip_validation: 是否跳过验证(布尔值)

响应(200):
{
    "code": 200,
    "message": "Import completed",
    "data": {
        "file_id": 1,
        "total_records": 150,
        "imported": 145,
        "skipped": 5,
        "errors": [
            {
                "line": 10,
                "record": "...",
                "error": "Invalid date format"
            }
        ]
    }
}
```

---

### 五、统计分析模块 (/api/v1/stats)

#### 5.1 获取统计概览
```
GET /api/v1/stats/overview
Authorization: Bearer {token}

响应(200):
{
    "code": 200,
    "message": "Success",
    "data": {
        "total_qso": 1500,
        "total_dxcc": 120,
        "total_waz": 38,
        "qsl_sent": 1200,
        "qsl_rcvd": 800,
        "eqsl_sent": 1450,
        "eqsl_rcvd": 1200,
        "lotw_confirmed": 600,
        "total_distance": 1500000,
        "average_distance": 1000,
        "last_qso_date": "2024-01-15",
        "last_updated": "2024-01-15T10:30:00Z"
    }
}
```

#### 5.2 获取DXCC统计
```
GET /api/v1/stats/dxcc
Authorization: Bearer {token}

响应(200):
{
    "code": 200,
    "message": "Success",
    "data": {
        "total_dxcc": 120,
        "confirmed_dxcc": 80,
        "dxcc_list": [
            {
                "entity": "Japan",
                "code": "JA",
                "count": 150,
                "first_contact": "2023-06-01",
                "last_contact": "2024-01-15",
                "qsl_status": "confirmed"
            },
            ...
        ]
    }
}
```

#### 5.3 获取WAZ统计
```
GET /api/v1/stats/waz
Authorization: Bearer {token}

响应(200):
{
    "code": 200,
    "message": "Success",
    "data": {
        "total_waz": 38,
        "confirmed_waz": 30,
        "waz_list": [
            {
                "zone": 1,
                "count": 50,
                "first_contact": "2023-06-01",
                "last_contact": "2024-01-15"
            },
            ...
        ]
    }
}
```

#### 5.4 获取波段统计
```
GET /api/v1/stats/band?start_date=2024-01-01&end_date=2024-01-31
Authorization: Bearer {token}

响应(200):
{
    "code": 200,
    "message": "Success",
    "data": {
        "band_stats": [
            {
                "band": "20m",
                "qso_count": 250,
                "percentage": 25.5
            },
            {
                "band": "40m",
                "qso_count": 200,
                "percentage": 20.4
            }
            ...
        ]
    }
}
```

#### 5.5 获取模式统计
```
GET /api/v1/stats/mode?start_date=2024-01-01&end_date=2024-01-31
Authorization: Bearer {token}

响应(200):
{
    "code": 200,
    "message": "Success",
    "data": {
        "mode_stats": [
            {
                "mode": "FT8",
                "qso_count": 500,
                "percentage": 51.0
            },
            {
                "mode": "SSB",
                "qso_count": 300,
                "percentage": 30.6
            }
            ...
        ]
    }
}
```

---

### 六、呼号查询模块 (/api/v1/callsigns)

#### 6.1 查询单个呼号
```
GET /api/v1/callsigns/{call_sign}
Authorization: Bearer {token}

响应(200):
{
    "code": 200,
    "message": "Success",
    "data": {
        "call_sign": "JA1ABC",
        "first_name": "Taro",
        "last_name": "Yamada",
        "full_name": "Taro Yamada",
        "country": "Japan",
        "grid_square": "PM95",
        "latitude": 35.6762,
        "longitude": 139.6503,
        "class": "1st Class",
        "license_date": "2010-01-15",
        "license_exp": "2025-12-31",
        "qrz_url": "https://www.qrz.com/db/JA1ABC",
        "cached": true,
        "cached_at": "2024-01-15T10:30:00Z"
    }
}

错误响应(404):
{
    "code": 404,
    "message": "Callsign not found on QRZ"
}
```

#### 6.2 批量查询呼号
```
POST /api/v1/callsigns/batch-query
Authorization: Bearer {token}
Content-Type: application/json

请求体:
{
    "call_signs": ["JA1ABC", "JA2DEF", "JA3GHI"]
}

响应(200):
{
    "code": 200,
    "message": "Success",
    "data": {
        "results": [
            { ... },
            { ... },
            { ... }
        ],
        "found": 3,
        "not_found": 0
    }
}
```

#### 6.3 搜索呼号前缀
```
GET /api/v1/callsigns/search?prefix=JA1&country=Japan
Authorization: Bearer {token}

响应(200):
{
    "code": 200,
    "message": "Success",
    "data": {
        "results": [
            { "call_sign": "JA1ABC", ... },
            { "call_sign": "JA1DEF", ... }
        ]
    }
}
```

#### 6.4 清除查询缓存
```
DELETE /api/v1/callsigns/cache/{call_sign}
Authorization: Bearer {token}

响应(204):
{
    "code": 204,
    "message": "Cache cleared"
}
```

---

### 七、数据同步模块 (/api/v1/sync)

#### 7.1 配置GitHub同步
```
POST /api/v1/sync/github/config
Authorization: Bearer {token}
Content-Type: application/json

请求体:
{
    "github_url": "https://github.com/username/radiomanager-logs",
    "branch": "main",
    "auto_sync": true,
    "sync_interval": 3600
}

响应(200):
{
    "code": 200,
    "message": "GitHub config saved",
    "data": {
        "config_id": 1,
        "github_url": "https://github.com/username/radiomanager-logs",
        "status": "verified"
    }
}
```

#### 7.2 手动同步到GitHub
```
POST /api/v1/sync/github/push
Authorization: Bearer {token}

响应(200):
{
    "code": 200,
    "message": "Push completed",
    "data": {
        "sync_id": 123,
        "status": "success",
        "added": 10,
        "updated": 5,
        "deleted": 0,
        "completed_at": "2024-01-15T10:30:00Z"
    }
}
```

#### 7.3 从GitHub拉取
```
POST /api/v1/sync/github/pull
Authorization: Bearer {token}

响应(200):
{
    "code": 200,
    "message": "Pull completed",
    "data": {
        "sync_id": 124,
        "status": "success",
        "added": 5,
        "updated": 2,
        "deleted": 0,
        "conflicts": []
    }
}
```

#### 7.4 获取同步历史
```
GET /api/v1/sync/history?page=1&page_size=20
Authorization: Bearer {token}

响应(200):
{
    "code": 200,
    "message": "Success",
    "data": {
        "items": [
            {
                "sync_id": 124,
                "sync_type": "pull",
                "source": "github",
                "status": "success",
                "added": 5,
                "updated": 2,
                "completed_at": "2024-01-15T10:30:00Z"
            }
        ],
        "total": 45
    }
}
```

---

### 八、网站快捷链接模块 (/api/v1/shortcuts)

#### 8.1 获取快捷链接列表
```
GET /api/v1/shortcuts
Authorization: Bearer {token}

响应(200):
{
    "code": 200,
    "message": "Success",
    "data": [
        {
            "id": 1,
            "name": "QRZ.com",
            "url": "https://www.qrz.com",
            "description": "Callsign database"
        },
        {
            "id": 2,
            "name": "ARRL DXCC",
            "url": "https://www.arrl.org/dxcc",
            "description": "DXCC entities list"
        }
    ]
}
```

#### 8.2 添加快捷链接
```
POST /api/v1/shortcuts
Authorization: Bearer {token}
Content-Type: application/json

请求体:
{
    "name": "EHAM",
    "url": "https://www.eham.net",
    "description": "Amateur radio reviews and information"
}

响应(201):
{
    "code": 201,
    "message": "Shortcut created",
    "data": { ... }
}
```

---

## 错误处理

### 标准错误响应格式
```json
{
    "code": 400,
    "message": "Bad request",
    "data": {
        "error_code": "INVALID_INPUT",
        "error_message": "Detailed error description",
        "fields": {
            "field_name": "error details"
        }
    },
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### 常见错误码
| 错误码 | 说明 |
|------|------|
| INVALID_INPUT | 输入参数无效 |
| UNAUTHORIZED | 未授权 |
| FORBIDDEN | 禁止访问 |
| NOT_FOUND | 资源不存在 |
| DUPLICATE | 资源已存在 |
| VALIDATION_ERROR | 数据验证失败 |
| RATE_LIMITED | 请求过于频繁 |
| INTERNAL_ERROR | 服务器内部错误 |

## 性能优化

### 缓存策略
- 用户信息：5分钟
- 呼号查询：24小时
- 统计数据：1小时
- 列表数据：3分钟

### 速率限制
- 普通用户：100请求/分钟
- 导入操作：10请求/小时
- 查询操作：1000请求/小时

## API文档访问
- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`
