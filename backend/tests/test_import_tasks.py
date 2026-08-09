from pathlib import Path

import pytest

from app.services.import_tasks import ImportTaskStore, ImportTaskStoreError


def test_task_store_tracks_progress_and_result_summary(tmp_path: Path) -> None:
    store = ImportTaskStore(max_tasks=10)
    source = tmp_path / "source.md"
    store.create("task-1", "手册.md", source)
    store.mark_upload_completed("task-1", "imports/task-1/source.md")
    store.mark_processing("task-1")
    store.mark_node_started("task-1", "entry_node")
    store.mark_node_completed("task-1", "entry_node", 12.5)
    store.mark_completed(
        "task-1",
        {
            "chunks": [{"chunk_id": 1}, {"chunk_id": 2}],
            "item_name": "RS-12 数字万用表",
            "milvus_collection_name": "knowledge_chunks",
        },
    )

    task = store.get("task-1")

    assert task.status == "completed"
    assert task.done_nodes == ("upload_file", "entry_node")
    assert task.running_node is None
    assert task.node_durations_ms == {"entry_node": 12.5}
    assert task.chunk_count == 2
    assert task.item_name == "RS-12 数字万用表"
    assert task.milvus_collection_name == "knowledge_chunks"


def test_task_store_tracks_safe_failure(tmp_path: Path) -> None:
    store = ImportTaskStore(max_tasks=10)
    store.create("task-1", "manual.md", tmp_path / "source.md")

    store.mark_failed("task-1", node_name="document_split_node", message="没有有效片段")

    task = store.get("task-1")
    assert task.status == "failed"
    assert task.error_node == "document_split_node"
    assert task.error_message == "没有有效片段"


def test_task_store_evicts_oldest_terminal_task(tmp_path: Path) -> None:
    store = ImportTaskStore(max_tasks=2)
    store.create("old", "old.md", tmp_path / "old.md")
    store.mark_failed("old", node_name=None, message="failed")
    store.create("active", "active.md", tmp_path / "active.md")

    store.create("new", "new.md", tmp_path / "new.md")

    with pytest.raises(ImportTaskStoreError, match="不存在"):
        store.get("old")
    assert store.get("active").status == "queued"
    assert store.get("new").status == "queued"


def test_task_store_rejects_capacity_when_all_tasks_are_active(tmp_path: Path) -> None:
    store = ImportTaskStore(max_tasks=1)
    store.create("active", "active.md", tmp_path / "active.md")

    with pytest.raises(ImportTaskStoreError, match="任务过多"):
        store.create("new", "new.md", tmp_path / "new.md")


def test_task_store_returns_isolated_duration_mapping(tmp_path: Path) -> None:
    store = ImportTaskStore(max_tasks=2)
    store.create("task", "manual.md", tmp_path / "source.md")
    snapshot = store.get("task")
    snapshot.node_durations_ms["fake"] = 1

    assert store.get("task").node_durations_ms == {}
