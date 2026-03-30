"""风格配置加载器 - 从 YAML 文件加载和管理风格配置"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

# 风格文件目录
STYLES_DIR = Path(__file__).parent.parent.parent / "styles"


def list_styles() -> list[dict[str, str]]:
    """
    列出所有可用的风格配置

    Returns:
        [{"name": "咨询报告", "display_name": "...", "description": "..."}]
    """
    styles = []
    for yaml_file in sorted(STYLES_DIR.glob("*.yaml")):
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            styles.append({
                "name": config.get("name", yaml_file.stem),
                "display_name": config.get("display_name", yaml_file.stem),
                "description": config.get("description", ""),
            })
        except Exception:
            continue
    return styles


def load_style(style_name: str) -> dict[str, Any]:
    """
    加载指定风格配置

    Args:
        style_name: 风格名称（对应 YAML 文件名，不含扩展名）

    Returns:
        完整的风格配置字典

    Raises:
        FileNotFoundError: 风格文件不存在
        ValueError: YAML 解析失败
    """
    yaml_path = STYLES_DIR / f"{style_name}.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(f"风格配置文件不存在: {yaml_path}")

    with open(yaml_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError(f"风格配置格式错误: {yaml_path}")

    errors = validate_style(config)
    if errors:
        raise ValueError(f"风格配置验证失败:\n" + "\n".join(f"  - {e}" for e in errors))

    return config


def validate_style(config: dict[str, Any]) -> list[str]:
    """
    验证风格配置的完整性

    Returns:
        错误信息列表，空列表表示验证通过
    """
    errors = []
    required_fields = ["name", "visual", "meta_prompt"]

    for field in required_fields:
        if field not in config:
            errors.append(f"缺少必需字段: {field}")

    visual = config.get("visual", {})
    if visual:
        if "resolution" not in visual:
            errors.append("visual 缺少 resolution")
        if "background_color" not in visual:
            errors.append("visual 缺少 background_color")

    return errors


def get_meta_prompt(style_config: dict[str, Any]) -> str:
    """从风格配置中提取 meta-prompt 模板"""
    return style_config.get("meta_prompt", "").strip()


def build_system_prompt_from_style(
    style_config: dict[str, Any],
) -> str:
    """
    从风格配置动态构建 system_prompt（适配所有风格，不硬编码特定风格）

    Args:
        style_config: 加载的风格 YAML 配置

    Returns:
        用于图片生成的 system_prompt 字符串
    """
    visual = style_config.get("visual", {})
    color_scheme = visual.get("color_scheme", {})

    style_name = style_config.get("name", "通用")
    style_desc = style_config.get("description", "")

    accent_colors = []
    for c in color_scheme.get("accent", []):
        accent_colors.extend(re.findall(r'#[0-9A-Fa-f]{6}', str(c)))

    bg_color = visual.get('background_color', '#FFFFFF')
    aspect = visual.get('aspect_ratio', '4:3')
    resolution = visual.get('resolution', '2048x1536')
    typography = visual.get("typography", {})
    typo_style = typography.get("style", "")

    parts = [
        f"Slide image generator for \"{style_name}\" style.",
        f"Description: {style_desc}.",
        f"Canvas: {aspect} ({resolution}). Background: {bg_color}.",
    ]

    if accent_colors:
        parts.append(f"Accent colors: {', '.join(accent_colors[:3])}.")
    if typo_style:
        parts.append(f"Typography: {typo_style}.")

    parts.append("All Chinese text must include English translation in parentheses.")
    parts.append("Every slide prompt must be self-contained with full visual details.")

    quality = style_config.get("quality", {})
    benchmark = quality.get("benchmark", "")
    if benchmark:
        parts.append(f"Quality benchmark: {benchmark}.")
    principles = quality.get("principles", [])
    if principles:
        parts.append("Principles: " + "; ".join(str(p) for p in principles[:4]) + ".")

    return " ".join(parts)


def get_style_fingerprint(style_config: dict[str, Any]) -> str:
    """
    从风格配置提取简短的风格指纹（3-5句），用作每页的固定风格锚点。
    比依赖前几页输出更稳定。
    """
    visual = style_config.get("visual", {})
    layout = visual.get("layout", {})
    typography = visual.get("typography", {})

    style_name = style_config.get("name", "")
    bg_color = visual.get("background_color", "")
    accent = visual.get("color_scheme", {}).get("accent", [])
    accent_str = ", ".join(str(c) for c in accent[:3]) if accent else ""
    density = layout.get("page_density", "")
    structure_pref = layout.get("structure_preference", "")
    typo = typography.get("title_style", "")

    lines = [f"Style: {style_name}. Background: {bg_color}."]
    if accent_str:
        lines.append(f"Accent palette: {accent_str}.")
    if density:
        lines.append(f"Page density: {density}.")
    if structure_pref:
        lines.append(f"Layout preference: {structure_pref}.")
    if typo:
        lines.append(f"Title style: {typo}.")
    return " ".join(lines)


def format_style_for_prompt(style_config: dict[str, Any]) -> str:
    """
    将风格配置格式化为可传给 LLM 的文本

    用于在生成 slide_prompt 时作为上下文传递
    """
    visual = style_config.get("visual", {})
    color_scheme = visual.get("color_scheme", {})
    typography = visual.get("typography", {})
    chart_policy = style_config.get("chart_policy", {})
    content_fw = style_config.get("content_framework", {})

    lines = [
        f"style: {style_config.get('name', '')}",
        f"description: {style_config.get('description', '')}",
        f"background_color: {visual.get('background_color', '')}",
        f"resolution: {visual.get('resolution', '')}",
        f"aspect_ratio: {visual.get('aspect_ratio', '')}",
        f"color_primary: {color_scheme.get('primary', '')}",
        f"color_accent: {color_scheme.get('accent', '')}",
        f"typography: {typography}",
        f"content_framework: {content_fw.get('method', '')}",
        f"chart_priority: {chart_policy.get('priority', [])}",
    ]

    master = style_config.get("master_template", {})
    if master:
        lines.append(f"master_template: {master}")

    page_types = style_config.get("page_types", {})
    if page_types:
        lines.append(f"page_types: {page_types}")

    return "\n".join(lines)
