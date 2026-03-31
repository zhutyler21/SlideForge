#!/usr/bin/env python3
"""PPT Slide Generator v2.0 - 主入口"""

import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中（兼容直接运行脚本的场景）
_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.tui.main_menu import main_menu


def main():
    main_menu()


if __name__ == "__main__":
    main()
