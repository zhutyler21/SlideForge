"""Step 2 每页内容展开 TUI"""

from __future__ import annotations

import time

from src.core.outline_generator import expand_page_details
from src.core.project_manager import (
    get_source_text,
    load_project,
    save_project,
)
from src.core.style_loader import load_style
from src.utils.openai_client import create_client
from src.utils.terminal_ui import prompt_choice, prompt_yes_no


def run_content_tui(project_name: str):
    """每页内容展开交互界面"""
    data = load_project(project_name)
    proj = data["project"]
    outline = data["outline"]

    # 检查前置条件
    if outline.get("status") == "empty" or not outline.get("chapters"):
        print("\n请先完成 Step 1（生成大纲框架）。")
        input("按回车返回...")
        return

    total_pages = sum(len(ch.get("pages", [])) for ch in outline["chapters"])
    has_detail = any(
        page.get("content_detail")
        for ch in outline["chapters"]
        for page in ch.get("pages", [])
    )

    print()
    print("=" * 50)
    print(f"  Step 2: 展开每页内容 - {proj['name']}")
    print("=" * 50)
    print(f"  大纲状态: {outline['status']} ({total_pages} 页)")
    print(f"  已有详细内容: {'是' if has_detail else '否'}")
    print()

    if has_detail:
        choice = prompt_choice(
            "已有详细内容，选择操作",
            [
                "重新展开所有页面（覆盖现有）",
                "返回",
            ],
            default_index=1,
        )
        if choice == 1:
            return

    if not prompt_yes_no("开始展开每页详细内容?", default=True):
        return

    # 加载依赖
    print("\n正在加载参考文档...")
    source_text = get_source_text(project_name)
    print(f"  文档长度: {len(source_text):,} 字符")

    style_config = load_style(proj["style"])
    client = create_client()

    print("\n正在展开每页详细内容...")
    t0 = time.time()
    chapters = expand_page_details(
        source_text=source_text,
        framework={"chapters": outline["chapters"]},
        style_config=style_config,
        client=client,
    )

    data["outline"]["chapters"] = chapters
    data["outline"]["status"] = "confirmed"
    save_project(project_name, data)
    elapsed = time.time() - t0

    print(f"\n每页内容展开完成! 用时 {elapsed:.1f} 秒。状态已更新为 confirmed。")
    print("可以直接编辑 project.json 进行微调，然后进入 Step 3 生成画图提示词。")
