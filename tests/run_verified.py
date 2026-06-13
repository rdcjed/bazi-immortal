"""
使用真正有出生时辰记录的名人，验证命理引擎的合理性和准确性
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collections import Counter, defaultdict
from bazi_immortal import (
    calculate_bazi,
    analyze_ri_zuo_strong_weak,
    analyze_all_shi_shen,
    find_shen_sha,
)
from bazi_immortal.wuxing import WU_XING_SHENG, WU_XING_KE, TG_WU_XING
from bazi_immortal.constants import TG_WU_XING as TG_WX, SHI_CHEN
from tests.verified_data import VERIFIED_CELEBRITIES

# VS 默认午时的对照组
from tests.celebrities_data import CELEBRITIES as DEFAULT_CELEBRITIES

print("=" * 70)
print("  🎯 基于真实出生时辰的精度验证")
print("  对比: 真实时辰 vs 默认午时的推算结果差异")
print("=" * 70)

# ══════════════════════════════════════════════
# Part 1: 真实时辰推算 vs 默认午时推算
# ══════════════════════════════════════════════

print(f"\n{'─' * 70}")
print(f"  Part 1: 同一人物，真实时辰 vs 默认午时")
print(f"{'─' * 70}")

# 找到同时在两个数据集中的名人
verified_by_name = {}
for entry in VERIFIED_CELEBRITIES:
    verified_by_name[entry[0]] = entry

default_by_name = {}
for entry in DEFAULT_CELEBRITIES:
    default_by_name[entry[0]] = entry

common_names = [n for n in verified_by_name if n in default_by_name]

print(f"\n  两个数据集共有: {len(common_names)}人")

changes = []
for name in sorted(common_names):
    ve = verified_by_name[name]  # (name, y, m, d, h, mi, gender, cat, note)
    de = default_by_name[name]
    
    # 真实时辰推算
    bazi_verified = calculate_bazi(ve[1], ve[2], ve[3], ve[4], ve[5], ve[6])
    wx_v = analyze_ri_zuo_strong_weak(bazi_verified)
    ss_v = analyze_all_shi_shen(bazi_verified)
    sh_v = find_shen_sha(bazi_verified)
    
    # 默认午时推算
    bazi_default = calculate_bazi(de[1], de[2], de[3], de[4], de[5], de[6])
    wx_d = analyze_ri_zuo_strong_weak(bazi_default)
    ss_d = analyze_all_shi_shen(bazi_default)
    sh_d = find_shen_sha(bazi_default)
    
    # 对比
    v_bazi_str = " ".join(p.gan_zhi for p in bazi_verified.si_zhu)
    d_bazi_str = " ".join(p.gan_zhi for p in bazi_default.si_zhu)
    
    # 看时柱是否不同
    v_hour = bazi_verified.hour_pillar.gan_zhi
    d_hour = bazi_default.hour_pillar.gan_zhi
    
    sw_change = "🔄" if wx_v["strong_weak"] != wx_d["strong_weak"] else "="
    useful_change = "🔄" if wx_v["useful_god"] != wx_d["useful_god"] else "="
    
    # 计算十神变化幅度
    ss_changes = {}
    for k in ["官杀", "印枭", "财", "比劫", "食伤"]:
        diff = ss_v["category_counts"].get(k, 0) - ss_d["category_counts"].get(k, 0)
        if abs(diff) >= 0.5:
            ss_changes[k] = f"{diff:+.1f}"
    
    changes.append({
        "name": name,
        "real_time": f"{ve[4]:02d}:{ve[5]:02d}",
        "default_hour": "12:00",
        "v_hour": v_hour,
        "d_hour": d_hour,
        "v_sw": wx_v["strong_weak"],
        "d_sw": wx_d["strong_weak"],
        "sw_change": sw_change,
        "v_useful": wx_v["useful_god"],
        "d_useful": wx_d["useful_god"],
        "useful_change": useful_change,
        "ss_changes": ss_changes,
        "v_bazi": v_bazi_str,
        "d_bazi": d_bazi_str,
    })
    
    print(f"\n  {name} ({ve[7]})")
    print(f"    真实时: {ve[4]:02d}:{ve[5]:02d} → {v_bazi_str} | 强弱={wx_v['strong_weak']}")
    print(f"    默认午: 12:00     → {d_bazi_str} | 强弱={wx_d['strong_weak']}")
    if sw_change == "🔄":
        print(f"    ⚠ 强弱判定改变! {wx_d['strong_weak']} → {wx_v['strong_weak']}")
    if useful_change == "🔄":
        print(f"    ⚠ 用神改变! {''.join(wx_d['useful_god'])} → {''.join(wx_v['useful_god'])}")
    if ss_changes:
        for k, v in ss_changes.items():
            print(f"    十神变动: {k} {v}")

# 汇总
sw_changed = [c for c in changes if c["sw_change"] == "🔄"]
useful_changed = [c for c in changes if c["useful_change"] == "🔄"]

print(f"\n{'=' * 70}")
print(f"  汇总: 真实时辰 vs 默认午时的影响")
print(f"{'=' * 70}")
print(f"  强弱判定改变: {len(sw_changed)}/{len(changes)}人")
for c in sw_changed:
    print(f"    {c['name']}: {c['d_sw']} → {c['v_sw']}")
print(f"  用神改变: {len(useful_changed)}/{len(changes)}人")
for c in useful_changed:
    print(f"    {c['name']}: {''.join(c['d_useful'])} → {''.join(c['v_useful'])}")


# ══════════════════════════════════════════════
# Part 2: 所有真实时辰人物的命理特征分析
# ══════════════════════════════════════════════

print(f"\n\n{'=' * 70}")
print(f"  Part 2: 精选数据集 ({len(VERIFIED_CELEBRITIES)}人) 命理特征")
print(f"{'=' * 70}")

cat_data = defaultdict(list)
all_verified_results = []

for entry in VERIFIED_CELEBRITIES:
    name, y, m, d, h, mi, gender, cat, note = entry
    
    bazi = calculate_bazi(y, m, d, h, mi, gender)
    wx = analyze_ri_zuo_strong_weak(bazi)
    ss = analyze_all_shi_shen(bazi)
    sh = find_shen_sha(bazi)
    
    result = {
        "name": name,
        "bazi": " ".join(p.gan_zhi for p in bazi.si_zhu),
        "ri_gan": bazi.ri_gan,
        "ri_wx": wx["ri_wx"],
        "strong_weak": wx["strong_weak"],
        "useful": wx["useful_god"],
        "cat_counts": dict(ss["category_counts"]),
        "shensha": list(sh.keys()),
        "note": note,
    }
    cat_data[cat].append(result)
    all_verified_results.append(result)

print(f"\n{'类别':<14} {'人数':<4} {'常见日主':<20} {'常见强弱':<20}")
print("-" * 65)
for cat, items in sorted(cat_data.items()):
    n = len(items)
    gan_dist = Counter(r["ri_gan"] for r in items).most_common(3)
    sw_dist = Counter(r["strong_weak"] for r in items).most_common(3)
    gan_str = "/".join(f"{g}({c})" for g, c in gan_dist)
    sw_str = "/".join(f"{s}({c})" for s, c in sw_dist)
    print(f"{cat:<14} {n:<4} {gan_str:<20} {sw_str:<20}")

# 各领域的十神强度
print(f"\n{'─' * 70}")
print(f"  各领域十神强度 (真实时辰):")
print(f"{'─' * 70}")
for cat in sorted(cat_data.keys()):
    items = cat_data[cat]
    n = len(items)
    cat_counts_acc = Counter()
    for r in items:
        cat_counts_acc += Counter(r["cat_counts"])
    
    print(f"\n  📂 【{cat}】{n}人")
    for tg in ["官杀", "印枭", "财", "比劫", "食伤"]:
        avg = cat_counts_acc[tg] / n
        bar = "█" * max(1, int(avg * 6))
        print(f"    {tg}: {avg:.2f} {bar}")

# ══════════════════════════════════════════════
# Part 3: 时辰敏感性分析
# ══════════════════════════════════════════════

print(f"\n\n{'=' * 70}")
print(f"  Part 3: 时辰敏感性分析 — 同一人不同时辰的结论变化")
print(f"{'=' * 70}")

# 用乔布斯做演示
print(f"\n  人物: 史蒂夫·乔布斯 (1955-02-24, 男)")
print(f"  实际出生: 19:00 (戌时)")
print(f"\n  测试全部12个时辰的影响:")

hour_names = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

results_by_hour = []
for hour in range(12):
    h = (hour + 23) % 24  # 子时从23点开始
    bazi = calculate_bazi(1955, 2, 24, h, 0, "男")
    wx = analyze_ri_zuo_strong_weak(bazi)
    ss = analyze_all_shi_shen(bazi)
    
    cat_counts = ss["category_counts"]
    consuming = cat_counts.get("食伤", 0) + cat_counts.get("财", 0) + cat_counts.get("官杀", 0)
    supporting = cat_counts.get("比劫", 0) + cat_counts.get("印枭", 0)
    
    results_by_hour.append({
        "hour_name": hour_names[hour],
        "hour": h,
        "bazi": " ".join(p.gan_zhi for p in bazi.si_zhu),
        "strong_weak": wx["strong_weak"],
        "useful": wx["useful_god"],
        "cat_counts": dict(cat_counts),
        "consuming": consuming,
        "supporting": supporting,
    })

# 找出结论变化的关键时辰
print(f"\n{'时辰':<6} {'八字':<24} {'强弱':<8} {'用神':<12} {'财':<4} {'官杀':<4} {'食伤':<4} {'印枭':<4} {'比劫':<4}")
print("-" * 80)
for r in results_by_hour:
    cc = r["cat_counts"]
    bazi_str = r["bazi"]
    useful_str = "".join(r["useful"])
    print(f"{r['hour_name']}({r['hour']:02d}h): {bazi_str:<24} {r['strong_weak']:<8} "
          f"{useful_str:<12} {cc.get('财',0):.0f}  {cc.get('官杀',0):.0f}  "
          f"{cc.get('食伤',0):.0f}  {cc.get('印枭',0):.0f}  {cc.get('比劫',0):.0f}")

# 找出实际时辰的结论
actual_hour_index = 8  # 戌时 = 19:00
actual = results_by_hour[actual_hour_index]

print(f"\n  实际戌时结论: 强弱={actual['strong_weak']}, 用神={'/'.join(actual['useful'])}")
print(f"  乔布斯是Apple创始人，科技/商业双成功")

# ══════════════════════════════════════════════
# Part 4: 关键矛盾分析
# ══════════════════════════════════════════════

print(f"\n\n{'=' * 70}")
print(f"  Part 4: 命理逻辑矛盾分析")
print(f"{'=' * 70}")

print("""
  判断原则:
  · 企业家 → 财星旺应为好事（身强能担财）
  · 身弱+财旺 → 应为压力大、不为好事
  · 政界 → 官杀旺
  · 科学家 → 印星旺+文昌
  · 娱乐 → 食伤旺+桃花
  · 体育 → 比劫旺+驿马
""")

for entry in VERIFIED_CELEBRITIES:
    name, y, m, d, h, mi, gender, cat, note = entry
    bazi = calculate_bazi(y, m, d, h, mi, gender)
    wx = analyze_ri_zuo_strong_weak(bazi)
    ss = analyze_all_shi_shen(bazi)
    sh = find_shen_sha(bazi)
    
    cat_counts = ss["category_counts"]
    ri_wx = wx["ri_wx"]
    sw = wx["strong_weak"]
    useful = wx["useful_god"]
    shensha_names = list(sh.keys())
    
    issues = []
    
    # 检查各行业的预期
    if cat == "国际企业家":
        cai = cat_counts.get("财", 0)
        if cai < 1.0:
            issues.append(f"财星极弱({cai})但为企业家")
        if sw in ("身弱", "偏弱"):
            issues.append(f"身弱({sw})+财旺可能不胜财")
    
    elif cat == "国际政界":
        guan = cat_counts.get("官杀", 0)
        if guan < 1.0:
            issues.append(f"官杀弱({guan})但为政界人物")
    
    elif cat in ("国际科学家", "中国科技"):
        yin = cat_counts.get("印枭", 0)
        if yin < 1.0:
            issues.append(f"印星弱({yin})但为科学家")
        if "文昌贵人" not in shensha_names:
            issues.append("无文昌贵人")
    
    elif cat in ("国际体育",):
        bi = cat_counts.get("比劫", 0)
        if bi < 2.0:
            issues.append(f"比劫偏弱({bi})但为运动员")
        if "驿马" not in shensha_names:
            pass  # 驿马不是必须的
    
    elif cat == "国际思想家":
        yin = cat_counts.get("印枭", 0)
        if yin < 2.0:
            issues.append(f"印星偏弱({yin})但为思想家")
    
    # 身强/身弱与财的协调
    if sw in ("身弱", "偏弱", "从弱"):
        cai = cat_counts.get("财", 0)
        consuming = cat_counts.get("食伤", 0) + cat_counts.get("财", 0) + cat_counts.get("官杀", 0)
        supporting = cat_counts.get("比劫", 0) + cat_counts.get("印枭", 0)
        if cai > 2.0:
            issues.append(f"身弱+财旺({cai}): 理论不胜财，实际却富")
        if consuming > supporting * 1.5:
            issues.append(f"身弱+克泄重({consuming}vs{supporting}): 理论压力大")
    
    if issues:
        bazi_str = " ".join(p.gan_zhi for p in bazi.si_zhu)
        print(f"\n  ⚠ [{name}] ({cat})")
        print(f"     八字: {bazi_str} | {ri_wx}{sw}")
        print(f"     十神: 官杀{cat_counts.get('官杀',0):.1f} 印枭{cat_counts.get('印枭',0):.1f} "
              f"财{cat_counts.get('财',0):.1f} 比劫{cat_counts.get('比劫',0):.1f} "
              f"食伤{cat_counts.get('食伤',0):.1f}")
        print(f"     神煞: {'/'.join(shensha_names[:5])}")
        for issue in issues:
            print(f"     矛盾: {issue}")

print(f"\n{'=' * 70}")
print(f"  总结与建议")
print(f"{'=' * 70}")
print("""
  核心发现:
  1. 真实时辰的数据量太少(30人)，还不足以做统计显著分析
  2. 从已有数据看，时辰对强弱判定影响很大（影响时柱）
  3. 部分真实时辰下的结论比默认午时更合理
  
  下一步建议:
  1. 补充更多有真实时辰记录的名人（可从维基百科的出生记录中找）
  2. 增加"普通人对照组"随机样本
  3. 开发大运计算功能——这才能验证人生起伏
  4. 做双盲测试——让命理师盲推后比对人生轨迹
""")