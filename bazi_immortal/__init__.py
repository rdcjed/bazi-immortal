"""
八字命理推算引擎 - 命运道士 AI
基于子平八字命理体系，输入生辰推运势
"""

__version__ = "1.0.0"
__author__ = "云中子"

from .calculator import BaZi, BaZiCalculator, calculate_bazi, bazi_to_string
from .wuxing import (
    analyze_wuxing_distribution, analyze_ri_zuo_strong_weak, analyze_ge_ju,
    get_season, format_wuxing_analysis
)
from .shisheng import (
    analyze_all_shi_shen, get_shi_shen_for_gan,
    get_shi_shen_interpretation, format_shi_shen_analysis
)
from .dayun import (
    calculate_da_yun, get_liu_nian, analyze_liu_nian, format_da_yun
)
from .shensha import (
    find_shen_sha, format_shen_sha
)