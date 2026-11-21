# API 端点说明

各模块端点的请求、返回与消息格式。响应包装、状态码、认证、分页和错误格式等共用规则见[API 通用规范](03_API通用规范.md)。

## 一、用户认证模块（`/api/v1/auth`）

| 方法 | 路径 | 请求 | 返回或条件 |
| --- | --- | --- | --- |
| POST | `/register` | JSON 注册信息 | 201，用户对象 |
| POST | `/login` | JSON 用户名、密码 | 令牌和用户对象 |
| GET | `/me` | Bearer 认证 | 当前用户 |
| PATCH | `/me` | JSON 偏好字段 | 更新后的用户 |
| POST | `/change-password` | JSON 密码字段 | `{message}` |
| POST | `/logout` | Bearer 认证 | `{message}` |
| POST | `/delete-account` | `{"password":"..."}` | MySQL 模式申请注销 |
| POST | `/cancel-delete` | 无请求体 | MySQL 模式撤销申请 |
| POST | `/confirm-delete` | `{"code":"..."}` | MySQL 模式确认注销 |

注册请求：

```json
{
  "username": "radio_user",
  "email": "radio@example.com",
  "password": "replace-with-your-password",
  "confirm_password": "replace-with-your-password",
  "full_name": "Radio Operator",
  "timezone": "Asia/Shanghai",
  "language": "zh-CN"
}
```

用户名长度为 3～50，密码至少 8 个字符且最多 72 个 UTF-8 字节；注册、改密和管理员重置使用相同规则。邮箱须满足邮箱格式，两个密码须一致。`full_name` 可省略，时区和语言默认 `UTC`、`zh-CN`。

登录请求为 JSON，不是 OAuth 表单：

```json
{"username":"radio_user","password":"replace-with-your-password","remember_me":false}
```

`remember_me` 不改变后端的令牌有效期。登录响应中的 `expires_in` 单位为秒；`user` 包含 `id`、`username`、`email`、`full_name`、`timezone`、`language`、`role`、`is_active`、`created_at`。

PATCH 资料支持 `full_name`、`timezone`、`language`。改密请求支持 `old_password`、`new_password`、`confirm_password`。两种数据库模式下改密和管理员重置都会在同一事务中撤销全部旧会话；客户端随后重新登录。

注销申请记录 30 天冷却期；到期后还需验证码确认，不会自动删除账户。邮件发送尚未接入，验证码也不通过申请接口返回，因此该流程尚不能作为完整的用户自助注销功能。

## 二、用户信息模块（`/api/v1/users`）

`GET /me` 返回当前用户，与 `GET /auth/me` 使用同一认证依赖。资料修改使用 `PATCH /auth/me`。

## 三、台站模块（`/api/v1/stations`）

| 方法 | 路径 | 请求或返回 |
| --- | --- | --- |
| POST | 空路径 | `{"callsign":"BA7ABC"}`，201 返回台站 |
| GET | 空路径 | 当前用户未删除台站数组 |
| GET | `/{station_id}` | 单个台站 |
| PATCH | `/{station_id}` | `{"callsign":"BA7XYZ"}` |
| DELETE | `/{station_id}` | 204；关联日志进入回收站，位置和台站软删除 |

空路径指 `/api/v1/stations`，不附加尾部 `/`，下文同理。创建呼号长度为 3～20；服务层去除首尾空格并转大写。同呼号的软删除台站优先恢复，位置和日志不会随之恢复。

## 四、位置模块（`/api/v1/locations`）

| 方法 | 路径 | 请求或返回 |
| --- | --- | --- |
| POST | 空路径 | JSON 位置；201 返回位置 |
| GET | 空路径 | 位置数组，可用查询参数 `station_id` 筛选 |
| GET | `/active/current` | 激活位置；没有时返回 404 |
| POST | `/{location_id}/activate` | 激活目标并取消当前用户其他位置的激活状态 |
| PATCH | `/{location_id}` | 更新位置字段 |
| DELETE | `/{location_id}` | 204；软删除，日志中的位置外键保留 |

创建示例：

```json
{
  "station_id": 1,
  "name": "Home",
  "grid_square": "OL63",
  "radio_model": "IC-7300",
  "antenna_model": "Dipole",
  "antenna_height": 10,
  "qth": "Home station"
}
```

`station_id` 和 `grid_square` 必填；`name` 默认 `Default`。PATCH 支持名称、网格、电台、天线、高度和 QTH，不支持通过 PATCH 更换所属台站。

## 五、日志管理模块（`/api/v1/logs`）

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| POST | 空路径 | 创建 QSO，201 返回日志对象 |
| GET | 空路径 | 筛选、排序、分页查询 |
| GET | `/{log_id}` | 单条日志 |
| PATCH | `/{log_id}` | 修改日志 |
| DELETE | `/{log_id}` | 204；备份到回收站并软删除 |
| GET | `/stats/overview` | 当前用户全部日志概览，`{data: ...}` |
| POST | `/import` | multipart 文件导入 |
| GET | `/export` | 下载 ADI 文件 |
| GET | `/recycle/list` | 回收站分页列表 |
| POST | `/recycle/{deleted_id}/restore` | 恢复日志 |
| POST | `/recycle/batch-delete` | `{"ids":[1,2]}`，返回 `{"deleted":2}` |
| POST | `/recycle/clear-all` | 清空回收站条目，返回 `{deleted}` |

### 创建与修改

有激活位置时，最小创建请求为：

```json
{"call_sign":"JA1ABC","band":"20m","mode":"FT8","freq":14.074}
```

`call_sign` 必填，最长 20 个字符。可显式指定 `station_id`、`location_id`、`qso_date`、`time_on`；未指定时从当前激活位置补全。台站、位置必须属于当前用户且未删除，位置必须属于所选台站；归属不符返回 404，关联不一致返回 422。

未指定 `station_id` 时，先使用显式 `location_id`，否则使用当前激活位置推断台站；两者都不可用时返回 422，不创建日志。显式指定合法台站的请求不要求存在激活位置。

CRUD 支持的其余字段包括结束日期与时间、收发频率与波段、模式、RST、对方网格、操作员、QTH、QSL/eQSL/LoTW 状态、距离、DXCC、功率、本网格、台站呼号字段和备注。响应额外包含 `id`、`user_id`、时间戳及展示用的 `station_callsign`、`location_name`。

PATCH 可修改 `station_id`、`location_id`，但更新后的关联仍须满足归属规则；不执行创建时的 QSL 联动。纸质和 eQSL 状态允许 `Y/N/R/I`，LoTW 允许 `Y/N`。

创建和导入还支持 `my_call`、`prop_mode`、`sat_name`、`srx`、`stx`、`contest_id`；字段长度受 Schema 校验。字段与类型见[数据库文档](02_数据库设计说明.md)。

### 列表筛选与排序

查询参数包括分页参数、`start_date`、`end_date`、`band`、`mode`、`call_sign`、`grid_square`、`dxcc`、`station_id`、`sort_by`、`sort_order`。

- 呼号为包含匹配；网格按对方网格前 4 位匹配。
- 不传 `station_id` 时查询当前用户全部未删除日志；前端可自行传入激活台站。
- 默认按 `qso_date desc` 排序，`sort_order` 只允许 `asc/desc`。
- 排序白名单为 `qso_date`、`call_sign`、`band`、`mode`、`freq`、`rst_sent`、`rst_rcvd`、`qsl_sent`、`qsl_rcvd`、`lotw_sent`、`lotw_rcvd`、`dxcc`、`distance`、`created_at`、`station_id`。其他符合参数格式的值回退到日期排序。

### 导入

```bash
curl -X POST 'http://localhost:8000/api/v1/logs/import?station_id=1' \
  -H "Authorization: Bearer $RADIO_TOKEN" \
  -F 'file=@contacts.adi'
```

`file` 为 multipart 字段，`station_id` 为查询参数。文件名须以 `.adi` 或 `.adif` 结尾（不区分大小写），按 UTF-8 解码。上传上限由 `MAX_UPLOAD_SIZE` 控制，默认 **50 MiB**；代理允许 51 MiB 以容纳 multipart 开销。

不传台站时使用当前激活位置所属台站。导入识别已有记录的键为 `(call_sign, qso_date, time_on, band, mode, freq)`，范围是当前用户全部未删除日志，台站不在键中。

命中已有记录时，服务只补充空的 RST、网格、本网格、备注、功率和结束日期/时间；收到确认的 QSL、LoTW、eQSL 状态可向 `Y` 更新，并同时设置相应发送状态。未命中时创建记录，每累计 500 条新记录提交一次。导入不保证整文件原子性，也不保证所有 ADIF 字段原样往返。

返回 `file_id`、`total_records`、`imported`、`skipped`、`duplicates`、`merged`、`updated`、`status`、`database_failed`、`errors`。`updated` 与 `merged` 相同；`errors` 最多返回 10 条，格式错误包含记录序号 `line`。格式错误可产生 `partial` 结果。数据库批次失败会回滚当前批次并中止处理，返回 HTTP 503，计数只包含已经提交的结果；此前批次不会撤回。调用方不能把 503 当作全文件未写入而盲目重试。

### 导出

查询参数为 `format=adi|adif`、日期范围、`band`、`station_id`、`location_id`。两种 `format` 值都生成 `.adi` 文件，文件名为 `{UTC日期}_{台站呼号或AllStations}.adi`。

传 `location_id` 时，实际按该位置网格的前 4 位筛选 `my_gridsquare`，不是直接按日志 `location_id` 筛选。文件名同时附加网格后缀。

导出包含源码明确输出的通联、收发频率/波段、RST、本台呼号与网格、功率、传播、卫星、比赛、备注及六个 QSL/eQSL/LoTW 状态字段。ADI 仍不包含用户、台站关系、会话等完整数据库内容，不能替代数据库备份。

### 回收站

`deleted_id` 是回收站条目 ID，不是原日志 ID。列表返回 `log_id`、呼号、日期、波段、模式、DXCC、删除原因、删除与到期时间及 `days_remaining`。后者按剩余整天数计算。

保留期为 7 天。恢复优先取消原日志的软删除；原日志不存在时才从快照重建。过期清理和“永久删除”操作只删除回收站备份，不物理删除 `qso_logs` 中的软删除行。

恢复过期条目返回 422，原日志保持删除状态，快照不标记为已恢复，也不新增日志。

## 六、统计分析模块（`/api/v1/stats`）

全部返回 `{data: ...}`。

| 方法与路径 | 参数与返回 |
| --- | --- |
| `GET /overview` | 可选 `station_id`；QSO、DXCC、确认、本月、本年、台站数等概览 |
| `GET /band-mode` | `{bands, modes}`；每项含波段或模式、`qso_count`、`percentage` |
| `GET /dxcc` | `{total_dxcc, dxcc_list}`，每项含 `entity`、`count` |
| `GET /dxcc-chart` | `bands`、`entities`、`band_confirmed`、`band_worked`、`total_entities` |
| `GET /band-mode-matrix` | `{band, mode, count}` 数组 |

只有概览接收台站参数，其余端点统计当前用户全部未删除日志。概览“已确认”使用 `qsl_rcvd=Y` 或 `lotw_rcvd=Y`；DXCC 图表使用 `lotw_rcvd=Y`，eQSL 不参与这两项判断。

## 七、呼号查询模块（`/api/v1/callsigns`）

| 方法 | 路径 | 参数或返回 |
| --- | --- | --- |
| GET | `/{call_sign}` | 呼号信息对象，可含 `cached`、`cached_at`、`offline` |
| POST | `/batch-query` | JSON `{"call_signs":["BA7ABC","JA1ABC"]}` |
| GET | `/search/{prefix}` | 搜索数据库缓存，可选查询参数 `country`，最多 20 条 |
| DELETE | `/cache/{call_sign}` | 删除共享缓存；无论是否命中均返回 204 |

查询顺序为新缓存、在线 QRZ、旧缓存、离线 DXCC 推断。离线结果不代表 QRZ 注册情况，详细身份信息可能为空。批量查询单次最多提交 50 个呼号；超过 50 个返回 422，拒绝整个请求且不执行呼号查询，不截断输入。当前前端界面仅支持单呼号查询，批量端点供 API 客户端使用。

## 八、数据同步模块（`/api/v1/sync`，预留）

| 方法 | 路径 | 行为 |
| --- | --- | --- |
| POST | `/github/config` | 查询参数 `github_url`、`branch=main`、`auto_sync=false`；返回配置回显，不持久化 |
| POST | `/github/push` | 要求配置 `GITHUB_TOKEN`；记录同步历史，不执行文件上传 |
| POST | `/github/pull` | 返回 `not_implemented`，不下载数据 |
| GET | `/history` | 当前用户的同步历史分页 |

这些端点的成功响应不构成备份成功凭据。

## 九、快捷链接模块（`/api/v1/shortcuts`）

| 方法 | 路径 | 参数或返回 |
| --- | --- | --- |
| GET | 空路径 | 内置链接与当前用户自定义链接数组 |
| POST | 空路径 | 查询参数 `name`、`url`、`description`；201 返回链接 |
| DELETE | `/{shortcut_id}` | 删除自定义链接，204 |

自定义链接保存在进程内存中，不跨 worker 共享，重启后丢失。POST 的参数不是 JSON 请求体。

## 十、DX Cluster 模块（`/api/v1/dxcluster`）

| 方法 | 路径 | 参数或返回 |
| --- | --- | --- |
| GET | `/nodes` | 预设节点数组 |
| GET | `/status` | 连接状态对象 |
| GET | `/spots` | `limit=50`，范围 1～100；历史 spot 由新到旧 |
| POST | `/connect` | JSON `{"node_host":"host.example","node_port":7300}` |
| POST | `/disconnect` | 返回断开后的状态 |
| WebSocket | `/ws` | 首条消息 `{"token":"<access_token>"}` 后接收历史和实时消息 |

连接使用操作者激活位置所属台站的呼号。管理器全进程共享，切换和断开影响所有订阅者，因此 MySQL 模式只允许管理员控制；公开 spot 可由已登录用户读取。连接仅允许预设或 `DX_CLUSTER_NODES` 配置的地址，不接受任意自定义目标。后端不自动重连 Telnet。

WebSocket 连接后逐条发送最多 100 条历史，再发送实时数据：

```json
{"type":"spot","data":{"spotter":"BA7ABC","freq":"14074.0","freq_mhz":"14.074","dx_callsign":"JA1ABC","mode":"FT8","comment":"FT8 CQ","time_utc":"1200Z","band":"20m","received_at":"2026-01-01T12:00:00Z","dxcc_entity":"Japan"}}
```

节点断开通知为 `{"type":"disconnect","message":"cluster disconnected"}`。WebSocket 的 `freq` 为节点原始频率字符串，`freq_mhz` 为归一化后的 MHz 字符串，`dxcc_entity` 为推断实体。HTTP `/spots` 受 `SpotResponse` 限制，不返回后两项，`freq` 转为浮点数但保留原始量级，不能一律当作 MHz。后端历史缓冲为 100 条，前端显示缓冲为 200 条。连接状态包含 `connected`、`connecting`、`current_node`、`callsign`、`spot_count`、`uptime_seconds`。

## 十一、梅登网格地图模块（`/api/v1/map`）

| 方法 | 路径 | 返回 |
| --- | --- | --- |
| GET | `/grids` | `{my_grid, my_lat, my_lon, grids}` |

每个网格项含 `grid`、`count`、`confirmed`、`lat`、`lon`。

查询参数 `my_grid` 按本台网格前 4 位过滤；未传时默认使用激活位置网格，仅在两者都没有时统计全部本网格。后台按原始对方网格分组后输出 4 位网格，多个 6 位网格可能输出相同的 4 位网格标识。确认数按纸质 QSL 或 LoTW 收到确认计算。

## 十二、登出与账号状态

`POST /auth/logout` 在 SQLite 和 MySQL 都删除当前会话，提交成功后才报告登出成功。改密或管理员重置、禁用或删除账号会撤销全部会话。旧令牌不能因用户重新启用而复活，客户端重新登录。

## 十三、管理员 API（`/api/v1/admin`）

仅服务器模式注册，要求管理员身份。

| 方法 | 路径 | 参数或行为 |
| --- | --- | --- |
| GET | `/users` | `page`、`page_size`、`keyword`、`role`、`is_active` |
| GET | `/users/{user_id}` | 用户信息 |
| POST | `/users/{user_id}/toggle` | 切换启用状态 |
| POST | `/users/{user_id}/reset-password` | JSON `{"new_password":"..."}` |
| DELETE | `/users/{user_id}` | 软删除用户 |
| GET | `/users/{user_id}/stats` | `{qso_count, station_count}` |
| GET | `/audit-logs` | 分页，可选 `user_id`、`action` |
| GET | `/system/config` | 配置项数组，空表时初始化默认项 |
| PATCH | `/system/config` | JSON `{"key":"...","value":"..."}`，修改已有项 |
| GET | `/system/status` | 数据库模式、用户、日志、台站及在线会话统计 |

系统配置表不等同于环境配置；存储开关值不会自动调整导入限制、限流或节点列表。

## 十四、会话与令牌撤销

JWT 包含 `sub`、`exp`、`jti`、`token_type=access`。HTTP 和 WebSocket 共用会话认证：令牌、用户状态及未过期会话必须同时有效。登出删除当前会话，改密、管理员重置、禁用和删除用户撤销其全部会话。Redis 与内存黑名单已移除；数据库失败不会被当作认证成功或普通 401。

## 十五、UDP 模块（`/api/v1/udp`）

| 方法 | 路径 | 请求与返回 |
| --- | --- | --- |
| GET | `/status` | `{data: {running, receiving, wsjtx_port, n1mm_port, qso_count, last_qso, ws_clients}}`；非接收者看不到 QSO 内容及计数 |
| POST | `/start` | JSON `{"wsjtx_port":2237,"n1mm_port":12060}`，字段可省略 |
| POST | `/stop` | `{data: {running:false}}` |
| POST | `/save-to-log` | `QSOLogCreate` JSON；成功为 `{data:{id,call_sign}}` |
| WebSocket | `/ws` | 首条消息认证后接收 QSO 与保存确认 |

广播消息为 `{type:"qso_received", source:"wsjtx"或"n1mm", data:QSO字段, count:计数}`。接收事件不会自动持久化。客户端可调用保存端点，也可发送 `{"action":"save","data":{"call_sign":"JA1ABC"}}`；后者成功后收到 `{type:"qso_saved",data:{id,call_sign}}`。

REST 保存失败返回明确的 4xx/5xx，不再使用 HTTP 200 包装失败；WebSocket 参数与业务错误返回 `{type:"error",message:...}`，认证失效关闭 4401。

主机只保留一个监听实例，启动者拥有本次监听及接收流，其他用户不能停止或接管。MySQL 模式仅管理员能启停；SQLite 允许已登录用户。默认仅绑定 `127.0.0.1` 并接收本机来源；其他设备需由部署方配置 `UDP_BIND_HOST`、`UDP_ALLOWED_SOURCES`。支持 WSJT-X schema 2/3 的 QSO Logged（type 5，QDataStream）与 N1MM XML；接收不自动保存。两个端口必须不同且在 1024～65535。
