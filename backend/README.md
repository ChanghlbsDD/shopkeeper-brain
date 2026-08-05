# Backend

该目录用于 FastAPI 服务、LangGraph 导入/查询工作流、数据模型、基础设施客户端和自动化测试。

计划中的主要边界：

- `app/api`：HTTP 与 SSE 接口。
- `app/core`：配置、日志、路径和异常。
- `app/schemas`：请求、响应及工作流状态模型。
- `app/services`：导入、查询和历史记录业务编排。
- `app/workflows`：文档导入与问答查询 LangGraph。
- `app/clients`：MinIO、Milvus、MongoDB 与 AI 模型客户端。
- `tests`：单元测试和集成测试。

实际代码和依赖将在后续步骤中加入。
