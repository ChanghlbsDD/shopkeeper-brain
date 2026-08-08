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

入口节点会真实检查文件是否存在、识别扩展名并选择分支；PDF 分支会调用 MinerU 云端 API 并写入下载后的 Markdown 路径；图片节点会把 Markdown 实际引用的本地图片上传至 MinIO，并把本地路径替换为对象地址；切分节点会根据 Markdown 标题层级生成知识片段；商品名节点会调用通义千问识别核心商品或设备名称并回填所有片段。向量化和 Milvus 写入节点目前仍只记录执行顺序，后续步骤会逐个替换为真实业务。

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

## 目录职责

- `app/api`：HTTP 与 SSE 接口。
- `app/clients`：MinIO、Milvus、MongoDB 与后续 AI 模型客户端。
- `app/core`：配置、日志和统一异常。
- `app/schemas`：请求与响应模型。
- `app/services`：后续导入、查询和历史记录业务编排。
- `app/workflows`：文档导入与后续问答查询 LangGraph；当前包含可运行的导入流程骨架。
- `tests`：单元测试和真实基础设施集成测试。
