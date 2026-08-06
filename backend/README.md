# Backend

掌柜智库后端使用 Python 3.10、FastAPI 和 Pydantic Settings。当前骨架提供统一配置、日志、异常响应、基础设施客户端及健康检查。

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

## 文档导入工作流骨架

当前已建立 PDF/Markdown 导入的 LangGraph 流程骨架。入口节点会真实检查文件是否存在、识别扩展名并选择分支；PDF 转 Markdown、图片处理、文档切分、商品名识别、向量化和 Milvus 写入节点目前只记录执行顺序，后续步骤会逐个替换为真实业务。

工作流暂未暴露为 HTTP API，可在 Python 中直接验证：

```python
from app.workflows.importing import run_import_workflow

result = run_import_workflow(r"D:\docs\manual.md")
print(result["completed_nodes"])
```

## 目录职责

- `app/api`：HTTP 与 SSE 接口。
- `app/clients`：MinIO、Milvus、MongoDB 与后续 AI 模型客户端。
- `app/core`：配置、日志和统一异常。
- `app/schemas`：请求与响应模型。
- `app/services`：后续导入、查询和历史记录业务编排。
- `app/workflows`：文档导入与后续问答查询 LangGraph；当前包含可运行的导入流程骨架。
- `tests`：单元测试和真实基础设施集成测试。
