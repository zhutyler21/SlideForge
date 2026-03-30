"""Step 4 图片生成 TUI"""

from __future__ import annotations

from src.core.image_generator import generate_images
from src.core.project_manager import (
    get_project_path,
    load_project,
    save_project,
)
from src.utils.common import parse_page_range
from src.utils.openai_client import create_client
from src.utils.terminal_ui import prompt_choice, prompt_text, prompt_yes_no


def run_image_tui(project_name: str):
    """图片生成交互界面"""
    data = load_project(project_name)
    proj = data["project"]
    generation = data.get("generation", {})

    # 检查前置条件：需要有提示词
    slides = generation.get("slides", [])
    slides_with_prompts = [s for s in slides if s.get("slide_prompt")]

    if not slides_with_prompts:
        print("\n没有可用的画图提示词，请先完成 Step 3（生成画图提示词）。")
        input("按回车返回...")
        return

    existing_images = sum(
        1 for s in slides if s.get("image_status") == "generated"
    )
    failed_images = sum(
        1 for s in slides if s.get("image_status") == "failed"
    )

    print()
    print("=" * 50)
    print(f"  Step 4: 生成图片 - {proj['name']}")
    print("=" * 50)
    print(f"  可用提示词: {len(slides_with_prompts)}")
    print(f"  已生成图片: {existing_images}")
    if failed_images:
        print(f"  失败图片: {failed_images}")
    print()

    client = create_client()
    project_path = get_project_path(project_name)

    # 1. 选择页面范围
    pages = _select_pages(slides)

    # 2. 覆盖选项
    overwrite = False
    if existing_images > 0:
        overwrite = prompt_yes_no("是否覆盖已有的图片?", default=False)

    # 3. 并发设置
    workers_str = prompt_text("并发线程数", default="4")
    workers = max(1, int(workers_str))

    # 4. 执行
    print("\n--- 生成图片 ---")
    output_dir = project_path / "output"
    data = generate_images(
        project_data=data,
        output_dir=output_dir,
        client=client,
        pages=pages,
        overwrite=overwrite,
        workers=workers,
    )
    save_project(project_name, data)
    print(f"\n图片保存在: {output_dir}")

    # 5. 失败重试
    failed = [
        s["page"] for s in data["generation"].get("slides", [])
        if s.get("image_status") == "failed"
    ]
    if failed and prompt_yes_no(f"有 {len(failed)} 页失败，是否重试?"):
        data = generate_images(
            project_data=data,
            output_dir=output_dir,
            client=client,
            pages=set(failed),
            overwrite=True,
            workers=workers,
        )
        save_project(project_name, data)


def _select_pages(slides: list[dict]) -> set[int] | None:
    """选择要处理的页面范围"""
    all_pages = [s["page"] for s in slides if s.get("slide_prompt")]
    pending = [s["page"] for s in slides if s.get("image_status") != "generated"]
    failed = [s["page"] for s in slides if s.get("image_status") == "failed"]

    total = max(all_pages) if all_pages else 0

    options = [
        f"全部页面 (1-{total})",
        "指定页码范围",
    ]
    if pending:
        options.append(f"仅未生成的页面 ({len(pending)} 页)")
    if failed:
        options.append(f"仅重试失败的页面 ({len(failed)} 页)")

    choice = prompt_choice("选择范围", options, default_index=0)

    if choice == 0:
        return None
    elif choice == 1:
        range_str = prompt_text(
            "输入页码范围 (如 1-10, 3,5,7)",
            default=f"1-{total}",
            validator=lambda v: parse_page_range(v),
        )
        return set(parse_page_range(range_str))
    elif choice == 2 and pending:
        return set(pending)
    elif choice == 3 and failed:
        return set(failed)

    return None
