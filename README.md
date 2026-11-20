# RadioManager

业余无线电 QSO 日志管理工具。导入 `.adi` / `.adif` 文件，按台站整理通联记录，查看 DXCC 和波段统计，也可以在地图上查看已通联的梅登网格。

前端 Vue 3，后端 FastAPI。个人使用可以把数据放在本机 SQLite；多人使用部署 MySQL 后端，通过浏览器访问。

## 功能

- 管理台站和操作位置，记录呼号、网格、电台与天线信息
- 新建、编辑、筛选和导出 QSO 日志；删除后 7 天内可从回收站恢复
- 查询呼号：数据库缓存、QRZ.com 或离线 DXCC 前缀推断
- DX Cluster 实时 spot、梅登网格地图和常用天线计算工具
- 中英文界面，浅色 / 深色主题

第一次使用：注册账户 → 创建台站 → 创建并激活操作位置。之后新日志和导入默认使用激活位置所属的台站。

## 快速开始

源码运行需要 Python 3.12 和 Node.js 22。先按[本地部署](doc/07_本地部署.md)配置 `backend/.env`，然后：

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
python -m pip install -r requirements.txt
python -m app.scripts.init_db
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另开一个终端：

```bash
cd frontend
npm ci
npm run dev
```

打开 <http://localhost:5173> 注册账户即可。

其他部署方式：[Docker 服务器](doc/08_服务器部署.md) · [Windows 本地包 / Android](doc/09_Windows与Android部署.md)

## 文档

- [文档索引](doc/README.md)
- [PROJECT.md](PROJECT.md) —— 架构索引，从功能定位源码

## 限制

GitHub 同步和邮件发送还没有完成，不能当备份或账号注销邮件用。地图底图、QRZ.com 和 DX Cluster 需要联网；日志数据存在本机或自己部署的数据库里。
