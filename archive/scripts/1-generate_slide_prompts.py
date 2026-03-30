#!/usr/bin/env python3
"""
基于 JSON 中的 slide content 调用大模型生成 slide_prompt。

工作流:
1. 读取 slides JSON
2. 读取可编辑的 meta-prompt 模板
3. 逐页将 page/section/title/content/system_prompt 发送给 GEN_PROMPT_MODEL
4. 将生成结果写回每页的 slide_prompt 字段
5. 同步兼容旧字段 prompt, 便于 generate_images.py 继续工作
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm
from src.utils.common import get_target_pages, parse_page_range, should_use_tui
from src.utils.config_validator import ConfigError, validate_prompt_gen_config
from src.utils.prompt_config import format_metadata_for_prompt, sync_system_prompt
from src.utils.terminal_ui import prompt_choice, prompt_text, prompt_yes_no


load_dotenv()


DEFAULT_JSON_FILE = "data/ai_agent_report_slides.json"
DEFAULT_META_PROMPT_FILE = "docs/prompts/slide_prompt_meta_prompt_optimized.md"  # 优先使用优化版


def build_client() -> OpenAI:
    return OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("BASE_URL"),
    )


def load_json(file_path: str) -> dict[str, Any]:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(file_path: str, data: dict[str, Any]) -> None:
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def load_text(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def run_tui(
    slides: list[dict[str, Any]],
    json_file: str,
    meta_prompt_file: str,
    temperature: float,
) -> dict[str, Any]:
    all_pages = sorted(
        slide.get("page")
        for slide in slides
        if isinstance(slide.get("page"), int)
    )
    existing_pages = sorted(
        slide.get("page")
        for slide in slides
        if isinstance(slide.get("page"), int)
        and bool((slide.get("slide_prompt") or "").strip())
    )

    print("=" * 60)
    print("Slide Prompt 生成配置")
    print("=" * 60)
    print(f"JSON文件: {Path(json_file).resolve()}")
    print(f"Meta-prompt: {Path(meta_prompt_file).resolve()}")
    print(f"总页数: {len(all_pages)}")
    print(f"已有 slide_prompt 页数: {len(existing_pages)}")
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

    overwrite = prompt_yes_no("是否覆盖已有 slide_prompt", default=False)

    print()
    return {
        "json_file": json_file,
        "meta_prompt_file": meta_prompt_file,
        "pages": pages_arg,
        "first_n": None,
        "temperature": temperature,
        "overwrite": overwrite,
    }


def build_user_prompt(
    slide: dict[str, Any],
    metadata: dict[str, Any],
    system_prompt: str,
) -> str:
    return (
        "Generate one slide-specific image-generation prompt for this slide.\n\n"
        "metadata:\n"
        f"{format_metadata_for_prompt(metadata)}\n\n"
        "derived_system_prompt:\n"
        f"{system_prompt}\n\n"
        f"page: {slide['page']}\n"
        f"section: {slide.get('section', '')}\n"
        f"title: {slide.get('title', '')}\n"
        f"content:\n{slide.get('content', '')}\n\n"
        "Important: the generated slide_prompt must comply with the metadata and the derived_system_prompt above.\n"
    )


def extract_text_response(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if getattr(item, "type", None) == "text":
                text_value = getattr(item, "text", "")
                if text_value:
                    text_parts.append(text_value)
                continue

            if isinstance(item, dict) and item.get("type") == "text":
                text_value = item.get("text", "")
                if text_value:
                    text_parts.append(text_value)

        return "\n".join(part.strip() for part in text_parts if part.strip()).strip()

    return str(content).strip()


def generate_slide_prompt(
    client: OpenAI,
    model: str,
    metadata: dict[str, Any],
    meta_prompt: str,
    system_prompt: str,
    slide: dict[str, Any],
    temperature: float,
) -> str:
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": meta_prompt},
            {
                "role": "user",
                "content": build_user_prompt(slide, metadata, system_prompt),
            },
        ],
    )
    content = response.choices[0].message.content
    slide_prompt = extract_text_response(content)
    if not slide_prompt:
        raise ValueError(f"第 {slide['page']} 页返回空 slide_prompt")
    return slide_prompt


def main() -> None:
    parser = argparse.ArgumentParser(
        description="基于 JSON 内容生成 slide_prompt 并写回 JSON"
    )
    parser.add_argument(
        "--json-file",
        default=DEFAULT_JSON_FILE,
        help=f"输入 JSON 文件路径 (默认: {DEFAULT_JSON_FILE})",
    )
    parser.add_argument(
        "--meta-prompt-file",
        default=DEFAULT_META_PROMPT_FILE,
        help=f"meta-prompt 文件路径 (默认: {DEFAULT_META_PROMPT_FILE})",
    )
    parser.add_argument(
        "--pages",
        default="1-40",
        help='要生成的页码范围，如 "1-5"、"1,3,5"、"1-3,5,7-9"',
    )
    parser.add_argument(
        "--first-n",
        type=int,
        help="仅处理按页码排序后的前 N 页，适合快速测试；设置后优先于 --pages",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.3,
        help="模型生成温度 (默认: 0.3)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="覆盖已有 slide_prompt；默认只补全缺失页",
    )
    parser.add_argument(
        "--tui",
        action="store_true",
        help="强制使用终端交互模式",
    )
    parser.add_argument(
        "--no-tui",
        action="store_true",
        help="禁用终端交互模式，强制使用命令行参数",
    )
    args = parser.parse_args()

    # 验证配置
    try:
        validate_prompt_gen_config()
    except ConfigError as e:
        print(f"配置错误: {e}", file=sys.stderr)
        sys.exit(1)

    model = os.getenv("GEN_PROMPT_MODEL")

    data = load_json(args.json_file)
    data = sync_system_prompt(data)
    metadata = data.get("metadata", {}) or {}
    meta_prompt = load_text(args.meta_prompt_file)
    system_prompt = data.get("system_prompt", "").strip()

    if not system_prompt:
        raise ValueError("JSON 缺少 system_prompt，无法生成 slide_prompt")

    slides = data.get("slides", [])
    if should_use_tui(args):
        resolved = run_tui(
            slides=slides,
            json_file=args.json_file,
            meta_prompt_file=args.meta_prompt_file,
            temperature=args.temperature,
        )
    else:
        resolved = {
            "json_file": args.json_file,
            "meta_prompt_file": args.meta_prompt_file,
            "pages": args.pages,
            "first_n": args.first_n,
            "temperature": args.temperature,
            "overwrite": args.overwrite,
        }

    target_pages = set(
        get_target_pages(slides, resolved["pages"], resolved["first_n"])
    )
    client = build_client()

    print("=" * 60)
    print("Slide Prompt 生成工具")
    print("=" * 60)
    print(f"JSON文件: {Path(resolved['json_file']).resolve()}")
    print(f"Meta-prompt: {Path(resolved['meta_prompt_file']).resolve()}")
    print(f"Prompt模型: {model}")
    if resolved["first_n"] is not None:
        print(f"测试模式: 前 {resolved['first_n']} 页")
    print(f"目标页码: {sorted(target_pages)}")
    print(f"覆盖已有结果: {resolved['overwrite']}")
    print("=" * 60)
    print()

    updated_count = 0
    skipped_count = 0

    # 筛选需要处理的幻灯片
    slides_to_process = [
        slide for slide in slides
        if slide.get("page") in target_pages
    ]

    with tqdm(total=len(slides_to_process), desc="生成提示词", unit="页") as pbar:
        for slide in slides_to_process:
            page = slide.get("page")

            has_existing_prompt = bool((slide.get("slide_prompt") or "").strip())
            if has_existing_prompt and not resolved["overwrite"]:
                tqdm.write(f"- 第 {page} 页已存在 slide_prompt，跳过")
                skipped_count += 1
                pbar.update(1)
                continue

            slide_prompt = generate_slide_prompt(
                client=client,
                model=model,
                metadata=metadata,
                meta_prompt=meta_prompt,
                system_prompt=system_prompt,
                slide=slide,
                temperature=resolved["temperature"],
            )
            slide["slide_prompt"] = slide_prompt
            slide["prompt"] = slide_prompt
            tqdm.write(f"✓ 第 {page} 页已生成")
            updated_count += 1
            pbar.update(1)

    save_json(resolved["json_file"], data)

    print()
    print("=" * 60)
    print("处理完成")
    print(f"新增/覆盖: {updated_count}")
    print(f"跳过: {skipped_count}")
    print("=" * 60)


if __name__ == "__main__":
    main()
