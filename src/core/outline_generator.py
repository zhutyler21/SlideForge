"""大纲生成器 - Step 1: 从参考文档生成 PPT 大纲"""

from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI
from tqdm import tqdm

from src.utils.openai_client import chat_with_retry, get_model


def generate_chapter_framework(
    source_text: str,
    total_pages: int,
    style_config: dict[str, Any],
    client: OpenAI,
) -> dict[str, Any]:
    """
    Phase 1: 生成章节框架（章节分组 + 每页标题）

    Args:
        source_text: 参考文档全文
        total_pages: 目标页数
        style_config: 风格配置
        client: OpenAI 客户端

    Returns:
        {
            "inferred": {"title": ..., "audience": ..., "tone": ..., "key_themes": [...]},
            "chapters": [
                {"chapter_index": 1, "chapter_title": "...", "pages": [
                    {"page": 1, "title": "...", "page_type": "cover", "content_brief": "..."}
                ]}
            ]
        }
    """
    model = get_model("outline")
    content_fw = style_config.get("content_framework", {})
    framework_method = content_fw.get("method", "narrative")

    system_prompt = _build_framework_system_prompt(style_config)
    user_prompt = _build_framework_user_prompt(source_text, total_pages, framework_method)

    response = chat_with_retry(
        client,
        model=model,
        temperature=0.4,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.choices[0].message.content
    return _parse_framework_response(content)


def regenerate_chapter_framework(
    source_text: str,
    total_pages: int,
    style_config: dict[str, Any],
    client: OpenAI,
    feedback: str,
) -> dict[str, Any]:
    """带用户反馈重新生成章节框架"""
    model = get_model("outline")
    content_fw = style_config.get("content_framework", {})
    framework_method = content_fw.get("method", "narrative")

    system_prompt = _build_framework_system_prompt(style_config)
    user_prompt = _build_framework_user_prompt(source_text, total_pages, framework_method)
    user_prompt += f"\n\n用户反馈（请据此调整框架）:\n{feedback}"

    response = chat_with_retry(
        client,
        model=model,
        temperature=0.4,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.choices[0].message.content
    return _parse_framework_response(content)


def expand_page_details(
    source_text: str,
    framework: dict[str, Any],
    style_config: dict[str, Any],
    client: OpenAI,
) -> list[dict[str, Any]]:
    """
    Phase 2: 为每页生成详细内容（content_detail）

    Args:
        source_text: 参考文档全文
        framework: Phase 1 生成的框架
        style_config: 风格配置
        client: OpenAI 客户端

    Returns:
        更新后的 chapters 列表（每页增加 content_detail 字段）
    """
    model = get_model("outline")
    chapters = framework.get("chapters", [])
    content_fw = style_config.get("content_framework", {})
    page_types_config = style_config.get("page_types", {})

    system_prompt = _build_expand_system_prompt(style_config)

    all_pages = []
    for ch in chapters:
        for page in ch.get("pages", []):
            all_pages.append((ch, page))

    # 构建完整大纲摘要（所有页的标题+简述），供每页展开时参考
    outline_summary = _build_outline_summary(chapters)

    with tqdm(total=len(all_pages), desc="展开详细内容", unit="页") as pbar:
        for idx, (chapter, page) in enumerate(all_pages):
            # 收集已展开页面的内容作为上下文
            expanded_context = _build_expanded_context(all_pages[:idx])

            # 获取当前 page_type 对应的配置
            pt = page.get("page_type", "content")
            page_type_config = page_types_config.get(pt, {})

            user_prompt = _build_expand_user_prompt(
                chapter_title=chapter.get("chapter_title", ""),
                page=page,
                content_framework=content_fw,
                outline_summary=outline_summary,
                expanded_context=expanded_context,
                page_type_config=page_type_config,
            )

            response = chat_with_retry(
                client,
                model=model,
                temperature=0.3,
                max_tokens=2048,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            detail = response.choices[0].message.content
            if isinstance(detail, str):
                page["content_detail"] = detail.strip()
            else:
                page["content_detail"] = str(detail).strip()

            tqdm.write(f"  p{page.get('page', '?')}: {page.get('title', '')[:30]}")
            pbar.update(1)

    return chapters


# ---- Internal helpers ----

def _build_framework_system_prompt(style_config: dict[str, Any]) -> str:
    name = style_config.get("name", "通用")
    content_fw = style_config.get("content_framework", {})
    method = content_fw.get("method", "narrative")
    description = content_fw.get("description", "")

    # 从 YAML 提取 page_types 规则
    page_types = style_config.get("page_types", {})
    page_types_desc = ""
    available_types = []
    if page_types:
        lines = []
        for pt_name, pt_config in page_types.items():
            available_types.append(pt_name)
            rules = pt_config.get("rules", "") if isinstance(pt_config, dict) else ""
            density = pt_config.get("density", "") if isinstance(pt_config, dict) else ""
            lines.append(f"  - {pt_name}: {rules} (density: {density})")
        page_types_desc = "\n".join(lines)
    if not available_types:
        available_types = ["cover", "section_divider", "content", "summary"]

    # 从 YAML 提取 structure_rules
    structure_rules = style_config.get("structure_rules", {})

    # 从 content_framework 中提取更详细的策略
    policy = content_fw.get("policy", content_fw.get("scqa_policy", {}))
    policy_desc = ""
    if isinstance(policy, dict):
        for key, val in policy.items():
            policy_desc += f"\n  {key}: {val}"

    # 构建结构约束段落
    divider_rule = structure_rules.get("section_divider", "optional")
    cover_rule = structure_rules.get("cover", "required")
    summary_rule = structure_rules.get("summary", "recommended")

    structure_guidance = f"""
结构约束:
- 封面(cover): {cover_rule}
- 章节分隔页(section_divider): {divider_rule}{"（不要生成 section_divider 页面）" if divider_rule == "none" else ""}
- 总结页(summary): {summary_rule}"""

    pages_range = structure_rules.get("pages_per_chapter", "")
    if pages_range:
        structure_guidance += f"\n- 每章页数范围: {pages_range}"

    return f"""你是一位资深的PPT内容策划专家。你的任务是根据用户提供的参考文档，规划一份"{name}"风格的PPT大纲。

内容框架: {method}
{description}{policy_desc}

页面类型说明（每页必须指定其中之一）:
{page_types_desc if page_types_desc else "  - cover: 封面, section_divider: 章节分隔, content: 内容, summary: 总结"}
{structure_guidance}

你必须返回一个JSON对象（不要包含markdown代码块标记），格式如下:
{{
  "inferred": {{
    "title": "推断的PPT标题",
    "audience": "推断的目标受众",
    "tone": "推断的语气风格",
    "key_themes": ["主题1", "主题2", "主题3"]
  }},
  "chapters": [
    {{
      "chapter_index": 1,
      "chapter_title": "章节标题",
      "pages": [
        {{
          "page": 1,
          "title": "页面标题",
          "page_type": "cover",
          "content_brief": "这页要呈现的核心内容简述（1-2句话）"
        }}
      ]
    }}
  ]
}}

page_type 可选值: {", ".join(available_types)}

注意:
- 从参考文档中推断标题、受众、语气，不要要求用户额外输入
- content_brief 是对该页核心内容的中文简述
- 严格遵守用户要求的总页数
- 严格遵守上面的结构约束和页面类型规则"""


def _build_framework_user_prompt(
    source_text: str,
    total_pages: int,
    framework_method: str,
) -> str:
    # 截断过长文本，保留前后
    max_len = 80000
    if len(source_text) > max_len:
        half = max_len // 2
        source_text = source_text[:half] + "\n\n...[中间内容省略]...\n\n" + source_text[-half:]

    return f"""请根据以下参考文档，规划一份 {total_pages} 页的PPT大纲。

使用 {framework_method} 框架组织内容。

参考文档全文:
---
{source_text}
---

请严格输出JSON格式，总页数必须为 {total_pages} 页。"""


def _build_expand_system_prompt(style_config: dict[str, Any]) -> str:
    name = style_config.get("name", "通用")
    content_policy = style_config.get("content_policy", {})
    preserve = content_policy.get("preserve_original", True)
    chart_policy = style_config.get("chart_policy", {})
    chart_priority = chart_policy.get("priority", [])
    chart_rules = chart_policy.get("rules", "")

    # 从 page_types 中获取各类型的密度描述
    page_types = style_config.get("page_types", {})
    density_guide = ""
    if page_types:
        lines = []
        for pt_name, pt_config in page_types.items():
            if isinstance(pt_config, dict):
                density = pt_config.get("density", "medium")
                word_count = pt_config.get("word_count", "")
                if word_count:
                    lines.append(f"  - {pt_name}: density={density}, word_count={word_count}")
                else:
                    lines.append(f"  - {pt_name}: density={density}")
        if lines:
            density_guide = "各页面类型的内容密度:\n" + "\n".join(lines)

    # 视觉化建议
    visual_hint = ""
    if chart_priority:
        visual_hint = f"优先使用的可视化类型: {', '.join(str(c) for c in chart_priority[:6])}"
    if chart_rules:
        visual_hint += f"\n图表规则: {chart_rules}"

    return f"""你是PPT内容撰写专家，正在为"{name}"风格的PPT填充每页的详细内容。

你的任务: 根据参考文档和页面标题，为这一页生成结构化的中文内容。

输出格式（严格遵守）:
---
核心论点: （一句话概括本页要传递的关键信息）
要点:
- 要点1
- 要点2
- 要点3（根据需要增减）
数据: （列出本页涉及的关键数字、百分比、对比数据，没有则写"无"）
建议可视化: （推荐一种最适合本页的图表/可视化类型，如时间线、对比表、流程图等）
详细内容:
（展开的段落内容）
---

{density_guide if density_guide else "默认字数: 200-600字（视内容复杂度而定）"}

{visual_hint if visual_hint else ""}

内容要求:
- {"忠实保留原文信息，不要删减实质性内容" if preserve else "可以适当精简和重组"}
- 保留原文中的关键数据、术语和论点
- 根据页面类型的 density 控制内容量：minimal/very_low 页面内容要极简，high 页面内容要丰富"""


def _build_outline_summary(chapters: list[dict[str, Any]]) -> str:
    """构建完整大纲摘要，让AI了解整体结构"""
    lines = []
    for ch in chapters:
        lines.append(f"【第{ch.get('chapter_index', '?')}章: {ch.get('chapter_title', '')}】")
        for page in ch.get("pages", []):
            lines.append(
                f"  p{page.get('page', '?')} [{page.get('page_type', '')}] "
                f"{page.get('title', '')} — {page.get('content_brief', '')}"
            )
    return "\n".join(lines)


def _build_expanded_context(
    previous_pages: list[tuple[dict, dict]],
    max_pages: int = 5,
) -> str:
    """收集最近已展开页面的内容摘要，避免重复和断裂"""
    if not previous_pages:
        return ""
    # 取最近 max_pages 页
    recent = previous_pages[-max_pages:]
    lines = []
    for ch, page in recent:
        detail = page.get("content_detail", "")
        if detail:
            # 截断过长的已展开内容
            preview = detail[:300] + "..." if len(detail) > 300 else detail
            lines.append(
                f"p{page.get('page', '?')} [{page.get('title', '')}]:\n{preview}"
            )
    return "\n\n".join(lines)


def _build_expand_user_prompt(
    chapter_title: str,
    page: dict[str, Any],
    content_framework: dict[str, Any],
    outline_summary: str = "",
    expanded_context: str = "",
    page_type_config: dict[str, Any] | None = None,
) -> str:
    page_type = page.get('page_type', 'content')
    density = ""
    word_count = ""
    if page_type_config and isinstance(page_type_config, dict):
        density = page_type_config.get("density", "")
        word_count = page_type_config.get("word_count", "")

    prompt = f"""请为以下PPT页面生成结构化内容:

章节: {chapter_title}
页码: {page.get('page', '')}
标题: {page.get('title', '')}
页面类型: {page_type}
内容简述: {page.get('content_brief', '')}"""

    if density:
        prompt += f"\n内容密度: {density}"
    if word_count:
        prompt += f"\n目标字数: {word_count}字"

    if outline_summary:
        prompt += f"""

完整大纲（请确保本页内容与整体结构协调，不要与其他页面重复）:
---
{outline_summary}
---"""

    if expanded_context:
        prompt += f"""

前几页已展开的内容（请确保本页内容与前页衔接连贯、不重复）:
---
{expanded_context}
---"""

    prompt += """

请严格按照 system prompt 要求的结构化格式输出。注意与整体大纲结构保持一致，避免与其他页面重复。"""

    return prompt


def _parse_framework_response(content: str) -> dict[str, Any]:
    """解析 LLM 返回的框架 JSON"""
    text = content.strip()

    # 去除可能的 markdown 代码块
    if text.startswith("```"):
        lines = text.split("\n")
        # 找到第一个非 ``` 行
        start = 1
        end = len(lines) - 1
        if lines[-1].strip() == "```":
            end = len(lines) - 1
        text = "\n".join(lines[start:end]).strip()
        if text.startswith("json"):
            text = text[4:].strip()

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        # 尝试在文本中找到 JSON 对象：先贪婪（最外层），再非贪婪（内层）
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                result = json.loads(json_match.group())
            except json.JSONDecodeError:
                # 贪婪匹配可能包含尾部垃圾，回退到非贪婪
                json_match = re.search(r'\{[\s\S]*?\}', text)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    raise ValueError(f"无法解析 AI 返回的框架 JSON:\n{text[:500]}")
        else:
            raise ValueError(f"无法解析 AI 返回的框架 JSON:\n{text[:500]}")

    # 验证基本结构
    if "chapters" not in result:
        raise ValueError("AI 返回的 JSON 缺少 chapters 字段")

    return result
