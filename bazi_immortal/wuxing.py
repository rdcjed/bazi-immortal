"""
五行分析模块
分析八字中的五行分布、日主强弱、用神忌神
"""

from typing import Dict, List, Tuple, Optional
from .plain_terms import STRONG_WEAK_PLAIN
from .constants import (
    TIAN_GAN, DI_ZHI, TG_WU_XING, DZ_WU_XING, DZ_CANG_GAN,
    WU_XING_SHENG, WU_XING_KE, SI_JI_WANG_XIANG,
    DZ_MONTH_INFO, SHI_ER_CHANG_SHENG, SHI_ER_CHANG_SHENG_INDEX,
    SHI_ER_CHANG_SHENG_ORDER, DZ_INDEX,
    SAN_HE_BY_WU_XING, SAN_HUI_BY_WU_XING,
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


def _detect_san_he_hui(zhi_list: List[str]) -> Dict[str, float]:
    """
    检测地支三合/三会局，返回增强的五行及分值

    三合：申子辰→水，亥卯未→木，寅午戌→火，巳酉丑→金 → 对应五行+2
    三会：亥子丑→水，寅卯辰→木，巳午未→火，申酉戌→金 → 对应五行+2
    """
    zhi_set = set(zhi_list)
    bonuses: Dict[str, float] = {}

    # 检测三合
    for wx, trio in SAN_HE_BY_WU_XING.items():
        if set(trio).issubset(zhi_set):
            bonuses[wx] = bonuses.get(wx, 0) + 2.0

    # 检测三会
    for wx, trio in SAN_HUI_BY_WU_XING.items():
        if set(trio).issubset(zhi_set):
            bonuses[wx] = bonuses.get(wx, 0) + 2.0

    return bonuses


def analyze_wuxing_distribution(bazi: BaZi) -> Dict[str, float]:
    """
    五行分布统计

    统计四柱中：
    - 天干（明现）
    - 地支本气（力量最大）
    - 地支藏干（余气）
    - 三合/三会局加成
    
    权重规则：
    - 天干：+2
    - 地支本气：+1.5（传统算法地支权重稍大于天干即可）
    - 主藏干：+0.5
    - 余气：+0.2
    - 三合/三会局：+2（对应五行）
    
    返回 { "木": N, "火": N, "土": N, "金": N, "水": N }
    """
    counts = {wx: 0.0 for wx in WU_XING_LIST}

    # 统计天干
    for gan in bazi.gan_list:
        wx = TG_WU_XING[gan]
        counts[wx] += 2  # 天干权重为2

    # 统计地支本气 + 藏干
    for zhi in bazi.zhi_list:
        # 地支本气（主气）— 力量最大
        main_wx = DZ_WU_XING[zhi]
        counts[main_wx] += 1.5  # 本气权重1.5

        # 藏干余气
        hidden_gans = DZ_CANG_GAN.get(zhi, [])
        for i, hg in enumerate(hidden_gans):
            hg_wx = TG_WU_XING[hg]
            if i == 0:
                counts[hg_wx] += 0.5  # 主藏干
            else:
                counts[hg_wx] += 0.2  # 余气（轻权）

    # 三合/三会局检测
    san_bonuses = _detect_san_he_hui(bazi.zhi_list)
    for wx, bonus in san_bonuses.items():
        counts[wx] += bonus

    return {k: round(v, 2) for k, v in sorted(counts.items(), key=lambda x: -x[1])}


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
    # 四季旺衰：旺+2, 相+1, 休0, 囚-1, 死-2
    # 十二长生额外调整：临官/帝旺/长生+1, 绝/死-1
    de_ling_score = 0
    de_ling_reasons = []

    if ri_wx_season_status == "旺":
        de_ling_score += 2
        de_ling_reasons.append(f"四季旺衰：{ri_wx}在{season}季为【旺】，当令")
    elif ri_wx_season_status == "相":
        de_ling_score += 1
        de_ling_reasons.append(f"四季旺衰：{ri_wx}在{season}季为【相】，次旺")
    elif ri_wx_season_status == "休":
        de_ling_score += 0
        de_ling_reasons.append(f"四季旺衰：{ri_wx}在{season}季为【休】，退气减力")
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
            helping_count += 1  # 天干印比各+1（降低极端化）
        elif ss in ("正官", "七杀", "正财", "偏财", "食神", "伤官"):
            harming_count += 1  # 天干克泄耗各+1（降低极端化）

    # 也看地支藏干中的扶助（藏干力量轻）
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
        score += 1  # 强根+1
        root_str = "、".join(f"{r}({s})" for r, s in roots[:3])
        reasoning.append(f"得地：地支有强根（{root_str}）")
    elif is_de_di:
        score += 0.5  # 弱根+0.5
        root_str = "、".join(f"{r}" for r, _ in roots[:3])
        reasoning.append(f"得地：地支有根（{root_str}），但力量一般")
    else:
        score -= 1
        reasoning.append("失地：地支无根")

    if is_de_shi:
        score += 1
        reasoning.append(f"得势：天干印比助力较多（+{_fmt_val(helping_count)}），得势有力")
    else:
        score -= 1
        reasoning.append(f"失势：天干克泄耗较多（+{_fmt_val(harming_count)}），失势无助")

    # 最终判断
    if score >= 3:
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
    helping_raw = helping_count + (3 if has_strong_root else 0)
    if helping_raw >= 8 and harming_count <= 2 and is_de_shi:
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
        "plain_strong_weak": STRONG_WEAK_PLAIN.get(strong_weak, ""),
    }


def _fmt_val(v):
    """格式化数值：≥1.0显示一位小数，<1.0显示两位小数"""
    if v >= 1.0:
        return f"{v:.1f}"
    return f"{v:.2f}"


def format_wuxing_analysis(result: Dict) -> str:
    """五行分析结果 → 可读文本"""
    parts = []
    parts.append("【五行分析】")
    
    # 五行分布
    dist = result["distribution"]
    dist_str = "、".join(f"{wx}{_fmt_val(dist.get(wx, 0))}" for wx in WU_XING_LIST)
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


def analyze_ge_ju(bazi, strength, ss_data) -> Dict:
    """
    分析八字格局

    检测顺序：
    1. 从格（印比≥75%从强，官杀≥45%从官，财≥45%从财，食伤≥45%从儿）
    2. 化气格（日主与年/月/时干合化）
    3. 普通格（月令藏干透干定格局）

    Args:
        bazi: BaZi 排盘对象
        strength: analyze_ri_zuo_strong_weak() 的输出
        ss_data: 十神分析数据（analyze_all_shi_shen 的输出）

    Returns:
        Dict with name, category, description, confidence
    """
    from .shisheng import get_shi_shen_for_gan

    ri_gan = bazi.ri_gan
    ri_wx = TG_WU_XING[ri_gan]
    month_zhi = bazi.month_pillar.di_zhi
    month_gan = bazi.month_pillar.tian_gan
    gan_list = bazi.gan_list  # [年干, 月干, 日干, 时干]
    zhi_list = bazi.zhi_list

    category_counts = ss_data.get("category_counts", {})
    total_count = sum(category_counts.values()) or 1.0

    yin_bi = category_counts.get("印枭", 0) + category_counts.get("比劫", 0)
    guan_sha = category_counts.get("官杀", 0)
    cai = category_counts.get("财", 0)
    shi_shang = category_counts.get("食伤", 0)

    yin_bi_pct = yin_bi / total_count * 100
    guan_sha_pct = guan_sha / total_count * 100
    cai_pct = cai / total_count * 100
    shi_shang_pct = shi_shang / total_count * 100

    # ═══════════════════════════════════════════════════
    # 1. 从格检测
    # ═══════════════════════════════════════════════════
    # 从强格 / 假从强格：印比 ≥ 75%
    if yin_bi_pct >= 75:
        is_real = yin_bi_pct >= 85 and strength.get("strong_weak") in ("从强", "身强")
        confidence = "high" if is_real else "mid"
        name = "从强格" if is_real else "假从强格"
        return {
            "name": name,
            "category": "从格",
            "description": f"全局印比占比{yin_bi_pct:.0f}%，日主极强，顺其旺势。{name}。",
            "confidence": confidence,
        }

    # 从官格：官杀 ≥ 45%
    if guan_sha_pct >= 45:
        confidence = "high" if guan_sha_pct >= 60 else "mid"
        return {
            "name": "从官格",
            "category": "从格",
            "description": f"全局官杀占比{guan_sha_pct:.0f}%，日主极弱从官杀之势。",
            "confidence": confidence,
        }

    # 从财格：财 ≥ 45%
    if cai_pct >= 45:
        confidence = "high" if cai_pct >= 60 else "mid"
        return {
            "name": "从财格",
            "category": "从格",
            "description": f"全局财星占比{cai_pct:.0f}%，日主极弱从财之势。",
            "confidence": confidence,
        }

    # 从儿格：食伤 ≥ 45%
    if shi_shang_pct >= 45:
        confidence = "high" if shi_shang_pct >= 60 else "mid"
        return {
            "name": "从儿格",
            "category": "从格",
            "description": f"全局食伤占比{shi_shang_pct:.0f}%，日主极弱从儿之势。",
            "confidence": confidence,
        }

    # ═══════════════════════════════════════════════════
    # 2. 化气格检测（日主与年/月/时干合化）
    # ═══════════════════════════════════════════════════
    # 合化组合：甲己→土, 乙庚→金, 丙辛→水, 丁壬→木, 戊癸→火
    # 需要月令辅助（合化后五行当令）
    hua_qi_pairs = {
        ("甲", "己"): ("土", ["辰", "戌", "丑", "未"]),
        ("己", "甲"): ("土", ["辰", "戌", "丑", "未"]),
        ("乙", "庚"): ("金", ["申", "酉"]),
        ("庚", "乙"): ("金", ["申", "酉"]),
        ("丙", "辛"): ("水", ["亥", "子"]),
        ("辛", "丙"): ("水", ["亥", "子"]),
        ("丁", "壬"): ("木", ["寅", "卯"]),
        ("壬", "丁"): ("木", ["寅", "卯"]),
        ("戊", "癸"): ("火", ["巳", "午"]),
        ("癸", "戊"): ("火", ["巳", "午"]),
    }

    # 检查所有配对组合
    # 日主 + 年干 / 月干 / 时干
    # 月干 + 时干 / 年干 + 日干
    check_pairs = [
        (ri_gan, bazi.year_pillar.tian_gan),
        (ri_gan, month_gan),
        (ri_gan, bazi.hour_pillar.tian_gan),
        (month_gan, bazi.hour_pillar.tian_gan),
        (bazi.year_pillar.tian_gan, ri_gan),
    ]

    for g1, g2 in check_pairs:
        key = (g1, g2)
        if key in hua_qi_pairs:
            hua_wx, need_zhi = hua_qi_pairs[key]
            if month_zhi in need_zhi:
                return {
                    "name": f"{g1}{g2}化气格（{hua_wx}）",
                    "category": "化气格",
                    "description": f"日主{ri_gan}与{g2}合化成功，化气为{hua_wx}，月令{month_zhi}助化。",
                    "confidence": "mid",
                }

    # ═══════════════════════════════════════════════════
    # 3. 普通格（月令藏干透干定格局）
    # ═══════════════════════════════════════════════════
    # 优先级：官杀 > 财 > 食伤 > 印 > 比劫
    priority_ss = ["正官", "七杀", "正财", "偏财", "食神", "伤官", "正印", "偏印"]
    # 比劫（建禄/月刃）最后处理

    month_cang_gan = DZ_CANG_GAN.get(month_zhi, [])

    # 检查月令藏干中有哪些透出在天干上
    found_ss = None
    found_gan = None

    for cg in month_cang_gan:
        if cg in gan_list:
            ss = get_shi_shen_for_gan(ri_gan, cg)
            if ss in priority_ss:
                if found_ss is None or priority_ss.index(ss) < priority_ss.index(found_ss):
                    found_ss = ss
                    found_gan = cg

    if found_ss:
        name = found_ss + "格"
        return {
            "name": name,
            "category": "普通格",
            "description": f"月令{month_zhi}中{found_gan}透出天干，定为{name}。",
            "confidence": "high",
        }

    # 如果月令藏干没有透出任何官杀财印食伤，检查比劫（建禄格/月刃格）
    monthly_state = get_monthly_state(ri_gan, month_zhi)
    if monthly_state == "临官":
        return {
            "name": "建禄格",
            "category": "普通格",
            "description": f"日主{ri_gan}在月令{month_zhi}为临官（建禄），月令得禄。",
            "confidence": "high",
        }
    if monthly_state == "帝旺":
        return {
            "name": "月刃格",
            "category": "普通格",
            "description": f"日主{ri_gan}在月令{month_zhi}为帝旺（月刃），月令刃旺。",
            "confidence": "high",
        }

    # 兜底
    return {
        "name": "正格（无特殊格局）",
        "category": "普通格",
        "description": f"日主{ri_gan}无特殊从格或化气，月令{month_zhi}藏干未透，归入正格。",
        "confidence": "low",
    }