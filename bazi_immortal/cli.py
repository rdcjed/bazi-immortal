"""
命运道士 - CLI 命令行工具
输入生辰八字，输出完整运势报告
"""

import argparse
import sys
from datetime import datetime
from typing import Dict, List, Optional

from .calculator import calculate_bazi, bazi_to_string, BaZi
from .wuxing import analyze_ri_zuo_strong_weak, analyze_wuxing_distribution, format_wuxing_analysis, get_season
from .shisheng import analyze_all_shi_shen, format_shi_shen_analysis
from .dayun import calculate_da_yun, get_liu_nian, analyze_liu_nian, format_da_yun
from .shensha import find_shen_sha, format_shen_sha


def generate_fortune_report(bazi: BaZi, liu_nian_year: int = None) -> str:
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
    da_yun_result = calculate_da_yun(bazi)
    parts.append(format_da_yun(da_yun_result))
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
        liu_nian_year
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


def generate_synthesis(
    bazi: BaZi,
    wx_result: Dict,
    ss_result: Dict,
    da_yun_result: Dict,
    ln_analysis: Dict,
    year: int,
) -> str:
    """生成综合运势解读"""
    parts = []
    parts.append("【综合运势解读】")
    
    ri_gan = bazi.ri_gan
    ri_wx = wx_result["ri_wx"]
    strong_weak = wx_result["strong_weak"]
    useful_god = wx_result["useful_god"]
    avoid_god = wx_result["avoid_god"]

    # 整体命格评价
    gan_wx_desc = {
        "甲": "参天大树", "乙": "花草藤蔓",
        "丙": "太阳之火", "丁": "灯烛之火",
        "戊": "泰山之土", "己": "田园之土",
        "庚": "钢铁刀剑", "辛": "珠宝玉石",
        "壬": "江河之水", "癸": "雨露之水",
    }

    parts.append(f"命主为{ri_gan}{ri_wx}命（{gan_wx_desc.get(ri_gan, '')}），"
                 f"综合分析为{strong_weak}之命。")
    parts.append(f"命局{ri_wx}喜：{'、'.join(useful_god)}，忌：{'、'.join(avoid_god)}。")

    # 先天特质
    parts.append("")
    parts.append("【先天命格特质】")
    category = ss_result["category_counts"]
    features = []
    
    if category.get("官杀", 0) >= 2:
        features.append("官杀旺——有管理能力和事业心，但压力也大")
    if category.get("印枭", 0) >= 2:
        features.append("印星旺——学习能力强，贵人运不错")
    if category.get("财", 0) >= 2:
        features.append("财星旺——财运不错，但要看身强身弱，弱者财来财去")
    if category.get("食伤", 0) >= 2:
        features.append("食伤旺——才华出众，适合创意类工作")
    if category.get("比劫", 0) >= 2:
        features.append("比劫旺——朋友多但也容易被拖累，不适合合伙")

    features.append(f"日主{strong_weak}，{'喜补' + '、'.join(useful_god) + '，避免' + '、'.join(avoid_god)}")
    
    for f in features:
        parts.append(f"· {f}")

    # 流年解读
    parts.append("")
    ln_ss = ln_analysis["liu_nian_shi_shen"]
    ln_year = ln_analysis["liu_nian"]["gan_zhi"]

    # 流年十神白话
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
        report = generate_fortune_report(bazi, liu_nian)
        print(report)
    except Exception as e:
        print(f"❌ 计算出错：{e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()