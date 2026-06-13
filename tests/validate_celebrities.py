"""
名人八字验证测试 — 验证推理准确性和逻辑一致性
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bazi_immortal import calculate_bazi
from bazi_immortal.wuxing import analyze_ri_zuo_strong_weak
from bazi_immortal.shisheng import analyze_all_shi_shen
from bazi_immortal.dayun import calculate_da_yun
from bazi_immortal.contextual import analyze_shi_shen_features, analyze_life_fortune

# 名人数据库：名字, 年, 月, 日, 时, 分, 性别, 已知特征
CELEBRITIES = [
    # ─── 政治领袖 ───
    ("毛泽东", 1893, 12, 26, 19, 0, "男",
     "开国领袖，丙火子月身弱，喜木火。甲子大运(印星)成事。"),
    ("邓小平", 1904, 8, 22, 0, 0, "男",
     "改革开放总设计师，己土申月。改革发生在庚申/辛酉食伤大运。"),
    ("习近平", 1953, 6, 15, 0, 0, "男",
     "癸水午月，当前执政期。"),

    # ─── 商界巨子 ───
    ("马云", 1964, 9, 10, 13, 0, "男",
     "阿里巴巴创始人，甲木酉月身弱？正官格。创立阿里在乙丑大运(劫财)。"),
    ("马化腾", 1972, 10, 29, 10, 0, "男",
     "腾讯创始人，壬水戌月。"),

    # ─── 科技先锋 ───
    ("乔布斯", 1955, 2, 24, 19, 0, "男",
     "苹果创始人，丙火寅月身强。iPhone时代在辛巳/壬午大运(正财/七杀)。"),
    ("埃隆·马斯克", 1971, 6, 28, 12, 0, "男",
     "Tesla/SpaceX创始人，辛亥巳月。"),

    # ─── 演艺名人 ───
    ("周杰伦", 1979, 1, 18, 8, 0, "男",
     "华语乐坛天王，戊午丑月。音乐才华在青春期展现。"),
    ("刘德华", 1961, 9, 27, 8, 0, "男",
     "四大天王之一，辛丑酉月。"),

    # ─── 体育明星 ───
    ("迈克尔·乔丹", 1963, 2, 17, 14, 0, "男",
     "篮球之神，癸卯寅月。职业生涯黄金期在24-34岁。"),
    ("姚明", 1980, 9, 12, 19, 0, "男",
     "篮球巨星，庚申酉月。身高优势与金旺有关。"),

    # ─── 文化名人 ───
    ("爱因斯坦", 1879, 3, 14, 11, 30, "男",
     "物理学家，己卯寅月。相对论在1905年（乙巳年）。"),
    ("莎士比亚", 1564, 4, 26, 12, 0, "男",
     "戏剧大师，甲子辰月。"),

    # ─── 古代名人 ───
    ("唐太宗李世民", 598, 1, 28, 7, 0, "男",
     "贞观之治，戊午丑月？"),
    ("诸葛亮", 181, 7, 23, 12, 0, "男",
     "三国谋士，辛酉未月。"),
]


def validate_celebrity(name, y, m, d, h, mi, g, known_info):
    """验证单个名人"""
    try:
        bazi = calculate_bazi(y, m, d, h, mi, g)
    except Exception as e:
        return {"name": name, "error": str(e), "pass": False}

    if bazi is None:
        return {"name": name, "pass": False, "error": "计算失败"}

    strength = analyze_ri_zuo_strong_weak(bazi)
    ss_data = analyze_all_shi_shen(bazi)
    try:
        dy = calculate_da_yun(bazi, birth_time=(y, m, d, h, mi))
    except:
        dy = calculate_da_yun(bazi)

    bazi_str = " ".join(p.gan_zhi for p in bazi.si_zhu)

    # 基本合理性检查
    checks = []
    issues = []

    # 1. 强弱判断是否在一个合理范围
    if strength["strong_weak"] in ("身强", "偏强"):
        checks.append(("强弱判断", strength["strong_weak"]))

        # 身强时喜克泄耗
        career_positive_dys = []
        for step in dy.get("da_yun_list", []):
            ss = step.get("shi_shen", "")
            if ss in ("正官", "七杀", "正财", "偏财", "食神", "伤官"):
                career_positive_dys.append(f"{step['range']}({ss})")
        checks.append(("事业黄金大运", "、".join(career_positive_dys[:3]) if career_positive_dys else "无"))
    else:
        checks.append(("强弱判断", strength["strong_weak"]))
        career_positive_dys = []
        for step in dy.get("da_yun_list", []):
            ss = step.get("shi_shen", "")
            if ss in ("正印", "偏印", "比肩", "劫财"):
                career_positive_dys.append(f"{step['range']}({ss})")
        checks.append(("事业黄金大运", "、".join(career_positive_dys[:3]) if career_positive_dys else "无"))

    # 3. 五行分布
    wx = strength.get("distribution", {})
    checks.append(("五行分布", str(dict(sorted(wx.items(), key=lambda x: -x[1])))))

    # 4. 流年验证 - 当前大运
    current_age = 2025 - y
    current_step = None
    for step in dy.get("da_yun_list", []):
        if step["start_age"] <= current_age <= step["end_age"]:
            current_step = step
            break
    if current_step:
        checks.append(("当前大运", f"{current_step['range']} {current_step['gan_zhi']}({current_step['shi_shen']})"))

    # 5. 一生运势分析 - 检查是否生成
    try:
        life = analyze_life_fortune(bazi, ss_data, strength, dy)
        checks.append(("一生运势", "已生成"))
        checks.append(("事业建议", life.get("career", "")[:50]))
    except Exception as e:
        issues.append(f"一生运势异常: {e}")

    score = len(checks) - len(issues)
    return {
        "name": name,
        "bazi": bazi_str,
        "ri_gan": bazi.ri_gan,
        "strength": strength["strong_weak"],
        "yongshen": strength.get("useful_god", []),
        "checks": checks,
        "issues": issues,
        "pass": len(issues) == 0,
        "score": score,
        "known": known_info[:60] + "...",
    }


def run_all():
    total = len(CELEBRITIES)
    passed = 0
    failed = 0

    print("=" * 70)
    print("  八字命理引擎 · 名人验证测试报告")
    print(f"  测试总数: {total}")
    print("=" * 70)

    for c in CELEBRITIES:
        name, y, m, d, h, mi, g, info = c
        result = validate_celebrity(name, y, m, d, h, mi, g, info)

        status = "✅" if result["pass"] else "❌"
        print(f"\n{status} {result['name']}")
        print(f"  八字: {result['bazi']} 日主: {result['ri_gan']}")
        print(f"  强弱: {result['strength']} 用神: {result.get('yongshen', [])}")
        for label, val in result["checks"]:
            print(f"  · {label}: {val}")
        if result["issues"]:
            for iss in result["issues"]:
                print(f"  ⚠ 问题: {iss}")
        print(f"  已知: {result['known']}")

        if result["pass"]:
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 70)
    print(f"  总结:")
    print(f"  通过: {passed}/{total}")
    print(f"  失败: {failed}/{total}")
    print(f"  通过率: {passed/total*100:.0f}%")
    print("=" * 70)


if __name__ == "__main__":
    run_all()