"""主菜单 TUI 路由"""

from __future__ import annotations

import sys
from pathlib import Path

from src.utils.terminal_ui import prompt_choice


def main_menu():
    """主菜单入口"""
    print()
    print("=" * 50)
    print("  PPT Slide Generator v2.0.0")
    print("=" * 50)
    print()

    while True:
        choice = prompt_choice(
            "请选择操作",
            [
                "新建项目",
                "打开已有项目",
                "退出",
            ],
            default_index=0,
        )

        if choice == 0:
            from src.tui.project_wizard import create_project_wizard
            create_project_wizard()
        elif choice == 1:
            from src.tui.project_wizard import open_project_wizard
            open_project_wizard()
        elif choice == 2:
            print("再见!")
            sys.exit(0)
