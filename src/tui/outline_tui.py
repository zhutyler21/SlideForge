"""Step 1 大纲框架生成 TUI"""

from __future__ import annotations

import time

from src.core.outline_generator import (
    generate_chapter_framework,
    regenerate_chapter_framework,
)
from pathlib import Path

from src.core.project_manager import (
    get_source_text,
    load_project,
    replace_source_document,
    save_project,
)
from src.core.style_loader import load_style
from src.utils.openai_client import create_client
from src.utils.terminal_ui import prompt_choice, prompt_text, prompt_yes_no


def run_outline_tui(project_name: str):
    """大纲生成交互界面"""
    data = load_project(project_name)
    proj = data["project"]
    outline = data["outline"]

    # 检查是否已有大纲
    if outline.get("status") in ("confirmed", "draft") and outline.get("chapters"):
        total_pages = sum(len(ch.get("pages", [])) for ch in outline["chapters"])
        print(f"\n当前大纲: {outline['status']} ({total_pages} 页)")

        choice = prompt_choice(
            "大纲已存在，选择操作",
            [
                "重新生成大纲框架（覆盖现有）",
                "返回",
            ],
            default_index=1,
        )

        if choice == 1:
            return
        # choice == 0: 继续重新生成

    # 可选：更换参考文档
    current_doc = proj.get("source_document", "")
    print(f"\n当前参考文档: {current_doc}")
    if prompt_yes_no("是否更换参考文档?", default=False):
        new_path = input("新文档路径: ").strip()
        if new_path and Path(new_path).exists():
            new_rel = replace_source_document(project_name, new_path)
            data = load_project(project_name)
            proj = data["project"]
            print(f"  已更换为: {new_rel}")
        else:
            print("  路径无效，保持原文档")

    # 加载文档和风格
    print("\n正在加载参考文档...")
    source_text = get_source_text(project_name)
    print(f"  文档长度: {len(source_text):,} 字符")

    style_config = load_style(proj["style"])
    client = create_client()

    # Phase 1: 生成章节框架
    t0 = time.time()
    framework = _generate_framework(
        source_text=source_text,
        total_pages=proj["total_pages"],
        style_config=style_config,
        client=client,
    )

    if framework is None:
        return

    # 保存框架到项目
    data["inferred"] = framework.get("inferred", data.get("inferred", {}))
    data["outline"]["status"] = "draft"
    data["outline"]["chapters"] = framework["chapters"]
    save_project(project_name, data)
    elapsed = time.time() - t0

    print(f"\n大纲框架已保存（draft 状态）。用时 {elapsed:.1f} 秒。")
    print("请进入 Step 2 展开每页详细内容。")


def _generate_framework(
    source_text: str,
    total_pages: int,
    style_config: dict,
    client,
    feedback: str | None = None,
) -> dict | None:
    """生成并确认章节框架，支持循环修改"""
    while True:
        print("\n正在生成章节框架...")
        if feedback:
            framework = regenerate_chapter_framework(
                source_text=source_text,
                total_pages=total_pages,
                style_config=style_config,
                client=client,
                feedback=feedback,
            )
        else:
            framework = generate_chapter_framework(
                source_text=source_text,
                total_pages=total_pages,
                style_config=style_config,
                client=client,
            )

        # 显示框架
        _display_framework(framework)

        choice = prompt_choice(
            "是否确认此框架?",
            [
                "确认，继续",
                "重新生成（不带反馈）",
                "修改后重新生成",
                "取消",
            ],
            default_index=0,
        )

        if choice == 0:
            return framework
        elif choice == 1:
            feedback = None
            continue
        elif choice == 2:
            feedback = prompt_text("请输入修改意见")
            continue
        elif choice == 3:
            print("已取消")
            return None


def _display_framework(framework: dict):
    """在终端显示章节框架"""
    inferred = framework.get("inferred", {})
    chapters = framework.get("chapters", [])

    print()
    print("=" * 55)
    print("  章节框架预览")
    print("=" * 55)

    if inferred.get("title"):
        print(f"  标题: {inferred['title']}")
    if inferred.get("audience"):
        print(f"  受众: {inferred['audience']}")
    if inferred.get("tone"):
        print(f"  语气: {inferred['tone']}")
    if inferred.get("key_themes"):
        print(f"  主题: {', '.join(inferred['key_themes'])}")

    print("-" * 55)

    total_pages = 0
    for ch in chapters:
        pages = ch.get("pages", [])
        total_pages += len(pages)
        page_range = ""
        if pages:
            first = pages[0].get("page", "?")
            last = pages[-1].get("page", "?")
            page_range = f"p{first}-{last}" if first != last else f"p{first}"

        print(f"\n  第{ch.get('chapter_index', '?')}章: {ch.get('chapter_title', '')} ({page_range}, {len(pages)}页)")

        for page in pages:
            ptype = page.get("page_type", "content")
            marker = {"cover": "[封面]", "section_divider": "[章节]", "summary": "[总结]"}.get(ptype, "")
            print(f"    p{page.get('page', '?'):>2}: {marker}{page.get('title', '')}")
            if page.get("content_brief"):
                print(f"         {page['content_brief'][:50]}...")

    print(f"\n  总计: {total_pages} 页")
    print("=" * 55)


