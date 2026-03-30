#!/usr/bin/env python3
"""
生成PPT图片
使用OpenAI SDK调用图像生成模型
从JSON文件中动态读取提示词
"""

import os
import json
import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tqdm import tqdm
from openai import OpenAI
from dotenv import load_dotenv
from src.utils.common import get_target_pages, parse_page_range, should_use_tui
from src.utils.config_validator import ConfigError, validate_openai_config
from src.utils.prompt_config import sync_system_prompt
from src.utils.terminal_ui import prompt_choice, prompt_text, prompt_yes_no

# 加载环境变量
load_dotenv()

# 初始化OpenAI客户端
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("BASE_URL")
)

# JSON文件路径
JSON_FILE = "data/ai_agent_report_slides.json"


def build_timestamped_output_dir(output_dir: str) -> Path:
    """
    为输出目录追加时间戳后缀，避免不同批次结果互相覆盖

    Args:
        output_dir: 用户指定的基础输出目录名

    Returns:
        带时间戳后缀的输出目录路径
    """
    base_path = Path(output_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return base_path.with_name(f"{base_path.name}_{timestamp}")


def load_slides_from_json(file_path: str) -> dict:
    """
    从JSON文件中加载所有幻灯片数据

    Args:
        file_path: JSON文件路径

    Returns:
        包含metadata和slides的字典
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"✓ 成功加载 {len(data['slides'])} 页幻灯片")
    return data


def run_tui(
    slides: list[dict],
    output_dir: str,
    json_file: str,
) -> dict:
    all_pages = sorted(
        slide.get("page")
        for slide in slides
        if isinstance(slide.get("page"), int)
    )

    output_path = Path(output_dir)
    existing_images = sorted(
        page for page in all_pages if (output_path / f"page_{page:02d}.png").exists()
    )

    print("=" * 60)
    print("PPT 图片生成配置")
    print("=" * 60)
    print(f"JSON文件: {Path(json_file).resolve()}")
    print(f"输出目录: {output_path.resolve()}")
    print(f"总页数: {len(all_pages)}")
    print(f"已有图片页数: {len(existing_images)}")
    print("=" * 60)

    scope = prompt_choice(
        "请选择生成范围",
        [
            "处理全部页",
            "只处理指定页码/范围",
        ],
        default_index=0,
    )

    pages_arg = f"{all_pages[0]}-{all_pages[-1]}" if all_pages else "1-1"
    if scope == 1:
        pages_arg = prompt_text(
            "输入页码范围",
            default="1",
            validator=lambda value: parse_page_range(value),
        )

    overwrite = prompt_yes_no("是否覆盖已存在图片", default=False)

    print()
    return {
        "pages": pages_arg,
        "first_n": None,
        "output": output_dir,
        "json_file": json_file,
        "overwrite": overwrite,
    }


def generate_image(system_prompt: str, user_prompt: str, page_num: int, output_dir: Path, max_retries: int = 3) -> str:
    """
    生成单张图片，支持重试机制

    Args:
        system_prompt: 系统提示词（通用风格规范）
        user_prompt: 用户提示词（具体页面内容）
        page_num: 页码
        output_dir: 输出目录
        max_retries: 最大重试次数

    Returns:
        保存的文件路径，失败返回 None
    """
    # 组合完整提示词: system_prompt 负责全局风格, slide_prompt 负责单页构图
    full_prompt = f"{system_prompt}\n\n{user_prompt}"

    for attempt in range(max_retries):
        try:
            # 使用标准chat completions接口生成图像
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL"),
                messages=[
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                temperature=0.7
            )

            # 从响应中提取图片
            content = response.choices[0].message.content

            # 尝试从markdown格式中提取base64图片数据
            import re
            import base64

            # 匹配 ![image](data:image/jpeg;base64,...)
            base64_match = re.search(r'!\[.*?\]\(data:image/[^;]+;base64,([^\)]+)\)', content)

            if base64_match:
                # 提取base64数据并解码
                base64_data = base64_match.group(1)
                image_data = base64.b64decode(base64_data)
            else:
                # 尝试查找URL格式
                url_match = re.search(r'!\[.*?\]\((https?://[^\)]+)\)', content)
                if not url_match:
                    url_match = re.search(r'(https?://[^\s]+\.(?:png|jpg|jpeg|webp))', content)

                if not url_match:
                    raise Exception(f"无法从响应中提取图片: {content[:200]}")

                # 下载图片
                import requests
                image_url = url_match.group(1)
                image_data = requests.get(image_url, timeout=30).content

            output_path = output_dir / f"page_{page_num:02d}.png"
            with open(output_path, "wb") as f:
                f.write(image_data)

            tqdm.write(f"✓ 第 {page_num} 页已保存")
            return str(output_path)

        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 指数退避: 1s, 2s, 4s
                tqdm.write(f"✗ 第 {page_num} 页失败 (尝试 {attempt + 1}/{max_retries}): {str(e)[:100]}")
                time.sleep(wait_time)
            else:
                tqdm.write(f"✗ 第 {page_num} 页失败 (已达最大重试): {str(e)[:100]}")
                return None

    return None


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='从JSON文件生成PPT图片',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  生成前5页:
    uv run generate_images.py --pages 1-5

  生成21-40页:
    uv run generate_images.py --pages 21-40

  生成特定页:
    uv run generate_images.py --pages 1,3,5

  生成多个范围:
    uv run generate_images.py --pages 1-5,10,15-20
        """
    )
    parser.add_argument(
        '--pages',
        type=str,
        default='1-5',
        help='要生成的页码范围，如 "1-5" 或 "1,3,5" 或 "1-3,5,7-9" (默认: 1-5)'
    )
    parser.add_argument(
        '--first-n',
        type=int,
        help='仅处理按页码排序后的前 N 页，适合快速测试；设置后优先于 --pages'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='output/generated_images',
        help='输出目录基础名称，实际会自动追加时间戳后缀 (默认: output/generated_images)'
    )
    parser.add_argument(
        '--json-file',
        type=str,
        default=JSON_FILE,
        help=f'JSON文件路径 (默认: {JSON_FILE})'
    )
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='覆盖已存在的输出图片；默认跳过已有图片'
    )
    parser.add_argument(
        '--tui',
        action='store_true',
        help='强制使用终端交互模式'
    )
    parser.add_argument(
        '--no-tui',
        action='store_true',
        help='禁用终端交互模式，强制使用命令行参数'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=1,
        help='并发生成的工作线程数 (默认: 1，串行生成)'
    )

    args = parser.parse_args()

    # 验证配置
    try:
        validate_openai_config()
    except ConfigError as e:
        print(f"配置错误: {e}", file=sys.stderr)
        sys.exit(1)

    # 从JSON加载数据
    print("正在加载JSON文件...")
    data = load_slides_from_json(args.json_file)
    data = sync_system_prompt(data)
    system_prompt = data['system_prompt']
    slide_list = data['slides']
    slides = {slide['page']: slide for slide in slide_list}

    final_output_dir = build_timestamped_output_dir(args.output)

    if should_use_tui(args):
        resolved = run_tui(
            slides=slide_list,
            output_dir=str(final_output_dir),
            json_file=args.json_file,
        )
    else:
        resolved = {
            "pages": args.pages,
            "first_n": args.first_n,
            "output": str(final_output_dir),
            "json_file": args.json_file,
            "overwrite": args.overwrite,
        }

    # 创建输出目录
    output_dir = Path(resolved["output"])
    output_dir.mkdir(exist_ok=True)
    page_numbers = get_target_pages(slide_list, resolved["pages"], resolved["first_n"])

    print("=" * 60)
    print("PPT图片生成工具")
    print("=" * 60)
    print(f"JSON文件: {resolved['json_file']}")
    print(f"输出目录: {output_dir.absolute()}")
    print(f"使用模型: {os.getenv('OPENAI_MODEL')}")
    print(f"并发线程数: {args.workers}")
    print(f"覆盖已有图片: {resolved['overwrite']}")
    print("=" * 60)
    print()

    if resolved["first_n"] is not None:
        print(f"测试模式: 前 {resolved['first_n']} 页")
    print(f"生成页码: {page_numbers}")
    print()

    # 准备任务列表
    tasks = []
    for page_num in page_numbers:
        if page_num not in slides:
            continue

        slide = slides[page_num]
        slide_prompt = (slide.get('slide_prompt') or slide.get('prompt') or '').strip()
        if not slide_prompt:
            continue

        output_path = output_dir / f"page_{page_num:02d}.png"
        if output_path.exists() and not resolved["overwrite"]:
            continue

        tasks.append((page_num, slide_prompt))

    # 生成图片
    results = [None] * len(page_numbers)

    if args.workers > 1:
        # 并发生成
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            future_to_page = {
                executor.submit(generate_image, system_prompt, prompt, page, output_dir): (idx, page)
                for idx, (page, prompt) in enumerate(tasks)
            }

            with tqdm(total=len(tasks), desc="生成图片", unit="页") as pbar:
                for future in as_completed(future_to_page):
                    idx, page_num = future_to_page[future]
                    try:
                        result = future.result()
                        results[idx] = result
                    except Exception as e:
                        tqdm.write(f"✗ 第 {page_num} 页异常: {str(e)[:100]}")
                    pbar.update(1)
    else:
        # 串行生成
        with tqdm(total=len(tasks), desc="生成图片", unit="页") as pbar:
            for idx, (page_num, slide_prompt) in enumerate(tasks):
                result = generate_image(system_prompt, slide_prompt, page_num, output_dir)
                results[idx] = result
                pbar.update(1)

    # 总结
    print("=" * 60)
    print("生成完成！")
    success_count = sum(1 for r in results if r is not None)
    print(f"成功: {success_count}/{len(tasks)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
