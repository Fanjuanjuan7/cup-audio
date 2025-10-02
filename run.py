#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
音频分割工具启动脚本
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from audio_splitter import main

if __name__ == "__main__":
    main()