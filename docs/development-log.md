# 掌柜智库开发笔记

本文档按实施步骤记录实际改动、目录差异、文件职责、验证结果和后续事项。每完成一步，都会在文档末尾增加一个独立章节。

## 文档分工

- 根目录 `README.md` 面向项目使用者，只维护项目介绍、结构、运行方式和安全约定等稳定内容。
- 本开发笔记面向开发过程，记录逐步改动、本机环境、前后目录差异、文件职责、验证结果和 Git 提交。
- 开发进度与机器相关问题不再写入根目录 README。

## 开发环境硬性约定

- 开始编写任何 Python 后端代码之前，必须先创建 `backend/.venv` 独立虚拟环境。
- 目标解释器为 Python 3.10；不得使用当前系统默认的 Python 3.13.9 创建项目环境。
- 安装依赖、运行测试、执行脚本和启动 FastAPI 时，统一使用 `backend/.venv/Scripts/python.exe` 对应的解释器与模块命令。
- `.venv` 只存在于本机并由 `.gitignore` 排除，不提交到 Git 或 GitHub。
- 每一步验证记录都要注明实际使用的 Python 解释器路径与版本，防止命令意外落到系统环境。

## 第 1 步：初始化仓库和工程规范

日期：2026-08-05

### 本步目标

1. 将空工作目录初始化为 Git 仓库，默认分支使用 `main`。
2. 建立后端、前端、部署和文档四个工程边界。
3. 统一文本编码、换行符和缩进约定。
4. 建立密钥、模型、缓存、用户文档和运行数据的忽略规则。
5. 提供不含真实密钥的环境变量模板。
6. 保留参考项目的 Apache License 2.0。

### 执行前目录

工作目录为空，且不是 Git 仓库：

```text
掌柜智库/
└── （空）
```

### 执行后目录

```text
掌柜智库/
├── backend/
│   └── README.md
├── deploy/
│   └── README.md
├── docs/
│   └── development-log.md
├── frontend/
│   └── README.md
├── .editorconfig
├── .env.example
├── .gitattributes
├── .gitignore
├── LICENSE
└── README.md
```

`.git/` 由 `git init -b main` 生成，属于 Git 内部数据，因此不在上面的项目文件树中展开。

### 与上一步相比

上一步没有任何文件。本步新增 4 个职责目录和 10 个受 Git 管理的文件，形成项目最小骨架；尚未添加业务代码、依赖清单或容器配置。

### 新文件作用

| 文件 | 作用 |
| --- | --- |
| `.editorconfig` | 统一 Python、Vue、JSON、YAML 等文件的字符集、缩进和尾随空格规则。 |
| `.env.example` | 列出后续服务需要的环境变量，并提供安全的本地示例值；不包含真实密钥。 |
| `.gitattributes` | 统一跨 Windows/Linux 的换行符，并标记图片、PDF、Office 文件为二进制。 |
| `.gitignore` | 阻止密钥、虚拟环境、Node 依赖、模型、缓存、运行数据和用户文档进入 Git。 |
| `LICENSE` | 声明 Apache License 2.0，保持与课程参考项目一致的再发布条件。 |
| `README.md` | 面向使用者说明项目目标、项目结构和安全约定，不记录逐步开发流水。 |
| `backend/README.md` | 定义 FastAPI、LangGraph、客户端、服务层和测试代码的后端边界。 |
| `frontend/README.md` | 定义 Vue 3 文档导入、流式问答和会话历史页面的前端边界。 |
| `deploy/README.md` | 说明下一步 Docker Compose 管理的五个基础设施容器及数据策略。 |
| `docs/development-log.md` | 持续记录每一步做了什么、目录差异、新文件职责及验证结果。 |

### 已确定的技术约定

- Git 默认分支：`main`。
- 后端目标版本：Python 3.10 独立虚拟环境。
- 前端：Vue 3 + Vite + TypeScript。
- 本地基础设施：Docker Compose。
- 配置方式：提交 `.env.example`，本机复制为不会被提交的 `.env`。
- 默认推理设备：CPU；确认 CUDA 与 PyTorch 兼容后再启用 GPU。

### 本机工具检查

| 工具 | 检查结果 | 处理方式 |
| --- | --- | --- |
| Git | 2.51.0.windows.1 | 可用。 |
| Python | 3.13.9 | 不是项目目标版本；后端阶段安装或定位 Python 3.10。 |
| Python Launcher (`py`) | 未安装或未进入 PATH | 后续使用 Python 3.10 的明确可执行文件路径创建虚拟环境。 |
| Node.js | 22.19.0 | 可用于后续 Vue 工程。 |
| npm | 10.9.3 | `npm.ps1` 被 PowerShell 策略拦截，后续使用 `npm.cmd`。 |
| Docker | 29.3.1 | CLI 可用。 |
| Docker Compose | 5.1.1 | CLI 可用。 |

Docker CLI 检查时无法在当前受限执行环境中读取用户目录下的 Docker 配置文件。第 2 步会通过实际容器命令验证 Docker Engine，而不把这条沙箱告警直接判断为 Docker 不可用。

### 安全检查

- `.env` 和 `.env.*` 默认忽略，仅放行 `.env.example`。
- 模型目录、容器数据、上传文件和 MinerU 临时结果已加入忽略规则。
- `requirements.txt` 和 Dockerfile 不会被忽略，后续可以正常纳入版本控制。
- 环境模板中的凭据为占位值，没有复制课程 `.env` 中的真实配置。

### 验证结果

- Git 已初始化，默认分支为 `main`。
- Git 暂存区包含上述 10 个新文件。
- 忽略规则抽样验证通过：`.env`、虚拟环境、`node_modules`、模型和上传文档均被忽略。
- 可提交文件抽样验证通过：`.env.example`、`requirements.txt` 和 Dockerfile 不会被错误忽略。
- 仓库疑似密钥扫描未发现结果。
- 暂存内容通过 Git 空白字符检查。

### 下一步

第 2 步将创建并验证 etcd、MinIO、Milvus、Attu、MongoDB 的 Docker Compose 配置，并在本节之后追加新的目录差异与文件说明。

### 一句话总结

第 1 步把空目录变成了具备 Git、工程边界、安全忽略规则和独立文档分工的项目骨架。

## 第 2 步：搭建五容器基础设施

日期：2026-08-05

### 本步目标

1. 连接用户创建的 GitHub 仓库 `ChanghlbsDD/shopkeeper-brain`。
2. 使用 Docker Compose 管理 etcd、MinIO、Milvus、Attu、MongoDB。
3. 固定镜像版本、服务依赖、健康检查、网络和数据卷。
4. 让服务端口默认只监听本机回环地址。
5. 真实拉取镜像并验证五个容器能够正常运行。

### 与第 1 步的目录区别

第 1 步结束时，`deploy` 目录只有职责说明：

```text
deploy/
└── README.md
```

本步新增 Compose 文件，并更新已有配置与使用文档：

```text
掌柜智库/
├── deploy/
│   ├── README.md             # 已更新：加入版本、命令、端口和数据说明
│   └── docker-compose.yml    # 新增：五容器可执行配置
├── docs/
│   └── development-log.md    # 已更新：增加第 2 步记录
├── .env.example              # 已更新：增加容器端口及认证配置
└── README.md                 # 已更新：增加稳定的基础设施启动说明
```

后端和前端目录没有新增业务代码。`.git/` 中增加了 GitHub `origin` 地址，但 Git 内部目录不在项目树中展开。

### 新文件作用

| 文件 | 作用 |
| --- | --- |
| `deploy/docker-compose.yml` | 定义五个服务、固定镜像、健康检查、依赖顺序、本地端口、专用网络和命名卷，是本步唯一新增的项目文件。 |

### 修改文件作用

| 文件 | 本步改动 |
| --- | --- |
| `.env.example` | 增加 MinIO、Milvus、Attu、MongoDB 的端口和本地开发认证变量，并保证后端与 Milvus 使用相同 MinIO 凭据。 |
| `deploy/README.md` | 将占位说明扩展为完整的启动、查看、停止、端口和持久化操作手册。 |
| `README.md` | 增加面向使用者的基础设施快速启动方式；没有写入开发流水。 |
| `docs/development-log.md` | 记录本步实际操作、前后差异、新文件职责和验证结果。 |

### 版本选择

| 服务 | 镜像版本 | 选择依据 |
| --- | --- | --- |
| etcd | `quay.io/coreos/etcd:v3.5.25` | 参考 Milvus 2.6.20 官方 Compose。 |
| MinIO | `minio/minio:RELEASE.2024-12-18T13-15-44Z` | Milvus 2.6 官方环境要求列出的兼容版本。 |
| Milvus | `milvusdb/milvus:v2.6.20` | 使用当前稳定的 2.6 系列，不采用 3.0 测试版。 |
| Attu | `zilliz/attu:v2.6.5` | Attu 官方兼容表对应 Milvus 2.6；Attu 3 不支持开源 Milvus 2.6。 |
| MongoDB | `mongo:7.0.16` | 固定 7.0 补丁版本，满足课程的会话历史功能且避免浮动标签。 |

参考资料：

- [Milvus 2.6.20 官方 Docker Compose](https://raw.githubusercontent.com/milvus-io/milvus/v2.6.20/deployments/docker/standalone/docker-compose.yml)
- [Milvus Docker 环境要求](https://milvus.io/docs/v2.6.x/prerequisite-docker.md)
- [Attu 2.6.5 使用及兼容说明](https://github.com/zilliztech/attu/tree/v2.6.5)

### 服务设计

- Compose 项目名固定为 `shopkeeper-brain`，专用网络为 `shopkeeper-knowledge`。
- etcd 和 MinIO 健康后才启动 Milvus，Milvus 健康后才启动 Attu。
- 对外端口全部绑定 `127.0.0.1`，不会直接暴露到局域网。
- etcd、MinIO、Milvus、MongoDB 分别使用独立命名卷。
- `docker compose down` 不删除命名卷；没有提供默认自动清库命令。
- MinIO 同时供 Milvus 存储对象和后续后端存储文档图片使用。

### 实际执行与验证

Docker Desktop 初始未运行，启动后检测到：

```text
Docker Engine: 29.3.1
CPU: 32
Docker 可用内存: 约 7.65 GiB
```

Milvus 官方建议 Standalone 至少使用 8 GB 内存。当前配置接近最低线，开发期间需要留意模型推理与 Milvus 同时运行时的内存压力。

Compose 验证结果：

- `docker compose config -q` 通过。
- 配置准确解析出 5 个服务和 5 个固定镜像。
- Attu、MinIO、Milvus、MongoDB 所有宿主机端口均绑定到 `127.0.0.1`。
- 五个镜像拉取成功，专用网络和四个命名卷创建成功。
- etcd、MinIO、Milvus、MongoDB 状态为 `healthy`，Attu 正常运行。
- MinIO 健康端点返回 HTTP 200。
- Milvus 健康端点返回 HTTP 200。
- Attu 首页返回 HTTP 200。
- MongoDB `db.adminCommand('ping')` 返回 `{"ok":1}`。

容器启动后的空载内存约为：

| 服务 | 空载内存 |
| --- | --- |
| etcd | 14 MiB |
| MinIO | 83 MiB |
| Milvus | 113 MiB |
| Attu | 43 MiB |
| MongoDB | 172 MiB |

### 安全说明

- 当前容器使用 `.env.example` 的示例凭据完成本机验证，端口只允许本机访问。
- 正式在本机创建 `.env` 时，需要替换所有包含 `change-me` 的密码。
- `.env` 已被 Git 忽略，不会进入 GitHub。
- 没有创建、复制或提交课程资料中的真实 API Key。

### Python 虚拟环境说明

本步只有 YAML 和 Markdown，没有运行 Python、安装 Python 包或编写后端代码，因此尚未创建虚拟环境。开始第 3 步后端骨架前，必须先准备 Python 3.10 并创建 `backend/.venv`。

### 下一步

第 3 步将先准备 Python 3.10 虚拟环境，再创建 FastAPI 后端骨架、配置系统、日志、异常处理和基础设施健康检查。

### 一句话总结

第 2 步用 Docker Compose 搭好了可持久化且仅供本机访问的五容器真实基础设施。

## 第 3 步：FastAPI 后端骨架

日期：2026-08-06

### 本步目标

1. 安装明确版本的 Python 3.10，不使用系统默认 Python 3.13。
2. 创建并始终使用 `backend/.venv` 独立虚拟环境。
3. 固定运行依赖和开发依赖版本。
4. 建立 FastAPI 应用、路由、配置、日志、异常及响应模型。
5. 建立 MinIO、Milvus、MongoDB 基础设施客户端和健康检查。
6. 编写单元测试与真实 Docker 基础设施集成测试。
7. 实际启动 Uvicorn 并验证根接口、健康接口和 OpenAPI。

### 与第 2 步的目录区别

第 2 步结束时，后端只有职责说明：

```text
backend/
└── README.md
```

本步完成后的后端目录：

```text
backend/
├── .venv/                         # 本地虚拟环境，Git 忽略
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── health.py
│   │   ├── __init__.py
│   │   └── router.py
│   ├── clients/
│   │   ├── __init__.py
│   │   └── infrastructure.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   └── logging.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── health.py
│   ├── __init__.py
│   └── main.py
├── tests/
│   ├── integration/
│   │   ├── __init__.py
│   │   └── test_infrastructure.py
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_exceptions.py
│   └── test_health_api.py
├── pyproject.toml
├── requirements-dev.txt
├── requirements.txt
└── README.md                       # 已更新为后端操作手册
```

仓库根目录还创建了本地 `.env`，它与 `.venv` 一样被 Git 忽略，不出现在 GitHub 文件树中。根目录 `.env.example` 和 `README.md` 已更新。

### 新文件作用

| 文件 | 作用 |
| --- | --- |
| `backend/requirements.txt` | 固定 FastAPI、Uvicorn、配置和三个基础设施 SDK 的运行依赖。 |
| `backend/requirements-dev.txt` | 在运行依赖之上固定 HTTPX2、pytest、覆盖率和 Ruff。 |
| `backend/pyproject.toml` | 限制 Python 为 3.10，并集中配置 pytest、coverage 和 Ruff。 |
| `backend/app/__init__.py` | 将 `app` 声明为后端应用包。 |
| `backend/app/main.py` | 创建 FastAPI 实例、注册 CORS、路由、异常处理和生命周期日志。 |
| `backend/app/api/__init__.py` | 声明 API 包。 |
| `backend/app/api/router.py` | 汇总后端所有 `/api` 路由。 |
| `backend/app/api/routes/__init__.py` | 声明业务路由子包。 |
| `backend/app/api/routes/health.py` | 实现 `/api/health`，汇总应用和基础设施状态。 |
| `backend/app/clients/__init__.py` | 声明外部客户端包。 |
| `backend/app/clients/infrastructure.py` | 按请求创建 MinIO、Milvus、MongoDB 客户端，执行带超时的真实连接检查。 |
| `backend/app/core/__init__.py` | 声明核心能力包。 |
| `backend/app/core/config.py` | 使用 Pydantic Settings 从根目录 `.env` 加载并校验配置。 |
| `backend/app/core/exceptions.py` | 定义业务异常和统一 JSON 错误响应，避免泄漏内部错误信息。 |
| `backend/app/core/logging.py` | 提供统一控制台日志格式和日志级别配置。 |
| `backend/app/schemas/__init__.py` | 声明 API 模型包。 |
| `backend/app/schemas/health.py` | 定义整体健康响应和单个组件健康状态模型。 |
| `backend/tests/__init__.py` | 声明测试包。 |
| `backend/tests/test_config.py` | 测试 CORS 解析和健康超时配置边界。 |
| `backend/tests/test_exceptions.py` | 测试业务异常格式及未知异常信息隐藏。 |
| `backend/tests/test_health_api.py` | 使用替身基础设施测试正常、降级和根接口响应。 |
| `backend/tests/integration/__init__.py` | 声明真实基础设施集成测试包。 |
| `backend/tests/integration/test_infrastructure.py` | 连接真实 MinIO、Milvus、MongoDB 并要求三者全部可用。 |

### 本地但不提交的新增内容

| 路径 | 作用 |
| --- | --- |
| `.env` | 保存本机运行配置和凭据，由 `.gitignore` 排除。 |
| `backend/.venv` | 保存 Python 3.10 解释器入口和项目依赖，由 `.gitignore` 排除。 |

### 修改文件作用

| 文件 | 本步改动 |
| --- | --- |
| `.env.example` | 增加日志级别和基础设施健康检查超时模板。 |
| `backend/README.md` | 从目录占位说明扩展为虚拟环境、安装、启动、测试和目录手册。 |
| `README.md` | 增加面向使用者的后端启动入口；未加入开发排错流水。 |
| `docs/development-log.md` | 记录本步目录变化、所有文件职责、问题处理和验证结果。 |

### Python 与虚拟环境

机器原有默认解释器为 Python 3.13.9，不符合本项目约定。通过 Python 官网下载官方 64 位 Python 3.10.11 安装器，验证结果：

```text
Authenticode 状态：Valid
签名者：Python Software Foundation
SHA256：D8DEDE5005564B408BA50317108B765ED9C3C510342A598F9FD42681CBE0648B
```

Python 3.10.11 安装为当前用户解释器，没有覆盖系统默认 `python`。随后使用明确路径创建虚拟环境：

```text
虚拟环境解释器：D:\code\xm\掌柜智库\backend\.venv\Scripts\python.exe
Python 版本：3.10.11
```

验证 `sys.prefix` 指向 `backend/.venv` 且不同于 `sys.base_prefix`，确认不是系统环境伪装。

### 固定依赖

运行依赖：

| 包 | 版本 | 用途 |
| --- | --- | --- |
| FastAPI | 0.141.1 | Web API 框架。 |
| Uvicorn | 0.52.1 | ASGI 开发服务器。 |
| Pydantic Settings | 2.14.2 | 环境变量读取与校验。 |
| MinIO SDK | 7.2.20 | 对象存储客户端。 |
| PyMilvus | 2.6.17 | 与 Milvus 2.6 服务端匹配的 Python SDK。 |
| PyMongo | 4.17.0 | MongoDB 客户端。 |

开发依赖：HTTPX2 2.9.1、pytest 9.1.1、pytest-cov 7.1.0、Ruff 0.16.1。

直接访问官方 PyPI 时本机 TLS 连接中断，因此按课程笔记使用清华 PyPI 镜像下载；版本信息仍从官方 PyPI 元数据核对。`pip check` 确认没有损坏或冲突依赖。

PyMilvus 当前默认最新版属于 3.0 系列，不能用于本项目的 Milvus 2.6，因此明确固定为可用的 2.6.17。FastAPI 当前测试栈提示旧 HTTPX 已弃用，开发依赖改用 HTTPX2。

### API 骨架

当前提供：

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/` | 返回应用名称、版本、健康和文档路径。 |
| GET | `/api/health` | 检查应用、MinIO、Milvus、MongoDB。 |
| GET | `/docs` | Swagger 交互文档。 |
| GET | `/redoc` | ReDoc 文档。 |
| GET | `/openapi.json` | OpenAPI 规范。 |

etcd 是 Milvus 的内部依赖，后端不直接访问；Milvus 健康检查成功已经覆盖其可用性链路。

### 测试与验证

最终结果：

- Ruff 代码检查通过。
- Ruff 格式检查通过，共检查 20 个 Python 文件。
- pytest 共 8 个测试全部通过。
- 真实 MinIO、Milvus、MongoDB 集成测试通过。
- 语句覆盖率 97%。
- `pip check` 返回 `No broken requirements found`。
- `/api/health` 实际响应为 `ok`。
- 健康响应确认 Python 为 3.10.11，MinIO、Milvus、MongoDB 均为 `up`。
- OpenAPI 标题和版本正确，共公开 2 条业务路径。

独立进程验收最初遇到固定测试端口被前一次 Uvicorn 子进程占用。核对命令行后只清理本次测试进程，并改用动态空闲端口完成验证。最终确认没有遗留 Uvicorn 进程和测试监听端口。

### 下一步

第 4 步将定义文档导入状态、节点基类与 LangGraph 工作流骨架，暂不一次性实现全部节点业务。

### 一句话总结

第 3 步在 Python 3.10 虚拟环境中建立了可运行、可测试并能连接真实基础设施的 FastAPI 后端骨架。

## 第 4 步：文档导入 LangGraph 工作流骨架

日期：2026-08-06

### 本步目标

1. 定义贯穿文档导入流程的共享状态，避免后续节点各自约定字段。
2. 建立统一节点基类，集中处理日志、执行耗时和异常包装。
3. 实现真实入口节点，校验文件并区分 PDF 与 Markdown 分支。
4. 使用 LangGraph 串起课程中的七个导入节点。
5. 让尚未开发的节点以明确的待实现节点参与流程，验证拓扑但不伪造业务结果。
6. 为状态隔离、入口分支、异常边界和两条完整路径编写单元测试。

### 与第 3 步的目录区别

第 3 步结束时，`backend/app` 还没有 `workflows` 目录，测试也只覆盖配置、异常、健康接口和基础设施。本步新增以下内容：

```text
backend/
├── app/
│   └── workflows/
│       ├── __init__.py
│       └── importing/
│           ├── nodes/
│           │   ├── __init__.py
│           │   ├── entry.py
│           │   └── pending.py
│           ├── __init__.py
│           ├── base.py
│           ├── exceptions.py
│           ├── graph.py
│           └── state.py
├── tests/
│   ├── test_import_nodes.py
│   ├── test_import_state.py
│   └── test_import_workflow.py
├── README.md                  # 已更新：增加工作流边界和调用示例
└── requirements.txt           # 已更新：增加 LangGraph
```

根目录 `README.md` 没有加入开发流水；本步过程仍只记录在本开发笔记中。

### 新文件作用

| 文件 | 作用 |
| --- | --- |
| `backend/app/workflows/__init__.py` | 声明后端 LangGraph 工作流包，为后续导入和查询流程提供统一目录。 |
| `backend/app/workflows/importing/__init__.py` | 导出导入状态、已编译工作流和便捷运行函数。 |
| `backend/app/workflows/importing/state.py` | 定义课程导入流程共享字段和深拷贝初始状态工厂，避免列表与字典跨任务共享。 |
| `backend/app/workflows/importing/base.py` | 提供节点统一调用入口、日志、毫秒耗时统计和未知异常包装。 |
| `backend/app/workflows/importing/exceptions.py` | 区分导入校验异常、节点异常和通用工作流异常。 |
| `backend/app/workflows/importing/graph.py` | 创建七节点 LangGraph，配置 PDF/Markdown 条件分支、顺序边和运行入口。 |
| `backend/app/workflows/importing/nodes/__init__.py` | 汇总当前可用的入口节点和待实现节点。 |
| `backend/app/workflows/importing/nodes/entry.py` | 真实检查导入路径、文件存在性和扩展名，并写入分支标志、标题及标准化路径。 |
| `backend/app/workflows/importing/nodes/pending.py` | 为后续六个业务节点提供不修改业务数据的显式占位实现，同时记录流程经过。 |
| `backend/tests/test_import_state.py` | 验证默认可变字段互不共享，并验证任务、文件和输出目录初始值。 |
| `backend/tests/test_import_nodes.py` | 验证 PDF/Markdown 识别、非法输入、节点耗时以及未知异常包装。 |
| `backend/tests/test_import_workflow.py` | 验证 PDF 完整路径、Markdown 跳过转换节点及无分支状态的失败行为。 |

### 修改文件作用

| 文件 | 本步改动 |
| --- | --- |
| `backend/requirements.txt` | 固定新增 `langgraph==1.2.10`。 |
| `backend/README.md` | 说明当前工作流已实现和未实现的边界，并提供直接调用示例。 |
| `docs/development-log.md` | 增加本步记录，并为第 1～3 步补充统一的“一句话总结”。 |

### 状态设计

状态字段沿用课程代码的主要命名，便于后续逐节点还原：

- 任务与输入：`task_id`、`import_file_path`、`file_dir`。
- 分支控制：`source_kind`、`is_pdf_read_enabled`、`is_md_read_enabled`。
- 文件处理：`pdf_path`、`md_path`、`file_title`、`md_content`。
- RAG 中间数据：`chunks`、`item_name`、`embeddings`、`milvus_ids`。
- 可观测信息：`completed_nodes`、`node_durations_ms`。

`create_import_state()` 每次深拷贝默认状态，避免一个任务修改 `chunks` 或耗时字典后污染另一个任务。

### 工作流结构

当前图的固定节点顺序为：

```text
START
  ↓
entry_node
  ├─ PDF → pdf_to_md_node ─┐
  └─ MD ───────────────────┤
                           ↓
                       md_img_node
                           ↓
                  document_split_node
                           ↓
               item_name_recognition_node
                           ↓
                  bge_embedding_node
                           ↓
                  import_milvus_node
                           ↓
                          END
```

`entry_node` 已经执行真实文件校验和分支选择。其余六个节点当前使用 `PendingNode`，只记录节点执行和未来职责，不读取 PDF、不生成假切片、不调用模型，也不写入数据库。

### LangGraph 版本选择

从官方 PyPI 元数据核对到 LangGraph 当前稳定版为 `1.2.10`，要求 Python `>=3.10`，与项目的 Python 3.10.11 兼容，因此固定直接依赖版本而不使用浮动标签。

参考资料：

- [LangGraph 官方 PyPI](https://pypi.org/project/langgraph/)
- [LangGraph Graph API 官方文档](https://docs.langchain.com/oss/python/langgraph/graph-api)

### Python 与虚拟环境

本步所有安装、检查和测试均使用：

```text
解释器：D:\code\xm\掌柜智库\backend\.venv\Scripts\python.exe
版本：Python 3.10.11
```

没有使用系统默认 Python 3.13，也没有在全局 Python 中安装 LangGraph。新增依赖安装完成后，`pip check` 返回 `No broken requirements found`。

### 测试与验证

最终结果：

- Ruff 代码检查通过。
- Ruff 格式检查通过，共检查 32 个 Python 文件。
- pytest 收集 19 个测试；常规测试为 18 个通过、1 个真实基础设施测试按开关跳过。
- 新增工作流的正常分支、错误分支和节点异常边界均被覆盖。
- 常规测试整体覆盖率为 90%；未覆盖部分仅来自默认不连接 Docker 的旧基础设施客户端。
- 显式开启 `RUN_INTEGRATION_TESTS=1` 后，MinIO、Milvus、MongoDB 真实集成测试通过。
- PDF 路径按七节点顺序结束，Markdown 路径正确跳过 `pdf_to_md_node`。

### 当前边界

- 工作流目前只能在 Python 内直接调用，尚未暴露上传 API。
- 只有入口节点拥有真实业务逻辑，其余节点不会伪造处理结果。
- 尚未安装 MinerU、PyTorch 或模型，也没有下载数 GB 的模型文件。
- 尚未修改 MinIO、Milvus 或 MongoDB 中的任何业务数据。

### 下一步

第 5 步将实现 `pdf_to_md_node`：先完成路径与输出目录校验、MinerU 命令构造和可测试的子进程边界，再根据本机资源决定 CPU pipeline 模型的安装与实际转换验证。

### 一句话总结

第 4 步把文档导入的数据契约和七节点 LangGraph 路线搭成了可运行、可追踪、可测试但不伪造业务结果的工作流骨架。
