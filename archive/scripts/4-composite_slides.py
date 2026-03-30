#!/usr/bin/env python3
"""
将AI生成的内容区域合成到固定版式模板上
确保所有页面版式完全一致
"""

import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json


class SlideCompositor:
    """幻灯片合成器：将内容叠加到固定模板"""

    def __init__(self, width=2048, height=1536, bg_color="#F3F4EF"):
        self.width = width
        self.height = height
        self.bg_color = bg_color

        # 版式参数（与模板一致）
        self.title_height = int(height * 0.15)
        self.footer_height = int(height * 0.12)
        self.margin = 80
        self.accent_color = "#0066CC"

        self.content_top = self.title_height
        self.content_bottom = height - self.footer_height

    def create_base_template(self) -> Image.Image:
        """创建固定的基础模板（标题区、页脚、装饰条）"""
        img = Image.new('RGB', (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)

        # 左侧蓝色装饰条
        draw.rectangle(
            [(self.margin, self.content_top),
             (self.margin + 8, self.content_bottom)],
            fill=self.accent_color
        )

        # 顶部标题区域边框
        draw.line(
            [(self.margin, self.title_height),
             (self.width - self.margin, self.title_height)],
            fill="#DDDDDD",
            width=2
        )

        # 底部页脚区域边框
        draw.line(
            [(self.margin, self.content_bottom),
             (self.width - self.margin, self.content_bottom)],
            fill="#DDDDDD",
            width=2
        )

        return img

    def add_title(self, img: Image.Image, title: str, page_num: int) -> Image.Image:
        """在固定位置添加标题和页码"""
        draw = ImageDraw.Draw(img)

        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 56)
            page_font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 36)
        except:
            title_font = ImageFont.load_default()
            page_font = ImageFont.load_default()

        # 标题（左对齐）
        draw.text(
            (self.margin + 20, self.title_height // 2),
            title,
            fill="#1A1A1A",
            font=title_font,
            anchor="lm"
        )

        # 页码（右对齐）
        draw.text(
            (self.width - self.margin - 20, self.height - self.footer_height // 2),
            f"{page_num}",
            fill="#666666",
            font=page_font,
            anchor="rm"
        )

        return img

    def composite_content(
        self,
        content_image_path: str,
        title: str,
        page_num: int,
        output_path: str
    ) -> str:
        """将AI生成的内容图片合成到模板上"""

        # 1. 创建基础模板
        base = self.create_base_template()

        # 2. 加载AI生成的内容图片
        content_img = Image.open(content_image_path)

        # 3. 裁剪/调整内容图片到内容区域
        content_width = self.width - 2 * self.margin - 20
        content_height = self.content_bottom - self.content_top - 20

        # 从原图中提取中间区域（假设AI生成的图也是完整页面）
        # 这里需要根据实际情况调整裁剪逻辑
        content_cropped = content_img.crop((
            self.margin,
            self.title_height,
            self.width - self.margin,
            self.content_bottom
        ))

        # 调整大小
        content_resized = content_cropped.resize(
            (content_width, content_height),
            Image.Resampling.LANCZOS
        )

        # 4. 粘贴内容到模板
        base.paste(
            content_resized,
            (self.margin + 10, self.content_top + 10)
        )

        # 5. 添加标题和页码
        base = self.add_title(base, title, page_num)

        # 6. 保存
        base.save(output_path)
        return output_path


def main():
    parser = argparse.ArgumentParser(description="将AI生成的内容合成到固定模板")
    parser.add_argument("--input-dir", required=True, help="AI生成的图片目录")
    parser.add_argument("--output-dir", default="composited_slides", help="输出目录")
    parser.add_argument("--json-file", default="ai_agent_report_slides.json")

    args = parser.parse_args()

    # 加载JSON获取标题信息
    with open(args.json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    slides = {slide['page']: slide for slide in data['slides']}

    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    compositor = SlideCompositor()

    # 处理所有图片
    input_dir = Path(args.input_dir)
    for img_file in sorted(input_dir.glob("page_*.png")):
        page_num = int(img_file.stem.split('_')[1])

        if page_num not in slides:
            print(f"⚠ 第 {page_num} 页无标题信息，跳过")
            continue

        title = slides[page_num].get('title', '')
        output_path = output_dir / f"page_{page_num:02d}.png"

        print(f"正在合成第 {page_num} 页...")
        compositor.composite_content(
            str(img_file),
            title,
            page_num,
            str(output_path)
        )
        print(f"✓ 已保存: {output_path}")

    print(f"\n完成！所有页面已保存到: {output_dir.absolute()}")


if __name__ == "__main__":
    main()
