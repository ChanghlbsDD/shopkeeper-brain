"""使用 MinerU 把 PDF 转换为 Markdown。"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from app.core.config import REPOSITORY_ROOT, get_settings
from app.workflows.importing.base import BaseNode
from app.workflows.importing.exceptions import ImportValidationError, PdfConversionError
from app.workflows.importing.state import ImportGraphState

CommandRunner = Callable[[Sequence[str], Mapping[str, str], int], subprocess.CompletedProcess[str]]
WORKING_DIRECTORY_ENV = "SHOPKEEPER_MINERU_WORKING_DIRECTORY"


def run_command(
    command: Sequence[str],
    environment: Mapping[str, str],
    timeout_seconds: int,
) -> subprocess.CompletedProcess[str]:
    """在无 shell 的子进程中执行 MinerU，避免路径被当作命令解析。"""

    child_environment = dict(environment)
    working_directory = child_environment.pop(WORKING_DIRECTORY_ENV, None)
    return subprocess.run(
        list(command),
        capture_output=True,
        check=False,
        encoding="utf-8",
        cwd=working_directory,
        env=child_environment,
        errors="replace",
        text=True,
        timeout=timeout_seconds,
    )


class PdfToMarkdownNode(BaseNode):
    """校验 PDF 和输出目录，调用 MinerU pipeline 并返回 Markdown 路径。"""

    name = "pdf_to_md_node"

    def __init__(
        self,
        *,
        runner: CommandRunner = run_command,
        executable: str | None = None,
    ) -> None:
        super().__init__()
        self.runner = runner
        self.executable = executable

    def process(self, state: ImportGraphState) -> Mapping[str, object]:
        self.log_step("1/4", "校验 PDF 与输出目录")
        pdf_path = self._validate_pdf(state)
        output_directory = self._prepare_output_directory(state)

        settings = get_settings()
        command = [
            self.executable or self._resolve_executable(),
            "-p",
            str(pdf_path),
            "-o",
            str(output_directory),
            "-b",
            settings.mineru_backend,
        ]
        environment = self._build_environment()

        self.log_step("2/4", "调用 MinerU pipeline")
        try:
            completed = self.runner(
                command,
                environment,
                settings.mineru_timeout_seconds,
            )
        except FileNotFoundError as exc:
            raise PdfConversionError(
                "没有找到 MinerU 命令，请先在 backend/.venv 中安装 mineru[pipeline]",
                node_name=self.name,
                cause=exc,
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise PdfConversionError(
                f"MinerU 转换超过 {settings.mineru_timeout_seconds} 秒",
                node_name=self.name,
                cause=exc,
            ) from exc

        self.log_step("3/4", "检查 MinerU 执行结果")
        if completed.returncode != 0:
            details = (completed.stderr or completed.stdout or "没有错误输出").strip()
            raise PdfConversionError(
                f"MinerU 转换失败（退出码 {completed.returncode}）：{details[-1000:]}",
                node_name=self.name,
            )

        self.log_step("4/4", "定位生成的 Markdown")
        markdown_path = self._find_markdown(pdf_path, output_directory)
        return {
            "md_path": str(markdown_path.resolve()),
            "is_md_read_enabled": True,
        }

    def _validate_pdf(self, state: ImportGraphState) -> Path:
        raw_path = state.get("pdf_path", "").strip()
        if not raw_path:
            raise ImportValidationError("PDF 路径不能为空", node_name=self.name)

        pdf_path = Path(raw_path).expanduser()
        if pdf_path.suffix.lower() != ".pdf":
            raise ImportValidationError(
                f"PDF 转换节点不支持该文件类型：{pdf_path.suffix or '无扩展名'}",
                node_name=self.name,
            )
        if not pdf_path.is_file():
            raise ImportValidationError(
                f"PDF 文件不存在：{pdf_path}",
                node_name=self.name,
            )
        return pdf_path.resolve()

    def _prepare_output_directory(self, state: ImportGraphState) -> Path:
        raw_directory = state.get("file_dir", "").strip()
        if not raw_directory:
            raise ImportValidationError("MinerU 输出目录不能为空", node_name=self.name)

        output_directory = Path(raw_directory).expanduser()
        if output_directory.exists() and not output_directory.is_dir():
            raise ImportValidationError(
                f"MinerU 输出路径不是目录：{output_directory}",
                node_name=self.name,
            )
        output_directory.mkdir(parents=True, exist_ok=True)
        return output_directory.resolve()

    def _resolve_executable(self) -> str:
        executable_name = "mineru.exe" if os.name == "nt" else "mineru"
        venv_executable = Path(sys.executable).with_name(executable_name)
        if venv_executable.is_file():
            return str(venv_executable)
        return shutil.which("mineru") or executable_name

    def _build_environment(self) -> dict[str, str]:
        settings = get_settings()
        environment = os.environ.copy()
        environment["MINERU_MODEL_SOURCE"] = settings.mineru_model_source
        modelscope_cache = settings.modelscope_cache or "models/modelscope"
        hf_home = settings.hf_home or "models/huggingface"
        environment["MODELSCOPE_CACHE"] = str(self._resolve_project_path(modelscope_cache))
        environment["HF_HOME"] = str(self._resolve_project_path(hf_home))
        self._enable_fasttext_unicode_path_compatibility(environment)
        return environment

    def _resolve_project_path(self, raw_path: str) -> Path:
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = REPOSITORY_ROOT / path
        return path.resolve()

    def _enable_fasttext_unicode_path_compatibility(
        self,
        environment: dict[str, str],
    ) -> None:
        """让 Windows FastText 能从含中文的虚拟环境路径加载内置模型。"""

        if os.name != "nt":
            return

        resource_directory = (
            Path(sys.executable).parent.parent
            / "Lib"
            / "site-packages"
            / "fast_langdetect"
            / "ft_detect"
            / "resources"
        )
        model_path = resource_directory / "lid.176.ftz"
        if not model_path.is_file() or str(model_path).isascii():
            return

        compatibility_directory = Path(__file__).resolve().parents[1] / "mineru_compat"
        python_path = environment.get("PYTHONPATH", "")
        environment["PYTHONPATH"] = os.pathsep.join(
            part for part in (str(compatibility_directory), python_path) if part
        )
        environment["SHOPKEEPER_MINERU_FASTTEXT_MODEL"] = model_path.name
        environment[WORKING_DIRECTORY_ENV] = str(resource_directory)

    def _find_markdown(self, pdf_path: Path, output_directory: Path) -> Path:
        expected_path = output_directory / pdf_path.stem / "auto" / f"{pdf_path.stem}.md"
        if expected_path.is_file():
            return expected_path

        document_directory = output_directory / pdf_path.stem
        candidates = (
            sorted(document_directory.rglob(f"{pdf_path.stem}.md"))
            if document_directory.is_dir()
            else []
        )
        if len(candidates) == 1:
            return candidates[0]

        raise PdfConversionError(
            f"MinerU 已结束，但没有找到生成的 Markdown：{expected_path}",
            node_name=self.name,
        )
