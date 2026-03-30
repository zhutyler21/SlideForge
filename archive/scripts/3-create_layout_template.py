#!/usr/bin/env python3
"""
生成固定版式模板图片，用作后续生成的参考
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def create_layout_template(output_path: str = "layout_template.png"):
    """创建标准版式模板"""

    # 2K分辨率 4:3
    width, height = 2048, 1536
    bg_color = "#F3F4EF"

    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # 定义版式区域
    title_height = int(height * 0.15)  # 标题区 15%
    footer_height = int(height * 0.12)  # 页脚区 12%
    content_top = title_height
    content_bottom = height - footer_height

    margin = 80
    accent_color = "#0066CC"  # 蓝色强调
    grid_color = "#CCCCCC"

    # 1. 绘制标题区域（顶部15%）
    draw.rectangle(
        [(margin, margin), (width - margin, title_height)],
        outline=accent_color,
        width=3
    )

    # 2. 绘制内容区3x3网格（中间70%）
    content_height = content_bottom - content_top
    grid_rows = 3
    grid_cols = 3

    cell_width = (width - 2 * margin) / grid_cols
    cell_height = content_height / grid_rows

    for i in range(grid_rows + 1):
        y = content_top + i * cell_height
        draw.line(
            [(margin, y), (width - margin, y)],
            fill=grid_color,
            width=2
        )

    for j in range(grid_cols + 1):
        x = margin + j * cell_width
        draw.line(
            [(x, content_top), (x, content_bottom)],
            fill=grid_color,
            width=2
        )

    # 3. 绘制页脚区域（底部12%）
    draw.rectangle(
        [(margin, content_bottom), (width - margin, height - margin)],
        outline=accent_color,
        width=3
    )

    # 4. 添加蓝色装饰条（左侧）
    draw.rectangle(
        [(margin, content_top), (margin + 8, content_bottom)],
        fill=accent_color
    )

    # 5. 标注区域名称
    try:
        font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 40)
    except:
        font = ImageFont.load_default()

    draw.text((width // 2, title_height // 2), "标题区域（固定）",
              fill="#333333", font=font, anchor="mm")
    draw.text((width // 2, (content_top + content_bottom) // 2),
              "内容区域（3x3网格）", fill="#666666", font=font, anchor="mm")
    draw.text((width // 2, content_bottom + footer_height // 2),
              "页脚区域（固定）", fill="#333333", font=font, anchor="mm")

    # 保存
    output = Path(output_path)
    img.save(output)
    print(f"✓ 版式模板已保存: {output.absolute()}")

    return output

if __name__ == "__main__":
    create_layout_template()
