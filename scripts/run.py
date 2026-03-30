#!/usr/bin/env python3
"""PPT Slide Generator v2.0 - 主入口"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tui.main_menu import main_menu


def main():
    main_menu()


if __name__ == "__main__":
    main()
