"""
大运流年计算模块
排大运、算流年
"""

from typing import Dict, List, Tuple, Optional
from .constants import (
    TIAN_GAN, DI_ZHI, DZ_INDEX, TG_INDEX,
    LIU_SHI_JIA_ZI, LIU_SHI_JIA_ZI_NAMES,
    DZ_LIU_CHONG, DZ_LIU_HE, DZ_LIU_HAI, DZ_SAN_XING,
    TG_YIN_YANG, DZ_YIN_YANG, TG_WU_XING, DZ_WU_XING, WU_XING_KE,
)
from .calculator import BaZi
from .shisheng import get_shi_shen_for_gan

# 节气对应的月地支
JIE_QI_MONTH_MAP = {
    (2, 4): "寅",  # 立春
    (3, 6): "卯",  # 惊蛰
    (4, 5): "辰",  # 清明
    (5, 6): "巳",  # 立夏
    (6, 6): "午",  # 芒种
    (7, 7): "未",  # 小暑
    (8, 7): "申",  # 立秋
    (9, 8): "酉",  # 白露
    (10, 8): "戌",  # 寒露
    (11, 7): "亥",  # 立冬
    (12, 7): "子",  # 大雪
}


def calculate_da_yun(bazi: BaZi) -> Dict:
    """
    排大运

    规则：
    1. 阳年男 / 阴年女 → 顺排
    2. 阴年男 / 阳年女 → 逆排
    3. 起运年龄 = 距离最近节气天数 ÷ 3
    4. 每10年一步大运

    Returns:
    {
        "direction": "顺排"/"逆排",
        "start_age": 起运年龄(float),
        "da_yun_list": [(年龄范围, 干支, 十神), ...],
        "reasoning": [推理过程]
    }
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

    # 2. 起运年龄计算
    
    # 计算从出生日到最近节气的天数
    try:
        from .jieqi import get_term_date
        
        # 确定要查的节气
        # 顺排 → 查下一个节气（月柱的下一个分界）
        # 逆排 → 查上一个节气
        month_zhi_index = DZ_INDEX[month_zhi]
        term_names = ["立春", "惊蛰", "清明", "立夏", "芒种", "小暑",
                      "立秋", "白露", "寒露", "立冬", "大雪", "小寒"]
        
        # 月支对应的节气（月支0=子→大雪？不对，需要映射）
        # 寅=立春, 卯=惊蛰... 子=大雪, 丑=小寒
        zhi_to_term = {
            "寅": "立春", "卯": "惊蛰", "辰": "清明",
            "巳": "立夏", "午": "芒种", "未": "小暑",
            "申": "立秋", "酉": "白露", "戌": "寒露",
            "亥": "立冬", "子": "大雪", "丑": "小寒",
        }
        
        # 这里简化处理：默认3岁起运
        # 完整计算需要根据实际节气日期差异÷3
        start_age = 3.0
        start_age_reason = "默认3岁起运（需精确节气日期计算）"
    except ImportError:
        start_age = 3.0
        start_age_reason = "默认3岁起运"

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

        # 大运十神（看大运天干对日主的关系）
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
        "start_age": start_age,
        "da_yun_list": da_yun_list,
        "reasoning": [
            f"年干{year_gan}为{'阳' if year_yang else '阴'}年，命主为{gender}性，故大运{direction}",
            f"默认{start_age}岁起运，每十年一步大运",
        ],
    }


def get_liu_nian(year: int) -> Dict:
    """
    获取某年的流年信息

    Returns:
    {
        "year": 年份,
        "gan_zhi": 流年干支,
        "tian_gan": 流年天干,
        "di_zhi": 流年地支,
        "na_yin": 纳音,
    }
    """
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
    """
    流年对八字的影响分析

    分析维度：
    1. 值太岁 / 冲太岁 / 刑太岁 / 害太岁
    2. 流年天干十神 → 当年哪方面运旺
    3. 流年地支与各柱的合冲刑害
    4. 流年与大运的关系
    """
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
        
        # 合
        if DZ_LIU_HE.get(ln_zhi) == zhi or DZ_LIU_HE.get(zhi) == ln_zhi:
            relations.append("合")
        # 冲
        if DZ_LIU_CHONG.get(ln_zhi) == zhi:
            relations.append("冲")
        # 害
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
    parts.append(f"大运{da_yun_result['direction']}")
    parts.append(f"起运年龄：{da_yun_result['start_age']}岁")

    parts.append("")
    parts.append(f"{'年龄':>8} {'大运':>6} {'十神':>6}")
    parts.append("-" * 30)

    current_da_yun = None
    for dy in da_yun_result["da_yun_list"]:
        marker = ""
        if dy["start_age"] <= current_age < dy["end_age"]:
            marker = " ← 当前"
            current_da_yun = dy
        parts.append(f"{dy['range']:>8} {dy['gan_zhi']:>6} {dy['shi_shen']:>6}{marker}")

    if current_da_yun:
        parts.append("")
        parts.append(f"当前正在走：{current_da_yun['range']} {current_da_yun['gan_zhi']}运，"
                     f"天干{current_da_yun['tian_gan']}为{current_da_yun['shi_shen']}运")

    return "\n".join(parts)