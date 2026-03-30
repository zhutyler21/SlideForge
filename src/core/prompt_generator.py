"""提示词生成器 - Step 2a: 为每页生成英文 slide_prompt"""

from __future__ import annotations

from typing import Any

from openai import OpenAI
from tqdm import tqdm

from src.core.style_loader import (
    build_system_prompt_from_style,
    format_style_for_prompt,
    get_meta_prompt,
    get_style_fingerprint,
)
from src.utils.openai_client import chat_with_retry, get_model

# 画幅 → 2K 分辨率映射
ASPECT_RATIO_MAP: dict[str, str] = {
    "16:9": "2560x1440",
    "4:3": "2048x1536",
}


def generate_slide_prompts(
    project_data: dict[str, Any],
    style_config: dict[str, Any],
    client: OpenAI,
    pages: set[int] | None = None,
    overwrite: bool = False,
    reference_analysis: str = "",
    custom_style_text: str = "",
    source_text: str = "",
    aspect_ratio: str = "16:9",
) -> dict[str, Any]:
    """
    为项目中的页面生成 slide_prompt

    Args:
        project_data: 项目 JSON 数据
        style_config: 风格配置
        client: OpenAI 客户端
        pages: 要生成的页码集合（None=全部）
        overwrite: 是否覆盖已有的 slide_prompt
        reference_analysis: 参考图片分析结果
        custom_style_text: 用户自定义风格文本描述
        aspect_ratio: 画幅比例，"16:9" 或 "4:3"

    Returns:
        更新后的 project_data
    """
    # 用用户选择的画幅覆盖 style_config 中的默认值
    resolution = ASPECT_RATIO_MAP.get(aspect_ratio, "2560x1440")
    style_config = _override_aspect_ratio(style_config, aspect_ratio, resolution)

    model = get_model("prompt")
    meta_prompt = get_meta_prompt(style_config)
    system_prompt = build_system_prompt_from_style(style_config)
    style_context = format_style_for_prompt(style_config)
    style_fingerprint = get_style_fingerprint(style_config)

    # 存储 system_prompt
    project_data["generation"]["system_prompt"] = system_prompt

    # 收集所有页面
    all_pages = _collect_pages(project_data)
    if pages:
        all_pages = [p for p in all_pages if p["page"] in pages]

    # 初始化 slides 数组（如果为空）
    existing_slides = {
        s["page"]: s for s in project_data["generation"].get("slides", [])
    }

    updated = 0
    skipped = 0
    # 收集已生成的 slide_prompt 作为风格锚点
    generated_prompts: list[dict[str, str]] = []

    with tqdm(total=len(all_pages), desc="生成提示词", unit="页") as pbar:
        for page_info in all_pages:
            page_num = page_info["page"]
            existing = existing_slides.get(page_num, {})

            # 检查是否需要生成
            if existing.get("slide_prompt") and not overwrite:
                # 已有的 prompt 也加入锚点列表，保持风格连贯
                generated_prompts.append({
                    "page": str(page_num),
                    "prompt": existing["slide_prompt"],
                })
                tqdm.write(f"  p{page_num}: 已存在，跳过")
                skipped += 1
                pbar.update(1)
                continue

            # 生成 slide_prompt（传入风格指纹 + 前几页锚点 + 原始文档）
            slide_prompt = _generate_single_prompt(
                client=client,
                model=model,
                meta_prompt=meta_prompt,
                system_prompt=system_prompt,
                style_context=style_context,
                style_fingerprint=style_fingerprint,
                page_info=page_info,
                previous_prompts=generated_prompts[-3:],
                source_text=source_text,
                reference_analysis=reference_analysis,
                custom_style_text=custom_style_text,
            )

            # 更新或创建 slide 记录
            existing_slides[page_num] = {
                "page": page_num,
                "slide_prompt": slide_prompt,
                "image_path": existing.get("image_path", f"output/page_{page_num:02d}.png"),
                "image_status": existing.get("image_status", "pending"),
            }

            # 加入锚点列表
            generated_prompts.append({
                "page": str(page_num),
                "prompt": slide_prompt,
            })

            tqdm.write(f"  p{page_num}: 已生成")
            updated += 1
            pbar.update(1)

    # 排序保存
    project_data["generation"]["slides"] = sorted(
        existing_slides.values(), key=lambda s: s["page"]
    )

    print(f"\n提示词生成完成: 新增/更新 {updated}, 跳过 {skipped}")
    return project_data


def _override_aspect_ratio(
    style_config: dict[str, Any],
    aspect_ratio: str,
    resolution: str,
) -> dict[str, Any]:
    """用用户选择的画幅覆盖 style_config（浅拷贝，不修改原始配置）"""
    import copy
    cfg = copy.deepcopy(style_config)
    visual = cfg.setdefault("visual", {})
    visual["aspect_ratio"] = aspect_ratio
    visual["resolution"] = resolution
    return cfg


def _collect_pages(project_data: dict[str, Any]) -> list[dict[str, Any]]:
    """从大纲中收集所有页面信息"""
    pages = []
    for ch in project_data.get("outline", {}).get("chapters", []):
        chapter_title = ch.get("chapter_title", "")
        for page in ch.get("pages", []):
            pages.append({
                "page": page.get("page", 0),
                "title": page.get("title", ""),
                "chapter_title": chapter_title,
                "page_type": page.get("page_type", "content"),
                "content_brief": page.get("content_brief", ""),
                "content_detail": page.get("content_detail", ""),
            })
    return sorted(pages, key=lambda p: p["page"])


def _generate_single_prompt(
    client: OpenAI,
    model: str,
    meta_prompt: str,
    system_prompt: str,
    style_context: str,
    page_info: dict[str, Any],
    style_fingerprint: str = "",
    previous_prompts: list[dict[str, str]] | None = None,
    source_text: str = "",
    reference_analysis: str = "",
    custom_style_text: str = "",
) -> str:
    """为单页生成 slide_prompt（动态适配所有风格）"""
    content = page_info['content_detail'] or page_info['content_brief']
    page_type = page_info['page_type']
    bg_color = _get_bg_color(style_context)

    user_prompt = (
        "Generate one self-contained image-generation prompt for this slide.\n\n"
        "**Output format**: A single continuous paragraph in natural language English, "
        "directly usable by an image generation model. Do NOT use grid syntax, "
        "bullet points, or markdown formatting. The prompt must be self-contained — "
        "include background color, style, color scheme, layout, all text content "
        "(Chinese with English translations in parentheses), visualization types, "
        "and density level.\n\n"
        "**Required structure**:\n"
        "1. Opening: State the slide style and background color explicitly\n"
        "2. Body: Detailed content with specific data, Chinese text with (English translation), "
        "concrete chart/diagram descriptions (not just type names)\n"
        "3. Closing: Summarize the color palette and density level for this style\n\n"
    )

    # 注入风格指纹作为稳定锚点（有参考图时标注视觉属性来自参考图）
    if style_fingerprint:
        if reference_analysis:
            user_prompt += (
                f"**Style fingerprint** (governs layout density, typography hierarchy, spacing, "
                f"and content structure — colors, art style, effects, and decorations will be "
                f"overridden by reference images below):\n{style_fingerprint}\n\n"
            )
        else:
            user_prompt += f"**Style fingerprint** (apply consistently to every slide):\n{style_fingerprint}\n\n"

    user_prompt += (
        f"style_context:\n{style_context}\n\n"
        f"page: {page_info['page']}\n"
        f"chapter: {page_info['chapter_title']}\n"
        f"title: {page_info['title']}\n"
        f"page_type: {page_type}\n"
        f"content:\n{content}\n\n"
    )

    # 原始参考文档
    if source_text:
        max_source_len = 8000
        source_snippet = source_text[:max_source_len]
        if len(source_text) > max_source_len:
            source_snippet += "\n...[truncated]..."
        user_prompt += (
            f"original_source_document (authoritative content source — "
            f"ensure slide content aligns with original text):\n"
            f"---\n{source_snippet}\n---\n\n"
        )

    # 参考图片风格分析（优先级高于 YAML 所有视觉设置）
    if reference_analysis:
        user_prompt += (
            f"**REFERENCE IMAGE VISUAL OVERRIDE** (HIGHEST PRIORITY — the visual "
            f"attributes below OVERRIDE the style_context defaults above, including: "
            f"color palette, background color, illustration/art style, visual effects, "
            f"decorative elements, shadows, gradients, textures, icon style, "
            f"and overall aesthetic. The style_context STILL governs: layout density, "
            f"grid structure, typography hierarchy, spacing, and content structure):\n"
            f"---\n{reference_analysis}\n---\n\n"
        )

    # 用户自定义风格文本（与参考图分析互补，用户意图优先级最高）
    if custom_style_text:
        if reference_analysis:
            user_prompt += (
                f"**USER STYLE DIRECTIVE** (refines and takes priority over the "
                f"REFERENCE IMAGE analysis above — use these specific attributes "
                f"to override or supplement the reference image analysis; any color, "
                f"art style, or effect specified here wins over conflicting reference "
                f"image attributes):\n"
                f"---\n{custom_style_text}\n---\n\n"
            )
        else:
            user_prompt += (
                f"**USER STYLE DIRECTIVE** (HIGHEST PRIORITY — the visual attributes "
                f"below OVERRIDE the style_context defaults above, including: color "
                f"palette, background color, illustration/art style, visual effects, "
                f"decorative elements, and overall aesthetic. The style_context STILL "
                f"governs: layout density, grid structure, typography hierarchy, "
                f"spacing, and content structure):\n"
                f"---\n{custom_style_text}\n---\n\n"
            )

    # 前几页的 slide_prompt 作为风格锚点
    if previous_prompts:
        anchors = "\n\n".join(
            f"[Page {p['page']}]:\n{p['prompt'][:600]}"
            for p in previous_prompts
        )
        user_prompt += (
            f"previous_slide_prompts (match this exact style, tone, and format — "
            f"your output must read like a continuation of these):\n---\n{anchors}\n---\n\n"
        )

    # 根据风格来源组合，调整优先级指令
    has_visual_override = bool(reference_analysis or custom_style_text)
    if has_visual_override:
        priority_parts = []
        if custom_style_text:
            priority_parts.append("USER STYLE DIRECTIVE (highest priority)")
        if reference_analysis:
            priority_parts.append("REFERENCE IMAGE VISUAL OVERRIDE")
        priority_str = " and ".join(priority_parts)
        user_prompt += (
            "CRITICAL: Output only the image-generation prompt paragraph. "
            "No explanations, no markdown, no labels. "
            "The prompt must be self-contained and follow the natural-language style "
            "shown in the examples from the meta_prompt. "
            f"PRIORITY RULE: The {priority_str} section(s) take highest priority "
            "for: color palette, background color, illustration/art style, visual effects "
            "(shadows, gradients, textures), decorative elements, icon style, and overall aesthetic. "
            "Reproduce these visual directives faithfully. "
            "The style_context STILL governs: layout density, grid structure, typography hierarchy, "
            "spacing, content structure, page types, and text formatting rules.\n"
        )
    else:
        user_prompt += (
            "CRITICAL: Output only the image-generation prompt paragraph. "
            "No explanations, no markdown, no labels. "
            "The prompt must be self-contained and follow the natural-language style "
            "shown in the examples from the meta_prompt. "
            "Strictly match the visual style described in the style_context — "
            "do NOT default to consulting/corporate style unless the style_context specifies it.\n"
        )

    response = chat_with_retry(
        client,
        model=model,
        temperature=0.3,
        messages=[
            {"role": "system", "content": meta_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.choices[0].message.content
    result = _extract_text(content)
    if not result:
        raise ValueError(f"第 {page_info['page']} 页返回空 slide_prompt")
    return result


def _get_bg_color(style_context: str) -> str:
    """从 style_context 中提取背景色"""
    for line in style_context.split("\n"):
        if line.startswith("background_color:"):
            color = line.split(":", 1)[1].strip()
            if color:
                return color
    return "#F3F4EF"


def _extract_text(content) -> str:
    """从 API 响应中提取文本"""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if getattr(item, "type", None) == "text":
                parts.append(getattr(item, "text", ""))
            elif isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        return "\n".join(p.strip() for p in parts if p.strip()).strip()
    return str(content).strip()
