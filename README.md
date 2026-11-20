# RadioManager

RadioManager 用于管理业余无线电 QSO 日志。你可以导入 `.adi` / `.adif` 文件，按台站整理通联记录，查看 DXCC 和波段统计，也可以在地图上查看已通联的梅登网格。

前端使用 Vue 3，后端使用 FastAPI。个人使用可把数据保存在本机 SQLite 数据库中；多人访问可部署 MySQL 后端，通过浏览器使用。

## 功能

- 管理台站和操作位置，记录呼号、网格、电台与天线信息。
- 新建、编辑、筛选和导出 QSO 日志；删除后可在 7 天内从回收站恢复。
- 查询呼号，使用数据库缓存、QRZ.com 查询或离线 DXCC 前缀推断。
- 查看 DX Cluster 实时 spot、网格地图和常用天线计算工具。
- 切换中文、英文和浅色、深色主题。

首次登录后，先创建台站，再创建并激活操作位置。未指定台站的新日志和导入操作会使用这个位置所属的台站。

## 快速开始

- [源码本地运行](doc/07_本地部署.md) —— Python 3.12 + Node.js 22 + SQLite，含 Windows 说明。
- [服务器部署](doc/08_服务器部署.md) —— Docker Compose（Nginx + FastAPI + MySQL + Redis），或云服务器 TLS 部署。
- [Windows 与 Android 部署](doc/09_Windows与Android部署.md) —— Windows 本地发布包、pywebview、Electron 与 Capacitor。

## 文档

设计与部署文档按功能拆分，索引见 [doc/README.md](doc/README.md)。[PROJECT.md](PROJECT.md) 提供简短的架构索引，便于从功能定位源码。

## 当前限制

GitHub 同步和邮件发送尚未完成，不能用作备份或账号注销邮件服务。地图底图、QRZ.com 和 DX Cluster 需要网络连接；本地日志读写使用本机数据库。
