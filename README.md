# 掌柜智库

掌柜智库是一个面向企业文档的 RAG（检索增强生成）知识库项目。项目将 PDF 或 Markdown 文档处理为可检索知识，并通过混合向量检索、多路召回、结果融合、重排序和流式回答提供知识问答能力。

本仓库依据课程笔记按功能链路逐步重建。后端使用 Python、FastAPI 和 LangGraph；原课程的静态 HTML 前端已替换为 Vue 3。目前已经完成文档入库、混合召回、云端精排、带引用回答和会话历史的完整开发链路。

## 项目结构

```text
.
├── backend/       # FastAPI 后端及 RAG 工作流
├── frontend/      # Vue 3 前端
├── deploy/        # Docker Compose 与部署配置
├── docs/          # 开发笔记和项目文档
├── .env.example   # 环境变量模板，不包含真实密钥
└── README.md
```

## 安全约定

- 不提交 `.env`、API Key、访问密钥或私有连接串。
- 不提交虚拟环境、依赖缓存、模型权重及容器数据卷。
- 不提交用户上传文档、MinerU 中间产物或向量数据库数据。
- 所有可公开配置写入 `.env.example`，真实值只保存在本机 `.env`。

## 本地基础设施

复制环境变量模板并启动五个基础设施容器：

```powershell
Copy-Item .env.example .env
docker compose --env-file .env -f deploy/docker-compose.yml up -d
docker compose --env-file .env -f deploy/docker-compose.yml ps
```

默认仅允许本机访问：

- Attu：`http://localhost:7000`
- MinIO 控制台：`http://localhost:9001`
- Milvus gRPC：`localhost:19530`
- Milvus WebUI/健康端口：`http://localhost:9091`
- MongoDB：`localhost:27017`

第一次启动前应修改 `.env` 中带有 `change-me` 的本地开发密码。

## 后端开发

后端要求 Python 3.10，并使用独立的 `backend/.venv`：

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

启动后可访问：

- 健康检查：`http://localhost:8000/api/health`
- 文档导入：`POST http://localhost:8000/api/imports`
- 知识召回：`POST http://localhost:8000/api/queries/search`
- 流式知识问答：`POST http://localhost:8000/api/queries/stream`
- 会话历史：`GET/DELETE http://localhost:8000/api/queries/history/{session_id}`
- Swagger API 文档：`http://localhost:8000/docs`

首次创建虚拟环境、测试和代码检查命令见 [`backend/README.md`](backend/README.md)。

## 前端开发

文档导入与知识问答页面使用 Vue 3、TypeScript 和 Vite：

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

访问 `http://localhost:5173`，用顶部导航切换“文档导入”和“知识问答”。问答页支持 SSE 流式显示、节点进度、来源引用、证据图片、商品澄清以及 MongoDB 会话恢复和清空。开发服务器会把 `/api` 请求代理到运行在 `127.0.0.1:8000` 的 FastAPI，因此应先启动后端。前端类型检查、测试、构建和环境变量说明见 [`frontend/README.md`](frontend/README.md)。

## 开发记录

逐步还原过程、目录差异、文件职责和验证结果单独记录在 [`docs/development-log.md`](docs/development-log.md)，不与项目使用说明混写。

## 许可证

本项目沿用参考项目的 Apache License 2.0，详见 [`LICENSE`](LICENSE)。发布衍生代码时将保留许可证与必要的来源说明。
