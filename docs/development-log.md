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
