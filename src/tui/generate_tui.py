"""Step 4 提示词+图片生成 TUI"""

from __future__ import annotations

import time
from pathlib import Path

from src.core.image_generator import generate_images
from src.core.prompt_generator import generate_slide_prompts
from src.core.reference_image_analyzer import analyze_reference_images
from src.core.project_manager import (
    get_project_path,
    get_source_text,
    load_project,
    save_project,
)
from src.core.style_loader import load_style
from src.utils.common import parse_page_range
from src.utils.openai_client import create_client
from src.utils.terminal_ui import prompt_choice, prompt_text, prompt_yes_no


def run_generate_tui(project_name: str):
    """图片生成交互界面"""
    data = load_project(project_name)
    proj = data["project"]
    outline = data.get("outline", {})
    generation = data.get("generation", {})

    # 检查大纲
    if outline.get("status") not in ("draft", "confirmed"):
        print("\n请先完成 Step 1（生成大纲）。")
        input("按回车返回...")
        return

    total_outline_pages = sum(
        len(ch.get("pages", []))
        for ch in outline.get("chapters", [])
    )

    existing_prompts = sum(
        1 for s in generation.get("slides", [])
        if s.get("slide_prompt")
    )
    existing_images = sum(
        1 for s in generation.get("slides", [])
        if s.get("image_status") == "generated"
    )

    print()
    print("=" * 50)
    print(f"  Step 2: 生成图片 - {proj['name']}")
    print("=" * 50)
    print(f"  大纲页数: {total_outline_pages}")
    print(f"  已有提示词: {existing_prompts}")
    print(f"  已有图片: {existing_images}")
    print()

    style_config = load_style(proj["style"])
    client = create_client()
    project_path = get_project_path(project_name)

    # 1. 分析参考图片（如果有且未分析）
    ref_analysis = generation.get("reference_images_analysis", "")
    ref_dir = project_path / "references"
    has_ref_images = ref_dir.exists() and any(ref_dir.iterdir())

    if has_ref_images and not ref_analysis:
        if prompt_yes_no("检测到参考图片，是否分析视觉风格?", default=True):
            print("正在分析参考图片...")
            ref_analysis = analyze_reference_images(ref_dir, client)
            data["generation"]["reference_images_analysis"] = ref_analysis
            save_project(project_name, data)
            print(f"  风格分析完成 ({len(ref_analysis)} 字符)")
    elif ref_analysis:
        print(f"  已有参考图片分析 ({len(ref_analysis)} 字符)")

    # 2. 选择操作
    choice = prompt_choice(
        "选择操作",
        [
            "生成提示词 + 图片（完整流程）",
            "仅生成提示词",
            "仅生成图片（需已有提示词）",
            "返回",
        ],
        default_index=0,
    )

    if choice == 3:
        return

    # 3. 选择页面范围
    pages = _select_pages(total_outline_pages, generation)

    # 4. 覆盖选项
    overwrite = False
    if choice in (0, 1) and existing_prompts > 0:
        overwrite_prompt = prompt_yes_no("是否覆盖已有的 slide_prompt?", default=False)
        overwrite = overwrite_prompt

    overwrite_images = False
    if choice in (0, 2) and existing_images > 0:
        overwrite_images = prompt_yes_no("是否覆盖已有的图片?", default=False)

    # 5. 画幅选择（优先使用项目中已保存的画幅）
    aspect_ratio = "16:9"
    if choice in (0, 1):
        saved_ar = proj.get("aspect_ratio", "")
        if saved_ar:
            print(f"  已保存画幅: {saved_ar}")
            if prompt_yes_no("是否更换画幅?", default=False):
                saved_ar = ""
        if not saved_ar:
            ar_choice = prompt_choice(
                "选择画幅",
                ["16:9（宽屏，2560x1440）", "4:3（标准，2048x1536）"],
                default_index=0,
            )
            saved_ar = "4:3" if ar_choice == 1 else "16:9"
            data["project"]["aspect_ratio"] = saved_ar
            save_project(project_name, data)
        aspect_ratio = saved_ar
        print(f"  画幅: {aspect_ratio}")

    # 6. 并发设置
    workers = 4
    if choice in (0, 2):
        workers_str = prompt_text("并发线程数", default="4")
        workers = max(1, int(workers_str))

    # 7. 加载原始参考文档
    try:
        source_text = get_source_text(project_name)
    except Exception:
        source_text = ""

    # 8. 执行
    t0 = time.time()

    if choice in (0, 1):
        print("\n--- 生成提示词 ---")
        data = generate_slide_prompts(
            project_data=data,
            style_config=style_config,
            client=client,
            pages=pages,
            overwrite=overwrite,
            reference_analysis=ref_analysis,
            source_text=source_text,
            aspect_ratio=aspect_ratio,
        )
        save_project(project_name, data)

    if choice in (0, 2):
        # 检查是否有提示词
        slides_with_prompts = [
            s for s in data["generation"].get("slides", [])
            if s.get("slide_prompt") and (pages is None or s["page"] in pages)
        ]
        if not slides_with_prompts:
            print("没有可用的 slide_prompt，请先生成提示词。")
            return

        print("\n--- 生成图片 ---")
        output_dir = project_path / "output"
        data = generate_images(
            project_data=data,
            output_dir=output_dir,
            client=client,
            pages=pages,
            overwrite=overwrite_images,
            workers=workers,
        )
        save_project(project_name, data)

        print(f"\n图片保存在: {output_dir}")

    elapsed = time.time() - t0
    print(f"\nStep 4 完成! 用时 {elapsed:.1f} 秒。")

    # 9. 失败重试
    if choice in (0, 2):
        failed = [
            s["page"] for s in data["generation"].get("slides", [])
            if s.get("image_status") == "failed"
        ]
        if failed and prompt_yes_no(f"有 {len(failed)} 页失败，是否重试?"):
            output_dir = project_path / "output"
            data = generate_images(
                project_data=data,
                output_dir=output_dir,
                client=client,
                pages=set(failed),
                overwrite=True,
                workers=workers,
            )
            save_project(project_name, data)


def _select_pages(total_pages: int, generation: dict) -> set[int] | None:
    """选择要处理的页面范围"""
    slides = generation.get("slides", [])
    pending = [s["page"] for s in slides if s.get("image_status") != "generated"]
    failed = [s["page"] for s in slides if s.get("image_status") == "failed"]

    options = [
        f"全部页面 (1-{total_pages})",
        "指定页码范围",
    ]
    if pending:
        options.append(f"仅未生成的页面 ({len(pending)} 页)")
    if failed:
        options.append(f"仅重试失败的页面 ({len(failed)} 页)")

    choice = prompt_choice("选择范围", options, default_index=0)

    if choice == 0:
        return None  # 全部
    elif choice == 1:
        range_str = prompt_text(
            "输入页码范围 (如 1-10, 3,5,7)",
            default=f"1-{total_pages}",
            validator=lambda v: parse_page_range(v),
        )
        return set(parse_page_range(range_str))
    elif choice == 2 and pending:
        return set(pending)
    elif choice == 3 and failed:
        return set(failed)

    return None
