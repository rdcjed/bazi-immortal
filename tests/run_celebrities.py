"""
100名人八字测试运行器
对每个名人计算八字，统计五行/十神/强弱分布，
识别规律并输出分析报告
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collections import Counter, defaultdict
from bazi_immortal import (
    calculate_bazi,
    analyze_ri_zuo_strong_weak,
    analyze_all_shi_shen,
    find_shen_sha,
)
from bazi_immortal.wuxing import TG_WU_XING, WU_XING_LIST
from tests.celebrities_data import CELEBRITIES


def analyze_all():
    """运行所有100个名人测试"""
    results = []
    errors = []
    
    for entry in CELEBRITIES:
        name, year, month, day, hour, minute, gender, category, known = entry
        
        try:
            bazi = calculate_bazi(year, month, day, hour, minute, gender)
            wx = analyze_ri_zuo_strong_weak(bazi)
            ss = analyze_all_shi_shen(bazi)
            shensha = find_shen_sha(bazi)
            
            results.append({
                "name": name,
                "category": category,
                "year": year,
                "bazi": " ".join(p.gan_zhi for p in bazi.si_zhu),
                "ri_gan": bazi.ri_gan,
                "ri_wx": wx["ri_wx"],
                "strong_weak": wx["strong_weak"],
                "score": wx["score"],
                "useful_god": wx["useful_god"],
                "avoid_god": wx["avoid_god"],
                "ss_counts": ss["counts"],
                "ss_category": ss["category_counts"],
                "shensha_count": len(shensha),
                "gender": gender,
            })
        except Exception as e:
            errors.append((name, str(e)))
    
    return results, errors


def print_report(results):
    """打印统计报告"""
    total = len(results)
    
    print("=" * 70)
    print("            📊 100名人八字统计分析报告")
    print("=" * 70)
    print(f"\n总样本数：{total}")
    
    # ─── 日主五行分布 ───
    ri_gan_counts = Counter(r["ri_gan"] for r in results)
    ri_wx_counts = Counter(r["ri_wx"] for r in results)
    
    print("\n━━━ 日主五行分布 ━━━")
    for wx in WU_XING_LIST:
        count = ri_wx_counts.get(wx, 0)
        pct = count / total * 100
        bar = "█" * count + "░" * (max(ri_wx_counts.values()) - count) if ri_wx_counts else ""
        print(f"  {wx}：{count:2d}人 ({pct:5.1f}%)")
    
    # 日干详细
    print("\n  【日干明细】")
    for gan, count in sorted(ri_gan_counts.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        print(f"    {gan}：{count}人 ({pct:.1f}%)")
    
    # ─── 强弱分布 ───
    print("\n━━━ 强弱分布 ━━━")
    sw_counts = Counter(r["strong_weak"] for r in results)
    for sw in ["从强", "身强", "偏强", "中和", "偏弱", "身弱", "从弱"]:
        count = sw_counts.get(sw, 0)
        if count > 0:
            pct = count / total * 100
            print(f"  {sw}：{count:2d}人 ({pct:.1f}%)")
    
    # 平均得分（身强者为正值，身弱者为负值）
    avg_score = sum(r["score"] for r in results) / total
    print(f"\n  平均得分：{avg_score:.2f}")
    
    # ─── 十神分布 ───
    print("\n━━━ 十神分布（平均值）━━━")
    ss_names = ["正官", "七杀", "正印", "偏印", "正财", "偏财", "比肩", "劫财", "食神", "伤官"]
    for ss in ss_names:
        avg = sum(r["ss_counts"].get(ss, 0) for r in results) / total
        bar_len = int(avg * 10)
        bar = "█" * bar_len
        print(f"  {ss}：{avg:.2f} {bar}")
    
    # 十神类别分布
    print("\n━━━ 十神类别均值 ━━━")
    cat_names = ["官杀", "印枭", "财", "比劫", "食伤"]
    for cat in cat_names:
        avg = sum(r["ss_category"].get(cat, 0) for r in results) / total
        print(f"  {cat}：{avg:.2f}")
    
    # ─── 按分类分析 ───
    print("\n━━━ 按领域分类分析 ━━━")
    categories = defaultdict(list)
    for r in results:
        categories[r["category"]].append(r)
    
    for cat in sorted(categories.keys()):
        cat_results = categories[cat]
        n = len(cat_results)
        sw_ct = Counter(r["strong_weak"] for r in cat_results)
        wx_ct = Counter(r["ri_wx"] for r in cat_results)
        
        top_wx = wx_ct.most_common(1)[0][0] if wx_ct else "?"
        top_sw = sw_ct.most_common(1)[0][0] if sw_ct else "?"
        
        # 平均十神
        avg_guan = sum(r["ss_category"].get("官杀", 0) for r in cat_results) / n
        avg_yin = sum(r["ss_category"].get("印枭", 0) for r in cat_results) / n
        avg_cai = sum(r["ss_category"].get("财", 0) for r in cat_results) / n
        avg_bi = sum(r["ss_category"].get("比劫", 0) for r in cat_results) / n
        
        print(f"\n  【{cat}】{n}人")
        print(f"    常见日主五行：{wx_ct.most_common(3)}")
        print(f"    常见强弱：{sw_ct.most_common(3)}")
        print(f"    官杀{avg_guan:.2f} 印枭{avg_yin:.2f} 财{avg_cai:.2f} 比劫{avg_bi:.2f}")
    
    # ─── 身强者Top10 ───
    print("\n━━━ 身强/从强者 Top 10 ━━━")
    strong = [r for r in results if r["strong_weak"] in ("身强", "从强")]
    strong.sort(key=lambda x: -x["score"])
    for i, r in enumerate(strong[:10]):
        print(f"  {i+1}. {r['name']}（{r['bazi']}）得分{r['score']}")
    
    # ─── 身弱者Top10 ───
    print("\n━━━ 身弱/从弱者 Top 10 ━━━")
    weak = [r for r in results if r["strong_weak"] in ("身弱", "从弱")]
    weak.sort(key=lambda x: x["score"])
    for i, r in enumerate(weak[:10]):
        print(f"  {i+1}. {r['name']}（{r['bazi']}）得分{r['score']}")
    
    # ─── 中和者 ───
    print("\n━━━ 中和 ━━━")
    zhonghe = [r for r in results if r["strong_weak"] == "中和"]
    for r in zhonghe:
        print(f"  {r['name']}（{r['bazi']}）")
    
    # ─── 神煞统计 ───
    print("\n━━━ 神煞统计 ─━━")
    sha_counts = Counter()
    # 复用之前的数据，这里直接从 results 里重新统计有困难
    # 在之前的循环里没有统计每个神煞，这里大概统计一下
    total_shensha = sum(r["shensha_count"] for r in results)
    avg_shensha = total_shensha / total
    print(f"  人均神煞数：{avg_shensha:.1f}个")
    
    # ─── 各行业日主偏好 ───
    print("\n━━━ 各领域日主五行偏好 ━━━")
    for cat in sorted(categories.keys()):
        cat_results = categories[cat]
        wx_ct = Counter(r["ri_wx"] for r in cat_results)
        top2 = wx_ct.most_common(2)
        print(f"  {cat}：偏好{top2[0][0]}({top2[0][1]}人)")
        if len(top2) > 1:
            print(f"      次偏好{top2[1][0]}({top2[1][1]}人)")

    print(f"\n{'='*70}")
    print(f"  报告完毕 | 总样本 {total}")
    print(f"{'='*70}")


if __name__ == "__main__":
    print("正在推算100个名人八字...")
    results, errors = analyze_all()
    
    if errors:
        print(f"\n⚠ 有 {len(errors)} 个错误：")
        for name, err in errors:
            print(f"  {name}: {err}")
    
    print_report(results)