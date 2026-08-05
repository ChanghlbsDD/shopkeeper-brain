# Deploy

该目录保存掌柜智库的本地基础设施配置。`docker-compose.yml` 管理以下五个容器：

| 服务 | 固定镜像 | 用途 |
| --- | --- | --- |
| etcd | `quay.io/coreos/etcd:v3.5.25` | 保存 Milvus 元数据。 |
| MinIO | `minio/minio:RELEASE.2024-12-18T13-15-44Z` | 保存 Milvus 对象及文档图片。 |
| Milvus | `milvusdb/milvus:v2.6.20` | 稠密、稀疏及混合向量检索。 |
| Attu | `zilliz/attu:v2.6.5` | Milvus 2.6 管理界面。 |
| MongoDB | `mongo:7.0.16` | 保存会话历史和辅助数据。 |

## 启动

在仓库根目录执行：

```powershell
Copy-Item .env.example .env
# 首次启动前编辑 .env 中带有 change-me 的密码
docker compose --env-file .env -f deploy/docker-compose.yml up -d
```

查看状态和日志：

```powershell
docker compose --env-file .env -f deploy/docker-compose.yml ps
docker compose --env-file .env -f deploy/docker-compose.yml logs -f
```

停止容器但保留数据：

```powershell
docker compose --env-file .env -f deploy/docker-compose.yml stop
```

删除容器但保留命名卷数据：

```powershell
docker compose --env-file .env -f deploy/docker-compose.yml down
```

删除命名卷会永久清除已导入知识和会话历史，因此开发流程不会提供默认的自动清库命令。

## 端口

所有端口默认绑定到 `127.0.0.1`，不会直接暴露到局域网：

| 服务 | 默认地址 |
| --- | --- |
| Attu | `http://localhost:7000` |
| MinIO API | `http://localhost:9000` |
| MinIO 控制台 | `http://localhost:9001` |
| Milvus gRPC | `localhost:19530` |
| Milvus WebUI/健康端口 | `http://localhost:9091` |
| MongoDB | `localhost:27017` |

## 数据持久化

Compose 使用 `etcd-data`、`minio-data`、`milvus-data`、`mongo-data` 四个命名卷。停止或重建容器不会删除这些数据。

Attu 2.6 的连接信息保存在浏览器本地存储，不需要单独的数据卷。Attu 3 只支持开源 Milvus 3.x，不能与本项目的 Milvus 2.6 混用。
