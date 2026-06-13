"""
地点五行分析 — 根据八字用神判断适合发展的城市/区域
"""

from typing import Dict, List, Tuple, Optional
from .constants import TG_WU_XING, DZ_WU_XING

# ════════════════════════════════════════════
# 省市五行映射（综合方位+地理+传统风水）
# ════════════════════════════════════════════

# 省级行政区 → 五行
PROVINCE_WUXING: Dict[str, str] = {
    # ── 北方（水）──
    "北京": "水", "天津": "水", "河北": "水", "山西": "水",
    "辽宁": "水", "吉林": "水", "黑龙江": "水", "内蒙古": "水",
    # ── 南方（火）──
    "广东": "火", "广西": "火", "海南": "火", "福建": "火",
    "湖南": "火", "江西": "火", "云南": "火",
    # ── 东方（木）──
    "上海": "木", "江苏": "木", "浙江": "木", "安徽": "木",
    "山东": "木", "台湾": "木",
    # ── 西方（金）──
    "新疆": "金", "青海": "金", "甘肃": "金", "宁夏": "金",
    "陕西": "金", "西藏": "金",
    # ── 中部/西南（土）──
    "河南": "土", "湖北": "土", "四川": "土", "重庆": "土",
    "贵州": "土", "澳门": "土", "香港": "土",
}

# 主要城市 → 五行（更精细的映射）
CITY_WUXING: Dict[str, str] = {
    # 北方城市（水）
    "北京": "水", "天津": "水", "石家庄": "水", "唐山": "水",
    "沈阳": "水", "大连": "水", "长春": "水", "哈尔滨": "水",
    "呼和浩特": "水", "太原": "水",
    # 南方城市（火）
    "广州": "火", "深圳": "火", "珠海": "火", "东莞": "火",
    "南宁": "火", "海口": "火", "福州": "火", "厦门": "火",
    "长沙": "火", "南昌": "火", "昆明": "火", "桂林": "火",
    # 东方城市（木）
    "上海": "木", "南京": "木", "苏州": "木", "无锡": "木",
    "杭州": "木", "宁波": "木", "温州": "木", "合肥": "木",
    "济南": "木", "青岛": "木", "烟台": "木", "台北": "木",
    # 西方城市（金）
    "乌鲁木齐": "金", "西宁": "金", "兰州": "金", "银川": "金",
    "西安": "金", "咸阳": "金", "拉萨": "金",
    # 中部/西南城市（土）
    "郑州": "土", "武汉": "土", "成都": "土", "重庆": "土",
    "贵阳": "土", "香港": "土", "澳门": "土", "宜昌": "土",
    "洛阳": "土", "开封": "土", "襄阳": "土",
}

# 区域方向映射
DIRECTION_MAP = {
    "水": "北方", "火": "南方", "木": "东方",
    "金": "西方", "土": "中部/西南",
}

# 五行行业对应
WUXING_CAREER: Dict[str, List[str]] = {
    "金": ["金融", "法律", "机械制造", "汽车", "科技", "军事", "公安", "精密仪器", "外科医生"],
    "木": ["教育", "文化", "出版", "设计", "服装", "木材", "医药", "环保", "园林", "传媒"],
    "水": ["物流", "贸易", "旅游", "航运", "水产", "水利", "销售", "媒体", "IT", "互联网"],
    "火": ["互联网", "能源", "电力", "餐饮", "娱乐", "演艺", "设计", "美容", "光电", "化工"],
    "土": ["房地产", "建筑", "农业", "矿业", "仓储", "工程", "顾问", "管理", "地产金融"],
}

# 五行对应人体器官
WUXING_ORGAN: Dict[str, str] = {
    "金": "肺/大肠/呼吸系统/皮肤",
    "木": "肝/胆/神经系统/筋骨",
    "水": "肾/膀胱/泌尿系统/内分泌",
    "火": "心/小肠/血液循环/眼睛",
    "土": "脾/胃/消化系统/肌肉",
}

# 五行对应色彩
WUXING_COLOR: Dict[str, str] = {
    "金": "白色、银色、金色",
    "木": "绿色、青色",
    "水": "黑色、蓝色、灰色",
    "火": "红色、紫色、粉红",
    "土": "黄色、棕色、米色",
}


def get_location_wuxing(province: str, city: str = "") -> Tuple[str, str]:
    """
    获取地点对应的五行

    Args:
        province: 省/直辖市/自治区
        city: 市（可选，优先查城市）

    Returns:
        (五行, 方向)
    """
    # 优先查城市
    if city and city in CITY_WUXING:
        wx = CITY_WUXING[city]
        return wx, DIRECTION_MAP.get(wx, "")

    # 查省份
    if province in PROVINCE_WUXING:
        wx = PROVINCE_WUXING[province]
        return wx, DIRECTION_MAP.get(wx, "")

    # 查别名
    for p, wx in PROVINCE_WUXING.items():
        if province in p or p in province:
            return wx, DIRECTION_MAP.get(wx, "")

    return "", ""


def analyze_location_compatibility(
    province: str, city: str,
    useful_god: List[str], avoid_god: List[str],
    strong_weak: str, ri_gan: str,
    categories: Dict[str, float],
    gender: str,
) -> Dict:
    """
    综合分析某地点对个人的发展适合度

    Args:
        province/city: 省市
        useful_god/avoid_god: 用神忌神
        strong_weak: 身强/身弱
        ri_gan: 日主
        categories: 十神分类统计
        gender: 性别

    Returns:
        {
            "location_wx": 地点五行,
            "direction": 方向,
            "overall_score": 综合评分(1-10),
            "overall_verdict": 总评价,
            "is_recommended": 是否推荐,
            "career": 事业分析,
            "love": 感情分析,
            "health": 健康分析,
            "wealth": 财运分析,
            "family": 家庭分析,
            "advice": 建议,
        }
    """
    loc_wx, direction = get_location_wuxing(province, city)

    if not loc_wx:
        return {"error": f"未找到地点「{province}{city}」的五行信息，请检查省市名称"}

    # 判断该地点五行是否属于用神/忌神
    is_yongshen = loc_wx in useful_god if useful_god else None
    is_jishen = loc_wx in avoid_god if avoid_god else None

    # 综合评分
    score = 6  # 基础分
    if is_yongshen:
        score += 2
    elif is_jishen:
        score -= 2

    if score >= 7:
        verdict = f"✅ 非常推荐"
        is_recommended = True
    elif score >= 5:
        verdict = f"🟡 可以发展，但需注意化解"
        is_recommended = True
    else:
        verdict = f"⚠ 不推荐，需谨慎考虑"
        is_recommended = False

    # ── 事业分析 ──
    career_parts = []
    if is_yongshen:
        career_parts.append(
            f"该地位于{direction}，五行属「{loc_wx}」，"
            f"与您的用神一致，在此地发展事业顺风顺水"
        )
        careers = WUXING_CAREER.get(loc_wx, [])
        if careers:
            career_parts.append(f"特别适合从事：{'、'.join(careers[:5])}")
    elif is_jishen:
        career_parts.append(
            f"该地位于{direction}，五行属「{loc_wx}」，"
            f"与您的忌神一致，在此地发展事业阻力较大"
        )
        careers = list(set(WUXING_CAREER.get(avoid_god[0], []) + WUXING_CAREER.get(loc_wx, [])))
        if careers:
            career_parts.append(f"如在此发展，宜选择五行属用神（{'、'.join(useful_god)}）的行业")
    else:
        career_parts.append(
            f"该地位于{direction}，五行属「{loc_wx}」，"
            f"对事业发展影响中性"
        )
    career_text = "；".join(career_parts)

    # ── 财运分析 ──
    wealth_parts = []
    if loc_wx in useful_god:
        wealth_parts.append(f"{direction}{loc_wx}地为您的财运加分，求财相对顺利")
    elif loc_wx in avoid_god:
        wealth_parts.append(f"{direction}{loc_wx}地克制财运，投资理财需格外谨慎")
    else:
        wealth_parts.append(f"财运表现中性，主要看个人行业选择")
    wealth_text = "；".join(wealth_parts)

    # ── 感情/婚姻分析 ──
    love_parts = []
    if is_yongshen:
        love_parts.append(f"用神方位利于人缘和感情和谐，容易遇到志同道合的伴侣")
    elif is_jishen:
        love_parts.append(f"忌神方位可能导致感情不和谐或桃花困扰")
    else:
        love_parts.append(f"感情运中性，主要看个人选择")

    if loc_wx == "水" and "火" in useful_god:
        love_parts.append("北方水旺地需注意感情中的沟通问题，多表达避免误会")
    elif loc_wx == "金" and "木" in useful_god:
        love_parts.append("西方金旺地需注意感情中的固执倾向，学会妥协")
    elif loc_wx == "火" and "水" in useful_god:
        love_parts.append("南方火旺地需注意情绪管理，避免冲动影响感情")
    love_text = "；".join(love_parts)

    # ── 健康分析 ──
    health_parts = []
    health_organ = WUXING_ORGAN.get(loc_wx, "")
    if loc_wx in avoid_god:
        health_parts.append(
            f"⚠ 注意：此地五行「{loc_wx}」与您的忌神一致，"
            f"长期居住可能影响{health_organ}健康"
        )
        # 建议补充的五行
        for god in useful_god[:2]:
            god_color = WUXING_COLOR.get(god, "")
            health_parts.append(f"建议多接触{god}元素（{god_color}色物品、饮食）来平衡")
    elif loc_wx in useful_god:
        health_parts.append(f"此地五行生扶您的身体，整体健康状况良好")
    health_text = "；".join(health_parts)

    # ── 家庭分析 ──
    family_parts = []
    if is_yongshen:
        family_parts.append(f"用神方位利于家庭和谐与长辈健康")
    elif is_jishen:
        family_parts.append(f"忌神方位可能带来家庭关系紧张，需多沟通包容")
    else:
        family_parts.append(f"家庭运中性")

    if loc_wx == "土" and "水" in useful_god:
        family_parts.append("中部/西南土旺地利于家庭稳定，适合扎根发展")
    elif loc_wx == "木" and "土" in useful_god:
        family_parts.append("东方木旺地利于家庭成长，注意兄弟姐妹关系")
    family_text = "；".join(family_parts)

    # ── 综合建议 ──
    advice_parts = []
    if is_recommended and is_yongshen:
        advice_parts.append(f"强烈推荐在此地发展，五行用神与方位相合，事半功倍")
        advice_parts.append(f"适合长期定居、创业、置业")
        advice_parts.append(f"多穿{loc_wx}色系（{'、'.join(WUXING_COLOR.get(loc_wx, '').split('、'))}色）增强气场")
    elif is_recommended:
        advice_parts.append(f"此地五行与您无冲克，可以发展。但仍有优化空间")
        if useful_god:
            advice_parts.append(f"可通过补充用神「{'、'.join(useful_god)}」元素（方位/颜色/行业）来增强运势")
    else:
        advice_parts.append(f"此地五行「{loc_wx}」与您的忌神一致，需谨慎考虑")
        advice_parts.append(f"建议优先考虑往用神方位（{', '.join(DIRECTION_MAP.get(g, '') for g in useful_god[:2])}）发展")
        advice_parts.append(f"如果必须在此地，需通过行业/色彩/风水进行调和")
    advice_text = "；".join(advice_parts)

    return {
        "location_wx": loc_wx,
        "direction": direction,
        "overall_score": score,
        "overall_verdict": verdict,
        "is_recommended": is_recommended,
        "career": career_text,
        "love": love_text,
        "health": health_text,
        "wealth": wealth_text,
        "family": family_text,
        "advice": advice_text,
    }