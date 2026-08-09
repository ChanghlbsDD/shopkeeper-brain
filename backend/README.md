# Backend

掌柜智库后端使用 Python 3.10、FastAPI 和 Pydantic Settings。当前提供统一配置、日志、异常响应、基础设施客户端、健康检查，以及基于 LangGraph 的文档导入流程。

## 创建虚拟环境

本项目要求 Python 3.10，不要使用系统默认的其他 Python 版本：

```powershell
cd backend
& "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe" -m venv .venv
```

后续命令始终显式使用虚拟环境解释器，无需修改 PowerShell 执行策略：

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

## 启动

先在仓库根目录准备 `.env` 并启动基础设施，然后执行：

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

可访问：

- 应用信息：`http://localhost:8000/`
- 健康检查：`http://localhost:8000/api/health`
- Swagger：`http://localhost:8000/docs`
- ReDoc：`http://localhost:8000/redoc`

## 测试与检查

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check app tests
```

真实基础设施集成测试默认跳过，需要五个 Docker 服务运行并显式开启：

```powershell
$env:RUN_INTEGRATION_TESTS='1'
.\.venv\Scripts\python.exe -m pytest -m integration
Remove-Item Env:RUN_INTEGRATION_TESTS
```

## PDF 转 Markdown

项目通过 MinerU 精准解析云端 API 把 PDF 转为 Markdown，不在本机或业务服务器安装 MinerU、PyTorch 和解析模型。先在 [MinerU API 管理页面](https://mineru.net/apiManage/token)创建 Token，再把 Token 写入仓库根目录的本机 `.env`：

```dotenv
MINERU_API_TOKEN=只填写在本机
MINERU_BASE_URL=https://mineru.net/api/v4
MINERU_MODEL_VERSION=vlm
MINERU_REQUEST_TIMEOUT_SECONDS=120
MINERU_POLL_INTERVAL_SECONDS=2
MINERU_TASK_TIMEOUT_SECONDS=1800
```

节点会依次申请签名上传地址、上传 PDF、轮询任务、下载完整 ZIP，并把 Markdown、JSON 和图片安全解压到指定输出目录。API Token 不得写入 `.env.example` 或提交到 Git。

使用云端 API 表示 PDF 会上传给 MinerU 服务。当前精准解析接口对单文件限制为不超过 200 MB、200 页，并受账号额度约束；具体规则以 [MinerU 官方 API 文档](https://mineru.net/apiManage/docs)为准。

## 文档导入工作流

入口节点会真实检查文件是否存在、识别扩展名并选择分支；PDF 分支会调用 MinerU 云端 API 并写入下载后的 Markdown 路径；图片节点会把 Markdown 实际引用的本地图片上传至 MinIO，并把本地路径替换为对象地址；切分节点会根据 Markdown 标题层级生成知识片段；商品名节点会调用通义千问识别核心商品或设备名称并回填所有片段；向量化节点会调用百炼云端 API 生成稠密和稀疏向量；最后由 Milvus 节点创建或校验集合及索引，批量写入知识片段并回填自动主键。当前七个导入节点均已实现真实业务。

工作流暂未暴露为 HTTP API，可在 Python 中直接验证：

```python
from app.workflows.importing import run_import_workflow

result = run_import_workflow(r"D:\docs\manual.pdf", file_dir=r"D:\docs\output")
print(result["completed_nodes"])
print(result["md_path"])
print(result["chunks"])
```

## Markdown 图片处理

图片节点使用独立的 `shopkeeper-images` 桶，不会把原始 PDF 或其他私有对象所在的知识桶设为公开。开发环境配置为：

```dotenv
MINIO_IMAGE_BUCKET_NAME=shopkeeper-images
MINIO_PUBLIC_BASE_URL=http://localhost:9000
MINIO_IMAGE_PUBLIC_READ=true
```

处理含本地图片的 Markdown 前需要启动 MinIO。节点只上传 Markdown 实际引用且位于 Markdown 目录内的 JPG、JPEG、PNG、GIF、WebP 或 BMP 文件；远程图片保持不变，重复引用只上传一次。处理结果保存为同目录下的 `*_images.md`，原文件保持不变。

图片桶默认允许匿名读取，以便浏览器和后续问答结果直接展示图片，因此不要上传包含敏感信息的图片。部署到服务器时，`MINIO_PUBLIC_BASE_URL` 必须改成浏览器能够访问的 HTTPS 域名或反向代理地址，不能填写仅容器内部可见的 `minio:9000`。

## Markdown 文档切分

切分节点使用以下配置，单位是字符数：

```dotenv
DOCUMENT_CHUNK_MAX_LENGTH=1000
DOCUMENT_CHUNK_MIN_LENGTH=200
DOCUMENT_CHUNK_BACKUP_ENABLED=true
```

处理顺序如下：

1. 按 Markdown 1～6 级标题建立章节，并保留父标题关系。
2. 忽略代码围栏内部看起来像标题的 `#` 行。
3. 把 Markdown 或 HTML 表格转换为保留行列关系的自然语言。
4. 超过最大长度的章节按段落、换行和中英文句末标点递归切分。
5. 仅在父标题相同且合并后不超过最大长度时合并短片段。

最终结果写入状态中的 `chunks`，每个片段包含 `title`、`parent_title`、`file_title` 和 `content`，超长章节还带有 `part` 序号。默认同时在 Markdown 旁生成 `*_chunks.json` 方便检查，该运行产物已被 Git 忽略；生产环境如不需要备份，可把 `DOCUMENT_CHUNK_BACKUP_ENABLED` 设为 `false`。

文档切分是本地纯文本处理，不会调用 MinerU、通义千问、MinIO 或其他网络服务。

## 通义千问商品名识别

项目使用通义千问的 OpenAI 兼容 Chat Completions 接口和 JSON mode，不额外安装 OpenAI SDK 或 LangChain 模型客户端。开发环境配置为：

```dotenv
OPENAI_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_API_KEY=只填写在本机
ITEM_MODEL=qwen-flash
LLM_DEFAULT_TEMPERATURE=0
QWEN_REQUEST_TIMEOUT_SECONDS=60
ITEM_NAME_MAX_OUTPUT_TOKENS=128
ITEM_NAME_CHUNK_COUNT=3
ITEM_NAME_CONTEXT_MAX_LENGTH=2500
ITEM_NAME_BACKUP_ENABLED=true
```

节点最多选取前 3 个 chunk，并把上下文严格限制在 2500 字符以内。模型返回的 `item_name` 会写入工作流状态和每个 chunk，同时通过 `item_name_source` 标记来源是 `qwen` 还是 `file_title_fallback`。只有模型明确返回 `UNKNOWN` 时才使用文件名降级；密钥缺失、HTTP 错误或 JSON 格式错误会终止节点，避免把错误结果当成真实商品名。

默认会在 Markdown 旁生成 `*_item_name_chunks.json` 供开发检查，该文件已被 Git 忽略。商品名识别会把文档标题和少量正文发送到阿里云百炼；处理敏感文档前需要确认数据合规要求。不同地域的 API 地址可能不同，部署时应按[阿里云百炼官方文档](https://help.aliyun.com/zh/model-studio/qwen-structured-output)调整 `OPENAI_API_BASE`。

## 百炼云端混合向量

课程原版使用本地 BGE-M3 生成稠密和稀疏向量。考虑到目标服务器只有 2 核、2 GiB 内存，本项目改用百炼 `text-embedding-v4` 原生 HTTP 接口，同时请求 `dense&sparse`，不下载或加载本地向量模型。

```dotenv
DASHSCOPE_API_BASE=https://dashscope.aliyuncs.com/api/v1
DASHSCOPE_API_KEY=只填写在本机
EMBEDDING_MODEL=text-embedding-v4
EMBEDDING_DIMENSION=1024
EMBEDDING_BATCH_SIZE=10
EMBEDDING_REQUEST_TIMEOUT_SECONDS=60
EMBEDDING_BACKUP_ENABLED=true
```

节点保留课程中的名称 `bge_embedding_node`，但该名称只用于流程对应关系。它把每个 chunk 组装成“商品名称 + 正文”，按最多 10 条一批发送，并显式使用底库文本类型 `document`。返回结果会写入每个 chunk 的 `dense_vector` 和 `sparse_vector`，同时把稠密向量列表写入 `state.embeddings`。

默认会在 Markdown 旁生成 `*_vectors.json` 供开发检查，该文件和本地 Python 运行时目录均已被 Git 忽略。API Key 缺失、HTTP 失败、数量不一致、1024 维校验失败或稀疏向量缺失都会终止节点，防止不完整向量进入 Milvus。

同一份知识库在入库和查询时必须使用相同模型及维度；后续查询节点会用 `query` 类型生成查询向量。向量化会把商品名称和全部切片正文发送给阿里云百炼，处理敏感文档前需要确认数据合规要求。接口限制和可选维度以[百炼同步向量接口文档](https://help.aliyun.com/zh/model-studio/text-embedding-synchronous-api)为准。

## Milvus 混合向量入库

入库节点使用以下配置：

```dotenv
CHUNKS_COLLECTION=knowledge_chunks
MILVUS_METRIC_TYPE=COSINE
MILVUS_INSERT_BATCH_SIZE=100
MILVUS_REQUEST_TIMEOUT_SECONDS=10
MILVUS_BACKUP_ENABLED=true
```

首次运行会创建显式 schema：`chunk_id` 是 Milvus 自动生成的 INT64 主键，`dense_vector` 是固定维度稠密向量，`sparse_vector` 是稀疏向量；正文、标题、父标题、文件标题和商品名称使用 VARCHAR，分片序号 `part` 是可空整数。稠密向量建立 `AUTOINDEX + COSINE` 索引，稀疏向量建立 `SPARSE_INVERTED_INDEX + IP` 索引。

集合已存在时不会盲目重建，而会先检查自动主键、字段类型、稠密维度和索引配置。任一 chunk 缺少正文、商品名或两种向量，向量含非有限数值、各片段维度不一致，或已有集合结构不兼容时，导入会明确失败，不会跳过错误数据继续写入。

数据按 `MILVUS_INSERT_BATCH_SIZE` 分批写入；后续批次失败时会尽力删除本次已经成功写入的前置批次。成功后，Milvus 返回的主键会同时写入每个 chunk 的 `chunk_id` 和状态的 `milvus_ids`。默认还会生成 Git 已忽略的 `*_milvus_chunks.json` 调试备份。

重复运行同一文档会生成新的记录，当前尚未实现按文件去重或覆盖。集合 schema 与索引的设计分别参考 [Milvus Schema](https://milvus.io/docs/v2.6.x/schema.md) 和 [稀疏向量索引](https://milvus.io/docs/v2.6.x/sparse-inverted-index.md)。

## 目录职责

- `app/api`：HTTP 与 SSE 接口。
- `app/clients`：MinIO、Milvus、MongoDB 与后续 AI 模型客户端。
- `app/core`：配置、日志和统一异常。
- `app/schemas`：请求与响应模型。
- `app/services`：后续导入、查询和历史记录业务编排。
- `app/workflows`：文档导入与后续问答查询 LangGraph；当前包含可运行的导入流程骨架。
- `tests`：单元测试和真实基础设施集成测试。
