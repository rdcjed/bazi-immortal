"""
八字命理引擎验证测试
包含各种命例验证，确保推算准确性
"""

import sys
sys.path.insert(0, "/root/bazi-immortal")

from bazi_immortal import (
    calculate_bazi, bazi_to_string,
    analyze_ri_zuo_strong_weak, analyze_all_shi_shen,
    find_shen_sha,
)


def test_case(name, year, month, day, hour, minute, gender, assertions):
    """单个测试用例"""
    bazi = calculate_bazi(year, month, day, hour, minute, gender)
    wx = analyze_ri_zuo_strong_weak(bazi)
    ss = analyze_all_shi_shen(bazi)
    shensha = find_shen_sha(bazi)

    print(f"\n{'='*60}")
    print(f"  📋 {name}")
    print(f"  八字：{' '.join(p.gan_zhi for p in bazi.si_zhu)}")
    print(f"  日主：{bazi.ri_gan}{'('+ wx['ri_wx'] + ')'}  性别：{gender}")
    print(f"  月令：{wx['monthly_state']}  季节：{wx.get('season', '?')}")
    print(f"  强弱：{wx['strong_weak']}（得分{wx['score']}）")
    print(f"  用神：{'/'.join(wx['useful_god'])}  忌神：{'/'.join(wx['avoid_god'])}")
    
    # 十神简要
    top_ss = ss["top_shi_shen"][:3]
    top_str = ", ".join(f"{s}={c}" for s, c in top_ss if c > 0)
    print(f"  十神：{ss['summary'][:60]}...")
    
    # 神煞
    sha_count = len(shensha)
    sha_names = "、".join(shensha.keys())[:50]
    print(f"  神煞：{sha_count}个（{sha_names}...）")
    
    # 验证断言
    all_pass = True
    for key, expected in assertions.items():
        actual = None
        if key == "strong_weak":
            actual = wx["strong_weak"]
        elif key == "useful_god":
            actual = wx["useful_god"]
        elif key == "avoid_god":
            actual = wx["avoid_god"]
        elif key == "score_min":
            actual = "≥" + str(expected) if wx["score"] >= expected else "<" + str(expected)
            if wx["score"] >= expected:
                continue  # pass
            all_pass = False
            print(f"  ❌ {key}: 得分{wx['score']} < {expected}")
            continue
        elif key == "has_shensha":
            all_ok = all(s in shensha for s in expected)
            if not all_ok:
                missing = [s for s in expected if s not in shensha]
                print(f"  ❌ 缺少神煞：{missing}")
                all_pass = False
            continue
        elif key == "not_has_shensha":
            found = [s for s in expected if s in shensha]
            if found:
                print(f"  ❌ 意外出现神煞：{found}")
                all_pass = False
            continue
        elif key == "score_max":
            if wx["score"] <= expected:
                continue
            all_pass = False
            print(f"  ❌ {key}: 得分{wx['score']} > {expected}")
            continue

        if actual == expected:
            continue
        all_pass = False
        print(f"  ❌ {key}: 期望={expected}，实际={actual}")

    if all_pass:
        print(f"  ✅ 全部通过")
    return all_pass


def run_tests():
    """运行所有测试用例"""
    passed = 0
    failed = 0
    tests = []

    # ─── 测试用例列表 ───
    # 注：断言只验证有把握的规则（如从强格的用神），强弱判断因具体八字而异

    # 1. 毛泽东：1893-12-26 辰时 
    tests.append(("毛泽东", 1893, 12, 26, 7, 0, "男", {
        "has_shensha": ["天乙贵人"],
    }))

    # 2. 申月乙木，绝地
    tests.append(("申月乙木", 2003, 8, 20, 6, 0, "男", {}))

    # 3. 丑月土旺（从强格 — 全局印比极旺）
    tests.append(("丑月从强格", 2000, 1, 1, 8, 0, "女", {
        "strong_weak": "从强",
        "useful_god": ["土", "火"],
        "avoid_god": ["木", "水"],
    }))

    # 4. 寅月甲木（临官位）
    tests.append(("寅月甲木", 1964, 2, 15, 10, 0, "男", {
        "strong_weak": "身强",
    }))

    # 5. 1986年5月
    tests.append(("巳月生人", 1986, 5, 20, 12, 0, "男", {}))

    # 6. 1995年12月子时
    tests.append(("冬月子时", 1995, 12, 15, 23, 30, "女", {}))

    # 7. 子月丙火
    tests.append(("子月丙火", 1990, 12, 1, 12, 0, "男", {}))

    # 8. 辰月戊土
    tests.append(("辰月生人", 1988, 4, 10, 15, 0, "男", {}))

    # 9. 闰年测试：2000-02-29
    tests.append(("闰年出生", 2000, 2, 29, 6, 0, "女", {}))

    # 10. 亥月壬水（临官位）
    tests.append(("亥月壬水", 1970, 11, 8, 3, 0, "男", {}))

    # 11. 午月丁火
    tests.append(("午月丁火", 1992, 6, 15, 14, 0, "女", {}))

    # 12. 未月己土
    tests.append(("未月己土", 1998, 7, 20, 9, 0, "男", {}))

    # 13. 酉月辛金
    tests.append(("酉月辛金", 2005, 9, 10, 17, 0, "女", {}))

    # 14. 卯月卯时
    tests.append(("卯月卯时", 1996, 3, 15, 5, 0, "男", {}))

    # 15. 子时出生（跨天）
    tests.append(("子时出生", 2001, 8, 8, 23, 30, "女", {}))

    # ─── 运行测试 ───
    for name, *args in tests:
        try:
            ok = test_case(name, *args)
            if ok:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n  ❌ {name} 抛出异常：{e}")
            import traceback
            traceback.print_exc()
            failed += 1

    # ─── 汇总 ───
    print(f"\n{'='*60}")
    print(f"  测试汇总")
    print(f"  ✅ 通过：{passed}")
    print(f"  ❌ 失败：{failed}")
    print(f"  总共：{len(tests)}")
    print(f"{'='*60}")
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)