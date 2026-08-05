# 掌柜智库

掌柜智库是一个面向企业文档的 RAG（检索增强生成）知识库项目。项目将 PDF 或 Markdown 文档处理为可检索知识，并通过混合向量检索、多路召回、结果融合、重排序和流式回答提供知识问答能力。

本仓库依据课程笔记按功能链路逐步重建。后端使用 Python、FastAPI 和 LangGraph；原课程的静态 HTML 前端将替换为 Vue 3。

## 当前进度

- [x] 第 1 步：初始化仓库和工程规范
- [ ] 第 2 步：搭建 etcd、MinIO、Milvus、Attu、MongoDB
- [ ] 后续：按 `docs/development-log.md` 持续记录

## 规划目录

```text
.
├── backend/       # FastAPI 后端及 RAG 工作流
├── frontend/      # Vue 3 前端
├── deploy/        # Docker Compose 与部署配置
├── docs/          # 开发笔记和项目文档
├── .env.example   # 环境变量模板，不包含真实密钥
└── README.md
```

各子目录将在对应开发步骤中逐步加入可运行代码。目前目录内的 README 用于约定职责，避免尚未实现的占位代码被误认为可运行功能。

## 安全约定

- 不提交 `.env`、API Key、访问密钥或私有连接串。
- 不提交虚拟环境、依赖缓存、模型权重及容器数据卷。
- 不提交用户上传文档、MinerU 中间产物或向量数据库数据。
- 所有可公开配置写入 `.env.example`，真实值只保存在本机 `.env`。

## 开发环境基线

课程建议 Python 3.10。当前机器默认 Python 为 3.13.9，因此在后端依赖安装阶段会先准备独立的 Python 3.10 环境，以降低 MinerU、PyTorch 和 BGE 相关依赖的兼容风险。

完整的逐步变更记录见 [`docs/development-log.md`](docs/development-log.md)。

## 许可证

本项目沿用参考项目的 Apache License 2.0，详见 [`LICENSE`](LICENSE)。发布衍生代码时将保留许可证与必要的来源说明。
