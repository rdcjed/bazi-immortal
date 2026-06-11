"""
大规模压力测试 — 1万/10万随机生辰验证
只报错，不做冗余输出
"""

import sys, os, random, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collections import Counter
from bazi_immortal import (
    calculate_bazi,
    analyze_ri_zuo_strong_weak,
    analyze_all_shi_shen,
    calculate_da_yun,
    find_shen_sha,
)
from bazi_immortal.constants import TIAN_GAN, DI_ZHI
from bazi_immortal.wuxing import WU_XING_LIST

random.seed(42)

# 一次性预生成所有随机数据
def generate_batch(size):
    data = []
    for _ in range(size):
        year = random.randint(1900, 2020)
        month = random.randint(1, 12)
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
            days_in_month[1] = 29
        day = random.randint(1, days_in_month[month - 1])
        hour = random.randint(0, 23)
        gender = random.choice(["男", "女"])
        data.append((year, month, day, hour, 0, gender))
    return data


# 检查单条
def check_one(bazi, wx, ss, da_yun, shensha):
    errs = []
    for p in bazi.si_zhu:
        if p.tian_gan not in TIAN_GAN:
            errs.append(f"天干异常:{p.tian_gan}")
        if p.di_zhi not in DI_ZHI:
            errs.append(f"地支异常:{p.di_zhi}")
    for wx_n, c in wx["distribution"].items():
        if c < 0: errs.append(f"五行{wx_n}负值:{c}")
    for ug in wx["useful_god"]:
        if ug in wx["avoid_god"]: errs.append(f"用忌重叠:{ug}")
        if ug not in WU_XING_LIST: errs.append(f"用神无效:{ug}")
    for ag in wx["avoid_god"]:
        if ag not in WU_XING_LIST: errs.append(f"忌神无效:{ag}")
    if not wx["useful_god"]: errs.append("用神空")
    if not wx["avoid_god"]: errs.append("忌神空")
    if wx["strong_weak"] not in {"身强","偏强","中和","偏弱","身弱","从强","从弱"}:
        errs.append(f"强弱无效:{wx['strong_weak']}")
    for sn, si in shensha.items():
        if not si.get("positions"): errs.append(f"神煞{sn}无位置")
    return errs


def run(size):
    print(f"🚀 开始测试{size}人...")
    t0 = time.time()
    
    data = generate_batch(size)
    errors = []
    stats = Counter()
    wx_stats = Counter()
    last_report = 0
    
    for i, (y, m, d, h, mi, g) in enumerate(data):
        try:
            b = calculate_bazi(y, m, d, h, mi, g)
            w = analyze_ri_zuo_strong_weak(b)
            s = analyze_all_shi_shen(b)
            dy = calculate_da_yun(b)
            sh = find_shen_sha(b)
            
            e = check_one(b, w, s, dy, sh)
            if e:
                uid = f"#{i+1}({y}-{m:02d}-{d:02d} {h:02d} {g})"
                errors.append((uid, b, e))
            
            stats[w["strong_weak"]] += 1
            wx_stats[w["ri_wx"]] += 1
            
        except Exception as ex:
            errors.append((f"#{i+1} CRASH", None, [str(ex)]))
        
        # 每2000人报一次进度
        pct = (i + 1) / size * 100
        elapsed = time.time() - t0
        if (i + 1) - last_report >= max(2000, size // 10):
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            print(f"  [{i+1}/{size}] {pct:.0f}% | 耗时{elapsed:.0f}s | {rate:.0f}人/秒 | 错误{len(errors)}")
            last_report = i + 1
    
    t = time.time() - t0
    print(f"\n{'='*60}")
    print(f"📊 {size}人测试完成")
    print(f"  耗时: {t:.1f}s ({size/t:.0f}人/秒)")
    print(f"  错误: {len(errors)}")
    
    if errors:
        # 按错误类型统计
        err_types = Counter()
        for uid, b, errs in errors:
            for e in errs:
                err_types[e] += 1
        print(f"\n❌ 错误类型:")
        for e, c in err_types.most_common(10):
            print(f"  [{c}次] {e}")
        print(f"\n前3个异常样本:")
        for uid, b, errs in errors[:3]:
            print(f"  {uid}")
            for e in errs[:3]:
                print(f"    ⚠ {e}")
    else:
        print(f"  ✅ 零异常！")
    
    print(f"\n📈 强弱分布:")
    for sw in ["从强","身强","偏强","中和","偏弱","身弱","从弱"]:
        c = stats.get(sw, 0)
        if c > 0:
            print(f"  {sw}: {c:5d} ({c/size*100:5.1f}%)")
    
    print(f"\n📈 日主五行分布:")
    for wx in ["木","火","土","金","水"]:
        c = wx_stats.get(wx, 0)
        print(f"  {wx}: {c:5d} ({c/size*100:5.1f}%)")
    
    return len(errors)


# 级联测试：先1万，通过则10万
if __name__ == "__main__":
    n_errors = run(10000)
    if n_errors == 0:
        print(f"\n{'='*60}")
        print("🎉 1万人全部通过，继续10万人测试...")
        print(f"{'='*60}\n")
        n_errors2 = run(100000)
        if n_errors2 == 0:
            print(f"\n{'='*60}")
            print("🎉🎉🎉 10万人全部通过！引擎稳定可靠。")
            print(f"{'='*60}")
        else:
            print(f"\n⚠ 10万人测试发现{n_errors2}个错误")
    else:
        print(f"\n⚠ 1万人测试发现{n_errors}个错误，先修bug再继续")
    
    sys.exit(0 if n_errors == 0 else 1)