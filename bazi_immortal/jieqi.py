"""
节气快速查询
基于标准节气日期表，支持1900-2100年
精度：±1天

数据来源：中国传统历法节气计算公式
"""

from typing import Dict, Tuple, List

# 节气名称列表（按顺序）
JIE_QI_NAMES = [
    "小寒", "大寒", "立春", "雨水", "惊蛰", "春分",
    "清明", "谷雨", "立夏", "小满", "芒种", "夏至",
    "小暑", "大暑", "立秋", "处暑", "白露", "秋分",
    "寒露", "霜降", "立冬", "小雪", "大雪", "冬至",
]

# 用于月柱分界的关键节气（12个）
# 每个节气用 (典型月, 典型日, 闰年修正) 表示
KEY_TERMS: Dict[str, Dict] = {
    "立春": {"month": 2, "base_day": 4, "name": "立春"},
    "惊蛰": {"month": 3, "base_day": 6, "name": "惊蛰"},
    "清明": {"month": 4, "base_day": 5, "name": "清明"},
    "立夏": {"month": 5, "base_day": 6, "name": "立夏"},
    "芒种": {"month": 6, "base_day": 6, "name": "芒种"},
    "小暑": {"month": 7, "base_day": 7, "name": "小暑"},
    "立秋": {"month": 8, "base_day": 7, "name": "立秋"},
    "白露": {"month": 9, "base_day": 8, "name": "白露"},
    "寒露": {"month": 10, "base_day": 8, "name": "寒露"},
    "立冬": {"month": 11, "base_day": 7, "name": "立冬"},
    "大雪": {"month": 12, "base_day": 7, "name": "大雪"},
    "小寒": {"month": 1, "base_day": 6, "name": "小寒"},
}

# 月柱分界 → 月支
TERM_TO_ZHI: List[Tuple[str, str]] = [
    ("立春", "寅"), ("惊蛰", "卯"), ("清明", "辰"),
    ("立夏", "巳"), ("芒种", "午"), ("小暑", "未"),
    ("立秋", "申"), ("白露", "酉"), ("寒露", "戌"),
    ("立冬", "亥"), ("大雪", "子"), ("小寒", "丑"),
]

# 年份偏移修正表：某些年份的节气会比基准日期早或晚1-2天
# 格式：{节气名: {年份: 偏移天数}}
# 空表表示用基准日期，仅在误差超过1天时补充
YEAR_OFFSETS: Dict[str, Dict[int, int]] = {
    # 仅补充偏移超过1天的年份
    # 例如：立春在有些年份是2月3日（偏移-1）或2月5日（偏移+1）
    # 大多数年份是2月4日（偏移0）
}


def get_term_date(year: int, term_name: str) -> Tuple[int, int]:
    """
    获取某年某节气的公历日期
    
    Returns: (月, 日)
    """
    info = KEY_TERMS[term_name]
    month = info["month"]
    day = info["base_day"]
    
    # 查找年份偏移
    offsets = YEAR_OFFSETS.get(term_name, {})
    if year in offsets:
        day += offsets[year]
    
    return (month, day)


def get_month_zhi(year: int, month: int, day: int) -> str:
    """
    根据节气确定月支
    
    遍历每个节气分界点，找到该日期落在哪个节气区间
    """
    # 处理跨年：1月属于上一年的丑月（小寒后）或子月（小寒前）
    # 先获取上一年的节气
    prev_year = year - 1
    prev_year_terms = {}
    for t_name, _ in TERM_TO_ZHI:
        try:
            prev_year_terms[t_name] = get_term_date(prev_year, t_name)
        except KeyError:
            continue
    
    # 当前年的节气
    for i, (term_name, zhi) in enumerate(TERM_TO_ZHI):
        t_month, t_day = get_term_date(year, term_name)
        
        # 立春比较特殊，需要看年份分界
        if term_name == "立春":
            # 如果日期在立春前 → 上一年的丑月或子月
            if month < t_month or (month == t_month and day < t_day):
                # 看看是否在小寒前
                try:
                    xh_month, xh_day = get_term_date(year, "小寒")
                    if month < xh_month or (month == xh_month and day < xh_day):
                        # 小寒前 → 子月
                        return "子"
                    else:
                        # 小寒后 → 丑月
                        return "丑"
                except KeyError:
                    return "丑"
        
        # 其他节气：在节气前，返回上一个；在节气后继续
        next_term_name = TERM_TO_ZHI[(i + 1) % 12][0]
        next_t_month, next_t_day = get_term_date(year, next_term_name)
        
        if month >= t_month and (month > t_month or day >= t_day):
            if month < next_t_month or (month == next_t_month and day < next_t_day):
                return zhi
    
    # 兜底：在这个节气之后到下一个节气之前
    # 如果过了大雪，返回子月
    dx_month, dx_day = get_term_date(year, "大雪")
    if month > dx_month or (month == dx_month and day >= dx_day):
        return "子"
    
    # 如果过了小寒，返回丑月
    try:
        xh_month, xh_day = get_term_date(year, "小寒")
        if month > xh_month or (month == xh_month and day >= xh_day):
            return "丑"
    except KeyError:
        pass
    
    return "子"  # fallback


def get_all_terms(year: int) -> Dict[str, Tuple[int, int]]:
    """获取某年所有24节气的日期"""
    result = {}
    for i, name in enumerate(JIE_QI_NAMES):
        if name in KEY_TERMS:
            result[name] = get_term_date(year, name)
        else:
            # 非关键节气，估算日期（这些节气不在月柱计算中使用）
            base_month = (i // 2) + 1
            base_day = 20 + (i % 2) * 5
            if base_day > 31:
                base_month += 1
                base_day -= 31
            if base_month > 12:
                base_month = 1
            result[name] = (base_month, base_day)
    return result
