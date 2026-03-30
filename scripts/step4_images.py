#!/usr/bin/env python3
"""Step 4: 图片生成 - CLI 入口"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from src.core.image_generator import generate_images
from src.core.project_manager import get_project_path, load_project, save_project
from src.utils.common import parse_page_range
from src.utils.openai_client import create_client


def main():
    parser = argparse.ArgumentParser(description="Step 4: 生成图片")
    parser.add_argument("project", help="项目名称")
    parser.add_argument("--pages", help="页码范围 (如 1-10, 3,5,7)")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已有图片")
    parser.add_argument("--workers", type=int, default=4, help="并发线程数 (默认: 4)")
    args = parser.parse_args()

    data = load_project(args.project)
    project_path = get_project_path(args.project)

    # 检查是否有提示词
    slides = data["generation"].get("slides", [])
    if not any(s.get("slide_prompt") for s in slides):
        print("没有可用的画图提示词，请先完成 Step 3。")
        sys.exit(1)

    client = create_client()

    pages = None
    if args.pages:
        pages = set(parse_page_range(args.pages))

    # 生成图片
    print("\n--- 生成图片 ---")
    output_dir = project_path / "output"
    data = generate_images(
        project_data=data,
        output_dir=output_dir,
        client=client,
        pages=pages,
        overwrite=args.overwrite,
        workers=args.workers,
    )
    save_project(args.project, data)
    print(f"\n图片保存在: {output_dir}")


if __name__ == "__main__":
    main()
