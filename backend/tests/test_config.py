import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_cors_origins_are_split_and_trimmed() -> None:
    settings = Settings(
        _env_file=None,
        cors_origins="http://localhost:5173, http://127.0.0.1:5173",
    )

    assert settings.cors_origin_list == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


def test_health_timeout_must_be_positive() -> None:
    settings = Settings(_env_file=None, infra_health_timeout_seconds=1.5)

    assert settings.infra_health_timeout_seconds == 1.5

    with pytest.raises(ValidationError):
        Settings(_env_file=None, infra_health_timeout_seconds=0)


def test_import_api_storage_and_limits() -> None:
    settings = Settings(_env_file=None)

    assert settings.import_storage_dir.name == "imports"
    assert settings.import_max_file_size_mb == 200
    assert settings.import_task_retention == 1000
    assert settings.import_source_archive_enabled is True

    with pytest.raises(ValidationError):
        Settings(_env_file=None, import_max_file_size_mb=0)

    with pytest.raises(ValidationError):
        Settings(_env_file=None, import_task_retention=9)


def test_mineru_timeout_and_model_version_are_validated() -> None:
    settings = Settings(_env_file=None, mineru_task_timeout_seconds=60)

    assert settings.mineru_model_version == "vlm"
    assert settings.mineru_task_timeout_seconds == 60

    with pytest.raises(ValidationError):
        Settings(_env_file=None, mineru_task_timeout_seconds=0)

    with pytest.raises(ValidationError):
        Settings(_env_file=None, mineru_model_version="unsupported")


def test_minio_images_use_a_separate_public_bucket() -> None:
    settings = Settings(_env_file=None)

    assert settings.minio_image_bucket_name == "shopkeeper-images"
    assert settings.minio_public_base_url == "http://localhost:9000"
    assert settings.minio_image_public_read is True


def test_document_chunk_lengths_are_validated() -> None:
    settings = Settings(
        _env_file=None,
        document_chunk_max_length=1000,
        document_chunk_min_length=200,
    )

    assert settings.document_chunk_backup_enabled is True

    with pytest.raises(ValidationError, match="MAX_LENGTH"):
        Settings(
            _env_file=None,
            document_chunk_max_length=200,
            document_chunk_min_length=200,
        )


def test_qwen_item_name_defaults_and_limits() -> None:
    settings = Settings(_env_file=None)

    assert settings.openai_api_base == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert settings.item_model == "qwen-flash"
    assert settings.item_name_max_output_tokens == 128
    assert settings.item_name_chunk_count == 3
    assert settings.item_name_context_max_length == 2500

    with pytest.raises(ValidationError):
        Settings(_env_file=None, item_name_chunk_count=0)


def test_cloud_embedding_defaults_and_limits() -> None:
    settings = Settings(_env_file=None)

    assert settings.dashscope_api_base == "https://dashscope.aliyuncs.com/api/v1"
    assert settings.embedding_model == "text-embedding-v4"
    assert settings.embedding_dimension == 1024
    assert settings.embedding_batch_size == 10
    assert settings.embedding_backup_enabled is True

    with pytest.raises(ValidationError):
        Settings(_env_file=None, embedding_batch_size=11)

    with pytest.raises(ValidationError):
        Settings(_env_file=None, embedding_dimension=1000)


def test_milvus_import_defaults_and_limits() -> None:
    settings = Settings(_env_file=None)

    assert settings.chunks_collection == "knowledge_chunks"
    assert settings.milvus_metric_type == "COSINE"
    assert settings.milvus_insert_batch_size == 100
    assert settings.milvus_request_timeout_seconds == 10
    assert settings.milvus_backup_enabled is True

    with pytest.raises(ValidationError):
        Settings(_env_file=None, milvus_insert_batch_size=1001)


def test_query_defaults_and_vector_weights_are_validated() -> None:
    settings = Settings(_env_file=None)

    assert settings.query_search_limit == 5
    assert settings.query_dense_weight == 0.6
    assert settings.query_sparse_weight == 0.4
    assert settings.query_history_max_messages == 10
    assert settings.query_item_name_max_count == 5
    assert settings.query_item_name_candidate_limit == 5
    assert settings.query_item_name_high_confidence == 0.7
    assert settings.query_item_name_mid_confidence == 0.6
    assert settings.query_item_name_score_gap == 0.15
    assert settings.query_item_name_dense_weight == 0.5
    assert settings.query_item_name_sparse_weight == 0.5
    assert settings.mongo_chat_collection == "chat_messages"
    assert settings.mongo_request_timeout_seconds == 5
    assert settings.query_hyde_enabled is True
    assert settings.query_hyde_model == "qwen-flash"
    assert settings.web_search_enabled is False
    assert settings.web_search_count == 3
    assert settings.query_rrf_k == 60
    assert settings.query_rrf_max_results == 10
    assert settings.query_rrf_vector_weight == 1.0
    assert settings.query_rrf_hyde_weight == 1.0

    with pytest.raises(ValidationError, match="不能同时为 0"):
        Settings(
            _env_file=None,
            query_dense_weight=0,
            query_sparse_weight=0,
        )

    with pytest.raises(ValidationError, match="中置信阈值"):
        Settings(
            _env_file=None,
            query_item_name_high_confidence=0.6,
            query_item_name_mid_confidence=0.7,
        )

    with pytest.raises(ValidationError, match="商品名稠密和稀疏"):
        Settings(
            _env_file=None,
            query_item_name_dense_weight=0,
            query_item_name_sparse_weight=0,
        )

    with pytest.raises(ValidationError, match="QUERY_HYDE_MODEL"):
        Settings(_env_file=None, query_hyde_enabled=True, query_hyde_model=" ")

    with pytest.raises(ValidationError, match="MCP_DASHSCOPE_BASE_URL"):
        Settings(
            _env_file=None,
            web_search_enabled=True,
            mcp_dashscope_base_url="not-a-url",
        )

    with pytest.raises(ValidationError, match="RRF"):
        Settings(
            _env_file=None,
            query_rrf_vector_weight=0,
            query_rrf_hyde_weight=0,
        )
