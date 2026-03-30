"""PDF 导出器 - Step 5: 将生成的图片合并为 PDF"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF


def export_images_to_pdf(
    output_dir: str | Path,
    pdf_path: str | Path,
    pages: set[int] | None = None,
    aspect_ratio: str = "16:9",
) -> Path:
    """
    将 output 目录中的 page_XX.png 图片按页码顺序合并为 PDF

    Args:
        output_dir: 图片所在目录
        pdf_path: 输出 PDF 文件路径
        pages: 要包含的页码集合（None=全部）
        aspect_ratio: 画幅比例，用于设置 PDF 页面尺寸

    Returns:
        生成的 PDF 路径
    """
    output_path = Path(output_dir)
    pdf_file = Path(pdf_path)

    # 收集图片文件并按页码排序
    image_files = sorted(output_path.glob("page_*.png"))
    if pages:
        image_files = [
            f for f in image_files
            if _extract_page_num(f.name) in pages
        ]

    if not image_files:
        raise FileNotFoundError("没有找到可用的图片文件")

    doc = fitz.open()

    for img_path in image_files:
        # 读取图片获取实际尺寸
        img = fitz.open(str(img_path))
        img_page = img[0]
        img_rect = img_page.rect
        img.close()

        # 创建与图片同尺寸的页面（保持原始分辨率比例）
        page = doc.new_page(width=img_rect.width, height=img_rect.height)
        page.insert_image(page.rect, filename=str(img_path))

    doc.save(str(pdf_file))
    doc.close()

    return pdf_file


def _extract_page_num(filename: str) -> int:
    """从文件名 page_XX.png 中提取页码"""
    stem = Path(filename).stem  # page_01
    parts = stem.split("_")
    if len(parts) >= 2:
        try:
            return int(parts[-1])
        except ValueError:
            pass
    return 0
