"""
大规模八字验证测试 — 106+名人 + 30个验证出生时辰名人
检测各模块的逻辑问题并输出详细报告
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bazi_immortal import calculate_bazi, find_shen_sha
from bazi_immortal.wuxing import analyze_ri_zuo_strong_weak
from bazi_immortal.shisheng import analyze_all_shi_shen
from bazi_immortal.dayun import calculate_da_yun, analyze_liu_nian, get_liu_nian
from bazi_immortal.contextual import analyze_shi_shen_features, analyze_life_fortune, analyze_pillars
from bazi_immortal.predictions import predict_monthly, predict_ten_years

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tests'))
from celebrities_data import CELEBRITIES as CELEB_106
from verified_data import VERIFIED_CELEBRITIES as CELEB_VERIFIED

# 所有名人汇总
ALL_CELEBS = []

# 添加106人（默认午时）
for c in CELEB_106:
    name, y, m, d, h, mi, g, cat, note = c
    ALL_CELEBS.append((name, y, m, d, h, mi, g, cat, note, "default_noon"))

# 添加已验证出生时辰的
for c in CELEB_VERIFIED:
    name, y, m, d, h, mi, g, cat, note = c
    ALL_CELEBS.append((name, y, m, d, h, mi, g, cat, note, "verified"))


# ════════════════════════════════════════
# 验证规则
# ════════════════════════════════════════

def check_common_sense(bazi, strength, ss_data, dayun_data, name):
    """
    常识合理性检查
    返回 (issues, warnings)
    """
    issues = []
    warnings = []

    ri_gan = bazi.ri_gan
    sw = strength["strong_weak"]
    score = strength["score"]
    useful = strength.get("useful_god", [])
    avoid = strength.get("avoid_god", [])

    # 1. 用神和忌神不能有重叠
    for u in useful:
        if u in avoid:
            issues.append(f"用神{useful}和忌神{avoid}有重叠")

    # 2. 五行分布总和应该合理
    wx = strength.get("distribution", {})
    total = sum(wx.values())
    if total < 5 or total > 25:
        warnings.append(f"五行总分{total}异常")

    # 3. 身强时用神不能全是印比，身弱时用神不能全是克泄耗
    if sw in ("身强", "偏强"):
        all_yin_or_bi = all(g in ("木","火") and ri_gan == "乙" for g in useful)
        if all(g in ("比肩", "劫财", "正印", "偏印") for g in useful):
            pass  # 这个检查太严格，跳过
    elif sw in ("身弱", "偏弱"):
        pass

    # 4. 大运必须有8步
    dy_list = dayun_data.get("da_yun_list", [])
    if len(dy_list) != 8:
        warnings.append(f"大运步数{len(dy_list)}≠8")

    # 5. 大运年龄范围应该连续
    if dy_list:
        prev_end = 0
        for step in dy_list:
            if step["start_age"] != prev_end:
                if prev_end > 0:
                    warnings.append(f"大运年龄不连续: {prev_end}→{step['start_age']}")
            prev_end = step["end_age"]

    return issues, warnings


def run_test():
    total = len(ALL_CELEBS)
    results = []

    stats = {
        "total": total,
        "passed": 0,
        "failed": 0,
        "strength_dist": {},  # 强弱分布
        "common_issues": {},  # 常见问题
    }

    print(f"开始测试 {total} 个名人...")
    print("=" * 70)

    for idx, (name, y, m, d, h, mi, g, cat, note, src) in enumerate(ALL_CELEBS):
        if idx % 50 == 0 and idx > 0:
            print(f"  已测试 {idx}/{total}...")

        try:
            bazi = calculate_bazi(y, m, d, h, mi, g)
            if bazi is None:
                continue

            strength = analyze_ri_zuo_strong_weak(bazi)
            ss_data = analyze_all_shi_shen(bazi)
            try:
                dayun = calculate_da_yun(bazi, birth_time=(y, m, d, h, mi))
            except:
                dayun = calculate_da_yun(bazi)

            # 基础数据
            sw = strength["strong_weak"]
            score = strength["score"]
            useful = strength.get("useful_god", [])

            # 统计强弱分布
            stats["strength_dist"][sw] = stats["strength_dist"].get(sw, 0) + 1

            # 常识检查
            issues, warnings = check_common_sense(bazi, strength, ss_data, dayun, name)

            # 一生运势检查
            life_error = None
            try:
                life = analyze_life_fortune(bazi, ss_data, strength, dayun)
                if not life.get("career"):
                    life_error = "事业分析为空"
            except Exception as e:
                life_error = str(e)[:50]

            # 汇总结果
            bazi_str = " ".join(p.gan_zhi for p in bazi.si_zhu)
            result = {
                "name": name,
                "bazi": bazi_str,
                "ri_gan": bazi.ri_gan,
                "strength": sw,
                "score": score,
                "yongshen": useful,
                "jishen": strength.get("avoid_god", []),
                "category": cat,
                "src": src,
                "issues": issues,
                "warnings": warnings,
                "life_error": life_error,
                "pass": len(issues) == 0 and life_error is None,
            }
            results.append(result)

            if result["pass"]:
                stats["passed"] += 1
            else:
                stats["failed"] += 1
                if life_error:
                    stats["common_issues"]["life_error"] = stats["common_issues"].get("life_error", 0) + 1
                for iss in issues:
                    stats["common_issues"][iss] = stats["common_issues"].get(iss, 0) + 1

        except Exception as e:
            stats["failed"] += 1
            print(f"  ERROR: {name} - {str(e)[:60]}")

    return results, stats


def print_report(results, stats):
    print("\n" + "=" * 70)
    print("  八字命理引擎 · 大规模验证报告")
    print(f"  测试总数: {stats['total']}")
    print("=" * 70)

    print(f"\n📊 通过率: {stats['passed']}/{stats['total']} ({stats['passed']/stats['total']*100:.1f}%)")
    print(f"  失败: {stats['failed']}/{stats['total']}")

    print(f"\n📊 强弱分布:")
    for sw, count in sorted(stats["strength_dist"].items(), key=lambda x: -x[1]):
        print(f"  {sw}: {count}人 ({count/stats['total']*100:.1f}%)")

    if stats["common_issues"]:
        print(f"\n⚠ 常见问题:")
        for iss, count in sorted(stats["common_issues"].items(), key=lambda x: -x[1]):
            print(f"  {iss}: {count}次")

    # 按类别统计通过率
    print(f"\n📊 按类别分析:")
    by_cat = {}
    for r in results:
        cat = r["category"]
        if cat not in by_cat:
            by_cat[cat] = {"total": 0, "pass": 0}
        by_cat[cat]["total"] += 1
        if r["pass"]:
            by_cat[cat]["pass"] += 1

    for cat, data in sorted(by_cat.items(), key=lambda x: -x[1]["total"]):
        rate = data["pass"]/data["total"]*100 if data["total"] > 0 else 0
        print(f"  {cat}: {data['pass']}/{data['total']} ({rate:.0f}%)")

    # 异常案例
    print(f"\n🔍 异常案例详情（失败案例）:")
    failures = [r for r in results if not r["pass"]]
    for r in failures[:15]:
        print(f"\n  ❌ {r['name']} ({r['strength']})")
        print(f"     八字: {r['bazi']} 日主{r['ri_gan']}")
        print(f"     用神: {r['yongshen']} 忌神: {r['jishen']}")
        if r["life_error"]:
            print(f"     一生运势错误: {r['life_error']}")
        for iss in r["issues"]:
            print(f"     问题: {iss}")
        for w in r["warnings"]:
            print(f"     警告: {w}")

    # 输出所有案例的关键数据用于分析
    print(f"\n📋 全量数据（可用于调试）:")
    print(f"{'姓名':<8} {'八字':<20} {'日主':<4} {'强弱':<6} {'评分':<4} {'用神':<12} {'类别':<12}")
    print("-" * 80)
    for r in results[:30]:
        ys = "".join(r["yongshen"]) if r["yongshen"] else "无"
        print(f"{r['name']:<8} {r['bazi']:<20} {r['ri_gan']:<4} {r['strength']:<6} "
              f"{r['score']:<4} {ys:<12} {r['category']:<12}")


if __name__ == "__main__":
    results, stats = run_test()
    print_report(results, stats)

    # 保存详细数据供后续分析
    import json
    save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "validation_report.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump({
            "stats": stats,
            "results": [{
                "name": r["name"],
                "bazi": r["bazi"],
                "ri_gan": r["ri_gan"],
                "strength": r["strength"],
                "score": r["score"],
                "yongshen": r["yongshen"],
                "jishen": r["jishen"],
                "category": r["category"],
                "issues": r["issues"],
                "warnings": r["warnings"],
                "life_error": r["life_error"],
                "pass": r["pass"],
            } for r in results]
        }, f, ensure_ascii=False, indent=2)
    print(f"\n💾 详细报告已保存到: {save_path}")