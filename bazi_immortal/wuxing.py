"""
五行分析模块
分析八字中的五行分布、日主强弱、用神忌神
"""

from typing import Dict, List, Tuple, Optional
from .constants import (
    TIAN_GAN, DI_ZHI, TG_WU_XING, DZ_WU_XING, DZ_CANG_GAN,
    WU_XING_SHENG, WU_XING_KE, SI_JI_WANG_XIANG,
    DZ_MONTH_INFO, SHI_ER_CHANG_SHENG, SHI_ER_CHANG_SHENG_INDEX,
    SHI_ER_CHANG_SHENG_ORDER, DZ_INDEX,
)
from .calculator import BaZi

WU_XING_LIST = ["木", "火", "土", "金", "水"]
WU_XING_COLORS = {
    "木": "绿色/青色",
    "火": "红色/紫色",
    "土": "黄色/棕色",
    "金": "白色/银色",
    "水": "黑色/蓝色",
}
WU_XING_DIRECTIONS = {
    "木": "东方",
    "火": "南方",
    "土": "中央",
    "金": "西方",
    "水": "北方",
}
WU_XING_ORGANS = {
    "木": "肝/胆",
    "火": "心/小肠",
    "土": "脾/胃",
    "金": "肺/大肠",
    "水": "肾/膀胱",
}
WU_XING_SEASONS = {
    "木": "春", "火": "夏", "土": "季末", "金": "秋", "水": "冬",
}


def analyze_wuxing_distribution(bazi: BaZi) -> Dict[str, int]:
    """
    五行分布统计

    统计四柱中：
    - 天干（明现，权重高）
    - 地支本气
    - 地支藏干（余气）
    
    返回 { "木": N, "火": N, "土": N, "金": N, "水": N }
    """
    counts = {wx: 0 for wx in WU_XING_LIST}

    # 统计天干
    for gan in bazi.gan_list:
        wx = TG_WU_XING[gan]
        counts[wx] += 2  # 天干权重为2

    # 统计地支本气 + 藏干
    for zhi in bazi.zhi_list:
        # 地支本气（主气）
        main_wx = DZ_WU_XING[zhi]
        counts[main_wx] += 1.5  # 本气权重1.5

        # 藏干余气
        hidden_gans = DZ_CANG_GAN.get(zhi, [])
        for i, hg in enumerate(hidden_gans):
            hg_wx = TG_WU_XING[hg]
            if i == 0:
                counts[hg_wx] += 1.0  # 主藏干
            else:
                counts[hg_wx] += 0.5  # 余气

    return {k: round(v, 1) for k, v in sorted(counts.items(), key=lambda x: -x[1])}


def get_season(bazi: BaZi) -> str:
    """
    根据月柱确定季节

    春：寅卯月
    夏：巳午月
    秋：申酉月
    冬：亥子月
    季末：辰戌丑未月
    """
    month_zhi = bazi.month_pillar.di_zhi
    season_map = {
        "寅": "春", "卯": "春",
        "巳": "夏", "午": "夏",
        "申": "秋", "酉": "秋",
        "亥": "冬", "子": "冬",
        "辰": "季末", "戌": "季末", "丑": "季末", "未": "季末",
    }
    return season_map.get(month_zhi, "春")


def get_monthly_state(ri_gan: str, month_zhi: str) -> str:
    """
    日主在月令的十二长生状态

    如甲木在寅月 = 临官（建禄）
    甲木在申月 = 绝
    """
    if ri_gan in SHI_ER_CHANG_SHENG and month_zhi in SHI_ER_CHANG_SHENG[ri_gan]:
        return SHI_ER_CHANG_SHENG[ri_gan][month_zhi]
    return "?不明?"


def get_roots_in_branches(ri_gan: str, zhi_list: List[str]) -> List[Tuple[str, str]]:
    """
    日主在地支中是否有根（同五行的地支）

    返回 [(地支, 状态)] 列表
    如甲木有寅（临官）或卯（帝旺）就是有强根
    """
    ri_wx = TG_WU_XING[ri_gan]
    roots = []
    
    for zhi in zhi_list:
        # 地支本气是否相同五行
        if DZ_WU_XING[zhi] == ri_wx:
            state = SHI_ER_CHANG_SHENG.get(ri_gan, {}).get(zhi, "?")
            roots.append((zhi, state))
        # 藏干是否有同五行
        hidden = DZ_CANG_GAN.get(zhi, [])
        for hg in hidden:
            if TG_WU_XING[hg] == ri_wx:
                state = SHI_ER_CHANG_SHENG.get(ri_gan, {}).get(zhi, "?")
                roots.append((zhi, f"藏{state}"))
                break

    return roots


def analyze_ri_zuo_strong_weak(bazi: BaZi) -> Dict:
    """
    综合判断日主强弱 + 用神忌神

    判断维度：
    1. 得令（月令状态）：长生~帝旺为得令，衰~绝为失令
    2. 得地（地支有根）：有同五行地支为得地，有多个为得地强
    3. 得势（天干扶助）：印比多（同五行或生扶五行的天干多）为得势

    综合：
    - 得令+得地/得势 → 身强
    - 失令+失地/失势 → 身弱
    - 极强（全局都是同五行/印比）→ 从强
    - 极弱（全局都是克泄耗）→ 从弱
    """
    ri_gan = bazi.ri_gan
    ri_wx = TG_WU_XING[ri_gan]
    month_zhi = bazi.month_pillar.di_zhi
    zhi_list = bazi.zhi_list
    gan_list = bazi.gan_list

    # 1. 得令分析 — 结合四季旺衰 + 十二长生
    monthly_state = get_monthly_state(ri_gan, month_zhi)
    season = get_season(bazi)
    season_wangxiang = SI_JI_WANG_XIANG[season]  # e.g. {"木":"旺","火":"相","水":"休","金":"囚","土":"死"}
    ri_wx_season_status = season_wangxiang[ri_wx]  # 日主五行在当季的旺衰状态

    # 十二长生强弱状态
    strong_life_states = {"临官", "帝旺", "长生"}
    weak_life_states = {"绝", "死", "墓", "病"}
    moderate_life_states = {"沐浴", "冠带", "衰", "胎", "养"}

    # 综合得分规则：
    # 四季旺衰：旺+3, 相+2, 休+0, 囚-1, 死-2
    # 十二长生额外调整：临官/帝旺/长生+1, 绝/死-1
    de_ling_score = 0
    de_ling_reasons = []

    if ri_wx_season_status == "旺":
        de_ling_score += 3
        de_ling_reasons.append(f"四季旺衰：{ri_wx}在{season}季为【旺】，当令")
    elif ri_wx_season_status == "相":
        de_ling_score += 2
        de_ling_reasons.append(f"四季旺衰：{ri_wx}在{season}季为【相】，次旺")
    elif ri_wx_season_status == "休":
        de_ling_reasons.append(f"四季旺衰：{ri_wx}在{season}季为【休】，退气")
    elif ri_wx_season_status == "囚":
        de_ling_score -= 1
        de_ling_reasons.append(f"四季旺衰：{ri_wx}在{season}季为【囚】，不得令")
    elif ri_wx_season_status == "死":
        de_ling_score -= 2
        de_ling_reasons.append(f"四季旺衰：{ri_wx}在{season}季为【死】，失令")

    # 十二长生额外调整
    if monthly_state in strong_life_states:
        de_ling_score += 1
        de_ling_reasons.append(f"长生状态：{ri_gan}在{month_zhi}月为【{monthly_state}】，加旺")
    elif monthly_state in weak_life_states:
        de_ling_score -= 1
        de_ling_reasons.append(f"长生状态：{ri_gan}在{month_zhi}月为【{monthly_state}】，减力")

    is_de_ling = de_ling_score >= 2  # 综合≥2算得令
    is_shi_ling = de_ling_score <= -2  # 综合≤-2算失令

    # 2. 得地分析
    roots = get_roots_in_branches(ri_gan, zhi_list)
    is_de_di = len(roots) > 0
    strong_root_states = {"临官", "帝旺", "长生"}
    has_strong_root = any(
        any(s in str(state) for s in strong_root_states) 
        for _, state in roots
    )

    # 3. 得势分析 - 统计扶助日主的天干（正印/偏印/比肩/劫财 = 印比）
    from .shisheng import get_shi_shen_for_gan
    helping_count = 0
    harming_count = 0
    for gan in gan_list:
        if gan == ri_gan:
            continue
        ss = get_shi_shen_for_gan(ri_gan, gan)
        if ss in ("正印", "偏印", "比肩", "劫财"):
            helping_count += 2
        elif ss in ("正官", "七杀", "正财", "偏财", "食神", "伤官"):
            harming_count += 2

    # 也看地支藏干中的扶助
    for zhi in zhi_list:
        hidden = DZ_CANG_GAN.get(zhi, [])
        for hg in hidden:
            if TG_WU_XING[hg] == ri_wx or WU_XING_SHENG.get(hg) == ri_wx:
                helping_count += 0.5
    
    is_de_shi = helping_count > harming_count

    # 4. 综合判断
    score = 0
    reasoning = []

    # 得令得分（精细版）
    score += de_ling_score
    for r in de_ling_reasons:
        reasoning.append(r)

    if has_strong_root:
        score += 2
        root_str = "、".join(f"{r}({s})" for r, s in roots[:3])
        reasoning.append(f"得地：地支有强根（{root_str}）")
    elif is_de_di:
        score += 1
        root_str = "、".join(f"{r}" for r, _ in roots[:3])
        reasoning.append(f"得地：地支有根（{root_str}），但力量一般")
    else:
        score -= 1
        reasoning.append("失地：地支无根")

    if is_de_shi:
        score += 1
        reasoning.append(f"得势：天干印比助力较多（+{helping_count}），得势有力")
    else:
        score -= 1
        reasoning.append(f"失势：天干克泄耗较多（+{harming_count}），失势无助")

    # 最终判断
    if score >= 4:
        strong_weak = "身强"
    elif score <= -3:
        strong_weak = "身弱"
    elif score >= 1:
        strong_weak = "偏强"
    elif score <= -1:
        strong_weak = "偏弱"
    else:
        strong_weak = "中和"

    # 极强/极弱检查
    helping_all = helping_count + (3 if is_de_ling else 0) + (3 if has_strong_root else 0)
    if helping_all >= 10 and is_de_shi:
        strong_weak = "从强"
    if harming_count >= 8 and not is_de_ling and not is_de_di:
        strong_weak = "从弱"

    # 辅助：找"生我"的五行（印枭）
    def find_sheng_wo(wx):
        for k, v in WU_XING_SHENG.items():
            if v == wx:
                return k
        return None

    # 找"克我"的五行（官杀）：反向映射 WU_XING_KE
    # WU_XING_KE = {木:土, 土:水, 水:火, 火:金, 金:木}
    # → {土:木, 水:土, 火:水, 金:火, 木:金}
    WU_XING_BEING_KE = {v: k for k, v in WU_XING_KE.items()}
    ke_wo = WU_XING_BEING_KE[ri_wx]  # 克我者（官杀）
    sheng_wo = find_sheng_wo(ri_wx)  # 生我者（印枭）

    if strong_weak in ("身强", "偏强"):
        # 身强 → 用克泄耗（官杀/食伤/财），忌生扶（印比）
        useful_god = [ke_wo, WU_XING_SHENG[ri_wx], WU_XING_KE[ri_wx]]
        avoid_god = [ri_wx, sheng_wo] if sheng_wo else [ri_wx]
    elif strong_weak == "从强":
        # 从强 → 全局都是同党，反而喜生扶
        useful_god = [ri_wx, sheng_wo] if sheng_wo else [ri_wx]
        avoid_god = [ke_wo, WU_XING_KE[ri_wx]]
    elif strong_weak in ("身弱", "偏弱"):
        # 身弱 → 用印比（生扶）
        useful_god = [ri_wx]
        if sheng_wo:
            useful_god.append(sheng_wo)
        avoid_god = [ke_wo]
        # 克我的、我生的、我克的均为忌神
        if WU_XING_SHENG[ri_wx]:
            avoid_god.append(WU_XING_SHENG[ri_wx])
        if WU_XING_KE[ri_wx]:
            avoid_god.append(WU_XING_KE[ri_wx])
    elif strong_weak == "从弱":
        # 从弱 → 全局都是克泄耗，喜克泄耗
        useful_god = [ke_wo, WU_XING_SHENG[ri_wx], WU_XING_KE[ri_wx]]
        avoid_god = [ri_wx, sheng_wo] if sheng_wo else [ri_wx]
    else:
        # 中和 → 看组合，通常补自身
        useful_god = [ri_wx]
        avoid_god = [ke_wo]

    # 去重
    useful_god = list(dict.fromkeys([g for g in useful_god if g]))
    avoid_god = list(dict.fromkeys([g for g in avoid_god if g]))

    # 6. 五行分布
    distribution = analyze_wuxing_distribution(bazi)

    return {
        "ri_gan": ri_gan,
        "ri_wx": ri_wx,
        "monthly_state": monthly_state,
        "season": season,
        "de_ling_score": de_ling_score,
        "distribution": distribution,
        "strong_weak": strong_weak,
        "score": score,
        "reasoning": reasoning,
        "useful_god": useful_god,
        "avoid_god": avoid_god,
        "roots": roots,
        "helping_count": helping_count,
        "harming_count": harming_count,
    }


def format_wuxing_analysis(result: Dict) -> str:
    """五行分析结果 → 可读文本"""
    parts = []
    parts.append("【五行分析】")
    
    # 五行分布
    dist = result["distribution"]
    dist_str = "、".join(f"{wx}{dist.get(wx, 0)}" for wx in WU_XING_LIST)
    parts.append(f"五行分布：{dist_str}")
    
    # 日主
    parts.append(f"日主：{result['ri_gan']}（{result['ri_wx']}），月令状态：{result['monthly_state']}，季节：{result.get('season', '?')}")
    
    # 强弱
    parts.append(f"综合判定：{result['strong_weak']}（得分{result['score']}）")
    for r in result["reasoning"]:
        parts.append(f"  · {r}")
    
    # 用神忌神
    ug = "、".join(result["useful_god"])
    ag = "、".join(result["avoid_god"])
    parts.append(f"用神：{ug}")
    parts.append(f"忌神：{ag}")
    
    return "\n".join(parts)