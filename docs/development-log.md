# 掌柜智库开发笔记

本文档按实施步骤记录实际改动、目录差异、文件职责、验证结果和后续事项。每完成一步，都会在文档末尾增加一个独立章节。

## 文档分工

- 根目录 `README.md` 面向项目使用者，只维护项目介绍、结构、运行方式和安全约定等稳定内容。
- 本开发笔记面向开发过程，记录逐步改动、本机环境、前后目录差异、文件职责、验证结果和 Git 提交。
- 开发进度与机器相关问题不再写入根目录 README。

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
