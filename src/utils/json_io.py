"""JSON 文件读写工具"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(file_path: str | Path) -> dict[str, Any]:
    """读取 JSON 文件"""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(file_path: str | Path, data: dict[str, Any]) -> None:
    """写入 JSON 文件（ensure_ascii=False, indent=2）"""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def load_text(file_path: str | Path) -> str:
    """读取文本文件"""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()
