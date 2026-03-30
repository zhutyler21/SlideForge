"""项目管理器 - 创建、列表、加载 PPT 项目"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from src.utils.json_io import load_json, save_json

# 项目根目录
PROJECTS_DIR = Path(__file__).parent.parent.parent / "projects"

SUPPORTED_IMAGE_FORMATS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def get_projects_dir() -> Path:
    """获取项目目录，不存在则创建"""
    PROJECTS_DIR.mkdir(exist_ok=True)
    return PROJECTS_DIR


def create_project(
    name: str,
    style: str,
    total_pages: int,
    source_doc_path: str | Path,
    ref_images_input: str | None = None,
) -> Path:
    """
    创建新项目

    Args:
        name: 项目名称
        style: 风格名称（对应 styles/ 下的 YAML 文件名）
        total_pages: 目标页数
        source_doc_path: 参考文档路径
        ref_images_input: 参考图片路径（图片文件/文件夹/逗号分隔，可选）

    Returns:
        项目文件夹路径

    Raises:
        FileExistsError: 项目已存在
        FileNotFoundError: 参考文档不存在
    """
    project_dir = get_projects_dir() / name
    if project_dir.exists():
        raise FileExistsError(f"项目已存在: {project_dir}")

    source_path = Path(source_doc_path)
    if not source_path.exists():
        raise FileNotFoundError(f"参考文档不存在: {source_path}")

    # 创建项目目录结构
    project_dir.mkdir(parents=True)
    (project_dir / "source").mkdir()
    (project_dir / "references").mkdir()
    (project_dir / "output").mkdir()

    # 复制参考文档
    dest_doc = project_dir / "source" / source_path.name
    shutil.copy2(source_path, dest_doc)

    # 复制参考图片
    if ref_images_input:
        image_files = resolve_image_paths(ref_images_input)
        ref_dest = project_dir / "references"
        for idx, img_file in enumerate(image_files):
            dest = ref_dest / img_file.name
            if dest.exists():
                dest = ref_dest / f"{idx:02d}_{img_file.name}"
            shutil.copy2(img_file, dest)

    # 创建 project.json
    project_data = {
        "version": "2.0",
        "project": {
            "name": name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "style": style,
            "total_pages": total_pages,
            "source_document": f"source/{source_path.name}",
        },
        "inferred": {
            "title": "",
            "audience": "",
            "tone": "",
            "key_themes": [],
        },
        "outline": {
            "status": "empty",
            "chapters": [],
        },
        "generation": {
            "reference_images_analysis": "",
            "custom_style_text": "",
            "system_prompt": "",
            "slides": [],
        },
    }

    save_json(project_dir / "project.json", project_data)
    return project_dir


def list_projects() -> list[dict[str, Any]]:
    """
    列出所有项目

    Returns:
        [{"name": "...", "style": "...", "total_pages": N, "outline_status": "...", "images_count": N}]
    """
    projects = []
    projects_dir = get_projects_dir()

    for project_dir in sorted(projects_dir.iterdir()):
        json_path = project_dir / "project.json"
        if not json_path.exists():
            continue

        try:
            data = load_json(json_path)
            proj = data.get("project", {})
            outline = data.get("outline", {})
            generation = data.get("generation", {})

            # 统计已生成的图片
            output_dir = project_dir / "output"
            images_count = len(list(output_dir.glob("*.png"))) if output_dir.exists() else 0

            # 统计大纲页数
            outline_pages = sum(
                len(ch.get("pages", []))
                for ch in outline.get("chapters", [])
            )

            projects.append({
                "name": proj.get("name", project_dir.name),
                "style": proj.get("style", ""),
                "total_pages": proj.get("total_pages", 0),
                "outline_status": outline.get("status", "empty"),
                "outline_pages": outline_pages,
                "images_count": images_count,
                "path": str(project_dir),
            })
        except Exception:
            continue

    return projects


def load_project(project_name: str) -> dict[str, Any]:
    """加载项目数据"""
    json_path = get_projects_dir() / project_name / "project.json"
    if not json_path.exists():
        raise FileNotFoundError(f"项目不存在: {project_name}")
    return load_json(json_path)


def save_project(project_name: str, data: dict[str, Any]) -> None:
    """保存项目数据"""
    data.setdefault("project", {})["updated_at"] = datetime.now().isoformat()
    json_path = get_projects_dir() / project_name / "project.json"
    save_json(json_path, data)


def get_project_path(project_name: str) -> Path:
    """获取项目文件夹路径"""
    return get_projects_dir() / project_name


def replace_source_document(project_name: str, new_doc_path: str | Path) -> str:
    """
    替换项目的参考文档

    Args:
        project_name: 项目名称
        new_doc_path: 新文档路径

    Returns:
        新文档的相对路径
    """
    new_path = Path(new_doc_path)
    if not new_path.exists():
        raise FileNotFoundError(f"文档不存在: {new_path}")

    project_dir = get_project_path(project_name)
    source_dir = project_dir / "source"

    # 清空旧文档
    for old_file in source_dir.iterdir():
        old_file.unlink()

    # 复制新文档
    dest = source_dir / new_path.name
    shutil.copy2(new_path, dest)

    # 更新 project.json
    data = load_project(project_name)
    data["project"]["source_document"] = f"source/{new_path.name}"
    save_project(project_name, data)

    return f"source/{new_path.name}"


def resolve_image_paths(input_str: str) -> list[Path]:
    """
    解析用户输入的图片路径，支持多种格式：
    - 单个图片文件路径
    - 单个文件夹路径（自动扫描其中的图片，含子目录）
    - 多个路径用逗号分隔（文件和文件夹可混用）

    Returns:
        解析后的图片文件路径列表
    """
    paths_raw = [p.strip() for p in input_str.split(",") if p.strip()]
    image_files: list[Path] = []

    for raw in paths_raw:
        p = Path(raw)
        if not p.exists():
            print(f"  ⚠ 路径不存在，跳过: {raw}")
            continue

        if p.is_file():
            if p.suffix.lower() in SUPPORTED_IMAGE_FORMATS:
                image_files.append(p)
            else:
                print(f"  ⚠ 不支持的格式 ({p.suffix})，跳过: {p.name}")
        elif p.is_dir():
            # 递归扫描文件夹（含子目录）
            for img in sorted(p.rglob("*")):
                if img.is_file() and img.suffix.lower() in SUPPORTED_IMAGE_FORMATS:
                    image_files.append(img)

    return image_files


def replace_reference_images(project_name: str, input_str: str) -> int:
    """
    替换项目的参考图片

    Args:
        project_name: 项目名称
        input_str: 用户输入的路径（图片文件/文件夹/逗号分隔的多个路径）

    Returns:
        复制的图片数量
    """
    image_files = resolve_image_paths(input_str)

    project_dir = get_project_path(project_name)
    ref_dir = project_dir / "references"

    # 清空旧图片
    for old_file in ref_dir.iterdir():
        old_file.unlink()

    # 复制新图片
    count = 0
    for img_file in image_files:
        dest_name = img_file.name
        # 避免同名覆盖：加序号前缀
        dest = ref_dir / dest_name
        if dest.exists():
            dest = ref_dir / f"{count:02d}_{dest_name}"
        shutil.copy2(img_file, dest)
        count += 1

    # 清空已有的参考图片分析（需要重新分析）
    data = load_project(project_name)
    data["generation"]["reference_images_analysis"] = ""
    save_project(project_name, data)

    return count


def get_source_text(project_name: str) -> str:
    """
    获取项目的参考文档文本内容

    使用 document_parser 自动解析
    """
    data = load_project(project_name)
    source_rel = data["project"]["source_document"]
    source_path = get_project_path(project_name) / source_rel

    from src.core.document_parser import parse_document
    return parse_document(source_path)
