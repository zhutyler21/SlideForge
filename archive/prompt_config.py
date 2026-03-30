#!/usr/bin/env python3
"""
共享的提示词配置工具。

职责:
1. 根据 JSON metadata 自动构建 system_prompt
2. 在需要时将 system_prompt 写回 JSON
3. 统一生成给 slide-prompt 模型的上下文
"""

from __future__ import annotations

import json
from typing import Any


def _clean(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _join_list(values: Any) -> str:
    if not isinstance(values, list):
        return ""
    return "; ".join(_clean(item) for item in values if _clean(item))


def _json_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return _clean(value)


def _collect_template_rules(master_template: dict[str, Any]) -> list[str]:
    if not master_template:
        return []

    rules: list[str] = []

    template_name = _clean(master_template.get("template_name", ""))
    consistency_mode = _clean(master_template.get("consistency_mode", ""))
    if template_name:
        rules.append(f"template name {template_name}")
    if consistency_mode:
        rules.append(f"consistency mode {consistency_mode}")

    canvas = master_template.get("canvas", {}) or {}
    canvas_desc = _clean(canvas.get("working_area", ""))
    if canvas_desc:
        rules.append(f"canvas working area {canvas_desc}")

    title_area = master_template.get("title_area", {}) or {}
    title_parts: list[str] = []
    for key in ("position", "width", "height", "alignment", "title_font_size", "title_weight"):
        value = _clean(title_area.get(key, ""))
        if value:
            title_parts.append(f"{key.replace('_', ' ')} {value}")
    if title_parts:
        rules.append("title area fixed: " + ", ".join(title_parts))

    header = master_template.get("header", {}) or {}
    header_parts: list[str] = []
    for key in ("enabled", "position", "height", "content", "style"):
        value = _clean(header.get(key, ""))
        if value:
            header_parts.append(f"{key.replace('_', ' ')} {value}")
    if header_parts:
        rules.append("header rule: " + ", ".join(header_parts))

    footer = master_template.get("footer", {}) or {}
    footer_parts: list[str] = []
    for key in ("enabled", "position", "height", "left_content", "right_content", "style"):
        value = _clean(footer.get(key, ""))
        if value:
            footer_parts.append(f"{key.replace('_', ' ')} {value}")
    if footer_parts:
        rules.append("footer rule: " + ", ".join(footer_parts))

    fixed_elements = master_template.get("fixed_elements", []) or []
    fixed_desc = _join_list(fixed_elements)
    if fixed_desc:
        rules.append(f"fixed repeated elements {fixed_desc}")

    locked = master_template.get("locked_elements", []) or []
    locked_desc = _join_list(locked)
    if locked_desc:
        rules.append(f"locked elements {locked_desc}")

    per_page_allowance = _clean(master_template.get("per_page_variation_rule", ""))
    if per_page_allowance:
        rules.append(f"allowed per-page variation {per_page_allowance}")

    exceptions = master_template.get("exception_handling", {}) or {}
    exception_rules: list[str] = []
    for name, desc in exceptions.items():
        clean_desc = _clean(desc)
        if clean_desc:
            exception_rules.append(f"{name.replace('_', ' ')}: {clean_desc}")
    if exception_rules:
        rules.append("template exceptions " + "; ".join(exception_rules))

    return rules


def build_system_prompt_from_metadata(metadata: dict[str, Any]) -> str:
    """构建精简的system_prompt,仅包含核心全局规则"""
    layout = metadata.get("layout", {}) or {}
    color_scheme = metadata.get("color_scheme", {}) or {}
    typography = metadata.get("typography", {}) or {}

    # 提取核心颜色(仅hex code)
    primary_raw = _clean(color_scheme.get('primary', ''))
    accent_raw = _clean(color_scheme.get('accent', ''))

    # 从长文本中提取hex codes
    import re
    primary_colors = re.findall(r'#[0-9A-Fa-f]{6}', primary_raw)
    accent_colors = re.findall(r'#[0-9A-Fa-f]{6}', accent_raw)

    primary_str = ','.join(primary_colors[:5]) if primary_colors else primary_raw[:50]
    accent_str = ','.join(accent_colors[:3]) if accent_colors else accent_raw[:50]

    # 核心规则:比例/分辨率/背景/配色/语言/框架
    essentials = [
        f"4:3 {_clean(layout.get('resolution', '2048x1536'))}",
        f"白底{_clean(metadata.get('background_color', '#FFFFFF'))}",
        f"主色{primary_str}",
        f"强调色{accent_str}",
        f"简体中文",
        f"{_clean(metadata.get('framework', 'SCQA'))}框架",
        f"{_clean(metadata.get('style', '咨询风格'))}"
    ]

    # Master template锁定规则(简化)
    master_template = metadata.get("master_template", {}) or {}
    template_lock = []
    if master_template:
        template_lock.append("固定元素:白底/顶部深蓝分隔条/左上标题框/右下页码")
        template_lock.append("仅中央内容区可变")

    # 质量要求(精简)
    quality_rules = [
        "优先内容映射而非冗长描述",
        "中文渲染:完整笔画/清晰间距/大号关键文本",
        "图表优先:表格/矩阵/时间线/流程图",
        "咨询级密度:高信息量+结构化留白"
    ]

    parts = [
        "专业PPT画图提示词生成.",
        "全局规则: " + "; ".join(essentials) + ".",
    ]

    if template_lock:
        parts.append("模板锁定: " + "; ".join(template_lock) + ".")

    parts.append("质量要求: " + "; ".join(quality_rules) + ".")

    return " ".join(parts)


def sync_system_prompt(data: dict[str, Any]) -> dict[str, Any]:
    metadata = data.get("metadata", {}) or {}
    data["system_prompt"] = build_system_prompt_from_metadata(metadata)
    return data


def format_metadata_for_prompt(metadata: dict[str, Any]) -> str:
    color_scheme = metadata.get("color_scheme", {}) or {}
    return "\n".join(
        [
            f"title: {_json_value(metadata.get('title', ''))}",
            f"total_pages: {_json_value(metadata.get('total_pages', ''))}",
            f"style: {_json_value(metadata.get('style', ''))}",
            f"background_color: {_json_value(metadata.get('background_color', ''))}",
            f"color_primary: {_json_value(color_scheme.get('primary', ''))}",
            f"color_accent: {_json_value(color_scheme.get('accent', ''))}",
            f"color_style: {_json_value(color_scheme.get('style', ''))}",
            f"framework: {_json_value(metadata.get('framework', ''))}",
            f"design_goal: {_json_value(metadata.get('design_goal', ''))}",
            f"target_aesthetic: {_json_value(metadata.get('target_aesthetic', ''))}",
            f"narrative_objective: {_json_value(metadata.get('narrative_objective', ''))}",
            f"layout: {_json_value(metadata.get('layout', {}))}",
            f"typography: {_json_value(metadata.get('typography', {}))}",
            f"content_policy: {_json_value(metadata.get('content_policy', {}))}",
            f"scqa_policy: {_json_value(metadata.get('scqa_policy', {}))}",
            f"chart_policy: {_json_value(metadata.get('chart_policy', {}))}",
            f"quality_bar: {_json_value(metadata.get('quality_bar', {}))}",
            f"high_quality_ppt_principles: {_json_value(metadata.get('high_quality_ppt_principles', {}))}",
            f"page_exception_policy: {_json_value(metadata.get('page_exception_policy', {}))}",
            f"master_template: {_json_value(metadata.get('master_template', {}))}",
        ]
    ).strip()
