"""文档解析器 - 支持 PDF/Word/Markdown/纯文本"""

from __future__ import annotations

from pathlib import Path


def _reject_doc(path: Path) -> str:
    raise ValueError("不支持旧版 .doc 格式，请先转换为 .docx")


def parse_document(file_path: str | Path) -> str:
    """
    自动识别文件类型并解析为纯文本

    Args:
        file_path: 文档路径

    Returns:
        解析后的文本内容

    Raises:
        ValueError: 不支持的文件格式
        FileNotFoundError: 文件不存在
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")

    suffix = path.suffix.lower()
    parsers = {
        ".pdf": _parse_pdf,
        ".docx": _parse_docx,
        ".doc": _reject_doc,
        ".md": _parse_text,
        ".markdown": _parse_text,
        ".txt": _parse_text,
        ".text": _parse_text,
    }

    parser = parsers.get(suffix)
    if not parser:
        raise ValueError(
            f"不支持的文件格式: {suffix}\n"
            f"支持的格式: {', '.join(parsers.keys())}"
        )

    text = parser(path)
    if not text.strip():
        raise ValueError(f"文档内容为空: {path}")

    return text


def _parse_pdf(path: Path) -> str:
    """使用 PyMuPDF 解析 PDF"""
    import fitz

    doc = fitz.open(str(path))
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text()
        if text.strip():
            pages.append(f"--- Page {i + 1} ---\n{text.strip()}")
    doc.close()

    return "\n\n".join(pages)


def _parse_docx(path: Path) -> str:
    """使用 python-docx 解析 Word 文档"""
    from docx import Document

    doc = Document(str(path))
    parts = []

    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text:
            # 保留标题层级信息
            if paragraph.style.name.startswith("Heading"):
                level = paragraph.style.name.replace("Heading ", "")
                prefix = "#" * int(level) if level.isdigit() else "#"
                parts.append(f"{prefix} {text}")
            else:
                parts.append(text)

    # 解析表格
    for table in doc.tables:
        rows = []
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            rows.append(" | ".join(cells))
        if rows:
            parts.append("\n".join(rows))

    return "\n\n".join(parts)


def _parse_text(path: Path) -> str:
    """直接读取文本文件"""
    text = path.read_text(encoding="utf-8")

    # 去除 Markdown front matter (---...---)
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            text = text[end + 3:].strip()

    return text


def get_document_stats(text: str) -> dict[str, int]:
    """获取文档统计信息"""
    return {
        "char_count": len(text),
        "word_count": len(text.split()),
        "line_count": text.count("\n") + 1,
    }
