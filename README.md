# RadioManager

RadioManager 用于管理业余无线电 QSO 日志。你可以导入 `.adi` / `.adif` 文件，按台站整理通联记录，查看 DXCC 和波段统计，也可以在地图上查看已通联的梅登网格。

前端使用 Vue 3，后端使用 FastAPI。个人使用可把数据保存在本机 SQLite 数据库中；多人访问可部署 MySQL 后端，通过浏览器使用。

## 日常使用

- 管理台站和操作位置，记录呼号、网格、电台与天线信息。
- 新建、编辑、筛选和导出 QSO 日志；删除后可在 7 天内从回收站恢复。
- 查询呼号，使用数据库缓存、QRZ.com 查询或离线 DXCC 前缀推断。
- 查看 DX Cluster 实时 spot、网格地图和常用天线计算工具。
- 切换中文、英文和浅色、深色主题。

首次登录后，先创建台站，再创建并激活操作位置。未指定台站的新日志和导入操作会使用这个位置所属的台站。

## 从源码启动

以下步骤使用 Python 3.12、Node.js 22 和 SQLite。Windows 可在 PowerShell 中完成相同配置，详见[部署说明](doc/06_部署说明.md)。

在项目根目录创建 `backend/.env`，填入以下内容。将数据库路径替换为本机绝对路径，`SQLITE_URL` 与 `SQLITE_PATH` 应指向同一个文件：

```dotenv
DATABASE_MODE=sqlite
SQLITE_URL=sqlite:////absolute/path/radioManger/backend/radiomanager.db
SQLITE_PATH=/absolute/path/radioManger/backend/radiomanager.db
SECRET_KEY=replace-with-a-random-secret
ENVIRONMENT=development
DEBUG=true
ENABLE_TEST_ACCOUNT=false
CORS_ORIGINS=["http://localhost:5173"]
```

用下面的命令生成 `SECRET_KEY`，并把输出填入配置文件。已有配置时请直接编辑，保留原密钥和数据路径。

```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

启动后端：

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python -m app.scripts.init_db
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

在另一个终端启动前端：

```bash
cd frontend
npm ci
npm run dev
```

打开 [http://localhost:5173](http://localhost:5173)，注册账户后登录。后端健康检查为 [http://localhost:8000/health](http://localhost:8000/health)；设置 `DEBUG=true` 后可访问 [API 文档](http://localhost:8000/docs)。

完成上述配置后，也可在项目根目录运行 `./start-local.sh` 启动前后端。它会使用 `backend/.env` 中的配置。

## 服务器与桌面使用

Docker Compose 提供 Nginx、FastAPI、MySQL 和 Redis 的组合。部署前需要配置凭据，启动后需要执行数据库及管理员初始化，步骤见[局域网与服务器部署](doc/06_部署说明.md#2-局域网部署)。

Windows 本地发布包通过 `release_server.py` 在 8000 端口同时提供网页和 API。仓库另外保留了 pywebview 桌面启动器、Electron 配置和 Capacitor Android 配置；它们的启动条件与打包方式见[部署说明](doc/06_部署说明.md)。

GitHub 同步和邮件发送尚未完成，不能用作备份或账号注销邮件服务。地图底图、QRZ.com 和 DX Cluster 需要网络连接；本地日志读写使用本机数据库。

## 文档

- [项目总览与源码导航](doc/01_项目总文件说明.md)
- [数据库字段与数据生命周期](doc/02_数据库设计说明.md)
- [API 请求、响应与实时消息](doc/03_API设计说明.md)
- [前端架构](doc/04_前端架构设计.md) / [后端架构](doc/05_后端架构设计.md)
- [部署、初始化与备份](doc/06_部署说明.md)
- [系统架构图](doc/07_系统架构图.md)

[PROJECT.md](PROJECT.md) 提供简短的架构索引，便于从功能定位源码。
