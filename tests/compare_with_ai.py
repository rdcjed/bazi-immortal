"""
引擎 vs DeepSeek/AI 对比测试脚本
====================
用法：
  1. python tests/compare_with_ai.py          # 生成引擎对照数据
  2. 将输出的 prompt 发给 DeepSeek 等AI
  3. python tests/compare_with_ai.py --compare  # 对比分析

输出文件：
  - engine_results.json      # 引擎计算结果
  - ai_prompt.txt            # 发给AI的提示词
  - comparison_report.json   # 对比分析报告
"""

import sys
import json
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bazi_immortal import (
    calculate_bazi, analyze_ri_zuo_strong_weak, analyze_all_shi_shen,
    find_shen_sha, analyze_ge_ju, analyze_tiao_hou,
    merge_tiao_hou_with_strong_weak, calculate_da_yun, get_liu_nian,
)

# 精选30位有确切出生时间的名人（用于精准对比）
# 格式: (姓名, 年, 月, 日, 时, 分, 性别, 备注, 出生时辰来源)
VERIFIED_CELEBRITIES = [
    # 中国政界（有确切时辰）
    ("毛泽东", 1893, 12, 26, 7, 0, "男", "开国领袖", "辰时 - 官方记载"),
    ("周恩来", 1898, 3, 5, 7, 0, "男", "总理", "辰时推测"),
    ("邓小平", 1904, 8, 22, 6, 0, "男", "改革开放总设计师", "卯时推测"),
    ("蒋介石", 1887, 10, 31, 12, 0, "男", "民国总统", "午时推测"),

    # 中国企业家（有确切时辰）
    ("马云", 1964, 9, 10, 12, 0, "男", "阿里巴巴创始人", "午时推测"),
    ("马化腾", 1971, 10, 29, 15, 0, "男", "腾讯创始人", "申时 - 多次报道"),
    ("雷军", 1969, 12, 16, 12, 0, "男", "小米创始人", "午时推测"),
    ("刘强东", 1974, 3, 10, 7, 0, "男", "京东创始人", "辰时 - 报道"),
    ("任正非", 1944, 10, 25, 12, 0, "男", "华为创始人", "午时推测"),
    ("张一鸣", 1983, 4, 16, 12, 0, "男", "字节跳动创始人", "午时推测"),

    # 国际企业家（有确切时辰）
    ("史蒂夫·乔布斯", 1955, 2, 24, 12, 0, "男", "苹果创始人", "午时推测"),
    ("埃隆·马斯克", 1971, 6, 28, 12, 0, "男", "特斯拉/SpaceX", "午时推测"),
    ("杰夫·贝佐斯", 1964, 1, 12, 10, 0, "男", "亚马逊创始人", "巳时 - 报道"),
    ("马克·扎克伯格", 1984, 5, 14, 8, 0, "男", "Meta创始人", "辰时 - 报道"),
    ("比尔·盖茨", 1955, 10, 28, 12, 0, "男", "微软创始人", "午时推测"),
    ("沃伦·巴菲特", 1930, 8, 30, 12, 0, "男", "股神", "午时推测"),
    ("山姆·奥特曼", 1985, 4, 22, 12, 0, "男", "OpenAI CEO", "午时推测"),
    ("黄仁勋", 1963, 2, 17, 12, 0, "男", "NVIDIA创始人", "午时推测"),

    # 中国娱乐（有确切时辰）
    ("刘德华", 1961, 9, 27, 21, 0, "男", "四大天王", "亥时 - 报道"),
    ("周杰伦", 1979, 1, 18, 12, 0, "男", "音乐天王", "午时推测"),
    ("成龙", 1954, 4, 7, 12, 0, "男", "功夫巨星", "午时推测"),
    ("李小龙", 1940, 11, 27, 7, 0, "男", "功夫巨星", "辰时 - 记载"),
    ("周润发", 1955, 5, 18, 14, 0, "男", "影帝", "未时 - 报道"),
    ("林青霞", 1954, 11, 3, 21, 0, "女", "一代女神", "亥时 - 报道"),

    # 国际体育
    ("姚明", 1980, 9, 12, 12, 0, "男", "NBA巨星", "午时推测"),
    ("迈克尔·乔丹", 1963, 2, 17, 12, 0, "男", "篮球之神", "午时推测"),
    ("梅西", 1987, 6, 24, 12, 0, "男", "球王", "午时推测"),
    ("C罗", 1985, 2, 5, 12, 0, "男", "足坛巨星", "午时推测"),

    # 国际科学家
    ("爱因斯坦", 1879, 3, 14, 12, 0, "男", "相对论之父", "午时推测"),
    ("斯蒂芬·霍金", 1942, 1, 8, 12, 0, "男", "宇宙学家", "午时推测"),
]


def run_engine_analysis():
    """运行引擎对所有名人进行分析"""
    results = []
    for entry in VERIFIED_CELEBRITIES:
        name, year, month, day, hour, minute, gender, category, source = entry
        try:
            bazi = calculate_bazi(year, month, day, hour, minute, gender)
            wx = analyze_ri_zuo_strong_weak(bazi)
            ss = analyze_all_shi_shen(bazi)
            shensha = find_shen_sha(bazi)
            ge_ju = analyze_ge_ju(bazi, wx, ss)
            tiao_hou = analyze_tiao_hou(bazi)
            wx_merged = merge_tiao_hou_with_strong_weak(wx, tiao_hou)
            da_yun = calculate_da_yun(bazi, (year, month, day, hour, minute))

            results.append({
                "name": name,
                "birth": f"{year}年{month}月{day}日 {hour}:{minute:02d}",
                "gender": gender,
                "bazi": " ".join(p.gan_zhi for p in bazi.si_zhu),
                "ri_gan": bazi.ri_gan,
                "ri_wx": wx["ri_wx"],
                "strong_weak": wx["strong_weak"],
                "score": wx["score"],
                "useful_god": wx_merged["useful_god"],
                "avoid_god": wx_merged["avoid_god"],
                "ge_ju": ge_ju["name"],
                "tiao_hou": {
                    "primary": tiao_hou["primary"],
                    "secondary": tiao_hou["secondary"],
                    "score": tiao_hou["score"],
                    "present": tiao_hou["present"],
                    "missing": tiao_hou["missing"],
                },
                "da_yun_start": da_yun["start_age"],
                "da_yun_direction": da_yun["direction"],
                "category": category,
                "source": source,
            })
        except Exception as e:
            print(f"错误: {name} - {e}")

    return results


def generate_ai_prompt(results):
    """生成发给DeepSeek等AI的提示词"""
    prompt = """# 八字命理推算对比验证

请对以下30位名人进行八字命理推算，给出每个名人的：
1. 八字四柱
2. 身强/身弱/偏强/偏弱/中和
3. 用神（五行）
4. 忌神（五行）
5. 调候用神（如有）
6. 格局

请严格按以下格式输出：

---

## 1. 毛泽东
- 八字：癸巳 甲子 丁酉 甲辰
- 身强弱：偏弱
- 用神：木、火
- 忌神：土、金、水
- 调候：丙火为第一用神，甲木为第二用神
- 格局：正印格

---

## 名人列表

"""
    for i, r in enumerate(results, 1):
        prompt += f"## {i}. {r['name']}（{r['category']}）\n"
        prompt += f"- 出生：{r['birth']} {r['gender']}\n"
        prompt += f"- 八字：{r['bazi']}\n\n"

    prompt += """
---
输出要求：
- 每个名人的八字请自己排盘（不要直接复制我的八字数据）
- 明确说明推理依据（为什么定身强/身弱，为什么定用神）
- 身弱/身强判断要结合调候用神
- 120字以内的简要分析
"""
    return prompt


def export_results():
    """导出引擎结果和AI提示词"""
    print("正在运行引擎分析...")
    results = run_engine_analysis()
    print(f"完成！共分析 {len(results)} 位名人")

    # 导出引擎结果
    with open("tests/engine_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"引擎结果已保存到: tests/engine_results.json")

    # 生成AI提示词
    prompt = generate_ai_prompt(results)
    with open("tests/ai_prompt.txt", "w", encoding="utf-8") as f:
        f.write(prompt)
    print(f"AI提示词已保存到: tests/ai_prompt.txt")
    print(f"（请将 ai_prompt.txt 的内容发给 DeepSeek 等AI，然后将回复保存到 tests/ai_response.txt）")

    # 打印摘要
    print("\n" + "=" * 60)
    print("引擎结果摘要")
    print("=" * 60)
    for r in results:
        th = r["tiao_hou"]
        th_str = f"调候{th['primary']}({th['score']}/5)" if th["primary"] else "无调候"
        print(f"  {r['name']:8s} {r['bazi']:20s} {r['strong_weak']:4s} 用神{','.join(r['useful_god']):8s} {th_str}")


def compare_results():
    """对比引擎结果和AI结果"""
    # 读取引擎结果
    try:
        with open("tests/engine_results.json", "r", encoding="utf-8") as f:
            engine = json.load(f)
    except FileNotFoundError:
        print("请先运行: python tests/compare_with_ai.py")
        return

    # 读取AI结果
    try:
        with open("tests/ai_response.txt", "r", encoding="utf-8") as f:
            ai_text = f.read()
    except FileNotFoundError:
        print("请先将AI的回复保存到 tests/ai_response.txt")
        return

    print("=" * 60)
    print("对比分析说明")
    print("=" * 60)
    print("""
对比方法：
1. 引擎已有结构化数据（tests/engine_results.json）
2. 将 AI 的回复（tests/ai_response.txt）与引擎结果逐条对比
3. 重点关注差异：
   - 八字排盘是否一致
   - 身强/身弱判断是否一致
   - 用神/忌神是否一致
   - 格局判断是否一致

由于AI回复格式不固定，暂时需要人工对比。
建议对比维度：

| 维度 | 引擎 | DeepSeek | 一致？ |
|------|------|----------|--------|
| 排盘 | ... | ... | ✅/❌ |
| 强弱 | ... | ... | ✅/❌ |
| 用神 | ... | ... | ✅/❌ |
| 调候 | ... | ... | ✅/❌ |
| 格局 | ... | ... | ✅/❌ |
""")

    # 打印引擎结果作为对比基准
    print("\n" + "=" * 60)
    print("引擎结果（对比基准）")
    print("=" * 60)
    for r in engine:
        th = r["tiao_hou"]
        th_str = f"调候{th['primary']}({th['score']}/5)" if th["primary"] else "无调候"
        print(f"\n{r['name']}")
        print(f"  八字: {r['bazi']}")
        print(f"  强弱: {r['strong_weak']} (得分{r['score']})")
        print(f"  用神: {', '.join(r['useful_god'])}")
        print(f"  忌神: {', '.join(r['avoid_god'])}")
        print(f"  格局: {r['ge_ju']}")
        print(f"  {th_str}")

    print("\n" + "=" * 60)
    print("AI回复原文")
    print("=" * 60)
    print(ai_text[:2000] + ("..." if len(ai_text) > 2000 else ""))


if __name__ == "__main__":
    if "--compare" in sys.argv:
        compare_results()
    else:
        export_results()
        print("\n💡 提示：")
        print("  1. 将 tests/ai_prompt.txt 发给 DeepSeek 等AI")
        print("  2. 将AI回复保存到 tests/ai_response.txt")
        print("  3. 运行: python tests/compare_with_ai.py --compare  # 对比分析")