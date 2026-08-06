from app.workflows.importing.state import create_import_state


def test_import_states_do_not_share_mutable_defaults() -> None:
    first = create_import_state("first.pdf")
    second = create_import_state("second.pdf")

    first["chunks"].append({"text": "only in first"})
    first["node_durations_ms"]["entry_node"] = 1.0

    assert second["chunks"] == []
    assert second["node_durations_ms"] == {}


def test_import_state_accepts_initial_overrides() -> None:
    state = create_import_state("manual.md", file_dir="output", task_id="task-001")

    assert state["import_file_path"] == "manual.md"
    assert state["file_dir"] == "output"
    assert state["task_id"] == "task-001"
