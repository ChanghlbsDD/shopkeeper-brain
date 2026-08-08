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

入口节点会真实检查文件是否存在、识别扩展名并选择分支；PDF 分支会调用 MinerU 云端 API 并写入下载后的 Markdown 路径。图片处理、文档切分、商品名识别、向量化和 Milvus 写入节点目前仍只记录执行顺序，后续步骤会逐个替换为真实业务。

工作流暂未暴露为 HTTP API，可在 Python 中直接验证：

```python
from app.workflows.importing import run_import_workflow

result = run_import_workflow(r"D:\docs\manual.pdf", file_dir=r"D:\docs\output")
print(result["completed_nodes"])
print(result["md_path"])
```

## 目录职责

- `app/api`：HTTP 与 SSE 接口。
- `app/clients`：MinIO、Milvus、MongoDB 与后续 AI 模型客户端。
- `app/core`：配置、日志和统一异常。
- `app/schemas`：请求与响应模型。
- `app/services`：后续导入、查询和历史记录业务编排。
- `app/workflows`：文档导入与后续问答查询 LangGraph；当前包含可运行的导入流程骨架。
- `tests`：单元测试和真实基础设施集成测试。
