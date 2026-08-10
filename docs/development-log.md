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

## 第 5 步：MinerU PDF 转 Markdown 节点

日期：2026-08-08

### 本步目标

1. 在项目的 Python 3.10 虚拟环境中安装 MinerU pipeline 依赖。
2. 把 `pdf_to_md_node` 从占位节点替换为真实业务节点。
3. 校验 PDF、输出目录、子进程退出码、超时和生成文件。
4. 让 MinerU 命令边界可替换，单元测试不下载模型也不运行推理。
5. 兼容 Windows 中文项目路径，并完成一次课程 PDF 的真实转换。
6. 保证模型、转换产物和用户文档都不进入 Git。

### 与第 4 步的目录区别

第 4 步结束时，PDF 分支仍由 `PendingNode` 记录流程经过。本步新增一个真实节点、一个仅供 MinerU 子进程使用的兼容文件和一组专项测试：

```text
backend/
├── app/
│   └── workflows/
│       └── importing/
│           ├── mineru_compat/
│           │   └── sitecustomize.py
│           └── nodes/
│               └── pdf_to_md.py
└── tests/
    └── test_pdf_to_md_node.py
```

以下已有文件也发生了修改：

```text
.
├── .env.example
├── backend/
│   ├── app/core/config.py
│   ├── app/workflows/importing/exceptions.py
│   ├── app/workflows/importing/graph.py
│   ├── app/workflows/importing/nodes/__init__.py
│   ├── tests/test_config.py
│   ├── tests/test_import_workflow.py
│   ├── README.md
│   └── requirements.txt
└── docs/development-log.md
```

真实验收还在 Git 忽略目录生成了 `models/` 和 `runtime/mineru-step5/`；它们属于本机运行数据，不是项目源码，因此不出现在提交目录中。

### 新文件作用

| 文件 | 作用 |
| --- | --- |
| `backend/app/workflows/importing/nodes/pdf_to_md.py` | 实现 PDF 路径和输出目录校验、MinerU 命令构造、无 shell 子进程调用、超时和退出码处理、Markdown 定位及状态更新。 |
| `backend/app/workflows/importing/mineru_compat/sitecustomize.py` | 仅在 MinerU 子进程中把 FastText 内置模型改为相对路径，绕开 Windows 原生 FastText 无法读取中文虚拟环境路径的问题。 |
| `backend/tests/test_pdf_to_md_node.py` | 用临时文件和可替换执行器验证命令、环境变量、标准与兼容输出目录、非法输入、失败退出、缺少产物和超时。 |

### 修改文件作用

| 文件 | 本步改动 |
| --- | --- |
| `.env.example` | 增加 MinerU 后端、超时和仓库内模型缓存默认值。 |
| `backend/app/core/config.py` | 增加 MinerU backend、模型来源、超时、ModelScope 和 Hugging Face 缓存配置及取值校验。 |
| `backend/app/workflows/importing/exceptions.py` | 新增可识别的 `PdfConversionError`。 |
| `backend/app/workflows/importing/graph.py` | 用真实 `PdfToMarkdownNode` 替换 PDF 占位节点，并允许测试注入替代节点。 |
| `backend/app/workflows/importing/nodes/__init__.py` | 公开导出 `PdfToMarkdownNode`。 |
| `backend/requirements.txt` | 固定新增 `mineru[pipeline]==3.4.4`。 |
| `backend/tests/test_config.py` | 增加 MinerU backend 和超时配置校验。 |
| `backend/tests/test_import_workflow.py` | PDF 路径改用模拟 MinerU 执行器走完整图，并确认真实写回 Markdown 路径。 |
| `backend/README.md` | 增加 MinerU 配置、模型缓存、中文路径兼容说明和 PDF 调用示例。 |
| `docs/development-log.md` | 增加第 5 步的实现、目录差异、文件职责和验证记录。 |

### 节点执行过程

`PdfToMarkdownNode` 按四段执行：

1. 必须从状态中取得一个真实存在的 `.pdf` 文件，并确认 `file_dir` 是目录或可创建目录。
2. 构造 `mineru -p <PDF> -o <目录> -b pipeline` 参数列表，以 `shell=False` 的方式执行。
3. 对命令不存在、运行超时和非零退出码分别抛出带节点名的可识别异常。
4. 优先查找 `<输出目录>/<文档名>/auto/<文档名>.md`；若 MinerU 小版本改变中间目录，则在该文档目录下接受唯一同名 Markdown。

转换成功后，节点写入绝对 `md_path` 并设置 `is_md_read_enabled=True`。耗时和节点完成顺序继续由第 4 步的 `BaseNode` 统一记录。

### 为什么测试不直接运行 MinerU

MinerU 首次使用需要下载约 GB 级模型，CPU 推理也远慢于普通单元测试。节点因此接收一个可替换的命令执行函数：

- 生产运行使用真实 `subprocess.run`。
- 单元测试用临时执行器检查完整命令和环境变量，并在临时目录创建预期产物。
- 另做一次真实验收覆盖模型下载和推理链路。

这样既验证了业务边界，也避免每次 `pytest` 都重新进行昂贵推理。

### Windows 中文路径兼容

第一次真实转换失败在 `fast_langdetect` 的原生 FastText 加载器：Python 能找到模型，但原生库打开包含“掌柜智库”的绝对路径时把中文转成乱码。

本步没有改名项目、没有重建虚拟环境，也没有恢复之前删除的英文项目入口。节点只在 Windows、内置 FastText 模型确实位于非 ASCII 路径时执行以下局部处理：

1. 仅向 MinerU 子进程的 `PYTHONPATH` 加入 `mineru_compat`。
2. 让子进程以 FastText 资源目录作为工作目录。
3. 用 `sitecustomize.py` 把模型位置改为纯英文相对文件名 `lid.176.ftz`。

第二次真实转换成功，其他 Python 进程和其他操作系统不会启用该补丁。

### 依赖与配置

本步固定使用 MinerU `3.4.4`，其当前 CLI 已实际核对支持：

```text
mineru -p <input> -o <output> -b pipeline
```

课程旧命令中的 `--source local` 没有继续硬编码；当前版本通过 `MINERU_MODEL_SOURCE` 环境变量选择 `modelscope`、`huggingface` 或 `local`。默认使用 ModelScope，并把模型放在已忽略的项目目录：

```dotenv
MINERU_BACKEND=pipeline
MINERU_MODEL_SOURCE=modelscope
MINERU_TIMEOUT_SECONDS=1800
MODELSCOPE_CACHE=models/modelscope
HF_HOME=models/huggingface
```

参考资料：

- [MinerU 官方中文 README](https://github.com/opendatalab/MinerU/blob/master/README_zh-CN.md)
- [MinerU 官方 CLI 文档](https://github.com/opendatalab/MinerU/blob/master/docs/en/usage/cli_tools.md)
- [MinerU 官方 PyPI](https://pypi.org/project/mineru/)

### Python 与虚拟环境

本步所有安装、检查、单元测试和真实转换均使用：

```text
解释器：D:\code\xm\掌柜智库\backend\.venv\Scripts\python.exe
版本：Python 3.10.11
MinerU：3.4.4
PyTorch：2.13.0+cpu
```

没有使用系统 Python 3.13，也没有把 MinerU 或 PyTorch 安装到全局环境。依赖安装约耗时 5 分 53 秒，中途一次下载中断后由 pip 自动续传完成，`pip check` 最终没有发现冲突。

### 测试与真实验证

最终结果：

- Ruff 代码检查通过。
- Ruff 格式检查通过，共检查 35 个 Python 文件。
- pytest 收集 29 个测试；28 个通过，1 个真实基础设施测试按开关跳过。
- 额外尝试显式运行旧基础设施集成测试时，确认 Docker Desktop 引擎未启动，三个本地端口均拒绝连接；本步不依赖这些服务，因此没有为了验收 MinerU 而启动容器。
- 常规测试总覆盖率为 88%，`pdf_to_md.py` 覆盖率为 83%。
- `pip check` 返回 `No broken requirements found`。
- MinerU CLI 版本为 `3.4.4`，实际参数与节点命令一致。
- 使用课程文件 `hak180产品安全手册.pdf` 真实转换成功，PDF 节点耗时约 44.9 秒。
- 生成的 Markdown 为 14,790 字节，开头正确识别出“HAK 180 烫金机”“产品安全手册（简体中文）”等正文。
- 真实转换生成 16 个输出文件，共约 4.27 MB。
- 本机项目缓存 15 个模型文件，共约 1.08 GB；`models/` 和 `runtime/` 均被 Git 忽略。

### 当前边界

- 入口节点和 PDF 转 Markdown 节点已经执行真实业务，其余五个导入节点仍是占位节点。
- 当前安装的是 CPU 版 PyTorch；可以正确转换，但大型 PDF 会明显更慢。
- 工作流仍未暴露为上传 HTTP API。
- 本步没有启动新的 Docker 容器，也没有向 MinIO、Milvus 或 MongoDB 写入业务数据。

### 下一步

第 6 步将实现 `md_img_node`：读取 MinerU Markdown 中的本地图片引用，上传图片到 MinIO，并把 Markdown 图片地址替换为可访问的对象地址。

### 一句话总结

第 5 步在项目 Python 3.10 虚拟环境中接通了可测试、可追踪且能兼容 Windows 中文路径的真实 MinerU PDF 转 Markdown 节点。

## 第 5 步调整：MinerU 改用云端 API

日期：2026-08-08

### 调整原因

准备部署的服务器只有 2 核 CPU、2 GiB 内存和 40 GiB 系统盘，不适合同时承载 MinerU 本地模型和项目基础设施。根据部署资源决定保留 PDF 转 Markdown 能力，但把计算迁移到 MinerU 精准解析云端 API。

这次是对第 5 步实现方式的调整，不提前进入第 6 步。第 5 步原记录保留，用于说明为什么曾安装本地模型以及最终为什么切换架构。

### 与调整前的目录区别

新增云端 API 客户端和专项测试：

```text
backend/
├── app/
│   └── clients/
│       └── mineru_api.py
└── tests/
    └── test_mineru_api_client.py
```

删除只服务于本地模型的兼容文件：

```text
backend/app/workflows/importing/mineru_compat/sitecustomize.py
```

修改以下已有文件：

```text
.
├── .env.example
├── backend/
│   ├── app/core/config.py
│   ├── app/workflows/importing/nodes/pdf_to_md.py
│   ├── tests/test_config.py
│   ├── tests/test_import_workflow.py
│   ├── tests/test_pdf_to_md_node.py
│   ├── README.md
│   └── requirements.txt
└── docs/development-log.md
```

本机还删除并重建了忽略目录中的虚拟环境，删除了下载模型和真实验收产物；这些目录原本不受 Git 管理，因此不会显示为 Git 文件删除。

### 新文件作用

| 文件 | 作用 |
| --- | --- |
| `backend/app/clients/mineru_api.py` | 封装 MinerU 精准解析 API 的签名地址申请、PDF 流式上传、任务轮询、ZIP 流式下载、安全解压和 Markdown 定位。 |
| `backend/tests/test_mineru_api_client.py` | 使用内存模拟 HTTP 服务验证上传、轮询、下载、任务失败、业务错误和 ZIP 路径越界防护，不消耗真实 API 次数。 |

### 删除文件作用

| 文件 | 删除原因 |
| --- | --- |
| `backend/app/workflows/importing/mineru_compat/sitecustomize.py` | 该文件只用于解决本地 FastText 模型读取 Windows 中文路径的问题；改用云端 API 后不再启动本地模型子进程。 |

### 修改文件作用

| 文件 | 本次改动 |
| --- | --- |
| `.env.example` | 删除本地 backend、模型来源和模型缓存变量，增加 API 地址、Token、云端模型版本、请求超时、轮询间隔和任务超时。 |
| `backend/app/core/config.py` | 用 MinerU API 配置替换本地模型配置，并限制云端模型为 `pipeline` 或 `vlm`。 |
| `backend/app/workflows/importing/nodes/pdf_to_md.py` | 删除命令行、子进程和中文路径兼容逻辑，改为校验输入后调用 API 客户端并写回 `full.md` 路径。 |
| `backend/requirements.txt` | 删除 `mineru[pipeline]==3.4.4`，明确增加轻量 HTTP 客户端 `httpx==0.28.1`。 |
| `backend/tests/test_config.py` | 改为验证 API 云端模型版本和任务超时。 |
| `backend/tests/test_import_workflow.py` | 完整 PDF 工作流改为注入模拟 API 转换器。 |
| `backend/tests/test_pdf_to_md_node.py` | 改为验证 API 转换器调用、路径校验、API 错误包装和缺少结果文件。 |
| `backend/README.md` | 改写 PDF 转换配置、Token 准备、数据上传说明和官方接口限制。 |
| `docs/development-log.md` | 保留原第 5 步历史，并新增本次架构调整记录。 |

### API 执行流程

当前 `PdfToMarkdownNode` 不再运行 `mineru` 命令，而是调用 `MinerUApiClient`：

```text
本地 PDF
  ↓ POST /file-urls/batch
申请 batch_id 和签名上传地址
  ↓ PUT 签名地址
流式上传 PDF
  ↓ GET /extract-results/batch/{batch_id}
轮询 waiting-file / pending / running / converting
  ↓ state=done
下载 full_zip_url
  ↓
安全解压 full.md、JSON 和 images
  ↓
把 full.md 绝对路径写回 LangGraph 状态
```

任务返回 `failed`、未知状态、超时、HTTP 错误或无结果文件时，都会转换为带 `pdf_to_md_node` 节点名的 `PdfConversionError`。

### 文件与安全处理

- PDF 和 ZIP 都采用流式传输，不把大文件整体读入内存，适合小内存服务器。
- ZIP 先写入输出目录中的临时文件，处理结束后无论成功失败都会删除。
- 解压前拒绝符号链接和 `../` 路径，防止压缩包把文件写到输出目录之外。
- API Token 只允许写入被 Git 忽略的本机 `.env`，示例配置保持空值。
- 使用云端 API 意味着 PDF 会发送到 MinerU 服务，需要接受其数据处理与额度规则。

### 本机清理结果

删除前：

- `models/`：15 个 MinerU 模型文件，约 1.08 GB。
- `runtime/mineru-step5/`：16 个真实验收文件，约 4.27 MB。
- `backend/.venv`：约 1.26 GB，包含 MinerU、PyTorch、ONNX Runtime 等依赖。

删除并按新依赖重建后：

- `models/` 已删除。
- `runtime/` 已删除；后续真实任务会按需重新创建输出目录。
- `mineru_compat/` 已删除。
- 新 `backend/.venv` 约 249 MB。
- 虚拟环境确认 `mineru` 和 `torch` 均未安装，`httpx` 已安装。
- 本次合计释放约 2.09 GB 本机磁盘空间。

首次从 PyPI 重建依赖时连续遇到 TLS 连接中断，最终使用阿里云 PyPI 镜像安装相同的固定版本；依赖完整性由 `pip check` 再次确认。

### API 配置

公开配置模板为：

```dotenv
MINERU_API_TOKEN=
MINERU_BASE_URL=https://mineru.net/api/v4
MINERU_MODEL_VERSION=vlm
MINERU_REQUEST_TIMEOUT_SECONDS=120
MINERU_POLL_INTERVAL_SECONDS=2
MINERU_TASK_TIMEOUT_SECONDS=1800
```

Token 需要用户在 [MinerU API 管理页面](https://mineru.net/apiManage/token)自行创建后，只写入仓库根目录 `.env`。本次没有 Token，因此没有发送真实 PDF，没有产生 API 调用或费用。

官方精准解析接口当前支持 `pipeline`、`vlm` 和 `MinerU-HTML`；本项目处理 PDF，默认使用官方推荐的 `vlm`。单个文件限制为不超过 200 MB、200 页，结果 ZIP 包含 Markdown、JSON 和图片。

参考资料：

- [MinerU 官方 API 文档](https://mineru.net/apiManage/docs)
- [课程环境配置与服务部署指南](D:/study/尚硅谷/掌柜智库项目/day09_MongDB_Milvus_查询流程骨架_商品名确认节点开始/笔记/课件全量最新/02_掌柜智库项目环境配置&服务部署指南.md)

### 测试与验证

当前验证结果：

- 所有检查均使用 `backend/.venv` 中的 Python 3.10.11。
- Ruff 代码检查通过。
- Ruff 格式检查通过，共检查 36 个 Python 文件。
- pytest 收集 33 个测试；32 个通过，1 个 Docker 基础设施测试按开关跳过。
- 总覆盖率为 86%；`pdf_to_md.py` 为 94%，`mineru_api.py` 为 76%。
- `pip check` 返回 `No broken requirements found`。
- 模拟 API 已验证上传、运行中轮询、成功下载、图片保留、业务错误、任务失败、任务超时和不安全 ZIP 拒绝。
- 没有使用真实 Token进行端到端 API 验收。

### 当前边界

- 服务器不需要 MinerU、PyTorch 或 1.08 GB PDF 解析模型，但每次解析需要访问 MinerU 云端服务。
- API 可用性、速度、额度和费用由 MinerU 平台决定。
- PDF 会离开业务服务器并上传到第三方服务。
- 入口节点和 PDF 转 Markdown 节点已经实现；其余五个导入节点仍为占位节点。
- Docker Desktop 当前未启动，本次调整不依赖 Docker。

### 下一步

第 6 步仍将实现 `md_img_node`：读取 API 结果 Markdown 中的本地图片引用，上传图片到 MinIO，并替换为可访问的对象地址。

### 一句话总结

第 5 步调整把 PDF 解析从本地重模型迁移为安全可测试的 MinerU 云端 API，并清除了约 2.09 GB 不再需要的本机文件。

## 第 6 步：Markdown 图片上传与链接替换

日期：2026-08-08

### 本步目标

把 `md_img_node` 从只记录顺序的占位节点替换为真实节点：读取 MinerU API 解压结果或用户 Markdown 中的本地图片引用，上传至 MinIO，并把 Markdown 中的本地地址替换为浏览器可访问的对象地址。

本步只负责图片存储和链接替换，不调用通义千问生成图片语义摘要。这样可以先独立验证文件与对象存储链路；图片理解能力在需要时再作为单独步骤接入。

### 与上一步的目录区别

上一步没有专用的图片存储客户端，`md_img_node` 仍由 `PendingNode` 代替。本步新增后的相关目录为：

```text
backend/
├── app/
│   ├── clients/
│   │   └── minio_storage.py                 # 新增
│   └── workflows/importing/nodes/
│       └── md_image.py                      # 新增
└── tests/
    ├── test_md_image_node.py                # 新增
    └── test_minio_image_storage.py          # 新增
```

同时修改以下已有文件：

```text
.
├── .env.example
├── backend/
│   ├── app/core/config.py
│   ├── app/workflows/importing/exceptions.py
│   ├── app/workflows/importing/graph.py
│   ├── app/workflows/importing/nodes/__init__.py
│   ├── app/workflows/importing/state.py
│   ├── tests/test_config.py
│   ├── tests/test_import_state.py
│   └── README.md
└── docs/development-log.md
```

### 每个新文件的作用

| 新文件 | 作用 |
| --- | --- |
| `backend/app/clients/minio_storage.py` | 创建独立图片桶、配置仅对象读取的公开策略、上传图片、识别 MIME 类型，并生成经过 URL 编码的公开地址。 |
| `backend/app/workflows/importing/nodes/md_image.py` | 解析 Markdown 图片语法，校验本地路径，去重上传，替换图片地址并保存非破坏性的处理结果。 |
| `backend/tests/test_md_image_node.py` | 验证本地与远程图片区分、重复引用去重、原文保留、异常路径拦截和存储错误转换。 |
| `backend/tests/test_minio_image_storage.py` | 使用模拟 MinIO 客户端验证建桶、公开只读策略、上传参数、URL 编码和异常包装。 |

### 已有文件的改动

| 文件 | 本次改动 |
| --- | --- |
| `.env.example` | 增加图片桶、浏览器公开基地址和公开读取开关。 |
| `backend/app/core/config.py` | 增加对应的三个 MinIO 图片配置项。 |
| `backend/app/workflows/importing/exceptions.py` | 新增 `MarkdownImageError`，让图片路径、上传和写入错误带有节点边界。 |
| `backend/app/workflows/importing/graph.py` | 用真实 `MarkdownImageNode` 替换 `md_img_node` 占位实现，并保留测试注入入口。 |
| `backend/app/workflows/importing/nodes/__init__.py` | 导出新的 Markdown 图片节点。 |
| `backend/app/workflows/importing/state.py` | 增加 `uploaded_image_urls`，记录本地引用与对象地址的对应关系。 |
| `backend/tests/test_config.py` | 验证图片桶默认配置。 |
| `backend/tests/test_import_state.py` | 验证图片地址映射不会在不同任务状态之间共享。 |
| `backend/README.md` | 增加图片节点的运行条件、配置方法、结果文件和公开访问安全说明。 |
| `docs/development-log.md` | 记录第 6 步实现、目录变化、验证结果和下一步。 |

### 节点执行流程

```text
读取 md_path
  ↓
解析 ![说明](图片地址)
  ↓
远程地址保持不变；本地地址执行路径和格式校验
  ↓
按真实文件去重，只上传 Markdown 实际引用的图片
  ↓
创建 shopkeeper-images 桶并设置仅 GetObject 的公开策略
  ↓
替换为 MINIO_PUBLIC_BASE_URL/桶名/对象名
  ↓
保存为 *_images.md，并更新 md_path、md_content、uploaded_image_urls
```

如果 Markdown 没有本地图片，节点只读取正文并继续，不会连接 MinIO。因此普通纯文本 Markdown 和不含图片的测试不要求 Docker 正在运行。

### 文件与安全处理

- 图片必须位于当前 Markdown 目录内部；绝对路径和 `../` 越界路径会直接拒绝，防止把服务器上的任意文件误传到对象存储。
- 当前允许 JPG、JPEG、PNG、GIF、WebP 和 BMP；无法识别的本地格式不会被静默忽略。
- 只上传正文实际引用的图片，不扫描并上传目录中的其他文件。
- 同一真实图片即使使用两种相对路径重复引用，也只上传一次。
- HTTP、HTTPS、Data URI 等远程地址保持不变。
- 上传失败会抛出明确的 `MarkdownImageError`，不会假装处理成功后继续工作流。
- 原始 Markdown 不覆盖；含本地图片时另存为 `*_images.md`。
- 图片使用独立的 `shopkeeper-images` 桶并只公开对象读取权限，原始文档所在的知识桶不会因此公开。
- 公开图片桶适合需要直接展示的非敏感文档图片；生产环境必须把公开基地址改为 HTTPS 域名或反向代理地址。

### Python 与虚拟环境

本步验证开始时发现原虚拟环境记录的基础解释器路径 `C:\Users\Lenovo\AppData\Local\Programs\Python\Python310` 已不存在，导致 `.venv` 启动器无法运行。已从 Python 官网恢复相同的 Python 3.10.11 运行时，原 `backend/.venv` 随即恢复可用，不需要把项目切换到 Python 3.13。

最终确认：

```text
解释器：D:\code\xm\掌柜智库\backend\.venv\Scripts\python.exe
Python：3.10.11
环境前缀：D:\code\xm\掌柜智库\backend\.venv
pip check：No broken requirements found
```

### 测试与验证

- Ruff 格式检查通过，共检查 40 个 Python 文件。
- Ruff 代码检查通过。
- pytest 共收集 45 个测试：44 个通过，1 个 Docker 基础设施测试按开关跳过。
- 总覆盖率为 87%；`minio_storage.py` 为 88%，`md_image.py` 为 93%。
- 新测试覆盖建桶、只读策略、MIME 类型、中文及空格 URL 编码、本地图片去重、远程图片保留、缺失文件、不支持格式、目录越界和 MinIO 异常。
- `pip check` 返回 `No broken requirements found`。
- Docker Desktop 当前未启动，因此没有执行真实 MinIO 写入；MinIO SDK 边界由模拟客户端验证，真实基础设施测试仍保留为显式开启模式。
- 本步没有调用 MinerU API，也没有消耗解析额度；已确认重启后的进程能够读取 `MINERU_API_TOKEN`，但没有输出或记录 Token 内容。

### 当前边界

- 当前图片替代文本沿用 Markdown 原值，尚未调用视觉模型生成图片说明。
- 图片链接依赖 MinIO 或其反向代理可被最终浏览器访问。
- 后续四个节点仍是占位节点：文档切分、商品名识别、向量化和 Milvus 写入。
- 工作流仍未暴露为文档上传 HTTP API。

### 下一步

第 7 步将实现 `document_split_node`：按 Markdown 标题和内容结构生成适合后续检索、向量化的文档片段。

### 一句话总结

第 6 步把 Markdown 本地图片安全上传到独立 MinIO 图片桶并替换为公开地址，同时保留原始文档和完整上传映射。

## 第 7 步：Markdown 文档结构化切分

日期：2026-08-08

### 本步目标

把 `document_split_node` 从占位节点替换为真实业务节点，将上一步得到的 Markdown 正文转换为适合后续商品名识别、向量化和 Milvus 入库的知识片段。

课程采用“标题初切、长块再切、短块合并、表格降维”的方案。本项目保留该主流程，并使用课程参数评估笔记最终推荐的默认值：最大 1000 字符、最小 200 字符。

### 与上一步的目录区别

上一步结束时，`document_split_node` 只记录执行顺序，没有真正产生 `chunks`。本步新增后的相关目录为：

```text
backend/
├── app/workflows/importing/
│   ├── markdown_tables.py                   # 新增
│   └── nodes/
│       └── document_split.py                # 新增
└── tests/
    ├── test_document_split_node.py          # 新增
    └── test_markdown_tables.py              # 新增
```

同时修改以下已有文件：

```text
.
├── .env.example
├── .gitignore
├── backend/
│   ├── app/core/config.py
│   ├── app/workflows/importing/exceptions.py
│   ├── app/workflows/importing/graph.py
│   ├── app/workflows/importing/nodes/__init__.py
│   ├── app/workflows/importing/state.py
│   ├── requirements.txt
│   ├── tests/test_config.py
│   ├── tests/test_import_workflow.py
│   └── README.md
└── docs/development-log.md
```

### 每个新文件的作用

| 新文件 | 作用 |
| --- | --- |
| `backend/app/workflows/importing/markdown_tables.py` | 识别 Markdown 与 HTML 表格，展开 `rowspan`、`colspan`，把行列关系转换为便于向量检索的中文线性文本。 |
| `backend/app/workflows/importing/nodes/document_split.py` | 校验正文和阈值，按标题切章节，拆分长章节，合并同父标题短章节，组装 `chunks` 并按需备份 JSON。 |
| `backend/tests/test_document_split_node.py` | 验证标题层级、代码围栏、纯标题文档、超长切分、短块合并、长度上限、表格处理、参数错误和备份开关。 |
| `backend/tests/test_markdown_tables.py` | 验证 Markdown 表格、HTML 键值表、跨行单元格以及非表格正文保持不变。 |

### 已有文件的改动

| 文件 | 本次改动 |
| --- | --- |
| `.env.example` | 增加最大切片长度、最小合并长度和 JSON 备份开关。 |
| `.gitignore` | 忽略运行时生成的 `*_chunks.json`，避免调试产物进入 Git。 |
| `backend/app/core/config.py` | 增加切分配置，并在启动配置阶段校验 `0 < min < max` 和最大值下限。 |
| `backend/app/workflows/importing/exceptions.py` | 新增 `DocumentSplitError`，用于表达无法生成有效知识片段的业务错误。 |
| `backend/app/workflows/importing/graph.py` | 用真实 `DocumentSplitNode` 替换占位节点，并保留测试注入参数。 |
| `backend/app/workflows/importing/nodes/__init__.py` | 导出文档切分节点。 |
| `backend/app/workflows/importing/state.py` | 定义 `DocumentChunk` 结构，并增加 `chunks_path` 备份路径。 |
| `backend/requirements.txt` | 固定增加 `langchain-text-splitters==1.1.2` 和 `beautifulsoup4==4.15.0`。 |
| `backend/tests/test_config.py` | 增加切分默认配置与大小关系校验。 |
| `backend/tests/test_import_workflow.py` | 确认 PDF 和 Markdown 两条完整分支现在都会真实产生 `chunks`。 |
| `backend/README.md` | 增加切分配置、处理顺序、输出结构、备份行为和本地执行说明。 |
| `docs/development-log.md` | 记录第 7 步目录差异、实现决策、验证结果和下一步。 |

### 节点执行流程

```text
读取 md_content、file_title 和切分配置
  ↓
统一 Windows、Linux 换行符
  ↓
识别 1～6 级 Markdown 标题并维护父标题层级
  ↓
跳过代码围栏内部看起来像标题的 # 行
  ↓
Markdown/HTML 表格转换为带行列语义的中文文本
  ↓
超长章节按段落、换行、中文和英文句末标点递归切分
  ↓
同一父标题下的短片段在不超过 max 的前提下合并
  ↓
组装 title、parent_title、file_title、content、可选 part
  ↓
写入 state.chunks，并按配置生成 *_chunks.json
```

### 相比课程示例的稳健性调整

- 课程示例直接读取 `current_sections[0]`，空文档可能产生下标异常；当前节点会提前验证正文并明确报告业务错误。
- 短片段只有在父标题相同且合并后仍不超过最大长度时才会合并，避免为了减少碎片而生成超长块。
- 不把空的结构标题单独生成无意义块，但仅含一个标题的合法 Markdown 仍会得到一个可用 chunk。
- 递归切分保留句末分隔符，避免中文句号等语义边界在切分时丢失。
- 超长章节保留原始标题，使用独立 `part` 数字标记顺序，不反复修改标题文字。
- 备份文件采用 `<Markdown 文件名>_chunks.json`，避免不同文档都覆盖同一个 `chunks.json`。
- JSON 备份失败只影响调试文件，不丢失已经写入 LangGraph 状态的核心 `chunks`。

### 配置与输出

公开配置模板为：

```dotenv
DOCUMENT_CHUNK_MAX_LENGTH=1000
DOCUMENT_CHUNK_MIN_LENGTH=200
DOCUMENT_CHUNK_BACKUP_ENABLED=true
```

每个 chunk 的基础结构为：

```json
{
  "title": "## 安全说明",
  "parent_title": "# 产品手册",
  "file_title": "产品手册",
  "content": "## 安全说明\n\n使用前请阅读……",
  "part": 1
}
```

`part` 只在一个超长章节被拆成多个片段时出现。当前阈值按字符数计算，不等同于模型 Token 数；其目标是在 BGE-M3 上限以内进一步控制语义粒度。

### Python 与依赖

所有安装和验证继续使用：

```text
解释器：D:\code\xm\掌柜智库\backend\.venv\Scripts\python.exe
Python：3.10.11
langchain-text-splitters：1.1.2
beautifulsoup4：4.15.0
虚拟环境大小：约 239 MB
```

官方 PyPI 查询时再次遇到 TLS 连接中断，随后使用阿里云 PyPI 镜像查询并安装相同的固定版本。安装没有升级或破坏现有 LangGraph 依赖，`pip check` 最终没有发现冲突。

### 测试与真实文档验证

- Ruff 格式检查通过，共检查 44 个 Python 文件。
- Ruff 代码检查通过。
- pytest 共收集 62 个测试：61 个通过，1 个 Docker 基础设施测试按开关跳过。
- 总覆盖率为 88%；`document_split.py` 为 93%，`markdown_tables.py` 为 86%。
- `pip check` 返回 `No broken requirements found`。
- 使用课程笔记 `切分与合并参数简单评估方式.md` 完成只读真实文档验收，没有写入课程目录。
- 该课程文档按默认 1000/200 参数得到 10 个 chunk；最短 221 字符，最长 990 字符，超过 1000 字符的片段为 0。
- 真实验证关闭了 JSON 备份，没有调用 MinerU、通义千问、MinIO、MongoDB 或 Milvus，也没有产生 API 费用。

### 当前边界

- 切分长度当前按 Python 字符数计算，不进行模型 Token 精确计数。
- 表格线性化面向常见 MinerU HTML 表格和标准 Markdown 表格，不执行复杂 HTML 页面渲染。
- 商品名识别、BGE-M3 向量化和 Milvus 写入三个后续节点仍是占位节点。
- 工作流仍未暴露为文档上传 HTTP API。

### 下一步

第 8 步将实现 `item_name_recognition_node`：调用通义千问兼容 API，从文档标题和切片内容中识别商品名称，并写回每个 chunk。

### 一句话总结

第 7 步把 Markdown 按标题语义、长度和表格结构稳定切成不超上限的知识片段，为后续商品识别和向量检索准备好了标准 `chunks`。

## 第 8 步：通义千问商品名称识别

日期：2026-08-08

### 本步目标

把 `item_name_recognition_node` 从占位节点替换为真实业务节点：从有限数量的前置文档切片中提取核心商品或设备名称，写入工作流状态，并回填到每个 chunk，为后续向量化和分类检索提供统一实体名称。

课程示例在该节点中同时执行商品名识别、BGE-M3 向量化和 Milvus 写入。当前项目的 LangGraph 已经为向量化和入库分别设置后续节点，因此本步只负责商品名识别与回填，不提前加载本地模型，也不写 Milvus。

### 与上一步的目录区别

上一步结束时，`item_name_recognition_node` 仍由 `PendingNode` 代替。本步新增后的相关目录为：

```text
backend/
├── app/
│   ├── clients/
│   │   └── qwen_chat.py                         # 新增
│   └── workflows/importing/
│       ├── prompts.py                           # 新增
│       └── nodes/
│           └── item_name_recognition.py         # 新增
└── tests/
    ├── test_item_name_recognition_node.py       # 新增
    └── test_qwen_chat_client.py                 # 新增
```

同时修改以下已有文件：

```text
.
├── .env.example
├── backend/
│   ├── app/core/config.py
│   ├── app/workflows/importing/exceptions.py
│   ├── app/workflows/importing/graph.py
│   ├── app/workflows/importing/nodes/__init__.py
│   ├── app/workflows/importing/state.py
│   ├── tests/test_config.py
│   ├── tests/test_import_workflow.py
│   └── README.md
└── docs/development-log.md
```

### 每个新文件的作用

| 新文件 | 作用 |
| --- | --- |
| `backend/app/clients/qwen_chat.py` | 使用现有 `httpx` 调用通义千问 OpenAI 兼容 Chat Completions，启用 JSON mode，校验配置、HTTP 状态和响应结构。 |
| `backend/app/workflows/importing/prompts.py` | 集中保存商品名识别系统提示词与用户模板，并明确文档是不可信数据、核心品类不得省略。 |
| `backend/app/workflows/importing/nodes/item_name_recognition.py` | 校验状态、限制上下文、调用千问、规范化商品名、处理 `UNKNOWN` 降级、无副作用回填 chunks 并按需备份。 |
| `backend/tests/test_qwen_chat_client.py` | 用内存 HTTP 服务验证请求地址、Bearer 鉴权、JSON mode、代码围栏兼容、配置错误、HTTP 错误、超时和异常 JSON。 |
| `backend/tests/test_item_name_recognition_node.py` | 验证上下文数量和长度、商品名回填、原状态不被修改、文件名降级、异常传播、输入校验与 JSON 备份。 |

### 已有文件的改动

| 文件 | 本次改动 |
| --- | --- |
| `.env.example` | 给出北京地域兼容地址、`qwen-flash` 默认模型、超时、输出上限、上下文数量与备份开关；Token 继续留空。 |
| `backend/app/core/config.py` | 正式加载通义千问和商品名识别配置，并限制温度、超时、输出 Token 和上下文参数范围。 |
| `backend/app/workflows/importing/exceptions.py` | 新增 `ItemNameRecognitionError`，为商品名 API 与响应错误提供清晰节点边界。 |
| `backend/app/workflows/importing/graph.py` | 用真实 `ItemNameRecognitionNode` 替换占位节点，并保留测试注入入口。 |
| `backend/app/workflows/importing/nodes/__init__.py` | 导出商品名识别节点。 |
| `backend/app/workflows/importing/state.py` | 给 `DocumentChunk` 增加 `item_name`，并增加识别来源和备份路径状态。 |
| `backend/tests/test_config.py` | 验证千问地址、模型、输出 Token 和上下文默认值及范围。 |
| `backend/tests/test_import_workflow.py` | 为完整工作流注入模拟识别器，确认 PDF 与 Markdown 分支都会生成并回填商品名，避免单元测试消耗真实 API。 |
| `backend/README.md` | 增加通义千问配置、数据范围、降级规则、隐私边界和地域地址说明。 |
| `docs/development-log.md` | 记录第 8 步实现、真实调用结果、目录差异和下一步。 |

### 节点执行流程

```text
读取 file_title 和 chunks
  ↓
最多选取前 ITEM_NAME_CHUNK_COUNT 个切片
  ↓
连同切片标签截断到 ITEM_NAME_CONTEXT_MAX_LENGTH 字符以内
  ↓
标题 + 有限正文进入防提示词注入的抽取模板
  ↓
POST /chat/completions，使用 qwen-flash 和 JSON mode
  ↓
解析 {"item_name": "..."} 并校验字符串、空值和 200 字符上限
  ↓
若明确为 UNKNOWN：使用 file_title，并标记 file_title_fallback
  ↓
其他有效结果：标记 qwen，无副作用地复制并回填所有 chunks
  ↓
按配置生成 *_item_name_chunks.json
```

### API 与安全设计

- 直接使用项目已有的 `httpx` 调用 OpenAI 兼容接口，没有新增 OpenAI SDK 或 LangChain 模型客户端，保持 2 GiB 服务器部署尽量轻量。
- 请求启用 `response_format={"type":"json_object"}`，系统与用户提示词都明确包含 JSON 要求，符合百炼 JSON mode 的调用条件。
- 单次回复最多 128 Token，温度默认为 0，减少费用、输出漂移和无关内容。
- 客户端不会在日志或异常中打印 API Key、请求正文或上游响应正文；HTTP 错误只暴露状态码。
- 文档片段被视为不可信数据，系统提示词明确禁止执行其中的指令，降低文档提示词注入风险。
- 只有模型明确返回 `UNKNOWN` 才降级为文件名；密钥缺失、网络错误、非 JSON 或缺少 `item_name` 会明确失败，避免错误数据继续入库。
- 传入模型的正文最多 2500 字符且默认仅取前 3 个 chunk，但这些内容仍会发送到阿里云百炼，敏感文档需要先确认合规要求。

当前官方文档仍支持 `qwen-flash` 的非思考 JSON mode，并说明北京地域可使用课程中的兼容地址。新工作区或其他地域应按控制台信息修改地址：

- [阿里云百炼：结构化输出](https://help.aliyun.com/zh/model-studio/qwen-structured-output)
- [阿里云百炼：首次调用通义千问](https://help.aliyun.com/zh/model-studio/first-api-call-to-qwen)

### 配置

公开配置模板为：

```dotenv
OPENAI_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_API_KEY=
ITEM_MODEL=qwen-flash
LLM_DEFAULT_TEMPERATURE=0
QWEN_REQUEST_TIMEOUT_SECONDS=60
ITEM_NAME_MAX_OUTPUT_TOKENS=128
ITEM_NAME_CHUNK_COUNT=3
ITEM_NAME_CONTEXT_MAX_LENGTH=2500
ITEM_NAME_BACKUP_ENABLED=true
```

当前 Codex 进程能够读取系统提供的 `DASHSCOPE_API_KEY`。验证只记录了“已配置”和长度，没有输出、复制或写入真实 Token；仓库根目录 `.env` 中没有新增该密钥，`.env.example` 仍为空值。

### Python 与依赖

本步没有增加 Python 包，继续复用已经固定的 `httpx==0.28.1`：

```text
解释器：D:\code\xm\掌柜智库\backend\.venv\Scripts\python.exe
Python：3.10.11
虚拟环境大小：约 239 MB
pip check：No broken requirements found
```

所有测试、真实 API 调用和检查都使用 `backend/.venv`，没有使用系统 Python 3.13。

### 测试与真实 API 验证

- Ruff 格式检查通过，共检查 49 个 Python 文件。
- Ruff 代码检查通过。
- pytest 共收集 88 个测试：87 个通过，1 个 Docker 基础设施测试按开关跳过。
- 总覆盖率为 88%；`qwen_chat.py` 为 93%，`item_name_recognition.py` 为 85%。
- `pip check` 返回 `No broken requirements found`。
- 单元测试全部使用内存 HTTP 服务和注入识别器，不消耗通义千问额度。
- 使用一段不含隐私的合成正文真实调用 `qwen-flash` 两次，验证 OpenAI 兼容端点、JSON mode、Token 和状态回填。
- 第一次返回“优利德 RS-12”，说明模型省略了正文明确存在的核心品类；据此收紧提示词，要求核心品类不得省略。
- 第二次返回“优利德 RS-12 数字万用表”，来源为 `qwen`，1 个测试 chunk 正确回填，真实链路验收通过。
- 两次调用均未输出 API Key 或完整请求；没有调用 MinerU，没有启动 Docker，也没有访问 MinIO、MongoDB 或 Milvus。

### 当前边界

- 商品名识别只查看文档标题和前置少量 chunk；如果商品名称只在文档很后面出现，可能降级或识别不完整。
- 当前只提取一个核心商品名称，不处理一份文档包含多个并列商品的情况。
- 本步不生成商品名向量，也不写入 Milvus；这两个职责留给后续向量化与入库节点。
- BGE-M3 本地模型对 2 核 2 GiB 服务器可能过重，下一步开始前需要结合现有服务器继续选择轻量 API 或本地方案。
- 工作流仍未暴露为文档上传 HTTP API。

### 下一步

第 9 步将先评估 2 核 2 GiB 服务器可承载的向量化方案，再实现 `bge_embedding_node`，为每个 chunk 生成后续 Milvus 检索需要的向量。

### 一句话总结

第 8 步用轻量、安全且经过真实调用验证的通义千问 JSON 接口识别商品全名，并把可信来源标记和名称写回了全部知识片段。

## 第 9 步：百炼云端混合向量生成

日期：2026-08-08

### 本步目标

把 `bge_embedding_node` 从占位节点替换为真实业务节点，为每个知识片段生成 Milvus 混合检索需要的稠密向量和稀疏向量。

课程使用本地 BGE-M3。结合目标服务器只有 2 核、2 GiB 内存，以及前面已经确定的“AI 推理优先走 API”部署原则，本项目改用阿里云百炼 `text-embedding-v4` 原生 HTTP 接口。该接口能够在一次请求中返回 `dense&sparse`，因此没有牺牲课程中的混合检索结构，也不需要服务器下载或常驻加载本地向量模型。

### 与上一步的目录区别

上一步结束时，`bge_embedding_node` 仍由 `PendingNode` 代替，chunk 只有正文和商品名称。本步新增后的相关目录为：

```text
backend/
├── app/
│   ├── clients/
│   │   └── dashscope_embedding.py              # 新增
│   └── workflows/importing/nodes/
│       └── bge_embedding.py                    # 新增
└── tests/
    ├── test_bge_embedding_node.py              # 新增
    └── test_dashscope_embedding_client.py      # 新增
```

同时修改以下已有文件：

```text
.
├── .env.example
├── .gitignore
├── backend/
│   ├── app/core/config.py
│   ├── app/workflows/importing/exceptions.py
│   ├── app/workflows/importing/graph.py
│   ├── app/workflows/importing/nodes/__init__.py
│   ├── app/workflows/importing/state.py
│   ├── tests/test_config.py
│   ├── tests/test_import_workflow.py
│   └── README.md
└── docs/development-log.md
```

### 每个新文件的作用

| 新文件 | 作用 |
| --- | --- |
| `backend/app/clients/dashscope_embedding.py` | 使用现有 `httpx` 调用百炼原生同步向量接口，请求底库文本的 1024 维稠密向量和稀疏向量，并校验鉴权配置、批量上限、HTTP 状态、返回数量、顺序、维度与数值。 |
| `backend/app/workflows/importing/nodes/bge_embedding.py` | 保留课程节点名，校验 chunks，拼接“商品名称 + 正文”，按批调用云端向量服务，无副作用地把两种向量写回 chunk，并按需备份 JSON。 |
| `backend/tests/test_dashscope_embedding_client.py` | 用内存 HTTP 服务验证 URL、Bearer 鉴权、`document` 类型、`dense&sparse` 参数、乱序响应复原、输入限制、超时、HTTP 错误及异常向量响应。 |
| `backend/tests/test_bge_embedding_node.py` | 验证分批、文本拼接、两种向量回填、原状态不被修改、备份开关、客户端错误、数量不一致和无效 chunk。 |

### 已有文件的改动

| 文件 | 本次改动 |
| --- | --- |
| `.env.example` | 删除不再使用的本地 BGE-M3 路径、设备和半精度配置，增加百炼向量地址、模型、维度、批次、超时和备份开关。 |
| `.gitignore` | 忽略 `*_vectors.json`、项目内 Python 3.10 基础运行时和安装缓存，避免大型运行文件进入 Git。 |
| `backend/app/core/config.py` | 加载百炼向量配置，限定官方支持的维度，并把单批文本数限制为 1～10。 |
| `backend/app/workflows/importing/exceptions.py` | 新增 `EmbeddingError`，使向量服务失败在节点边界清晰终止。 |
| `backend/app/workflows/importing/graph.py` | 用真实 `BgeEmbeddingNode` 替换占位节点，并增加测试或调用方注入接口。 |
| `backend/app/workflows/importing/nodes/__init__.py` | 导出混合向量节点。 |
| `backend/app/workflows/importing/state.py` | 给 `DocumentChunk` 增加 `dense_vector`、`sparse_vector`，给图状态增加向量备份路径。 |
| `backend/tests/test_config.py` | 验证云端向量默认配置、批次上限和可选维度限制。 |
| `backend/tests/test_import_workflow.py` | 在 PDF、Markdown 完整流程测试中注入模拟向量服务，并确认真实节点已回填向量。 |
| `backend/README.md` | 更新导入流程进度，增加云端混合向量配置、输出、错误边界、隐私和模型一致性说明。 |
| `docs/development-log.md` | 记录第 9 步的方案取舍、目录差异、验证结果和下一步。 |

### 节点执行流程

```text
读取上一步已回填 item_name 的 chunks
  ↓
逐块组装：item_name + 换行 + content
  ↓
每批最多 10 条，使用 text_type=document
  ↓
调用百炼 text-embedding-v4 原生同步接口
  ↓
一次返回 dense 1024 维向量与 sparse 非零权重
  ↓
按 text_index 恢复输入顺序并做完整校验
  ↓
把 dense_vector、sparse_vector 写回每个 chunk
  ↓
把稠密向量列表写入 state.embeddings
  ↓
按配置生成 *_vectors.json 调试备份
```

### 为什么使用百炼原生接口

- OpenAI 兼容 `/embeddings` 接口适合获得稠密向量，但百炼原生接口还支持 `output_type=dense&sparse`，可以一次完成课程 BGE-M3 的两类输出。
- 稠密向量负责语义相近内容，稀疏向量更擅长型号、专业词和精确关键词；下一步仍可在 Milvus 中建立两套索引并做混合召回。
- 服务器只运行 FastAPI、数据处理和数据库客户端，不运行 PyTorch 或 BGE-M3，因此不会额外占用大量常驻内存，也没有模型缓存要部署。
- 入库显式使用 `text_type=document`；后续查询必须使用同一模型、同一维度并改用 `query`，避免入库与检索向量空间不一致。

官方同步接口说明 `text-embedding-v4` 单次最多接收 10 条文本、单条最长 8192 Token，并支持 64～2048 的多个向量维度。本项目继续采用课程兼容且官方推荐用于通用检索的 1024 维：

- [阿里云百炼：同步向量接口](https://help.aliyun.com/zh/model-studio/text-embedding-synchronous-api)
- [阿里云百炼：向量模型与规格](https://help.aliyun.com/zh/model-studio/embedding)

### 配置与输出

公开配置模板为：

```dotenv
DASHSCOPE_API_BASE=https://dashscope.aliyuncs.com/api/v1
DASHSCOPE_API_KEY=
EMBEDDING_MODEL=text-embedding-v4
EMBEDDING_DIMENSION=1024
EMBEDDING_BATCH_SIZE=10
EMBEDDING_REQUEST_TIMEOUT_SECONDS=60
EMBEDDING_BACKUP_ENABLED=true
```

每个 chunk 在本步新增：

```json
{
  "dense_vector": [0.012, -0.034, 0.056],
  "sparse_vector": {
    "7149": 0.829,
    "111290": 0.9004
  }
}
```

示例只展示少量元素；真实稠密向量固定为 1024 维。Python 内部的稀疏索引键是整数，JSON 规范会在调试备份中把对象键显示为字符串，后续写入 Milvus 时仍使用内存中的整数键。

### Python 与虚拟环境

检查开始时，`backend/.venv` 记录的 Python 3.10 基础解释器再次缺失。恢复官方 Python 3.10.11 后发现 Codex 项目沙箱无法在普通命令中持续读取用户目录，因此把同一基础运行时复制到 Git 忽略的 `backend/.python310`，并让 `.venv` 指向该路径。

最终确认：

```text
项目解释器：D:\code\xm\掌柜智库\backend\.venv\Scripts\python.exe
Python：3.10.11
虚拟环境依赖目录：约 239 MiB
项目内基础运行时：约 54 MiB（Git 已忽略）
新增 Python 包：0
pip check：No broken requirements found
```

所有代码检查、单元测试和真实 API 调用都使用 `backend/.venv`，没有使用系统 Python 3.13。

### 测试与真实 API 验证

- Ruff 格式检查通过，共检查 53 个 Python 文件。
- Ruff 代码检查通过。
- pytest 共收集 117 个测试：116 个通过，1 个 Docker 基础设施测试按开关跳过。
- 总覆盖率为 89%；`dashscope_embedding.py` 为 89%，`bge_embedding.py` 为 91%。
- `pip check` 返回 `No broken requirements found`。
- 单元测试使用内存 HTTP 服务和注入向量器，不消耗百炼额度。
- 使用 2 段不含隐私的 RS-12 合成说明真实调用 `text-embedding-v4`，返回 2 组 1024 维稠密向量和分别含 7、8 个非零项的稀疏向量，真实链路通过。
- 真实验证只输出结果数量和向量维度，没有输出 API Key、完整向量或上游请求正文。
- 本步没有调用 MinerU，没有启动 Docker，也没有访问 MinIO、MongoDB 或 Milvus。

### 当前边界

- 向量化会把商品名称和全部切片正文发送给阿里云百炼，敏感资料需要先确认数据合规要求。
- 向量结果与模型和维度绑定；修改 `EMBEDDING_MODEL` 或 `EMBEDDING_DIMENSION` 后，需要重建已有知识库向量，不能混用。
- API 临时失败当前会明确终止导入，尚未加入自动重试和断点续传。
- `import_milvus_node` 仍是占位节点，因此本步生成的向量尚未写入数据库。
- 工作流仍未暴露为文档上传 HTTP API。

### 下一步

第 10 步将实现 `import_milvus_node`：创建稠密和稀疏向量字段及索引，把 chunks 批量写入 Milvus，并将数据库生成的 ID 回填到工作流状态。

### 一句话总结

第 9 步用百炼 `text-embedding-v4` API 取代本地 BGE-M3，为每个知识片段生成可供 Milvus 混合检索的 1024 维稠密向量和关键词稀疏向量。

## 第 10 步：Milvus 混合向量入库

日期：2026-08-09

### 本步目标

把导入流程最后一个 `import_milvus_node` 从占位节点替换为真实业务节点：创建或校验知识片段集合，为稠密向量和稀疏向量建立索引，批量写入上一步生成的 chunks，并把 Milvus 自动生成的主键回填到工作流状态。

本步完成后，PDF 与 Markdown 两条导入分支从入口、解析、图片处理、切分、商品名识别、向量化到 Milvus 入库的七个节点都已具备真实实现，不再保留只记录执行顺序的占位节点。

### 与上一步的目录区别

上一步结束时，`import_milvus_node` 仍由通用 `PendingNode` 代替，向量只保存在内存状态和调试 JSON 中。本步新增后的相关目录为：

```text
backend/
├── app/
│   ├── clients/
│   │   └── milvus_storage.py                    # 新增
│   └── workflows/importing/nodes/
│       └── import_milvus.py                     # 新增
└── tests/
    ├── integration/
    │   └── test_milvus_import.py                # 新增
    ├── test_import_milvus_node.py               # 新增
    └── test_milvus_storage.py                   # 新增
```

同时修改或删除以下已有文件：

```text
.
├── .env.example
├── backend/
│   ├── app/core/config.py
│   ├── app/workflows/importing/exceptions.py
│   ├── app/workflows/importing/graph.py
│   ├── app/workflows/importing/nodes/__init__.py
│   ├── app/workflows/importing/nodes/pending.py  # 删除
│   ├── app/workflows/importing/state.py
│   ├── tests/test_config.py
│   ├── tests/test_import_workflow.py
│   └── README.md
└── docs/development-log.md
```

### 每个新文件的作用

| 新文件 | 作用 |
| --- | --- |
| `backend/app/clients/milvus_storage.py` | 封装集合 schema、稠密与稀疏索引、已有集合兼容性检查、分批写入、返回主键校验和失败后的尽力回滚。 |
| `backend/app/workflows/importing/nodes/import_milvus.py` | 校验工作流 chunks、标量字段和两种向量，组装明确的 Milvus 实体，调用存储层入库，把自动主键回填到 chunks，并按配置生成调试备份。 |
| `backend/tests/test_milvus_storage.py` | 用内存模拟客户端验证建表、索引、已有集合兼容性、分批写入、主键校验、刷新和后续批次失败回滚。 |
| `backend/tests/test_import_milvus_node.py` | 验证节点的实体组装、ID 回填、原状态不被修改、备份开关、集合名、批次、字段、维度、稀疏向量及异常包装。 |
| `backend/tests/integration/test_milvus_import.py` | 连接 Docker 中的真实 Milvus，创建唯一临时集合，写入两条混合向量数据，读取核对字段与索引，并在结束时删除临时集合。 |

### 已有文件的改动

| 文件 | 本次改动 |
| --- | --- |
| `.env.example` | 增加 Milvus 单批写入数量、请求超时和入库结果备份开关。 |
| `backend/app/core/config.py` | 加载集合名、稠密度量、批次大小、请求超时和备份配置，并限制合法范围。 |
| `backend/app/workflows/importing/exceptions.py` | 新增 `MilvusImportError`，在工作流节点边界表达集合或写入失败。 |
| `backend/app/workflows/importing/graph.py` | 用真实 `ImportMilvusNode` 替换最后一个占位节点，并提供测试注入入口。 |
| `backend/app/workflows/importing/nodes/__init__.py` | 导出 Milvus 入库节点，不再导出通用占位节点。 |
| `backend/app/workflows/importing/nodes/pending.py` | 删除；七个导入节点均已完成真实实现，项目中已没有调用方。 |
| `backend/app/workflows/importing/state.py` | 给 chunk 增加整数 `chunk_id`，把 `milvus_ids` 明确为整数列表，并增加集合名和备份路径状态。 |
| `backend/tests/test_config.py` | 验证 Milvus 新配置的默认值及边界限制。 |
| `backend/tests/test_import_workflow.py` | 在 PDF、Markdown 完整流程中注入内存入库器，确认最后节点执行并回填主键。 |
| `backend/README.md` | 宣布七节点导入链路已经完整实现，并说明 Milvus 配置、schema、索引、校验、回滚与重复导入边界。 |
| `docs/development-log.md` | 记录第 10 步的目录差异、文件职责、实现方案和真实验证结果。 |

### 节点执行流程

```text
读取已含 item_name、dense_vector、sparse_vector 的 chunks
  ↓
逐项校验文本、UTF-8 长度、向量数值、稠密维度和可选 part
  ↓
连接 MILVUS_URL 指向的 Milvus
  ↓
集合不存在：创建显式 schema 和两套索引
集合已存在：校验字段、维度、自动主键和索引兼容性
  ↓
按 MILVUS_INSERT_BATCH_SIZE 分批写入
  ↓
校验每批 insert_count 和自动生成的 INT64 主键
  ↓
flush 集合，把 chunk_id 和 milvus_ids 回填到状态
  ↓
按配置生成 *_milvus_chunks.json 调试备份
```

### 集合字段和索引

| 字段 | Milvus 类型 | 作用 |
| --- | --- | --- |
| `chunk_id` | INT64，主键，auto_id | 由 Milvus 自动生成的知识片段唯一 ID。 |
| `dense_vector` | FLOAT_VECTOR | 保存百炼生成的固定维度语义向量。 |
| `sparse_vector` | SPARSE_FLOAT_VECTOR | 保存关键词索引及对应权重。 |
| `content` | VARCHAR | 知识片段正文。 |
| `title` | VARCHAR | 当前 Markdown 标题。 |
| `parent_title` | VARCHAR | 上级标题，可为空字符串。 |
| `file_title` | VARCHAR | 来源文档标题。 |
| `item_name` | VARCHAR | 上一步识别并回填的商品或设备名称。 |
| `part` | nullable INT64 | 超长章节被拆分后的可选序号。 |

稠密字段使用 `AUTOINDEX + COSINE`，稀疏字段使用 `SPARSE_INVERTED_INDEX + IP + DAAT_MAXSCORE`。集合关闭动态字段，避免拼写错误的字段静默进入数据库；已有集合必须通过结构和维度校验才允许继续写入。

设计依据：

- [Milvus：Schema Explained](https://milvus.io/docs/v2.6.x/schema.md)
- [Milvus：Sparse Vector](https://milvus.io/docs/v2.6.x/sparse_vector.md)
- [Milvus：Sparse Inverted Index](https://milvus.io/docs/v2.6.x/sparse-inverted-index.md)
- [PyMilvus：Insert](https://milvus.io/api-reference/pymilvus/v2.6.x/MilvusClient/Vector/insert.md)

### 数据校验与失败边界

- 不跳过坏 chunk：正文、文件标题、商品名称或任一向量缺失时，整次入库在写数据库前失败。
- 所有稠密向量必须至少包含两个有限数值并具有相同维度；稀疏向量索引必须是非负整数，权重必须是有限数值。
- 文本按 UTF-8 字节数检查 Milvus VARCHAR 上限，避免中文字符数和实际存储字节数不一致。
- 已有集合维度与当前向量不一致时明确报错，防止修改模型或维度后把不同向量空间混在同一集合。
- 每批响应都必须包含正确的 `insert_count` 和等量 INT64 主键；响应不完整不会被当作成功。
- 如果第二批或后续批次失败，会尽力删除本次已成功写入的前置批次并 flush；如果进程或数据库突然中断，仍不能把这种补偿机制视为跨系统事务。

### 配置与输出

公开配置模板为：

```dotenv
CHUNKS_COLLECTION=knowledge_chunks
MILVUS_METRIC_TYPE=COSINE
MILVUS_INSERT_BATCH_SIZE=100
MILVUS_REQUEST_TIMEOUT_SECONDS=10
MILVUS_BACKUP_ENABLED=true
```

入库成功后，状态新增或更新：

```json
{
  "chunks": [{"chunk_id": 123456789}],
  "milvus_ids": [123456789],
  "milvus_collection_name": "knowledge_chunks",
  "milvus_chunks_path": "D:\\docs\\manual_milvus_chunks.json"
}
```

真实 chunk 仍保留上游生成的其他字段。调试备份已经由现有 `*_chunks.json` 忽略规则排除在 Git 之外；生产环境不需要本地备份时可设置 `MILVUS_BACKUP_ENABLED=false`。

### Python 与虚拟环境

本步继续使用项目内已经恢复稳定的 Python 3.10 环境：

```text
项目解释器：D:\code\xm\掌柜智库\backend\.venv\Scripts\python.exe
Python：3.10.11
新增 Python 包：0
pip check：No broken requirements found
```

PyMilvus 继续使用项目已经固定的 2.6.17，没有重复下载 Python、创建额外虚拟环境或安装本地 AI 模型。

### 测试与真实 Milvus 验证

- Ruff 格式检查通过，共检查 57 个 Python 文件。
- Ruff 代码检查通过。
- pytest 共收集 145 个测试：默认模式 143 个通过，2 个 Docker 集成测试按开关跳过。
- 总覆盖率为 88%；`milvus_storage.py` 为 84%，`import_milvus.py` 为 85%。
- `pip check` 返回 `No broken requirements found`。
- 显式设置 `RUN_INTEGRATION_TESTS=1` 后，五个基础设施健康检查和真实 Milvus 入库测试共 2 个全部通过。
- 真实入库测试创建唯一临时集合，验证两种索引、两批写入、主键回填和字段读取，结束后已删除集合，没有保留测试数据。
- 本步没有调用 MinerU、通义千问或百炼，不消耗任何 AI API 额度；真实 Milvus 测试使用的是合成文本和测试向量。

### 当前边界

- 重复导入同一文档会产生新的 chunk 记录，尚未实现文档级去重、覆盖或版本管理。
- 批次失败使用补偿删除而不是数据库事务；进程被强制终止时可能需要按任务 ID 清理，但当前 schema 还没有保存任务 ID。
- 集合一旦创建，修改 `EMBEDDING_DIMENSION` 或切换不兼容的向量模型必须使用新集合或重建旧集合。
- 导入工作流目前仍只能在 Python 中调用，尚未提供文档上传和任务状态 HTTP API。

### 下一步

第 11 步将把已经完整可运行的文档导入工作流封装为后端服务和 HTTP API，支持上传 PDF 或 Markdown、返回导入结果，并为后续 Vue 管理页面提供调用入口。

### 一句话总结

第 10 步把向量化后的知识片段可靠地批量写入了带稠密与稀疏索引的 Milvus，并把数据库自动主键回填到完整导入工作流。

## 第 11 步：文档上传与导入任务 HTTP API

日期：2026-08-09

### 本步目标

把前十步完成的七节点文档导入工作流封装成可供前端调用的 FastAPI Web 层：客户端上传一个 PDF 或 Markdown 后立即获得任务 ID，再通过状态接口轮询节点进度和最终结果摘要。

课程在这一阶段使用 `UploadFile + BackgroundTasks + 进程内任务字典`。本项目保留相同的交互方式，方便下一步 Vue 页面直接对接，同时补充流式大小限制、内容基础校验、安全存储名、私有 MinIO 原件归档、线程安全任务表、统一错误结构和结果脱敏。

### 与上一步的目录区别

上一步只能从 Python 调用 `run_import_workflow()`，浏览器和 Vue 尚无上传入口。本步新增后的相关目录为：

```text
backend/
├── app/
│   ├── api/routes/
│   │   └── imports.py                         # 新增
│   ├── clients/
│   │   └── minio_document_storage.py          # 新增
│   ├── schemas/
│   │   └── imports.py                         # 新增
│   └── services/
│       ├── __init__.py                        # 新增
│       ├── import_files.py                    # 新增
│       └── import_tasks.py                    # 新增
└── tests/
    ├── integration/
    │   └── test_import_upload.py              # 新增
    ├── test_import_api.py                     # 新增
    ├── test_import_file_service.py            # 新增
    ├── test_import_tasks.py                   # 新增
    └── test_minio_document_storage.py         # 新增
```

同时修改以下已有文件：

```text
.
├── .env.example
├── backend/
│   ├── app/api/router.py
│   ├── app/core/config.py
│   ├── app/main.py
│   ├── app/workflows/importing/base.py
│   ├── app/workflows/importing/graph.py
│   ├── app/workflows/importing/state.py
│   ├── requirements.txt
│   ├── tests/test_config.py
│   ├── tests/test_import_nodes.py
│   └── README.md
└── docs/development-log.md
```

### 每个新文件的作用

| 新文件 | 作用 |
| --- | --- |
| `backend/app/api/routes/imports.py` | 提供 `POST /api/imports` 和 `GET /api/imports/{task_id}`，使用依赖注入调用服务，并把耗时工作流安排到响应后的后台任务。 |
| `backend/app/clients/minio_document_storage.py` | 将原始 PDF/Markdown 写入私有知识桶，校验对象名，按扩展名设置 MIME 类型，不生成公开 URL 或公开桶策略。 |
| `backend/app/schemas/imports.py` | 定义 HTTP 202 上传响应、任务状态响应和安全错误摘要，并负责把内部任务记录转换为外部数据契约。 |
| `backend/app/services/__init__.py` | 建立后端业务服务包。 |
| `backend/app/services/import_files.py` | 完成文件名与扩展名校验、分块落盘、文件内容基础校验、MinIO 归档、后台工作流运行、节点进度回调和失败脱敏。 |
| `backend/app/services/import_tasks.py` | 用锁保护有上限的进程内任务表，记录任务状态、完成节点、当前节点、耗时和最终摘要，不保存正文或向量。 |
| `backend/tests/integration/test_import_upload.py` | 通过真实 FastAPI multipart 请求上传合成 Markdown，确认原件真实进入 Docker MinIO、后台任务完成，并在测试后删除对象。 |
| `backend/tests/test_import_api.py` | 验证 HTTP 202、轮询响应、统一 404/415 错误、结果脱敏和 OpenAPI multipart 描述。 |
| `backend/tests/test_import_file_service.py` | 验证安全文件名、分块大小限制、PDF 文件头、UTF-8 Markdown、原件归档、失败清理、工作流成功与异常脱敏。 |
| `backend/tests/test_import_tasks.py` | 验证任务生命周期、节点进度、结果摘要、失败状态、快照隔离、终态任务淘汰和容量保护。 |
| `backend/tests/test_minio_document_storage.py` | 验证私有知识桶创建、文档 MIME、对象名检查和 MinIO 异常包装。 |

### 已有文件的改动

| 文件 | 本次改动 |
| --- | --- |
| `.env.example` | 增加上传存储目录、最大文件大小、内存任务保留数和原件归档开关。 |
| `backend/app/api/router.py` | 把导入路由挂载到统一 `/api` 路由。 |
| `backend/app/core/config.py` | 加载并限制导入 Web 层四项配置。 |
| `backend/app/main.py` | 在根路径应用信息中公布 `/api/imports`。 |
| `backend/app/workflows/importing/base.py` | 在每个节点开始和完成时触发可选进度回调；回调自身失败只记录日志，不破坏导入业务。 |
| `backend/app/workflows/importing/graph.py` | 让 `run_import_workflow()` 接收并传递可选进度回调。 |
| `backend/app/workflows/importing/state.py` | 给内部图状态增加进度事件和回调类型；未提供回调时原有 Python 调用保持不变。 |
| `backend/requirements.txt` | 增加 FastAPI 解析 multipart 表单所需的 `python-multipart==0.0.32`。 |
| `backend/tests/test_config.py` | 验证上传配置默认值和边界。 |
| `backend/tests/test_import_nodes.py` | 验证真实节点会依次发出 started、completed 事件和毫秒耗时。 |
| `backend/README.md` | 增加接口、PowerShell 调用、配置、安全校验、存储策略和部署边界说明。 |
| `docs/development-log.md` | 记录第 11 步实现、目录差异、依赖和真实 HTTP/MinIO 验证。 |

### HTTP 交互流程

```text
Vue / Swagger 选择 PDF 或 Markdown
  ↓
POST /api/imports（multipart/form-data）
  ↓
校验文件名和扩展名，生成 32 位随机 task_id
  ↓
按 1 MiB 分块写入 backend/temp_data/imports/日期/task_id/source.ext
  ↓
检查真实大小、PDF 文件头或 UTF-8 Markdown
  ↓
按配置归档到私有 MinIO：imports/日期/task_id/source.ext
  ↓
返回 HTTP 202、task_id 和 status_url
  ↓
FastAPI BackgroundTasks 在响应后运行七节点 LangGraph
  ↓
每个节点通过回调更新 started、completed 和 duration_ms
  ↓
Vue 每隔约 1～2 秒 GET /api/imports/{task_id}
  ↓
completed：展示片段数、商品名、Milvus 集合
failed：展示安全的节点名和业务错误
```

### API 数据契约

上传请求：

```http
POST /api/imports
Content-Type: multipart/form-data
file=<一个 PDF、MD 或 Markdown>
```

成功接收返回 HTTP 202：

```json
{
  "message": "文件已接收，正在后台导入",
  "task_id": "c5b73b2397ef469bb5345f5520d60d90",
  "status": "queued",
  "filename": "产品手册.md",
  "status_url": "/api/imports/c5b73b2397ef469bb5345f5520d60d90"
}
```

轮询结果：

```json
{
  "task_id": "c5b73b2397ef469bb5345f5520d60d90",
  "filename": "产品手册.md",
  "status": "completed",
  "done_nodes": ["upload_file", "entry_node", "md_img_node", "document_split_node"],
  "running_node": null,
  "node_durations_ms": {"entry_node": 1.25},
  "chunk_count": 12,
  "item_name": "RS-12 数字万用表",
  "milvus_collection_name": "knowledge_chunks",
  "error": null,
  "created_at": "2026-08-09T08:00:00Z",
  "updated_at": "2026-08-09T08:00:06Z"
}
```

任务状态固定为：

| 状态 | 含义 |
| --- | --- |
| `queued` | 文件已经安全保存，等待后台工作流开始。 |
| `processing` | 工作流正在执行，`running_node` 指向当前节点。 |
| `completed` | Milvus 入库完成，响应包含安全结果摘要。 |
| `failed` | 某节点失败，响应包含节点名和经过控制的错误说明。 |

### 文件与响应安全

- 不使用客户端文件名构造磁盘路径或 MinIO 对象名；原文件统一保存为任务目录内的 `source.ext`，防止 `../` 和绝对路径穿越。
- 不相信客户端声明的 MIME 类型；PDF 要求 `%PDF-` 文件头，Markdown 要求 UTF-8 且不能含 NUL 字节。
- 读取和写入按 1 MiB 分块进行，实际累计字节超过上限立即终止并删除未完成任务目录。
- 空文件、伪造 PDF、非 UTF-8 Markdown、不支持扩展名分别返回明确的 400、413 或 415 业务错误。
- 原始文件进入默认私有知识桶；只有正文实际引用的文档图片仍按第 6 步进入独立公开图片桶。
- 状态接口不返回文档正文、向量、服务器本地路径、MinIO 内部对象名、异常原因链或堆栈。
- 任务表只保留摘要；达到上限时先淘汰最早的完成或失败任务，不会淘汰正在排队或处理的任务。

### 为什么当前使用 BackgroundTasks 和轮询

课程导入节点少、单节点耗时较长且状态变化频率低，前端每 1～2 秒轮询一次比维护 SSE 长连接更简单。FastAPI 官方也把“接收文件后返回 HTTP 202，再在后台处理”列为 `BackgroundTasks` 的典型用法：

- [FastAPI：Request Files](https://fastapi.tiangolo.com/tutorial/request-files/)
- [FastAPI：Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)

但官方同时提示，重型后台工作更适合 Celery 一类独立任务工具。当前实现是为了先完成课程的单机开发闭环，不把它误当成可横向扩容的生产任务系统。

### 配置

公开配置模板新增：

```dotenv
IMPORT_STORAGE_DIR=backend/temp_data/imports
IMPORT_MAX_FILE_SIZE_MB=200
IMPORT_TASK_RETENTION=1000
IMPORT_SOURCE_ARCHIVE_ENABLED=true
```

`IMPORT_STORAGE_DIR` 的相对路径按仓库根目录解析，目录已经被 Git 忽略。200 MB 与当前 MinerU PDF API 单文件限制保持一致；服务仍会按实际读取字节再次限制，不能依赖客户端上报大小。

### Python、依赖与虚拟环境

本步继续使用唯一的项目虚拟环境：

```text
项目解释器：D:\code\xm\掌柜智库\backend\.venv\Scripts\python.exe
Python：3.10.11
新增 Python 包：python-multipart==0.0.32
新增本地 AI 模型：0
pip check：No broken requirements found
```

FastAPI 官方说明接收 multipart 上传需要安装 `python-multipart`。选用检查时 PyPI 的最新稳定版 0.0.32，要求 Python 3.10 及以上。pip 23 在本机连接 PyPI 时发生 TLS 中断，因此从 PyPI 官方 `files.pythonhosted.org` 下载 wheel 到 Git 已忽略的 `.cache`，核对官方 SHA-256 `ff6d3f...1fe2e23` 完全一致后在 `.venv` 本地安装，没有使用第三方镜像或升级其他依赖：

- [PyPI：python-multipart 0.0.32](https://pypi.org/project/python-multipart/)

### 测试与真实 HTTP/MinIO 验证

- Ruff 格式检查通过，共检查 68 个 Python 文件。
- Ruff 代码检查通过。
- pytest 共收集 176 个测试：默认模式 173 个通过，3 个 Docker 集成测试按开关跳过。
- 总覆盖率为 88%；`import_files.py` 为 91%，`import_tasks.py` 为 95%，`imports.py` schema 为 94%。
- `pip check` 返回 `No broken requirements found`。
- 显式设置 `RUN_INTEGRATION_TESTS=1` 后，基础设施、Milvus 入库和 HTTP 上传三项真实集成测试全部通过。
- HTTP 集成测试通过真实 multipart 请求上传不含隐私的合成 Markdown，确认本地文件、私有 MinIO 对象、HTTP 202、后台状态和结果摘要；测试结束后删除了 MinIO 对象和临时目录。
- Web 层单元测试使用注入的无费用工作流，不调用 MinerU、通义千问或百炼，也不产生新的 Milvus 业务记录。

### 当前边界

- 任务状态只存在当前 FastAPI 进程内；服务重启会丢失状态，多个 Uvicorn worker 之间也不会共享任务。
- `BackgroundTasks` 与 API 使用同一进程，不具备持久消息、自动重试、任务抢占或跨服务器调度能力；部署阶段需要独立任务队列。
- 任务状态淘汰不会自动删除本地原件和 MinIO 原件，文件生命周期与定时清理策略尚未实现。
- 当前没有认证和用户隔离，知道 task ID 的调用方即可查询摘要；对公网部署前必须增加登录鉴权和权限检查。
- 重复上传同一文档仍会生成新的 Milvus 数据，文档去重和版本管理尚未实现。

### 下一步

第 12 步将创建 Vue 3 文档导入页面：选择或拖放 PDF/Markdown，调用 `POST /api/imports`，按任务 ID 轮询状态，并用节点进度、耗时、成功结果和失败提示完整展示导入过程。

### 一句话总结

第 11 步为完整导入工作流增加了安全的文件上传、私有原件归档和可轮询任务 API，让下一步 Vue 页面拥有了稳定的后端入口。

## 第 12 步：Vue 3 文档导入工作台

日期：2026-08-09

### 本步目标

用 Vue 3、TypeScript 和 Vite 正式初始化前端工程，替换课程中的单文件 `import.html`，并对接第 11 步的文档上传与任务状态 API。

页面需要完成完整用户闭环：选择或拖放 PDF/Markdown、在浏览器端预先排除明显无效文件、上传一个或多个任务、每 1.5 秒轮询状态、按实际分支展示节点时间线、显示耗时和最终入库摘要，并对后端业务错误与短暂断网给出可恢复反馈。

### 与上一步的目录区别

上一步结束时，`frontend` 只有一份规划说明，没有 `package.json`、源码、测试或构建配置。本步新增后的目录为：

```text
frontend/
├── .env.example
├── index.html
├── package.json
├── package-lock.json
├── tsconfig.json
├── vite.config.ts
└── src/
    ├── App.vue
    ├── env.d.ts
    ├── main.ts
    ├── api/
    │   ├── imports.ts
    │   └── imports.spec.ts
    ├── components/
    │   ├── ImportTaskCard.vue
    │   ├── ImportTaskCard.spec.ts
    │   ├── PipelineOverview.vue
    │   └── UploadDropzone.vue
    ├── composables/
    │   ├── useImportTasks.ts
    │   └── useImportTasks.spec.ts
    ├── styles/
    │   └── main.css
    ├── types/
    │   └── imports.ts
    └── utils/
        ├── imports.ts
        └── imports.spec.ts
```

同时修改以下已有文件：

```text
.
├── README.md
├── docs/development-log.md
└── frontend/README.md
```

### 每个新文件的作用

| 新文件 | 作用 |
| --- | --- |
| `frontend/.env.example` | 提供可选公开 API 基址和本地 Vite 代理目标；只允许放浏览器可见配置，不放密钥。 |
| `frontend/index.html` | 提供 Vue 挂载节点、中文语言、移动端 viewport、页面标题和产品描述。 |
| `frontend/package.json` | 固定 Vue、Vite、TypeScript、类型检查和测试依赖，并定义开发、检查、测试、构建脚本。 |
| `frontend/package-lock.json` | 锁定 178 个直接与传递依赖的精确版本和校验值，保证其他电脑安装结果一致。 |
| `frontend/tsconfig.json` | 开启严格 TypeScript、DOM 类型、Vue/Vite 类型和无产物类型检查。 |
| `frontend/vite.config.ts` | 加载 Vue 单文件组件插件，固定 5173 开发端口，把 `/api` 代理到 FastAPI，并配置 jsdom 测试环境。 |
| `frontend/src/env.d.ts` | 声明 Vite 客户端和 `VITE_API_BASE_URL` 的类型。 |
| `frontend/src/main.ts` | 创建 Vue 应用，挂载根组件并加载全局样式。 |
| `frontend/src/App.vue` | 组合品牌页头、产品说明、上传区、处理路线、错误提示和任务记录，是导入页面入口。 |
| `frontend/src/api/imports.ts` | 封装 multipart 上传和任务查询，安全编码 task ID，解析后端统一错误结构，并隐藏原始错误响应内容。 |
| `frontend/src/api/imports.spec.ts` | 验证 FormData、接口路径、task ID 编码、后端业务错误和无效 JSON 响应。 |
| `frontend/src/components/UploadDropzone.vue` | 提供可点击、可键盘操作、可拖放且支持多文件的 PDF/Markdown 选择区域。 |
| `frontend/src/components/PipelineOverview.vue` | 用四个业务阶段解释从原件归档到 Milvus 入库的完整路线。 |
| `frontend/src/components/ImportTaskCard.vue` | 展示单任务文件信息、状态、进度条、分支节点、单节点耗时、结果摘要、错误和重试操作。 |
| `frontend/src/components/ImportTaskCard.spec.ts` | 验证完成结果、100% 进度、错误提示、重试事件及不显示向量字段。 |
| `frontend/src/composables/useImportTasks.ts` | 管理多任务上传、1.5 秒轮询、AbortController 清理、连续断线重试、结果同步、重新导入和记录清理。 |
| `frontend/src/composables/useImportTasks.spec.ts` | 验证上传后立即轮询、完成摘要回填，以及连续五次连接失败后停止请求。 |
| `frontend/src/styles/main.css` | 实现掌柜智库专属的纸张、账册与墨绿色视觉，覆盖桌面、平板、手机、键盘焦点和减少动画偏好。 |
| `frontend/src/types/imports.ts` | 定义后端响应、任务状态、前端视图任务、错误和节点数据结构。 |
| `frontend/src/utils/imports.ts` | 定义 PDF/Markdown 两条节点路线、文件预校验、分支进度、大小和耗时格式化。 |
| `frontend/src/utils/imports.spec.ts` | 验证两类路线、扩展名识别、空文件、200 MB 上限、进度上限和格式化结果。 |

### 已有文件的改动

| 文件 | 本次改动 |
| --- | --- |
| `README.md` | 增加前端安装、启动地址、代理关系和前端说明入口。 |
| `frontend/README.md` | 从规划文件改为可执行的安装、启动、检查、API 代理、功能和安全配置说明。 |
| `docs/development-log.md` | 记录第 12 步目录差异、组件职责、交互、依赖选择和验证结果。 |

### 页面交互流程

```text
点击“选择文件”或拖放多个文件
  ↓
逐个检查扩展名、空文件和 200 MB 上限
  ├─ 无效：页面顶部显示具体文件错误，不发送请求
  └─ 有效：立即创建本地“正在上传”任务卡
  ↓
POST /api/imports，FormData 字段名为 file
  ↓
收到 HTTP 202：记录 task_id，标记 upload_file 完成
  ↓
立即 GET /api/imports/{task_id}，之后每 1.5 秒轮询
  ↓
根据 done_nodes、running_node 和文件类型计算进度
  ├─ PDF：上传 + 入口 + PDF 解析 + 后续五节点，共 8 步
  └─ Markdown：跳过 PDF 解析，共 7 步
  ↓
completed：展示商品名、知识片段数、Milvus 集合和总节点耗时
failed：展示后端安全错误，可用原 File 对象重新导入
连续五次查询失败：停止轮询并显示连接中断，可重新导入
```

### 组件与状态分工

```text
App.vue
├── UploadDropzone.vue          只负责文件交互，不直接请求 API
├── PipelineOverview.vue        解释静态业务路线
└── ImportTaskCard.vue          只根据一个任务状态渲染
        ↑
useImportTasks.ts               统一管理上传、轮询、重试和列表
        ↓
api/imports.ts                  统一管理 HTTP 地址、FormData 和错误
        ↓
FastAPI /api/imports
```

组件不直接拼接后端错误 HTML，所有内容使用 Vue 文本插值输出。API 层、状态层和展示层分开后，后续更换任务持久化方式或增加鉴权时不需要重写页面组件。

### 视觉与可访问性

- 没有照搬课程的深色科技模板；采用暖白纸张、墨绿、朱砂橙和账册网格，保持“掌柜智库”的业务辨识度。
- 第一屏直接呈现产品价值、文件入口和处理路线，没有增加与当前功能无关的侧边栏或空导航。
- 文件输入保留真实可访问标签；拖放之外始终提供普通按钮，不要求用户必须使用鼠标拖拽。
- 进度条使用原生 `role=progressbar` 及数值属性，错误使用 `role=alert`，任务列表使用 `aria-live`。
- 所有交互元素具有键盘焦点样式；窄屏把两栏改为单栏，任务时间线从四列降到两列。
- 遵循 `prefers-reduced-motion`，用户减少动画时关闭脉冲和过渡。
- 页面不请求外部字体、图片或统计脚本，离线开发环境也能完整显示。

网站构建技能使本步在功能之外同步落实了产品首屏、移动端、键盘操作、状态提示和错误恢复。项目没有 `.openai/hosting.json`，且当前开发流程明确以本地和 GitHub 为阶段交付，因此没有提前创建外部托管站点；部署会在后续服务器步骤统一处理。

### API 与环境配置

默认开发模式使用同源相对地址 `/api`，由 Vite 代理到 FastAPI：

```dotenv
VITE_API_BASE_URL=
VITE_PROXY_TARGET=http://127.0.0.1:8000
```

生产环境同域部署时仍可让 `VITE_API_BASE_URL` 保持为空。只有前后端分属不同域名时才填写公开 API 地址。所有 `VITE_*` 变量都会进入浏览器构建产物，禁止写入 Token、MinIO 密钥或数据库连接串。

### Node、依赖与版本取舍

本步使用现有 Node 环境，没有额外复制运行时：

```text
Node：22.19.0
npm：10.9.3
生产依赖：Vue 3.5.40
开发依赖：Vite 8.1.5、@vitejs/plugin-vue 6.0.8、TypeScript 6.0.2
检查与测试：vue-tsc 3.3.7、Vitest 4.1.10、Vue Test Utils 2.4.11、jsdom 29.1.1
npm audit：0 vulnerabilities
```

检查时 Vue 3.5.40、Vite 8.1.5、Vue 插件 6.0.8 和 Vitest 4.1.10 均为 npm `latest` 稳定标签：

- [npm：Vue](https://www.npmjs.com/package/vue)
- [npm：Vite](https://www.npmjs.com/package/vite)
- [npm：@vitejs/plugin-vue](https://www.npmjs.com/package/@vitejs/plugin-vue)
- [npm：Vitest](https://www.npmjs.com/package/vitest)

没有选用 Vue 3.6 RC。初次尝试 TypeScript 7.0.2 时，构建发现其新的 package exports 与 `vue-tsc 3.3.7` 不兼容，因此固定为 vue-tsc 支持且实际检查通过的 TypeScript 6.0.2。jsdom 30.0.1 要求 Node 22.22.2，而当前为 22.19.0，因此固定为引擎范围兼容的 29.1.1。这里优先保证整个工具链被官方版本约束接受并真实可运行，而不是只追求每个包单独的最大版本号。

### 测试与构建验证

- `vue-tsc --noEmit` 严格类型检查通过。
- Vitest 共 4 个测试文件、13 个测试全部通过。
- Vite 生产构建通过，共转换 23 个模块。
- 构建产物：HTML 0.62 kB，CSS 16.97 kB，JavaScript 77.02 kB；gzip 后分别为 0.44 kB、4.53 kB、30.42 kB。
- `npm audit --audit-level=high` 返回 0 个已知漏洞。
- 后端回归测试 173 个通过，3 个真实 Docker 测试按开关跳过；`pip check` 仍为 `No broken requirements found`。
- `frontend/dist`、`frontend/node_modules` 和本地前端 `.env` 均由 Git 忽略，提交中只包含源码、配置和锁文件。
- 按网站构建验证规则，本步完成代码、类型、单元测试和生产构建；用户未要求浏览器视觉验收，因此没有自动打开浏览器或执行截图点击测试。

### 当前边界

- 页面刷新后任务列表会清空，因为第 11 步后端状态和本步前端列表都尚未持久化。
- 浏览器只能停止轮询，不能取消已经提交到后端的导入工作流；后续需要单独设计取消协议。
- 客户端文件校验用于快速反馈，真正安全边界仍是后端；浏览器的 MIME、文件名和大小都不能替代服务器校验。
- 上传请求目前没有字节级进度事件，任务卡在收到 HTTP 202 前显示固定的 4%；若后续需要大文件实时上传百分比，可改用 XMLHttpRequest 或支持上传进度的客户端。
- 当前只有文档导入页面，知识问答导航仍是禁用提示。

### 下一步

第 13 步将进入课程的查询链路：建立问答请求状态和 LangGraph 骨架，接入商品名确认、查询向量生成与 Milvus 混合召回，为之后的 Vue 知识问答页面准备后端 API。

### 一句话总结

第 12 步用经过类型、测试和生产构建验证的 Vue 3 工作台替换了课程静态导入页，让多文件上传、节点轮询、结果展示和错误恢复形成了完整前端闭环。

## 第 13 步：知识查询骨架与 Milvus 混合召回 API

日期：2026-08-09

### 本步目标

进入课程 day09 的查询链路，把原课程中尚未实现的 `vector_search` 空节点补成可调用的最小召回闭环。本步建立独立查询状态和 LangGraph，依次完成商品名称提取与问题改写、百炼查询向量生成、Milvus 稠密与稀疏向量混合召回，并通过 FastAPI 暴露稳定数据契约。

本步只负责“找到回答可能需要的知识片段”，不提前实现 HyDE、网页搜索、RRF、重排序或最终答案生成，以便后续逐层验证每一种召回与排序策略。

### 与上一步的目录区别

上一步只有完整的文档导入后端和 Vue 导入页面，后端没有查询状态、查询节点、查询服务或查询 API。本步新增后的相关目录为：

```text
backend/
├── app/
│   ├── api/routes/
│   │   └── queries.py
│   ├── clients/
│   │   └── milvus_search.py
│   ├── schemas/
│   │   └── queries.py
│   ├── services/
│   │   └── query_service.py
│   └── workflows/querying/
│       ├── __init__.py
│       ├── base.py
│       ├── exceptions.py
│       ├── graph.py
│       ├── prompts.py
│       ├── state.py
│       └── nodes/
│           ├── __init__.py
│           ├── item_name_confirm.py
│           ├── query_embedding.py
│           └── vector_search.py
└── tests/
    ├── integration/
    │   └── test_query_search.py
    ├── test_milvus_search.py
    ├── test_query_api.py
    ├── test_query_nodes.py
    └── test_query_workflow.py
```

### 每个新文件的作用

| 新文件 | 作用 |
| --- | --- |
| `backend/app/api/routes/queries.py` | 注册 `POST /api/queries/search`，通过依赖注入调用查询服务。 |
| `backend/app/clients/milvus_search.py` | 创建两路 `AnnSearchRequest`、参数化商品名过滤、执行 `WeightedRanker` 混合检索，并把 Milvus 响应解析为安全结果。 |
| `backend/app/schemas/queries.py` | 定义问题、历史消息、结果数量、召回片段和完整响应的 Pydantic 契约。 |
| `backend/app/services/query_service.py` | 把 API 请求转换为图状态，运行查询工作流，并把节点异常映射为统一 HTTP 错误。 |
| `backend/app/workflows/querying/__init__.py` | 对外导出查询状态、工作流创建器和运行入口。 |
| `backend/app/workflows/querying/base.py` | 为查询节点统一记录日志、执行耗时、完成顺序和异常边界。 |
| `backend/app/workflows/querying/exceptions.py` | 区分输入、商品名确认、查询向量和 Milvus 搜索错误。 |
| `backend/app/workflows/querying/graph.py` | 编排三个查询节点并提供同步 `run_query_workflow` 入口。 |
| `backend/app/workflows/querying/prompts.py` | 保存商品名提取、指代消解和独立问题改写的 JSON 提示词。 |
| `backend/app/workflows/querying/state.py` | 定义历史消息、查询向量、召回结果和节点耗时等共享状态，并创建隔离的默认状态。 |
| `backend/app/workflows/querying/nodes/__init__.py` | 集中导出三个查询节点，简化图模块导入。 |
| `backend/app/workflows/querying/nodes/item_name_confirm.py` | 使用通义千问结合最近历史消息提取、去重商品名并改写问题。 |
| `backend/app/workflows/querying/nodes/query_embedding.py` | 使用百炼 `query` 类型生成一组稠密和稀疏查询向量。 |
| `backend/app/workflows/querying/nodes/vector_search.py` | 校验图状态并调用 Milvus 混合检索客户端返回相关知识片段。 |
| `backend/tests/integration/test_query_search.py` | 在显式开关下真实调用通义千问、百炼和本地 Milvus，默认不消耗 API 额度。 |
| `backend/tests/test_milvus_search.py` | 验证两路请求、参数化过滤、结果解析、空集合和异常输入。 |
| `backend/tests/test_query_api.py` | 验证接口响应不泄露向量、请求约束、统一错误和 OpenAPI 契约。 |
| `backend/tests/test_query_nodes.py` | 分别验证历史截断、商品名清洗、问题降级、查询向量和搜索参数传递。 |
| `backend/tests/test_query_workflow.py` | 验证三个节点按顺序执行并累积状态和耗时。 |

### 本步修改的已有文件

| 文件 | 修改内容 |
| --- | --- |
| `.env.example` | 删除没有实际独立服务的 `QUERY_API_PORT`，增加查询数量、权重、历史和商品名配置。 |
| `README.md` | 在后端访问地址中补充导入与知识召回 API。 |
| `backend/README.md` | 增加查询 API、PowerShell 示例、环境配置、数据边界和真实测试额度说明。 |
| `backend/app/api/router.py` | 把查询路由并入现有 `/api` 主路由。 |
| `backend/app/clients/dashscope_embedding.py` | 在原有 `document` 向量接口之外新增 `query` 类型入口，共用请求与响应校验。 |
| `backend/app/core/config.py` | 增加查询限制、混合权重、历史上下文和商品名输出配置，并禁止两种权重同时为零。 |
| `backend/tests/test_config.py` | 增加查询默认配置与权重校验测试。 |
| `backend/tests/test_dashscope_embedding_client.py` | 验证查询向量请求确实发送 `text_type=query`。 |

### 查询流程

```text
START
  ↓
item_name_confirm_node
  ├─ 读取当前问题和最多 10 条客户端历史消息
  ├─ 通义千问提取并去重 item_names
  └─ 生成 rewritten_query
  ↓
query_embedding_node
  └─ 百炼 text-embedding-v4（text_type=query）
       ├─ dense vector
       └─ sparse vector
  ↓
vector_search_node
  ├─ dense_vector / COSINE ─┐
  ├─ sparse_vector / IP ────┤→ WeightedRanker → Top K chunks
  └─ item_name 参数化过滤 ─┘
  ↓
END
```

入库继续使用 `text_type=document`，查询改用 `text_type=query`。两端仍使用同一个 `text-embedding-v4` 模型和相同维度，防止查询向量与底库向量空间不一致。百炼官方文档也将两种文本类型分别定义为用户查询与底库文档：[百炼向量化文档](https://help.aliyun.com/zh/model-studio/embedding)。

Milvus 每次混合检索创建一个稠密请求和一个稀疏请求，再用权重 `0.6 / 0.4` 合并归一化分数。每个权重与一个 ANN 请求对应，做法参考 [Milvus Hybrid Search](https://milvus.io/docs/multi-vector-search.md) 和 [Milvus Reranking](https://milvus.io/docs/reranking.md)。

### HTTP 数据契约

请求示例：

```json
{
  "query": "它怎么测量直流电压？",
  "history": [
    {
      "role": "assistant",
      "content": "这是 RS-12 数字万用表。"
    }
  ],
  "limit": 5
}
```

响应只包含前端后续生成回答需要的检索摘要：

```json
{
  "original_query": "它怎么测量直流电压？",
  "rewritten_query": "RS-12 数字万用表如何测量直流电压？",
  "item_names": ["RS-12 数字万用表"],
  "matches": [
    {
      "chunk_id": 42,
      "score": 0.91,
      "content": "将量程旋钮转到直流电压档。",
      "title": "直流电压测量",
      "parent_title": "基本测量",
      "file_title": "RS-12 用户手册",
      "item_name": "RS-12 数字万用表",
      "part": 1
    }
  ],
  "completed_nodes": [
    "item_name_confirm_node",
    "query_embedding_node",
    "vector_search_node"
  ],
  "node_durations_ms": {}
}
```

稠密向量和稀疏向量只在工作流内部传递，不会进入 HTTP 响应。外部服务错误不会返回响应正文、Token、连接串或 Python 堆栈。

### 输入、过滤与错误边界

- 问题会去除首尾空白，不能为空且最多 2000 字符。
- 历史消息只允许 `user` 和 `assistant`，最多 10 条，每条最多 2000 字符；额外字段直接拒绝。
- 返回数量只能是 1～20，默认 5。
- 商品名会去空白、忽略大小写去重，并受数量和单项长度限制。
- 有商品名时使用 `item_name in {item_names}` 和 `expr_params`，不把用户文本拼接进 Milvus 表达式。
- 没有识别到商品名时仍可在全部知识片段中搜索。
- 集合尚未建立返回 `QUERY_KNOWLEDGE_EMPTY`；AI、Milvus 和其他工作流错误使用不同统一错误码。

### 测试与验证

- Ruff 对 `app` 和 `tests` 的静态检查通过。
- Pytest 共 196 个测试通过，4 个真实集成测试按开关跳过。
- 新测试覆盖 query/document 向量类型差异、商品名清洗、历史截断、混合请求、参数化过滤、工作流顺序、HTTP 契约和安全错误。
- `python -m compileall` 通过，新增模块均可正常导入。
- 本机只读检查确认当前 `knowledge_chunks` 集合尚不存在，因此没有强行调用真实通义千问和百炼，也没有消耗 Token 额度；先通过导入页面成功导入文档后，才具备真实查询条件。
- 真实链路测试必须显式设置 `RUN_INTEGRATION_TESTS=1`，并会使用本机 `.env` 中的 Token 和本地 Docker 基础设施。

### 当前边界

- 本步“商品名确认”是基于 LLM 的提取与改写，还没有把近似名称与知识库中的标准商品名做候选对齐；如果模型返回名称与入库名称不完全一致，精确商品过滤可能得到空结果。
- 历史消息由客户端随请求传入，尚未写入或读取 MongoDB。
- API 当前同步返回召回结果，没有 SSE 流式进度，也没有异步查询任务状态。
- 还没有 HyDE、网页搜索、RRF、多路融合、重排序和答案生成，因此 `matches` 是初步混合召回结果，不是最终答案依据顺序。
- 当前本地没有 `knowledge_chunks` 集合；需要先从 Vue 导入页上传至少一份文档。

### 下一步

第 14 步将完成商品名称候选对齐与澄清分支：从知识库标准名称中匹配 LLM 提取结果，在名称不明确时返回候选项，并开始用 MongoDB 保存会话消息，为后续多轮知识问答做好状态基础。

### 一句话总结

第 13 步打通了商品名提取、查询向量生成、Milvus 稠密稀疏混合召回和 FastAPI 数据契约，让项目第一次具备了从用户问题安全检索知识片段的后端能力。

## 第 14 步：商品名称候选对齐与 MongoDB 会话历史

日期：2026-08-10

### 本步目标

完成课程 day10 的商品名称确认后半段：把通义千问提取的口语名称与知识库中的标准商品名做向量匹配，根据置信区间和分数差决定“直接检索、请用户选择、无法识别”三条路径。同时让查询 API 用 MongoDB 保存会话，使下一轮简短回复能够自动获得上一轮澄清上下文。

本步仍不生成最终回答；商品名确认后继续使用第 13 步的混合召回，名称不明确时则在商品名节点后提前结束，不浪费查询向量和知识片段检索调用。

### 与上一步的目录区别

第 13 步只有 LLM 商品名提取，没有标准名称对齐；历史完全由客户端随请求传入。本步新增目录如下：

```text
backend/
├── app/
│   ├── clients/
│   │   ├── milvus_item_names.py
│   │   └── mongo_history.py
│   └── workflows/querying/
│       └── item_name_alignment.py
└── tests/
    ├── integration/
    │   └── test_mongo_history.py
    ├── test_item_name_alignment.py
    ├── test_milvus_item_names.py
    └── test_mongo_history.py
```

### 每个新文件的作用

| 新文件 | 作用 |
| --- | --- |
| `backend/app/clients/milvus_item_names.py` | 使用商品名查询向量搜索现有知识片段，并按 `item_name` 分组返回不重复的标准名称候选。 |
| `backend/app/clients/mongo_history.py` | 建立 MongoDB 消息索引，保存、读取和按会话删除标准化聊天消息。 |
| `backend/app/workflows/querying/item_name_alignment.py` | 批量生成商品名查询向量，调用候选检索，并执行精确匹配、阈值分区和头部分差决策。 |
| `backend/tests/integration/test_mongo_history.py` | 用随机会话 ID 验证真实 MongoDB 容器的写入、读取和最终清理。 |
| `backend/tests/test_item_name_alignment.py` | 覆盖精确命中、唯一高置信、多高置信分差、中置信候选和低分丢弃。 |
| `backend/tests/test_milvus_item_names.py` | 验证分组检索参数、候选去重、向量校验、空集合和异常响应。 |
| `backend/tests/test_mongo_history.py` | 用内存假集合验证索引、消息元数据、最近消息顺序、会话隔离和非法数据拒绝。 |

### 本步修改的已有文件

| 文件 | 修改内容 |
| --- | --- |
| `.env.example` | 增加 MongoDB 消息集合、超时和商品名对齐阈值；删除未使用的独立商品名集合与最低余弦分配置。 |
| `backend/README.md` | 补充三路决策、会话 ID、响应状态、MongoDB 历史和降级规则。 |
| `backend/app/core/config.py` | 增加候选数量、高中置信阈值、分数差、候选向量权重及 MongoDB 历史配置校验。 |
| `backend/app/schemas/queries.py` | 请求新增可选 `session_id`；响应新增状态、候选、澄清信息和历史持久化标记。 |
| `backend/app/services/query_service.py` | 查询前读取服务端历史，查询后保存用户消息和澄清消息，并区分新会话降级与已有会话读取失败。 |
| `backend/app/workflows/querying/state.py` | 增加提取名称、确认状态、候选列表和澄清文本。 |
| `backend/app/workflows/querying/nodes/item_name_confirm.py` | 在 LLM 提取后调用候选对齐器，并生成确认、澄清或无法识别状态。 |
| `backend/app/workflows/querying/graph.py` | 在商品名节点后增加条件边，只有确认状态才进入查询向量和 Milvus 召回。 |
| `backend/tests/test_config.py` | 增加阈值顺序、候选权重和 MongoDB 默认值测试。 |
| `backend/tests/test_query_api.py` | 增加会话持久化、下一轮历史读取、澄清响应和 MongoDB 故障策略测试。 |
| `backend/tests/test_query_nodes.py` | 为旧节点测试注入候选对齐器，并验证确认和无法识别状态。 |
| `backend/tests/test_query_workflow.py` | 验证确认分支继续召回、澄清分支提前结束和非法路由状态。 |

### 为什么不新建独立商品名向量集合

课程示例使用 `ITEM_NAME_COLLECTION` 保存一份单独的商品名向量。本项目已经在 `knowledge_chunks` 的每条记录中保存了 `item_name` 和混合向量，如果再建一套集合，需要改变导入工作流、额外调用一次向量 API，并处理两套数据的一致性和删除问题。

本步改为在现有知识片段集合上搜索，再使用 Milvus 的 `group_by_field="item_name"` 每个商品只保留一个代表结果。Milvus 官方将 Grouping Search 用于按标量字段聚合片段、增加结果多样性：[Milvus Grouping Search](https://milvus.io/docs/grouping-search.md)。

这项取舍减少了服务器存储、导入调用和维护成本，适合当前 2 核 2 GiB 服务器。代价是候选分数同时受到片段正文影响，不是纯商品名称相似度；后续需要用真实问法数据集校准阈值，如果准确率不足，再升级为独立商品名称索引。

### 商品名称对齐规则

```text
LLM 提取名称
    ↓ 百炼 query 混合向量
Milvus chunks 混合检索 + item_name 分组
    ↓
候选评分
    ├─ 标准名精确命中              → confirmed
    ├─ 只有一个分数 ≥ 0.70         → confirmed
    ├─ 多个分数 ≥ 0.70
    │   ├─ 第一名 - 第二名 ≥ 0.15 → confirmed 第一名
    │   └─ 分数接近                → options
    ├─ 0.60 ≤ 分数 < 0.70          → options
    └─ 分数 < 0.60                 → 丢弃
```

当一个问题提到多个商品时，每个提取名称分别搜索和判断，不使用课程示例中的“所有已确认商品与全局最高分比较”方式。全局过滤可能错误删除用户明确询问的第二个商品；本项目只用头部分差解决同一个提取名称内部的歧义。

如果任一名称仍有候选项，本轮返回 `needs_clarification` 并停止；候选全部确认后才进入查询向量和知识片段召回；没有可用候选则返回 `unrecognized`。

### 查询图变化

```text
START
  ↓
item_name_confirm_node
  ├─ confirmed ─────────────→ query_embedding_node
  │                                  ↓
  │                           vector_search_node → END
  ├─ needs_clarification ─────────────────────────→ END
  └─ unrecognized ─────────────────────────────────→ END
```

澄清和无法识别分支不会调用第二次查询向量 API，也不会执行知识片段搜索。

### MongoDB 会话结构

`chat_messages` 中每条记录包含：

```json
{
  "message_id": "后端生成的随机 ID",
  "session_id": "session-1",
  "role": "user",
  "content": "万用表怎么测电压？",
  "rewritten_query": "万用表怎么测电压？",
  "item_names": [],
  "created_at": "UTC 时间"
}
```

索引：

- `message_id_unique`：保证消息 ID 唯一。
- `session_recent_messages`：按 `session_id + created_at` 快速读取最近消息。

查询成功后写入用户消息；如果本轮返回澄清或无法识别文本，同时写入助手消息。下一轮带同一个 `session_id` 时，MongoDB 历史优先于客户端 `history`；数据库尚无记录时，客户端历史只作为首次会话启动上下文。

已有会话读取失败时返回 `QUERY_HISTORY_UNAVAILABLE`，避免缺少上下文却继续解释“它”“这个”等代词。新会话在 MongoDB 暂时不可用时仍可完成独立问题查询，但响应标记 `history_persisted=false`。

### API 响应变化

确认并召回：

```json
{
  "session_id": "session-1",
  "status": "retrieved",
  "history_persisted": true,
  "item_names": ["RS-12 数字万用表"],
  "item_name_options": [],
  "clarification": "",
  "matches": []
}
```

需要用户选择：

```json
{
  "session_id": "session-1",
  "status": "needs_clarification",
  "history_persisted": true,
  "item_names": [],
  "item_name_options": [
    "RS-12 数字万用表",
    "RS-13 数字万用表"
  ],
  "clarification": "我不确定您指的是哪款产品……",
  "matches": []
}
```

响应示例省略了未变化字段。查询向量、MongoDB `_id`、连接串和异常堆栈仍不会返回。

### 测试与验证

- Ruff 静态检查和格式检查通过。
- Pytest 共 220 个测试通过，5 个显式集成测试默认跳过。
- `pip check` 返回 `No broken requirements found`。
- 单元测试覆盖分组参数、候选去重、全部置信分支、LangGraph 条件边、消息索引、按时序读取、会话连续性和 MongoDB 故障降级。
- 单独开启 `RUN_INTEGRATION_TESTS=1` 后，真实 MongoDB 写入、读取和精确会话清理测试通过；随机测试会话在 `finally` 中删除，没有残留。
- 当前 `knowledge_chunks` 仍不存在，因此商品候选和完整查询真实集成测试继续跳过，需先导入文档。
- 第一次执行旧单元测试时，因为没有给新增对齐依赖注入替身，意外发送了 2 次百炼向量请求；随后已修正测试隔离，单元测试不再访问真实 API。该次测试写入的 1 条 MongoDB 消息也已按精确会话 ID 删除。

### 当前边界

- 0.70、0.60 和 0.15 是课程开发初值，不是经过业务数据集验证的最终阈值。
- 候选使用“商品名查询向量对知识片段向量”，正文会影响分数；真实数据量增长后需要评估独立商品名索引。
- MongoDB 目前保存查询输入和澄清文本；最终回答要等答案生成节点完成后再写入。
- 暂无清空会话历史的 HTTP API，只有客户端层的精确 `delete_session`，避免提前暴露删除操作。
- 前端仍只有文档导入页面，尚未使用 `session_id`、候选按钮或澄清状态。

### 下一步

第 15 步将进入多路召回：保留当前直接向量检索，新增 HyDE 假设文档检索和可关闭的网页检索分支，在 LangGraph 中并行执行并为后续 RRF 融合准备统一结果格式。

### 一句话总结

第 14 步让查询链路能够把口语商品名对齐到知识库标准名称、在歧义时主动澄清，并通过 MongoDB 延续多轮会话上下文。

## 第 15 步：直接向量、HyDE 与网页三路召回

日期：2026-08-10

### 本步目标

还原课程 day11 的三路检索：保留第 13 步已有的直接 Milvus 混合检索，新增 HyDE 假设文档检索和阿里云百炼 WebSearch MCP 检索。商品名确认后先生成一次直接查询向量，再让三个召回节点在 LangGraph 同一阶段并行执行，分别保存结果，为下一步 RRF 融合排序提供输入。

本步仍不生成最终答案，也不把三路结果混成一个排名。网页搜索默认关闭；HyDE 和网页分支出现故障时只标记该分支失败，不中断直接知识库检索。

### 与上一步的目录区别

第 14 步只有直接向量检索。本步新增目录项如下：

```text
backend/
├─ app/
│  ├─ clients/
│  │  └─ dashscope_web_search.py
│  └─ workflows/querying/nodes/
│     ├─ hyde_search.py
│     └─ web_search.py
└─ tests/
   ├─ test_dashscope_web_search.py
   └─ test_multi_retrieval_nodes.py
```

### 每个新文件的作用

| 新文件 | 作用 |
| --- | --- |
| `backend/app/clients/dashscope_web_search.py` | 使用现有 `httpx` 完成 MCP Streamable HTTP 初始化、工具调用、SSE/JSON 响应解析和会话关闭，只返回网页标题、URL 与摘要。 |
| `backend/app/workflows/querying/nodes/hyde_search.py` | 调用通义千问生成 200～300 字假设技术文档，把“问题 + 假设文档”向量化后执行第二路 Milvus 混合检索。 |
| `backend/app/workflows/querying/nodes/web_search.py` | 根据开关调用百炼 `bailian_web_search` 工具；关闭或失败时返回明确状态和空结果。 |
| `backend/tests/test_dashscope_web_search.py` | 用内存 HTTP 传输验证 MCP 握手、会话头、工具参数、SSE/JSON 解析、结果清洗和缺少 Token 的错误。 |
| `backend/tests/test_multi_retrieval_nodes.py` | 验证 HyDE 的生成—向量化—检索链路、故障降级，以及网页分支的开关、问题和数量参数。 |

### 本步修改的已有文件

| 文件 | 修改内容 |
| --- | --- |
| `.env.example` | 增加 HyDE 开关、模型和输出长度，以及 WebSearch MCP 地址、数量和超时配置；网页搜索保持默认关闭。 |
| `backend/README.md` | 说明三路结果字段、API 调用成本、开关和分支降级规则。 |
| `backend/app/clients/qwen_chat.py` | 在原 JSON mode 之外增加普通文本响应方法，供 HyDE 生成自然语言技术文档。 |
| `backend/app/core/config.py` | 增加 HyDE 与网页搜索配置及启用时的模型、URL 校验。 |
| `backend/app/schemas/queries.py` | 保留 `matches` 兼容字段，并新增 `hyde_matches`、`web_matches` 和两个分支状态。 |
| `backend/app/workflows/querying/base.py` | 节点改为只返回状态增量，使并行节点不会重复覆盖整个查询状态。 |
| `backend/app/workflows/querying/state.py` | 增加 HyDE 文档、两路新结果和分支状态，并为完成节点列表和耗时字典配置并行合并器。 |
| `backend/app/workflows/querying/graph.py` | 查询向量节点后同时连接直接向量、HyDE 和网页三个召回节点。 |
| `backend/app/workflows/querying/nodes/item_name_confirm.py` | 所有分支显式返回空商品名、候选或澄清字段，适配状态增量写入。 |
| `backend/app/workflows/querying/nodes/__init__.py` | 导出两个新增召回节点。 |
| `backend/tests/test_query_workflow.py` | 注入三路假客户端，验证并行节点全部执行且状态、耗时正确合并。 |
| `backend/tests/test_qwen_chat_client.py` | 验证普通文本请求不携带 JSON mode 参数。 |
| `backend/tests/test_query_api.py` | 验证 API 安全返回三路结果和分支状态，仍不泄露内部查询向量。 |

### 查询图变化

```text
START
  ↓
item_name_confirm_node
  ├─ needs_clarification / unrecognized ───────────────→ END
  └─ confirmed
       ↓
query_embedding_node
       ├─ vector_search_node ──────────────────────────→ END
       ├─ hyde_search_node ────────────────────────────→ END
       └─ web_search_node（默认关闭）──────────────────→ END
```

`query_embedding_node` 仍只为直接检索生成问题向量。HyDE 节点需要用“问题 + 假设文档”生成自己的第二组查询向量；网页节点直接把改写后的问题交给搜索服务，不使用 Milvus 向量。

### 三路召回分别解决什么问题

- 直接向量检索忠实于用户原问题，成本最低，是主要知识库召回路线。
- HyDE 先猜一段可能的手册答案，再用答案中的专业词和操作描述搜索，适合用户问题过短、口语化或与手册措辞差异较大的情况。
- 网页检索补充知识库外部或较新的信息，但内容质量和稳定性不如内部手册，所以默认关闭并保留独立结果。

三路结果暂不直接相加，因为 Milvus 相似度和网页搜索顺序不是同一种分数。下一步会使用基于名次的 RRF，避免直接比较不同来源的原始分值。

### API 响应变化

```json
{
  "matches": [],
  "hyde_status": "succeeded",
  "hyde_matches": [],
  "web_search_status": "disabled",
  "web_matches": []
}
```

`matches` 继续表示直接 Milvus 结果，避免破坏前一步调用方；两个新数组保留各自来源。`hyde_document` 只在工作流内部传递，不返回给前端，查询向量、Token、MCP 会话 ID 和上游错误正文同样不会暴露。

### 配置与调用成本

```dotenv
QUERY_HYDE_ENABLED=true
QUERY_HYDE_MODEL=qwen-flash
QUERY_HYDE_MAX_OUTPUT_TOKENS=512
WEB_SEARCH_ENABLED=false
MCP_DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/mcp
WEB_SEARCH_COUNT=3
WEB_SEARCH_TIMEOUT_SECONDS=60
```

HyDE 默认开启，每次商品名确认成功的查询会额外调用一次通义千问文本生成和一次百炼向量 API，然后再查询一次本地 Milvus；不需要时可关闭。网页搜索默认不调用任何外部服务，开启后复用 `DASHSCOPE_API_KEY`。这两个节点不加载本地 AI 模型，因此不会明显增加 2 核 2 GiB 服务器的常驻内存，主要增加请求时间、API 次数和少量并发网络连接。

MCP 客户端没有引入课程中的完整 Agent 框架，而是使用项目已有的 `httpx` 实现当前百炼端点使用的 Streamable HTTP 交互，从而减少服务器依赖和安装体积。实现包含协议版本、会话头、初始化通知、工具调用以及关闭会话，并同时兼容 JSON 与 SSE 响应。

### 故障与安全边界

- 直接 Milvus 检索仍是主路径；它失败时沿用统一查询错误处理。
- HyDE 的通义千问、向量或 Milvus 请求失败时，返回 `hyde_status=failed` 和空数组。
- 网页 MCP 连接、鉴权或响应解析失败时，返回 `web_search_status=failed` 和空数组。
- 网页 URL 只接受 `http://` 或 `https://`，无效页面被跳过；上游错误正文和认证信息不会进入 API 响应。
- 网页检索会把改写后的用户问题发送给外部服务，处理敏感问题前应评估数据合规要求。

### 测试与验证

- Ruff 静态检查与格式检查通过。
- Pytest 共 228 个测试通过，5 个显式集成测试默认跳过。
- 新测试全部使用注入客户端或 `httpx.MockTransport`，不依赖真实 Token、网络或知识库集合。
- 完整测试覆盖旧的导入、切分、商品名识别、会话历史和直接检索功能，说明状态增量与并行合并没有破坏前 14 步。
- 第一次运行改造后的旧工作流测试时，测试尚未注入 HyDE 替身，意外执行了 1 次通义千问 HyDE 生成和 1 次百炼向量请求；随后在 Milvus 空集合处降级，没有写入任何知识库或会话数据。测试现已注入三路替身，后续单元测试不再访问真实 API。

### 当前边界

- 当前没有可用的 `knowledge_chunks` 集合，因此本步没有执行三路真实端到端查询；要先通过导入页面导入文档。
- HyDE 生成内容可能有事实错误，它只用于改善召回，不能直接作为最终答案展示。
- 网页结果目前只有搜索摘要，没有抓取和清洗网页全文。
- 三路结果仍是独立列表，存在重复片段，也没有统一名次或相关性阈值。

### 下一步

第 16 步将实现 RRF 多路融合：按直接向量、HyDE 和网页结果各自的名次计算融合分数，去重后形成统一候选列表，为重排和最终答案生成准备上下文。

### 一句话总结

第 15 步让已确认的问题能够并行执行直接知识库、HyDE 扩展和可选网页三路召回，并以可降级、可追踪的独立结果为下一步融合排序做好准备。
