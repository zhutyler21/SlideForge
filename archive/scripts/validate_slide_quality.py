#!/usr/bin/env python3
"""
验证生成的slide_prompt是否符合咨询报告质量标准
"""

import json
import re
from typing import List, Dict


class SlidePromptValidator:
    """咨询报告slide_prompt质量验证器"""

    def __init__(self):
        self.required_colors = {
            "#1F2937": "charcoal (主标题)",
            "#2E9B6F": "consulting green (关键信息)",
            "#1E3A5F": "deep navy (结构元素)",
            "#6B7280": "cool gray (辅助信息)",
            "#D1D5DB": "light gray (分隔线)",
            "#E7F3EE": "pale mint (背景高亮)"
        }

        self.grid_zones = [
            "upper-left", "upper-center", "upper-right",
            "middle-left", "middle-center", "middle-right",
            "lower-left", "lower-center", "lower-right",
            "spanning"
        ]

        self.chart_keywords = [
            "时间线", "timeline", "表格", "table", "矩阵", "matrix",
            "流程图", "flow", "对比", "comparison", "框", "box",
            "图表", "chart", "列表", "list", "结论", "insight"
        ]

    def validate_slide(self, slide: dict, page_num: int) -> Dict[str, any]:
        """验证单页slide_prompt"""
        prompt = slide.get("slide_prompt", "")
        page_type = slide.get("page_type", "content")

        issues = []
        warnings = []
        score = 100

        # 1. 检查是否使用grid定位
        has_grid = any(zone in prompt for zone in self.grid_zones)
        if not has_grid:
            issues.append("❌ 未使用grid定位语法")
            score -= 30

        # 2. 检查颜色使用
        used_colors = set(re.findall(r'#[0-9A-Fa-f]{6}', prompt))
        if not used_colors:
            warnings.append("⚠️  未使用任何颜色标注")
            score -= 10
        elif "#2E9B6F" not in used_colors and page_type == "content":
            warnings.append("⚠️  内容页未使用consulting green高亮关键信息")
            score -= 5

        # 3. 检查是否包含图表
        has_chart = any(kw in prompt for kw in self.chart_keywords)
        if not has_chart and page_type not in ["cover", "section_divider"]:
            issues.append("❌ 内容页缺少实质性图表")
            score -= 25

        # 4. 检查长度(避免冗长描述)
        if len(prompt) > 800:
            warnings.append("⚠️  提示词过长,可能包含冗余描述")
            score -= 10

        # 5. 检查是否重复metadata规则
        redundant_keywords = [
            "white background", "4:3", "2048x1536",
            "master template", "professional consulting"
        ]
        if any(kw in prompt.lower() for kw in redundant_keywords):
            issues.append("❌ 重复描述了metadata中的全局规则")
            score -= 15

        # 6. 检查中文内容是否用引号
        chinese_pattern = r'[\u4e00-\u9fff]{3,}'
        chinese_texts = re.findall(chinese_pattern, prompt)
        unquoted_chinese = [
            text for text in chinese_texts
            if f'"{text}"' not in prompt and f'"{text}' not in prompt
        ]
        if unquoted_chinese and len(unquoted_chinese) > 2:
            warnings.append(f"⚠️  部分中文内容未用引号标注: {unquoted_chinese[:2]}")
            score -= 5

        # 7. 特殊页面类型检查
        if page_type == "cover" and len(prompt) > 300:
            warnings.append("⚠️  封面页应保持极简,当前描述过于复杂")
            score -= 5

        if page_type == "summary" and "结论" not in prompt and "洞察" not in prompt:
            warnings.append("⚠️  总结页应包含明确的结论框")
            score -= 10

        return {
            "page": page_num,
            "page_type": page_type,
            "score": max(0, score),
            "issues": issues,
            "warnings": warnings,
            "used_colors": list(used_colors),
            "has_grid": has_grid,
            "has_chart": has_chart,
            "prompt_length": len(prompt)
        }

    def generate_report(self, json_file: str) -> dict:
        """生成完整的质量报告"""
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        slides = data.get("slides", [])
        results = []

        print("=" * 80)
        print("咨询报告Slide Prompt质量验证报告")
        print("=" * 80)

        for slide in slides:
            page_num = slide.get("page")
            result = self.validate_slide(slide, page_num)
            results.append(result)

            # 打印单页结果
            status = "✓" if result["score"] >= 80 else "⚠" if result["score"] >= 60 else "✗"
            print(f"\n{status} Page {page_num} ({result['page_type']}) - 得分: {result['score']}/100")

            if result["issues"]:
                for issue in result["issues"]:
                    print(f"  {issue}")

            if result["warnings"]:
                for warning in result["warnings"]:
                    print(f"  {warning}")

        # 统计总结
        print("\n" + "=" * 80)
        print("总体统计")
        print("=" * 80)

        avg_score = sum(r["score"] for r in results) / len(results)
        excellent = sum(1 for r in results if r["score"] >= 90)
        good = sum(1 for r in results if 80 <= r["score"] < 90)
        needs_improvement = sum(1 for r in results if r["score"] < 80)

        print(f"平均得分: {avg_score:.1f}/100")
        print(f"优秀(≥90分): {excellent}页")
        print(f"良好(80-89分): {good}页")
        print(f"需改进(<80分): {needs_improvement}页")

        # 常见问题统计
        all_issues = []
        all_warnings = []
        for r in results:
            all_issues.extend(r["issues"])
            all_warnings.extend(r["warnings"])

        if all_issues:
            print("\n最常见的问题:")
            issue_counts = {}
            for issue in all_issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
            for issue, count in sorted(issue_counts.items(), key=lambda x: -x[1])[:5]:
                print(f"  {issue} ({count}次)")

        return {
            "average_score": avg_score,
            "excellent_count": excellent,
            "good_count": good,
            "needs_improvement_count": needs_improvement,
            "detailed_results": results
        }


def main():
    import sys

    json_file = sys.argv[1] if len(sys.argv) > 1 else "data/ai_agent_report_slides.json"

    validator = SlidePromptValidator()
    report = validator.generate_report(json_file)

    # 保存详细报告
    output_file = json_file.replace('.json', '_quality_report.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n详细报告已保存到: {output_file}")


if __name__ == "__main__":
    main()
