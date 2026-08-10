# Frontend

掌柜智库前端使用 Vue 3、TypeScript 和 Vite，已经替换课程中的静态 `import.html` 与 `chat.html`。

## 安装与启动

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

开发服务器默认运行在 `http://localhost:5173`，并把 `/api` 代理到 `http://127.0.0.1:8000`。请先启动 FastAPI 后端。

## 检查

```powershell
npm.cmd run type-check
npm.cmd run test
npm.cmd run build
```

## 文档导入页面

当前页面支持：

- 点击选择或拖放多个 PDF、MD、Markdown 文件。
- 在上传前检查扩展名、空文件和 200 MB 上限。
- 调用 `POST /api/imports`，每 1.5 秒轮询 `GET /api/imports/{task_id}`。
- 按 PDF/Markdown 分支展示节点时间线、进度、耗时、结果和安全错误。
- 状态查询短暂断线时自动重试，连续失败 5 次后停止轮询并提示重新导入。

## 知识问答页面

从顶部导航进入“知识问答”，页面支持：

- 使用 `POST /api/queries/stream` 接收节点进度、通义千问增量文本和最终结果。
- 关闭“流式显示回答”后改用 `POST /api/queries/search` 同步返回。
- 展示本地知识片段或网页来源、证据图片和商品名澄清选项。
- 在浏览器保存不含密钥的会话 ID，刷新后通过 MongoDB 恢复历史。
- 经用户确认后清空当前会话；随后自动生成新会话 ID，不影响其他会话。

流式接口使用 `fetch + ReadableStream`，可正确处理一个 JSON 事件被拆到多个网络数据块的情况。前端不会读取或保存百炼、MinerU 等服务的 Token。

生产环境如果前后端不是同域，可在前端构建环境中配置：

```dotenv
VITE_API_BASE_URL=https://api.example.com
```

不要把密钥放入 `VITE_*` 环境变量；Vite 会把这些值公开到浏览器代码中。
