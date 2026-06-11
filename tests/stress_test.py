"""
1000人批量测试 — 压测引擎的稳定性和逻辑一致性
随机生成生辰八字，验证每个环节的合理性
"""

import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collections import Counter, defaultdict
from bazi_immortal import (
    calculate_bazi,
    analyze_ri_zuo_strong_weak,
    analyze_all_shi_shen,
    calculate_da_yun, get_liu_nian, analyze_liu_nian,
    find_shen_sha,
)
from bazi_immortal.constants import (
    TIAN_GAN, DI_ZHI,
)
from bazi_immortal.wuxing import WU_XING_LIST
random.seed(42)

# ─── 随机生辰生成器 ───
def random_birth():
    """生成随机公历出生日期"""
    year = random.randint(1900, 2020)
    month = random.randint(1, 12)
    
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
        days_in_month[1] = 29
    day = random.randint(1, days_in_month[month - 1])
    
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    gender = random.choice(["男", "女"])
    
    return year, month, day, hour, minute, gender


# ─── 一致性校验规则 ───
def check_result(name, idx, bazi, wx, ss, da_yun, shensha):
    """校验单条结果的合理性，返回错误列表"""
    errors = []
    
    # 1. 八字格式检查
    gan_zhi_str = "".join(p.gan_zhi for p in bazi.si_zhu)
    if len(gan_zhi_str) != 8:
        errors.append(f"八字长度异常: {gan_zhi_str}")
    
    # 2. 每个天干地支都有效
    for p in bazi.si_zhu:
        if p.tian_gan not in TIAN_GAN:
            errors.append(f"无效天干: {p.tian_gan}")
        if p.di_zhi not in DI_ZHI:
            errors.append(f"无效地支: {p.di_zhi}")
    
    # 3. 五行分布各值非负
    for wx_name, count in wx["distribution"].items():
        if count < 0:
            errors.append(f"五行{wx_name}负值: {count}")
    
    # 4. 用神忌神不能重叠
    for ug in wx["useful_god"]:
        if ug in wx["avoid_god"]:
            errors.append(f"用神忌神重叠: {ug}")
    
    # 5. 用神忌神不能为空
    if not wx["useful_god"]:
        errors.append("用神为空")
    if not wx["avoid_god"]:
        errors.append("忌神为空")
    
    # 6. 用神忌神必须是有效五行
    for ug in wx["useful_god"]:
        if ug not in WU_XING_LIST:
            errors.append(f"用神无效五行: {ug}")
    for ag in wx["avoid_god"]:
        if ag not in WU_XING_LIST:
            errors.append(f"忌神无效五行: {ag}")
    
    # 7. 强弱判断必须有效
    valid_sw = {"身强", "偏强", "中和", "偏弱", "身弱", "从强", "从弱"}
    if wx["strong_weak"] not in valid_sw:
        errors.append(f"无效强弱状态: {wx['strong_weak']}")
    
    # 8. 得分范围合理
    if not (-10 <= wx["score"] <= 10):
        errors.append(f"得分异常: {wx['score']}")
    
    # 9. 十神统计每个值非负
    for ss_name, count in ss["counts"].items():
        if count < 0:
            errors.append(f"十神{ss_name}负值: {count}")
    
    # 10. 大运步数必须是8步
    if len(da_yun["da_yun_list"]) != 8:
        errors.append(f"大运步数异常: {len(da_yun['da_yun_list'])}")
    
    # 11. 大运每步都有关键字段
    for step, yun in enumerate(da_yun["da_yun_list"]):
        if not yun.get("gan_zhi"):
            errors.append(f"大运{step}无干支")
        if not yun.get("shi_shen"):
            errors.append(f"大运{step}无十神")
    
    # 12. 神煞每个都有位置和含义
    for s_name, s_info in shensha.items():
        if not s_info.get("positions"):
            errors.append(f"神煞{s_name}无位置")
        if not s_info.get("meaning"):
            errors.append(f"神煞{s_name}无含义")
    
    return errors


# ─── 主测试逻辑 ───
def run_batch(size=1000):
    print(f"🚀 开始批量测试 {size} 人...")
    print("=" * 70)
    
    all_errors = []
    sample_counter = 0
    
    # 统计用
    sw_dist = Counter()
    wx_dist = Counter()
    ri_gan_dist = Counter()
    gender_dist = Counter()
    shensha_count_total = 0
    
    for i in range(size):
        year, month, day, hour, minute, gender = random_birth()
        
        try:
            bazi = calculate_bazi(year, month, day, hour, minute, gender)
            wx = analyze_ri_zuo_strong_weak(bazi)
            ss = analyze_all_shi_shen(bazi)
            da_yun = calculate_da_yun(bazi)
            shensha = find_shen_sha(bazi)
            
            # 校验
            uid = f"#{i+1}({year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d} {gender})"
            errors = check_result(uid, i, bazi, wx, ss, da_yun, shensha)
            
            if errors:
                all_errors.append((uid, str(bazi), errors))
            
            # 统计
            sw_dist[wx["strong_weak"]] += 1
            wx_dist[wx["ri_wx"]] += 1
            ri_gan_dist[bazi.ri_gan] += 1
            gender_dist[gender] += 1
            shensha_count_total += len(shensha)
            sample_counter += 1
            
        except Exception as e:
            all_errors.append((f"#{i+1}", "EXCEPTION", [str(e)]))
        
        # 进度
        if (i + 1) % 200 == 0:
            print(f"  进度: {i+1}/{size}，当前错误: {len(all_errors)}")
    
    # ─── 输出报告 ───
    print(f"\n{'='*70}")
    print(f"📊 批量测试报告")
    print(f"{'='*70}")
    print(f"\n总样本: {sample_counter}")
    print(f"异常数: {len(all_errors)}")
    
    if all_errors:
        print(f"\n❌ 异常详情:")
        # 按类型分组
        error_types = Counter()
        for uid, bazi_str, errs in all_errors:
            for e in errs:
                error_types[e] += 1
        
        print("\n错误类型分布:")
        for err_type, count in error_types.most_common():
            print(f"  · [{count}次] {err_type}")
        
        # 显示前5个异常
        print(f"\n前5个异常样本:")
        for uid, bazi_str, errs in all_errors[:5]:
            print(f"  {uid}")
            print(f"    八字: {bazi_str}")
            for e in errs[:3]:
                print(f"    ⚠ {e}")
    else:
        print("  ✅ 零异常！")
    
    # ─── 统计分布 ───
    print(f"\n{'='*70}")
    print("📈 统计分布")
    print(f"{'='*70}")
    
    print(f"\n性别分布:")
    for g, c in gender_dist.most_common():
        print(f"  {g}: {c}人 ({c/size*100:.1f}%)")
    
    print(f"\n日主五行分布:")
    for wx_name in ["木", "火", "土", "金", "水"]:
        c = wx_dist.get(wx_name, 0)
        bar = "█" * max(1, c // 5)
        print(f"  {wx_name}: {c:3d}人 ({c/size*100:5.1f}%) {bar}")
    
    print(f"\n日干分布:")
    for gan in TIAN_GAN:
        c = ri_gan_dist.get(gan, 0)
        if c > 0:
            print(f"  {gan}: {c:3d}人 ({c/size*100:5.1f}%)")
    
    print(f"\n强弱分布:")
    for sw in ["从强", "身强", "偏强", "中和", "偏弱", "身弱", "从弱"]:
        c = sw_dist.get(sw, 0)
        if c > 0:
            pct = c / size * 100
            bar = "█" * max(1, c // 5)
            print(f"  {sw}: {c:4d}人 ({pct:5.1f}%) {bar}")
    
    avg_shensha = shensha_count_total / max(sample_counter, 1)
    print(f"\n人均神煞: {avg_shensha:.1f}个")
    
    # 取样检查：输出几个有代表性的结果
    print(f"\n{'='*70}")
    print("🔍 抽样检查（5个随机样本）")
    print(f"{'='*70}")
    
    # 重新生成5个样本展示
    for i in range(5):
        year, month, day, hour, minute, gender = random_birth()
        bazi = calculate_bazi(year, month, day, hour, minute, gender)
        wx = analyze_ri_zuo_strong_weak(bazi)
        print(f"\n  #{i+1}: {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d} {gender}")
        print(f"     八字: {' '.join(p.gan_zhi for p in bazi.si_zhu)}")
        print(f"     日主: {bazi.ri_gan}({wx['ri_wx']})")
        print(f"     季节: {wx.get('season', '?')} | 月令: {wx['monthly_state']}")
        print(f"     强弱: {wx['strong_weak']} (得分{wx['score']})")
        print(f"     用神: {'/'.join(wx['useful_god'])} 忌神: {'/'.join(wx['avoid_god'])}")
        print(f"     用神忌神不重叠: {'✅' if not any(ug in wx['avoid_god'] for ug in wx['useful_god']) else '❌'}")
    
    return len(all_errors)


if __name__ == "__main__":
    total_errors = run_batch(1000)
    print(f"\n{'='*70}")
    if total_errors == 0:
        print("🎉 1000人全部通过！引擎逻辑一致，无异常。")
    else:
        print(f"⚠ 发现 {total_errors} 个异常，需要修复。")
    print(f"{'='*70}")
    
    sys.exit(0 if total_errors == 0 else 1)