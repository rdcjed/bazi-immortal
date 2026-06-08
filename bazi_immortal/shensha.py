"""
神煞推算模块
根据年干/日干/年支推算各种神煞
"""

from typing import Dict, List, Tuple, Optional
from .constants import (
    TIAN_GAN, DI_ZHI, DZ_INDEX, TG_INDEX,
    DZ_CANG_GAN, TG_WU_XING,
)
from .calculator import BaZi

# 神煞基础规则数据库
# 格式: {神煞名: {"method": 查找依据, "rule": 规则字典, "meaning": 含义}}

SHEN_SHA_DB = {
    "天乙贵人": {
        "method": "年干/日干",
        "rule": {
            "甲": ["丑", "未"], "乙": ["子", "申"], "丙": ["亥", "酉"],
            "丁": ["亥", "酉"], "戊": ["丑", "未"], "己": ["子", "申"],
            "庚": ["丑", "未"], "辛": ["午", "寅"], "壬": ["巳", "卯"],
            "癸": ["巳", "卯"],
        },
        "meaning": "最大的贵人星，逢凶化吉。八字带天乙贵人的人一生贵人运强，危难时有人相助。",
    },
    "文昌贵人": {
        "method": "年干/日干",
        "rule": {
            "甲": ["巳"], "乙": ["午"], "丙": ["申"], "丁": ["酉"],
            "戊": ["申"], "己": ["酉"], "庚": ["亥"], "辛": ["子"],
            "壬": ["寅"], "癸": ["卯"],
        },
        "meaning": "文运昌盛，聪明好学。文昌入命的人读书好、有才学，适合从事文化教育工作。",
    },
    "禄神": {
        "method": "日干",
        "rule": {
            "甲": ["寅"], "乙": ["卯"], "丙": ["巳"], "丁": ["午"],
            "戊": ["巳"], "己": ["午"], "庚": ["申"], "辛": ["酉"],
            "壬": ["亥"], "癸": ["子"],
        },
        "meaning": "福禄之所在。禄神所在的地支为财禄之源，代表稳定的收入和福气。",
    },
    "桃花（咸池）": {
        "method": "年支/日支",
        "rule": {
            "寅": ["卯"], "午": ["卯"], "戌": ["卯"],
            "巳": ["午"], "酉": ["午"], "丑": ["午"],
            "申": ["酉"], "子": ["酉"], "辰": ["酉"],
            "亥": ["子"], "卯": ["子"], "未": ["子"],
        },
        "meaning": "异性缘佳，感情丰富。桃花星入命的人魅力足，但也容易有感情纠葛。",
    },
    "驿马": {
        "method": "年支/日支",
        "rule": {
            "寅": ["申"], "午": ["申"], "戌": ["申"],
            "巳": ["亥"], "酉": ["亥"], "丑": ["亥"],
            "申": ["寅"], "子": ["寅"], "辰": ["寅"],
            "亥": ["巳"], "卯": ["巳"], "未": ["巳"],
        },
        "meaning": "奔波变动，远行出差。驿马入命的人一生多动少静，适合在外发展，也意味着事业变动快。",
    },
    "华盖": {
        "method": "年支/日支",
        "rule": {
            "寅": ["戌"], "午": ["戌"], "戌": ["戌"],
            "巳": ["丑"], "酉": ["丑"], "丑": ["丑"],
            "申": ["辰"], "子": ["辰"], "辰": ["辰"],
            "亥": ["未"], "卯": ["未"], "未": ["未"],
        },
        "meaning": "孤高聪慧，艺术修行。华盖入命的人聪明而有才华，但性格孤独，多与宗教、艺术有缘。",
    },
    "羊刃": {
        "method": "日干",
        "rule": {
            "甲": ["卯"], "丙": ["午"], "戊": ["午"],
            "庚": ["酉"], "壬": ["子"],
        },
        "meaning": "刚强勇猛，易招是非。羊刃入命的人性格刚烈、敢作敢当，但也容易与人冲突，需注意人际关系。",
    },
    "劫煞": {
        "method": "年支",
        "rule": {
            "申": ["亥"], "子": ["亥"], "辰": ["亥"],
            "寅": ["巳"], "午": ["巳"], "戌": ["巳"],
            "巳": ["申"], "酉": ["申"], "丑": ["申"],
            "亥": ["寅"], "卯": ["寅"], "未": ["寅"],
        },
        "meaning": "劫财破财，需防小人。劫煞入命的人容易遇到小人、意外破财，投资合作需谨慎。",
    },
    "灾煞": {
        "method": "年支",
        "rule": {
            "申": ["子"], "子": ["子"], "辰": ["子"],
            "寅": ["午"], "午": ["午"], "戌": ["午"],
            "巳": ["酉"], "酉": ["酉"], "丑": ["酉"],
            "亥": ["卯"], "卯": ["卯"], "未": ["卯"],
        },
        "meaning": "意外灾祸，需谨慎行事。灾煞入命年份易有意外伤害，做事需多留个心眼。",
    },
    "天德": {
        "method": "月支",
        "rule": {
            "寅": ["丁"], "卯": ["申"], "辰": ["壬"], "巳": ["辛"],
            "午": ["亥"], "未": ["甲"], "申": ["癸"], "酉": ["寅"],
            "戌": ["丙"], "亥": ["乙"], "子": ["巳"], "丑": ["庚"],
        },
        "meaning": "上天恩德，逢凶化吉。天德入命的人一生多遇贵人，灾祸可化解。",
    },
    "月德": {
        "method": "月支（三合局）",
        "rule": {
            "寅": ["丙"], "午": ["丙"], "戌": ["丙"],   # 寅午戌→丙
            "亥": ["甲"], "卯": ["甲"], "未": ["甲"],   # 亥卯未→甲
            "申": ["壬"], "子": ["壬"], "辰": ["壬"],   # 申子辰→壬
            "巳": ["庚"], "酉": ["庚"], "丑": ["庚"],   # 巳酉丑→庚
        },
        "meaning": "月之德神，贵人相助。月德入命者仁慈宽厚，一生少灾祸。",
    },
    "煞贡/人专/直星": {
        "method": "特殊情况",
        "rule": {},
        "meaning": "道家常用的出行吉时神煞，需要具体日时推算。",
    },
}


def find_shen_sha(bazi: BaZi) -> Dict[str, Dict]:
    """
    扫描八字四柱，找出命局中所有的神煞

    Returns: {神煞名: {位置说明, 含义}}
    """
    result = {}
    ri_gan = bazi.ri_gan
    year_gan = bazi.year_pillar.tian_gan
    year_zhi = bazi.year_pillar.di_zhi
    month_zhi = bazi.month_pillar.di_zhi
    all_zhi = bazi.zhi_list
    all_gan = bazi.gan_list

    # 按年干/日干查找的神煞
    for shen_name, info in SHEN_SHA_DB.items():
        if info["method"].startswith("年干") or info["method"].startswith("日干"):
            # 同时用年干和日干查找
            for key_gan in [year_gan, ri_gan]:
                if key_gan in info["rule"]:
                    target_zhi = info["rule"][key_gan]
                    for zhi in target_zhi:
                        if zhi in all_zhi:
                            positions = []
                            for p in bazi.si_zhu:
                                if p.di_zhi == zhi:
                                    positions.append(p.label)
                            if shen_name not in result:
                                result[shen_name] = {
                                    "zhi": zhi,
                                    "positions": positions,
                                    "meaning": info["meaning"],
                                }
            continue

        # 按年支查找的神煞
        elif info["method"] == "年支":
            if year_zhi in info["rule"]:
                target_zhi = info["rule"][year_zhi]
                for zhi in target_zhi:
                    if zhi in all_zhi:
                        positions = [p.label for p in bazi.si_zhu if p.di_zhi == zhi]
                        result[shen_name] = {
                            "zhi": zhi,
                            "positions": positions,
                            "meaning": info["meaning"],
                        }
            continue

        # 按月支查找的神煞
        elif info["method"].startswith("月支"):
            if month_zhi in info["rule"]:
                if isinstance(info["rule"][month_zhi], list):
                    target_gans = info["rule"][month_zhi]
                    for gan in target_gans:
                        if gan in all_gan:
                            positions = [p.label for p in bazi.si_zhu if p.tian_gan == gan]
                            result[shen_name] = {
                                "zhi": zhi if 'zhi' in locals() else "",
                                "positions": positions,
                                "meaning": info["meaning"],
                            }
                else:
                    # 月德的特殊处理（三合局）
                    target_gan = info["rule"][month_zhi]
                    if target_gan in all_gan:
                        positions = [p.label for p in bazi.si_zhu if p.tian_gan == target_gan]
                        result[shen_name] = {
                            "zhi": "",
                            "positions": positions,
                            "meaning": info["meaning"],
                        }
            continue

        # 月支三合局查找
        elif info["method"].startswith("月支（三合局）"):
            # 已在上面的逻辑中处理了
            if month_zhi in info["rule"]:
                target_gan = info["rule"][month_zhi]
                if target_gan in all_gan:
                    positions = [p.label for p in bazi.si_zhu if p.tian_gan == target_gan]
                    result[shen_name] = {
                        "zhi": "",
                        "positions": positions,
                        "meaning": info["meaning"],
                    }
            continue

    return result


def format_shen_sha(result: Dict) -> str:
    """神煞结果 → 可读文本"""
    if not result:
        return "【神煞】未发现明显神煞。\n"

    parts = []
    parts.append("【神煞】")

    for shen_name, info in result.items():
        pos = "、".join(info["positions"])
        parts.append(f"· {shen_name}（{shen_name}）：在{pos}，{info['meaning']}")

    return "\n".join(parts)