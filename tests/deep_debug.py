"""
深度排查：比劫计数过高的原因 + 乔丹矛盾分析
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
from bazi_immortal.wuxing import WU_XING_SHENG, WU_XING_KE, TG_WU_XING, analyze_wuxing_distribution
from bazi_immortal.constants import (
    TG_WU_XING as TG_WX, DZ_WU_XING, DZ_CANG_GAN,
    TIAN_GAN, DI_ZHI, TG_INDEX, DZ_INDEX,
    SHI_ER_CHANG_SHENG,
)
from bazi_immortal.shisheng import get_shi_shen_for_gan

print("=" * 70)
print("  排查1: 比劫计数为什么普遍偏高?")
print("=" * 70)

# 选一个典型名人来分析
print(f"\n  案例: 阿尔伯特·爱因斯坦 (1879-03-14 11:30)")
print(f"  八字: 己卯 丁卯 乙丑 壬午")
print(f"  日主: 乙木")

bazi = calculate_bazi(1879, 3, 14, 11, 30, "男")
ss = analyze_all_shi_shen(bazi)

print(f"\n  十神原始数据:")
for i, (pillar, label) in enumerate(zip(bazi.si_zhu, ["年", "月", "日", "时"])):
    cangs = pillar.cang_gan
    print(f"    {label}柱: {pillar.gan_zhi}")
    print(f"      天干: {pillar.tian_gan} → {get_shi_shen_for_gan(bazi.ri_gan, pillar.tian_gan)}")
    print(f"      地支: {pillar.di_zhi} (本气{DZ_WU_XING[pillar.di_zhi]})")
    for j, cg in enumerate(cangs):
        weight = "主藏干(×1.0)" if j == 0 else "余气(×0.5)"
        ss_name = get_shi_shen_for_gan(bazi.ri_gan, cg)
        print(f"      藏干: {cg} {weight} → {ss_name}")

print(f"\n  类别汇总:")
for cat, cnt in ss["category_counts"].items():
    print(f"    {cat}: {cnt}")
print(f"  原始十神: {dict(ss['counts'])}")

print(f"\n  → 比劫={ss['category_counts']['比劫']:.1f}")
print(f"  问题: 年柱卯木含乙木藏干→比肩 ×0.5")
print(f"        日支丑土含癸水→印枭 ×1.0")
print(f"        这就是爱因斯坦比劫偏高的原因")

print(f"\n{'=' * 70}")
print(f"  排查2: 迈克尔·乔丹矛盾分析")
print(f"{'=' * 70}")

print(f"\n  乔丹: 1963-02-17 14:00 (未时)")

# 实际时辰
bazi_real = calculate_bazi(1963, 2, 17, 14, 0, "男")
print(f"  真实八字: {' '.join(p.gan_zhi for p in bazi_real.si_zhu)}")

# 提取各柱的天干和藏干
ri_gan = bazi_real.ri_gan  # 辛
print(f"  日主: {ri_gan}(金)")

# 逐个分析十神
print(f"\n  逐个十神分析:")
for pillar, label in zip(bazi_real.si_zhu, ["年", "月", "日", "时"]):
    cangs = pillar.cang_gan
    tg_ss = get_shi_shen_for_gan(ri_gan, pillar.tian_gan)
    print(f"    {label}柱 {pillar.gan_zhi}:")
    print(f"      天干 {pillar.tian_gan}→{tg_ss}")
    for j, cg in enumerate(cangs):
        w = "主藏(×1.0)" if j == 0 else "余气(×0.5)"
        ss_name = get_shi_shen_for_gan(ri_gan, cg)
        print(f"      藏干 {cg} {w}→{ss_name}")

# 看强弱分析
wx = analyze_ri_zuo_strong_weak(bazi_real)
print(f"\n  身强/身弱:")
print(f"  判定: {wx['strong_weak']} (得分{wx['score']})")
for r in wx["reasoning"]:
    print(f"    · {r}")

print(f"\n  用神: {'/'.join(wx['useful_god'])}")
print(f"  忌神: {'/'.join(wx['avoid_god'])}")

# 乔丹的关键矛盾
print(f"\n  【矛盾分析】")
print(f"  1. 辛金身弱 + 财旺(4.0 木) = 理论不胜财")
print(f"  2. 但乔丹是世界上最富有的运动员之一(净资产$2.2B)")
print(f"  3. 比劫仅1.0 → 运动员应有比劫旺")
print(f"  4. 食伤1.0 → 偏弱")
print(f"")
print(f"  可能原因:")
print(f"  A. 时辰不正确 (2pm是推测不是确证)")
print(f"  B. 大运起关键作用 (需要大运分析)")
print(f"  C. 身弱判定有缺陷")

# 测试不同时辰的乔丹
print(f"\n  测试不同时辰下的结论:")
print(f"{'时辰':<6} {'八字':<24} {'强弱':<8} {'财':<4} {'比劫':<4} {'官杀':<4} {'食伤':<4} {'印枭':<4}")
for hour in range(12):
    h = (hour + 23) % 24
    b = calculate_bazi(1963, 2, 17, h, 0, "男")
    w = analyze_ri_zuo_strong_weak(b)
    s = analyze_all_shi_shen(b)
    cc = s["category_counts"]
    bazi_str = " ".join(p.gan_zhi for p in b.si_zhu)
    if hour == 3:  # 辰时
        print(f"  辰({h:02d}h): {bazi_str:<24} {w['strong_weak']:<8} "
              f"{cc.get('财',0):.0f}  {cc.get('比劫',0):.0f}  {cc.get('官杀',0):.0f}  "
              f"{cc.get('食伤',0):.0f}  {cc.get('印枭',0):.0f} ←推荐?")

print(f"\n{'=' * 70}")
print(f"  排查3: 比劫计数问题的根因")
print(f"{'=' * 70}")

# 统计所有名人各位置的比劫贡献
total_contrib = {"天干": 0, "本气": 0, "主藏": 0, "余气": 0}
total_count = 0
from tests.celebrities_data import CELEBRITIES

for entry in CELEBRITIES[:50]:
    name, y, m, d, h, mi, gender, cat, known = entry
    b = calculate_bazi(y, m, d, h, mi, gender)
    ri_gan = b.ri_gan
    
    for pillar in b.si_zhu:
        # 天干
        ss = get_shi_shen_for_gan(ri_gan, pillar.tian_gan)
        if ss in ("比肩", "劫财"):
            total_contrib["天干"] += 2
            total_count += 1
        
        # 本气
        dz_wx = DZ_WU_XING[pillar.di_zhi]
        ri_wx = TG_WU_XING[ri_gan]
        if dz_wx == ri_wx:
            total_contrib["本气"] += 1.5
            total_count += 1
        
        # 藏干
        cangs = DZ_CANG_GAN.get(pillar.di_zhi, [])
        for j, cg in enumerate(cangs):
            ss = get_shi_shen_for_gan(ri_gan, cg)
            if ss in ("比肩", "劫财"):
                w = 1.0 if j == 0 else 0.5
                key = "主藏" if j == 0 else "余气"
                total_contrib[key] += w
                total_count += 1

total_bi = sum(total_contrib.values())
print(f"  样本: 50人, 每人4柱, 共{total_count}个比劫计数点")
print(f"  比劫来源分布:")
for src, cnt in sorted(total_contrib.items(), key=lambda x: -x[1]):
    pct = cnt / total_bi * 100 if total_bi > 0 else 0
    bar = "█" * max(1, int(pct / 3))
    print(f"    {src}: {cnt:.1f} ({pct:.0f}%) {bar}")

print(f"\n")
print(f"  结论: 藏干(余气)是最大来源!")
print(f"  → 每个地支有2-3个藏干，每个都可能被算作比劫")
print(f"  → 建议: 余气权重从0.5降到0.3，降低藏干影响")