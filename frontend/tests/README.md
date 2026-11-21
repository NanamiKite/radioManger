# 浏览器契约测试

预期来自 [测试设计与验收](../../doc/12_测试设计与验收.md) 与 [前端架构设计](../../doc/05_前端架构设计.md)，不是从当前实现的输出生成。测试不修改应用源码，不重试，不将失败标记为预期失败。

从仓库根目录安装：

```bash
npm --prefix frontend ci
npm --prefix frontend/tests ci
cd frontend/tests
npx playwright install chromium
npm test -- --workers=2
```

该目录是独立测试包，只依赖固定版本的 `@playwright/test`，不向应用添加运行时依赖。Playwright 启动现有 Vite 服务在 `127.0.0.1:5179`；端口占用时不复用未知服务。

测试通过真实登录表单、菜单、上传输入、对话框和设置控件操作页面。HTTP 与 WebSocket 响应在浏览器网络边界固定，不写入 Pinia、Vue 内部状态或伪造 DOM 控件。固定失败响应验证前端如何呈现失败，不能证明真实后端已正确执行这些行为。

- `specs/auth-realtime.spec.ts`：401、退出失败、模式/角色权限、首消息认证和 4401。
- `specs/log-workflows.spec.ts`：导入拒绝与部分提交、导出等待/失败/下载、校验错误、查询 URL 和旧响应隔离。
- `specs/settings.spec.ts`：偏好保存失败、UDP 端口传参与边界拒绝。

`playwright-report/` 为 HTML 报告；`test-results/` 保存失败截图、视频及 trace，均忽略提交。运行 `npm run test:report` 打开报告。报告中的失败需要保留并定位，不修改源码或放宽断言来消除红灯。
