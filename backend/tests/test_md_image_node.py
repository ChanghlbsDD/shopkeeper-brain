from pathlib import Path

import pytest

from app.clients.minio_storage import MinioImageStorageError
from app.workflows.importing.exceptions import MarkdownImageError
from app.workflows.importing.nodes import MarkdownImageNode
from app.workflows.importing.state import create_import_state


class FakeImageStorage:
    def __init__(self) -> None:
        self.uploads: list[tuple[Path, str]] = []

    def upload(self, image_path: Path, object_name: str) -> str:
        self.uploads.append((image_path, object_name))
        return f"https://assets.example.com/{object_name}"


def create_markdown_state(markdown_path: Path, *, title: str = "商品手册") -> dict[str, object]:
    state: dict[str, object] = create_import_state(str(markdown_path))
    state.update({"md_path": str(markdown_path), "file_title": title})
    return state


def test_uploads_local_images_once_and_preserves_original_markdown(tmp_path: Path) -> None:
    images_directory = tmp_path / "images"
    images_directory.mkdir()
    image_path = images_directory / "product.png"
    image_path.write_bytes(b"png")
    original_content = (
        "# 手册\n\n"
        "![正面](images/product.png)\n"
        '![重复](./images/product.png "详情")\n'
        "![远程](https://example.com/remote.png)\n"
    )
    markdown_path = tmp_path / "full.md"
    markdown_path.write_text(original_content, encoding="utf-8")
    storage = FakeImageStorage()

    result = MarkdownImageNode(storage=storage)(create_markdown_state(markdown_path))

    assert len(storage.uploads) == 1
    assert storage.uploads[0][0] == image_path.resolve()
    assert storage.uploads[0][1].startswith("documents/商品手册-")
    assert storage.uploads[0][1].endswith("/images/product.png")
    assert result["md_path"].endswith("full_images.md")
    assert Path(result["md_path"]).read_text(encoding="utf-8") == result["md_content"]
    assert "https://assets.example.com/documents/" in result["md_content"]
    assert "https://example.com/remote.png" in result["md_content"]
    assert ' "详情"' in result["md_content"]
    assert markdown_path.read_text(encoding="utf-8") == original_content
    assert len(result["uploaded_image_urls"]) == 2


def test_markdown_without_local_images_does_not_connect_to_minio(tmp_path: Path) -> None:
    markdown_path = tmp_path / "remote-only.md"
    content = (
        "![远程图片](https://example.com/image.png)\n![协议相对地址](//cdn.example.com/image.png)"
    )
    markdown_path.write_text(content, encoding="utf-8")
    storage = FakeImageStorage()

    result = MarkdownImageNode(storage=storage)(create_markdown_state(markdown_path))

    assert storage.uploads == []
    assert result["md_path"] == str(markdown_path)
    assert result["md_content"] == content
    assert result["uploaded_image_urls"] == {}


@pytest.mark.parametrize(
    ("target", "message"),
    [
        ("images/missing.png", "图片不存在"),
        ("images/diagram.svg", "不支持的本地图片格式"),
        ("../outside.png", "图片路径超出 Markdown 目录"),
    ],
)
def test_rejects_invalid_local_image_references(
    tmp_path: Path,
    target: str,
    message: str,
) -> None:
    outside_image = tmp_path.parent / "outside.png"
    outside_image.write_bytes(b"outside")
    images_directory = tmp_path / "images"
    images_directory.mkdir()
    (images_directory / "diagram.svg").write_text("<svg/>", encoding="utf-8")
    markdown_path = tmp_path / "invalid.md"
    markdown_path.write_text(f"![图片]({target})", encoding="utf-8")

    with pytest.raises(MarkdownImageError, match=message):
        MarkdownImageNode(storage=FakeImageStorage())(create_markdown_state(markdown_path))


def test_rejects_absolute_local_image_path(tmp_path: Path) -> None:
    image_path = tmp_path / "absolute.png"
    image_path.write_bytes(b"png")
    markdown_path = tmp_path / "absolute.md"
    markdown_path.write_text(f"![图片]({image_path.as_posix()})", encoding="utf-8")

    with pytest.raises(MarkdownImageError, match="绝对路径"):
        MarkdownImageNode(storage=FakeImageStorage())(create_markdown_state(markdown_path))


def test_wraps_storage_failure_as_markdown_image_error(tmp_path: Path) -> None:
    image_path = tmp_path / "image.png"
    image_path.write_bytes(b"png")
    markdown_path = tmp_path / "failed.md"
    markdown_path.write_text("![图片](image.png)", encoding="utf-8")

    class FailedStorage:
        def upload(self, _image_path: Path, _object_name: str) -> str:
            raise MinioImageStorageError("MinIO 不可用")

    with pytest.raises(MarkdownImageError, match="MinIO 不可用"):
        MarkdownImageNode(storage=FailedStorage())(create_markdown_state(markdown_path))
