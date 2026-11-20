# Windows 与 Android 部署

## 1. Windows 源码本地运行

配置 `backend/.env`，SQLite 使用 Windows 绝对路径。PowerShell 后端命令：

```powershell
cd backend
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m app.scripts.init_db
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

另一个终端在 `frontend/` 执行 `npm ci` 和 `npm run dev`。`start-windows-local.bat` 也用于启动源码前后端，它最终运行 Vite，不是 Electron 桌面安装包。

## 2. Windows Web 本地发布包

`build-win64-v2.6.0.sh` 生成包含 Python、前端静态资源和后端的 Windows 本地包。构建前先在 `frontend/` 安装依赖，再从项目根目录运行：

```bash
bash build-win64-v2.6.0.sh
```

脚本需要下载运行时和 Windows wheels，并使用 `pip`、`wget`、`unzip` 等工具；它会重建同名输出目录。版本名与输出目录以脚本为准。

使用包时从解压目录运行 `start.bat`，浏览器访问 `http://localhost:8000`。`release_server.py` 挂载 `backend/frontend_dist`，首次创建 `TEST_ACCOUNT_*` 指定的账户；它不受 `ENABLE_TEST_ACCOUNT` 开关限制。脚本生成的默认账户是 `admin/admin123`，使用前应调整包根目录 `.env` 的密钥和账户配置。已有账户不会因修改初始密码配置而自动更新。

该包的 SQLite 默认位于解压目录根部，配置文件也是包根目录 `.env`。它与源码运行的 `backend/.env` 不是同一个运行入口。

`build-win64-web.sh`、`build_release.sh` 是其他版本的包装脚本，不能仅凭文件名认定与当前包行为一致。

## 3. 桌面窗口与 Electron

`build-win64-desktop.sh` 使用 `desktop_launcher.py` 和 pywebview/Edge WebView2，在 Windows 窗口内打开本机 HTTP 页面，并在窗口关闭时结束后端进程。它与 Electron 是不同入口。

Electron 命令在 `frontend/` 运行：

```bash
npm run electron
npm run electron:win
npm run electron:win-portable
npm run electron:linux
npm run electron:mac
```

Electron 优先加载 `dist/index.html`，没有构建目录时加载本地 5173。打包配置只包含前端与 Electron 文件，`extraResources` 为空；主进程不会启动 Python 后端。现有相对 API、WebSocket 和 History 路由依赖 HTTP 服务，不能把前端壳构建成功等同于可直接使用的完整本地桌面应用。

`start-windows-web.bat` 中输入的 `RADIOMANAGER_API_URL` 没有被现有客户端读取；远程使用应配置同源代理或直接访问服务器网页。

## 4. Android 浏览器与主屏幕入口

手机可通过浏览器访问服务器网页。`public/manifest.json` 和图标提供主屏幕显示信息；仓库没有 Service Worker 或离线资源缓存实现，不能承诺完整 PWA 安装能力或离线网页运行。

## 5. Capacitor APK 打包

仓库已有 `capacitor.config.ts`，但未包含生成的 `frontend/android/` 工程。安装依赖后，首次添加平台可运行：

```bash
cd frontend
npm ci
npm run build
npx cap add android
npm run android:sync
npm run android:open
```

已有配置时无需重复 `cap init`。安装 Android 构建工具并配置好网络入口后，可运行：

```bash
npm run android:build
```

脚本执行 `assembleDebug`，产物为 `frontend/android/app/build/outputs/apk/debug/app-debug.apk`，不是签名发布包。

## 6. 网络配置

Capacitor 配置使用 `webDir=dist`、HTTPS scheme，并关闭明文流量。页面仍使用同源 `/api/v1` 和 `/health`，仅设置允许导航的主机不会指定 API 后端；需要为容器明确配置网页服务器或适配请求地址后再使用。Android 包不包含 Python 后端或本地数据库服务。
