"""项目创建/打开向导 TUI"""

from __future__ import annotations

import sys
from pathlib import Path

from src.core.document_parser import get_document_stats, parse_document
from src.core.project_manager import (
    create_project,
    get_project_path,
    list_projects,
    load_project,
)
from src.core.style_loader import list_styles
from src.utils.terminal_ui import prompt_choice, prompt_text, prompt_yes_no


def create_project_wizard():
    """新建项目向导"""
    print()
    print("=" * 50)
    print("  新建项目")
    print("=" * 50)
    print()

    # 1. 项目名称
    name = prompt_text("项目名称")

    # 2. 参考文档路径
    source_path = prompt_text(
        "参考文档路径 (支持 PDF/Word/Markdown/txt)",
        validator=_validate_file_exists,
    )

    # 解析并显示文档信息
    try:
        text = parse_document(source_path)
        stats = get_document_stats(text)
        print(f"  已解析文档: {stats['char_count']:,} 字符, {stats['line_count']:,} 行")
    except Exception as e:
        print(f"  文档解析失败: {e}")
        if not prompt_yes_no("是否继续创建项目?"):
            return

    # 3. 页数
    total_pages = int(prompt_text(
        "目标页数",
        default="30",
        validator=_validate_page_count,
    ))

    # 4. 选择风格
    styles = list_styles()
    if not styles:
        print("没有找到风格配置文件，请检查 styles/ 目录")
        return

    style_names = [f"{s['display_name']} - {s['description'][:30]}" for s in styles]
    style_idx = prompt_choice("选择风格", style_names, default_index=0)
    style = styles[style_idx]["name"]

    # 5. 参考图片路径（可选，留空跳过）
    ref_images_input = None
    raw_ref = input("参考图片路径 (文件/文件夹/多个逗号分隔，留空跳过): ").strip()
    if raw_ref:
        from src.core.project_manager import resolve_image_paths
        found_images = resolve_image_paths(raw_ref)
        if found_images:
            print(f"  检测到 {len(found_images)} 张图片")
            ref_images_input = raw_ref
        else:
            print("  未找到有效图片（支持 png/jpg/jpeg/webp/bmp）")

    # 6. 确认
    print()
    print("-" * 40)
    print(f"  项目名称: {name}")
    print(f"  参考文档: {source_path}")
    print(f"  目标页数: {total_pages}")
    print(f"  风格: {style}")
    if ref_images_input:
        print(f"  参考图片: {ref_images_input}")
    print("-" * 40)

    if not prompt_yes_no("确认创建?", default=True):
        print("已取消")
        return

    # 创建项目
    try:
        project_dir = create_project(
            name=name,
            style=style,
            total_pages=total_pages,
            source_doc_path=source_path,
            ref_images_input=ref_images_input,
        )
        print(f"\n项目已创建: {project_dir}")
        print()

        # 直接进入项目操作菜单
        _project_menu(name)

    except Exception as e:
        print(f"创建失败: {e}")


def open_project_wizard():
    """打开已有项目"""
    projects = list_projects()
    if not projects:
        print("没有找到已有项目。请先创建一个新项目。")
        return

    print()
    print("=" * 50)
    print("  打开项目")
    print("=" * 50)
    print()

    options = []
    for p in projects:
        status_parts = []
        if p["outline_status"] != "empty":
            status_parts.append(f"大纲:{p['outline_status']}/{p['outline_pages']}页")
        if p["images_count"] > 0:
            status_parts.append(f"图片:{p['images_count']}张")
        status = " | ".join(status_parts) if status_parts else "空项目"
        options.append(f"{p['name']} [{p['style']}] ({status})")

    options.append("返回主菜单")

    idx = prompt_choice("选择项目", options, default_index=0)
    if idx == len(projects):
        return

    project_name = projects[idx]["name"]
    _project_menu(project_name)


def _project_menu(project_name: str):
    """项目操作菜单"""
    while True:
        data = load_project(project_name)
        proj = data.get("project", {})
        outline = data.get("outline", {})
        generation = data.get("generation", {})

        outline_pages = sum(len(ch.get("pages", [])) for ch in outline.get("chapters", []))
        has_detail = any(
            page.get("content_detail")
            for ch in outline.get("chapters", [])
            for page in ch.get("pages", [])
        )
        prompts_count = sum(
            1 for s in generation.get("slides", [])
            if s.get("slide_prompt")
        )
        images_count = sum(
            1 for s in generation.get("slides", [])
            if s.get("image_status") == "generated"
        )

        print()
        print(f"=== 项目: {proj.get('name', project_name)} ===")
        print(f"  风格: {proj.get('style', 'N/A')} | 目标: {proj.get('total_pages', 0)} 页")
        print(f"  Step 1 大纲: {outline.get('status', 'empty')} ({outline_pages} 页)")
        print(f"  Step 2 内容: {'已展开' if has_detail else '未展开'}")
        print(f"  Step 3 提示词: {prompts_count} 条")
        print(f"  Step 4 图片: {images_count} 张已生成")

        # PDF 状态
        output_dir = get_project_path(project_name) / "output"
        pdf_files = list(output_dir.glob("*.pdf")) if output_dir.exists() else []
        if pdf_files:
            print(f"  Step 5 PDF: {len(pdf_files)} 个文件")
        else:
            print(f"  Step 5 PDF: 未导出")
        print()

        choice = prompt_choice(
            "选择操作",
            [
                "Step 1: 生成大纲框架",
                "Step 2: 展开每页内容",
                "Step 3: 生成画图提示词",
                "Step 4: 生成图片",
                "Step 5: 导出 PDF",
                "保存审美风格为模板",
                "查看项目状态",
                "返回主菜单",
            ],
            default_index=0,
        )

        if choice == 0:
            from src.tui.outline_tui import run_outline_tui
            run_outline_tui(project_name)
        elif choice == 1:
            from src.tui.content_tui import run_content_tui
            run_content_tui(project_name)
        elif choice == 2:
            from src.tui.prompt_tui import run_prompt_tui
            run_prompt_tui(project_name)
        elif choice == 3:
            from src.tui.image_tui import run_image_tui
            run_image_tui(project_name)
        elif choice == 4:
            from src.tui.pdf_tui import run_pdf_tui
            run_pdf_tui(project_name)
        elif choice == 5:
            _save_visual_template(project_name)
        elif choice == 6:
            _show_project_status(project_name)
        elif choice == 7:
            break


def _show_project_status(project_name: str):
    """显示项目详细状态"""
    data = load_project(project_name)
    proj = data["project"]
    outline = data["outline"]
    generation = data["generation"]

    print()
    print("=" * 50)
    print(f"  项目状态: {proj['name']}")
    print("=" * 50)
    print(f"  创建时间: {proj.get('created_at', 'N/A')}")
    print(f"  最后更新: {proj.get('updated_at', 'N/A')}")
    print(f"  风格: {proj.get('style', 'N/A')}")
    print(f"  参考文档: {proj.get('source_document', 'N/A')}")
    print()

    # Step 1: 大纲状态
    print(f"\n  [Step 1] 大纲框架: {outline.get('status', 'empty')}")
    for ch in outline.get("chapters", []):
        pages = ch.get("pages", [])
        print(f"    第{ch.get('chapter_index', '?')}章: {ch.get('chapter_title', '')} ({len(pages)} 页)")

    # Step 2: 内容展开状态
    has_detail = any(
        page.get("content_detail")
        for ch in outline.get("chapters", [])
        for page in ch.get("pages", [])
    )
    print(f"\n  [Step 2] 每页内容: {'已展开' if has_detail else '未展开'}")

    # Step 3: 提示词状态
    slides = generation.get("slides", [])
    prompts_count = sum(1 for s in slides if s.get("slide_prompt"))
    print(f"\n  [Step 3] 画图提示词: {prompts_count} 条")

    # Step 4: 图片生成状态
    if slides:
        generated = sum(1 for s in slides if s.get("image_status") == "generated")
        failed = sum(1 for s in slides if s.get("image_status") == "failed")
        pending = sum(1 for s in slides if s.get("image_status") == "pending")
        print(f"\n  [Step 4] 图片生成: 成功 {generated} / 失败 {failed} / 待生成 {pending}")

    # Step 5: PDF 导出状态
    output_dir = get_project_path(project_name) / "output"
    pdf_files = sorted(output_dir.glob("*.pdf")) if output_dir.exists() else []
    if pdf_files:
        print(f"\n  [Step 5] PDF 导出: {len(pdf_files)} 个文件")
        for pf in pdf_files:
            size_kb = pf.stat().st_size / 1024
            print(f"    {pf.name} ({size_kb:.0f} KB)")
    else:
        print(f"\n  [Step 5] PDF 导出: 未导出")

    # 推断信息
    inferred = data.get("inferred", {})
    if inferred.get("title"):
        print(f"\n  推断标题: {inferred['title']}")
        print(f"  推断受众: {inferred.get('audience', 'N/A')}")

    print()


def _save_visual_template(project_name: str):
    """从当前项目保存审美风格模板"""
    from src.core.visual_template_manager import save_template, list_templates

    data = load_project(project_name)
    generation = data.get("generation", {})
    ref_analysis = generation.get("reference_images_analysis", "")
    custom_style = generation.get("custom_style_text", "")

    if not ref_analysis and not custom_style:
        print("\n当前项目没有参考图片分析和自定义风格文本，无法保存模板。")
        print("请先在 Step 3 中设置参考图片或自定义风格文本。")
        input("按回车返回...")
        return

    print()
    print("=" * 50)
    print("  保存审美风格模板")
    print("=" * 50)
    if ref_analysis:
        print(f"  参考图片分析: {len(ref_analysis)} 字符")
    if custom_style:
        preview = custom_style[:80] + ("..." if len(custom_style) > 80 else "")
        print(f"  自定义风格文本: {preview}")
    print()

    # 显示已有模板
    existing = list_templates()
    if existing:
        print("  已有模板:")
        for t in existing:
            imgs = f" | {t['image_count']}张参考图" if t['has_images'] else ""
            print(f"    - {t['name']}: {t['description']}{imgs}")
        print()

    name = prompt_text("模板名称")
    description = prompt_text("模板描述 (一句话说明风格特征)")

    # 复制参考图片
    project_path = get_project_path(project_name)
    ref_dir = project_path / "references"
    has_ref_images = ref_dir.exists() and any(ref_dir.iterdir())

    tpl_dir = save_template(
        name=name,
        description=description,
        reference_images_analysis=ref_analysis,
        custom_style_text=custom_style,
        reference_images_dir=ref_dir if has_ref_images else None,
    )

    img_count = sum(
        1 for f in (tpl_dir / "references").iterdir()
        if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".bmp")
    ) if (tpl_dir / "references").exists() else 0

    print(f"\n模板已保存: {tpl_dir}")
    print(f"  包含: 风格分析{'Yes' if ref_analysis else 'No'} | "
          f"自定义文本{'Yes' if custom_style else 'No'} | "
          f"参考图片{img_count}张")
    input("按回车返回...")


def _validate_file_exists(path: str) -> None:
    if not Path(path).exists():
        raise ValueError(f"文件不存在: {path}")


def _validate_dir_exists(path: str) -> None:
    p = Path(path)
    if not p.exists() or not p.is_dir():
        raise ValueError(f"目录不存在: {path}")


def _validate_page_count(value: str) -> None:
    if not value.strip().isdigit():
        raise ValueError("请输入有效的数字")
    n = int(value)
    if n < 1 or n > 200:
        raise ValueError("页数应在 1-200 之间")
