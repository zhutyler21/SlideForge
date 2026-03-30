"""图片生成器 - Step 2b: 调用图像模型生成 PNG"""

from __future__ import annotations

import base64
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests
from openai import OpenAI
from tqdm import tqdm

from src.utils.openai_client import get_model


def generate_images(
    project_data: dict[str, Any],
    output_dir: str | Path,
    client: OpenAI,
    pages: set[int] | None = None,
    overwrite: bool = False,
    workers: int = 4,
    max_retries: int = 3,
) -> dict[str, Any]:
    """
    为项目中的页面生成图片

    Args:
        project_data: 项目 JSON 数据
        output_dir: 输出目录
        client: OpenAI 客户端
        pages: 要生成的页码集合（None=全部）
        overwrite: 是否覆盖已有图片
        workers: 并发线程数
        max_retries: 最大重试次数

    Returns:
        更新后的 project_data
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    model = get_model("image")
    system_prompt = project_data["generation"].get("system_prompt", "")
    slides = project_data["generation"].get("slides", [])

    if pages:
        slides = [s for s in slides if s["page"] in pages]

    # 过滤需要生成的
    tasks = []
    for slide in slides:
        page_num = slide["page"]
        slide_prompt = slide.get("slide_prompt", "").strip()
        if not slide_prompt:
            continue

        img_path = output_path / f"page_{page_num:02d}.png"
        if img_path.exists() and not overwrite:
            continue

        tasks.append((page_num, slide_prompt, img_path))

    if not tasks:
        print("没有需要生成的图片。")
        return project_data

    print(f"待生成: {len(tasks)} 页, 并发: {workers} 线程")

    results = {}

    if workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_page = {
                executor.submit(
                    _generate_single_image,
                    client, model, system_prompt,
                    prompt, page_num, img_path, max_retries,
                ): page_num
                for page_num, prompt, img_path in tasks
            }

            with tqdm(total=len(tasks), desc="生成图片", unit="页") as pbar:
                for future in as_completed(future_to_page):
                    page_num = future_to_page[future]
                    try:
                        success = future.result()
                        results[page_num] = success
                    except Exception as e:
                        tqdm.write(f"  p{page_num}: 异常 - {str(e)[:80]}")
                        results[page_num] = False
                    pbar.update(1)
    else:
        with tqdm(total=len(tasks), desc="生成图片", unit="页") as pbar:
            for page_num, prompt, img_path in tasks:
                success = _generate_single_image(
                    client, model, system_prompt,
                    prompt, page_num, img_path, max_retries,
                )
                results[page_num] = success
                pbar.update(1)

    # 更新 slides 状态
    slides_map = {s["page"]: s for s in project_data["generation"]["slides"]}
    for page_num, success in results.items():
        if page_num in slides_map:
            if success:
                slides_map[page_num]["image_status"] = "generated"
                slides_map[page_num]["image_path"] = f"output/page_{page_num:02d}.png"
            else:
                slides_map[page_num]["image_status"] = "failed"

    success_count = sum(1 for v in results.values() if v)
    fail_count = sum(1 for v in results.values() if not v)
    print(f"\n图片生成完成: 成功 {success_count}, 失败 {fail_count}")

    return project_data


def _generate_single_image(
    client: OpenAI,
    model: str,
    system_prompt: str,
    slide_prompt: str,
    page_num: int,
    output_path: Path,
    max_retries: int = 3,
) -> bool:
    """
    生成单张图片，带重试机制

    Returns:
        True=成功, False=失败
    """
    image_instruction = (
        "Generate an image based on the following description. "
        "Output only the image, no text response.\n\n"
    )
    # Lovart风格: slide_prompt已自包含所有视觉信息，system_prompt仅作补充
    full_prompt = f"{image_instruction}{slide_prompt}"

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": full_prompt}],
                temperature=0.7,
                # Gemini image generation 需要声明输出模态
                modalities=["text", "image"],
            )

            message = response.choices[0].message
            image_data = _extract_image_from_message(message)

            if image_data is None:
                # 调试：打印实际响应结构帮助排查
                content_preview = repr(message.content)[:200]
                tqdm.write(f"  p{page_num}: 响应内容预览: {content_preview}")
                raise ValueError(f"无法从响应中提取图片")

            with open(output_path, "wb") as f:
                f.write(image_data)

            tqdm.write(f"  p{page_num}: 已保存")
            return True

        except Exception as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                tqdm.write(
                    f"  p{page_num}: 失败 ({attempt + 1}/{max_retries}) "
                    f"- {str(e)[:60]}，{wait}s 后重试"
                )
                time.sleep(wait)
            else:
                tqdm.write(f"  p{page_num}: 失败（已达最大重试）- {str(e)[:80]}")
                return False

    return False


def _extract_image_from_message(message: Any) -> bytes | None:
    """
    从 chat completion 的 message 中提取图片数据。
    支持多种返回格式：
    1. 结构化 content parts（含 image_url 类型的 part）
    2. 文本中的 base64 data URI
    3. 文本中的图片 URL
    4. 纯 base64 字符串
    """
    # --- 格式1: 结构化 content parts (列表) ---
    content = message.content
    if isinstance(content, list):
        for part in content:
            # dict 格式的 part
            if isinstance(part, dict):
                # {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
                if part.get("type") == "image_url":
                    url = part.get("image_url", {}).get("url", "")
                    data = _decode_data_uri_or_url(url)
                    if data:
                        return data
                # {"type": "image", "data": "base64...", "mime_type": "image/png"}
                if part.get("type") == "image":
                    b64 = part.get("data") or part.get("source", {}).get("data", "")
                    if b64:
                        return base64.b64decode(b64)
            # 对象格式的 part (如 pydantic model)
            elif hasattr(part, "type"):
                if getattr(part, "type", None) == "image_url":
                    image_url_obj = getattr(part, "image_url", None)
                    url = getattr(image_url_obj, "url", "") if image_url_obj else ""
                    data = _decode_data_uri_or_url(url)
                    if data:
                        return data
                if getattr(part, "type", None) == "image":
                    b64 = getattr(part, "data", "") or ""
                    if not b64:
                        source = getattr(part, "source", None)
                        b64 = getattr(source, "data", "") if source else ""
                    if b64:
                        return base64.b64decode(b64)
        # 如果列表中有文本 part，也尝试从文本提取
        for part in content:
            text = ""
            if isinstance(part, dict) and part.get("type") == "text":
                text = part.get("text", "")
            elif hasattr(part, "type") and getattr(part, "type", None) == "text":
                text = getattr(part, "text", "")
            if text:
                data = _extract_image_from_text(text)
                if data:
                    return data
        return None

    # --- 格式2: 纯文本 content ---
    if isinstance(content, str):
        return _extract_image_from_text(content)

    # --- 格式3: content 为 None，检查其他属性 ---
    # 某些代理 API 可能把图片放在 message 的其他属性上
    if content is None:
        # 检查 tool_calls 或自定义字段
        raw = getattr(message, "model_extra", {}) or {}
        for key in ("image", "image_data", "images"):
            if key in raw:
                val = raw[key]
                if isinstance(val, str):
                    return base64.b64decode(val)
                if isinstance(val, list) and val:
                    return base64.b64decode(val[0])

    return None


def _decode_data_uri_or_url(url: str) -> bytes | None:
    """解析 data URI 或 HTTP URL，返回图片字节"""
    if not url:
        return None
    # data:image/png;base64,...
    m = re.match(r'data:image/[^;]+;base64,(.+)', url, re.DOTALL)
    if m:
        return base64.b64decode(m.group(1))
    # HTTP(S) URL
    if url.startswith("http"):
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.content
    return None


def _extract_image_from_text(text: str) -> bytes | None:
    """从文本字符串中提取图片数据"""
    # 尝试 markdown 格式: ![image](data:image/...;base64,...)
    b64_match = re.search(
        r'!\[.*?\]\(data:image/[^;]+;base64,([^\)]+)\)', text
    )
    if b64_match:
        return base64.b64decode(b64_match.group(1))

    # 尝试裸 data URI
    bare_data_uri = re.search(r'data:image/[^;]+;base64,([A-Za-z0-9+/=\s]+)', text)
    if bare_data_uri:
        return base64.b64decode(bare_data_uri.group(1).strip())

    # 尝试 URL 格式
    url_match = re.search(r'!\[.*?\]\((https?://[^\)]+)\)', text)
    if not url_match:
        url_match = re.search(r'(https?://[^\s]+\.(?:png|jpg|jpeg|webp))', text)

    if url_match:
        resp = requests.get(url_match.group(1), timeout=30)
        resp.raise_for_status()
        return resp.content

    # 尝试纯 base64（至少 100 字符，避免误匹配）
    pure_b64 = re.search(r'^([A-Za-z0-9+/]{100,}={0,2})$', text.strip())
    if pure_b64:
        data = base64.b64decode(pure_b64.group(1))
        # 验证是否为有效图片（PNG/JPEG 魔术字节）
        if data[:4] in (b'\x89PNG', b'\xff\xd8\xff\xe0', b'\xff\xd8\xff\xe1'):
            return data

    return None
