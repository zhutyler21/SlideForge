"""参考图片分析器 - 使用 VISION_MODEL 分析参考图片的视觉风格"""

from __future__ import annotations

import base64
from pathlib import Path

from openai import OpenAI

from src.utils.openai_client import chat_with_retry, get_model

SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

ANALYSIS_PROMPT = """Analyze these reference slides/images and extract ALL visual style characteristics in English.

Your output will OVERRIDE the default style template for ALL visual aspects, so be precise and exhaustive.

Focus on:
- **Color palette**: Exact hex codes or closest named colors for background, primary text, accent, and highlight colors. List the dominant background color and all key accent colors.
- **Illustration style**: Are there illustrations, photos, 3D renders, flat icons, hand-drawn elements, gradients, or abstract shapes? Describe the art style precisely (e.g., flat vector, isometric 3D, watercolor, line art, cartoon, realistic).
- **Visual effects**: Shadows, gradients, glows, transparency, blur, texture overlays, rounded corners, borders, card-style containers, glassmorphism, etc.
- **Decorative elements**: Background patterns, geometric shapes, ornamental lines, icon usage, badges, ribbons, floating elements, etc.
- **Chart/diagram style**: How data is visualized — chart types, chart styling, use of infographics vs formal charts.

Do NOT describe the text content. Only describe the visual design characteristics.

Structure your output as:
1. **COLOR PALETTE** (first paragraph): Exact background color, primary/secondary text colors, and all accent/highlight colors with hex codes.
2. **ILLUSTRATION & ART STYLE** (second paragraph): The illustration/imagery approach — art style, rendering technique, character style if any, icon style, image treatment.
3. **VISUAL EFFECTS & DECORATIONS** (third paragraph): Shadows, gradients, textures, borders, decorative shapes, background patterns, container styles.
4. **OVERALL VISUAL LANGUAGE** (fourth paragraph): Synthesize the complete design language — the mood, the visual identity, what makes this style distinctive.

NOTE: Do NOT extract layout density, grid structure, spacing, typography hierarchy, or information density — those are governed by the style template, not the reference images."""


def analyze_reference_images(images_dir: str | Path, client: OpenAI) -> str:
    """
    分析参考图片文件夹中的所有图片

    Args:
        images_dir: 参考图片文件夹路径
        client: OpenAI 客户端

    Returns:
        英文风格描述文本（空字符串表示无参考图片）
    """
    images_dir = Path(images_dir)
    if not images_dir.exists() or not images_dir.is_dir():
        return ""

    image_files = sorted(
        f for f in images_dir.iterdir()
        if f.suffix.lower() in SUPPORTED_FORMATS
    )

    if not image_files:
        return ""

    # 最多分析 10 张图片
    image_files = image_files[:10]

    model = get_model("vision")

    # 构建多模态消息
    content_parts = [{"type": "text", "text": ANALYSIS_PROMPT}]

    for img_path in image_files:
        b64_data = _encode_image(img_path)
        mime = _get_mime(img_path)
        content_parts.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{b64_data}"},
        })

    response = chat_with_retry(
        client,
        model=model,
        messages=[{"role": "user", "content": content_parts}],
        temperature=0.3,
    )

    result = response.choices[0].message.content
    if isinstance(result, str):
        return result.strip()
    return str(result).strip()


def _encode_image(path: Path) -> str:
    """将图片编码为 base64"""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _get_mime(path: Path) -> str:
    """获取图片 MIME 类型"""
    suffix = path.suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
    }.get(suffix, "image/png")
