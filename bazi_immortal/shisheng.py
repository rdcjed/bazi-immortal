"""
十神分析模块
根据日主和其他天干的关系，确定十神
"""

from typing import Dict, List, Tuple
from .constants import (
    TIAN_GAN, TG_WU_XING, TG_YIN_YANG,
    WU_XING_SHENG, WU_XING_KE,
)
from .calculator import BaZi, Pillar

# 十神完整列表
SHI_SHEN_LIST = ["正官", "七杀", "正印", "偏印", "正财", "偏财", "比肩", "劫财", "食神", "伤官"]

# 十神类别分组
SHI_SHEN_CATEGORIES = {
    "官杀": ["正官", "七杀"],
    "印枭": ["正印", "偏印"],
    "财": ["正财", "偏财"],
    "比劫": ["比肩", "劫财"],
    "食伤": ["食神", "伤官"],
}

# 十神吉凶（传统看法，仅供参考）
SHI_SHEN_JI_XIONG = {
    "正官": "吉", "七杀": "凶",
    "正印": "吉", "偏印": "凶",
    "正财": "吉", "偏财": "吉",
    "比肩": "平", "劫财": "凶",
    "食神": "吉", "伤官": "凶",
}


def get_shi_shen_for_gan(ri_gan: str, other_gan: str) -> str:
    """
    根据日干和其他天干，返回十神名称

    规则：
    - 同五行同阴阳 = 比肩
    - 同五行异阴阳 = 劫财
    - 生我（同阴阳）= 正印
    - 生我（异阴阳）= 偏印
    - 我生（同阴阳）= 食神
    - 我生（异阴阳）= 伤官
    - 克我（同阴阳）= 正官
    - 克我（异阴阳）= 七杀
    - 我克（同阴阳）= 正财
    - 我克（异阴阳）= 偏财
    """
    if ri_gan == other_gan:
        return "比肩"

    ri_wx = TG_WU_XING[ri_gan]
    other_wx = TG_WU_XING[other_gan]
    ri_yin_yang = TG_YIN_YANG[ri_gan]
    other_yin_yang = TG_YIN_YANG[other_gan]
    same_yy = (ri_yin_yang == other_yin_yang)

    # ⚠ 先检查同五行不同天干（比肩/劫财），再检查生克
    if ri_wx == other_wx:
        return "比肩" if same_yy else "劫财"

    # 生我者为印枭
    if WU_XING_SHENG.get(other_wx) == ri_wx:
        return "正印" if not same_yy else "偏印"
    # 我生者为食伤
    if WU_XING_SHENG.get(ri_wx) == other_wx:
        return "食神" if same_yy else "伤官"
    # 克我者为官杀
    if WU_XING_KE.get(other_wx) == ri_wx:
        return "正官" if not same_yy else "七杀"
    # 我克者为财
    if WU_XING_KE.get(ri_wx) == other_wx:
        return "正财" if same_yy else "偏财"

    return "比肩"


def get_shi_shen_for_zhi(ri_gan: str, zhi: str) -> Dict[str, str]:
    """
    根据地支藏干确定十神（返回每个藏干的十神）

    如：日中 甲木，月支 辰 → 藏干戊乙癸 → 偏财/劫财/正印
    """
    from .constants import DZ_CANG_GAN
    result = {}
    hidden = DZ_CANG_GAN.get(zhi, [])
    for hg in hidden:
        result[hg] = get_shi_shen_for_gan(ri_gan, hg)
    return result


def analyze_all_shi_shen(bazi: BaZi) -> Dict:
    """
    完整的十神分析

    返回：
    - gan_shi_shen: 四个天干的十神列表
    - zhi_shi_shen: 四个地支藏干的十神列表
    - counts: 十神数量统计
    - category_counts: 类别统计（官杀/印枭/财/比劫/食伤）
    - summary: 文字总结
    """
    ri_gan = bazi.ri_gan
    pillars = bazi.si_zhu

    # 四个天干的十神
    gan_ss = []
    for p in pillars:
        ss = get_shi_shen_for_gan(ri_gan, p.tian_gan)
        gan_ss.append({"gan": p.tian_gan, "shi_shen": ss, "position": p.label})

    # 四个地支藏干的十神
    zhi_ss = []
    for p in pillars:
        dz_ss = get_shi_shen_for_zhi(ri_gan, p.di_zhi)
        zhi_ss.append({"zhi": p.di_zhi, "cang_gan_shi_shen": dz_ss, "position": p.label})

    # 统计十神数量
    counts = {ss: 0 for ss in SHI_SHEN_LIST}
    for item in gan_ss:
        if item["shi_shen"] in counts:
            counts[item["shi_shen"]] += 1
    for item in zhi_ss:
        # 差异化藏干权重：本气(第一个藏干)=0.7，余气(其余)=0.3
        from .constants import DZ_CANG_GAN
        zhi = item["zhi"]
        hidden_list = DZ_CANG_GAN.get(zhi, [])
        hidden_items = list(item["cang_gan_shi_shen"].items())
        for i, (cg, ss) in enumerate(hidden_items):
            if ss in counts:
                weight = 0.7 if i == 0 else 0.3  # 本气0.7，余气0.3
                counts[ss] += weight

    # 按类别统计
    category_counts = {}
    for cat, members in SHI_SHEN_CATEGORIES.items():
        total = sum(counts.get(m, 0) for m in members)
        category_counts[cat] = round(total, 1)

    # 特征总结
    features = []
    
    # 看最突出的十神
    sorted_ss = sorted(counts.items(), key=lambda x: -x[1])
    top_ss = [ss for ss, c in sorted_ss if c >= 1.5]
    if top_ss:
        features.append(f"十神特点：{', '.join(top_ss)}较为突出")

    # 看缺什么（补充说明：缺十神≠缺贵人）
    missing = [ss for ss, c in counts.items() if c == 0]
    if missing and len(missing) < 8:
        features.append(f"缺少：{'、'.join(missing)}")
    # 说明缺失的十神并不直接等同于对应的人事物——具体需结合八字综合分析

    # 类别分析
    for cat, total in category_counts.items():
        if total >= 3:
            features.append(f"{cat}旺：{total}个，影响较大")
        elif total == 0:
            features.append(f"无{cat}：四柱不见{cat}")

    summary = "；".join(features) if features else "十神分布较为均衡"

    return {
        "ri_gan": ri_gan,
        "gan_shi_shen": gan_ss,
        "zhi_shi_shen": zhi_ss,
        "counts": counts,
        "category_counts": category_counts,
        "summary": summary,
        "top_shi_shen": sorted_ss[:3],
    }


INTERPRETATIONS = {
    "正官": "正官代表贵气、纪律、事业。正官旺的人守规矩、有责任感，适合公职或稳定工作。",
    "七杀": "七杀代表魄力、竞争、压力。七杀旺的人果断有领导力，但易招是非和压力。",
    "正印": "正印代表学历、贵人、慈爱。正印旺的人学习好、人缘好、有长辈提携。",
    "偏印": "偏印代表特殊才能、偏门学问。偏印旺的人聪明有创意，但性格较孤僻。",
    "正财": "正财代表稳定收入、正职财运。正财旺的人踏实赚钱，适合稳定收入型工作。",
    "偏财": "偏财代表意外之财、投资收益。偏财旺的人适合做生意、投资，有横财运。",
    "比肩": "比肩代表自我、兄弟朋友。比肩旺的人独立自主，但也容易固执己见。",
    "劫财": "劫财代表竞争、破财。劫财旺的人易被朋友拖累，不适合合伙生意。",
    "食神": "食神代表才华、享受、福气。食神旺的人有才艺天赋，生活有品味。",
    "伤官": "伤官代表才华、叛逆、口舌。伤官旺的人聪明绝顶但容易得罪人。",
}


def get_shi_shen_interpretation(shi_shen: str) -> str:
    """获取十神的白话解释"""
    return INTERPRETATIONS.get(shi_shen, f"{shi_shen}未知")


def format_shi_shen_analysis(result: Dict) -> str:
    """十神分析 → 可读文本"""
    parts = []
    parts.append("【十神分析】")

    # 四柱十神表
    header = f"{'':>6} {'年柱':>8} {'月柱':>8} {'日柱':>8} {'时柱':>8}"
    parts.append(header)
    parts.append("-" * 40)

    gan_line = "天干"
    for item in result["gan_shi_shen"]:
        gan_line += f" {item['shi_shen']:>6}"
    parts.append(gan_line)

    parts.append("")
    
    # 用量统计
    counts = result["counts"]
    sorted_counts = sorted(counts.items(), key=lambda x: -x[1])
    count_str = "、".join(f"{ss}={c}" for ss, c in sorted_counts if c > 0)
    parts.append(f"十神分布：{count_str}")

    # 类别统计
    cat = result["category_counts"]
    cat_str = "、".join(f"{k}{v}" for k, v in cat.items() if v > 0)
    parts.append(f"类别统计：{cat_str}")

    # 特征
    parts.append(f"特征：{result['summary']}")

    # 每个十神的解释
    top = [ss for ss, _ in result["top_shi_shen"] if ss]
    for ss in top:
        if ss in INTERPRETATIONS:
            parts.append(f"· {ss}：{INTERPRETATIONS[ss]}")

    return "\n".join(parts)