# Deploy

该目录用于本地开发和部署配置。

下一步会加入 Docker Compose，并管理以下五个容器：

- etcd：Milvus 元数据存储。
- MinIO：Milvus 依赖及文档图片对象存储。
- Milvus：稠密/稀疏向量数据库。
- Attu：Milvus 可视化管理界面。
- MongoDB：会话历史及辅助数据存储。

容器数据将写入 Git 忽略的持久化目录或命名卷，不进入代码仓库。
