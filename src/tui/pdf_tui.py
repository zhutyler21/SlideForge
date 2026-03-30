"""Step 5 导出 PDF TUI"""

from __future__ import annotations

from src.core.pdf_exporter import export_images_to_pdf
from src.core.project_manager import (
    get_project_path,
    load_project,
)
from src.utils.common import parse_page_range
from src.utils.terminal_ui import prompt_choice, prompt_text, prompt_yes_no


def run_pdf_tui(project_name: str):
    """PDF 导出交互界面"""
    data = load_project(project_name)
    proj = data["project"]
    generation = data.get("generation", {})

    # 检查前置条件：需要有已生成的图片
    slides = generation.get("slides", [])
    generated_slides = [s for s in slides if s.get("image_status") == "generated"]

    if not generated_slides:
        print("\n没有已生成的图片，请先完成 Step 4（生成图片）。")
        input("按回车返回...")
        return

    project_path = get_project_path(project_name)
    output_dir = project_path / "output"

    print()
    print("=" * 50)
    print(f"  Step 5: 导出 PDF - {proj['name']}")
    print("=" * 50)
    print(f"  已生成图片: {len(generated_slides)} 张")
    print()

    # 1. 选择页面范围
    pages = _select_pages(generated_slides)

    # 2. PDF 文件名
    default_name = f"{proj['name']}.pdf"
    pdf_name = prompt_text("PDF 文件名", default=default_name)
    if not pdf_name.endswith(".pdf"):
        pdf_name += ".pdf"

    pdf_path = output_dir / pdf_name

    # 3. 覆盖检查
    if pdf_path.exists():
        if not prompt_yes_no(f"文件已存在: {pdf_name}，是否覆盖?", default=True):
            print("已取消")
            return

    # 4. 执行导出
    print("\n--- 导出 PDF ---")
    aspect_ratio = proj.get("aspect_ratio", "16:9")

    try:
        result_path = export_images_to_pdf(
            output_dir=output_dir,
            pdf_path=pdf_path,
            pages=pages,
            aspect_ratio=aspect_ratio,
        )
        count = len(generated_slides) if pages is None else len(pages)
        print(f"\nPDF 导出成功! 共 {count} 页")
        print(f"文件路径: {result_path}")
    except Exception as e:
        print(f"\nPDF 导出失败: {e}")

    input("\n按回车返回...")


def _select_pages(slides: list[dict]) -> set[int] | None:
    """选择要导出的页面范围"""
    all_pages = sorted(s["page"] for s in slides)
    total = max(all_pages) if all_pages else 0

    options = [
        f"全部已生成的图片 ({len(all_pages)} 页)",
        "指定页码范围",
    ]

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

    return None
