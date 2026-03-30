#!/usr/bin/env python3
"""
自动分析并标注页面类型,为差异化处理提供基础
"""

import json
import re
from pathlib import Path
from typing import Literal

PageType = Literal["cover", "section_divider", "content", "summary", "comparison", "timeline"]


def classify_page_type(slide: dict) -> PageType:
    """
    根据页面特征自动分类
    """
    page = slide.get("page", 0)
    section = slide.get("section", "").lower()
    title = slide.get("title", "").lower()
    content = slide.get("content", "")

    # 封面页
    if page == 1 or "封面" in section:
        return "cover"

    # 章节分隔页
    if "章节概览" in title or "概览" in title or len(content) < 200:
        return "section_divider"

    # 总结页
    if "总结" in title or "结论" in title or "answer" in title.lower():
        return "summary"

    # 对比分析页
    comparison_keywords = ["对比", "vs", "比较", "差异", "优劣", "before", "after"]
    if any(kw in title or kw in content[:200] for kw in comparison_keywords):
        return "comparison"

    # 时间线页
    timeline_keywords = ["时间线", "历史", "演进", "里程碑", "发展史", "timeline"]
    if any(kw in title or kw in content[:200] for kw in timeline_keywords):
        return "timeline"

    # 默认为内容页
    return "content"


def analyze_content_structure(content: str) -> dict:
    """
    分析内容结构,提取关键信息
    """
    # 统计数字/数据点
    numbers = re.findall(r'\d+[.,]?\d*[%倍x×]', content)

    # 识别列表结构
    has_list = bool(re.search(r'[1-9]\)|[1-9]\.|\n-|\n•', content))

    # 识别对比结构
    has_comparison = bool(re.search(r'(相反|然而|但是|而|vs|对比)', content))

    # 识别时间信息
    time_markers = re.findall(r'\d{4}年|\d{1,2}月', content)

    # 识别因果关系
    has_causality = bool(re.search(r'(因此|所以|导致|促使|使得|从而)', content))

    return {
        "data_points": len(numbers),
        "has_list_structure": has_list,
        "has_comparison": has_comparison,
        "time_markers": len(time_markers),
        "has_causality": has_causality,
        "content_length": len(content),
        "key_numbers": numbers[:5]  # 前5个关键数字
    }


def suggest_chart_type(page_type: PageType, structure: dict) -> list[str]:
    """
    根据页面类型和内容结构推荐图表类型
    """
    suggestions = []

    if page_type == "cover":
        suggestions.append("极简几何装饰")

    elif page_type == "section_divider":
        suggestions.append("章节编号+thin分隔线")

    elif page_type == "timeline":
        suggestions.append("横向时间线")
        if structure["data_points"] > 3:
            suggestions.append("里程碑标注")

    elif page_type == "comparison":
        suggestions.append("左右对比框")
        if structure["data_points"] > 5:
            suggestions.append("多维对比表")

    elif page_type == "summary":
        suggestions.append("核心洞察框")
        suggestions.append("行动建议列表")

    else:  # content
        if structure["time_markers"] > 2:
            suggestions.append("时间线图")

        if structure["has_comparison"]:
            suggestions.append("对比表格")

        if structure["has_causality"]:
            suggestions.append("因果流程图")

        if structure["has_list_structure"]:
            suggestions.append("结构化列表框")

        if structure["data_points"] > 3:
            suggestions.append("数据可视化图表")

        # 默认至少推荐一个
        if not suggestions:
            suggestions.append("结构化内容框")

    return suggestions


def enrich_slides_metadata(json_file: str, output_file: str = None):
    """
    为JSON中的每页添加类型标注和图表建议
    """
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    slides = data.get("slides", [])

    for slide in slides:
        # 分类页面类型
        page_type = classify_page_type(slide)
        slide["page_type"] = page_type

        # 分析内容结构
        content = slide.get("content", "")
        structure = analyze_content_structure(content)
        slide["content_structure"] = structure

        # 推荐图表类型
        chart_suggestions = suggest_chart_type(page_type, structure)
        slide["suggested_charts"] = chart_suggestions

        print(f"Page {slide.get('page')}: {page_type} | Charts: {', '.join(chart_suggestions)}")

    # 保存结果
    output_path = output_file or json_file.replace('.json', '_enriched.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 已保存到: {output_path}")

    # 统计报告
    type_counts = {}
    for slide in slides:
        pt = slide.get("page_type", "unknown")
        type_counts[pt] = type_counts.get(pt, 0) + 1

    print("\n页面类型分布:")
    for pt, count in sorted(type_counts.items()):
        print(f"  {pt}: {count}页")


if __name__ == "__main__":
    import sys

    json_file = sys.argv[1] if len(sys.argv) > 1 else "data/ai_agent_report_slides.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    enrich_slides_metadata(json_file, output_file)
