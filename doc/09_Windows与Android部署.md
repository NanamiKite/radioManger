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

脚本需要下载运行时和 Windows wheels，并使用 `pip`、`wget`、`unzip` 等工具；它会重建同名输出目录。四套打包脚本统一读取 `frontend/package.json` 的版本（当前 `2.6.0`），包名、生成的启动提示和 README 使用同一值，不再分别硬编码版本。

使用包时从解压目录运行 `start.bat`，浏览器访问 `http://localhost:8000`。`release_server.py` 只监听本机，挂载 `backend/frontend_dist`，先执行数据库迁移。首次缺少 JWT 密钥时在包根目录 `.env` 生成并保存随机密钥，不覆盖已有值；不再创建默认管理员，首次使用在网页注册账户。旧包升级先备份并按[迁移说明](10_初始化备份与常见问题.md#1-数据库初始化)接管无版本旧库，旧默认密码须由用户自行修改。

该包的 SQLite 默认位于解压目录根部，配置文件也是包根目录 `.env`。它与源码运行的 `backend/.env` 不是同一个运行入口。

发布入口用安全的 `StaticFiles` 处理前端与 History 回退；包根地址显示网页，不再被独立后端的 `/` 信息 JSON 抢先响应。API、健康检查和缺失资源不会回退为网页。

从本次图标更新后的源码构建的 Windows 包，首次运行 `start.bat` 或桌面启动器时会在解压目录创建带应用图标的 `RadioManager.lnk`。可将快捷方式复制到桌面；移动解压目录后，删除旧快捷方式并重新运行启动器生成。也可在包根目录手动运行 `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\create-shortcut.ps1`。GitHub 上已有的发布包不会自动更新，需要重新构建发布。

`build-win64-web.sh`、`build-win64-desktop.sh`、`build_release.sh` 使用相同项目版本，但包内容与启动方式仍有差异。

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

Electron 优先加载 `dist/index.html`，没有构建目录时加载本地 5173。打包配置只包含前端与 Electron 文件，`extraResources` 为空；主进程不会启动 Python 后端。现有相对 API、WebSocket 和 History 路由依赖 HTTP 服务，Electron 只提供前端壳。

`start-windows-web.bat` 中输入的 `RADIOMANAGER_API_URL` 没有被现有客户端读取；远程使用应配置同源代理或直接访问服务器网页。

## 4. Android 浏览器与主屏幕入口

手机可通过浏览器访问服务器网页。`public/manifest.json` 和图标提供主屏幕显示信息。

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

`android:sync` 和 `android:build` 会把 `resources/android/` 中各密度的启动图标、圆形图标和自适应图标复制到 Android 工程。单独更新已有工程中的图标可运行 `npm run android:icons`。

## 6. 网络配置

Capacitor 配置使用 `webDir=dist`、HTTPS scheme，并关闭明文流量。页面仍使用同源 `/api/v1` 和 `/health`；允许导航的主机不指定 API 后端，容器需配置网页服务器或适配请求地址。

## 7. 应用图标

图标源文件为 [`frontend/public/icon.svg`](../frontend/public/icon.svg)，采用短波电台面板与通联日志卡片。网页标签、登录与注册页、应用顶栏共用该设计；Electron 打包配置指定 Windows ICO、macOS ICNS 和 Linux PNG，pywebview 使用发布包中的 `favicon.ico`。

图标修改后，在安装了 ImageMagick 7 和 Pillow 的 Python 工具环境中，从仓库根目录运行：

```bash
python scripts/generate-icons.py
```

脚本重新生成网页 PNG、多尺寸 ICO、ICNS、maskable 图标和 `frontend/resources/android/` 下的位图；之后重新构建前端。资源已提交到仓库，普通构建不需要安装图像处理工具。Android 自适应图标 XML 与背景色定义也保存在 `frontend/resources/android/` 中。

## 8. CI 候选包

GitHub Actions 的 **Manual target validation** 仅手动运行，一次选择一个目标：`windows-web` 调用 `build-win64-web.sh`，`windows-desktop` 调用 `build-win64-desktop.sh`，`macos` 调用 `build_release.sh mac`。它们都只使用 SQLite，不要求本机或 runner 安装 MySQL 服务。其他打包入口仍单独维护。

Windows 在 Linux runner 解析目标平台 wheels、打包，再在 Windows runner 使用嵌入式 Python 验证；桌面依赖中的纯 Python `proxy_tools` 单独构建并只接受通用 wheel，其他依赖不得混入构建机的原生 wheel。下载失败会传播为构建失败。macOS 包的首次安装需求仍保留，只在临时解压副本中创建虚拟环境和数据库。

产物可从对应运行的 Artifacts 下载，保留 7 天。Windows 构建候选标记为 `unverified`；随后 `runtime-*` 报告包含原始包的 SHA-256、提交、版本、验证系统/架构及后端结果。桌面 GUI/WebView2 和 macOS 独立 `.app` 需要人工验收。完整触发规则见[GitHub Actions](12_测试设计与验收.md#github-actions)。

## 已知限制 / TODO

- Electron 和 Android 包只包含前端，Python 后端需另行部署。
- Windows 桌面窗口、WebView2 和 macOS 独立 `.app` 需要人工验收。
- 网页和 Android 容器不支持离线运行。

