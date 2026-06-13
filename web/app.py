"""
八字命理推算 - Web 交互页面
基于 bazi_immortal 引擎的 Flask Web 应用
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, render_template

from bazi_immortal import calculate_bazi, find_shen_sha
from bazi_immortal.wuxing import analyze_ri_zuo_strong_weak, analyze_wuxing_distribution
from bazi_immortal.shisheng import analyze_all_shi_shen
from bazi_immortal.dayun import calculate_da_yun, get_liu_nian, analyze_liu_nian
from bazi_immortal.contextual import analyze_shi_shen_features, get_guiren_analysis, analyze_pillars, analyze_life_fortune
from bazi_immortal.predictions import predict_monthly, predict_ten_years
from bazi_immortal.location import analyze_location_compatibility
from bazi_immortal.constants import TG_WU_XING

app = Flask(__name__)

TEN_YEAR_PASSWORD = "111111"


def generate_report(year, month, day, hour, minute, gender, target_year=None,
                    location_province=None, location_city=None):
    """完整的推算流程，返回结构化结果"""
    bazi = calculate_bazi(year, month, day, hour, minute, gender)
    if bazi is None:
        return {"error": "八字推算失败，请检查日期格式"}

    if target_year is None:
        target_year = 2026

    # ── 基础信息 ──
    gan_zhi_list = [
        bazi.year_pillar.gan_zhi, bazi.month_pillar.gan_zhi,
        bazi.day_pillar.gan_zhi, bazi.hour_pillar.gan_zhi,
    ]

    # ── 五行分析 ──
    strength = analyze_ri_zuo_strong_weak(bazi)
    wx_dist = analyze_wuxing_distribution(bazi)

    # ── 十神 ──
    ss_data = analyze_all_shi_shen(bazi)
    ss_counts = {k: v for k, v in sorted(ss_data["counts"].items(), key=lambda x: -x[1]) if v > 0}
    top_ss = ss_data.get("top_shi_shen", [])

    # ── 神煞 ──
    shensha_result = find_shen_sha(bazi)

    # ── 大运 ──
    birth_time = (year, month, day, hour, minute)
    dayun_data = calculate_da_yun(bazi, birth_time=birth_time)
    current_age = target_year - year
    current_dayun = None
    for step in dayun_data["da_yun_list"]:
        if step["start_age"] <= current_age <= step["end_age"]:
            current_dayun = step
            break

    # ── 流年 ──
    liunian_info = get_liu_nian(target_year)
    liunian_analysis = analyze_liu_nian(bazi, target_year)
    ln_shi_shen = liunian_analysis.get("shi_shen", "")

    # ── 命格特质分析(分情况) ──
    features = analyze_shi_shen_features(bazi.ri_gan, ss_data, strength)

    # ── 贵人评估 ──
    guiren = get_guiren_analysis(shensha_result)
    shaguan_count = ss_data["counts"].get("七杀", 0) + ss_data["counts"].get("正官", 0)
    if shaguan_count > 0:
        is_yong = "为用神" if strength.get("strong_weak") == "身强" else "需印星化杀"
        guiren["guiren_list"].append({
            "name": "官杀贵人",
            "desc": f"官杀旺（{shaguan_count}）{is_yong}：职场/上司贵人运强",
            "positions": "",
        })

    # ── 月度运势预测（用流年的年干，不是出生年干）──
    liunian_gan = get_liu_nian(target_year)["tian_gan"]
    months = predict_monthly(
        liunian_gan, bazi.ri_gan, bazi.zhi_list,
        strength["strong_weak"], strength.get("useful_god", [])
    )

    # ── 四柱逐柱分析 ──
    yongshen_info = {
        "strong_weak": strength["strong_weak"],
        "useful_god": strength.get("useful_god", []),
        "avoid_god": strength.get("avoid_god", []),
    }
    pillar_analysis = analyze_pillars(bazi, strength, ss_data, yongshen_info)

    # ── 一生运势综合 ──
    life_fortune = analyze_life_fortune(bazi, ss_data, strength, dayun_data)

    # ── 地点分析 ──
    location_result = None
    if location_province:
        location_result = analyze_location_compatibility(
            location_province, location_city or "",
            strength.get("useful_god", []),
            strength.get("avoid_god", []),
            strength["strong_weak"],
            bazi.ri_gan,
            ss_data["category_counts"],
            gender,
        )

    ri_gan = bazi.ri_gan
    ri_wx = TG_WU_XING[ri_gan]

    return {
        "basic": {
            "gan_zhi": gan_zhi_list,
            "day_gan": ri_gan,
            "day_wx": ri_wx,
            "gender": gender,
            "birth_str": f"{year}年{month}月{day}日 {hour}:{minute:02d}",
        },
        "wuxing": {
            "distribution": {k: v for k, v in sorted(wx_dist.items(), key=lambda x: -x[1])},
            "strength": strength["strong_weak"],
            "season": strength.get("season", ""),
            "monthly_state": strength.get("monthly_state", ""),
            "score": strength.get("score", 0),
            "useful_god": strength.get("useful_god", []),
            "avoid_god": strength.get("avoid_god", []),
        },
        "shishen": {
            "counts": ss_counts,
            "top_shi_shen": top_ss,
        },
        "shensha": {
            "list": [{"name": k, **v} for k, v in shensha_result.items()],
        },
        "dayun": {
            "direction": dayun_data["direction"],
            "start_age": dayun_data["start_age"],
            "list": dayun_data["da_yun_list"],
            "current": current_dayun,
            "current_age": current_age,
        },
        "liunian": {
            "gan_zhi": liunian_info["gan_zhi"],
            "tian_gan": liunian_info["tian_gan"],
            "di_zhi": liunian_info["di_zhi"],
            "shi_shen": ln_shi_shen,
            "tai_sui": liunian_analysis.get("tai_sui_relations", []),
        },
        "features": features,
        "guiren": guiren,
        "monthly": months,
        "pillars": pillar_analysis,
        "life_fortune": life_fortune,
        "location": location_result,
    }


def generate_ten_year_report(bazi, year, gender, birth_year):
    """生成10年运势预测"""
    strength = analyze_ri_zuo_strong_weak(bazi)
    dayun_data = calculate_da_yun(bazi, birth_time=(
        birth_year,
        int(gender == "女"),  # placeholder, will override
        1, 0, 0
    ))
    # Re-calculate with proper birth_time
    return predict_ten_years(
        bazi, bazi.ri_gan, bazi.year_pillar.tian_gan,
        bazi.zhi_list, strength["strong_weak"], strength.get("useful_god", []),
        None, birth_year, gender, year
    )


@app.route("/", methods=["GET", "POST"])
def index():
    """支持 GET（空表单）和 POST（提交+结果）"""
    result = None
    error = None
    form_values = {
        "year": "1900", "month": "1", "day": "1",
        "hour": "0", "minute": "0", "gender": "男",
        "target_year": "2026", "province": "", "city": "",
    }
    ten_year_error = None
    ten_year_data = None

    if request.method == "POST":
        form_values["year"] = request.form.get("year", "1986")
        form_values["month"] = request.form.get("month", "3")
        form_values["day"] = request.form.get("day", "2")
        form_values["hour"] = request.form.get("hour", "10")
        form_values["minute"] = request.form.get("minute", "30")
        form_values["gender"] = request.form.get("gender", "男")
        form_values["target_year"] = request.form.get("target_year", "2026")
        form_values["enable_ten_year"] = request.form.get("enable_ten_year", "")
        form_values["ten_year_password"] = request.form.get("ten_year_password", "")
        form_values["province"] = request.form.get("province", "")
        form_values["city"] = request.form.get("city", "")

        try:
            year = int(form_values["year"])
            month = int(form_values["month"])
            day = int(form_values["day"])
            hour = int(form_values["hour"])
            minute = int(form_values["minute"])
            gender = form_values["gender"]
            target_year = int(form_values["target_year"])

            if not (1900 <= year <= 2100):
                error = "年份范围：1900-2100"
            elif not (1 <= month <= 12):
                error = "月份范围：1-12"
            elif not (1 <= day <= 31):
                error = "日期范围：1-31"
            elif not (0 <= hour <= 23):
                error = "小时范围：0-23"
            elif not (0 <= minute <= 59):
                error = "分钟范围：0-59"
            elif gender not in ("男", "女"):
                error = "性别请填'男'或'女'"
            else:
                province = form_values.get("province", "")
                city = form_values.get("city", "")
                result = generate_report(year, month, day, hour, minute, gender, target_year,
                                         province if province else None,
                                         city if city else None)
                if "error" in result:
                    error = result["error"]
                    result = None

            # ── 10年运势预测（需密码验证）──
            enable_ten = request.form.get("enable_ten_year", "")
            if enable_ten == "on" and result is not None:
                password = request.form.get("ten_year_password", "")
                if password == TEN_YEAR_PASSWORD:
                    bazi = calculate_bazi(year, month, day, hour, minute, gender)
                    if bazi:
                        strength = analyze_ri_zuo_strong_weak(bazi)
                        dayun_data = calculate_da_yun(bazi, birth_time=(year, month, day, hour, minute))
                        ten_year_data = predict_ten_years(
                            bazi, bazi.ri_gan, bazi.year_pillar.tian_gan,
                            bazi.zhi_list, strength["strong_weak"],
                            strength.get("useful_god", []),
                            dayun_data["da_yun_list"], year, gender, target_year
                        )
                elif password != "":
                    ten_year_error = "密码错误，请重新输入"

        except (ValueError, TypeError):
            error = "请填写有效的数字格式"

    return render_template(
        "index.html", result=result, error=error, form=form_values,
        ten_year=ten_year_data, ten_year_error=ten_year_error,
    )


if __name__ == "__main__":
    print("☯ 八字命理预测系统已启动 → http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)