"""
命运道士 Web 服务
Flask 后端，提供八字推算 API
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request, send_from_directory
from bazi_immortal import (
    calculate_bazi, bazi_to_string,
    analyze_ri_zuo_strong_weak, analyze_all_shi_shen,
    calculate_da_yun, get_liu_nian, analyze_liu_nian,
    find_shen_sha,
)
from bazi_immortal.wuxing import (
    analyze_wuxing_distribution, WU_XING_COLORS, WU_XING_DIRECTIONS,
    WU_XING_ORGANS, WU_XING_SEASONS, WU_XING_LIST,
)

app = Flask(__name__, static_folder=None)

# ─── 静态文件 ───
HTML_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web")


@app.route("/")
def index():
    return send_from_directory(HTML_DIR, "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(HTML_DIR, path)


# ─── API ───

@app.route("/api/bazi")
def api_bazi():
    try:
        year = request.args.get("year", type=int)
        month = request.args.get("month", type=int)
        day = request.args.get("day", type=int)
        hour = request.args.get("hour", type=int, default=12)
        gender = request.args.get("gender", default="男")
        liunian = request.args.get("liunian", type=int, default=0)

        if not all([year, month, day]):
            return jsonify({"error": "请填写完整的出生年月日"}), 400

        bazi = calculate_bazi(year, month, day, hour, 0, gender)
        liunian_year = liunian if liunian else 2026

        # ─── 五行分析 ───
        wx = analyze_ri_zuo_strong_weak(bazi)
        wx_dist = analyze_wuxing_distribution(bazi)

        # ─── 十神分析 ───
        ss = analyze_all_shi_shen(bazi)

        # ─── 神煞 ───
        shensha_result = find_shen_sha(bazi)
        shensha_list = []
        # 分吉凶
        ji_names = ["天乙贵人", "天德", "月德", "文昌贵人", "国印贵人", "禄神",
                     "金舆", "天赦", "红鸾", "天喜", "学堂", "词馆", "将星",
                     "福星贵人", "天厨贵人", "天权"]
        xiong_names = ["羊刃", "劫煞", "灾煞", "勾神", "绞神", "元辰",
                        "孤辰", "寡宿", "十恶大败", "四废", "天罗地网"]
        for name, info in shensha_result.items():
            if name in ji_names:
                stype = "吉"
            elif name in xiong_names:
                stype = "凶"
            else:
                stype = "中"
            shensha_list.append({
                "name": name,
                "position": "、".join(info["positions"]),
                "meaning": info["meaning"],
                "type": stype,
            })

        # ─── 大运 ───
        dy = calculate_da_yun(bazi)
        da_yun_list = []
        # 用默认年龄30岁来标记当前
        for yun in dy["da_yun_list"]:
            da_yun_list.append({
                "range": yun["range"],
                "start_age": yun["start_age"],
                "end_age": yun["end_age"],
                "gan_zhi": yun["gan_zhi"],
                "shi_shen": yun["shi_shen"],
                "is_current": yun["start_age"] <= 30 < yun["end_age"],
            })

        # ─── 流年 ───
        ln = get_liu_nian(liunian_year)
        ln_analysis = analyze_liu_nian(bazi, liunian_year)

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

        # ─── 建议 ───
        useful_god = wx["useful_god"]
        advice = []
        for ug in useful_god:
            color = WU_XING_COLORS.get(ug, "?")
            direction = WU_XING_DIRECTIONS.get(ug, "?")
            season = WU_XING_SEASONS.get(ug, "?")
            organ = WU_XING_ORGANS.get(ug, "?")
            advice.append(f"用神为{ug}：多穿{color}色系，往{direction}发展有利，{season}季运势最佳")

        wuxing_careers = {
            "木": "教育、文化、医疗、环保、园艺",
            "火": "互联网、能源、设计、餐饮、传媒",
            "土": "房地产、建筑、农业、矿业、仓储",
            "金": "金融、法律、机械、汽车、科技",
            "水": "物流、旅游、贸易、媒体、水产",
        }
        for ug in useful_god:
            careers = wuxing_careers.get(ug, "")
            if careers:
                advice.append(f"适合行业（{ug}）：{careers}")

        # ─── 响应 ───
        return jsonify({
            "bazi": " ".join(p.gan_zhi for p in bazi.si_zhu),
            "bazi_detail": bazi_to_string(bazi).split("\n")[3],
            "ri_gan": bazi.ri_gan,
            "ri_wx": wx["ri_wx"],
            "gender": bazi.gender,
            # 五行
            "wuxing_distribution": wx_dist,
            "monthly_state": wx["monthly_state"],
            "strong_weak": wx["strong_weak"],
            "score": wx["score"],
            "reasoning": wx["reasoning"],
            "useful_god": "、".join(wx["useful_god"]),
            "avoid_god": "、".join(wx["avoid_god"]),
            # 十神
            "shisheng_summary": ss["summary"],
            # 神煞
            "shensha": shensha_list,
            # 大运
            "da_yun": da_yun_list,
            "start_age": dy["start_age"],
            # 流年
            "liu_nian": f"{ln['tian_gan']}{ln['di_zhi']}",
            "tai_sui": "、".join(ln_analysis["tai_sui_relations"]),
            "liu_nian_shi_shen": ln_analysis["liu_nian_shi_shen"],
            "liu_nian_forecast": ss_forecast.get(ln_analysis["liu_nian_shi_shen"], ""),
            # 建议
            "advice": advice,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
