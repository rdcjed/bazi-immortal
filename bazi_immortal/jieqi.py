"""
节气精确计算 - 天文算法
基于太阳黄经计算24节气精确时刻
支持1900-2100年，精度：分钟级

数据来源：Jean Meeus《天文算法》(Astronomical Algorithms)
公式有效范围：-1000年至+3000年

太阳黄经公式：
  L = L0 + C
  L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T^2
  C = (1.914602 - 0.004817 * T - 0.000014 * T^2) * sin(M)
      + (0.019993 - 0.000101 * T) * sin(2*M)
      + 0.000289 * sin(3*M)
  M = 357.52911 + 35999.05029 * T - 0.0001537 * T^2
  T = (JD - 2451545.0) / 36525  (儒略世纪)
"""

import math
from typing import Dict, Tuple, List

# 24节气对应的太阳黄经（度）
JIE_QI_LONGITUDE = {
    "小寒": 285, "大寒": 300, "立春": 315, "雨水": 330,
    "惊蛰": 345, "春分": 0, "清明": 15, "谷雨": 30,
    "立夏": 45, "小满": 60, "芒种": 75, "夏至": 90,
    "小暑": 105, "大暑": 120, "立秋": 135, "处暑": 150,
    "白露": 165, "秋分": 180, "寒露": 195, "霜降": 210,
    "立冬": 225, "小雪": 240, "大雪": 255, "冬至": 270,
}

# 用于月柱分界的关键节气（12个）
KEY_TERMS = list(JIE_QI_LONGITUDE.keys())

# 月柱分界 → 月支
TERM_TO_ZHI = [
    ("立春", "寅"), ("惊蛰", "卯"), ("清明", "辰"),
    ("立夏", "巳"), ("芒种", "午"), ("小暑", "未"),
    ("立秋", "申"), ("白露", "酉"), ("寒露", "戌"),
    ("立冬", "亥"), ("大雪", "子"), ("小寒", "丑"),
]


def _julian_day(year: int, month: int, day: int) -> float:
    """计算儒略日数"""
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045


def _solar_longitude(jd: float) -> float:
    """
    计算太阳黄经（度）
    使用 Jean Meeus《天文算法》公式，有效范围 -1000 至 +3000 年
    """
    # 儒略世纪
    T = (jd - 2451545.0) / 36525.0

    # 太阳平黄经
    L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T

    # 太阳平近点角
    M = 357.52911 + 35999.05029 * T - 0.0001537 * T * T
    M_rad = math.radians(M % 360)

    # 中心方程（方程中心）
    C = ((1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(M_rad)
         + (0.019993 - 0.000101 * T) * math.sin(2 * M_rad)
         + 0.000289 * math.sin(3 * M_rad))

    # 太阳真黄经（不包裹，单调递增）
    return L0 + C


def _solar_longitude_wrapped(jd: float) -> float:
    """计算太阳黄经并包裹到 [0, 360) 范围"""
    return _solar_longitude(jd) % 360


def _julian_to_date(jd: float) -> Tuple[int, int, int, int, int]:
    """将儒略日转换为年月日时分"""
    a = int(jd) + 32044
    b = (4 * a + 3) // 146097
    c = a - 146097 * b // 4
    d = (4 * c + 3) // 1461
    e = c - 1461 * d // 4
    m = (5 * e + 2) // 153

    day = e - (153 * m + 2) // 5 + 1
    month = m + 3 - 12 * (m // 10)
    year = 100 * b + d - 4800 + m // 10

    # 计算时分
    fraction = jd - int(jd)
    hour = int(fraction * 24)
    minute = int((fraction * 24 - hour) * 60)

    return (year, month, day, hour, minute)


def _find_term_time(year: int, longitude: float) -> Tuple[int, int, int, int]:
    """
    找到某年某黄经对应的精确时刻
    使用全年二分法搜索（不包裹的太阳黄经）
    返回 (月, 日, 时, 分)
    """
    jd_low = _julian_day(year, 1, 1)
    jd_high = _julian_day(year, 12, 31)

    # 使用不包裹的太阳黄经进行计算
    # 目标黄经 = longitude + k*360，确保 target 在 [lon_low, lon_high] 之间
    lon_low = _solar_longitude(jd_low)
    lon_high = _solar_longitude(jd_high)
    k = int((lon_low - longitude) / 360) + 1
    target = longitude + 360 * k
    # 如果 target 超过了年末，向回退一个周期
    if target > lon_high:
        target -= 360

    for _ in range(100):  # 100次迭代足够精确到分钟
        jd_mid = (jd_low + jd_high) / 2
        lon_mid = _solar_longitude(jd_mid)

        if lon_mid < target:
            jd_low = jd_mid
        else:
            jd_high = jd_mid

        if abs(jd_high - jd_low) < 1 / 1440:  # 1分钟精度
            break

    jd_result = (jd_low + jd_high) / 2

    # 转换为年月日时分
    y, m, d, h, mi = _julian_to_date(jd_result)

    return (m, d, h, mi)


def get_term_date(year: int, term_name: str) -> Tuple[int, int]:
    """
    获取某年某节气的公历日期
    使用天文算法精确计算

    Returns: (月, 日)
    """
    longitude = JIE_QI_LONGITUDE.get(term_name)
    if longitude is None:
        raise ValueError(f"未知节气: {term_name}")

    month, day, hour, minute = _find_term_time(year, longitude)
    return (month, day)


def get_term_datetime(year: int, term_name: str) -> Tuple[int, int, int, int]:
    """
    获取某年某节气的精确时刻
    使用天文算法精确计算

    Returns: (月, 日, 时, 分)
    """
    longitude = JIE_QI_LONGITUDE.get(term_name)
    if longitude is None:
        raise ValueError(f"未知节气: {term_name}")

    return _find_term_time(year, longitude)


def get_month_zhi(year: int, month: int, day: int) -> str:
    """
    根据节气确定月支
    使用天文算法精确计算

    遍历每个节气分界点，找到该日期落在哪个节气区间
    """
    # 处理跨年：1月属于上一年的丑月（小寒后）或子月（小寒前）
    prev_year = year - 1

    # 获取当前年和上一年的关键节气时刻
    terms_current = {}
    terms_prev = {}

    for term_name, zhi in TERM_TO_ZHI:
        try:
            terms_current[term_name] = get_term_datetime(year, term_name)
        except:
            pass
        try:
            terms_prev[term_name] = get_term_datetime(prev_year, term_name)
        except:
            pass

    # 将日期转换为儒略日便于比较
    jd_input = _julian_day(year, month, day)

    # 遍历节气分界点，找到该日期落在哪个区间
    for i, (term_name, zhi) in enumerate(TERM_TO_ZHI):
        if term_name in terms_current:
            t_month, t_day, t_hour, t_minute = terms_current[term_name]
            jd_term = _julian_day(year, t_month, t_day) + t_hour / 24 + t_minute / 1440

            # 获取下一个节气
            next_term_name = TERM_TO_ZHI[(i + 1) % 12][0]
            if next_term_name in terms_current:
                nt_month, nt_day, nt_hour, nt_minute = terms_current[next_term_name]
                jd_next = _julian_day(year, nt_month, nt_day) + nt_hour / 24 + nt_minute / 1440
            elif next_term_name in terms_prev:
                # 跨年情况
                nt_month, nt_day, nt_hour, nt_minute = terms_prev[next_term_name]
                jd_next = _julian_day(prev_year, nt_month, nt_day) + nt_hour / 24 + nt_minute / 1440
            else:
                continue

            # 检查日期是否在该节气区间内
            if jd_term <= jd_input < jd_next:
                return zhi

    # 兜底：使用简化判断
    return _get_month_zhi_fallback(year, month, day)


def _get_month_zhi_fallback(year: int, month: int, day: int) -> str:
    """
    简化节气边界（精确到日，不考虑年份波动）
    作为天文算法的兜底方案
    """
    # 1月特殊处理：小寒(1/6)前为子月，后为丑月
    if month == 1:
        return "子" if day < 6 else "丑"

    boundaries = [
        (2, 4, "寅"),   # 立春
        (3, 6, "卯"),   # 惊蛰
        (4, 5, "辰"),   # 清明
        (5, 6, "巳"),   # 立夏
        (6, 6, "午"),   # 芒种
        (7, 7, "未"),   # 小暑
        (8, 7, "申"),   # 立秋
        (9, 8, "酉"),   # 白露
        (10, 8, "戌"),  # 寒露
        (11, 7, "亥"),  # 立冬
        (12, 7, "子"),  # 大雪
    ]

    for b_month, b_day, zhi in boundaries:
        if month < b_month or (month == b_month and day < b_day):
            prev_zhi = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
            zhi_index = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"].index(zhi)
            return prev_zhi[(zhi_index - 1) % 12]

    # 如果过了大雪（12月7日），是子月
    if month == 12 and day >= 7:
        return "子"

    # 最后兜底：根据月份粗略对应
    month_to_zhi = {1: "丑", 2: "寅", 3: "卯", 4: "辰", 5: "巳", 6: "午",
                    7: "未", 8: "申", 9: "酉", 10: "戌", 11: "亥", 12: "子"}
    return month_to_zhi.get(month, "子")


def get_all_terms(year: int) -> Dict[str, Tuple[int, int]]:
    """获取某年所有24节气的日期"""
    result = {}
    for name in JIE_QI_LONGITUDE.keys():
        try:
            result[name] = get_term_date(year, name)
        except:
            # 如果天文算法失败，使用简化估算
            base_month = (list(JIE_QI_LONGITUDE.keys()).index(name) // 2) + 1
            base_day = 20 + (list(JIE_QI_LONGITUDE.keys()).index(name) % 2) * 5
            if base_day > 31:
                base_month += 1
                base_day -= 31
            if base_month > 12:
                base_month = 1
            result[name] = (base_month, base_day)
    return result


if __name__ == "__main__":
    # 测试：计算2024年所有节气
    print("2024年24节气精确时刻：")
    for name in JIE_QI_LONGITUDE.keys():
        try:
            m, d, h, mi = get_term_datetime(2024, name)
            print(f"{name}: {m}月{d}日 {h:02d}:{mi:02d}")
        except Exception as e:
            print(f"{name}: 计算失败 - {e}")