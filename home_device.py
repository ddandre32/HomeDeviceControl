#!/usr/bin/env python3
"""
Home Device Control - 主入口
整合 miot SDK 和 Skill 功能
"""

import sys
import os

# 添加 miot 到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli import main as cli_main

if __name__ == "__main__":
    sys.exit(cli_main())
