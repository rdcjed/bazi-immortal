"""
地点五行分析 — 根据八字用神判断适合发展的城市/区域
增强版：增加城市地理特征分析（沿海/山地/盆地等），扩展城市覆盖
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

# 主要城市 → 五行（更精细的映射，已扩展至200+城市）
CITY_WUXING: Dict[str, str] = {
    # ── 直辖市 ──
    "北京": "水", "天津": "水", "上海": "木", "重庆": "土",
    # ── 北方城市（水）──
    "石家庄": "水", "唐山": "水", "秦皇岛": "水", "邯郸": "水", "邢台": "水",
    "保定": "水", "张家口": "水", "承德": "水", "沧州": "水", "廊坊": "水", "衡水": "水",
    "沈阳": "水", "大连": "水", "鞍山": "水", "抚顺": "水", "本溪": "水",
    "丹东": "水", "锦州": "水", "营口": "水", "阜新": "水", "辽阳": "水",
    "盘锦": "水", "铁岭": "水", "朝阳": "水", "葫芦岛": "水",
    "长春": "水", "吉林": "水", "四平": "水", "辽源": "水", "通化": "水",
    "白山": "水", "松原": "水", "白城": "水", "延吉": "水",
    "哈尔滨": "水", "齐齐哈尔": "水", "鸡西": "水", "鹤岗": "水", "双鸭山": "水",
    "大庆": "水", "伊春": "水", "佳木斯": "水", "七台河": "水", "牡丹江": "水",
    "黑河": "水", "绥化": "水",
    "呼和浩特": "水", "包头": "水", "乌海": "水", "赤峰": "水", "通辽": "水",
    "鄂尔多斯": "水", "呼伦贝尔": "水", "巴彦淖尔": "水", "乌兰察布": "水",
    "太原": "水", "大同": "水", "阳泉": "水", "长治": "水", "晋城": "水",
    "朔州": "水", "晋中": "水", "运城": "水", "忻州": "水", "临汾": "水", "吕梁": "水",
    # ── 南方城市（火）──
    "广州": "火", "深圳": "火", "珠海": "火", "汕头": "火", "佛山": "火",
    "韶关": "火", "湛江": "火", "肇庆": "火", "江门": "火", "茂名": "火",
    "惠州": "火", "梅州": "火", "汕尾": "火", "河源": "火", "阳江": "火",
    "清远": "火", "东莞": "火", "中山": "火", "潮州": "火", "揭阳": "火", "云浮": "火",
    "南宁": "火", "柳州": "火", "桂林": "火", "梧州": "火", "北海": "火",
    "防城港": "火", "钦州": "火", "贵港": "火", "玉林": "火", "百色": "火",
    "贺州": "火", "河池": "火", "来宾": "火", "崇左": "火",
    "海口": "火", "三亚": "火", "三沙": "火", "儋州": "火",
    "福州": "火", "厦门": "火", "莆田": "火", "三明": "火", "泉州": "火",
    "漳州": "火", "南平": "火", "龙岩": "火", "宁德": "火",
    "长沙": "火", "株洲": "火", "湘潭": "火", "衡阳": "火", "邵阳": "火",
    "岳阳": "火", "常德": "火", "张家界": "火", "益阳": "火", "郴州": "火",
    "永州": "火", "怀化": "火", "娄底": "火",
    "南昌": "火", "景德镇": "火", "萍乡": "火", "九江": "火", "新余": "火",
    "鹰潭": "火", "赣州": "火", "吉安": "火", "宜春": "火", "抚州": "火", "上饶": "火",
    "昆明": "火", "曲靖": "火", "玉溪": "火", "保山": "火", "昭通": "火",
    "丽江": "火", "普洱": "火", "临沧": "火", "楚雄": "火", "大理": "火",
    "红河": "火", "西双版纳": "火", "德宏": "火", "怒江": "火", "迪庆": "火",
    # ── 东方城市（木）──
    "南京": "木", "苏州": "木", "无锡": "木", "常州": "木", "南通": "木",
    "扬州": "木", "镇江": "木", "泰州": "木", "盐城": "木", "淮安": "木",
    "连云港": "木", "徐州": "木", "宿迁": "木",
    "杭州": "木", "宁波": "木", "温州": "木", "嘉兴": "木", "湖州": "木",
    "绍兴": "木", "金华": "木", "衢州": "木", "舟山": "木", "台州": "木", "丽水": "木",
    "合肥": "木", "芜湖": "木", "蚌埠": "木", "淮南": "木", "马鞍山": "木",
    "淮北": "木", "铜陵": "木", "安庆": "木", "黄山": "木", "滁州": "木",
    "阜阳": "木", "宿州": "木", "六安": "木", "亳州": "木", "池州": "木", "宣城": "木",
    "济南": "木", "青岛": "木", "淄博": "木", "枣庄": "木", "东营": "木",
    "烟台": "木", "潍坊": "木", "济宁": "木", "泰安": "木", "威海": "木",
    "日照": "木", "临沂": "木", "德州": "木", "聊城": "木", "滨州": "木", "菏泽": "木",
    "台北": "木", "高雄": "木", "台中": "木", "台南": "木", "基隆": "木", "新竹": "木",
    # ── 西方城市（金）──
    "乌鲁木齐": "金", "克拉玛依": "金", "吐鲁番": "金", "哈密": "金",
    "昌吉": "金", "库尔勒": "金", "阿克苏": "金", "喀什": "金", "伊宁": "金",
    "西宁": "金", "海东": "金", "格尔木": "金",
    "兰州": "金", "嘉峪关": "金", "金昌": "金", "白银": "金", "天水": "金",
    "武威": "金", "张掖": "金", "平凉": "金", "酒泉": "金", "庆阳": "金",
    "定西": "金", "陇南": "金",
    "银川": "金", "石嘴山": "金", "吴忠": "金", "固原": "金", "中卫": "金",
    "西安": "金", "铜川": "金", "宝鸡": "金", "咸阳": "金", "渭南": "金",
    "延安": "金", "汉中": "金", "榆林": "金", "安康": "金", "商洛": "金",
    "拉萨": "金", "日喀则": "金", "昌都": "金", "林芝": "金", "山南": "金", "那曲": "金",
    # ── 中部/西南城市（土）──
    "郑州": "土", "开封": "土", "洛阳": "土", "平顶山": "土", "安阳": "土",
    "鹤壁": "土", "新乡": "土", "焦作": "土", "濮阳": "土", "许昌": "土",
    "漯河": "土", "三门峡": "土", "南阳": "土", "商丘": "土", "信阳": "土",
    "周口": "土", "驻马店": "土",
    "武汉": "土", "黄石": "土", "十堰": "土", "宜昌": "土", "襄阳": "土",
    "鄂州": "土", "荆门": "土", "孝感": "土", "荆州": "土", "黄冈": "土",
    "咸宁": "土", "随州": "土", "恩施": "土",
    "成都": "土", "自贡": "土", "攀枝花": "土", "泸州": "土", "德阳": "土",
    "绵阳": "土", "广元": "土", "遂宁": "土", "内江": "土", "乐山": "土",
    "南充": "土", "眉山": "土", "宜宾": "土", "广安": "土", "达州": "土",
    "雅安": "土", "巴中": "土", "资阳": "土", "西昌": "土",
    "贵阳": "土", "六盘水": "土", "遵义": "土", "安顺": "土", "毕节": "土",
    "铜仁": "土", "黔西南": "土", "黔东南": "土", "黔南": "土",
    "香港": "土", "澳门": "土",
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

# ════════════════════════════════════════════
# 地理特征 → 五行修正
# ════════════════════════════════════════════
GEO_FEATURES: Dict[str, Dict[str, float]] = {
    "沿海": {"水": 0.3},
    "沿海岛屿": {"水": 0.5},
    "山地": {"土": 0.3, "金": 0.1},
    "高原": {"金": 0.3, "火": 0.2},
    "盆地": {"土": 0.4},
    "平原": {},  # 无修正
    "河谷": {"水": 0.2, "土": 0.2},
}

# ════════════════════════════════════════════
# 城市 → 地理特征（覆盖全国所有重要城市）
# ════════════════════════════════════════════
CITY_GEO_FEATURES: Dict[str, List[str]] = {
    # ── 沿海城市（水属性叠加）──
    "大连": ["沿海"], "天津": ["沿海"], "青岛": ["沿海"], "上海": ["沿海"],
    "宁波": ["沿海"], "厦门": ["沿海"], "深圳": ["沿海"], "珠海": ["沿海"],
    "海口": ["沿海"], "三亚": ["沿海"], "威海": ["沿海"], "烟台": ["沿海"],
    "日照": ["沿海"], "秦皇岛": ["沿海"], "温州": ["沿海"], "福州": ["沿海"],
    "泉州": ["沿海"], "汕头": ["沿海"], "北海": ["沿海"], "防城港": ["沿海"],
    "连云港": ["沿海"], "舟山": ["沿海岛屿"], "惠州": ["沿海"], "中山": ["沿海"],
    "江门": ["沿海"], "湛江": ["沿海"], "茂名": ["沿海"], "阳江": ["沿海"],
    "汕尾": ["沿海"], "潮州": ["沿海"], "漳州": ["沿海"], "莆田": ["沿海"],
    "宁德": ["沿海"], "南通": ["沿海"], "盐城": ["沿海"], "嘉兴": ["沿海"],
    "绍兴": ["沿海"], "台州": ["沿海"], "丹东": ["沿海"], "营口": ["沿海"],
    "盘锦": ["沿海"], "锦州": ["沿海"], "葫芦岛": ["沿海"], "钦州": ["沿海"],
    "基隆": ["沿海"], "高雄": ["沿海"],

    # ── 山地城市（土+金叠加）──
    "重庆": ["山地"], "贵阳": ["山地"], "昆明": ["山地"], "丽江": ["山地"],
    "遵义": ["山地"], "六盘水": ["山地"], "安顺": ["山地"], "毕节": ["山地"],
    "昭通": ["山地"], "攀枝花": ["山地"], "张家界": ["山地"], "黄山": ["山地"],
    "三明": ["山地"], "龙岩": ["山地"], "韶关": ["山地"], "清远": ["山地"],
    "河源": ["山地"], "梅州": ["山地"], "云浮": ["山地"], "十堰": ["山地"],
    "恩施": ["山地"], "宜昌": ["山地"], "三门峡": ["山地"], "延安": ["山地"],
    "宝鸡": ["山地"], "汉中": ["山地"], "安康": ["山地"], "商洛": ["山地"],
    "陇南": ["山地"], "天水": ["山地"], "乐山": ["山地"], "雅安": ["山地"],
    "广元": ["山地"], "巴中": ["山地"], "达州": ["山地"], "宜宾": ["山地"],
    "泸州": ["山地"], "自贡": ["山地"], "内江": ["山地"], "资阳": ["山地"],
    "眉山": ["山地"], "曲靖": ["山地"], "玉溪": ["山地"], "保山": ["山地"],
    "普洱": ["山地"], "临沧": ["山地"], "楚雄": ["山地"], "红河": ["山地"],
    "德宏": ["山地"], "怒江": ["山地"], "迪庆": ["山地"], "铜仁": ["山地"],
    "黔西南": ["山地"], "黔东南": ["山地"], "黔南": ["山地"], "湘西": ["山地"],
    "怀化": ["山地"], "永州": ["山地"], "郴州": ["山地"], "邵阳": ["山地"],
    "娄底": ["山地"], "衡阳": ["山地"], "株洲": ["山地"], "湘潭": ["山地"],
    "赣州": ["山地"], "吉安": ["山地"], "宜春": ["山地"], "抚州": ["山地"],
    "上饶": ["山地"], "景德镇": ["山地"], "萍乡": ["山地"], "九江": ["山地"],
    "南平": ["山地"], "丽水": ["山地"], "衢州": ["山地"], "金华": ["山地"],
    "池州": ["山地"], "宣城": ["山地"], "六安": ["山地"], "安庆": ["山地"],
    "黄冈": ["山地"], "咸宁": ["山地"], "随州": ["山地"], "荆门": ["山地"],
    "宜昌": ["山地"], "襄阳": ["山地"], "绵阳": ["山地"], "德阳": ["山地"],
    "南充": ["山地"], "广安": ["山地"], "遂宁": ["山地"], "西昌": ["山地"],

    # ── 盆地城市（土属性叠加）──
    "成都": ["盆地"], "西安": ["盆地"], "太原": ["盆地"], "南昌": ["盆地"],
    "长沙": ["盆地"], "武汉": ["盆地"], "郑州": ["盆地"], "合肥": ["盆地"],
    "南京": ["盆地"], "南宁": ["盆地"],

    # ── 高原城市（金+火叠加）──
    "拉萨": ["高原"], "西宁": ["高原"], "兰州": ["高原"], "呼和浩特": ["高原"],
    "乌鲁木齐": ["高原"], "银川": ["高原"], "格尔木": ["高原"], "日喀则": ["高原"],
    "昌都": ["高原"], "林芝": ["高原"], "山南": ["高原"], "那曲": ["高原"],
    "香格里拉": ["高原"], "大理": ["高原"], "嘉峪关": ["高原"],
    "张掖": ["高原"], "酒泉": ["高原"], "武威": ["高原"], "中卫": ["高原"],

    # ── 河谷/特殊地理特征 ──
    "桂林": ["河谷"],  # 喀斯特河谷，水+土
    "大理": ["高原", "河谷"],  # 高原湖泊，水+金
    "西双版纳": ["河谷"],  # 热带河谷，火+水
    "牡丹江": ["河谷"], "伊春": ["山地"], "黑河": ["河谷"],
    "铜陵": ["河谷"], "芜湖": ["河谷"],

    # ── 平原城市（无修正）──
    "北京": ["平原"], "石家庄": ["平原"], "唐山": ["平原"], "邯郸": ["平原"],
    "保定": ["平原"], "沧州": ["平原"], "廊坊": ["平原"], "衡水": ["平原"],
    "沈阳": ["平原"], "长春": ["平原"], "哈尔滨": ["平原"],
    "济南": ["平原"], "淄博": ["平原"], "潍坊": ["平原"], "济宁": ["平原"],
    "临沂": ["平原"], "德州": ["平原"], "聊城": ["平原"], "滨州": ["平原"],
    "菏泽": ["平原"], "枣庄": ["平原"], "泰安": ["平原"], "徐州": ["平原"],
    "宿迁": ["平原"], "淮安": ["平原"], "阜阳": ["平原"], "宿州": ["平原"],
    "亳州": ["平原"], "周口": ["平原"], "驻马店": ["平原"], "信阳": ["平原"],
    "南阳": ["平原"], "商丘": ["平原"], "开封": ["平原"], "洛阳": ["平原"],
    "新乡": ["平原"], "安阳": ["平原"], "濮阳": ["平原"], "许昌": ["平原"],
    "漯河": ["平原"], "平顶山": ["平原"], "鹤壁": ["平原"], "焦作": ["平原"],
    "广州": ["平原"], "佛山": ["平原"], "东莞": ["平原"],
    "杭州": ["平原"], "苏州": ["平原"], "无锡": ["平原"], "常州": ["平原"],
    "扬州": ["平原"], "镇江": ["平原"], "泰州": ["平原"],
    "宁波": ["平原"], "湖州": ["平原"],
}

# 中文地理特征描述
GEO_FEATURE_DESC: Dict[str, str] = {
    "沿海": "沿海城市，水汽充沛，兼具「水」的灵动与包容",
    "沿海岛屿": "海岛城市，四面环水，水性极旺",
    "山地": "山地城市，地势高峻，土金之气较重",
    "高原": "高原城市，海拔较高，金火之气明显",
    "盆地": "盆地城市，地势低洼，土气汇聚厚重",
    "平原": "平原城市，地势平坦，五行较为中和",
    "河谷": "河谷城市，山水交汇，水土交融",
}


def _normalize_city(city: str) -> str:
    """规范化城市名：去除 '市'/'区'/'县' 后缀"""
    for suffix in ["市", "区", "县", "镇"]:
        if city.endswith(suffix) and len(city) > 2:
            return city[:-len(suffix)]
    return city


def get_location_wuxing(province: str, city: str = "") -> Dict:
    """
    获取地点对应的五行及地理特征

    Args:
        province: 省/直辖市/自治区
        city: 市（可选，优先查城市）

    Returns:
        {
            main_wx: 主要五行,
            direction: 方向,
            geo_features: 地理特征列表,
            geo_modifiers: 地理修正列表 [(五行, 权重), ...],
            combined_wxs: {五行: 总权重, ...}
        }
    """
    city_key = _normalize_city(city) if city else ""

    # 获取基础五行
    main_wx = ""
    if city_key and city_key in CITY_WUXING:
        main_wx = CITY_WUXING[city_key]
    elif province in PROVINCE_WUXING:
        main_wx = PROVINCE_WUXING[province]
    else:
        for p, wx in PROVINCE_WUXING.items():
            if province in p or p in province:
                main_wx = wx
                break

    direction = DIRECTION_MAP.get(main_wx, "")
    if not main_wx:
        return {
            "main_wx": "",
            "direction": "",
            "geo_features": [],
            "geo_modifiers": [],
            "combined_wxs": {},
        }

    # 获取地理特征
    geo_features: List[str] = []
    if city_key and city_key in CITY_GEO_FEATURES:
        geo_features = CITY_GEO_FEATURES[city_key]
    elif province in CITY_GEO_FEATURES:
        geo_features = CITY_GEO_FEATURES[province]
    else:
        geo_features = ["平原"]  # 默认平原

    # 计算地理修正
    geo_modifiers: List[Tuple[str, float]] = []
    combined_wxs: Dict[str, float] = {main_wx: 1.0}

    for feature in geo_features:
        modifiers = GEO_FEATURES.get(feature, {})
        for wx, weight in modifiers.items():
            geo_modifiers.append((wx, weight))
            combined_wxs[wx] = combined_wxs.get(wx, 0.0) + weight

    return {
        "main_wx": main_wx,
        "direction": direction,
        "geo_features": geo_features,
        "geo_modifiers": geo_modifiers,
        "combined_wxs": combined_wxs,
    }


def get_geo_feature_text(geo_features: List[str]) -> str:
    """生成地理特征描述文本"""
    parts = []
    for f in geo_features:
        desc = GEO_FEATURE_DESC.get(f, f)
        parts.append(desc)
    return "，".join(parts)


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
            "geo_features": 地理特征列表,
            "geo_modifiers": 地理修正列表,
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
    loc_info = get_location_wuxing(province, city)
    loc_wx = loc_info["main_wx"]
    direction = loc_info["direction"]
    geo_features = loc_info["geo_features"]
    geo_modifiers = loc_info["geo_modifiers"]

    if not loc_wx:
        return {"error": f"未找到地点「{province}{city}」的五行信息，请检查省市名称"}

    # 判断该地点五行是否属于用神/忌神
    is_yongshen = loc_wx in useful_god if useful_god else None
    is_jishen = loc_wx in avoid_god if avoid_god else None

    # 综合评分（基础分+地理修正）
    score = 6  # 基础分
    if is_yongshen:
        score += 2
    elif is_jishen:
        score -= 2

    # 地理特征加分：用神五行有地理叠加时加分
    for wx, _ in geo_modifiers:
        if wx in useful_god:
            score += 0.5
        elif wx in avoid_god:
            score -= 0.5

    score = max(1, min(10, round(score)))

    if score >= 7:
        verdict = f"✅ 非常推荐"
        is_recommended = True
    elif score >= 5:
        verdict = f"🟡 可以发展，但需注意化解"
        is_recommended = True
    else:
        verdict = f"⚠ 不推荐，需谨慎考虑"
        is_recommended = False

    # 地理特征描述（用于分析文本）
    geo_desc = get_geo_feature_text(geo_features)
    geo_modifier_text = ""
    if geo_modifiers:
        modifier_parts = [f"五行「{wx}」叠加 +{weight}" for wx, weight in geo_modifiers]
        geo_modifier_text = "（" + "，".join(modifier_parts) + "）"

    # ── 事业分析 ──
    career_parts = []
    if is_yongshen:
        geo_intro = f"{city}地处{geo_desc}（地理特征叠加）" if geo_features and geo_features != ["平原"] else f"该地位于{direction}"
        career_parts.append(
            f"{geo_intro}，五行属「{loc_wx}」，"
            f"与您的用神一致，在此地发展事业顺风顺水"
        )
        careers = WUXING_CAREER.get(loc_wx, [])
        if careers:
            career_parts.append(f"特别适合从事：{'、'.join(careers[:5])}")
    elif is_jishen:
        geo_intro = f"{city}地处{geo_desc}" if geo_features and geo_features != ["平原"] else f"该地位于{direction}"
        career_parts.append(
            f"{geo_intro}，五行属「{loc_wx}」，"
            f"与您的忌神一致，在此地发展事业阻力较大"
        )
        careers = list(set(WUXING_CAREER.get(avoid_god[0], []) + WUXING_CAREER.get(loc_wx, [])))
        if careers:
            career_parts.append(f"如在此发展，宜选择五行属用神（{'、'.join(useful_god)}）的行业")
    else:
        geo_intro = f"{city}地处{geo_desc}" if geo_features and geo_features != ["平原"] else f"该地位于{direction}"
        career_parts.append(
            f"{geo_intro}，五行属「{loc_wx}」，"
            f"对事业发展影响中性"
        )
    career_text = "；".join(career_parts)

    # 事业大白话
    if is_yongshen:
        career_tip = f"说白了，{city}这个地方跟您命里合拍，干事业省力气，属于「天时地利」都占了。趁早来发展！"
    elif is_jishen:
        career_tip = f"说白了，{city}这个地方跟您命里有点犯冲，干事业容易碰到磕磕绊绊。如果非来不可，选对行业是关键。"
    else:
        career_tip = f"说白了，{city}这地方对您来说不算最好也不算最差，中规中矩，主要看您自己怎么干。"
    career_text = career_text + "\n💡 " + career_tip

    # ── 财运分析 ──
    wealth_parts = []
    if loc_wx in useful_god:
        wealth_parts.append(f"{direction}{loc_wx}地为您的财运加分，求财相对顺利")
    elif loc_wx in avoid_god:
        wealth_parts.append(f"{direction}{loc_wx}地克制财运，投资理财需格外谨慎")
    else:
        wealth_parts.append(f"财运表现中性，主要看个人行业选择")
    wealth_text = "；".join(wealth_parts)
    if loc_wx in useful_god:
        wealth_tip = f"说白了，在{city}赚钱比别处顺当，财路比较宽。"
    elif loc_wx in avoid_god:
        wealth_tip = f"说白了，在{city}赚钱得留个心眼，投资容易踩坑，稳字当头。"
    else:
        wealth_tip = f"说白了，在{city}能不能发财，关键看您干啥行业，地方本身不拖后腿。"
    wealth_text = wealth_text + "\n💡 " + wealth_tip

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

    # 地理特征对感情的影响
    if "沿海" in geo_features or "沿海岛屿" in geo_features:
        if "水" in avoid_god:
            love_parts.append(f"{city}为沿海城市，水性流动多变，感情上容易聚少离多，需要注意经营")
        elif "水" in useful_god:
            love_parts.append(f"{city}为沿海城市，水性灵动浪漫，利于感情升温")
    if "山地" in geo_features:
        if "土" in avoid_god:
            love_parts.append(f"{city}为山地城市，土性厚重固执，感情中需注意包容和变通")

    love_text = "；".join(love_parts)
    if is_yongshen:
        love_tip = f"说白了，在{city}找对象、处感情比较顺，人缘好。"
    elif is_jishen:
        love_tip = f"说白了，在{city}感情上容易有波折，得多用用心思经营。"
    else:
        love_tip = f"说白了，在{city}的感情运势就看你个人造化，地方不背锅。"
    love_text = love_text + "\n💡 " + love_tip

    # ── 健康分析 ──
    health_parts = []
    health_organ = WUXING_ORGAN.get(loc_wx, "")
    if loc_wx in avoid_god:
        health_parts.append(
            f"⚠ 注意：此地五行「{loc_wx}」与您的忌神一致，"
            f"长期居住可能影响{health_organ}健康"
        )
        # 检查地理特征叠加对健康的影响
        for geo_wx, _ in geo_modifiers:
            if geo_wx in avoid_god:
                geo_name = next((k for k, v in GEO_FEATURES.items() if geo_wx in v), "")
                health_parts.append(
                    f"⚠ {city}的{geo_name}地理特征进一步加重了「{geo_wx}」的不利影响，"
                    f"需特别注意{WUXING_ORGAN.get(geo_wx, '相关部位')}"
                )
        # 建议补充的五行
        for god in useful_god[:2]:
            god_color = WUXING_COLOR.get(god, "")
            health_parts.append(f"建议多接触{god}元素（{god_color}色物品、饮食）来平衡")
    elif loc_wx in useful_god:
        health_parts.append(f"此地五行生扶您的身体，整体健康状况良好")
        for geo_wx, _ in geo_modifiers:
            if geo_wx in useful_god:
                health_parts.append(f"{city}的地理特征增强了「{geo_wx}」的生扶作用，对健康更有利")
    health_text = "；".join(health_parts)
    if loc_wx in avoid_god:
        health_tip = f"说白了，在{city}住久了身体容易出些小毛病，得多注意{health_organ}方面的保养。"
    else:
        health_tip = f"说白了，在{city}住着对身体没坏处，整体气场比较养人。"
    health_text = health_text + "\n💡 " + health_tip

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

    # 地理特征对家庭的影响
    if "盆地" in geo_features:
        family_parts.append(f"{city}为盆地地形，土气汇聚，家庭氛围较为和睦安稳，适合安家")
    if "平原" in geo_features:
        family_parts.append(f"{city}地势平坦开阔，家庭关系较为平和")

    family_text = "；".join(family_parts)
    if is_yongshen:
        family_tip = f"说白了，在{city}安家落户挺合适，家里人相处和气。"
    else:
        family_tip = f"说白了，在{city}家庭方面需要多花点心思，家和万事兴。"
    family_text = family_text + "\n💡 " + family_tip

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

    # 地理特征建议
    if geo_features and geo_features != ["平原"]:
        geo_advice = f"鉴于{city}的{get_geo_feature_text(geo_features)}特征"
        if any(wx in useful_god for wx, _ in geo_modifiers):
            geo_advice += "，地理特征与您用神相合，可充分利用这一优势"
        elif any(wx in avoid_god for wx, _ in geo_modifiers):
            geo_advice += "，地理特征可能带来额外克制，需特别留意"
        advice_parts.append(geo_advice)

    advice_text = "；".join(advice_parts)

    return {
        "location_wx": loc_wx,
        "direction": direction,
        "geo_features": geo_features,
        "geo_modifiers": geo_modifiers,
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