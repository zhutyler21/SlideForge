#!/usr/bin/env python3
"""Step 1: 大纲生成 - CLI 入口"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from src.core.outline_generator import expand_page_details, generate_chapter_framework
from src.core.project_manager import get_source_text, load_project, save_project
from src.core.style_loader import load_style
from src.utils.openai_client import create_client


def main():
    parser = argparse.ArgumentParser(description="Step 1: 为项目生成大纲")
    parser.add_argument("project", help="项目名称")
    parser.add_argument("--expand-only", action="store_true", help="仅展开详细内容（跳过框架生成）")
    args = parser.parse_args()

    data = load_project(args.project)
    proj = data["project"]
    style_config = load_style(proj["style"])
    client = create_client()

    if not args.expand_only:
        print("正在加载参考文档...")
        source_text = get_source_text(args.project)
        print(f"文档长度: {len(source_text):,} 字符")

        print("正在生成章节框架...")
        framework = generate_chapter_framework(
            source_text=source_text,
            total_pages=proj["total_pages"],
            style_config=style_config,
            client=client,
        )

        data["inferred"] = framework.get("inferred", data.get("inferred", {}))
        data["outline"]["status"] = "draft"
        data["outline"]["chapters"] = framework["chapters"]
        save_project(args.project, data)
        print("框架已保存")
    else:
        source_text = get_source_text(args.project)

    print("正在展开每页详细内容...")
    chapters = expand_page_details(
        source_text=source_text,
        framework={"chapters": data["outline"]["chapters"]},
        style_config=style_config,
        client=client,
    )

    data["outline"]["chapters"] = chapters
    data["outline"]["status"] = "confirmed"
    save_project(args.project, data)
    print("大纲生成完成!")


if __name__ == "__main__":
    main()
