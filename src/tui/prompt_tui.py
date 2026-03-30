"""Step 3 画图提示词生成 TUI"""

from __future__ import annotations

import time
from pathlib import Path

from src.core.prompt_generator import generate_slide_prompts
from src.core.reference_image_analyzer import analyze_reference_images
from src.core.project_manager import (
    get_project_path,
    get_source_text,
    load_project,
    replace_reference_images,
    save_project,
)
from src.core.style_loader import load_style
from src.utils.common import parse_page_range
from src.utils.openai_client import create_client
from src.utils.terminal_ui import prompt_choice, prompt_text, prompt_yes_no


def run_prompt_tui(project_name: str):
    """画图提示词生成交互界面"""
    data = load_project(project_name)
    proj = data["project"]
    outline = data.get("outline", {})
    generation = data.get("generation", {})

    # 检查前置条件：大纲需要 confirmed（已展开详细内容）
    if outline.get("status") != "confirmed":
        print("\n请先完成 Step 2（展开每页内容），使大纲状态变为 confirmed。")
        input("按回车返回...")
        return

    total_pages = sum(
        len(ch.get("pages", []))
        for ch in outline.get("chapters", [])
    )

    existing_prompts = sum(
        1 for s in generation.get("slides", [])
        if s.get("slide_prompt")
    )

    print()
    print("=" * 50)
    print(f"  Step 3: 生成画图提示词 - {proj['name']}")
    print("=" * 50)
    print(f"  大纲页数: {total_pages}")
    print(f"  已有提示词: {existing_prompts}")
    print()

    style_config = load_style(proj["style"])
    client = create_client()
    project_path = get_project_path(project_name)

    # 0. 选择视觉风格来源：预设模板 or 手动设置
    used_template = False
    ref_analysis = generation.get("reference_images_analysis", "")
    custom_style = generation.get("custom_style_text", "")

    from src.core.visual_template_manager import list_templates, load_template
    templates = list_templates()
    if templates:
        style_source_options = [
            "手动设置（参考图片 + 自定义文本）",
            "使用预设审美模板",
        ]
        # 已有风格数据时，增加"保持当前设置"选项
        has_existing_style = bool(ref_analysis or custom_style)
        if has_existing_style:
            style_source_options.insert(0, "保持当前设置")

        source_choice = prompt_choice("视觉风格来源", style_source_options, default_index=0)

        # 解析选择结果
        if has_existing_style:
            if source_choice == 0:
                used_template = True  # 跳过手动设置流程
            elif source_choice == 2:
                # 使用预设模板
                used_template = _apply_visual_template(
                    templates, project_name, project_path, data, generation,
                )
                if used_template:
                    ref_analysis = generation.get("reference_images_analysis", "")
                    custom_style = generation.get("custom_style_text", "")
            # source_choice == 1: 手动设置，不做任何事，走下面的流程
        else:
            if source_choice == 1:
                used_template = _apply_visual_template(
                    templates, project_name, project_path, data, generation,
                )
                if used_template:
                    ref_analysis = generation.get("reference_images_analysis", "")
                    custom_style = generation.get("custom_style_text", "")

    # 手动设置流程（未使用模板时执行）
    if not used_template:
        ref_dir = project_path / "references"
        has_ref_images = ref_dir.exists() and any(ref_dir.iterdir())
        ref_count = sum(1 for f in ref_dir.iterdir() if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".bmp")) if has_ref_images else 0
        print(f"  参考图片: {ref_count} 张")
        if prompt_yes_no("是否更换参考图片?", default=False):
            new_input = input("图片路径 (文件/文件夹/多个逗号分隔): ").strip()
            if new_input:
                count = replace_reference_images(project_name, new_input)
                data = load_project(project_name)
                generation = data.get("generation", {})
                if count > 0:
                    print(f"  已更换: {count} 张图片（风格分析已清空，将重新分析）")
                else:
                    print("  未找到有效图片（支持 png/jpg/jpeg/webp/bmp）")
            else:
                print("  未输入路径，保持原图片")

        # 分析参考图片（如果有且未分析）
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

        # 自定义风格文本
        custom_style = generation.get("custom_style_text", "")
        if custom_style:
            preview = custom_style[:80] + ("..." if len(custom_style) > 80 else "")
            print(f"  已有自定义风格文本: {preview}")
            if prompt_yes_no("是否重新编辑自定义风格文本?", default=False):
                custom_style = ""
        if not custom_style:
            if prompt_yes_no("是否输入自定义风格文本? (描述配色、画风等，与参考图互补)", default=False):
                print("  请输入风格描述 (如: Modern minimal pop art, Pastel colors: mint #A8E6C8...):")
                custom_style = input("  > ").strip()
        if custom_style != generation.get("custom_style_text", ""):
            data["generation"]["custom_style_text"] = custom_style
            save_project(project_name, data)
            if custom_style:
                print(f"  自定义风格文本已保存 ({len(custom_style)} 字符)")
            else:
                print("  自定义风格文本已清空")

    # 2. 选择页面范围
    pages = _select_pages(total_pages)

    # 3. 覆盖选项
    overwrite = False
    if existing_prompts > 0:
        overwrite = prompt_yes_no("是否覆盖已有的 slide_prompt?", default=False)

    # 4. 画幅选择（优先使用项目中已保存的画幅）
    saved_ar = proj.get("aspect_ratio", "")
    if saved_ar:
        print(f"  已保存画幅: {saved_ar}")
        if prompt_yes_no("是否更换画幅?", default=False):
            saved_ar = ""  # 重新选择
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

    # 5. 加载原始参考文档
    try:
        source_text = get_source_text(project_name)
    except Exception:
        source_text = ""

    # 6. 执行
    print("\n--- 生成画图提示词 ---")
    t0 = time.time()
    data = generate_slide_prompts(
        project_data=data,
        style_config=style_config,
        client=client,
        pages=pages,
        overwrite=overwrite,
        reference_analysis=ref_analysis,
        custom_style_text=custom_style,
        source_text=source_text,
        aspect_ratio=aspect_ratio,
    )
    save_project(project_name, data)
    elapsed = time.time() - t0

    print(f"\n画图提示词生成完成! 用时 {elapsed:.1f} 秒。可进入 Step 4 生成图片。")


def _select_pages(total_pages: int) -> set[int] | None:
    """选择要处理的页面范围"""
    options = [
        f"全部页面 (1-{total_pages})",
        "指定页码范围",
    ]

    choice = prompt_choice("选择范围", options, default_index=0)

    if choice == 0:
        return None
    elif choice == 1:
        range_str = prompt_text(
            "输入页码范围 (如 1-10, 3,5,7)",
            default=f"1-{total_pages}",
            validator=lambda v: parse_page_range(v),
        )
        return set(parse_page_range(range_str))

    return None


def _apply_visual_template(
    templates: list[dict],
    project_name: str,
    project_path: Path,
    data: dict,
    generation: dict,
) -> bool:
    """
    让用户选择并应用预设审美模板。

    Returns:
        True 表示已成功应用模板
    """
    import shutil
    from src.core.visual_template_manager import load_template

    tpl_options = []
    for t in templates:
        imgs = f" | {t['image_count']}张参考图" if t['has_images'] else ""
        tpl_options.append(f"{t['name']} - {t['description']}{imgs}")
    tpl_options.append("返回")

    tpl_idx = prompt_choice("选择审美模板", tpl_options, default_index=0)
    if tpl_idx == len(templates):
        return False

    tpl = load_template(templates[tpl_idx]["dir_name"])
    print(f"\n  应用模板: {tpl['name']}")

    # 写入参考图分析
    if tpl["reference_images_analysis"]:
        generation["reference_images_analysis"] = tpl["reference_images_analysis"]
        print(f"  参考图分析: {len(tpl['reference_images_analysis'])} 字符")

    # 写入自定义风格文本
    if tpl["custom_style_text"]:
        generation["custom_style_text"] = tpl["custom_style_text"]
        preview = tpl["custom_style_text"][:80] + ("..." if len(tpl["custom_style_text"]) > 80 else "")
        print(f"  自定义风格文本: {preview}")

    # 复制参考图片到项目
    if tpl["references_dir"]:
        ref_dir = project_path / "references"
        # 清空旧图片
        if ref_dir.exists():
            for old_file in ref_dir.iterdir():
                old_file.unlink()
        else:
            ref_dir.mkdir()
        # 复制模板中的图片
        count = 0
        for img in sorted(tpl["references_dir"].iterdir()):
            if img.is_file() and img.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".bmp"):
                shutil.copy2(img, ref_dir / img.name)
                count += 1
        if count:
            print(f"  参考图片: 已复制 {count} 张")

    save_project(project_name, data)
    print("  模板应用完成!")
    return True
