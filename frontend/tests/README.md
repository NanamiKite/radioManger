# 浏览器测试

浏览器测试覆盖登录、日志导入导出、设置和实时连接。用例通过真实页面操作，HTTP/WebSocket 响应在网络边界固定，便于稳定复现成功和失败分支。

## 运行

从仓库根目录安装：

```bash
npm --prefix frontend ci
npm --prefix frontend/tests ci
cd frontend/tests
npx playwright install chromium
npm test -- --workers=2
```

Playwright 启动现有 Vite 服务在 `127.0.0.1:5179`，端口占用时会报错。测试依赖独立安装，不进入应用运行时依赖。

## 用例

- `specs/auth-realtime.spec.ts`：401、退出失败、模式/角色权限、首消息认证和 4401。
- `specs/log-workflows.spec.ts`：导入拒绝与部分提交、导出等待/失败/下载、校验错误、查询 URL 和旧响应隔离。
- `specs/settings.spec.ts`：偏好保存失败、UDP 端口传参与边界拒绝。

## 报告

`playwright-report/` 是 HTML 报告，`test-results/` 保存失败截图、视频和 trace，均不提交。运行 `npm run test:report` 打开报告。
