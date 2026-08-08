"""MinerU 精准解析云端 API 客户端。"""

from __future__ import annotations

import shutil
import stat
import tempfile
import time
import zipfile
from collections.abc import Callable
from pathlib import Path, PurePosixPath
from typing import Any
from uuid import uuid4

import httpx


class MinerUApiError(Exception):
    """MinerU API 请求、任务或结果文件不符合预期。"""


class MinerUApiClient:
    """上传本地 PDF，轮询 MinerU 任务并下载完整解析结果。"""

    def __init__(
        self,
        *,
        base_url: str,
        token: str,
        model_version: str,
        request_timeout_seconds: float,
        poll_interval_seconds: float,
        task_timeout_seconds: int,
        transport: httpx.BaseTransport | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token.strip()
        self.model_version = model_version
        self.request_timeout_seconds = request_timeout_seconds
        self.poll_interval_seconds = poll_interval_seconds
        self.task_timeout_seconds = task_timeout_seconds
        self.transport = transport
        self.sleeper = sleeper
        self.clock = clock

    def convert(self, pdf_path: Path, output_directory: Path) -> Path:
        """把 PDF 交给 MinerU API，并返回下载后的 Markdown 路径。"""

        if not self.token:
            raise MinerUApiError("未配置 MINERU_API_TOKEN")
        if not self.base_url.startswith(("https://", "http://")):
            raise MinerUApiError("MINERU_BASE_URL 必须是 HTTP 或 HTTPS 地址")

        output_directory.mkdir(parents=True, exist_ok=True)
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            with httpx.Client(
                timeout=self.request_timeout_seconds,
                transport=self.transport,
                follow_redirects=True,
            ) as client:
                batch_id, upload_url = self._request_upload_url(client, headers, pdf_path)
                self._upload_file(client, upload_url, pdf_path)
                archive_url = self._wait_for_result(client, headers, batch_id, pdf_path.name)
                archive_path = self._download_archive(client, archive_url, output_directory)
        except httpx.HTTPError as exc:
            raise MinerUApiError(f"MinerU API 网络请求失败：{exc}") from exc
        except OSError as exc:
            raise MinerUApiError(f"MinerU 结果文件处理失败：{exc}") from exc

        try:
            result_directory = output_directory / pdf_path.stem / "auto"
            self._extract_archive(archive_path, result_directory)
            return self._find_markdown(result_directory)
        finally:
            archive_path.unlink(missing_ok=True)

    def _request_upload_url(
        self,
        client: httpx.Client,
        headers: dict[str, str],
        pdf_path: Path,
    ) -> tuple[str, str]:
        response = client.post(
            f"{self.base_url}/file-urls/batch",
            headers=headers,
            json={
                "files": [{"name": pdf_path.name, "data_id": uuid4().hex}],
                "model_version": self.model_version,
            },
        )
        data = self._response_data(response, "申请文件上传地址")
        batch_id = data.get("batch_id")
        file_urls = data.get("file_urls")
        if not isinstance(batch_id, str) or not batch_id:
            raise MinerUApiError("MinerU API 未返回 batch_id")
        if not isinstance(file_urls, list) or len(file_urls) != 1:
            raise MinerUApiError("MinerU API 未返回唯一的文件上传地址")
        upload_url = file_urls[0]
        if not isinstance(upload_url, str) or not upload_url:
            raise MinerUApiError("MinerU API 返回的文件上传地址无效")
        return batch_id, upload_url

    def _upload_file(self, client: httpx.Client, upload_url: str, pdf_path: Path) -> None:
        with pdf_path.open("rb") as source:
            response = client.put(
                upload_url,
                headers={"Content-Length": str(pdf_path.stat().st_size)},
                content=source,
            )
        response.raise_for_status()

    def _wait_for_result(
        self,
        client: httpx.Client,
        headers: dict[str, str],
        batch_id: str,
        file_name: str,
    ) -> str:
        deadline = self.clock() + self.task_timeout_seconds
        while self.clock() < deadline:
            response = client.get(
                f"{self.base_url}/extract-results/batch/{batch_id}",
                headers=headers,
            )
            data = self._response_data(response, "查询解析结果")
            result = self._select_result(data, file_name)
            state = result.get("state")

            if state == "done":
                archive_url = result.get("full_zip_url")
                if isinstance(archive_url, str) and archive_url:
                    return archive_url
                raise MinerUApiError("MinerU 任务已完成，但没有返回结果压缩包")
            if state == "failed":
                reason = result.get("err_msg") or "没有错误说明"
                raise MinerUApiError(f"MinerU 解析失败：{reason}")
            if state not in {"waiting-file", "pending", "running", "converting"}:
                raise MinerUApiError(f"MinerU 返回未知任务状态：{state}")

            self.sleeper(self.poll_interval_seconds)

        raise MinerUApiError(f"MinerU 解析超过 {self.task_timeout_seconds} 秒")

    def _download_archive(
        self,
        client: httpx.Client,
        archive_url: str,
        output_directory: Path,
    ) -> Path:
        archive_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                suffix=".zip",
                prefix="mineru-",
                dir=output_directory,
                delete=False,
            ) as temporary_file:
                archive_path = Path(temporary_file.name)
                with client.stream("GET", archive_url) as response:
                    response.raise_for_status()
                    for chunk in response.iter_bytes():
                        temporary_file.write(chunk)
        except Exception:
            if archive_path is not None:
                archive_path.unlink(missing_ok=True)
            raise
        if archive_path is None:
            raise MinerUApiError("无法创建 MinerU 临时结果文件")
        return archive_path

    def _extract_archive(self, archive_path: Path, destination: Path) -> None:
        destination.mkdir(parents=True, exist_ok=True)
        destination_root = destination.resolve()

        try:
            with zipfile.ZipFile(archive_path) as archive:
                for member in archive.infolist():
                    mode = member.external_attr >> 16
                    if stat.S_ISLNK(mode):
                        raise MinerUApiError("MinerU 结果压缩包包含不允许的符号链接")

                    archive_name = member.filename.replace("\\", "/")
                    relative_path = PurePosixPath(archive_name)
                    target_path = (destination / Path(*relative_path.parts)).resolve()
                    if not target_path.is_relative_to(destination_root):
                        raise MinerUApiError("MinerU 结果压缩包包含不安全路径")

                    if member.is_dir():
                        target_path.mkdir(parents=True, exist_ok=True)
                        continue

                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(member) as source, target_path.open("wb") as target:
                        shutil.copyfileobj(source, target)
        except zipfile.BadZipFile as exc:
            raise MinerUApiError("MinerU 返回的结果不是有效 ZIP 文件") from exc

    def _find_markdown(self, result_directory: Path) -> Path:
        full_markdown = result_directory / "full.md"
        if full_markdown.is_file():
            return full_markdown.resolve()

        candidates = sorted(result_directory.rglob("*.md"))
        if len(candidates) == 1:
            return candidates[0].resolve()
        raise MinerUApiError("MinerU 结果压缩包中没有找到唯一的 Markdown 文件")

    def _response_data(self, response: httpx.Response, operation: str) -> dict[str, Any]:
        response.raise_for_status()
        try:
            payload = response.json()
        except ValueError as exc:
            raise MinerUApiError(f"MinerU {operation}响应不是有效 JSON") from exc

        if not isinstance(payload, dict):
            raise MinerUApiError(f"MinerU {operation}响应格式错误")
        if payload.get("code") != 0:
            message = payload.get("msg") or "没有错误说明"
            raise MinerUApiError(f"MinerU {operation}失败：{message}")
        data = payload.get("data")
        if not isinstance(data, dict):
            raise MinerUApiError(f"MinerU {operation}响应缺少 data")
        return data

    def _select_result(self, data: dict[str, Any], file_name: str) -> dict[str, Any]:
        results = data.get("extract_result")
        if not isinstance(results, list) or not results:
            raise MinerUApiError("MinerU 查询响应中没有解析任务")

        matching = [
            item
            for item in results
            if isinstance(item, dict) and item.get("file_name") == file_name
        ]
        if len(matching) == 1:
            return matching[0]
        if len(results) == 1 and isinstance(results[0], dict):
            return results[0]
        raise MinerUApiError(f"MinerU 查询响应中无法定位文件：{file_name}")
