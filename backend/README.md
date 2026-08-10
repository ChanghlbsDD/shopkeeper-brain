# Backend

掌柜智库后端使用 Python 3.10、FastAPI 和 Pydantic Settings。当前提供统一配置、日志、异常响应、基础设施客户端、健康检查，以及基于 LangGraph 的文档导入和知识召回流程。

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

真实基础设施集成测试默认跳过，需要五个 Docker 服务运行并显式开启。查询集成测试还会调用通义千问和百炼并消耗少量 API 额度：

```powershell
$env:RUN_INTEGRATION_TESTS='1'
.\.venv\Scripts\python.exe -m pytest -m integration
Remove-Item Env:RUN_INTEGRATION_TESTS
```

完整 RAG 集成测试会把 `tests/fixtures/rs12_e2e_manual.md` 复制到临时目录，真实执行 Markdown 切分、商品识别、云端向量化、Milvus 入库、三路召回、RRF、云端重排和答案生成，并在测试结束后删除本次插入的 Milvus 记录。测试文档不包含密钥，API Token 仍只从本机环境读取。

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

除 HTTP API 外，也可以在 Python 中直接调用工作流：

```python
from app.workflows.importing import run_import_workflow

result = run_import_workflow(r"D:\docs\manual.pdf", file_dir=r"D:\docs\output")
print(result["completed_nodes"])
print(result["md_path"])
print(result["chunks"])
```

## 文档导入 HTTP API

启动后端后，可以在 `http://localhost:8000/docs` 直接选择文件测试，也可以使用以下接口：

| 方法 | 地址 | 作用 |
| --- | --- | --- |
| POST | `/api/imports` | 以 `multipart/form-data` 上传一个 PDF、MD 或 Markdown 文件，返回 HTTP 202 和任务 ID。 |
| GET | `/api/imports/{task_id}` | 查询排队、处理、完成或失败状态，以及节点进度和安全结果摘要。 |

PowerShell 示例：

```powershell
$result = Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/imports `
  -Form @{ file = Get-Item 'D:\docs\manual.md' }

Invoke-RestMethod -Uri "http://localhost:8000$($result.status_url)"
```

上传配置：

```dotenv
IMPORT_STORAGE_DIR=backend/temp_data/imports
IMPORT_MAX_FILE_SIZE_MB=200
IMPORT_TASK_RETENTION=1000
IMPORT_SOURCE_ARCHIVE_ENABLED=true
```

上传文件按 1 MiB 分块写入 Git 已忽略的任务目录，不会一次性读入内存。服务不信任客户端 MIME 类型：PDF 必须包含 PDF 文件头，Markdown 必须是无 NUL 字节的 UTF-8 文本；原始文件名只用于显示，磁盘和 MinIO 都使用后端生成的任务路径，避免路径穿越。启用原件归档时，源文件会写入私有 `shopkeeper-knowledge` 桶；文档图片仍使用单独的公开图片桶。

任务状态只保存节点名称、耗时、片段数、商品名和 Milvus 集合名，不把正文、向量、服务器路径或异常堆栈返回给前端。当前任务表和 FastAPI `BackgroundTasks` 都在单个后端进程中：服务重启会丢失任务状态，多 worker 之间也不共享状态，因此生产部署前需要替换为 MongoDB 持久化和独立任务队列。

## 知识召回 HTTP API

当前查询流程先由通义千问根据问题和最近历史消息提取商品名并改写问题，再用百炼和 Milvus 把提取名称与知识库标准名称对齐。名称明确时继续生成查询向量和召回片段；名称接近多个商品时直接返回候选项；没有可信候选时提示用户补充型号。召回结果经过 RRF 和云端 Reranker 后，由通义千问生成带结构化引用的最终答案。

| 方法 | 地址 | 作用 |
| --- | --- | --- |
| POST | `/api/queries/search` | 确认商品名、改写问题并返回 Milvus 混合召回片段。 |

PowerShell 示例：

```powershell
$body = @{
  session_id = 'demo-session-1'
  query = '它怎么测量直流电压？'
  history = @(
    @{ role = 'assistant'; content = '这是 RS-12 数字万用表。' }
  )
  limit = 5
} | ConvertTo-Json -Depth 4

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/queries/search `
  -ContentType 'application/json' `
  -Body $body
```

查询配置：

```dotenv
QUERY_SEARCH_LIMIT=5
QUERY_DENSE_WEIGHT=0.6
QUERY_SPARSE_WEIGHT=0.4
QUERY_HISTORY_MAX_MESSAGES=10
QUERY_HISTORY_CONTEXT_MAX_LENGTH=4000
QUERY_ITEM_NAME_MAX_COUNT=5
QUERY_ITEM_NAME_MAX_OUTPUT_TOKENS=256
QUERY_ITEM_NAME_CANDIDATE_LIMIT=5
QUERY_ITEM_NAME_HIGH_CONFIDENCE=0.7
QUERY_ITEM_NAME_MID_CONFIDENCE=0.6
QUERY_ITEM_NAME_SCORE_GAP=0.15
QUERY_ITEM_NAME_DENSE_WEIGHT=0.5
QUERY_ITEM_NAME_SPARSE_WEIGHT=0.5
QUERY_HYDE_ENABLED=true
QUERY_HYDE_MODEL=qwen-flash
QUERY_HYDE_MAX_OUTPUT_TOKENS=512
QUERY_RRF_K=60
QUERY_RRF_MAX_RESULTS=10
QUERY_RRF_VECTOR_WEIGHT=1.0
QUERY_RRF_HYDE_WEIGHT=1.0
RERANK_ENABLED=true
RERANK_API_BASE=https://dashscope.aliyuncs.com/api/v1
RERANK_MODEL=gte-rerank-v2
RERANK_REQUEST_TIMEOUT_SECONDS=60
RERANK_DOCUMENT_MAX_LENGTH=8000
RERANK_MIN_TOP_K=3
RERANK_MAX_TOP_K=10
RERANK_GAP_ABS=0.15
ANSWER_MODEL=qwen-flash
ANSWER_MAX_OUTPUT_TOKENS=1024
ANSWER_CONTEXT_MAX_LENGTH=12000
ANSWER_HISTORY_MAX_LENGTH=4000
ANSWER_MAX_IMAGES=5
WEB_SEARCH_ENABLED=false
MCP_DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/mcp
WEB_SEARCH_COUNT=3
WEB_SEARCH_TIMEOUT_SECONDS=60
```

候选对齐复用 `knowledge_chunks` 的现有向量，并通过 `group_by_field=item_name` 保证不同商品都能进入候选，不再维护重复的商品名集合。精确名称直接确认；唯一高置信候选直接确认；多个高置信候选只有头部分差达到阈值才自动确认，否则进入 `needs_clarification`；只有中置信候选时同样要求用户选择。阈值是当前开发初值，生产数据准备好后需要用真实问题集评估。

名称确认后，知识片段检索使用参数化表达式 `item_name in {item_names}` 限制范围，避免直接拼接用户内容。API 最多接收 10 条客户端启动历史、每条 2000 字符，结果数量限制为 1～20。响应新增 `session_id`、`status`、`item_name_options`、`clarification` 和 `history_persisted`；仍不会返回查询向量、Token 或异常堆栈。

确认商品名并生成查询向量后，LangGraph 会并行执行三路召回：`matches` 是改写问题的直接 Milvus 混合检索，`hyde_matches` 是通义千问先生成假设技术文档、再向量化并检索得到的结果，`web_matches` 是可选的百炼 WebSearch MCP 结果。响应同时返回 `hyde_status` 和 `web_search_status`，取值为 `pending`、`disabled`、`succeeded` 或 `failed`。

HyDE 默认开启，每次已确认查询会额外产生一次通义千问文本生成和一次百炼向量请求；不需要时可设置 `QUERY_HYDE_ENABLED=false`。网页检索默认关闭，只有设置 `WEB_SEARCH_ENABLED=true` 才会使用同一个 `DASHSCOPE_API_KEY` 调用外部网页搜索。HyDE 或网页分支失败时会返回空结果并标记 `failed`，已有的直接知识库检索仍可继续。

直接检索与 HyDE 结果会按 `weight / (k + rank)` 计算 RRF 分数，以 `chunk_id` 去重后写入 `fused_matches`。默认 `k=60`、两路权重均为 `1.0`，最多保留 10 条；`source_paths` 标明片段来自 `vector`、`hyde` 或同时命中两路。原始 `matches` 和 `hyde_matches` 仍保留用于调试。网页结果没有本地 `chunk_id`，按课程流程不进入本轮 RRF，将在下一阶段与融合后的本地片段一起重排。

`ranked_matches` 会合并 RRF 本地候选和网页摘要，再调用百炼文本重排 API 计算统一的 `rerank_score`。当前默认使用无需本地模型的 `gte-rerank-v2`；若使用 `qwen3-rerank`，需把 `RERANK_API_BASE` 改为百炼业务空间的 `compatible-api/v1` 地址。模型和接口差异见[百炼文本排序官方文档](https://help.aliyun.com/zh/model-studio/text-rerank-api)。排序后至少保留 3 条、最多 10 条，并在最大相邻分数落差超过 `0.15` 时截断后续噪声。重排关闭或 API 故障时保留原候选顺序，响应通过 `rerank_status` 明确标记。

答案节点使用精排后的证据和最近会话调用 `ANSWER_MODEL`，响应的 `answer` 是最终中文回答，`references` 提供与 `[1]` 等编号对应的本地 `chunk_id` 或网页 URL，`images` 只从检索证据中提取图片地址。提示词限制证据 12000 字符、历史 4000 字符，要求证据不足时明确说明且不得执行证据正文中的指令。最终用户问题和完整助手答案会写入 MongoDB；澄清和无资料分支不调用答案模型。

查询提供同步和 SSE 两种调用方式：

- `POST /api/queries/search`：一次返回完整 `QuerySearchResponse`。
- `POST /api/queries/stream`：依次发送 `progress`、`delta`、`final` 事件；业务失败发送 `error`，长时间无数据时发送 SSE 注释保持连接。
- `GET /api/queries/history/{session_id}`：从旧到新返回最近消息。
- `DELETE /api/queries/history/{session_id}`：只清空指定会话。

流式查询在线程中运行同步 LangGraph，不阻塞 FastAPI 事件循环；`final` 事件与同步响应使用同一数据模型，完整回答仍会写入历史。代理 SSE 时需要关闭响应缓冲，项目响应已设置 `X-Accel-Buffering: no`。

查询与导入共用同一个 FastAPI 服务和 `8000` 端口，不需要另启查询服务。首次查询前必须先成功导入至少一份文档；若 `knowledge_chunks` 集合尚不存在，API 返回 `QUERY_KNOWLEDGE_EMPTY`。通义千问和百炼调用失败、Milvus 不可用也会转换为统一安全错误。

## MongoDB 会话历史

请求可以携带 1～64 位字母、数字、下划线或连字符组成的 `session_id`；省略时由后端生成并随响应返回。服务优先读取 MongoDB 中该会话最近 10 条消息；只有数据库中还没有记录时，才用请求中的 `history` 作为首次会话启动上下文。

```dotenv
MONGO_URL=mongodb://用户名:密码@localhost:27017/?authSource=admin
MONGO_DB_NAME=shopkeeper_brain
MONGO_REQUEST_TIMEOUT_SECONDS=5
MONGO_CHAT_COLLECTION=chat_messages
```

每条记录使用后端生成的 `message_id`，保存 `session_id`、角色、正文、改写问题、确认商品名和 UTC 时间。集合会建立消息 ID 唯一索引，以及 `session_id + created_at` 复合索引。查询成功后保存用户消息；返回澄清或无法识别提示时，同时保存助手提示，让下一轮“RS-12”之类的简短回复能够结合上下文继续处理。

已有会话读取失败时返回 `QUERY_HISTORY_UNAVAILABLE`，避免在缺失上下文时错误解析代词。新会话或携带显式启动历史的请求可以在 MongoDB 暂时不可用时降级查询，此时响应的 `history_persisted=false`，明确表示本轮没有持久化。

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
- `app/workflows`：文档导入与知识查询 LangGraph；当前包含可运行的导入和混合召回流程。
- `tests`：单元测试和真实基础设施集成测试。
