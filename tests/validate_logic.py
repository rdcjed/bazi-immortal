"""
命理合理性验证 — 名人八字 vs 实际人生轨迹

验证核心规则：
· 企业家 → 财星旺/财为用神
· 政界 → 官杀旺/官杀为用
· 科学家 → 印星旺/印为用
· 娱乐明星 → 食伤旺/食伤为用
· 体育明星 → 比劫旺/驿马
· 身强能担财官 → 多为成功人士
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
from bazi_immortal.wuxing import WU_XING_SHENG, WU_XING_KE
from tests.celebrities_data import CELEBRITIES


def analyze():
    """主分析函数"""
    results = defaultdict(list)  # category → [result_dict]
    
    for entry in CELEBRITIES:
        name, y, m, d, h, mi, gender, cat, known = entry
        bazi = calculate_bazi(y, m, d, h, mi, gender)
        wx = analyze_ri_zuo_strong_weak(bazi)
        ss = analyze_all_shi_shen(bazi)
        sh = find_shen_sha(bazi)
        
        ri_wx = wx["ri_wx"]
        strong_weak = wx["strong_weak"]
        useful = wx["useful_god"]
        avoid = wx["avoid_god"]
        
        # 十神类别统计
        cat_counts = ss["category_counts"]
        
        # 各十神的权重（该类别是否是日主的用神）
        # 财星
        cai_is_useful = "火" in useful or "土" in useful  # 需要按日主五行具体判断
        
        # 更精确的用神判断：看财/官/印/食伤对应的五行是否在useful_god中
        # 财对应"我克"的五行
        cai_wx = WU_XING_KE.get(ri_wx)  # 我克=财
        guan_wx = None  # 克我=官杀
        for k, v in WU_XING_KE.items():
            if v == ri_wx:
                guan_wx = k
                break
        yin_wx = None  # 生我=印
        for k, v in WU_XING_SHENG.items():
            if v == ri_wx:
                yin_wx = k
                break
        shi_wx = WU_XING_SHENG.get(ri_wx)  # 我生=食伤
        
        results[cat].append({
            "name": name,
            "bazi": bazi,
            "wx": wx,
            "ri_wx": ri_wx,
            "strong_weak": strong_weak,
            "useful": useful,
            "avoid": avoid,
            "cat_counts": cat_counts,
            "cai_wx": cai_wx, "cai_useful": cai_wx in useful,
            "guan_wx": guan_wx, "guan_useful": guan_wx in useful,
            "yin_wx": yin_wx, "yin_useful": yin_wx in useful,
            "shi_wx": shi_wx, "shi_useful": shi_wx in useful,
            "shensha": sh,
        })
    
    return results


def print_category_analysis(results, cat, expected, label):
    """分析某一类别的命理特征"""
    items = results.get(cat, [])
    if not items:
        return
    
    total = len(items)
    print(f"\n{'='*60}")
    print(f"  📂 【{cat}】{total}人")
    print(f"{'='*60}")
    print(f"  预期特征：{label}")
    
    # 1. 强弱分布
    sw_dist = Counter(r["strong_weak"] for r in items)
    qiang = sw_dist.get("身强", 0) + sw_dist.get("偏强", 0) + sw_dist.get("从强", 0)
    ruo = sw_dist.get("身弱", 0) + sw_dist.get("偏弱", 0) + sw_dist.get("从弱", 0)
    print(f"\n  强弱：身强/偏强/从强={qiang}({qiang/total*100:.0f}%)  "
          f"中和={sw_dist.get('中和',0)}({sw_dist.get('中和',0)/total*100:.0f}%)  "
          f"身弱/偏弱/从弱={ruo}({ruo/total*100:.0f}%)")
    
    # 2. 财/官/印/食伤为用的比例
    useful_pcts = {}
    for key, field_name in [("cai_useful", "财星为用"), ("guan_useful", "官杀为用"),
                             ("yin_useful", "印星为用"), ("shi_useful", "食伤为用")]:
        count = sum(1 for r in items if r[key])
        pct = count / total * 100
        useful_pcts[field_name] = (count, pct)
        bar = "█" * max(1, int(pct / 5))
        print(f"  {field_name}: {count}/{total}={pct:.0f}% {bar}")
    
    # 3. 平均十神类别
    avg_cat = {}
    for cname in ["官杀", "印枭", "财", "比劫", "食伤"]:
        avg = sum(r["cat_counts"].get(cname, 0) for r in items) / total
        avg_cat[cname] = avg
    print(f"\n  平均十神类别：")
    max_avg = max(avg_cat.values())
    for cname in ["官杀", "印枭", "财", "比劫", "食伤"]:
        bar = "█" * max(1, int(avg_cat[cname] * 8))
        print(f"    {cname}: {avg_cat[cname]:.2f} {bar}")
    
    # 4. 样本列表（前10个）
    print(f"\n  样本明细（前{min(10,total)}个）：")
    for r in items[:10]:
        ri_wx = r["ri_wx"]
        sw = r["strong_weak"]
        useful_str = "/".join(r["useful"])
        # 财/官/印/食伤为用标记
        marks = []
        t = ("💰" if r["cai_useful"] else "") + \
            ("🏛" if r["guan_useful"] else "") + \
            ("📚" if r["yin_useful"] else "") + \
            ("🎨" if r["shi_useful"] else "")
        
        shensha_names = list(r["shensha"].keys())[:3]
        ss_str = ",".join(shensha_names) if shensha_names else ""
        
        print(f"    {r['name']:<8} {ri_wx}{sw:<4} 用神:{useful_str:<8} {t} 神煞:{ss_str}")
    
    return items


def cross_category_comparison(results):
    """跨类别对比分析"""
    print(f"\n{'='*60}")
    print(f"  🔬 跨类别对比分析")
    print(f"{'='*60}")
    
    categories = list(results.keys())
    
    # 各类别的用神偏好对比
    print(f"\n  各领域『财星为用』比例：")
    cai_data = []
    for cat in categories:
        items = results[cat]
        n = sum(1 for r in items if r["cai_useful"])
        pct = n / len(items) * 100
        cai_data.append((cat, n, len(items), pct))
        bar = "█" * max(1, int(pct / 4))
        print(f"    {cat:<10}: {n}/{len(items):<3} = {pct:5.1f}% {bar}")
    
    print(f"\n  各领域『官杀为用』比例：")
    for cat in categories:
        items = results[cat]
        n = sum(1 for r in items if r["guan_useful"])
        pct = n / len(items) * 100
        bar = "█" * max(1, int(pct / 4))
        print(f"    {cat:<10}: {n}/{len(items):<3} = {pct:5.1f}% {bar}")
    
    print(f"\n  各领域『印星为用』比例：")
    for cat in categories:
        items = results[cat]
        n = sum(1 for r in items if r["yin_useful"])
        pct = n / len(items) * 100
        bar = "█" * max(1, int(pct / 4))
        print(f"    {cat:<10}: {n}/{len(items):<3} = {pct:5.1f}% {bar}")
    
    print(f"\n  各领域『食伤为用』比例：")
    for cat in categories:
        items = results[cat]
        n = sum(1 for r in items if r["shi_useful"])
        pct = n / len(items) * 100
        bar = "█" * max(1, int(pct / 4))
        print(f"    {cat:<10}: {n}/{len(items):<3} = {pct:5.1f}% {bar}")


def detail_analysis(results):
    """深度分析：看每个名人的具体命理特征是否符合其人生轨迹"""
    print(f"\n{'='*60}")
    print(f"  🧐 深度案例分析")
    print(f"{'='*60}")
    
    # 挑选几个典型人物做深度分析
    deep_cases = [
        # 企业家代表
        ("马云", "阿里巴巴创始人，巨大财富"),
        ("任正非", "华为创始人，技术派企业家"),
        ("马化腾", "腾讯创始人，社交/游戏"),
        # 政界代表
        ("毛泽东", "开国领袖"),
        ("周恩来", "总理，外交家"),
        # 科学家
        ("钱学森", "两弹一星，学术成就"),
        ("屠呦呦", "诺贝尔奖"),
        # 娱乐明星
        ("周杰伦", "音乐天王，才华横溢"),
        ("刘德华", "四大天王，长青树"),
        # 体育明星
        ("姚明", "NBA巨星"),
        ("科比·布莱恩特", "NBA传奇，偏执好胜"),
    ]
    
    # 从所有结果中查找这些人物
    all_items = []
    for cat_items in results.values():
        all_items.extend(cat_items)
    
    name_to_item = {r["name"]: r for r in all_items}
    
    for name, expected in deep_cases:
        r = name_to_item.get(name)
        if not r:
            continue
        
        bazi_str = " ".join(p.gan_zhi for p in r["bazi"].si_zhu)
        ri_gan = r["bazi"].ri_gan
        ri_wx = r["ri_wx"]
        sw = r["strong_weak"]
        useful = "/".join(r["useful"])
        avoid = "/".join(r["avoid"])
        cat_counts = r["cat_counts"]
        
        # 神煞
        sha_names = list(r["shensha"].keys())
        key_sha = [s for s in sha_names if s in 
                   ["天乙贵人", "文昌贵人", "桃花（咸池）", "驿马", "华盖", "羊刃",
                    "天德", "月德", "红鸾", "天喜", "将星", "魁罡"]]
        
        # 分析评论
        comments = []
        
        # 强弱评论
        if sw in ("身强", "偏强", "从强"):
            comments.append("身强能担财官")
        elif sw in ("身弱", "偏弱"):
            comments.append("身弱需印比扶助")
        else:
            comments.append("中和之命")
        
        # 十神类别评论
        top_cat = sorted(cat_counts.items(), key=lambda x: -x[1])[:2]
        for cat_name, cat_val in top_cat:
            if cat_val >= 2.0:
                comments.append(f"{cat_name}旺({cat_val})")
        
        # 神煞评论
        if "天乙贵人" in key_sha:
            comments.append("贵人运强")
        if "驿马" in key_sha:
            comments.append("一生奔波/变动多")
        if "华盖" in key_sha:
            comments.append("孤高有才/艺术缘")
        if "将星" in key_sha:
            comments.append("有领导才能")
        if "魁罡" in key_sha:
            comments.append("刚毅果断")
        
        print(f"\n  ┌─ {name}")
        print(f"  ├ 八字：{bazi_str}")
        print(f"  ├ 日主：{ri_gan}({ri_wx}) | {sw} | 用神：{useful} 忌神：{avoid}")
        print(f"  ├ 十神：官杀{cat_counts.get('官杀',0):.1f} 印枭{cat_counts.get('印枭',0):.1f} "
              f"财{cat_counts.get('财',0):.1f} 比劫{cat_counts.get('比劫',0):.1f} "
              f"食伤{cat_counts.get('食伤',0):.1f}")
        print(f"  ├ 神煞：{'、'.join(key_sha[:5])}")
        print(f"  ├ 特征：{'，'.join(comments)}")
        print(f"  └ 人生：{expected}")


if __name__ == "__main__":
    print("=" * 60)
    print("  🎯 命理合理性验证报告")
    print("  验证106位名人的八字是否符合其人生轨迹")
    print("=" * 60)
    
    results = analyze()
    
    # 各分类分析
    print(f"\n📊 样本总量：{sum(len(v) for v in results.values())}人")
    print(f"    类别数：{len(results)}")
    
    # 各行业类别详细分析
    for cat in sorted(results.keys()):
        if cat == "中国企业家":
            print_category_analysis(results, cat, "财旺/财为用神", 
                "企业家应财星旺或财为用神，身强能担财")
        elif cat == "中国政界":
            print_category_analysis(results, cat, "官杀旺/官杀为用",
                "政界人物应官杀旺或官杀为用")
        elif cat == "国际政界":
            print_category_analysis(results, cat, "官杀旺",
                "政界人物应官杀旺")
        elif cat in ("中国科技", "国际科学家"):
            print_category_analysis(results, cat, "印星为用/文昌",
                "科学家应印星旺或印为用神，文昌贵人")
        elif cat in ("中国娱乐",):
            print_category_analysis(results, cat, "食伤为用/桃花",
                "娱乐明星应食伤旺或食伤为用，桃花星")
        elif cat in ("中国体育", "国际体育"):
            print_category_analysis(results, cat, "比劫旺/驿马",
                "体育明星应比劫旺，有驿马")
        else:
            print_category_analysis(results, cat, "", "")
    
    # 跨类别对比
    cross_category_comparison(results)
    
    # 深度案例分析
    detail_analysis(results)
    
    # 总结
    print(f"\n{'='*60}")
    print(f"  总结")
    print(f"{'='*60}")
    print("""
  命理核心规则验证：
  
  1. 『财星为用 → 财富』规则
     企业家类（26人）中财星为用神的比例应显高于其他行业
  
  2. 『官杀为用 → 从政』规则
     政界人物中官杀为用的比例应高于娱乐/体育界
  
  3. 『印星为用 → 学术』规则
     科学家/学者中印星为用的比例应最高
  
  4. 『食伤为用 → 才华』规则
     娱乐明星中食伤为用的比例应最高
  
  5. 『身强能担财官』规则
     成功人士中身强比例应高于身弱
    """)
