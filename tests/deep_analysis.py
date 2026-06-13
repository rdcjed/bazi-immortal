"""
深度分析：当前验证框架的方法论缺陷
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
from tests.celebrities_data import CELEBRITIES

print("=" * 70)
print("  问题1: 用神判断逻辑 — 验证框架的核心缺陷")
print("=" * 70)

# 统计用神列表长度
useful_lengths = Counter()
for entry in CELEBRITIES:
    name, y, m, d, h, mi, gender, cat, known = entry
    bazi = calculate_bazi(y, m, d, h, mi, gender)
    wx = analyze_ri_zuo_strong_weak(bazi)
    n = len(wx["useful_god"])
    useful_lengths[n] += 1

print(f"  用神数量分布: {dict(sorted(useful_lengths.items()))}")
print(f"  → 普遍3个用神，随机命中率 ~60%，验证无意义")
print()

print("=" * 70)
print("  问题2: 实际财星强度 vs 用神判断")
print("=" * 70)

print(f"{'姓名':<8} {'日主':<4} {'财五行':<6} {'用神':<14} {'财在用神?':<10} {'实际财数':<10} {'财占比':<8}")
print("-" * 70)
for entry in CELEBRITIES[:15]:
    name, y, m, d, h, mi, gender, cat, known = entry
    bazi = calculate_bazi(y, m, d, h, mi, gender)
    wx = analyze_ri_zuo_strong_weak(bazi)
    ss = analyze_all_shi_shen(bazi)
    
    ri_wx = wx["ri_wx"]
    useful = wx["useful_god"]
    cai_wx = WU_XING_KE.get(ri_wx)
    
    cai_count = ss["category_counts"].get("财", 0)
    total = sum(ss["category_counts"].values())
    cai_pct = cai_count / total * 100 if total > 0 else 0
    
    useful_str = "".join(useful)
    mark = "YES" if cai_wx in useful else "NO"
    
    print(f"  {name:<6} {ri_wx:<4} {cai_wx:<6} {useful_str:<14} {mark:<10} {cai_count:<10} {cai_pct:.0f}%")

print()
print("  → 大部分人的财五行都在用神里，因为用神=3个/总五行=5个")
print("  → 但实际财星出现次数可能很少，这说明验证有问题")
print()

print("=" * 70)
print("  问题3: 各领域十神强度的实际分布")
print("=" * 70)

cat_ten_god = defaultdict(lambda: Counter())
cat_counts = Counter()

for entry in CELEBRITIES:
    name, y, m, d, h, mi, gender, cat, known = entry
    bazi = calculate_bazi(y, m, d, h, mi, gender)
    ss = analyze_all_shi_shen(bazi)
    cat_ten_god[cat] += Counter(ss["category_counts"])
    cat_counts[cat] += 1

for cat in sorted(cat_counts.keys()):
    n = cat_counts[cat]
    if n < 3:
        continue
    c = cat_ten_god[cat]
    print(f"\n  【{cat}】{n}人")
    for tg in ["官杀", "印枭", "财", "比劫", "食伤"]:
        avg = c[tg] / n
        bar = "█" * int(avg * 5)
        print(f"    {tg}: {avg:.2f} {bar}")

print()
print("=" * 70)
print("  核心问题总结")
print("=" * 70)
print("""
当前验证框架的关键缺陷：

1. 【方法论错误】用神判断太宽泛
   - 用神=3个五行，财/官/印/食伤各=1个五行
   - 随机命中率~60%，任何类别都能得出50-70%的匹配率
   - 这不是"验证"，而是"噪声中的偶然"

2. 【数据不准确】95%的人使用默认午时
   - 出生时辰影响时柱，时柱影响用神判断
   - 错误时辰 → 对错判断都不可信

3. 【维度单一】只看"是否在用神里"
   - 正确的做法：检查实际十神强度
   - 财星旺(出现次数多)→ 企业家倾向 ✅
   - 食伤旺(出现次数多)→ 艺术倾向 ✅

4. 【缺少对照】没有"普通人"对照组
   - 如果100%的成功人士都身强，那身强是成功的必要条件
   - 但普通人中也有60%身强，那这个指标就没区分度

改进方向：
  1. 查找真实出生时辰的名人（至少20-30人）
  2. 验证十神强度与职业的对应关系
  3. 增加"普通人对照组"
  4. 使用卡方检验等统计方法
""")
