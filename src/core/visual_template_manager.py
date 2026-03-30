"""审美风格模板管理器 - 保存/加载/列出可复用的视觉风格模板"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

# 模板存放目录（与 styles/ 和 projects/ 同级）
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "visual_templates"

SUPPORTED_IMAGE_FORMATS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def get_templates_dir() -> Path:
    """获取模板目录，不存在则创建"""
    TEMPLATES_DIR.mkdir(exist_ok=True)
    return TEMPLATES_DIR


def list_templates() -> list[dict[str, str]]:
    """
    列出所有审美模板

    Returns:
        [{"name": "...", "description": "...", "has_images": True/False, "created_at": "..."}]
    """
    templates_dir = get_templates_dir()
    result = []

    for tpl_dir in sorted(templates_dir.iterdir()):
        meta_path = tpl_dir / "template.yaml"
        if not meta_path.exists():
            continue

        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = yaml.safe_load(f) or {}

            ref_dir = tpl_dir / "references"
            has_images = ref_dir.exists() and any(
                f.suffix.lower() in SUPPORTED_IMAGE_FORMATS
                for f in ref_dir.iterdir()
            ) if ref_dir.exists() else False

            img_count = sum(
                1 for f in ref_dir.iterdir()
                if f.suffix.lower() in SUPPORTED_IMAGE_FORMATS
            ) if has_images else 0

            result.append({
                "name": meta.get("name", tpl_dir.name),
                "description": meta.get("description", ""),
                "has_images": has_images,
                "image_count": img_count,
                "created_at": meta.get("created_at", ""),
                "dir_name": tpl_dir.name,
            })
        except Exception:
            continue

    return result


def save_template(
    name: str,
    description: str,
    reference_images_analysis: str = "",
    custom_style_text: str = "",
    reference_images_dir: str | Path | None = None,
) -> Path:
    """
    保存审美风格模板

    Args:
        name: 模板名称
        description: 模板描述
        reference_images_analysis: 参考图片视觉分析文本
        custom_style_text: 自定义风格文本
        reference_images_dir: 参考图片源目录（复制图片到模板中）

    Returns:
        模板目录路径
    """
    # 用名称作为目录名（去除特殊字符）
    dir_name = name.replace("/", "_").replace("\\", "_").strip()
    tpl_dir = get_templates_dir() / dir_name

    if tpl_dir.exists():
        # 覆盖已有模板
        shutil.rmtree(tpl_dir)

    tpl_dir.mkdir(parents=True)
    ref_dest = tpl_dir / "references"
    ref_dest.mkdir()

    # 复制参考图片
    if reference_images_dir:
        src_dir = Path(reference_images_dir)
        if src_dir.exists() and src_dir.is_dir():
            for img_file in sorted(src_dir.iterdir()):
                if img_file.is_file() and img_file.suffix.lower() in SUPPORTED_IMAGE_FORMATS:
                    shutil.copy2(img_file, ref_dest / img_file.name)

    # 保存元数据
    meta = {
        "name": name,
        "description": description,
        "created_at": datetime.now().isoformat(),
        "reference_images_analysis": reference_images_analysis,
        "custom_style_text": custom_style_text,
    }

    with open(tpl_dir / "template.yaml", "w", encoding="utf-8") as f:
        yaml.dump(meta, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return tpl_dir


def load_template(dir_name: str) -> dict[str, Any]:
    """
    加载审美风格模板

    Args:
        dir_name: 模板目录名

    Returns:
        {
            "name": "...",
            "description": "...",
            "reference_images_analysis": "...",
            "custom_style_text": "...",
            "references_dir": Path | None,
        }
    """
    tpl_dir = get_templates_dir() / dir_name
    meta_path = tpl_dir / "template.yaml"

    if not meta_path.exists():
        raise FileNotFoundError(f"模板不存在: {dir_name}")

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = yaml.safe_load(f) or {}

    ref_dir = tpl_dir / "references"
    has_images = ref_dir.exists() and any(
        f.suffix.lower() in SUPPORTED_IMAGE_FORMATS
        for f in ref_dir.iterdir()
    ) if ref_dir.exists() else False

    return {
        "name": meta.get("name", dir_name),
        "description": meta.get("description", ""),
        "reference_images_analysis": meta.get("reference_images_analysis", ""),
        "custom_style_text": meta.get("custom_style_text", ""),
        "references_dir": ref_dir if has_images else None,
    }
