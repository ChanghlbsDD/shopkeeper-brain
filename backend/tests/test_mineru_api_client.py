import io
import json
import zipfile
from pathlib import Path

import httpx
import pytest

from app.clients.mineru_api import MinerUApiClient, MinerUApiError


def create_zip(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def create_client(
    handler,
    *,
    task_timeout_seconds: int = 30,
    sleeper=lambda _seconds: None,
    clock=lambda: 0,
) -> MinerUApiClient:
    return MinerUApiClient(
        base_url="https://mineru.test/api/v4",
        token="secret-token",
        model_version="vlm",
        request_timeout_seconds=10,
        poll_interval_seconds=1,
        task_timeout_seconds=task_timeout_seconds,
        transport=httpx.MockTransport(handler),
        sleeper=sleeper,
        clock=clock,
    )


def test_convert_uploads_polls_downloads_and_extracts(tmp_path: Path) -> None:
    pdf_path = tmp_path / "manual.pdf"
    pdf_path.write_bytes(b"pdf-content")
    archive_bytes = create_zip(
        {
            "full.md": b"# Converted",
            "images/page.jpg": b"image-content",
        }
    )
    poll_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal poll_count
        if request.method == "POST":
            assert request.headers["Authorization"] == "Bearer secret-token"
            payload = json.loads(request.content)
            assert payload["files"][0]["name"] == "manual.pdf"
            assert payload["model_version"] == "vlm"
            return httpx.Response(
                200,
                json={
                    "code": 0,
                    "data": {
                        "batch_id": "batch-1",
                        "file_urls": ["https://upload.test/manual.pdf"],
                    },
                },
            )
        if request.method == "PUT":
            assert request.url == "https://upload.test/manual.pdf"
            assert request.headers["Content-Length"] == str(len(b"pdf-content"))
            assert request.content == b"pdf-content"
            return httpx.Response(200)
        if request.url.host == "mineru.test":
            poll_count += 1
            state = "running" if poll_count == 1 else "done"
            result = {"file_name": "manual.pdf", "state": state, "err_msg": ""}
            if state == "done":
                result["full_zip_url"] = "https://download.test/result.zip"
            return httpx.Response(
                200,
                json={"code": 0, "data": {"extract_result": [result]}},
            )
        return httpx.Response(200, content=archive_bytes)

    markdown_path = create_client(handler).convert(pdf_path, tmp_path / "output")

    assert markdown_path.read_text(encoding="utf-8") == "# Converted"
    assert (markdown_path.parent / "images/page.jpg").read_bytes() == b"image-content"
    assert poll_count == 2
    assert list((tmp_path / "output").glob("mineru-*.zip")) == []


def test_convert_requires_token(tmp_path: Path) -> None:
    client = MinerUApiClient(
        base_url="https://mineru.test/api/v4",
        token="",
        model_version="vlm",
        request_timeout_seconds=10,
        poll_interval_seconds=1,
        task_timeout_seconds=30,
    )

    with pytest.raises(MinerUApiError, match="MINERU_API_TOKEN"):
        client.convert(tmp_path / "manual.pdf", tmp_path / "output")


def test_convert_reports_api_business_error(tmp_path: Path) -> None:
    pdf_path = tmp_path / "manual.pdf"
    pdf_path.write_bytes(b"pdf-content")

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"code": -60018, "msg": "每日任务数量已达上限"})

    with pytest.raises(MinerUApiError, match="每日任务数量已达上限"):
        create_client(handler).convert(pdf_path, tmp_path / "output")


def test_convert_reports_failed_task(tmp_path: Path) -> None:
    pdf_path = tmp_path / "manual.pdf"
    pdf_path.write_bytes(b"pdf-content")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(
                200,
                json={
                    "code": 0,
                    "data": {
                        "batch_id": "batch-1",
                        "file_urls": ["https://upload.test/manual.pdf"],
                    },
                },
            )
        if request.method == "PUT":
            return httpx.Response(200)
        return httpx.Response(
            200,
            json={
                "code": 0,
                "data": {
                    "extract_result": [
                        {
                            "file_name": "manual.pdf",
                            "state": "failed",
                            "err_msg": "文件页数超过限制",
                        }
                    ]
                },
            },
        )

    with pytest.raises(MinerUApiError, match="文件页数超过限制"):
        create_client(handler).convert(pdf_path, tmp_path / "output")


def test_convert_reports_task_timeout(tmp_path: Path) -> None:
    pdf_path = tmp_path / "manual.pdf"
    pdf_path.write_bytes(b"pdf-content")
    ticks = iter([0.0, 0.0, 1.0])

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(
                200,
                json={
                    "code": 0,
                    "data": {
                        "batch_id": "batch-1",
                        "file_urls": ["https://upload.test/manual.pdf"],
                    },
                },
            )
        if request.method == "PUT":
            return httpx.Response(200)
        return httpx.Response(
            200,
            json={
                "code": 0,
                "data": {
                    "extract_result": [
                        {"file_name": "manual.pdf", "state": "pending", "err_msg": ""}
                    ]
                },
            },
        )

    with pytest.raises(MinerUApiError, match="解析超过 1 秒"):
        create_client(
            handler,
            task_timeout_seconds=1,
            clock=lambda: next(ticks),
        ).convert(pdf_path, tmp_path / "output")


def test_extract_archive_rejects_parent_directory(tmp_path: Path) -> None:
    archive_path = tmp_path / "unsafe.zip"
    archive_path.write_bytes(create_zip({"../outside.md": b"unsafe"}))
    client = create_client(lambda _request: httpx.Response(500))

    with pytest.raises(MinerUApiError, match="不安全路径"):
        client._extract_archive(archive_path, tmp_path / "output")

    assert not (tmp_path / "outside.md").exists()
