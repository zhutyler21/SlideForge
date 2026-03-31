#!/usr/bin/env python3
"""
共享工具函数模块

提供跨脚本使用的通用功能:
- 页码范围解析
- 目标页面筛选
- TUI 模式判断
"""

from __future__ import annotations

import argparse
import sys
from typing import Any


def parse_page_range(range_str: str) -> list[int]:
    """
    解析页码范围字符串

    Args:
        range_str: 页码范围，如 "1-5" 或 "1,3,5" 或 "1-3,5,7-9"

    Returns:
        排序后的唯一页码列表

    Examples:
        >>> parse_page_range("1-5")
        [1, 2, 3, 4, 5]
        >>> parse_page_range("1,3,5")
        [1, 3, 5]
        >>> parse_page_range("1-3,5,7-9")
        [1, 2, 3, 5, 7, 8, 9]
    """
    pages: list[int] = []
    parts = range_str.split(",")

    for part in parts:
        part = part.strip()
        if not part:
            continue

        if "-" in part:
            start, end = map(int, part.split("-", 1))
            pages.extend(range(start, end + 1))
        else:
            pages.append(int(part))

    # 过滤无效页码（负数和0）
    pages = [p for p in pages if p > 0]
    if not pages:
        raise ValueError("没有有效的页码")
    return sorted(set(pages))


def get_target_pages(
    slides: list[dict[str, Any]],
    pages_arg: str,
    first_n: int | None,
) -> list[int]:
    """
    根据参数确定目标页码列表

    Args:
        slides: 幻灯片列表
        pages_arg: 页码范围字符串
        first_n: 仅处理前 N 页（优先级高于 pages_arg）

    Returns:
        目标页码列表

    Raises:
        ValueError: 当 first_n <= 0 时
    """
    if first_n is not None:
        if first_n <= 0:
            raise ValueError("--first-n 必须是大于 0 的整数")

        page_numbers = sorted(
            slide.get("page")
            for slide in slides
            if isinstance(slide.get("page"), int)
        )
        return page_numbers[:first_n]

    return parse_page_range(pages_arg)


def should_use_tui(args: argparse.Namespace) -> bool:
    """
    判断是否应该使用终端交互模式

    Args:
        args: 命令行参数对象，需包含 no_tui 和 tui 属性

    Returns:
        True 表示使用 TUI，False 表示使用命令行参数
    """
    if args.no_tui:
        return False
    if args.tui:
        return True
    # 无参数启动且在交互终端时默认使用 TUI
    return len(sys.argv) == 1 and sys.stdin.isatty() and sys.stdout.isatty()
