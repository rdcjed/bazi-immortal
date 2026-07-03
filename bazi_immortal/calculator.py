"""
八字命理推算引擎 - 核心计算器
包含：排四柱（年柱/月柱/日柱/时柱）、日干支计算、月柱节气判断、时柱时辰判断
"""

import datetime
from typing import Dict, List, Tuple, Optional

from .constants import (
    TIAN_GAN, DI_ZHI, TG_INDEX, DZ_INDEX,
    TG_WU_XING, DZ_WU_XING, DZ_CANG_GAN,
    WU_HU_DUN, WU_SHU_DUN,
    LIU_SHI_JIA_ZI, LIU_SHI_JIA_ZI_NAMES,
    SHI_CHEN, DZ_MONTH_INFO, LICHUN_DATES,
    SHI_ER_CHANG_SHENG,
)


class Pillar:
    """四柱中的一柱"""
    def __init__(self, heavenly_stem: str, earthly_branch: str, label: str = ""):
        self.tian_gan = heavenly_stem     # 天干
        self.di_zhi = earthly_branch      # 地支
        self.label = label                # 年/月/日/时

    @property
    def gan_zhi(self) -> str:
        """返回干支字符串，如 丙午"""
        return self.tian_gan + self.di_zhi

    @property
    def cang_gan(self) -> List[str]:
        """地支藏干"""
        return DZ_CANG_GAN.get(self.di_zhi, [])

    def __repr__(self) -> str:
        return f"Pillar({self.gan_zhi}, {self.label})"


class BaZi:
    """八字命盘"""
    def __init__(self, year: Pillar, month: Pillar, day: Pillar, hour: Pillar, gender: str):
        self.year_pillar = year
        self.month_pillar = month
        self.day_pillar = day
        self.hour_pillar = hour
        self.gender = gender  # "男" or "女"

    @property
    def si_zhu(self) -> List[Pillar]:
        """四柱列表"""
        return [self.year_pillar, self.month_pillar, self.day_pillar, self.hour_pillar]

    @property
    def ri_gan(self) -> str:
        """日主（日干）"""
        return self.day_pillar.tian_gan

    @property
    def gan_list(self) -> List[str]:
        """四个天干"""
        return [p.tian_gan for p in self.si_zhu]

    @property
    def zhi_list(self) -> List[str]:
        """四个地支"""
        return [p.di_zhi for p in self.si_zhu]

    def __repr__(self) -> str:
        return f"八字: {' '.join(p.gan_zhi for p in self.si_zhu)} [{self.gender}]"


class BaZiCalculator:
    """
    八字计算器
    输入：公历出生日期 + 出生时间 + 性别
    输出：完整的四柱八字
    """

    def __init__(self):
        # 预先计算一些缓存数据
        self._lichun_cache = LICHUN_DATES

    # ─── 公共接口 ───

    def calculate(self, year: int, month: int, day: int, hour: int, minute: int, gender: str) -> BaZi:
        """
        主入口：由公历生日+时间计算八字

        Args:
            year: 公历年份
            month: 公历月份 (1-12)
            day: 公历日期
            hour: 小时 (0-23)
            minute: 分钟 (0-59)
            gender: 性别 "男" or "女"

        Returns:
            BaZi 对象
        """
        year_pillar = self._calc_year_pillar(year, month, day)
        month_pillar = self._calc_month_pillar(year, month, day, year_pillar.tian_gan)
        day_pillar = self._calc_day_pillar(year, month, day)
        hour_pillar = self._calc_hour_pillar(hour, minute, day_pillar.tian_gan)

        return BaZi(year_pillar, month_pillar, day_pillar, hour_pillar, gender)

    # ─── 年柱计算 ───

    def _calc_year_pillar(self, year: int, month: int, day: int) -> Pillar:
        """
        年柱：以立春为界
        立春前仍是上一年干支，立春后是本年年干支
        """
        lichun_month, lichun_day = self._get_lichun(year)

        if month < lichun_month or (month == lichun_month and day < lichun_day):
            # 未到立春，算上一年
            target_year = year - 1
        else:
            target_year = year

        gan_zhi_index = (target_year - 4) % 60
        tg, dz = LIU_SHI_JIA_ZI[gan_zhi_index]
        return Pillar(TIAN_GAN[tg], DI_ZHI[dz], "年柱")

    def _get_lichun(self, year: int) -> Tuple[int, int]:
        """获取某年立春的月、日

        优先使用天文算法精确计算（支持1900-2100年），
        失败则回退到预设缓存（2020-2030年），
        最后兜底返回 (2, 4)
        """
        try:
            from .jieqi import get_term_date
            return get_term_date(year, '立春')
        except Exception:
            pass
        return self._lichun_cache.get(year, (2, 4))

    # ─── 月柱计算 ───

    def _calc_month_pillar(self, year: int, month: int, day: int, year_gan: str) -> Pillar:
        """
        月柱：节气分界 + 五虎遁

        1. 月支：按节气确定（立春~惊蛰=寅月，惊蛰~清明=卯月...）
        2. 月干：五虎遁口诀——年干决定正月（寅月）的天干
        3. 正月天干确定后，顺数即可
        """
        # 1. 确定月支
        month_zhi = self._get_month_zhi(year, month, day)

        # 2. 五虎遁定月干
        zheng_yue_gan = WU_HU_DUN[year_gan]  # 正月（寅月）的天干
        zheng_yue_index = TG_INDEX[zheng_yue_gan]
        
        # 寅月索引=2，月支偏移 = (目标地支索引 - 寅索引) % 12
        yin_index = DZ_INDEX["寅"]
        target_zhi_index = DZ_INDEX[month_zhi]
        offset = (target_zhi_index - yin_index) % 12
        
        month_gan_index = (zheng_yue_index + offset) % 10
        month_gan = TIAN_GAN[month_gan_index]

        return Pillar(month_gan, month_zhi, "月柱")

    def _get_month_zhi(self, year: int, month: int, day: int) -> str:
        """
        根据公历日期确定月支（节气分界）
        
        使用节气计算器精确确定月份
        """
        try:
            from .jieqi import get_month_zhi
            return get_month_zhi(year, month, day)
        except ImportError:
            # fallback: 简化判断
            pass

        # 简化节气边界（精确到日，不考虑年份波动）
        boundaries = [
            (1, 6, "丑"),   # 小寒
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
                # 在这个节气之前，返回上一个地支
                # 但如果是一二月份，可能需要回退到上一年
                # 处理跨年：如果当前在1月或2月初（没到立春），应该是丑月
                prev_zhi = DI_ZHI[(DZ_INDEX[zhi] - 1) % 12]
                return prev_zhi

        # 如果过了大雪（12月7日），是子月，但还要检查小寒
        if month == 12 and day >= 7:
            # 子月范围：12月7日~1月5日
            # 丑月：1月6日~2月3日
            return "子"

        # 最后兜底：根据月份粗略对应
        month_to_zhi = {1: "丑", 2: "寅", 3: "卯", 4: "辰", 5: "巳", 6: "午",
                        7: "未", 8: "申", 9: "酉", 10: "戌", 11: "亥", 12: "子"}
        return month_to_zhi.get(month, "子")

    # ─── 日柱计算 ───

    def _calc_day_pillar(self, year: int, month: int, day: int) -> Pillar:
        """
        日柱：使用基于儒略日（Julian Day Number）的天文算法

        精确适用于所有公历年份（1582年10月15日之后的格里历），
        不受世纪限制，无1900-2099的限制。

        算法：
        1. 计算该日期的儒略日数（JDN）
        2. 日干支索引 = (JDN + 49) % 60（49为修正偏移，使甲子日正确对应）
        """
        # 儒略日计算（格里历）
        a = (14 - month) // 12
        y = year + 4800 - a
        m = month + 12 * a - 3
        jdn = day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045

        # 日干支索引 = (JDN + 49) % 60
        # 其中49是修正偏移，使得JDN(1900-01-01)=2415021的日干支为甲子(index 0)
        target_index = (jdn + 49) % 60
        tg, dz = LIU_SHI_JIA_ZI[target_index]

        return Pillar(TIAN_GAN[tg], DI_ZHI[dz], "日柱")

    def _day_of_year(self, year: int, month: int, day: int) -> int:
        """计算某日是当年的第几天"""
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if self._is_leap_year(year):
            days_in_month[1] = 29
        return sum(days_in_month[:month - 1]) + day

    def _is_leap_year(self, year: int) -> bool:
        """闰年判断"""
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

    # ─── 时柱计算 ───

    def _calc_hour_pillar(self, hour: int, minute: int, day_gan: str) -> Pillar:
        """
        时柱：时辰确定 + 五鼠遁

        1. 时辰地支：根据小时+分钟判断
        子时：23:00-0:59
        丑时：1:00-2:59
        ...
        2. 时干：五鼠遁——日干决定子时的天干
        """
        # 1. 确定时辰地支
        hour_zhi = self._get_hour_zhi(hour, minute)

        # 2. 五鼠遁定时干
        zi_shi_gan = WU_SHU_DUN[day_gan]  # 子时的天干
        zi_index = TG_INDEX[zi_shi_gan]
        hour_zhi_index = DZ_INDEX[hour_zhi]
        
        offset = hour_zhi_index  # 子=0, 丑=1, 寅=2...
        hour_gan_index = (zi_index + offset) % 10
        hour_gan = TIAN_GAN[hour_gan_index]

        return Pillar(hour_gan, hour_zhi, "时柱")

    def _get_hour_zhi(self, hour: int, minute: int) -> str:
        """根据时间确定时辰"""
        # 子时特殊处理（跨天）
        if hour == 23 or hour == 0:
            return "子"
        for sc in SHI_CHEN:
            if sc["start_hour"] <= hour <= sc["end_hour"]:
                if hour == sc["start_hour"] and minute < sc["start_min"]:
                    continue
                if hour == sc["end_hour"] and minute > sc["end_min"]:
                    continue
                return sc["name"]
        return "子"  # fallback


def calculate_bazi(year: int, month: int, day: int, hour: int = 12, minute: int = 0, gender: str = "男") -> BaZi:
    """
    便捷函数：输入公历生日，返回八字对象

    Args:
        year: 公历年份
        month: 公历月份
        day: 公历日期
        hour: 小时 (0-23)，默认12点
        minute: 分钟 (0-59)，默认0分
        gender: "男" or "女"

    Returns:
        BaZi 八字对象
    """
    calc = BaZiCalculator()
    return calc.calculate(year, month, day, hour, minute, gender)


def bazi_to_string(bazi: BaZi) -> str:
    """八字对象 → 可读字符串"""
    lines = []
    pillars = bazi.si_zhu
    labels = ["年柱", "月柱", "日柱", "时柱"]
    
    # 表头
    lines.append(f"{'':>4} {'年柱':>8} {'月柱':>8} {'日柱':>8} {'时柱':>8}")
    lines.append("-" * 40)
    
    # 天干行
    gan_str = "天干"
    for p in pillars:
        gan_str += f" {p.tian_gan:>6}"
    lines.append(gan_str)
    
    # 地支行
    zhi_str = "地支"
    for p in pillars:
        zhi_str += f" {p.di_zhi:>6}"
    lines.append(zhi_str)
    
    # 藏干行
    cg_str = "藏干"
    for p in pillars:
        cang = "".join(p.cang_gan)
        cg_str += f" {cang:>6}"
    lines.append(cg_str)
    
    lines.append("")
    lines.append(f"日主: {bazi.ri_gan}（{TG_WU_XING[bazi.ri_gan]}）")
    lines.append(f"性别: {bazi.gender}")
    
    return "\n".join(lines)
