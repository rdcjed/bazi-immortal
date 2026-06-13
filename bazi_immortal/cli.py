"""
命运道士 - CLI 命令行工具
输入生辰八字，输出完整运势报告
"""

import argparse
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .calculator import calculate_bazi, bazi_to_string, BaZi
from .wuxing import analyze_ri_zuo_strong_weak, analyze_wuxing_distribution, format_wuxing_analysis, get_season
from .shisheng import analyze_all_shi_shen, format_shi_shen_analysis
from .dayun import calculate_da_yun, get_liu_nian, analyze_liu_nian, format_da_yun
from .shensha import find_shen_sha, format_shen_sha


def generate_fortune_report(bazi: BaZi, liu_nian_year: int = None,
                            birth_time: Optional[Tuple[int, int, int, int, int]] = None) -> str:
    """
    生成完整的运势报告

    这是整个引擎的核心输出——把所有分析模块整合成一份报告
    """
    if liu_nian_year is None:
        liu_nian_year = datetime.now().year

    parts = []
    parts.append("=" * 60)
    parts.append("     ☯ 命运道士 - 八字命理运势报告 ☯")
    parts.append("=" * 60)
    parts.append("")

    # ─── 1. 八字排盘 ───
    parts.append("【八字排盘】")
    parts.append(bazi_to_string(bazi))
    parts.append("")

    # ─── 2. 五行分析 ───
    wx_result = analyze_ri_zuo_strong_weak(bazi)
    parts.append(format_wuxing_analysis(wx_result))
    parts.append("")

    # ─── 3. 十神分析 ───
    ss_result = analyze_all_shi_shen(bazi)
    parts.append(format_shi_shen_analysis(ss_result))
    parts.append("")

    # ─── 4. 神煞 ───
    shensha_result = find_shen_sha(bazi)
    parts.append(format_shen_sha(shensha_result))
    parts.append("")

    # ─── 5. 大运 ───
    da_yun_result = calculate_da_yun(bazi, birth_time)
    # 计算当前年龄
    if birth_time:
        from datetime import datetime as dt
        by, bm, bd, bh, bmi = birth_time
        try:
            birth_dt = dt(by, bm, bd, bh, bmi)
            ref_dt = dt(liu_nian_year, 7, 1)  # 以年中为参考
            current_age = (ref_dt - birth_dt).days / 365.25
        except:
            current_age = liu_nian_year - by
        current_age = max(0, round(current_age, 1))
    else:
        current_age = 30
    parts.append(format_da_yun(da_yun_result, current_age))
    parts.append("")

    # ─── 6. 当前流年 ───
    liu_nian = get_liu_nian(liu_nian_year)
    ln_analysis = analyze_liu_nian(bazi, liu_nian_year)
    parts.append(f"【{liu_nian_year}年流年运势】")
    parts.append(f"该年干支：{liu_nian['tian_gan']}{liu_nian['di_zhi']}")
    parts.append(f"太岁关系：{'、'.join(ln_analysis['tai_sui_relations'])}")
    parts.append(f"流年天干十神：{ln_analysis['liu_nian_shi_shen']}")

    if ln_analysis["pillar_relations"]:
        parts.append("流年与四柱关系：")
        for pr in ln_analysis["pillar_relations"]:
            rel_str = "、".join(pr["relations"])
            parts.append(f"  · 与{pr['pillar']}{pr['zhi']}相{rel_str}")
    parts.append("")

    # ─── 7. 综合运势解读 ───
    parts.append(generate_synthesis(
        bazi, wx_result, ss_result, da_yun_result, ln_analysis,
        liu_nian_year, shensha_result
    ))
    parts.append("")

    # ─── 8. 建议 ───
    parts.append(generate_advice(wx_result, ss_result))
    parts.append("")

    # ─── 9. 注意事项 ───
    parts.append("【温馨提示】")
    parts.append("命理分析反映的是一种趋势和可能性，而非绝对的命运。")
    parts.append("人生的精彩在于选择与努力，命运掌握在自己手中。")
    parts.append("本报告仅供参考娱乐，重大决策请结合现实情况。")
    parts.append("")
    parts.append("=" * 60)
    parts.append(f"    云中子 · 命运道士    {liu_nian_year}")
    parts.append("=" * 60)

    return "\n".join(parts)


def identify_pattern(bazi, wx_result, ss_result):
    """识别经典命理格局"""
    ri_gan = bazi.ri_gan
    ri_wx = wx_result["ri_wx"]
    sw = wx_result["strong_weak"]
    cat = ss_result["category_counts"]
    useful = wx_result["useful_god"]
    avoid = wx_result["avoid_god"]
    
    guan = cat.get("官杀", 0)
    yin = cat.get("印枭", 0)
    cai = cat.get("财", 0)
    shi = cat.get("食伤", 0)
    bi = cat.get("比劫", 0)
    
    # 杀印相生格：官杀旺 + 印星旺 + 印为用神
    from .wuxing import WU_XING_KE, WU_XING_SHENG
    guan_wx = None
    for k, v in WU_XING_KE.items():
        if v == ri_wx:
            guan_wx = k
            break
    yin_wx = None
    for k, v in WU_XING_SHENG.items():
        if v == ri_wx:
            yin_wx = k
            break
    
    patterns = []
    
    # 1. 杀印相生格
    if guan >= 2.0 and yin >= 1.5 and sw in ("偏弱", "身弱"):
        patterns.append(("杀印相生格", 
            "官杀旺而有印星化解，以印化杀。这种格局的人越是压力大越能激发潜力，"
            "能在逆境中崛起，往往大器晚成。毛泽东、任正非都是这种格局。"))
    
    # 2. 食神制杀格
    if guan >= 2.0 and shi >= 1.5 and yin_wx in useful:
        patterns.append(("食神制杀格",
            "以才华智慧（食伤）制衡压力挑战（七杀）。这种格局的人智勇双全，"
            "能在竞争中以智取胜，适合军警、管理、竞技类职业。"))
    
    # 3. 伤官配印格
    if shi >= 2.0 and yin >= 1.5 and yin_wx in useful:
        patterns.append(("伤官配印格",
            "才华（伤官）与学识（正印）相配。这种格局的人才华横溢又有学历加持，"
            "既聪明又有涵养，艺术造诣和学术成就都很高。"))
    
    # 4. 财官双美格
    if cai >= 1.5 and guan >= 1.5 and sw in ("身强", "偏强"):
        patterns.append(("财官双美格",
            "财星生官杀，官杀护财。这种格局的人既有赚钱能力又有社会地位，"
            "事业财运双向发展，适合经商从政。马云、马化腾都是此格局。"))
    
    # 5. 从强/从弱格
    if sw == "从强":
        patterns.append(("从强格",
            "全局都是印比同党，一气专旺。这种格局的人意志力极强，"
            "不达目的不罢休。运势顺时一飞冲天，逆时则一落千丈，大起大落之命。"))
    elif sw == "从弱":
        patterns.append(("从弱格",
            "全局都是克泄耗，无一帮身。这种格局的人适应能力极强，"
            "善于借力使力，借别人的资源成就自己的事业，适合与人合作。"))
    
    # 6. 比劫夺财格
    if bi >= 3.0 and cai >= 1.5 and sw in ("偏强", "身强"):
        patterns.append(("比劫夺财格",
            "朋友兄弟多（比劫旺），但也容易因朋友破财。合作生意需谨慎，"
            "适合个人单干或技术型独立工作。"))
    
    # 7. 食伤生财格
    if shi >= 2.0 and cai >= 1.5 and shi >= cai:
        patterns.append(("食伤生财格",
            "以才华技艺（食伤）生财。这种格局的人靠本事吃饭，技术流、创意型人才，"
            "适合IT、设计、咨询、演艺等行业。"))
    
    return patterns


def generate_synthesis(
    bazi: BaZi,
    wx_result: Dict,
    ss_result: Dict,
    da_yun_result: Dict,
    ln_analysis: Dict,
    year: int,
    shensha_result: Dict = None,
) -> str:
    """生成综合运势解读（增强版）"""
    parts = []
    parts.append("【综合运势解读】")
    
    ri_gan = bazi.ri_gan
    ri_wx = wx_result["ri_wx"]
    strong_weak = wx_result["strong_weak"]
    useful_god = wx_result["useful_god"]
    avoid_god = wx_result["avoid_god"]
    season = wx_result.get("season", "?")
    
    # 计算财/官/印/食伤/比劫对应的五行
    try:
        from .wuxing import WU_XING_KE, WU_XING_SHENG
        cai_wx = WU_XING_KE.get(ri_wx)  # 我克=财
        shi_wx = WU_XING_SHENG.get(ri_wx)  # 我生=食伤
        # 克我=官杀
        guan_wx = None
        for k, v in WU_XING_KE.items():
            if v == ri_wx:
                guan_wx = k
                break
        # 生我=印枭
        yin_wx = None
        for k, v in WU_XING_SHENG.items():
            if v == ri_wx:
                yin_wx = k
                break
        bi_wx = ri_wx  # 比劫=我
    except:
        cai_wx = shi_wx = guan_wx = yin_wx = bi_wx = None

    # 整体命格评价
    gan_wx_desc = {
        "甲": "参天大树", "乙": "花草藤蔓",
        "丙": "太阳之火", "丁": "灯烛之火",
        "戊": "泰山之土", "己": "田园之土",
        "庚": "钢铁刀剑", "辛": "珠宝玉石",
        "壬": "江河之水", "癸": "雨露之水",
    }

    ri_desc = gan_wx_desc.get(ri_gan, "")
    
    # ─── 格局判断 ───
    patterns = identify_pattern(bazi, wx_result, ss_result)
    
    parts.append(f"命主为{ri_gan}{ri_wx}命（{ri_desc}），出生于{season}季。")
    parts.append(f"综合推断：{strong_weak}之命。命局{'喜' + '、'.join(useful_god)}，{'忌' + '、'.join(avoid_god)}。")
    
    if patterns:
        for p_name, p_desc in patterns:
            parts.append(f"格局：{p_name} ——{p_desc}")

    # ─── 先天特质 ───
    parts.append("")
    parts.append("【先天命格特质】")
    features = []
    category = ss_result["category_counts"]
    
    # 使用新的分情况分析引擎
    try:
        from .contextual import analyze_shi_shen_features, get_guiren_analysis
        new_features = analyze_shi_shen_features(bazi.ri_gan, ss_result, wx_result)
        for text, conf in new_features:
            features.append(text)
    except ImportError:
        pass
    
    for f in features:
        parts.append(f"· {f}")
    
    # ─── 贵人综合评估（独立板块） ───
    try:
        if shensha_result:
            from .contextual import get_guiren_analysis as ga
            guiren_data = ga(shensha_result)
            parts.append("")
            parts.append(f"【贵人综合评估】— {guiren_data['level']}")
            parts.append(guiren_data['summary'])
            for g in guiren_data['guiren_list']:
                parts.append(f"· {g['name']}：{g['desc']}")
            # 十神贵人补充
            guan_cat = category.get("官杀", 0)
            if guan_cat >= 2.0:
                parts.append(f"· 官杀旺（{guan_cat:.1f}）：职场/上司贵人运强")
    except ImportError:
        pass

    # ─── 流年解读 ───
    ln_ss = ln_analysis["liu_nian_shi_shen"]
    ln_year = ln_analysis["liu_nian"]["gan_zhi"]

    ss_forecast = {
        "正官": "事业运旺，有晋升机会，但也需注意压力",
        "七杀": "挑战与机遇并存，有突破但也有阻力",
        "正印": "学习运佳，贵人运好，适合进修提升",
        "偏印": "偏门路数有收获，但要注意判断",
        "正财": "正财运好，工资收入稳定增长",
        "偏财": "偏财机会多，适合投资但不宜贪心",
        "比肩": "朋友助力多，但也需防竞争",
        "劫财": "开销大，谨防投资亏损和朋友借钱",
        "食神": "才华显现，有意外惊喜和口福",
        "伤官": "名利显露但容易得罪人，言语需谨慎",
    }

    parts.append("")
    parts.append(f"【{year}年流年解读】")
    parts.append(f"流年{ln_year}，天干为{ln_ss}运。")
    parts.append(ss_forecast.get(ln_ss, f"{ln_ss}运，需结合具体八字判断。"))

    # 太岁
    tai = ln_analysis["tai_sui_relations"]
    if "值太岁" in tai:
        parts.append("⚠ 今年值太岁（本命年），运势波动较大，宜静不宜动，多行善事。")
    if "冲太岁" in tai:
        parts.append("⚠ 今年冲太岁，变动较多，注意人际关系和合作事宜。")
    if "刑太岁" in tai:
        parts.append("⚠ 今年刑太岁，注意口舌是非和法律文书。")
    if "害太岁" in tai:
        parts.append("⚠ 今年害太岁，防小人暗算，凡事多留个心眼。")

    return "\n".join(parts)


def generate_advice(wx_result: Dict, ss_result: Dict) -> str:
    """生成具体建议"""
    parts = []
    parts.append("【趋吉避凶建议】")

    useful_god = wx_result["useful_god"]
    avoid_god = wx_result["avoid_god"]

    from .wuxing import WU_XING_COLORS, WU_XING_DIRECTIONS, WU_XING_ORGANS, WU_XING_SEASONS

    # 五行建议
    for ug in useful_god:
        color = WU_XING_COLORS.get(ug, "?")
        direction = WU_XING_DIRECTIONS.get(ug, "?")
        organ = WU_XING_ORGANS.get(ug, "?")
        season = WU_XING_SEASONS.get(ug, "?")
        parts.append(f"· 用神为{ug}：多穿{color}色系，往{direction}发展有利，"
                     f"{season}季运势最佳，注意保养{organ}。")

    for ag in avoid_god:
        color = WU_XING_COLORS.get(ag, "?")
        direction = WU_XING_DIRECTIONS.get(ag, "?")
        parts.append(f"· 忌神为{ag}：少穿{color}色系，避免往{direction}发展。")

    # 行业建议
    parts.append("")
    wuxing_careers = {
        "木": "教育、文化、医疗、环保、园艺、出版",
        "火": "互联网、能源、设计、餐饮、传媒、娱乐",
        "土": "房地产、建筑、农业、矿业、仓储、顾问",
        "金": "金融、法律、机械、汽车、科技、军警",
        "水": "物流、旅游、贸易、媒体、艺术、水产",
    }
    for ug in useful_god:
        careers = wuxing_careers.get(ug, "")
        if careers:
            parts.append(f"· 适合行业（{ug}）：{careers}")

    return "\n".join(parts)


def parse_time(time_str: str) -> tuple:
    """解析时间字符串 → (hour, minute)"""
    try:
        if not time_str:
            return (12, 0)
        if ":" in time_str:
            h, m = time_str.split(":")
            return (int(h), int(m))
        # 时辰名称
        shi_chen_map = {
            "子": (23, 0), "丑": (1, 0), "寅": (3, 0), "卯": (5, 0),
            "辰": (7, 0), "巳": (9, 0), "午": (11, 0), "未": (13, 0),
            "申": (15, 0), "酉": (17, 0), "戌": (19, 0), "亥": (21, 0),
        }
        if time_str in shi_chen_map:
            return shi_chen_map[time_str]
        h = int(time_str)
        return (h, 0)
    except:
        return (12, 0)


def main():
    parser = argparse.ArgumentParser(
        description="命运道士 - 八字命理运势推算工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  bazi 1990 5 15 12:00 男
  bazi 1990 5 15 --hour 午 --gender 女
  bazi 1990 5 15 子 男 --year 2026

时辰对照:
  子(23-01) 丑(01-03) 寅(03-05) 卯(05-07)
  辰(07-09) 巳(09-11) 午(11-13) 未(13-15)
  申(15-17) 酉(17-19) 戌(19-21) 亥(21-23)
        """
    )
    parser.add_argument("year", type=int, help="出生年份（公历）")
    parser.add_argument("month", type=int, help="出生月份（1-12）")
    parser.add_argument("day", type=int, help="出生日期")
    parser.add_argument("time", nargs="?", default="12:00",
                        help="出生时间，支持 12:00 / 午 / 8 等格式")
    parser.add_argument("gender", nargs="?", default="男",
                        help="性别：男/女")
    parser.add_argument("--hour", "-H", help="出生小时（替代time参数）")
    parser.add_argument("--gender", "-g", dest="gender_flag", 
                        help="性别：男/女")
    parser.add_argument("--year", "-y", type=int, dest="liu_nian",
                        help="要查询的流年年份（默认当前年份）")
    parser.add_argument("--version", "-V", action="store_true",
                        help="显示版本信息")

    args = parser.parse_args()

    if args.version:
        from . import __version__
        print(f"命运道士 v{__version__}")
        return

    gender = args.gender_flag or args.gender
    time_str = args.hour if args.hour else args.time

    hour, minute = parse_time(time_str)
    liu_nian = args.liu_nian or datetime.now().year

    try:
        bazi = calculate_bazi(args.year, args.month, args.day, hour, minute, gender)
        birth_time = (args.year, args.month, args.day, hour, minute)
        report = generate_fortune_report(bazi, liu_nian, birth_time)
        print(report)
    except Exception as e:
        print(f"❌ 计算出错：{e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()