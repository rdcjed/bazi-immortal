"""
运势预测模块 — 月度流月 + 10年大运展望（增强版 v3.0）
改进：多维评分系统 + 五行推理 + 藏干辅助 + 节气背景
"""

from typing import Dict, List, Optional, Tuple

from .constants import (
    TIAN_GAN, DI_ZHI, TG_INDEX, DZ_INDEX,
    TG_WU_XING, DZ_WU_XING, DZ_CANG_GAN,
    WU_HU_DUN, WU_SHU_DUN, WU_XING_SHENG, WU_XING_KE,
    DZ_LIU_HE, DZ_LIU_CHONG, DZ_SAN_XING, DZ_LIU_HAI, DZ_LIU_PO,
)
from .shisheng import get_shi_shen_for_gan
from .wuxing import analyze_ri_zuo_strong_weak
from .knowledge_loader import get_shi_shen_description

# ─── 月干表（五虎遁） ───
MONTH_GAN_START = WU_HU_DUN

# 月地支对应（农历月份编号 → 地支）
MONTH_ZHI_MAP = {
    1: "寅", 2: "卯", 3: "辰", 4: "巳", 5: "午", 6: "未",
    7: "申", 8: "酉", 9: "戌", 10: "亥", 11: "子", 12: "丑",
}

MONTH_NAMES = {
    1: "正月", 2: "二月", 3: "三月", 4: "四月", 5: "五月", 6: "六月",
    7: "七月", 8: "八月", 9: "九月", 10: "十月", 11: "冬月", 12: "腊月",
}

MONTH_DATE_RANGE = {
    1: "2/4-3/5", 2: "3/6-4/4", 3: "4/5-5/5", 4: "5/6-6/5",
    5: "6/6-7/6", 6: "7/7-8/7", 7: "8/8-9/7", 8: "9/8-10/7",
    9: "10/8-11/6", 10: "11/7-12/6", 11: "12/7-1/5", 12: "1/6-2/3",
}

# 季节性因素：每个地支当令的五行强度
SEASON_STRENGTH = {
    "寅": {"木": 2}, "卯": {"木": 3}, "辰": {"土": 2, "木": 1, "水": 1},
    "巳": {"火": 2}, "午": {"火": 3}, "未": {"土": 2, "火": 1},
    "申": {"金": 2}, "酉": {"金": 3}, "戌": {"土": 2, "金": 1},
    "亥": {"水": 2}, "子": {"水": 3}, "丑": {"土": 2, "水": 1},
}

# 十神强度系数（正偏差异+特性调整）
SS_INTENSITY = {
    "正官": 1.0, "七杀": 1.3,  # 七杀更猛烈
    "正印": 1.0, "偏印": 0.8,  # 偏印不定
    "正财": 1.0, "偏财": 0.9,
    "比肩": 1.0, "劫财": 1.2,  # 劫财更烈
    "食神": 1.0, "伤官": 1.2,  # 伤官更冲
}


# ════════════════════════════════════════════════
#  月干地支计算
# ════════════════════════════════════════════════

def get_month_gan_zhi(year_gan: str, month_num: int) -> Tuple[str, str]:
    """根据年干和农历月份计算月柱干支（五虎遁）"""
    start_gan = MONTH_GAN_START[year_gan]
    start_idx = TG_INDEX[start_gan]
    offset = month_num - 1
    gan_idx = (start_idx + offset) % 10
    zhi_idx = (DZ_INDEX["寅"] + offset) % 12
    return TIAN_GAN[gan_idx], DI_ZHI[zhi_idx]


def get_zhi_relations(month_zhi: str, all_zhi: List[str]) -> List[str]:
    """分析月地支与四柱地支的刑冲害合关系"""
    relations = []
    pillar_names = ["年", "月", "日", "时"]

    for i, zhi in enumerate(all_zhi):
        p_name = pillar_names[i]
        # 六合
        if zhi in DZ_LIU_HE and DZ_LIU_HE[zhi] == month_zhi:
            relations.append(f"合{p_name}柱（{zhi}→{month_zhi}）")
        if month_zhi in DZ_LIU_HE and DZ_LIU_HE[month_zhi] == zhi:
            relations.append(f"合{p_name}柱（{month_zhi}→{zhi}）")
        # 六冲
        if zhi in DZ_LIU_CHONG and DZ_LIU_CHONG[zhi] == month_zhi:
            relations.append(f"冲{p_name}柱（{zhi}↔{month_zhi}）")
        if month_zhi in DZ_LIU_CHONG and DZ_LIU_CHONG[month_zhi] == zhi:
            relations.append(f"冲{p_name}柱（{month_zhi}↔{zhi}）")
        # 六害
        if zhi in DZ_LIU_HAI and DZ_LIU_HAI[zhi] == month_zhi:
            relations.append(f"害{p_name}柱（{zhi}↔{month_zhi}）")
        # 六破
        if zhi in DZ_LIU_PO and DZ_LIU_PO[zhi] == month_zhi:
            relations.append(f"破{p_name}柱（{zhi}↔{month_zhi}）")
        # 三刑
        for k, v in DZ_SAN_XING.items():
            if {zhi, month_zhi} == {k, v}:
                relations.append(f"刑{p_name}柱（{zhi}↔{month_zhi}）")
                break
        # 自刑
        if zhi == month_zhi and month_zhi in ("辰", "午", "酉", "亥"):
            relations.append(f"刑{p_name}柱（{zhi}↔{month_zhi}自刑）")

    return relations


# ════════════════════════════════════════════════
#  增强评分系统 (v3.0)
# ════════════════════════════════════════════════

def _calc_enhanced_score(
    ss: str,
    ri_gan: str,
    month_gan: str,
    month_zhi: str,
    all_zhi: List[str],
    strong_weak: str,
    useful_god: List[str],
) -> Tuple[int, str]:
    """
    多维评分系统 (v3.0) — 明确分段版

    评分结构：
    1. 基础分(0-4)：日主旺衰
    2. 用神分(0-3)：月干用神匹配度（含五行生克和藏干影响）
    3. 季节分(0-2)：调候季节当令强度
    4. 冲刑扣分(0-2)：刑冲害合

    Returns:
        (score: 1-10, reasoning: 推理说明)
    """
    reasons = []
    base = 0

    # ─── 1. 基础分(0-4)：日主旺衰 ───
    base_by_strength = {
        "从强": 4, "从弱": 4,
        "身强": 3, "身弱": 3,
        "偏强": 2, "偏弱": 2,
        "中和": 1,
    }
    sw_base = base_by_strength.get(strong_weak, 2)
    base += sw_base
    reasons.append(f"基础分：{strong_weak}（+{sw_base}/4）")

    # ─── 2. 用神分(0-3)：月干用神匹配度（含五行生克+藏干） ───
    ri_wx = TG_WU_XING[ri_gan]
    month_gan_wx = TG_WU_XING[month_gan]

    # 判断月干是否为用神
    is_useful = month_gan_wx in useful_god
    is_avoid = month_gan_wx not in useful_god if useful_god else False

    # 正偏区分：正=稳定，偏=波动
    intensity = SS_INTENSITY.get(ss, 1.0)
    us_score = 0

    if is_useful:
        # 喜用神：匹配度高，用神分 2-3
        us_score = min(3, 2 + int(intensity))
        reasons.append(f"月干{ss}({month_gan_wx})为用神（+{us_score}/3）")
    elif is_avoid:
        # 忌神：用神分为 0
        us_score = 0
        reasons.append(f"月干{ss}({month_gan_wx})为忌神（+0/3）")
    else:
        # 中性：用神分 1
        us_score = 1
        reasons.append(f"月干{month_gan_wx}为中性（+1/3）")

    # 月干五行生克微调（在用神分基础上微调±1）
    if WU_XING_SHENG.get(month_gan_wx) == ri_wx:
        us_score = min(3, max(0, us_score + 1))
        reasons.append(f"  月干{month_gan_wx}生日主{ri_wx}(微调+1)")
    elif WU_XING_KE.get(month_gan_wx) == ri_wx:
        us_score = min(3, max(0, us_score - 1))
        reasons.append(f"  月干{month_gan_wx}克日主{ri_wx}(微调-1)")

    # 藏干微调
    cang_gan_list = DZ_CANG_GAN.get(month_zhi, [])
    hidden_adjust = 0
    for cg in cang_gan_list:
        cg_wx = TG_WU_XING[cg]
        if useful_god and cg_wx in useful_god:
            hidden_adjust += 1
        elif useful_god and cg_wx not in useful_god and cg_wx != month_gan_wx:
            hidden_adjust -= 1
    if hidden_adjust > 0:
        us_score = min(3, max(0, us_score + 1))
        reasons.append(f"  藏干中有用神(微调+1)")
    elif hidden_adjust < 0:
        us_score = min(3, max(0, us_score - 1))
        reasons.append(f"  藏干中有忌神(微调-1)")

    base += us_score

    # ─── 3. 季节分(0-2)：调候季节当令强度 ───
    seasonal = SEASON_STRENGTH.get(month_zhi, {})
    season_score = 0
    for wx, strength in seasonal.items():
        if wx == ri_wx:
            season_score = 2
            reasons.append(f"季节分：{month_zhi}月{ri_wx}当令（+2/2）")
            break
        elif wx in useful_god if useful_god else False:
            season_score = 1
            reasons.append(f"季节分：{month_zhi}月用神{wx}当令（+1/2）")
            break

    base += season_score

    # ─── 4. 冲刑扣分(0-2)：刑冲害合 ───
    conflict_deduction = 0
    relations = get_zhi_relations(month_zhi, all_zhi)
    for r in relations:
        if r.startswith("冲"):
            conflict_deduction += 2
            reasons.append(f"冲刑扣分：{r}（-2）")
        elif r.startswith("害"):
            conflict_deduction += 1
            reasons.append(f"冲刑扣分：{r}（-1）")
        elif r.startswith("刑"):
            conflict_deduction += 1
            reasons.append(f"冲刑扣分：{r}（-1）")
        elif "合" in r:
            conflict_deduction -= 1  # 合为吉，减少扣分
            reasons.append(f"冲刑扣分：{r}（+1）")

    conflict_deduction = max(0, min(2, conflict_deduction))
    base -= conflict_deduction

    # 总结各段得分
    segment_summary = (
        f"基础{sw_base}/4 + 用神{us_score}/3"
        f" + 季节{season_score}/2 - 冲刑{conflict_deduction}/2"
    )

    # 最终范围 1-10
    score = max(1, min(10, base))
    reasoning = "；".join(reasons) if reasons else "各段评分汇总"
    reasoning += f" → 最终得分{score}/10"

    return score, reasoning


# ════════════════════════════════════════════════
#  月份运势分析
# ════════════════════════════════════════════════

def _generate_detailed_description(
    ss: str,
    ri_gan: str,
    month_gan: str,
    month_zhi: str,
    month_num: int,
    all_zhi: List[str],
    strong_weak: str,
    useful_god: List[str],
    score: int,
    relations: List[str],
    ss_positive: bool,
) -> Dict[str, str]:
    """
    生成详细的月度运势描述（含推理过程）
    
    Returns:
        {
            "shi_shen_analysis": 十神推理,
            "wuxing_analysis": 五行推理, 
            "seasonal_context": 节气背景,
            "cang_gan_analysis": 藏干影响,
            "career": 事业,
            "wealth": 财运,
            "love": 感情,
            "family": 家庭,
            "health": 健康,
            "lucky_tip": 开运建议,
        }
    """
    ri_wx = TG_WU_XING[ri_gan]
    month_gan_wx = TG_WU_XING[month_gan]
    month_zhi_wx = DZ_WU_XING[month_zhi]
    cang_gan_list = DZ_CANG_GAN.get(month_zhi, [])

    # ─── 十神推理 ───
    is_useful = month_gan_wx in useful_god if useful_god else False
    is_avoid = month_gan_wx not in useful_god if useful_god else False
    
    if is_useful:
        quality = "喜用" if ss_positive else "用神（克制忌神）"
    elif is_avoid:
        quality = "忌神" if not ss_positive else "克制喜用"
    else:
        quality = "中性"
    
    shi_shen_analysis = (
        f"【十神推理】本月月干为{ss}，五行属{month_gan_wx}。"
        f"日主{ri_gan}（{ri_wx}命）见{ss}→{'喜用' if ss_positive else '忌神'}。"
    )
    
    if ss_positive:
        shi_shen_analysis += (
            f" {ss}为喜用神，对日主{ri_gan}有正面助力。"
        )
        if ss == "正官":
            shi_shen_analysis += "官星为喜，事业贵人显，做事顺利有章法。"
        elif ss == "七杀":
            shi_shen_analysis += "七杀虽猛但为你所用，压力转化为动力，挑战即是机遇。"
        elif ss == "正印":
            shi_shen_analysis += "印星护身，思维清晰，学习能力增强，得长辈或师长之助。"
        elif ss == "偏印":
            shi_shen_analysis += "枭神为用，思路独特、创意非凡，适合策划和偏门领域。"
        elif ss == "正财":
            shi_shen_analysis += "正财为喜，收入稳定增长，劳动报酬与付出成正比。"
        elif ss == "偏财":
            shi_shen_analysis += "偏财为喜，意外之财和投资回报可期，但不可贪多。"
        elif ss == "比肩":
            shi_shen_analysis += "比肩帮身，得同事朋友之助，团队合作效率倍增。"
        elif ss == "劫财":
            shi_shen_analysis += "劫财为用则竞争转化为动力，良性竞争助你进步。"
        elif ss == "食神":
            shi_shen_analysis += "食神泄秀，才华展示的好时机，表达和创作能力突出。"
        elif ss == "伤官":
            shi_shen_analysis += "伤官为喜，创新思维活跃，合适新尝试，但需注意分寸。"
    else:
        shi_shen_analysis += (
            f" {ss}为忌神，对日主{ri_gan}构成压力或消耗。"
        )
        if ss == "正官":
            shi_shen_analysis += "官星为忌，约束感强，压力大，容易被上级或规则限制。"
        elif ss == "七杀":
            shi_shen_analysis += "七杀攻身，压力山大！易遇小人、突发挑战或人事变动。需格外谨慎。"
        elif ss == "正印":
            shi_shen_analysis += "印星为忌，依赖心重、行动力不足，容易陷入舒适区而不思进取。"
        elif ss == "偏印":
            shi_shen_analysis += "枭神为忌，想法偏激、思维钻牛角尖。职场人际关系易紧张。"
        elif ss == "正财":
            shi_shen_analysis += "财星为忌，为钱所累——赚钱辛苦，劳动强度大但回报有限。"
        elif ss == "偏财":
            shi_shen_analysis += "偏财为忌，投资易亏、副业不顺。专注主业守住基本盘才是上策。"
        elif ss == "比肩":
            shi_shen_analysis += "比肩为忌，同事朋友之间暗涌竞争，利益分配容易产生摩擦。"
        elif ss == "劫财":
            shi_shen_analysis += "劫财为忌！是非月、破财月。防小人、防借贷、防合作陷阱。"
        elif ss == "食神":
            shi_shen_analysis += "食神为忌，享乐主义抬头，工作懈怠，需自律收心。"
        elif ss == "伤官":
            shi_shen_analysis += "伤官为忌！口舌是非月，易得罪人。谨言慎行，不参与八卦。"
    
    # ─── 五行推理 ───
    # 月干生日主？
    if WU_XING_SHENG.get(month_gan_wx) == ri_wx:
        wx_relation = f"月干{month_gan_wx}五行生日主{ri_wx}五行，"
        if is_useful: wx_relation += "生机勃勃，能量源源不绝。"
        else: wx_relation += "虽为忌神但因生身而有所缓冲。"
    elif WU_XING_SHENG.get(ri_wx) == month_gan_wx:
        wx_relation = f"日主{ri_wx}五行生月干{month_gan_wx}五行，"
        if is_useful: wx_relation += "输出有回报，付出有价值。"
        else: wx_relation += "被泄气，精力消耗大，容易感觉疲劳。"
    elif WU_XING_KE.get(month_gan_wx) == ri_wx:
        wx_relation = f"月干{month_gan_wx}五行克日主{ri_wx}五行，"
        if is_useful: wx_relation += "克为管制，压力之下出成果。"
        else: wx_relation += "受制被欺压，压抑感强烈。"
    elif WU_XING_KE.get(ri_wx) == month_gan_wx:
        wx_relation = f"日主{ri_wx}五行克月干{month_gan_wx}五行，"
        if is_useful: wx_relation += "掌控感强，能驾驭局面。"
        else: wx_relation += "虽能驾驭但耗费心力——能控制但累。"
    else:
        wx_relation = f"月干{month_gan_wx}与日主{ri_wx}五行相同，同气相连。"
    
    wuxing_analysis = f"【五行生克】{wx_relation}"

    # ─── 节气背景 ───
    seasonal_info = {
        1: "寅月，春木当令。木旺生火，对火命人有利。",
        2: "卯月，仲春木旺至极。木气最盛之月。",
        3: "辰月，暮春土旺。木有余气，水库开启。",
        4: "巳月，孟夏火旺。火势初升，木已退气。",
        5: "午月，仲夏火旺至极。一年中火气最盛之时。",
        6: "未月，季夏土旺。火有余气，木库收藏。",
        7: "申月，孟秋金旺。金气初升，火渐退气。",
        8: "酉月，仲秋金旺至极。金最盛之月，肃杀之气重。",
        9: "戌月，季秋土旺。金有余气，火库收藏。",
        10: "亥月，孟冬水旺。水气初升，金已退气。",
        11: "子月，仲冬水旺至极。一年中水气最盛之时。",
        12: "丑月，季冬土旺。水有余气，金库收藏。",
    }
    
    seasonal_context = f"【节气背景（知识库《00_五行详解》×《05_十二长生与旺衰》综合判断）】{seasonal_info.get(month_num, '')}"
    
    # 结合命主强弱调整节气描述
    if busy := SEASON_STRENGTH.get(month_zhi, {}):
        for wx, strength in busy.items():
            if wx == ri_wx:
                seasonal_context += f" 你的日主是{ri_wx}命，此月{ri_wx}当令（强度{strength}），"
                if strong_weak in ("身弱", "从弱", "偏弱"):
                    seasonal_context += f"对{strong_weak}的你来说如得助力，整体气场提升。"
                else:
                    seasonal_context += f"对{strong_weak}的你来说更是锦上添花，但注意过旺则折。"
            elif wx in useful_god if useful_god else False:
                seasonal_context += f" 此月用神{wx}当令，整体环境助你运势。"
    
    # ─── 藏干分析 ───
    if cang_gan_list:
        cang_ss = [get_shi_shen_for_gan(ri_gan, cg) for cg in cang_gan_list]
        cang_detail = "、".join(f"{cg}({ss})" for cg, ss in zip(cang_gan_list, cang_ss))
        cang_gan_analysis = (
            f"【藏干影响】月支{month_zhi}藏干：{cang_detail}。"
        )
        # 藏干分析对6个领域的影响
        useful_in_hidden = False
        for cg in cang_gan_list:
            cg_wx = TG_WU_XING[cg]
            if useful_god and cg_wx in useful_god:
                useful_in_hidden = True
                break
        if useful_in_hidden:
            cang_gan_analysis += " 地支藏干中有用神五行，虽非显性但对运势有潜在支撑。"
        else:
            cang_gan_analysis += " 藏干中无情帮助，需依靠月干外部力量。"
    else:
        cang_gan_analysis = ""

    # ─── 关系总结 ───
    relations_text = "、".join(relations) if relations else "无特殊刑冲害合"

    # ─── 6领域预测 ───
    categories = _gen_month_categories_v3(
        ss, ss_positive, relations, score, month_num,
        month_gan_wx, ri_wx, useful_god,
    )

    return {
        "shi_shen_analysis": shi_shen_analysis,
        "wuxing_analysis": wuxing_analysis,
        "seasonal_context": seasonal_context,
        "cang_gan_analysis": cang_gan_analysis,
        "relations_text": relations_text,
        **categories,
    }


# ════════════════════════════════════════════════
#  月度6领域预测 (v3 - 更丰富)
# ════════════════════════════════════════════════

def _gen_month_categories_v3(
    ss: str, ss_positive: bool,
    relations: List[str],
    score: int,
    month_num: int,
    month_gan_wx: str,
    ri_wx: str,
    useful_god: List[str],
) -> Dict[str, str]:
    """生成6领域预测（v3增强版：结合五行+十神双维度）"""
    month_name = MONTH_NAMES[month_num]
    has_conflict = any(r.startswith("冲") or r.startswith("害") or r.startswith("刑") for r in relations)
    has_he = any("合" in r for r in relations)

    c = {}

    # ═══════════ 事业 ═══════════
    if ss_positive:
        career = f"【{month_name}·事业】"
        career += _positive_career_detail(ss, month_gan_wx, ri_wx, useful_god)
    else:
        career = f"【{month_name}·事业】"
        career += _negative_career_detail(ss, month_gan_wx, ri_wx)
    
    if has_conflict:
        career += " 注意：月支有冲刑，职场易有变数和人事摩擦，重要决策慎之又慎。"
    if has_he:
        career += " 六合之象对合作有利，适合团队协作和商务谈判。"
    if score >= 8:
        career += " 综合评分高，宜积极进取，大胆把握机会。"
    elif score <= 4:
        career += " 综合评分偏低，宜稳守本位，不宜冒进。"
    c["事业"] = career

    # ═══════════ 财运 ═══════════
    if ss_positive:
        wealth = f"【{month_name}·财运】"
        if ss in ("正财", "偏财"):
            wealth += f"财星值月为喜，收入增长明显。"
            if ss == "偏财":
                wealth += " 偏财旺，投资/副业有额外进账。见好就收，不要贪心。"
            else:
                wealth += " 正财稳步增长，工资奖金有提升，理财收益稳定。"
        elif ss in ("正官", "七杀"):
            wealth += "官杀值月，财运以正职为主。收入稳定但横财不显，不宜投机。"
        elif ss in ("正印", "偏印"):
            wealth += "印星值月，财运平稳。在学习/提升上的投资会有长远回报。节俭为上。"
        elif ss in ("比肩", "劫财"):
            wealth += "比劫值月为喜，合作得财。但账目要清晰，先小人后君子。"
        elif ss in ("食神", "伤官"):
            wealth += "食伤值月为喜，才华变现能力强。靠技能/创意赚钱。消费欲望也强，适度节制。"
    else:
        wealth = f"【{month_name}·财运】"
        if ss in ("正财", "偏财"):
            wealth += "财星为忌，为钱所累。工作强度大但收入增长有限。控制开支。"
            if ss == "偏财":
                wealth += " 投资风险高，不宜进场。"
        elif ss in ("正官", "七杀"):
            wealth += "官杀为忌，工作压力大影响财运。不要因急于赚钱而冲动决策。"
        elif ss in ("正印", "偏印"):
            wealth += "印星为忌，赚钱动力不足，容易安于现状。需主动出击。"
        elif ss in ("比肩", "劫财"):
            wealth += "比劫为忌，防合伙破财、防借钱。管好自己的钱包。"
            if ss == "劫财":
                wealth += " ⚠️本月破财风险高！不借贷、不担保、不投资。"
        elif ss in ("食神", "伤官"):
            wealth += "食伤为忌，开销大。为娱乐、美食、面子花钱。延迟消费，三思而买。"
    
    if has_conflict:
        wealth += " 冲刑影响财运稳定，避免大额资金变动。"
    c["财运"] = wealth

    # ═══════════ 感情 ═══════════
    if ss_positive:
        love = f"【{month_name}·感情】"
        if ss in ("正官", "七杀"):
            love += "官杀月，女命情感关注度高。单身者有机会遇到重要缘分。"
            if ss == "七杀":
                love += " 但七杀之缘来得快去得也快，需辨别良缘还是过客。"
        elif ss in ("正财", "偏财"):
            love += "财星月（男命妻星），感情关系融洽。单身者桃花运不错。"
            if ss == "偏财":
                love += " 但偏财为偏缘，注意烂桃花。"
        elif ss in ("正印", "偏印"):
            love += "印星月，感情平淡温馨。适合陪伴和沟通。家庭氛围好。"
        elif ss in ("比肩", "劫财"):
            love += "比劫月，感情中双方平等互动。劫财需注意沟通方式。"
        elif ss in ("食神", "伤官"):
            love += "食伤月，魅力提升。表达能力强，相处愉快。"
            if ss == "伤官":
                love += " 但伤官亦主挑剔，眼光高容易失望。"
    else:
        love = f"【{month_name}·感情】"
        if ss in ("正官", "七杀"):
            love += "官杀为忌，情感压力大。"
            if ss == "七杀":
                love += " 容易冲动做决定，不要因一时情绪说分手。"
            else:
                love += " 要求和期待高，给自己和对方都留点空间。"
        elif ss in ("正财", "偏财"):
            love += "财星为忌，感情易被现实问题困扰。坦诚沟通财务安排。"
        elif ss in ("正印", "偏印"):
            love += "印星为忌，感情中依赖性增强。注意保持独立性。"
            if ss == "偏印":
                love += " 想太多、疑心重，多交流为上。"
        elif ss in ("比肩", "劫财"):
            love += "比劫为忌，注意感情中的竞争和第三方干扰。"
            if ss == "劫财":
                love += " 容易因财务或朋友问题起矛盾。"
        elif ss in ("食神", "伤官"):
            love += "食伤为忌。"
            if ss == "伤官":
                love += " ⚠️伤官克官，注意言辞，容易出口伤人。生气时少说话。"
            else:
                love += " 太过放纵自我，忽略伴侣感受。"
    
    if has_conflict:
        love += " 冲刑影响感情稳定，多沟通、少冷战。"
    if has_he:
        love += " 合象有利感情发展，适合约会和增进感情。"
    c["感情"] = love

    # ═══════════ 家庭 ═══════════
    if ss_positive:
        family = f"【{month_name}·家庭】"
        if ss in ("正印", "偏印"):
            family += "印星为喜，家庭和睦。父母/长辈身体健康，是你的坚强后盾。"
        elif ss in ("正财", "偏财"):
            family += "家庭财务状况良好，适合添置大件或改善家庭环境。"
        elif ss in ("比肩", "劫财"):
            family += "兄弟姐妹来往密切，家庭热闹。注意劫财月可能因为钱闹小矛盾。"
        elif ss in ("食神", "伤官"):
            family += "家庭氛围轻松愉快，适合组织家庭聚会或短途出游。"
        elif ss in ("正官", "七杀"):
            family += "家庭责任感强，愿意为家庭付出。是家中可靠的顶梁柱。"
    else:
        family = f"【{month_name}·家庭】"
        if ss in ("正官", "七杀"):
            family += "家庭压力增大，可能为长辈健康/家庭事务操心。"
        elif ss in ("正印", "偏印"):
            family += "家庭中容易依赖或被依赖过度，需平衡角色。"
        elif ss in ("正财", "偏财"):
            family += "家庭开支增多，注意预算管理。"
        elif ss in ("比肩", "劫财"):
            family += "家庭内部容易因利益问题产生分歧。"
        elif ss in ("食神", "伤官"):
            family += "家庭气氛懒散或紧张，需要主动带动正能量。"
    
    if has_conflict:
        family += " 冲刑入命，家庭易有突发事件需要处理。保持冷静。"
    if has_he:
        family += " 合象入家庭，关系和谐融洽。"
    c["家庭"] = family

    # ═══════════ 健康 ═══════════
    health = f"【{month_name}·健康】"
    if ss_positive:
        if ss in ("正官", "七杀"):
            health += "官杀月压力大，注意肩颈和神经紧张。适当运动和放松很重要。"
            if ss == "七杀":
                health += " 精力充沛但也容易过度消耗，注意休息。"
        elif ss in ("正印", "偏印"):
            health += "身体状态良好，适合养生调理。注意饮食规律。"
            if ss == "偏印":
                health += " 偏印主思虑，注意睡眠质量。"
        elif ss in ("正财", "偏财"):
            health += "整体健康平稳。劳逸结合，避免过度劳累。"
        elif ss in ("比肩", "劫财"):
            health += "体能充沛，适合运动和户外活动。"
        elif ss in ("食神", "伤官"):
            health += "胃口好，享受美食同时注意节制。适合作息规律。"
    else:
        if ss in ("正官", "七杀"):
            health += "工作压力影响身体。注意：头部紧张、失眠、肩颈酸痛。"
            if ss == "七杀":
                health += " ⚠️七杀克身，注意免疫力下降，小病可能找上门。"
        elif ss in ("正印", "偏印"):
            health += "懒动、疲劳感强。再忙也要逼自己运动。"
        elif ss in ("正财", "偏财"):
            health += "劳碌命，赚钱辛苦。不要透支身体换钱。"
        elif ss in ("比肩", "劫财"):
            health += "社交活动多影响作息，注意休息质量。"
        elif ss in ("食神", "伤官"):
            health += "饮食不节、作息紊乱。注意肠胃和上火问题。"
    
    # 五行健康提醒
    wx_health_tips = {
        "木": "注意肝胆和眼睛保养，少熬夜。",
        "火": "注意心脏和血液循环，避免过劳。",
        "土": "注意脾胃消化系统，饮食规律。",
        "金": "注意呼吸系统和皮肤护理。",
        "水": "注意肾脏和泌尿系统，保暖防寒。",
    }
    health += f" 五行健康参考：{wx_health_tips.get(ri_wx, '')}"
    c["健康"] = health

    # ═══════════ 开运建议 ═══════════
    tip = f"【{month_name}·开运建议】"
    if ss_positive:
        tip += f"本月运势向好（评分{score}/10）。宜主动出击，把握{ss}带来的机遇。"
    else:
        tip += f"本月运势偏弱（评分{score}/10）。宜静不宜动，重要决策延后。多听取他人意见。"
    
    if useful_god:
        god_colors = {"木": "绿色/青色", "火": "红色/紫色", "土": "黄色/棕色", "金": "白色/金色", "水": "黑色/蓝色"}
        color = god_colors.get(useful_god[0], "当季色")
        tip += f" 宜穿{color}服饰增强运势。"
    
    if has_conflict:
        tip += " 冲刑较重，注意出行安全和重要文件备份。"
    if has_he:
        tip += " 合象有利，适合合作谈判和社交应酬。"
    
    c["开运建议"] = tip

    return c


def _positive_career_detail(ss: str, mw: str, rw: str, ug: List[str]) -> str:
    """喜用神事业描述（数据驱动：从 knowledge_loader 加载）"""
    return get_shi_shen_description(ss, "positive", "career")


def _negative_career_detail(ss: str, mw: str, rw: str) -> str:
    """忌神事业描述（数据驱动：从 knowledge_loader 加载）"""
    return get_shi_shen_description(ss, "negative", "career")


# ════════════════════════════════════════════════
#  月份分析入口
# ════════════════════════════════════════════════

def analyze_single_month(
    month_num: int,
    year_gan: str,
    ri_gan: str,
    all_zhi: List[str],
    strong_weak: str,
    useful_god: List[str],
) -> Dict:
    """
    分析一个月份的运势（v3增强版）
    """
    month_gan, month_zhi = get_month_gan_zhi(year_gan, month_num)

    # 十神
    ss = get_shi_shen_for_gan(ri_gan, month_gan)

    # 地支五行
    zhi_wx = DZ_WU_XING[month_zhi]

    # 地支关系
    relations = get_zhi_relations(month_zhi, all_zhi)

    # 简单喜忌判断（用于兜底）
    if strong_weak == "从强":
        ss_positive = ss in ("正印", "偏印", "比肩", "劫财")
    elif strong_weak == "从弱":
        ss_positive = ss in ("正官", "七杀", "正财", "偏财", "食神", "伤官")
    elif strong_weak == "身强":
        ss_positive = ss in ("正官", "七杀", "正财", "偏财", "食神", "伤官")
    else:
        ss_positive = ss in ("正印", "偏印", "比肩", "劫财")

    # 增强评分
    score, score_reasoning = _calc_enhanced_score(
        ss, ri_gan, month_gan, month_zhi, all_zhi,
        strong_weak, useful_god,
    )

    # 详细信息
    details = _generate_detailed_description(
        ss, ri_gan, month_gan, month_zhi, month_num,
        all_zhi, strong_weak, useful_god, score, relations,
        ss_positive,
    )

    # 简单亮点/警告（保留兼容）
    highlights = []
    warnings = []
    if ss_positive:
        highlights.append(f"{ss}值月为喜用，运势向好")
    else:
        warnings.append(f"{ss}值月为忌神，需谨慎行事")
    for r in relations:
        if "冲" in r:
            warnings.append(f"月支相冲，注意变动和意外")
        elif "害" in r:
            warnings.append(f"月支相害，提防小人和是非")
        elif "刑" in r:
            warnings.append(f"月支相刑，注意口舌和纠纷")
    if any("合" in r for r in relations):
        highlights.append("有六合之象，人际关系和谐")

    return {
        "month_num": month_num,
        "month_name": MONTH_NAMES[month_num],
        "date_range": MONTH_DATE_RANGE[month_num],
        "gan": month_gan,
        "zhi": month_zhi,
        "gan_zhi": month_gan + month_zhi,
        "shi_shen": ss,
        "zhi_wx": zhi_wx,
        "relations": relations,
        "score": score,
        "score_reasoning": score_reasoning,
        "highlights": highlights,
        "warnings": warnings,
        "analysis": details,  # 详细推理
        "categories": {
            "事业": details["事业"],
            "财运": details["财运"],
            "感情": details["感情"],
            "家庭": details["家庭"],
            "健康": details["健康"],
            "开运建议": details["开运建议"],
        },
    }


def predict_monthly(year_gan: str, ri_gan: str, all_zhi: List[str],
                    strong_weak: str, useful_god: List[str]) -> List[Dict]:
    """生成整年的月度运势预测"""
    results = []
    for m in range(1, 13):
        month_data = analyze_single_month(
            m, year_gan, ri_gan, all_zhi, strong_weak, useful_god
        )
        results.append(month_data)
    return results


# ════════════════════════════════════════════════
#  10年运势预测
# ════════════════════════════════════════════════

def analyze_year_shi_shen(ri_gan: str, year_gan: str) -> str:
    """年干对日主的十神关系"""
    return get_shi_shen_for_gan(ri_gan, year_gan)


def _generate_year_detail_description(
    year: int, ss: str, strong_weak: str,
    liunian_gan: str, liunian_zhi: str,
    all_zhi: List[str], current_da_yun: Optional[Dict],
    ri_gan: str, useful_god: List[str],
) -> Dict[str, str]:
    """生成年度详细描述"""
    ri_wx = TG_WU_XING[ri_gan]
    year_wx = TG_WU_XING[liunian_gan]
    cang_gan_list = DZ_CANG_GAN.get(liunian_zhi, [])
    
    # 十神推理
    is_useful = year_wx in useful_god if useful_god else False
    if is_useful:
        ss_nature = "喜用神"
    else:
        ss_nature = "忌神" if useful_god else "中性"
    
    shi_shen_analysis = (
        f"【{year}年十神推理】流年天干{liunian_gan}（{year_wx}）对日主{ri_gan}（{ri_wx}）"
        f"呈{ss}关系，为{ss_nature}。"
    )
    
    # 五行生克
    if WU_XING_SHENG.get(year_wx) == ri_wx:
        wx_part = f"{year_wx}生{ri_wx}，能量输入之年，生机勃勃。"
    elif WU_XING_SHENG.get(ri_wx) == year_wx:
        wx_part = f"{ri_wx}生{year_wx}，输出之年，付出较多。"
    elif WU_XING_KE.get(year_wx) == ri_wx:
        wx_part = f"{year_wx}克{ri_wx}，压力之年，外部环境对你形成挑战。"
    elif WU_XING_KE.get(ri_wx) == year_wx:
        wx_part = f"{ri_wx}克{year_wx}，掌控之年，你能驾驭局面但消耗心力。"
    else:
        wx_part = f"{year_wx}与{ri_wx}同五行，同气连枝。"
    
    wuxing_analysis = f"【五行生克】{wx_part}"

    # 藏干影响
    if cang_gan_list:
        cang_ss = [get_shi_shen_for_gan(ri_gan, cg) for cg in cang_gan_list]
        cang_detail = "、".join(f"{cg}({ss})" for cg, ss in zip(cang_gan_list, cang_ss))
        cang_gan_analysis = f"【藏干影响】流年地支{liunian_zhi}藏干：{cang_detail}。"
    else:
        cang_gan_analysis = ""

    # 大运叠加
    dy_analysis = ""
    if current_da_yun:
        dy_ss = current_da_yun.get("shi_shen", "")
        dy_gan_zhi = current_da_yun.get("gan_zhi", "")
        dy_age_range = f"{current_da_yun['start_age']}-{current_da_yun['end_age']}岁"
        dy_analysis = (
            f"【大运叠加】当前处于{dy_gan_zhi}大运（{dy_age_range}，大运十神{dy_ss}）。"
        )
        if dy_ss == ss:
            dy_analysis += f" 大运{dy_ss}与流年{ss}叠加，能量加倍，吉凶效果显著放大。"
        elif dy_ss in ("劫财") and ss in ("正财", "偏财"):
            dy_analysis += " 大运劫财遇流年财星，破财风险较高，理财需格外谨慎。"
        elif dy_ss in ("正官") and ss in ("正官", "七杀"):
            dy_analysis += " 大运+流年官杀并旺，事业机遇与压力同步增大。"
        elif dy_ss in ("正印") and ss in ("食神", "伤官"):
            dy_analysis += " 大运印星可化解流年伤官之弊，有惊无险。"
        else:
            dy_analysis += f" 大运{dy_ss}与流年{ss}相互交织，运势呈现叠加效应。"

    return {
        "shi_shen_analysis": shi_shen_analysis,
        "wuxing_analysis": wuxing_analysis,
        "cang_gan_analysis": cang_gan_analysis,
        "dy_analysis": dy_analysis,
    }


def analyze_year_detail(
    year: int,
    liunian_gan: str,
    liunian_zhi: str,
    ri_gan: str,
    current_da_yun: Optional[Dict],
    all_zhi: List[str],
    strong_weak: str,
    age: int,
    useful_god: List[str],
) -> Dict:
    """对某一年份进行详细的10项分析"""
    ss = analyze_year_shi_shen(ri_gan, liunian_gan)
    zhi_wx = DZ_WU_XING[liunian_zhi]
    relations = get_zhi_relations(liunian_zhi, all_zhi)
    has_conflict = any(
        r.startswith("冲") or r.startswith("害") or r.startswith("刑")
        for r in relations
    )

    # 评分（使用增强评分）
    score, score_reasoning = _calc_enhanced_score(
        ss, ri_gan, liunian_gan, liunian_zhi, all_zhi,
        strong_weak, useful_god,
    )
    has_he = any("合" in r for r in relations)

    # 大运影响
    dayun_effect = ""
    if current_da_yun:
        dy_ss = current_da_yun.get("shi_shen", "")
        if dy_ss == ss:
            dayun_effect = f"大运{dy_ss}与流年{ss}相同，力量加倍，影响显著。"
        elif dy_ss == "劫财" and ss in ("正财", "偏财"):
            dayun_effect = "大运劫财遇流年财星，破财风险高，需格外谨慎。"
        elif dy_ss == "正官" and ss in ("正官", "七杀"):
            dayun_effect = "大运与流年官杀并旺，事业机遇与压力同步增大。"
        elif dy_ss == "正印" and ss in ("食神", "伤官"):
            dayun_effect = "大运印星解流年伤官之弊，有惊无险。"
        else:
            dy_effect_ss = current_da_yun.get("shi_shen", "")
            dayun_effect = f"大运{dy_effect_ss}与流年{ss}相互作用。"

    # 详细描述
    detail = _generate_year_detail_description(
        year, ss, strong_weak, liunian_gan, liunian_zhi,
        all_zhi, current_da_yun, ri_gan, useful_god,
    )

    # 年度各领域预测
    categories = _gen_year_categories(
        ss, strong_weak, has_conflict, has_he, year,
        liunian_gan, liunian_zhi, ri_gan,
    )

    # 关键决策建议
    suggestions = _gen_year_suggestions(ss, has_conflict, has_he)

    return {
        "year": year,
        "age": age,
        "gan_zhi": liunian_gan + liunian_zhi,
        "gan": liunian_gan,
        "zhi": liunian_zhi,
        "shi_shen": ss,
        "score": score,
        "score_reasoning": score_reasoning,
        "has_conflict": has_conflict,
        "has_he": has_he,
        "relations": relations,
        "categories": categories,
        "dayun_effect": dayun_effect,
        "detail": detail,
        "suggestions": suggestions,
    }


def _gen_year_categories(
    ss: str, strong_weak: str, has_conflict: bool,
    has_he: bool, year: int,
    liunian_gan: str, liunian_zhi: str, ri_gan: str,
) -> Dict[str, str]:
    """生成年度各领域预测（v3增强版）"""
    c = {}
    ri_wx = TG_WU_XING[ri_gan]
    year_wx = TG_WU_XING[liunian_gan]

    # 五行关系判断
    if WU_XING_SHENG.get(year_wx) == ri_wx:
        wx_nature = "生我"
    elif WU_XING_SHENG.get(ri_wx) == year_wx:
        wx_nature = "我生"
    elif WU_XING_KE.get(year_wx) == ri_wx:
        wx_nature = "克我"
    elif WU_XING_KE.get(ri_wx) == year_wx:
        wx_nature = "我克"
    else:
        wx_nature = "同五行"

    # 事业
    career = f"【{year}年·事业】{liunian_gan}{liunian_zhi}年，流年十神{ss}。"
    career_text = {
        "正官": "官星值年，事业运势向好，职场上有晋升或加薪机会。上级器重，适合展示能力。但压力随之增大，需要学会调节。",
        "七杀": "七杀临年！事业上的挑战之年。压力与机遇并存，可能有岗位调整或职责变化。拿出勇气和魄力去面对，跨过这个坎之后事业会有质的飞跃。注意：不宜冲动跳槽。",
        "正印": "印星护年，事业平稳不是忙乱的一年。适合静心学习、考证、提升专业技能。工作中得长辈和前辈指点，贵人运不错。",
        "偏印": "偏印之年，思路活跃但可能不被主流理解。适合研究、策划、创意类工作。注意职场人际关系，想法虽好也要注意沟通方式。",
        "正财": "正财之年，事业稳定发展，付出有回报。工作表现会被看见，可能获得奖金或绩效提成。适合稳扎稳打，不宜激进。",
        "偏财": "偏财之年，事业上有额外机遇。可能有副业、兼职或项目提成的机会。但也容易分散主业精力，需权衡利弊。",
        "比肩": "比肩值年，适合团队合作。同事/合作伙伴会给你带来帮助，但也要注意利益分配。不宜单打独斗，借力使力效果更好。",
        "劫财": "劫财之年！职场竞争激烈。谨防功劳被抢或被甩锅，做事留好记录和证据。人际关系上多留个心眼。",
        "食神": "食神之年，才华得以发挥。创意和想法会被采纳，适合从事内容创作、设计等创意工作。工作氛围轻松愉快。",
        "伤官": "伤官临年，锋芒毕露。适合创新、创业，但不适合循规蹈矩的工作。注意口舌是非，言辞不要太尖锐。",
    }
    career += career_text.get(ss, f"事业运势平稳。")
    # 五行生克对事业的影响
    if wx_nature == "生我":
        career += f" 从五行看，{year_wx}年生{ri_wx}，能量注入，事业上有外援助力。"
    elif wx_nature == "克我":
        career += f" 从五行看，{year_wx}年克{ri_wx}，外在压力大，但也促使成长。"
    c["事业"] = career

    # 财运
    wealth = f"【{year}年·财运】"
    wealth_text = {
        "正官": "正财为主，收入稳定但增长空间有限。官星制劫财，适合存钱和稳健理财。不宜投机。",
        "七杀": "有偏财运但也伴随风险。投资机会多但需谨慎甄别，高风险高回报。宜见好就收，切忌追涨杀跌。",
        "正印": "财运平稳，不是大进大出的年份。在学习/进修上的投资会获得长远回报。家庭大额支出可能。",
        "偏印": "偏门财运较旺，但来路不正的钱不要碰。投资理财保持理性和谨慎。",
        "正财": "财运亨通的一年！正职收入增长明显，工资奖金有望提升。理财收益稳健。",
        "偏财": "偏财运强劲，投资/副业有明显收获。但也容易财来财去，需有储蓄计划。",
        "比肩": "财运一般，有朋友合作赚钱的机会。注意合伙中的利益分配，先小人后君子。",
        "劫财": "破财之年！开销大，意外支出多。不宜大额投资，不借钱，不做担保。控制消费。",
        "食神": "财源来自才艺和创意。靠技术/内容赚钱，收入来源多样化。但消费欲望也强。",
        "伤官": "开销大，容易为面子消费。可能有创业或投资举动，需谨慎评估风险。偏财运存在但不稳定。",
    }
    wealth += wealth_text.get(ss, f"财运普通，以稳为主。")
    c["财运"] = wealth

    # 感情
    love = f"【{year}年·感情】"
    love_text = {
        "正官": "感情运势稳定（女命正官为夫星）。单身者有机会遇到靠谱对象，恋爱中的人适合谈婚论嫁。已婚者家庭责任感增强。",
        "七杀": "感情波动较大（女命七杀为偏夫）。可能有新的感情诱惑，桃花运旺但也容易冲动。已有伴侣的注意沟通。",
        "正印": "感情平淡温馨。单身者可能通过家人介绍认识对象。已婚者家庭生活和谐，适合备孕或增加家庭活动。",
        "偏印": "感情上容易想太多，患得患失。需要多和伴侣沟通，不要一个人闷在心里。",
        "正财": "感情运佳（男命正财为妻星）。单身男命有机会遇到心仪对象，已婚者夫妻关系甜蜜。",
        "偏财": "异性缘佳（男命偏财为偏妻）。注意烂桃花，已婚者需保持分寸避免误会。",
        "比肩": "感情上需注意竞争。单身者可能有情敌，已婚者注意别让工作占用陪伴时间。",
        "劫财": "感情因财务问题可能产生矛盾。坦诚沟通财务状况，避免隐瞒。桃花运一般。",
        "食神": "感情生活愉快，相处融洽。适合一起旅行、参加活动。单身者魅力提升。",
        "伤官": "注意言辞，容易因小事伤害伴侣感情。单身者眼光高、要求多，不容易找到满意对象。",
    }
    love += love_text.get(ss, f"感情运势平顺。")
    c["感情"] = love

    # 健康
    health = f"【{year}年·健康】"
    health_text = {
        "正官": "精神压力大，注意肩颈/脊柱健康。建议定期运动，避免久坐。",
        "七杀": "身体容易疲劳，免疫力下降。注意外伤和意外，避免高风险活动。注意心脏和血压。",
        "正印": "健康状况良好，适合体检和养生。注意消化系统，饮食规律。",
        "偏印": "注意神经衰弱和睡眠问题。容易思虑过度影响休息，建议规律作息。",
        "正财": "身体状态平稳。注意饮食，防止三高。适当运动，保持活力。",
        "偏财": "精力旺盛但容易过劳。注意劳逸结合，不要透支身体。",
        "比肩": "身体不错，适合运动健身。注意和朋友聚会时的饮食节制。",
        "劫财": "注意消化系统问题。情绪容易影响身体，保持心情愉悦。",
        "食神": "胃口好，容易发胖。注意肠胃和饮食节制。适合健身塑形。",
        "伤官": "注意上火、失眠、皮肤问题。情绪波动大，需要给自己减压。",
    }
    health += health_text.get(ss, f"身体状况整体平稳。")
    health += f" 五行建议：{ri_wx}命人全年注意{'肝胆和眼睛' if ri_wx == '木' else '心脏和血液循环' if ri_wx == '火' else '脾胃消化' if ri_wx == '土' else '呼吸系统和皮肤' if ri_wx == '金' else '肾脏和保暖'}方面的保养。"
    c["健康"] = health

    # 家庭
    if has_conflict:
        c["家庭"] = f"【{year}年·家庭】冲刑之年，家庭关系需留意。可能有意见不合的时候。多包容少计较，家和万事兴。"
    elif has_he:
        c["家庭"] = f"【{year}年·家庭】家庭和睦，适合家庭聚会和共同出游。长辈身体健康，家庭氛围良好。"
    else:
        c["家庭"] = f"【{year}年·家庭】家庭运势平稳，按部就班即可。"

    # 开运建议
    suggestions_parts = []
    if has_conflict:
        suggestions_parts.append(f"冲刑之年宜静不宜动，重大决策多方求证后再做。")
    if ss in ("劫财", "伤官", "七杀"):
        suggestions_parts.append(f"{ss}年为风险期，凡事保守三分，留好退路。")
    if ss in ("正财", "正官", "食神"):
        suggestions_parts.append(f"{ss}年为好运年，积极把握机会，大胆行动。")
    c["开运建议"] = "；".join(suggestions_parts) if suggestions_parts else "顺势而为，保持平常心。"

    return c


def _gen_year_suggestions(ss: str, has_conflict: bool, has_he: bool) -> List[str]:
    """关键决策建议"""
    suggestions = []

    if ss in ("正官", "七杀"):
        suggestions.append("事业发展是关键，可争取晋升或承担更重要的角色。")
    if ss in ("正财", "偏财"):
        suggestions.append("财运好，适合做财务规划，但在偏财年注意风险控制。")
    if ss == "劫财":
        suggestions.append("避免大额投资、借贷和担保。做好预算，控制支出。")
    if ss == "伤官":
        suggestions.append("注意言行举止，避免得罪人。适合创新但也需遵守规则。")
    if ss in ("正印", "偏印"):
        suggestions.append("适合学习进修、考取证书，为未来发展打基础。")
    if has_conflict:
        suggestions.append("冲刑之年，不宜远行或重大变动。")
    if has_he:
        suggestions.append("合象之年，适合合作、谈判和社交。")
    suggestions.append("保持积极心态，运势只是一种趋势，主动权在你自己手中。")

    return suggestions


def dynamic_shishen_text(ss: str) -> str:
    name_map = {
        "正官": "官运", "七杀": "杀运", "正印": "印运", "偏印": "枭运",
        "正财": "财运", "偏财": "财运", "比肩": "比肩运", "劫财": "劫财运",
        "食神": "食神运", "伤官": "伤官运",
    }
    return name_map.get(ss, ss)


def predict_ten_years(
    bazi, ri_gan: str, year_gan: str, all_zhi: List[str],
    strong_weak: str, useful_god: List[str],
    dayun_list: List[Dict], birth_year: int, gender: str,
    start_year: int = 2026
) -> Dict:
    """预测未来10年运势"""
    from .dayun import get_liu_nian

    years = []

    for i in range(10):
        year = start_year + i
        age = year - birth_year

        # 流年干支
        ln = get_liu_nian(year)

        # 找到当前所处的大运
        current_dy = None
        for step in dayun_list:
            if step["start_age"] <= age <= step["end_age"]:
                current_dy = step
                break

        detail = analyze_year_detail(
            year, ln["tian_gan"], ln["di_zhi"],
            ri_gan, current_dy, all_zhi,
            strong_weak, age, useful_god,
        )
        years.append(detail)

    # 综合10年评价
    avg_score = sum(y["score"] for y in years) / len(years)
    good_years = [y["year"] for y in years if y["score"] >= 7]
    tough_years = [y["year"] for y in years if y["score"] <= 4]

    summary_parts = []
    if avg_score >= 7:
        summary_parts.append("未来10年整体运势向好，是人生的上升期。")
    elif avg_score >= 5:
        summary_parts.append("未来10年运势起伏中等，把握好年份是关键。")
    else:
        summary_parts.append("未来10年挑战较多，需谨慎规划，稳中求进。")

    if good_years:
        summary_parts.append(f"好运年份：{'、'.join(str(y) for y in good_years)}，这些年份宜积极进取。")
    if tough_years:
        summary_parts.append(f"挑战年份：{'、'.join(str(y) for y in tough_years)}，这些年份宜稳重保守。")

    return {
        "start_year": start_year,
        "end_year": start_year + 9,
        "years": years,
        "avg_score": round(avg_score, 1),
        "summary": " ".join(summary_parts),
        "good_years": good_years,
        "tough_years": tough_years,
    }

def generate_year_overview(monthly_predictions, ri_gan,
                            strong_weak, useful_god,
                            liunian_gan_zhi, ri_wx):
    """
    基于12个月度数据生成年度总评
    Returns: {avg_score, good_months, bad_months, summary, categories, yi_list, ji_list}
    """
    scores = [m['score'] for m in monthly_predictions]
    avg_score = round(sum(scores) / len(scores), 1)
    good_months = sum(1 for s in scores if s >= 7)
    bad_months = sum(1 for s in scores if s <= 4)

    domains = ['事业', '财运', '感情', '家庭', '健康', '开运建议']
    domain_months = {d: [] for d in domains}
    for m in monthly_predictions:
        cats = m.get('categories', {})
        for d in domains:
            if d in cats:
                domain_months[d].append(cats[d])

    # 年度综合概况
    summary_parts = []
    if avg_score >= 7:
        summary_parts.append(f'{liunian_gan_zhi}年整体运势不错，全年平均{avg_score}分，{good_months}个月份处于高位，是值得把握机遇的一年。')
    elif avg_score >= 5:
        summary_parts.append(f'{liunian_gan_zhi}年运势整体平稳，全年平均{avg_score}分，{good_months}个月份较好、{bad_months}个月份偏弱，起伏中求稳即可。')
    else:
        summary_parts.append(f'{liunian_gan_zhi}年需多加谨慎，全年平均{avg_score}分，{bad_months}个月份偏弱。守住基本盘比冒进更重要。')

    if good_months >= 6:
        summary_parts.append(f'有{good_months}个月运势较好，适合在这些月份推进重要事项、做出关键决策。')
    if bad_months >= 4:
        summary_parts.append(f'有{bad_months}个月需要特别留意，在这些月份应保守行事、减少重大变动。')

    # 各领域年度分析（精简版）
    categories = {}
    for d in domains:
        texts = domain_months[d]
        positive = sum(1 for t in texts if any(kw in t for kw in ['好', '佳', '顺', '旺', '进', '吉', '宜', '积极', '有利']))
        negative = sum(1 for t in texts if any(kw in t for kw in ['差', '凶', '谨慎', '注意', '防范', '压力', '不宜', '波动']))
        if positive >= negative + 3:
            trend = '向好'; flag = 'good'
        elif negative >= positive + 3:
            trend = '偏弱'; flag = 'bad'
        else:
            trend = '平稳'; flag = 'mid'

        if d == '事业':
            if flag == 'good':
                analysis = f'事业运整体{trend}，{positive}个月份有积极信号，适合主动争取机会、推进项目。'
                yi = '把握积极月份的良机，主动承担新任务或争取升迁机会；拓展人脉，参与行业交流'
                ji = '不在运势偏弱月份做重大职业变动；避免盲目扩张或过度承诺'
            elif flag == 'bad':
                analysis = f'事业运整体{trend}，{negative}个月份压力较大。不求有功但求无过，稳住现有局面。'
                yi = '以稳为主，在运势较好的月份巩固现有成果；专注提升专业技能'
                ji = '不宜跳槽、创业或大额投资；不与上级正面冲突'
            else:
                analysis = f'事业运整体{trend}，有起有伏但不至于大起大落。按部就班推进即可。'
                yi = '按计划推进工作，不急于求成；在运势较好的月份抓住小机会'
                ji = '不宜在运势偏弱的月份做激进决策'
        elif d == '财运':
            if flag == 'good':
                analysis = f'财运整体{trend}，收入稳定中见增长，{positive}个月份有不错的进账机会。'
                yi = '积极月份可适度投资理财；做好财务规划，确保储蓄比例'
                ji = '避免冲动消费和跟风投机；不宜为面子花钱'
            elif flag == 'bad':
                analysis = f'财运整体{trend}，{negative}个月份需防破财。收入上以守为主。'
                yi = '减少非必要开支；做好预算和记账'
                ji = '不宜投资、借贷、担保；避免与朋友有金钱往来'
            else:
                analysis = f'财运整体{trend}，收入支出基本平衡。偶尔会有意外支出但不会伤筋动骨。'
                yi = '保持现有的理财节奏；适当储备应急资金'
                ji = '不宜高风险投资或大额借贷'
        elif d == '感情':
            if flag == 'good':
                analysis = f'感情运整体{trend}，{positive}个月份关系融洽，是增进感情的好时机。'
                yi = '多陪伴伴侣，制造浪漫和仪式感；单身者积极社交'
                ji = '不宜在运势偏弱月份做感情上的重大决定；避免翻旧账'
            elif flag == 'bad':
                analysis = f'感情运整体{trend}，{negative}个月份容易出现摩擦和误会。需要多沟通、多包容。'
                yi = '遇到矛盾及时沟通，不让问题过夜；给对方多一些空间'
                ji = '不宜冷战、翻旧账；不宜在运势差月份谈分手或开始新恋情'
            else:
                analysis = f'感情运整体{trend}，没有太大波澜。日常相处中注意细节，小矛盾及时化解就好。'
                yi = '保持日常的关心和交流；适当制造小惊喜'
                ji = '不要因为忙于工作而忽视对方感受'
        elif d == '健康':
            if flag == 'good':
                analysis = f'健康状况整体{trend}，身体素质不错，精力充沛。但仍需注意日常作息。'
                yi = '坚持运动习惯；定期体检，关注身体信号'
                ji = '不宜过度透支身体熬夜；避免暴饮暴食'
            elif flag == 'bad':
                analysis = f'健康方面整体{trend}，{negative}个月份容易出现疲劳或小病痛。需格外注意身体保养。'
                yi = '调整作息，保证充足睡眠；注意饮食均衡，适当补充营养；劳逸结合'
                ji = '不宜过度劳累、熬夜；不宜忽视身体的早期信号'
            else:
                analysis = f'健康方面整体{trend}，没有大问题但也不可掉以轻心。保持规律生活即可。'
                yi = '保持运动习惯；注意换季时的保暖和饮食'
                ji = '不宜久坐不动；不宜过度焦虑'
        elif d == '家庭':
            if flag == 'good':
                analysis = f'家庭运整体{trend}，家人关系融洽，家庭氛围和谐。'
                yi = '多花时间陪伴家人；家庭聚会和旅行安排起来'
                ji = '不宜因工作忽略家庭；避免在家人面前发泄情绪'
            elif flag == 'bad':
                analysis = f'家庭运整体{trend}，{negative}个月份需注意家庭关系。多一分理解少一分计较。'
                yi = '多沟通多包容；遇到分歧各退一步'
                ji = '不宜把工作中的情绪带回家；避免因小事争执'
            else:
                analysis = f'家庭运整体{trend}，平平淡淡才是真。'
                yi = '保持日常沟通；节日记得表达心意'
                ji = '不宜因外界压力影响家庭关系'
        elif d == '开运建议':
            if flag == 'good':
                analysis = f'全年机遇较多，运势配合下主动出击事半功倍。'
                yi = '重要决策放在运势最好的几个月；佩戴喜用神五行的饰品和颜色'
                ji = '运势偏弱月份不冒进；忌神月份少做重大决定'
            elif flag == 'bad':
                analysis = f'全年需以稳为主，减少无谓折腾，积蓄力量等待时机。'
                yi = '多学习充电提升自己；修身养性调整心态'
                ji = '不盲目跟风；不与人攀比'
            else:
                analysis = f'运势平稳年，稳扎稳打就是最好的策略。'
                yi = '做好日常积累；抓住偶尔出现的小机会'
                ji = '不骄不躁，保持平常心'

        categories[d] = {'trend': trend, 'flag': flag, 'analysis': analysis, 'yi': yi, 'ji': ji}

    summary = ' '.join(summary_parts)
    return {
        'avg_score': avg_score,
        'good_months': good_months,
        'bad_months': bad_months,
        'summary': summary,
        'categories': categories,
        'yi_list': [categories[k]['yi'] for k in domains],
        'ji_list': [categories[k]['ji'] for k in domains],
    }

