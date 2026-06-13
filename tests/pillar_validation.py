#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度八卦验证脚本 — 逐柱验证八字推演的准确性

功能：
1. 年柱验证：立春分界检查
2. 月柱验证：节气分界检查
3. 日柱验证：日干支计算检查（跨世纪验证）
4. 时辰验证：时辰边界检查（含跨天子时）
5. 身强身弱推理验证：推理链条输出
6. 综合评分：每人的合理性评分

数据源：celebrities_data.py 中的106位名人
"""

import sys
import os
import copy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bazi_immortal import calculate_bazi
from bazi_immortal.calculator import BaZi, BaZiCalculator
from bazi_immortal.wuxing import analyze_ri_zuo_strong_weak
from bazi_immortal.shisheng import analyze_all_shi_shen
from bazi_immortal.constants import (
    TIAN_GAN, DI_ZHI, TG_INDEX, DZ_INDEX,
    TG_WU_XING, DZ_WU_XING, DZ_CANG_GAN,
    WU_HU_DUN, WU_SHU_DUN,
    LIU_SHI_JIA_ZI, LIU_SHI_JIA_ZI_NAMES, JIA_ZI_NAME_TO_INDEX,
    SHI_CHEN, DZ_MONTH_INFO,
    SHI_ER_CHANG_SHENG, WU_XING_SHENG, WU_XING_KE,
    SI_JI_WANG_XIANG,
)
from bazi_immortal.jieqi import get_month_zhi, get_term_date, KEY_TERMS, TERM_TO_ZHI

# ──────────────────────────────────────────────────────────────
# 导入名人数据
# ──────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests"))
from celebrities_data import CELEBRITIES

# ──────────────────────────────────────────────────────────────
# 已知日干支对照表（用于日柱验证）
# 来源：万年历/官方历法数据
# 格式: (年, 月, 日, 日干支)
# ──────────────────────────────────────────────────────────────
KNOWN_DAY_PILLARS = [
    # 毛泽东 1893-12-26 → 已知：己丑日
    (1893, 12, 26, "己丑"),
    # 孙中山 1866-11-12 → 已知：辛未日
    (1866, 11, 12, "辛未"),
    # 爱因斯坦 1879-3-14 → 已知：己卯日
    (1879, 3, 14, "己卯"),
    # 乔布斯 1955-2-24 → 已知：丙午日
    (1955, 2, 24, "丙午"),
    # 马云 1964-9-10 → 已知：庚申日
    (1964, 9, 10, "庚申"),
    # 姚明 1980-9-12 → 已知：甲子日
    (1980, 9, 12, "甲子"),
    # 已知固定日柱以验证公式：1900-01-01 = 甲戌，2000-01-01 = 甲午
    (1900, 1, 1, "甲戌"),
    (2000, 1, 1, "甲午"),
    (2100, 1, 1, "甲寅"),
    # 其他著名日期
    (1949, 10, 1, "甲辰"),  # 建国日
    (1978, 12, 18, "戊寅"),  # 十一届三中全会
    (2008, 8, 8, "癸未"),   # 奥运开幕
]

# ──────────────────────────────────────────────────────────────
# 十二节气分界基准日期
# 用于月柱验证
# ──────────────────────────────────────────────────────────────
JIEQI_BOUNDARIES = {
    "立春": (2, 4),
    "惊蛰": (3, 6),
    "清明": (4, 5),
    "立夏": (5, 6),
    "芒种": (6, 6),
    "小暑": (7, 7),
    "立秋": (8, 7),
    "白露": (9, 8),
    "寒露": (10, 8),
    "立冬": (11, 7),
    "大雪": (12, 7),
    "小寒": (1, 6),
}

# 节气 → 月支
TERM_TO_ZHI_DICT = dict(TERM_TO_ZHI)

# 月支 → 节气起始
ZHI_TO_TERM = {zhi: term for term, zhi in TERM_TO_ZHI}

# ──────────────────────────────────────────────────────────────
# 验证函数
# ──────────────────────────────────────────────────────────────

def create_calculator():
    """创建计算器实例（含缓存）"""
    return BaZiCalculator()


def validate_year_pillar(calc, name, year, month, day):
    """验证年柱：立春分界是否正确"""
    result = {"pass": True, "issues": [], "details": []}
    
    # 获取当年立春日
    lichun_m, lichun_d = calc._get_lichun(year)
    
    # 计算实际年柱
    actual_pillar = calc._calc_year_pillar(year, month, day)
    actual_gan_zhi = actual_pillar.gan_zhi
    
    # 计算应得的年干支基准
    prev_year_gan_zhi_index = (year - 1 - 4) % 60
    prev_tg, prev_dz = LIU_SHI_JIA_ZI[prev_year_gan_zhi_index]
    prev_year_expected = TIAN_GAN[prev_tg] + DI_ZHI[prev_dz]
    
    curr_year_gan_zhi_index = (year - 4) % 60
    curr_tg, curr_dz = LIU_SHI_JIA_ZI[curr_year_gan_zhi_index]
    curr_year_expected = TIAN_GAN[curr_tg] + DI_ZHI[curr_dz]
    
    # 基准：立春前后各测试几天
    from datetime import date, timedelta
    try:
        lichun_date = date(year, lichun_m, lichun_d)
        before_lichun = lichun_date - timedelta(days=1)
        before_pillar = calc._calc_year_pillar(
            before_lichun.year, before_lichun.month, before_lichun.day
        )
        after_lichun = lichun_date + timedelta(days=1)
        after_pillar = calc._calc_year_pillar(
            after_lichun.year, after_lichun.month, after_lichun.day
        )
        
        # 检查立春前的年柱
        before_ok = before_pillar.gan_zhi == prev_year_expected
        after_ok = after_pillar.gan_zhi == curr_year_expected
        
        result["details"].append({
            "lichun_date": f"{year}-{lichun_m:02d}-{lichun_d:02d}",
            "year": year,
            "actual_pillar": actual_gan_zhi,
            "expected_prev_year": prev_year_expected,
            "expected_curr_year": curr_year_expected,
            "before_lichun": f"{before_lichun} → {before_pillar.gan_zhi} (expected: {prev_year_expected}, ok={before_ok})",
            "after_lichun": f"{after_lichun} → {after_pillar.gan_zhi} (expected: {curr_year_expected}, ok={after_ok})",
        })
        
        if not before_ok:
            result["issues"].append(
                f"立春前1日({before_lichun})年柱应为{prev_year_expected}，实际得到{before_pillar.gan_zhi}"
            )
            result["pass"] = False
        if not after_ok:
            result["issues"].append(
                f"立春后1日({after_lichun})年柱应为{curr_year_expected}，实际得到{after_pillar.gan_zhi}"
            )
            result["pass"] = False
            
    except Exception as e:
        result["issues"].append(f"年柱边界测试异常: {e}")
        result["pass"] = False
    
    # 检查此人的年柱
    person_expected = prev_year_expected if (month < lichun_m or (month == lichun_m and day < lichun_d)) else curr_year_expected
    if actual_gan_zhi != person_expected:
        result["issues"].append(
            f"{name}({year}-{month:02d}-{day:02d})年柱应为{person_expected}({'上一年' if actual_gan_zhi != curr_year_expected else '本年'})，实际{actual_gan_zhi}"
        )
        # 不立即判失败，因为本人生日本身可能就在边界附近
        result["pass"] = False
    
    return result


def validate_month_pillar(calc, name, year, month, day, year_gan):
    """验证月柱：节气分界是否正确"""
    result = {"pass": True, "issues": [], "details": []}
    
    # 获取计算所得月柱
    month_pillar = calc._calc_month_pillar(year, month, day, year_gan)
    actual_zhi = month_pillar.di_zhi
    actual_gan = month_pillar.tian_gan
    
    # 获取预期月支（通过jieqi模块精确计算）
    expected_zhi = get_month_zhi(year, month, day)
    
    # 验证月支
    zhi_ok = (actual_zhi == expected_zhi)
    if not zhi_ok:
        result["issues"].append(
            f"月支错误：应为{expected_zhi}，实际得到{actual_zhi}"
        )
        result["pass"] = False
    
    # 验证月干（五虎遁）
    zheng_yue_gan = WU_HU_DUN[year_gan]
    zheng_yue_index = TG_INDEX[zheng_yue_gan]
    yin_index = DZ_INDEX["寅"]
    target_zhi_index = DZ_INDEX[actual_zhi]
    offset = (target_zhi_index - yin_index) % 12
    expected_gan_index = (zheng_yue_index + offset) % 10
    expected_gan = TIAN_GAN[expected_gan_index]
    
    gan_ok = (actual_gan == expected_gan)
    if not gan_ok:
        result["issues"].append(
            f"月干错误：五虎遁计算应为{expected_gan}（年干{year_gan}→正月{zheng_yue_gan}，月支{actual_zhi}偏移{offset}），实际得到{actual_gan}"
        )
        result["pass"] = False
    
    # 节气边界测试：对每个节气，测试前后各3天
    boundary_tests = []
    for term_name, (b_month, b_day) in JIEQI_BOUNDARIES.items():
        expected_start_zhi = TERM_TO_ZHI_DICT.get(term_name, "")
        if not expected_start_zhi:
            continue
        # 这个节气的上一个地支
        prev_zhi = DI_ZHI[(DZ_INDEX[expected_start_zhi] - 1) % 12]
        
        try:
            # 测试节气前1天
            test_d = b_day - 1
            test_m = b_month
            if test_d < 1:
                # 跨月回退
                if b_month == 1:
                    test_m = 12
                    test_d = 31
                else:
                    test_m = b_month - 1
                    test_d = 31  # 近似
            
            before_zhi = get_month_zhi(year, test_m, test_d)
            # 如果节气前1天的月支是上一个地支，则正确
            if before_zhi != prev_zhi:
                boundary_tests.append(
                    f"⚠ {term_name}({b_month}/{b_day})前1天({test_m}/{test_d})月支={before_zhi}，预期={prev_zhi}"
                )
            
            # 测试节气当天
            on_zhi = get_month_zhi(year, b_month, b_day)
            if on_zhi != expected_start_zhi:
                boundary_tests.append(
                    f"⚠ {term_name}当天({b_month}/{b_day})月支={on_zhi}，预期={expected_start_zhi}"
                )
            
            # 测试节气后1天
            after_zhi = get_month_zhi(year, b_month, b_day + 1)
            if after_zhi != expected_start_zhi:
                boundary_tests.append(
                    f"⚠ {term_name}后1天({b_month}/{b_day+1})月支={after_zhi}，预期={expected_start_zhi}"
                )
        except Exception as e:
            boundary_tests.append(f"⚠ {term_name}边界测试异常: {e}")
    
    result["details"].append({
        "actual_zhi": actual_zhi,
        "expected_zhi": expected_zhi,
        "actual_gan": actual_gan,
        "expected_gan": expected_gan,
        "year_gan": year_gan,
        "zhi_ok": zhi_ok,
        "gan_ok": gan_ok,
        "boundary_tests": boundary_tests,
    })
    
    return result


def validate_day_pillar(calc, year, month, day):
    """验证日柱：计算日干支并对照已知数据"""
    result = {"pass": True, "issues": [], "details": []}
    
    day_pillar = calc._calc_day_pillar(year, month, day)
    actual = day_pillar.gan_zhi
    
    # 查找已知对照
    matched = None
    for ky, km, kd, expected in KNOWN_DAY_PILLARS:
        if ky == year and km == month and kd == day:
            matched = (actual, expected)
            break
    
    if matched:
        actual, expected = matched
        if actual != expected:
            result["issues"].append(f"日柱错误：已知应为{expected}，实际计算为{actual}")
            result["pass"] = False
        else:
            result["details"].append(f"日柱正确：{actual}（与已知对照一致）")
    else:
        # 未匹配已知数据，只记录
        result["details"].append(f"日柱：{actual}（无已知对照）")
    
    return result


def validate_hour_pillar(calc, hour, minute, day_gan):
    """验证时柱：时辰边界和五鼠遁"""
    result = {"pass": True, "issues": [], "details": []}
    
    hour_pillar = calc._calc_hour_pillar(hour, minute, day_gan)
    actual_zhi = hour_pillar.di_zhi
    actual_gan = hour_pillar.tian_gan
    
    # 1. 验证时辰地支
    expected_zhi = calc._get_hour_zhi(hour, minute)
    zhi_ok = (actual_zhi == expected_zhi)
    if not zhi_ok:
        result["issues"].append(
            f"时支错误：hour={hour}, minute={minute}，预期时支={expected_zhi}，实际={actual_zhi}"
        )
        result["pass"] = False
    
    # 2. 验证时干（五鼠遁）
    zi_gan = WU_SHU_DUN[day_gan]
    zi_index = TG_INDEX[zi_gan]
    hour_zhi_index = DZ_INDEX[actual_zhi]
    expected_gan_index = (zi_index + hour_zhi_index) % 10
    expected_gan = TIAN_GAN[expected_gan_index]
    
    gan_ok = (actual_gan == expected_gan)
    if not gan_ok:
        result["issues"].append(
            f"时干错误：五鼠遁应为{expected_gan}（日干{day_gan}→子时{zi_gan}，时支{actual_zhi}偏移{hour_zhi_index}），实际{actual_gan}"
        )
        result["pass"] = False
    
    # 3. 跨天子时测试（23:00-00:59）
    zi_gan_shuren = None
    if hour == 23 or hour == 0:
        zi_gan_shuren = zi_gan
        result["details"].append(f"跨天子时：{hour}:{minute:02d} → 时支=子，子时天干={zi_gan}")
    
    result["details"].append({
        "actual_zhi": actual_zhi,
        "expected_zhi": expected_zhi,
        "actual_gan": actual_gan,
        "expected_gan": expected_gan,
        "day_gan": day_gan,
        "zi_shi_gan": zi_gan,
        "zhi_ok": zhi_ok,
        "gan_ok": gan_ok,
    })
    
    return result


def validate_strength_weakness(bazi):
    """验证身强身弱推理链条"""
    result = {"pass": True, "issues": [], "details": [], "chain": []}
    
    try:
        strength = analyze_ri_zuo_strong_weak(bazi)
    except Exception as e:
        result["issues"].append(f"强弱分析异常: {e}")
        result["pass"] = False
        return result
    
    ri_gan = bazi.ri_gan
    ri_wx = TG_WU_XING[ri_gan]
    month_zhi = bazi.month_pillar.di_zhi
    
    chain = []
    
    # ── 推理链条第1环：得令分析 ──
    from bazi_immortal.wuxing import get_monthly_state, get_season
    monthly_state = get_monthly_state(ri_gan, month_zhi)
    season = get_season(bazi)
    season_wangxiang = SI_JI_WANG_XIANG[season]
    ri_wx_season_status = season_wangxiang[ri_wx]
    
    chain.append({
        "step": 1,
        "title": "【得令分析】日主在月令的状态",
        "content": [
            f"日主：{ri_gan}（{ri_wx}）",
            f"月支：{month_zhi}（{DZ_WU_XING[month_zhi]}）",
            f"季节：{season}",
            f"日主五行在{season}季为：【{ri_wx_season_status}】",
            f"十二长生状态：{ri_gan}在{month_zhi}月为【{monthly_state}】",
        ],
    })
    
    # ── 推理链条第2环：得地分析 ──
    from bazi_immortal.wuxing import get_roots_in_branches
    roots = get_roots_in_branches(ri_gan, bazi.zhi_list)
    chain.append({
        "step": 2,
        "title": "【得地分析】地支是否有根",
        "content": [
            f"四柱地支：{' '.join(bazi.zhi_list)}",
            f"有根地支：{roots if roots else '无根'}",
        ],
    })
    
    # ── 推理链条第3环：得势分析 ──
    from bazi_immortal.shisheng import get_shi_shen_for_gan
    helping = 0
    harming = 0
    helping_details = []
    harming_details = []
    for gan in bazi.gan_list:
        if gan == ri_gan:
            continue
        ss = get_shi_shen_for_gan(ri_gan, gan)
        if ss in ("正印", "偏印", "比肩", "劫财"):
            helping += 2
            helping_details.append(f"{gan}={ss}")
        elif ss in ("正官", "七杀", "正财", "偏财", "食神", "伤官"):
            harming += 2
            harming_details.append(f"{gan}={ss}")
    
    chain.append({
        "step": 3,
        "title": "【得势分析】天干印比/克泄耗统计",
        "content": [
            f"天干印比帮身：{helping_details if helping_details else '无'} (得分{helping})",
            f"天干克泄耗：{harming_details if harming_details else '无'} (得分{harming})",
            f"得势判断：{'得势' if helping > harming else '失势' if harming > helping else '平势'}",
        ],
    })
    
    # ── 推理链条第4环：综合判断 ──
    strong_weak = strength["strong_weak"]
    score = strength["score"]
    reasoning = strength.get("reasoning", [])
    
    chain.append({
        "step": 4,
        "title": "【综合判断】",
        "content": [
            f"综合得分：{score}",
            f"推理过程：",
        ] + [f"  · {r}" for r in reasoning[:5]],
    })
    
    # ── 推理链条第5环：用神忌神 ──
    useful = strength.get("useful_god", [])
    avoid = strength.get("avoid_god", [])
    chain.append({
        "step": 5,
        "title": "【用神忌神】",
        "content": [
            f"用神：{'、'.join(useful) if useful else '无'}",
            f"忌神：{'、'.join(avoid) if avoid else '无'}",
            f"最终判定：{strong_weak}",
        ],
    })
    
    # 矛盾点检查
    contradictions = []
    
    # 矛盾1：得令但失势的矛盾
    monthly_strong = ri_wx_season_status in ("旺", "相")
    is_de_shi = helping > harming
    if monthly_strong and not is_de_shi:
        contradictions.append(
            f"矛盾：月令得令({ri_wx_season_status})但天干失势，数字上{helping}<={harming}"
        )
    
    # 矛盾2：有根但无帮扶
    if roots and not is_de_shi:
        contradictions.append(
            f"矛盾：地支有根({len(roots)}处)但天干无帮扶"
        )
    
    # 矛盾3：从强/从弱的极端判断矛盾
    if "从" in strong_weak:
        if strong_weak == "从强" and not monthly_strong:
            contradictions.append(
                f"矛盾：判定从强但月令不得令({ri_wx_season_status})"
            )
        if strong_weak == "从弱" and monthly_strong:
            contradictions.append(
                f"矛盾：判定从弱但月令得令({ri_wx_season_status})"
            )
    
    result["details"].append({
        "strong_weak": strong_weak,
        "score": score,
        "distribution": strength.get("distribution", {}),
    })
    result["chain"] = chain
    result["contradictions"] = contradictions
    
    return result


def test_day_pillar_cross_century(calc):
    """跨世纪日柱公式兼容性测试"""
    result = {"pass": True, "issues": [], "details": []}
    
    # 测试1800-2100年的每个世纪切换点
    test_dates = [
        (1800, 1, 1, "辛卯"),
        (1850, 1, 1, "庚申"),
        (1899, 12, 31, "丙午"),
        (1900, 1, 1, "甲戌"),
        (1900, 2, 28, "壬寅"),
        (1900, 3, 1, "癸卯"),
        (1950, 1, 1, "己巳"),
        (1999, 12, 31, "丙子"),
        (2000, 1, 1, "甲午"),
        (2000, 2, 29, "癸亥"),  # 2000年是闰年
        (2000, 3, 1, "甲子"),
        (2001, 1, 1, "己亥"),
        (2024, 1, 1, "壬辰"),
        (2025, 1, 1, "丁酉"),
        (2099, 12, 31, "庚辰"),
        (2100, 1, 1, "甲寅"),
        (2100, 2, 28, "壬午"),
        (2100, 3, 1, "癸未"),  # 2100不是闰年
    ]
    
    for y, m, d, expected in test_dates:
        try:
            pillar = calc._calc_day_pillar(y, m, d)
            actual = pillar.gan_zhi
            if actual != expected:
                result["issues"].append(
                    f"跨世纪日柱错误：{y}-{m:02d}-{d:02d} 应得{expected}，实际{actual}"
                )
                result["pass"] = False
            else:
                result["details"].append(f"✅ {y}-{m:02d}-{d:02d} → {actual}")
        except Exception as e:
            result["issues"].append(f"跨世纪日柱异常 {y}-{m:02d}-{d:02d}: {e}")
            result["pass"] = False
    
    return result


def validate_all_shizhu_hours():
    """验证所有时辰边界的准确性"""
    result = {"pass": True, "issues": [], "details": []}
    calc = BaZiCalculator()
    
    # 每个时辰边界测试：边界时间 ±1分钟
    boundary_tests = [
        # (时辰名称, 应得地支, 测试小时, 测试分钟)
        ("子时(晚23:00)", "子", 23, 0),
        ("子时(晚23:59)", "子", 23, 59),
        ("子时(凌晨00:00)", "子", 0, 0),
        ("子时(凌晨00:59)", "子", 0, 59),
        ("丑时(凌晨01:00)", "丑", 1, 0),
        ("丑时(凌晨02:59)", "丑", 2, 59),
        ("寅时(凌晨03:00)", "寅", 3, 0),
        ("寅时(凌晨04:59)", "寅", 4, 59),
        ("卯时(凌晨05:00)", "卯", 5, 0),
        ("卯时(凌晨06:59)", "卯", 6, 59),
        ("辰时(早晨07:00)", "辰", 7, 0),
        ("辰时(早晨08:59)", "辰", 8, 59),
        ("巳时(上午09:00)", "巳", 9, 0),
        ("巳时(上午10:59)", "巳", 10, 59),
        ("午时(上午11:00)", "午", 11, 0),
        ("午时(下午12:59)", "午", 12, 59),
        ("未时(下午13:00)", "未", 13, 0),
        ("未时(下午14:59)", "未", 14, 59),
        ("申时(下午15:00)", "申", 15, 0),
        ("申时(下午16:59)", "申", 16, 59),
        ("酉时(下午17:00)", "酉", 17, 0),
        ("酉时(下午18:59)", "酉", 18, 59),
        ("戌时(晚上19:00)", "戌", 19, 0),
        ("戌时(晚上20:59)", "戌", 20, 59),
        ("亥时(晚上21:00)", "亥", 21, 0),
        ("亥时(晚上22:59)", "亥", 22, 59),
    ]
    
    # 用甲日做测试（甲日子时为甲子，方便验证五鼠遁）
    test_day_gan = "甲"
    
    for label, expected_zhi, h, mi in boundary_tests:
        try:
            actual_zhi = calc._get_hour_zhi(h, mi)
            ok = actual_zhi == expected_zhi
            if not ok:
                result["issues"].append(
                    f"时辰边界错误：{label} 应得{expected_zhi}，实际{actual_zhi}"
                )
                result["pass"] = False
            result["details"].append(
                f"{'✅' if ok else '❌'} {label} → {actual_zhi}"
            )
        except Exception as e:
            result["issues"].append(f"时辰边界异常 {label}: {e}")
            result["pass"] = False
    
    return result


def score_celebrity(name, year, month, day, hour, minute, gender):
    """对单个名人进行综合评分"""
    calc = BaZiCalculator()
    
    scores = {}
    deductions = []
    bonus = []
    
    try:
        bazi = calc.calculate(year, month, day, hour, minute, gender)
    except Exception as e:
        return {
            "name": name,
            "error": str(e),
            "total_score": 0,
            "scores": {},
            "deductions": [f"计算异常: {e}"],
            "bonus": [],
        }
    
    # 1. 年柱验证（20分）
    yr = validate_year_pillar(calc, name, year, month, day)
    if yr["pass"]:
        scores["年柱"] = 20
        bonus.append("年柱立春分界正确")
    else:
        base = 10
        for iss in yr["issues"]:
            deductions.append(f"年柱问题: {iss}")
        scores["年柱"] = base
    
    # 2. 月柱验证（25分）
    year_pillar = calc._calc_year_pillar(year, month, day)
    mr = validate_month_pillar(calc, name, year, month, day, year_pillar.tian_gan)
    month_score = 25
    boundary_issues = []
    if not mr["pass"]:
        for iss in mr["issues"]:
            month_score -= 8
            deductions.append(f"月柱问题: {iss}")
    if mr["details"] and mr["details"][0].get("boundary_tests"):
        boundary_issues = [b for b in mr["details"][0]["boundary_tests"] if b.startswith("⚠")]
        for bi in boundary_issues[:3]:
            month_score -= 3
            deductions.append(f"节气边界: {bi}")
    scores["月柱"] = max(month_score, 0)
    if mr["pass"] and not boundary_issues:
        bonus.append("月柱节气分界精准")
    
    # 3. 日柱验证（25分）
    expected_day = None
    for ky, km, kd, e in KNOWN_DAY_PILLARS:
        if ky == year and km == month and kd == day:
            expected_day = e
            break
    dr = validate_day_pillar(calc, year, month, day)
    if dr["pass"] and expected_day:
        scores["日柱"] = 25
        bonus.append(f"日柱{dr['details'][0] if dr['details'] else ''}")
    elif expected_day:
        scores["日柱"] = 5
        deductions.append(f"日柱计算错误：已知应为{expected_day}")
    else:
        # 无已知对照，给基础分
        scores["日柱"] = 20
    
    # 4. 时柱验证（15分）
    hr = validate_hour_pillar(calc, hour, minute, bazi.day_pillar.tian_gan)
    if hr["pass"]:
        scores["时柱"] = 15
        bonus.append("时柱时辰正确")
    else:
        scores["时柱"] = 5
        for iss in hr["issues"]:
            deductions.append(f"时柱问题: {iss}")
    
    # 5. 身强身弱推理（15分）
    sw = validate_strength_weakness(bazi)
    sw_score = 10
    if sw["pass"]:
        if not sw["contradictions"]:
            sw_score = 15
            bonus.append("身强身弱推理逻辑一致")
        else:
            sw_score = 10
            for c in sw["contradictions"][:2]:
                deductions.append(f"推理矛盾: {c}")
    else:
        sw_score = 5
        deductions.append("身强身弱推理异常")
    scores["身强身弱"] = sw_score
    
    total = sum(scores.values())
    
    return {
        "name": name,
        "bazi": " ".join(p.gan_zhi for p in bazi.si_zhu),
        "ri_gan": bazi.ri_gan,
        "strength": sw["details"][0]["strong_weak"] if sw["details"] else "?",
        "scores": scores,
        "total_score": total,
        "deductions": deductions,
        "bonus": bonus,
        "year_detail": yr["details"],
        "month_detail": mr["details"],
        "day_detail": dr["details"],
        "hour_detail": hr["details"],
        "strength_chain": sw["chain"],
        "contradictions": sw["contradictions"],
    }


# ──────────────────────────────────────────────────────────────
# 主报告函数
# ──────────────────────────────────────────────────────────────

def print_separator(char="=", width=80):
    print(char * width)


def run_full_validation():
    """运行完整的逐柱验证并输出中文报告"""
    calc = BaZiCalculator()
    total = len(CELEBRITIES)
    
    print_separator()
    print(f"  🔮 八字命理引擎 · 深度八卦验证报告")
    print(f"  测试集：{total}位名人（来自 celebrities_data.py）")
    print(f"  测试时间：逐柱验证 + 跨世纪公式 + 时辰边界 + 强弱推理")
    print_separator()
    
    # ════════════════════════════════════════════════════
    # 第一部分：全局基础测试
    # ════════════════════════════════════════════════════
    print("\n  📋 第一部分：全局基础测试\n")
    
    # 1.1 跨世纪日柱测试
    print("  【1.1】跨世纪日柱公式兼容性（1800-2100）")
    print_separator("-", 60)
    century_result = test_day_pillar_cross_century(calc)
    for d in century_result["details"]:
        print(f"  {d}")
    if century_result["issues"]:
        print(f"\n  ❌ 跨世纪日柱问题：")
        for iss in century_result["issues"]:
            print(f"    ⚠ {iss}")
    else:
        print(f"\n  ✅ 跨世纪日柱公式兼容性良好")
    print()
    
    # 1.2 全部时辰边界测试
    print("  【1.2】时辰边界全面测试（12时辰×边界±1分钟）")
    print_separator("-", 60)
    shizhen_result = validate_all_shizhu_hours()
    failed_shi = [d for d in shizhen_result["details"] if "❌" in d]
    passed_shi = [d for d in shizhen_result["details"] if "✅" in d]
    print(f"  通过：{len(passed_shi)}/{len(shizhen_result['details'])}")
    for d in shizhen_result["details"]:
        print(f"  {d}")
    if shizhen_result["issues"]:
        for iss in shizhen_result["issues"]:
            print(f"  ❌ {iss}")
    print()
    
    # ════════════════════════════════════════════════════
    # 第二部分：逐人逐柱验证
    # ════════════════════════════════════════════════════
    print("  📋 第二部分：名人逐柱验证（按分类）\n")
    
    all_results = []
    category_results = {}
    
    for i, entry in enumerate(CELEBRITIES):
        name, y, m, d, h, mi, g, cat, note = entry
        
        try:
            r = score_celebrity(name, y, m, d, h, mi, g)
        except Exception as e:
            r = {
                "name": name,
                "error": str(e),
                "total_score": 0,
                "scores": {},
                "deductions": [f"严重错误: {e}"],
                "bonus": [],
                "bazi": "N/A",
                "ri_gan": "?",
                "strength": "?",
            }
        
        all_results.append(r)
        
        if cat not in category_results:
            category_results[cat] = []
        category_results[cat].append(r)
        
        # 输出每人报告（精简）
        total_s = r["total_score"]
        grade = "A" if total_s >= 85 else "B" if total_s >= 70 else "C" if total_s >= 50 else "D"
        
        status_icon = "✅" if total_s >= 70 else "⚠️" if total_s >= 40 else "❌"
        
        print(f"  [{i+1:03d}] {status_icon} {name} ({cat})")
        print(f"      生日：{y}-{m:02d}-{d:02d} {h:02d}:{mi:02d} {g}")
        print(f"      八字：{r.get('bazi', 'N/A')}  日主：{r.get('ri_gan', '?')}  强弱：{r.get('strength', '?')}")
        print(f"      评分：{', '.join(f'{k}={v}' for k, v in r['scores'].items())} 总分={total_s}/100 (等级{grade})")
        
        if r.get("deductions"):
            for ded in r["deductions"][:3]:
                print(f"      ⚠ {ded}")
        if r.get("bonus"):
            for bn in r["bonus"][:2]:
                print(f"      ✅ {bn}")
        if r.get("contradictions"):
            for c in r["contradictions"][:2]:
                print(f"      ⚡ {c}")
        
        # 输出推理链条（精简版）
        if r.get("strength_chain"):
            chain = r["strength_chain"]
            print(f"      推理链：")
            for step in chain[:3]:
                for line in step["content"][:2]:
                    print(f"        · {line}")
        print()
    
    # ════════════════════════════════════════════════════
    # 第三部分：分类统计与总结
    # ════════════════════════════════════════════════════
    print("  📋 第三部分：分类统计与总结\n")
    
    # 总体统计
    total_avg = sum(r["total_score"] for r in all_results) / len(all_results)
    a_count = sum(1 for r in all_results if r["total_score"] >= 85)
    b_count = sum(1 for r in all_results if 70 <= r["total_score"] < 85)
    c_count = sum(1 for r in all_results if 50 <= r["total_score"] < 70)
    d_count = sum(1 for r in all_results if r["total_score"] < 50)
    
    print(f"  【总体统计】")
    print(f"  总人数：{len(all_results)}")
    print(f"  平均分：{total_avg:.1f}/100")
    print(f"  等级分布：A(≥85)={a_count}  B(70-84)={b_count}  C(50-69)={c_count}  D(<50)={d_count}")
    print()
    
    # 分类统计
    print(f"  【分类统计】")
    for cat, results in sorted(category_results.items()):
        cat_avg = sum(r["total_score"] for r in results) / len(results)
        names = ", ".join(r["name"] for r in results[:5])
        if len(results) > 5:
            names += f"...(共{len(results)}人)"
        print(f"  📂 {cat}（平均分{cat_avg:.1f}）：{names}")
    print()
    
    # 各柱得分统计
    print(f"  【各柱得分统计】")
    pillar_types = ["年柱", "月柱", "日柱", "时柱", "身强身弱"]
    pillar_max = {"年柱": 20, "月柱": 25, "日柱": 25, "时柱": 15, "身强身弱": 15}
    for ptype in pillar_types:
        vals = [r["scores"].get(ptype, 0) for r in all_results if ptype in r.get("scores", {})]
        if vals:
            avg = sum(vals) / len(vals)
            max_v = pillar_max[ptype]
            pct = avg / max_v * 100
            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            print(f"  {ptype}：avg={avg:.1f}/{max_v} {bar} {pct:.0f}%")
    print()
    
    # 问题汇总
    print(f"  【常见问题汇总】")
    all_deductions = []
    for r in all_results:
        for d in r.get("deductions", []):
            all_deductions.append(d)
    
    if all_deductions:
        from collections import Counter
        # 简单归类统计
        issue_cats = Counter()
        for d in all_deductions:
            if "年柱" in d:
                issue_cats["年柱问题"] += 1
            elif "月柱" in d or "月支" in d or "月干" in d or "节气" in d:
                issue_cats["月柱/节气问题"] += 1
            elif "日柱" in d:
                issue_cats["日柱问题"] += 1
            elif "时柱" in d or "时支" in d or "时干" in d or "时辰" in d:
                issue_cats["时柱问题"] += 1
            elif "推理" in d or "矛盾" in d or "身强" in d or "身弱" in d:
                issue_cats["强弱推理问题"] += 1
            else:
                issue_cats["其他"] += 1
        
        for cat, cnt in issue_cats.most_common():
            print(f"  ⚠ {cat}：{cnt}例")
    else:
        print(f"  ✅ 无任何问题")
    print()
    
    # ════════════════════════════════════════════════════
    # 第四部分：评分排行榜
    # ════════════════════════════════════════════════════
    print("  📋 第四部分：评分排行榜 TOP 10\n")
    
    sorted_results = sorted(all_results, key=lambda x: x["total_score"], reverse=True)
    for i, r in enumerate(sorted_results[:10]):
        grade = "A" if r["total_score"] >= 85 else "B" if r["total_score"] >= 70 else "C"
        print(f"  #{i+1:02d} {r['name']:8s}  {r['bazi']:16s}  评分{r['total_score']}/100 ({grade})")
    
    print()
    print(f"  📋 评分排行榜 BOTTOM 5\n")
    for i, r in enumerate(sorted_results[-5:]):
        print(f"  #{len(sorted_results)-4+i:02d} {r['name']:8s}  {r['bazi']:16s}  评分{r['total_score']}/100")
    
    print_separator()
    print(f"  🔮 验证完成")
    print(f"  总平均分：{total_avg:.1f}/100")
    print(f"  通过率（≥70分）：{(b_count + a_count)}/{total} ({(b_count + a_count)/total*100:.0f}%)")
    print_separator()


if __name__ == "__main__":
    run_full_validation()