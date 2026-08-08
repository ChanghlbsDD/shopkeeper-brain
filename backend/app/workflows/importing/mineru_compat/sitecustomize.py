"""MinerU 子进程的 Windows 中文路径兼容补丁。"""

from __future__ import annotations

import os
from pathlib import Path

model_name = os.environ.get("SHOPKEEPER_MINERU_FASTTEXT_MODEL")
if model_name:
    import fast_langdetect.ft_detect.infer as fasttext_infer

    fasttext_infer.LOCAL_SMALL_MODEL_PATH = Path(model_name)
