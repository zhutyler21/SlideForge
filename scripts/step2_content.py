#!/usr/bin/env python3
"""Step 2: 每页内容展开 - CLI 入口"""

import argparse
import sys
from pathlib import Path

_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from dotenv import load_dotenv

load_dotenv()

from src.core.outline_generator import expand_page_details
from src.core.project_manager import get_source_text, load_project, save_project
from src.core.style_loader import load_style
from src.utils.openai_client import create_client


def main():
    parser = argparse.ArgumentParser(description="Step 2: 展开每页详细内容")
    parser.add_argument("project", help="项目名称")
    args = parser.parse_args()

    data = load_project(args.project)
    proj = data["project"]
    outline = data["outline"]

    if outline.get("status") == "empty" or not outline.get("chapters"):
        print("请先完成 Step 1（生成大纲框架）。")
        sys.exit(1)

    source_text = get_source_text(args.project)
    style_config = load_style(proj["style"])
    client = create_client()

    print("正在展开每页详细内容...")
    chapters = expand_page_details(
        source_text=source_text,
        framework={"chapters": outline["chapters"]},
        style_config=style_config,
        client=client,
    )

    data["outline"]["chapters"] = chapters
    data["outline"]["status"] = "confirmed"
    save_project(args.project, data)

    print("\n每页内容展开完成! 状态已更新为 confirmed。")


if __name__ == "__main__":
    main()
