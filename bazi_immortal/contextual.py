"""
十神综合分析 — 分情况、多维度推理
"""

from typing import Dict, List, Tuple, Optional

from .constants import (
    TIAN_GAN, DI_ZHI, TG_INDEX, DZ_INDEX,
    TG_WU_XING, DZ_WU_XING, DZ_CANG_GAN,
    WU_XING_SHENG, WU_XING_KE,
    TG_YIN_YANG,
)
from .plain_terms import (
    SHI_SHEN_PLAIN, SHI_SHEN_CATEGORY_PLAIN,
    STRONG_WEAK_PLAIN, WU_XING_PLAIN, WU_XING_HEALTH,
    PILLAR_PLAIN, SHENG_KE_PLAIN,
    wrap_ss, wrap_sw, wrap_wx, explain_ss, explain_sw,
)

def _fmt_val(v):
    """格式化数值：≥1.0显示一位小数，<1.0显示两位小数"""
    if v >= 1.0:
        return f"{v:.1f}"
    return f"{v:.2f}"


def analyze_shi_shen_features(ri_gan, ss_result, wx_result):
    """
    分情况分析十神特征，避免片面结论
    降低阈值、增加中等和极弱分支、每条分析用通俗语言表述

    返回: [(feature_text, confidence), ...]
    """
    features = []
    category = ss_result["category_counts"]
    useful_god = wx_result["useful_god"]
    strong_weak = wx_result["strong_weak"]

    guan = category.get("官杀", 0)
    yin = category.get("印枭", 0)
    cai = category.get("财", 0)
    shi = category.get("食伤", 0)
    bi = category.get("比劫", 0)

    # 五行关系
    ri_wx = wx_result["ri_wx"]
    from .wuxing import WU_XING_KE, WU_XING_SHENG
    cai_wx = WU_XING_KE.get(ri_wx)
    shi_wx = WU_XING_SHENG.get(ri_wx)
    guan_wx = next((k for k, v in WU_XING_KE.items() if v == ri_wx), None)
    yin_wx = next((k for k, v in WU_XING_SHENG.items() if v == ri_wx), None)

    # ════════════════════════════════════
    # 官杀分析 — 3分支（旺≥1.0 / 中等0.2~1.0 / 极弱<0.2）
    # ════════════════════════════════════
    if guan >= 1.0:
        is_useful = guan_wx and guan_wx in useful_god
        if is_useful:
            features.append((f"✅ 官杀（掌控管束之力：事业地位/权力责任）旺（{_fmt_val(guan)}）为用神→事业磁场强，能掌权，适合管理或从政。你天生有领导潜质，管人管事有一套，气场能镇住场子", "high"))
        else:
            sub = []
            if shi >= 1.0:
                sub.append("有食伤制杀（以才华化解压力）")
            if yin >= 1.0:
                sub.append("有印星化杀（以学识转化压力）")
            if cai >= 0.8:
                sub.append("有财星生官（财富带动地位）")
            if not sub:
                sub.append("官杀无制，需主动调节压力")
            features.append((f"⚠ 官杀（掌控管束之力）旺（{_fmt_val(guan)}）为忌神→生活中管束你的人或事不少，压力是有的。不过你同时有{sub[0]}，不是硬扛的那种，抗压能力其实不错", "high"))
    elif guan >= 0.2:
        features.append((f"🔸 官杀（掌控管束之力）中等（{_fmt_val(guan)}）→有上进心但不算特别强，能平衡工作和生活。你管得好自己分内的事，日子过得平稳踏实", "medium"))
    else:
        features.append((f"💡 官杀（掌控管束之力）极弱（{_fmt_val(guan)}）→官杀几乎不显，你受不了被人管着，喜欢自己做主，适合自由职业或创业当老板", "medium"))

    # ════════════════════════════════════
    # 印枭分析 — 3分支（旺≥1.0 / 中等0.2~1.0 / 极弱<0.2）
    # ════════════════════════════════════
    if yin >= 1.0:
        is_useful = yin_wx and yin_wx in useful_god
        if is_useful:
            features.append((f"✅ 印星（庇护学习之力：贵人/学历/长辈）旺（{_fmt_val(yin)}）为用神→学习力强，学术运和长辈贵人运都很好。你读书厉害，总有长辈愿意帮你提携你", "high"))
        else:
            if strong_weak in ("身强", "偏强", "从强"):
                features.append((f"⚠ 印星（庇护学习之力）旺（{_fmt_val(yin)}）但为忌神→依赖心偏重，需要增强独立性。有人帮你是好事，但太依赖了反而会阻碍你成长", "high"))
            else:
                features.append((f"⚠ 印星偏旺（{_fmt_val(yin)}）但非用神→有长辈缘，但助力不一定能落到实处，得看具体组合。身边有人想帮你，但帮不帮得到点子上要看情况", "medium"))
    elif yin >= 0.2:
        has_guan = guan >= 1.0
        has_shi = shi >= 1.0
        if has_guan:
            features.append((f"🔸 印星中等（{_fmt_val(yin)}）但有官杀旺→学术型的贵人虽然不多，但职场上总有领导赏识你、提携你", "high"))
        elif has_shi:
            features.append((f"🔸 印星中等（{_fmt_val(yin)}）但有食伤旺→你完全靠自己本事吃饭，不需要仰仗别人提携，用才华开路就够了", "high"))
        else:
            features.append((f"🔸 印星（庇护学习之力）中等（{_fmt_val(yin)}）→师长和学术方面的助力不多不少，身边偶尔有人指点，但主要还得靠自己钻研", "medium"))
    else:
        has_guan = guan >= 1.0
        has_shi = shi >= 1.0
        if has_guan:
            features.append((f"💡 无印星但有官杀旺→学术和长辈缘几乎为零，读书时基本没人指点，全靠工作中遇到贵人", "medium"))
        elif has_shi:
            features.append((f"💡 无印星但有食伤旺→从小到大就靠自己，从不指望别人，全靠自己的才华打天下", "medium"))
        else:
            features.append((f"💡 印星极弱（{_fmt_val(yin)}）→师长辈的助力非常少，身边几乎没有能帮你的人，什么事都得自己扛", "medium"))

    # ════════════════════════════════════
    # 比劫分析 — 3分支（旺≥1.5 / 中等0.2~1.5 / 极弱<0.2）
    # ════════════════════════════════════
    if bi >= 1.5:
        is_useful = ri_wx in useful_god
        if is_useful:
            features.append((f"✅ 比劫（同辈互动之力：社交/合作/朋友）旺（{_fmt_val(bi)}）为用神→你人缘好，身边愿意帮你的人多，团队合作运强", "high"))
        else:
            features.append((f"⚠ 比劫（同辈互动之力）旺（{_fmt_val(bi)}）为忌神→朋友虽然多但不一定都是好事，容易有财务纠纷，合伙一定要谨慎，涉及钱的事要格外小心", "high"))
    elif bi >= 0.2:
        features.append((f"🔸 比劫（同辈互动之力）中等（{_fmt_val(bi)}）→朋友关系适中，不靠朋友吃饭也不缺朋友，有几个知心朋友就够了，不需要一大帮人围着", "medium"))
    else:
        features.append((f"💡 比劫（同辈互动之力）极弱（{_fmt_val(bi)}）→不太依赖朋友，性格偏独立独行。你是个独行侠，一个人反而效率更高", "medium"))

    # ════════════════════════════════════
    # 食伤分析 — 3分支（旺≥1.0 / 中等0.2~1.0 / 极弱<0.2）
    # ════════════════════════════════════
    if shi >= 1.0:
        is_useful = shi_wx and shi_wx in useful_god
        if is_useful:
            features.append((f"✅ 食伤（才华输出之力：创意/技能/表达）旺（{_fmt_val(shi)}）为用神→你有一技之长，靠本事就能赚钱，适合创意、技术或自由职业", "high"))
        else:
            features.append((f"⚠ 食伤（才华输出之力）旺（{_fmt_val(shi)}）为忌神→想法特别多但执行起来有难度，主意太多落地难，需要有人帮你聚焦", "high"))
    elif shi >= 0.2:
        features.append((f"🔸 食伤（才华输出之力）中等（{_fmt_val(shi)}）→有点小才华，关键时刻能露一手，但不是靠它吃饭的，更多是锦上添花", "medium"))
    else:
        features.append((f"💡 食伤（才华输出之力）极弱（{_fmt_val(shi)}）→务实型人格，不喜张扬。你是个实干家，不喜欢花里胡哨的东西，稳扎稳打是你的风格", "medium"))

    # ════════════════════════════════════
    # 财星分析 — 3分支（旺≥0.8 / 中等0.2~0.8 / 极弱<0.2）
    # ════════════════════════════════════
    if cai >= 0.8:
        is_useful = cai_wx and cai_wx in useful_god
        if is_useful:
            features.append((f"✅ 财星（物质财富之力：收入/理财/资源）旺（{_fmt_val(cai)}）为用神→你有赚钱的手气，会管钱会理财，适合经商", "high"))
        else:
            features.append((f"⚠ 财星（物质财富之力）旺（{_fmt_val(cai)}）为忌神→赚得多花得也多，钱像流水一样抓不住，需要有比劫来护住钱财", "high"))
    elif cai >= 0.2:
        features.append((f"🔸 财星（物质财富之力）中等（{_fmt_val(cai)}）→你的财运说不上多好但也够花，赚钱欲望适中，收入稳定，日子过得去", "medium"))
    else:
        features.append((f"💡 财星（物质财富之力）极弱（{_fmt_val(cai)}）→对钱不太敏感，不追求物质生活。你对钱没有太大概念，够用就行，更在乎开不开心", "medium"))

    # ════════════════════════════════════
    # 综合五行总结 — 日主五行强弱感受
    # ════════════════════════════════════
    wx_dist = wx_result.get("distribution", {})
    ri_wx_score = wx_dist.get(ri_wx, 0)
    wx_sorted = sorted(wx_dist.items(), key=lambda x: -x[1])

    if ri_wx_score >= 3.0:
        wx_feeling = f"日主五行【{ri_wx}】在全盘中力量很强（{_fmt_val(ri_wx_score)}），你天生精力旺盛，有主见，不容易被外界影响"
    elif ri_wx_score >= 1.5:
        wx_feeling = f"日主五行【{ri_wx}】在全盘中力量中等偏上（{_fmt_val(ri_wx_score)}），你内在能量还不错，有自己的想法但也会听别人意见"
    elif ri_wx_score >= 0.5:
        wx_feeling = f"日主五行【{ri_wx}】在全盘中力量中等（{_fmt_val(ri_wx_score)}），能量均衡，没有什么特别强的气场，但胜在随和、适应力强"
    else:
        wx_feeling = f"日主五行【{ri_wx}】在全盘中力量偏弱（{_fmt_val(ri_wx_score)}），可能比较容易受别人影响，需要多给自己打气，增强自信心"

    features.append((f"📊 {wx_feeling}", "medium"))

    if len(wx_sorted) >= 2:
        most_wx = wx_sorted[0]
        least_wx = wx_sorted[-1]
        if most_wx[1] >= 4.0 and least_wx[1] <= 1.0:
            features.append((f"⚠ 五行中【{most_wx[0]}】最旺（{_fmt_val(most_wx[1])}）、【{least_wx[0]}】最弱（{_fmt_val(least_wx[1])}），命局五行偏枯较明显，需要刻意补短板。某个能量特别强、某个特别弱，容易在某些方面很强、在某些方面很吃亏", "high"))

    return features


def get_guiren_analysis(shensha_data):
    """
    综合所有贵人星分析（十神贵人+神煞贵人）
    支持 shensha 模块返回的 {神煞名: {zhi, positions, meaning}} 格式
    返回: (summary, detail_list)
    """
    guiren_list = []
    
    # 贵人星关键词
    guiren_keywords = ["天乙贵人", "天德", "月德", "福星贵人", "文昌贵人", "国印贵人"]
    
    # 遍历神煞数据
    for shen_name, shen_info in shensha_data.items():
        if shen_name in guiren_keywords:
            if isinstance(shen_info, dict):
                desc = shen_info.get('meaning', '')
                positions = shen_info.get('positions', [])
                pos_str = "在" + "、".join(positions) if positions else ""
                guiren_list.append({
                    "name": shen_name,
                    "desc": desc,
                    "positions": pos_str,
                })
    
    # 分类统计
    has_tianyi = any(g["name"] == "天乙贵人" for g in guiren_list)
    has_yuede = any(g["name"] == "月德" for g in guiren_list)
    has_tiande = any(g["name"] == "天德" for g in guiren_list)
    has_fuxing = any(g["name"] == "福星贵人" for g in guiren_list)
    has_wenchang = any(g["name"] == "文昌贵人" for g in guiren_list)
    has_guoyin = any(g["name"] == "国印贵人" for g in guiren_list)
    
    # 综合强度评分
    strength = 0
    if has_tianyi: strength += 4
    if has_yuede: strength += 3
    if has_tiande: strength += 3
    if has_fuxing: strength += 2
    if has_wenchang: strength += 2
    if has_guoyin: strength += 2
    
    if strength >= 6:
        level = "很强"
        summary = "命带天乙/月德/天德等强力贵人星，一生贵人运极佳，逢凶化吉，关键时刻总有贵人相助"
    elif strength >= 3:
        level = "较强"
        summary = "命带月德/文昌等贵人星，常有意外之助，关键时刻易得人帮"
    elif strength >= 1:
        level = "一般"
        summary = "贵人运一般偏稳，但结合十神中的官杀/印星贵人，仍有助力"
    else:
        level = "偏弱"
        summary = "神煞贵人较少，更多靠自身实力和十神官杀/财星带来的贵人"
    
    return {
        "level": level,
        "summary": summary,
        "guiren_list": guiren_list,
    }


def analyze_pillars(bazi, strength_analysis, ss_data, yongshen_info):
    """
    逐柱分析：分别评估年、月、日、时四柱的好坏及含义
    Returns: [{pillar, gan_zhi, tiangan, dizhi, shishen, rating, analysis}, ...]
    """
    from .shisheng import get_shi_shen_for_gan

    ri_gan = bazi.ri_gan
    ri_wx = TG_WU_XING[ri_gan]
    useful_god = yongshen_info.get("useful_god", [])
    strong_weak = yongshen_info.get("strong_weak", "中和")
    season = strength_analysis.get("season", "")
    monthly_state = strength_analysis.get("monthly_state", "")

    pillar_info = {
        "年柱": {"name": "年柱", "meaning": "祖业/家庭出身/童年/长辈"},
        "月柱": {"name": "月柱", "meaning": "父母兄弟/青年运势/事业根基/季节"},
        "日柱": {"name": "日柱", "meaning": "自身/配偶/婚姻/中年运势"},
        "时柱": {"name": "时柱", "meaning": "子女/下属/晚年归宿/事业收尾"},
    }

    results = []

    for pillar in bazi.si_zhu:
        label = pillar.label
        gan = pillar.tian_gan
        zhi = pillar.di_zhi
        info = pillar_info.get(label, {"name": label, "meaning": ""})

        # 天干十神
        gan_ss = get_shi_shen_for_gan(ri_gan, gan)
        # 地支藏干中主要十神
        cang_gan = DZ_CANG_GAN.get(zhi, [])
        main_cang = cang_gan[0] if cang_gan else ""
        zhi_ss = get_shi_shen_for_gan(ri_gan, main_cang) if main_cang else ""

        # 干支五行
        gan_wx = TG_WU_XING[gan]
        zhi_wx = DZ_WU_XING[zhi]

        # 分析该柱的好坏
        analysis_parts = []
        rating = "中"  # 吉/中/凶
        good_points = []
        bad_points = []

        # 1. 天干十神判断
        if strong_weak in ("身强", "偏强"):
            is_gan_good = gan_ss in ("正官", "七杀", "正财", "偏财", "食神", "伤官")
        else:
            is_gan_good = gan_ss in ("正印", "偏印", "比肩", "劫财")

        if is_gan_good:
            # 根据柱位和十神给出具体说明
            pillar_desc = {
                "年柱": "家庭出身和早年环境",
                "月柱": "青年运势和事业根基",
                "日柱": "自身特质和婚姻",
                "时柱": "晚年状态和收尾",
            }
            context = pillar_desc.get(label, "")
            # 十神具体解读
            ss_meaning = {
                "正官": "有责任心和自律性，做事有分寸",
                "七杀": "有魄力和闯劲，遇强则强",
                "正印": "学习能力强，容易得到长辈提携",
                "偏印": "想法独特，有钻研精神，适合走专业化路线",
                "正财": "求财踏实务实，正业收入稳定",
                "偏财": "有赚钱头脑和经济嗅觉，擅抓机会",
                "比肩": "独立性好，有自己的主见",
                "劫财": "社交能力强，朋友多路子广",
                "食神": "性格温和有才华，懂享受生活",
                "伤官": "思维活跃创意多，不墨守成规",
            }
            meaning = ss_meaning.get(gan_ss, f"{gan_ss}的能量对你有利")
            good_points.append(f"天干【{gan}】是【{gan_ss}】——{meaning}。对应到{context}，这股力量能帮到你")
        else:
            # 不利时的具体说明
            pillar_desc_neg = {
                "年柱": "家庭出身和早年环境",
                "月柱": "青年运势和事业根基",
                "日柱": "自身特质和婚姻",
                "时柱": "晚年状态和收尾",
            }
            context = pillar_desc_neg.get(label, "")
            ss_meaning_neg = {
                "正官": "约束感会偏强，容易被规则和上级管着",
                "七杀": "压力大挑战多，容易遇到强势的人和事",
                "正印": "容易变得依赖，独立性需要刻意培养",
                "偏印": "想法容易偏激，人际关系上需要多注意",
                "正财": "求财会比较辛苦，一分耕耘一分收获",
                "偏财": "求财上容易大起大落，守财比赚钱更难",
                "比肩": "容易固执己见，团队合作中需多让步",
                "劫财": "朋友方面容易有利益纠纷，合伙需谨慎",
                "食神": "容易安于现状，进取心需要激发",
                "伤官": "容易说话太直得罪人，沟通中需注意方式",
            }
            meaning = ss_meaning_neg.get(gan_ss, f"{gan_ss}的能量对你来说是一道坎")
            bad_points.append(f"天干【{gan}】是【{gan_ss}】——{meaning}。对应到{context}，这股力量需要多留意")

        # 2. 地支五行判断
        if useful_god:
            is_zhi_good = zhi_wx in useful_god
            if is_zhi_good:
                good_points.append(f"地支【{zhi}】五行属【{zhi_wx}】——是你的用神五行，辅助性强")
            else:
                bad_points.append(f"地支【{zhi}】五行属【{zhi_wx}】——是你的忌神五行，需要注意")

        # 3. 特殊格局分析
        # 月柱特殊判断
        if label == "月柱":
            analysis_parts.append(f"月令{zhi}，日主{ri_gan}{ri_wx}在此状态为「{monthly_state}」")
            analysis_parts.append(f"当前季节：{season}季")

        # 日柱特殊判断
        if label == "日柱":
            if zhi in bazi.zhi_list:
                same_zhi_count = bazi.zhi_list.count(zhi)
                if same_zhi_count > 1:
                    bad_points.append(f"日支【{zhi}】与其他柱地支相同（伏吟：反复之象），婚姻宫容易反复不安定，感情上容易有重复的问题出现，同一个坑掉两次")

        # 时柱特殊判断
        if label == "时柱":
            if zhi in ["子", "午", "卯", "酉"]:
                bad_points.append(f"时柱【{zhi}】为桃花位——晚年可能还桃花运不衰，年纪不小了仍有情感纠葛")

        # 4. 综合评分
        score = len(good_points) - len(bad_points)
        if score >= 2:
            rating = "吉"
        elif score <= -2:
            rating = "凶"
        elif score >= 1:
            rating = "小吉"
        elif score <= -1:
            rating = "小凶"
        else:
            rating = "中"

        # 构建分析文本
        full_analysis = "；".join(analysis_parts + good_points + bad_points) if analysis_parts or good_points or bad_points else "配置平稳"

        # 简化版：逐条列出
        details = []
        if analysis_parts:
            details.extend(analysis_parts)
        if good_points:
            details.extend(good_points)
        if bad_points:
            details.extend(bad_points)

        results.append({
            "pillar": label,
            "gan_zhi": gan + zhi,
            "tiangan": gan,
            "dizhi": zhi,
            "gan_wx": gan_wx,
            "zhi_wx": zhi_wx,
            "tiangan_shishen": gan_ss,
            "dizhi_canggan": "、".join(cang_gan),
            "zhuyao_shishen": zhi_ss if zhi_ss else gan_ss,
            "rating": rating,
            "meaning": info["meaning"],
            "details": details,
        })

    return results


def analyze_life_fortune(bazi, ss_data, strength_analysis, dayun_data):
    """
    一生运势综合分析 — 事业/感情/家庭/健康 + 人生阶段 + 重要年份
    """
    ri_gan = bazi.ri_gan
    ri_wx = TG_WU_XING[ri_gan]
    strong_weak = strength_analysis["strong_weak"]
    useful_god = strength_analysis.get("useful_god", [])
    avoid_god = strength_analysis.get("avoid_god", [])
    monthly_state = strength_analysis.get("monthly_state", "")
    season = strength_analysis.get("season", "")
    counts = ss_data["counts"]
    cats = ss_data["category_counts"]

    guan = cats.get("官杀", 0)
    yin = cats.get("印枭", 0)
    cai = cats.get("财", 0)
    shi = cats.get("食伤", 0)
    bi = cats.get("比劫", 0)
    gender = bazi.gender

    from .shisheng import get_shi_shen_for_gan
    ss_desc = {"正官": "贵人运/事业升", "七杀": "挑战/突破", "正印": "学习/贵人",
               "偏印": "独特/转型", "正财": "财运/务实", "偏财": "机遇/投资",
               "比肩": "合作/朋友", "劫财": "竞争/波动", "食神": "才华/享受",
               "伤官": "创新/口舌"}

    result = {}

    # ═══════════ 1. 先天格局 ═══════════
    pattern_parts = [f"日主{ri_gan}{ri_wx}生于{season}季"]
    pattern_parts.append(f"月令状态「{monthly_state}」")

    # 格局判断
    wu_xing = {k: round(v, 2) for k, v in strength_analysis.get("distribution", {}).items()}
    wx_sorted = sorted(wu_xing.items(), key=lambda x: -x[1])

    if guan >= 3 and strong_weak in ("身强", "偏强"):
        pattern_parts.append("官杀为用神→格局贵气，适合管人管事，天生有当领导的命格")
    elif yin >= 3 and strong_weak in ("身强", "偏强"):
        pattern_parts.append("印星为用神→格局清气，有学问有修养，书卷气重，适合靠知识和口碑吃饭")
    elif cai >= 2 and strong_weak in ("身强", "偏强"):
        pattern_parts.append("财星为用神→格局富气，财运不错，命中有财，赚钱不会太难")
    elif shi >= 3:
        pattern_parts.append("食伤吐秀→格局灵性，才思敏捷，脑子好使，有创造力")
    elif bi >= 3 and strong_weak in ("身弱", "偏弱"):
        pattern_parts.append("比劫帮身→格局独立性强，不靠别人，自己打天下")

    if counts.get("伤官", 0) >= 2 and counts.get("正官", 0) >= 1:
        pattern_parts.append("⚠ 伤官见官（才华和规则冲突）→感情事业易有波折，需学会收敛锋芒。个性太强容易得罪人，尤其在感情里要控制脾气")
    if bi >= 3 and cai >= 2:
        pattern_parts.append("⚠ 比劫夺财（朋友和钱财难两全）→注意财务纠纷，合伙要签协议，和朋友涉及钱的事一定要说清楚")
    if yin >= 3 and shi >= 2:
        pattern_parts.append("✅ 印星化食伤（聪明又有内涵）→有学术/艺术天赋，既有才华又有修养，不是花架子")
    if guan >= 2 and yin >= 2:
        pattern_parts.append("✅ 官印相生（事业靠谱有后盾）→适合体制内/大企业发展，事业稳中有升。上有领导器重，下有知识支撑，事业路走得很稳")

    summary = "；".join(pattern_parts)
    result["summary"] = summary

    # ═══════════ 2. 事业运 ═══════════
    career_parts = []
    if counts.get("正官", 0) >= 2 or counts.get("七杀", 0) >= 2:
        if strong_weak in ("身强", "偏强"):
            career_parts.append(f"官杀（掌控管束之力）旺（{_fmt_val(guan)}）为用神→天生管理才能，适合体制内、企业管理、军警法律。你有领导气场，适合管人管事")
        else:
            career_parts.append(f"官杀（掌控管束之力）旺（{_fmt_val(guan)}）为忌神→事业压力大，需印星化杀或食伤制杀方能化解。管束你的人或事太多，但你有办法化解压力")
    else:
        career_parts.append(f"官杀运中平（{_fmt_val(guan)}），事业以稳为主。事业不算大起大落，稳扎稳打就好")

    if counts.get("偏财", 0) >= 2:
        career_parts.append("偏财旺，有经商头脑，适合创业/投资类工作。有商业嗅觉，投资眼光不错")
    elif counts.get("正财", 0) >= 2:
        career_parts.append("正财旺，适合稳定职业，收入稳健。财运稳定，拿死工资也能过得好")

    if shi >= 2:
        career_parts.append("食伤（才华输出之力）旺，适合创意、技术、自由职业。靠技术或创意吃饭，不坐班也能赚钱")

    if yin >= 2 and strong_weak in ("身弱", "偏弱"):
        career_parts.append("印星（庇护学习之力）生身，适合学术、教育、研究等稳定性工作。适合靠知识和技术吃饭的稳定工作")

    # 黄金期
    career_golden = []
    for step in dayun_data.get("da_yun_list", []):
        dy_ss = step.get("shi_shen", "")
        dy_gan_zhi = step.get("gan_zhi", "")
        if strong_weak in ("身强", "偏强"):
            is_good = dy_ss in ("正官", "七杀", "正财", "偏财", "食神", "伤官")
        else:
            is_good = dy_ss in ("正印", "偏印", "比肩", "劫财")
        if is_good:
            career_golden.append(f"{step['range']}（{dy_gan_zhi} {dy_ss}运）")

    if career_golden:
        career_parts.append(f"事业黄金期（知识库《02_八字排盘十神大运》：好运大运需顺时而为）：{'、'.join(career_golden)}")
    result["career"] = "；".join(career_parts)

    # ═══════════ 3. 感情/婚姻运 ═══════════
    love_parts = []
    ri_zhi = bazi.day_pillar.di_zhi  # 配偶宫
    love_parts.append(f"配偶宫（你的另一半的映射）为{ri_zhi}（知识库《02_八字排盘十神大运》记载：日支代表配偶宫，反映婚姻的先天状态）")

    # 配偶宫分析
    ri_zhi_ss = get_shi_shen_for_gan(ri_gan, DZ_CANG_GAN.get(ri_zhi, ["甲"])[0])
    love_parts.append(f"配偶宫藏干主十神为{ri_zhi_ss}")

    if gender == "女":
        gf = counts.get("正官", 0)
        qs = counts.get("七杀", 0)
        love_parts.append(f"官星共{_fmt_val(gf+qs)}位（正官{_fmt_val(gf)}、七杀{_fmt_val(qs)}）")
        if gf + qs >= 2:
            love_parts.append("官杀混杂→感情经历丰富，需注意选择。追求者多，但要擦亮眼睛，别被花言巧语骗了")
        elif gf + qs == 0:
            love_parts.append("官星不显→缘分较晚或需主动争取。感情上别等着找上门，自己主动点")
            if yin >= 2:
                love_parts.append("但印星旺→可通过长辈/熟人介绍。让亲戚朋友帮忙介绍，成功率更高")
        elif gf == 1 and qs == 0:
            love_parts.append("正官独显→感情专一，婚姻稳定。认定一个人就不容易变心，适合结婚过日子")
    else:
        zc = counts.get("正财", 0)
        pc = counts.get("偏财", 0)
        love_parts.append(f"财星共{_fmt_val(zc+pc)}位（正财{_fmt_val(zc)}、偏财{_fmt_val(pc)}）")
        if zc + pc >= 2:
            love_parts.append("财星旺→异性缘不错，需注意桃花。异性缘好但别花心，专一才是王道")
        elif zc + pc == 0:
            love_parts.append("财星不显→缘分来得晚一些。感情上别着急，好饭不怕晚")

    # 感情波动期
    love_waves = []
    for step in dayun_data.get("da_yun_list", []):
        dy_ss = step.get("shi_shen", "")
        if gender == "女" and dy_ss in ("七杀", "伤官"):
            love_waves.append(f"{step['range']}（{dy_ss}运）波动期")
        elif gender == "男" and dy_ss in ("劫财", "偏财"):
            love_waves.append(f"{step['range']}（{dy_ss}运）波动期")
    if love_waves:
        love_parts.append(f"感情波动大运：{'、'.join(love_waves)}")
    result["love"] = "；".join(love_parts)

    # ═══════════ 4. 家庭运 ═══════════
    family_parts = []
    if yin >= 2:
        if strong_weak in ("身弱", "偏弱"):
            family_parts.append("印星（庇护学习之力）为用→家庭是你的坚强后盾，长辈助力大。家里人对你很支持，有事找家里人准没错")
        else:
            family_parts.append("印星（庇护学习之力）为忌→注意与家人的边界感，需培养独立性。家人太照顾你反而不是好事，要学会自己拿主意")
    else:
        family_parts.append("印星不旺→成年后与原生家庭联系不那么紧密。长大了更靠自己，和家里联系不多")

    if bi >= 2:
        family_parts.append("比劫（同辈互动之力）旺→兄弟姐妹/朋友多，注意人际关系的取舍。身边人多是非也多，要学会分辨谁是真朋友")

    # 简化为家庭分析
    family_parts.append(f"月柱为父母宫（{bazi.month_pillar.gan_zhi}），十神{ss_data['counts']}综合分析")
    result["family"] = "；".join(family_parts)

    # ═══════════ 5. 健康运 ═══════════
    health_parts = []
    # 五行偏枯
    wx_items = sorted(wu_xing.items(), key=lambda x: x[1])
    if wx_items[0][1] <= 1 and wx_items[-1][1] >= 6:
        health_parts.append(f"五行严重偏枯→{wx_items[0][0]}极弱需注意（知识库《00_五行详解》：五行过弱对应的器官需重点保养）")
    elif wx_items[0][1] <= 2:
        health_parts.append(f"五行{wx_items[0][0]}偏弱→日常需有意识补充。多吃这个五行对应颜色的食物，注意相关器官保养")

    # 五行对应器官
    wx_organ = {"木": "肝胆/神经系统", "火": "心脏/血液循环/小肠",
                "土": "脾胃/消化系统", "金": "肺部/呼吸系统/大肠",
                "水": "肾脏/泌尿系统/内分泌"}
    for wx, val in wx_items:
        if val <= 1.5 and wx in wx_organ:
            health_parts.append(f"{wx}弱（{_fmt_val(val)}），注意{wx_organ[wx]}保养")
    result["health"] = "；".join(health_parts)

    # ═══════════ 6. 人生阶段分析 ═══════════
    
    stages = []
    for step in dayun_data.get("da_yun_list", []):
        dy_ss = step.get("shi_shen", "")
        if strong_weak in ("身强", "偏强"):
            is_good = dy_ss in ("正官", "七杀", "正财", "偏财", "食神", "伤官")
            rating = "吉祥" if is_good else "平缓"
        else:
            is_good = dy_ss in ("正印", "偏印", "比肩", "劫财")
            rating = "吉祥" if is_good else "平缓"
    
        ss_desc = {"正官": "贵人运/事业升", "七杀": "挑战/突破", "正印": "学习/贵人",
                   "偏印": "独特/转型", "正财": "财运/务实", "偏财": "机遇/投资",
                   "比肩": "合作/朋友", "劫财": "竞争/波动", "食神": "才华/享受",
                   "伤官": "创新/口舌"}
        stages.append({
            "range": step["range"],
            "gan_zhi": step["gan_zhi"],
            "shi_shen": dy_ss,
            "rating": rating,
            "desc": f"{ss_desc.get(dy_ss, '平稳')}运",
        })
    
    result["stages"] = stages
    
    # ═══════════ 7. 关键年份 ═══════════
    good_years = [s["range"] for s in stages if s["rating"] == "吉祥"]
    bad_years = [s["range"] for s in stages if s["rating"] != "吉祥"]
    result["key_years"] = {
        "good": good_years[:5],
        "bad": bad_years[:3],
    }
    
    return result