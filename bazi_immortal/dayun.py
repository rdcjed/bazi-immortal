"""
大运流年计算模块 — 增强版
包含：准确起运年龄计算、大运排盘、流年分析
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from .constants import (
    TIAN_GAN, DI_ZHI, DZ_INDEX, TG_INDEX,
    LIU_SHI_JIA_ZI, LIU_SHI_JIA_ZI_NAMES,
    DZ_LIU_CHONG, DZ_LIU_HE, DZ_LIU_HAI, DZ_SAN_XING,
    TG_YIN_YANG, DZ_YIN_YANG, TG_WU_XING, DZ_WU_XING, WU_XING_KE,
)
from .calculator import BaZi
from .shisheng import get_shi_shen_for_gan


# 节气 → 月支映射（按月柱分界顺序）
TERM_TO_ZHI = [
    ("立春", "寅"), ("惊蛰", "卯"), ("清明", "辰"),
    ("立夏", "巳"), ("芒种", "午"), ("小暑", "未"),
    ("立秋", "申"), ("白露", "酉"), ("寒露", "戌"),
    ("立冬", "亥"), ("大雪", "子"), ("小寒", "丑"),
]

# 关键节气基准日期（月、日）
# 部分年份有±1天偏移，在YEAR_TERM_OFFSETS中修正
TERM_BASE_DATES = {
    "立春": (2, 4),   "惊蛰": (3, 6),   "清明": (4, 5),
    "立夏": (5, 6),   "芒种": (6, 6),   "小暑": (7, 7),
    "立秋": (8, 7),   "白露": (9, 8),   "寒露": (10, 8),
    "立冬": (11, 7),  "大雪": (12, 7),  "小寒": (1, 6),
}

# 年份偏移修正（仅补需要±1天以上的年份）
YEAR_TERM_OFFSETS = {
    "立春": {
        1900: 0, 1901: 0, 1902: 0, 1903: 0,
        1904: -1, 1905: 0, 1906: 0, 1907: 0,
        # 少量年份立春在2月3日或5日
    },
    "小寒": {
        # 小寒通常在1月5-6日
    },
}


def _get_term_date(year: int, term_name: str) -> Tuple[int, int]:
    """获取某年某节气的公历日期 (月, 日)"""
    if term_name not in TERM_BASE_DATES:
        raise KeyError(f"未知节气: {term_name}")
    
    month, base_day = TERM_BASE_DATES[term_name]
    day = base_day
    
    # 年份偏移修正
    offsets = YEAR_TERM_OFFSETS.get(term_name, {})
    if year in offsets:
        day += offsets[year]
    
    return (month, day)


def _get_next_term_date(year: int, month: int, day: int, term_list: List[Tuple[str, str]]) -> Tuple[int, int, int, str]:
    """找当前日期之后/之前的下一个节气，返回 (年, 月, 日, 节气名)"""
    birth_dt = datetime(year, month, day)
    
    # 生成所有12个节气的日期
    all_terms = []
    for t_name, _ in term_list:
        # 节气可能在今年，也可能在明年
        for y in [year - 1, year, year + 1]:
            try:
                t_month, t_day = _get_term_date(y, t_name)
                t_dt = datetime(y, t_month, t_day)
                all_terms.append((t_dt, t_name, y))
            except (KeyError, ValueError):
                continue
    
    # 按时间排序
    all_terms.sort(key=lambda x: x[0])
    
    # 找到出生后的第一个节气
    for t_dt, t_name, y in all_terms:
        if t_dt > birth_dt:
            return (y, t_dt.month, t_dt.day, t_name)
    
    return (year, month, day, "立春")  # fallback


def _get_prev_term_date(year: int, month: int, day: int, term_list: List[Tuple[str, str]]) -> Tuple[int, int, int, str]:
    """找当前日期之前的最后一个节气"""
    birth_dt = datetime(year, month, day)
    
    all_terms = []
    for t_name, _ in term_list:
        for y in [year - 1, year, year + 1]:
            try:
                t_month, t_day = _get_term_date(y, t_name)
                t_dt = datetime(y, t_month, t_day)
                all_terms.append((t_dt, t_name, y))
            except (KeyError, ValueError):
                continue
    
    all_terms.sort(key=lambda x: x[0])
    
    # 倒序找出生前的最后一个节气
    for t_dt, t_name, y in reversed(all_terms):
        if t_dt < birth_dt:
            return (y, t_dt.month, t_dt.day, t_name)
    
    return (year, month, day, "小寒")  # fallback


def _calculate_start_age(
    birth_year: int, birth_month: int, birth_day: int,
    birth_hour: int, birth_minute: int,
    direction: str
) -> Tuple[float, List[str]]:
    """
    计算起运年龄
    
    规则：
    - 顺排：从生日到下一个节气
    - 逆排：从上一个节气到生日
    - 3天=1岁，1天=4个月，1个时辰(2小时)=10天
    
    Returns: (start_age_years, [reasoning])
    """
    reasoning = []
    
    # 出生日期时间
    birth_dt = datetime(birth_year, birth_month, birth_day, birth_hour, birth_minute)
    
    if direction == "顺排":
        t_year, t_month, t_day, t_name = _get_next_term_date(
            birth_year, birth_month, birth_day, TERM_TO_ZHI)
        term_dt = datetime(t_year, t_month, t_day, 0, 0, 0)
        delta = term_dt - birth_dt
        direction_desc = f"从{birth_year}年{birth_month}月{birth_day}日到下一个节气「{t_name}」({t_year}年{t_month}月{t_day}日)"
    else:  # 逆排
        t_year, t_month, t_day, t_name = _get_prev_term_date(
            birth_year, birth_month, birth_day, TERM_TO_ZHI)
        term_dt = datetime(t_year, t_month, t_day, 0, 0, 0)  # 节气开始时刻
        delta = birth_dt - term_dt
        direction_desc = f"从上一个节气「{t_name}」({t_year}年{t_month}月{t_day}日)到{birth_year}年{birth_month}月{birth_day}日"
    
    reasoning.append(direction_desc)
    
    # 计算精确天数差
    total_seconds = abs(delta.total_seconds())
    total_days = total_seconds / 86400.0  # 秒转天
    reasoning.append(f"间隔{total_days:.4f}天")
    
    # 换算：3天=1岁
    years_part = total_days / 3.0
    reasoning.append(f"/ 3 = {years_part:.4f}岁")
    
    reasoning.append(f"即{years_part:.1f}岁起运")
    
    return years_part, reasoning


def calculate_da_yun(bazi: BaZi, birth_time: Optional[Tuple[int, int, int, int, int]] = None) -> Dict:
    """
    排大运（增强版）
    
    与旧版兼容：如果不传birth_time，使用默认3岁起运
    
    Args:
        bazi: 八字对象
        birth_time: (年, 月, 日, 时, 分) 用于精确计算起运
    
    Returns:
        大运结果字典
    """
    year_gan = bazi.year_pillar.tian_gan
    month_gan = bazi.month_pillar.tian_gan
    month_zhi = bazi.month_pillar.di_zhi
    gender = bazi.gender
    
    # 1. 判断顺逆
    year_yang = TG_YIN_YANG[year_gan] == "阳"
    is_male = (gender == "男")
    
    if (year_yang and is_male) or (not year_yang and not is_male):
        direction = "顺排"
    else:
        direction = "逆排"
    
    reasoning = [f"年干{year_gan}为{'阳' if year_yang else '阴'}年，命主为{gender}性，故大运{direction}"]
    
    # 2. 起运年龄计算
    if birth_time:
        b_year, b_month, b_day, b_hour, b_minute = birth_time
        start_age, age_reasoning = _calculate_start_age(
            b_year, b_month, b_day, b_hour, b_minute, direction)
        reasoning.extend(age_reasoning)
    else:
        start_age = 3.0
        reasoning.append("（无出生时间参数，默认3岁起运）")
    
    # 3. 排大运干支
    month_zhi_index = DZ_INDEX[month_zhi]
    month_gan_index = TG_INDEX[month_gan]
    
    da_yun_list = []
    for step in range(8):  # 排8步大运，够80年
        if direction == "顺排":
            zhi_i = (month_zhi_index + step + 1) % 12
            gan_i = (month_gan_index + step + 1) % 10
        else:
            zhi_i = (month_zhi_index - step - 1) % 12
            gan_i = (month_gan_index - step - 1) % 10
        
        gan = TIAN_GAN[gan_i]
        zhi = DI_ZHI[zhi_i]
        gan_zhi = gan + zhi
        
        start = round(start_age + step * 10, 1)
        end = round(start_age + (step + 1) * 10, 1)
        
        # 大运十神（大运天干对日主的关系）
        yun_shi_shen = get_shi_shen_for_gan(bazi.ri_gan, gan)
        
        da_yun_list.append({
            "range": f"{start}-{end}岁",
            "start_age": start,
            "end_age": end,
            "gan_zhi": gan_zhi,
            "tian_gan": gan,
            "di_zhi": zhi,
            "shi_shen": yun_shi_shen,
        })
    
    return {
        "direction": direction,
        "start_age": round(start_age, 2),
        "da_yun_list": da_yun_list,
        "reasoning": reasoning,
    }


def get_liu_nian(year: int) -> Dict:
    """获取某年的流年信息"""
    gan_zhi_index = (year - 4) % 60
    tg, dz = LIU_SHI_JIA_ZI[gan_zhi_index]
    gan = TIAN_GAN[tg]
    zhi = DI_ZHI[dz]
    
    return {
        "year": year,
        "gan_zhi": gan + zhi,
        "tian_gan": gan,
        "di_zhi": zhi,
    }


def analyze_liu_nian(bazi: BaZi, liu_nian_year: int) -> Dict:
    """流年对八字的影响分析"""
    liu_nian = get_liu_nian(liu_nian_year)
    ln_gan = liu_nian["tian_gan"]
    ln_zhi = liu_nian["di_zhi"]
    ri_gan = bazi.ri_gan
    
    # 1. 太岁关系
    tai_sui_relations = []
    year_zhi = bazi.year_pillar.di_zhi
    
    if ln_zhi == year_zhi:
        tai_sui_relations.append("值太岁（本命年）")
    if ln_zhi == DZ_LIU_CHONG.get(year_zhi):
        tai_sui_relations.append("冲太岁")
    if year_zhi in DZ_SAN_XING and DZ_SAN_XING[year_zhi] == ln_zhi:
        tai_sui_relations.append("刑太岁")
    if DZ_LIU_HAI.get(ln_zhi) == year_zhi:
        tai_sui_relations.append("害太岁")
    
    if not tai_sui_relations:
        tai_sui_relations.append("无冲刑害")
    
    # 2. 流年天干十神
    ln_shi_shen = get_shi_shen_for_gan(ri_gan, ln_gan)
    
    # 3. 流年地支与四柱的合冲刑害
    pillar_relations = []
    for p in bazi.si_zhu:
        relations = []
        zhi = p.di_zhi
        
        if DZ_LIU_HE.get(ln_zhi) == zhi or DZ_LIU_HE.get(zhi) == ln_zhi:
            relations.append("合")
        if DZ_LIU_CHONG.get(ln_zhi) == zhi:
            relations.append("冲")
        if DZ_LIU_HAI.get(ln_zhi) == zhi:
            relations.append("害")
        
        if relations:
            pillar_relations.append({
                "pillar": p.label,
                "zhi": zhi,
                "relations": relations,
            })
    
    return {
        "liu_nian": liu_nian,
        "tai_sui_relations": tai_sui_relations,
        "liu_nian_shi_shen": ln_shi_shen,
        "pillar_relations": pillar_relations,
    }


def format_da_yun(da_yun_result: Dict, current_age: float = 30) -> str:
    """大运结果 → 可读文本"""
    parts = []
    parts.append("【大运走势】")
    parts.append(f"大运{direction_str(da_yun_result['direction'])}")
    parts.append(f"起运年龄：{da_yun_result['start_age']}岁")
    
    # 推理过程
    for r in da_yun_result["reasoning"]:
        parts.append(f"  · {r}")
    
    parts.append("")
    parts.append(f"{'年龄':>10} {'大运':>6} {'十神':>6}")
    parts.append("-" * 30)
    
    current_da_yun = None
    for dy in da_yun_result["da_yun_list"]:
        marker = ""
        if dy["start_age"] <= current_age < dy["end_age"]:
            marker = " ← 当前"
            current_da_yun = dy
        parts.append(f"{dy['range']:>10} {dy['gan_zhi']:>6} {dy['shi_shen']:>6}{marker}")
    
    if current_da_yun:
        parts.append("")
        parts.append(f"当前大运：{current_da_yun['range']} {current_da_yun['gan_zhi']}运（{current_da_yun['shi_shen']}运）")
        
        # 大运十神解读
        ss_meaning = {
            "正官": "事业/管理运强，适合职场晋升",
            "七杀": "压力与机遇并存，需敢于拼搏",
            "正印": "学业/贵人运旺，适合进修提升",
            "偏印": "独创/偏门发展，不走寻常路",
            "正财": "财运佳，正职收入增长",
            "偏财": "偏财运好，投资/副业有收获",
            "比肩": "朋友/同事助力，团队合作运旺",
            "劫财": "竞争激烈，注意财务纠纷",
            "食神": "才华展现，创意/表达运强",
            "伤官": "锋芒毕露，利于创新但防口舌",
        }
        parts.append(f"  {ss_meaning.get(current_da_yun['shi_shen'], '')}")
    
    return "\n".join(parts)


def direction_str(d: str) -> str:
    return "顺排（阳男阴女顺行）" if d == "顺排" else "逆排（阴男阳女逆行）"