"""pytest 配置：确保 tests 目录可被正确导入"""
import sys, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, "tests"))