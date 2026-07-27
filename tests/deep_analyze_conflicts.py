"""深度分析4个冲突案例"""
import json
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bazi_immortal import (
    calculate_bazi, analyze_ri_zuo_strong_weak, analyze_all_shi_shen,
    find_shen_sha, analyze_ge_ju, analyze_tiao_hou,
    merge_tiao_hou_with_strong_weak, calculate_da_yun
)
from bazi_immortal.constants import TG_WU_XING

cases = [
    ("马云", 1964, 9, 10, 12, 0, "男"),
    ("张一鸣", 1983, 4, 16, 12, 0, "男"),
    ("李小龙", 1940, 11, 27, 7, 0, "男"),
    ("林青霞", 1954, 11, 3, 21, 0, "女"),
]

for name, y, m, d, h, mi, g in cases:
    print(f"\n{'='*60}")
    print(f"  【{name}】{y}年{m}月{d}日 {h}:{mi:02d} {g}")
    print(f"{'='*60}")
    
    bazi = calculate_bazi(y, m, d, h, mi, g)
    wx = analyze_ri_zuo_strong_weak(bazi)
    ss = analyze_all_shi_shen(bazi)
    tiao_hou = analyze_tiao_hou(bazi)
    wx_merged = merge_tiao_hou_with_strong_weak(wx, tiao_hou)
    ge_ju = analyze_ge_ju(bazi, wx, ss)
    
    # 四季旺衰
    season_wx = {"春": "木旺火相", "夏": "火旺土相", "秋": "金旺水相", "冬": "水旺木相", "季末": "土旺金相"}.get(wx['season'], '')
    
    print(f"八字: {' '.join(p.gan_zhi for p in bazi.si_zhu)}")
    print(f"日主: {bazi.ri_gan}({wx['ri_wx']})  月令地支: {bazi.month_pillar.di_zhi}")
    print(f"季节: {wx['season']} ({season_wx})")
    print(f"月令状态: {wx['monthly_state']}")
    
    print(f"\n得分明细:")
    for r in wx['reasoning']:
        print(f"  {r}")
    
    print(f"\n强弱判定: {wx['strong_weak']} (综合得分: {wx['score']})")
    print(f"用神: {wx_merged['useful_god']}  忌神: {wx_merged['avoid_god']}")
    
    print(f"\n调候用神: 第一={tiao_hou['primary']} 第二={tiao_hou['secondary']}")
    print(f"调候得分: {tiao_hou['score']}/5  已出现: {tiao_hou['present']}")
    
    print(f"格局: {ge_ju['name']}")
    
    print(f"十神类别: ", end="")
    for cat, cnt in sorted(ss['category_counts'].items(), key=lambda x: -x[1]):
        if cnt > 0:
            print(f"{cat}={cnt:.1f}", end="  ")
    print()
    
    print(f"天干十神: ", end="")
    for item in ss['gan_shi_shen']:
        print(f"{item['gan']}({item['shi_shen']})", end=" ")
    print()
    
    # 地支持有
    ri_wx = wx['ri_wx']
    roots = []
    for zhi in bazi.zhi_list:
        from bazi_immortal.constants import DZ_WU_XING, DZ_CANG_GAN
        if DZ_WU_XING[zhi] == ri_wx:
            roots.append(f"{zhi}(本气)")
        for cg in DZ_CANG_GAN.get(zhi, []):
            if TG_WU_XING[cg] == ri_wx:
                roots.append(f"{zhi}(藏{cg})")
                break
    print(f"地支有根: {roots if roots else '无根'}")
    
    # 天干印比数量
    helping = sum(1 for item in ss['gan_shi_shen'] if item['shi_shen'] in ('正印','偏印','比肩','劫财'))
    harming = sum(1 for item in ss['gan_shi_shen'] if item['shi_shen'] in ('正官','七杀','正财','偏财','食神','伤官'))
    print(f"天干印比: {helping}  天干克泄耗: {harming}")
    
    deepseek_sw = {'马云': '偏弱', '张一鸣': '偏弱', '李小龙': '偏弱', '林青霞': '偏强'}
    print(f"\n>> 引擎: {wx['strong_weak']}  vs  DeepSeek: {deepseek_sw[name]}")
    if wx['strong_weak'] != deepseek_sw[name]:
        print(f"   ⚠️ 方向相反！")
    else:
        print(f"   ✅ 一致")