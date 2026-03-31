#!/usr/bin/env python3
"""Step 3: 画图提示词生成 - CLI 入口"""

import argparse
import sys
from pathlib import Path

_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from dotenv import load_dotenv

load_dotenv()

from src.core.prompt_generator import generate_slide_prompts
from src.core.reference_image_analyzer import analyze_reference_images
from src.core.project_manager import get_project_path, get_source_text, load_project, save_project
from src.core.style_loader import load_style
from src.utils.common import parse_page_range
from src.utils.openai_client import create_client


def main():
    parser = argparse.ArgumentParser(description="Step 3: 生成画图提示词")
    parser.add_argument("project", help="项目名称")
    parser.add_argument("--pages", help="页码范围 (如 1-10, 3,5,7)")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已有提示词")
    parser.add_argument("--aspect-ratio", choices=["16:9", "4:3"], default="16:9", help="画幅比例 (默认: 16:9)")
    args = parser.parse_args()

    data = load_project(args.project)
    proj = data["project"]

    if data["outline"].get("status") != "confirmed":
        print("请先完成 Step 2（展开每页内容）。")
        sys.exit(1)

    style_config = load_style(proj["style"])
    client = create_client()
    project_path = get_project_path(args.project)

    pages = None
    if args.pages:
        pages = set(parse_page_range(args.pages))

    # 分析参考图片
    ref_analysis = data["generation"].get("reference_images_analysis", "")
    ref_dir = project_path / "references"
    if not ref_analysis and ref_dir.exists() and any(ref_dir.iterdir()):
        print("正在分析参考图片...")
        ref_analysis = analyze_reference_images(ref_dir, client)
        data["generation"]["reference_images_analysis"] = ref_analysis
        save_project(args.project, data)

    # 加载原始参考文档
    try:
        source_text = get_source_text(args.project)
    except Exception:
        source_text = ""

    # 生成提示词
    print(f"\n--- 生成画图提示词 (画幅: {args.aspect_ratio}) ---")
    data = generate_slide_prompts(
        project_data=data,
        style_config=style_config,
        client=client,
        pages=pages,
        overwrite=args.overwrite,
        reference_analysis=ref_analysis,
        source_text=source_text,
        aspect_ratio=args.aspect_ratio,
    )
    save_project(args.project, data)


if __name__ == "__main__":
    main()
