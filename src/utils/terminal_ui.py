#!/usr/bin/env python3
"""
轻量级终端交互工具。

不依赖第三方库，提供适合脚本场景的简洁 TUI。
"""

from __future__ import annotations

import sys
from typing import Callable


def is_interactive_terminal() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def prompt_yes_no(message: str, default: bool = False) -> bool:
    suffix = "Y/n" if default else "y/N"
    while True:
        raw = input(f"{message} ({suffix}): ").strip().lower()
        if not raw:
            return default
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        print("请输入 y 或 n。")


def prompt_text(
    message: str,
    default: str | None = None,
    validator: Callable[[str], None] | None = None,
) -> str:
    while True:
        suffix = f" [{default}]" if default else ""
        value = input(f"{message}{suffix}: ").strip()
        if not value and default is not None:
            value = default

        if not value:
            print("输入不能为空。")
            continue

        try:
            if validator:
                validator(value)
        except ValueError as exc:
            print(exc)
            continue

        return value


def prompt_choice(title: str, options: list[str], default_index: int = 0) -> int:
    if not options:
        raise ValueError("options 不能为空")

    print(title)
    for idx, option in enumerate(options, start=1):
        default_mark = " [默认]" if idx - 1 == default_index else ""
        print(f"  {idx}. {option}{default_mark}")

    while True:
        raw = input("请选择序号: ").strip()
        if not raw:
            return default_index
        if raw.isdigit():
            selected = int(raw) - 1
            if 0 <= selected < len(options):
                return selected
        print(f"请输入 1-{len(options)} 之间的序号。")
