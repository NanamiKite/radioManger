<div align="center">

<img src="frontend/public/icon.svg" alt="RadioManager 应用图标" width="120" height="120" />

# RadioManager

**把每一次通联，记进自己的日志。**

导入 ADI / ADIF，按台站整理 QSO，查看 DXCC、波段统计与梅登网格地图。

[![Release](https://img.shields.io/github/v/release/NanamiKite/radioManger?style=flat&sort=date&display_name=release)](https://github.com/NanamiKite/radioManger/releases/latest)
[![GitHub stars](https://img.shields.io/github/stars/NanamiKite/radioManger?style=flat)](https://github.com/NanamiKite/radioManger/stargazers)
[![Downloads](https://img.shields.io/github/downloads/NanamiKite/radioManger/total?style=flat)](https://github.com/NanamiKite/radioManger/releases)

[下载应用](https://github.com/NanamiKite/radioManger/releases/latest) · [使用文档](doc/README.md) · [源码运行](doc/07_本地部署.md) · [反馈问题](https://github.com/NanamiKite/radioManger/issues)

</div>

RadioManager 是业余无线电 QSO 日志管理工具。个人使用时，日志保存在本机 SQLite；多人访问时，可以部署 MySQL 后端，通过浏览器使用。

## 功能

- 管理台站和操作位置，记录呼号、网格、电台与天线信息
- 新建、编辑、筛选和导出 QSO 日志；删除后 7 天内可从回收站恢复
- 查询呼号：数据库缓存、QRZ.com 或离线 DXCC 前缀推断
- DX Cluster 实时 spot、梅登网格地图和常用天线计算工具
- 中英文界面，浅色 / 深色主题

## 开始使用

**Windows 用户**：从 [Releases](https://github.com/NanamiKite/radioManger/releases/latest) 下载 Windows 64 位 ZIP 包，解压后运行 `start.bat`，在浏览器打开 <http://localhost:8000>。详细说明见 [Windows 部署](doc/09_Windows与Android部署.md)。

**从源码运行**：准备 Python 3.12 和 Node.js 22，按[本地部署指南](doc/07_本地部署.md)配置并启动前后端。局域网或云服务器部署见[服务器部署指南](doc/08_服务器部署.md)。

首次使用：注册或登录账户 → 创建台站 → 创建并激活操作位置。未指定台站的新日志和导入操作会使用激活位置所属的台站。

## 文档

- [文档索引](doc/README.md) —— 部署、接口和架构说明
- [PROJECT.md](PROJECT.md) —— 从功能定位源码

## 限制

GitHub 同步和邮件发送还没有完成，不能当备份或账号注销邮件用。地图底图、QRZ.com 和 DX Cluster 需要联网；日志数据存在本机或自己部署的数据库里。
