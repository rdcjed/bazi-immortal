"""
八字命理推算 - Web 交互页面
基于 bazi_immortal 引擎的 Flask Web 应用
"""
import sys, os, json, requests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, render_template
from zhdate import ZhDate

from bazi_immortal import calculate_bazi, find_shen_sha
from bazi_immortal.wuxing import analyze_ri_zuo_strong_weak, analyze_wuxing_distribution, analyze_ge_ju
from bazi_immortal.shisheng import analyze_all_shi_shen
from bazi_immortal.dayun import calculate_da_yun, get_liu_nian, analyze_liu_nian
from bazi_immortal.contextual import analyze_shi_shen_features, get_guiren_analysis, analyze_pillars, analyze_life_fortune
from bazi_immortal.predictions import predict_monthly, predict_ten_years, generate_year_overview
from bazi_immortal.location import analyze_location_compatibility
from bazi_immortal.constants import TG_WU_XING
from bazi_immortal.knowledge_loader import load_all_knowledge

app = Flask(__name__)

# LLM 质检配置
LLM_ENABLED = os.environ.get("LLM_QUALITY_CHECK", "").lower() in ("1", "true", "yes")
LLM_API_KEY = os.environ.get("SENSENOVA_API_KEY", "")
LLM_BASE_URL = "https://token.sensenova.cn/v1"
LLM_MODEL = "deepseek-v4-flash"


TEN_YEAR_PASSWORD = "111111"


# ════════════════════════════════════════════
#  省份-城市联动数据
# ════════════════════════════════════════════
PROVINCE_CITIES = {
    "北京市": ["东城区","西城区","朝阳区","海淀区","丰台区","石景山区","通州区","大兴区","昌平区","顺义区","房山区","怀柔区","密云区","延庆区","门头沟区","平谷区"],
    "上海市": ["黄浦区","徐汇区","长宁区","静安区","普陀区","虹口区","杨浦区","浦东新区","闵行区","宝山区","嘉定区","金山区","松江区","青浦区","奉贤区","崇明区"],
    "天津市": ["和平区","河东区","河西区","南开区","河北区","红桥区","滨海新区","东丽区","西青区","津南区","北辰区","武清区","宝坻区","宁河区","静海区","蓟州区"],
    "重庆市": ["渝中区","大渡口区","江北区","沙坪坝区","九龙坡区","南岸区","北碚区","綦江区","大足区","渝北区","巴南区","长寿区","江津区","合川区","永川区","南川区","璧山区","铜梁区","潼南区","荣昌区","开州区","梁平区","武隆区","涪陵区","万州区","黔江区"],
    "河北省": ["石家庄市","唐山市","秦皇岛市","邯郸市","邢台市","保定市","张家口市","承德市","沧州市","廊坊市","衡水市"],
    "山西省": ["太原市","大同市","阳泉市","长治市","晋城市","朔州市","晋中市","运城市","忻州市","临汾市","吕梁市"],
    "内蒙古": ["呼和浩特市","包头市","乌海市","赤峰市","通辽市","鄂尔多斯市","呼伦贝尔市","巴彦淖尔市","乌兰察布市","兴安盟","锡林郭勒盟","阿拉善盟"],
    "辽宁省": ["沈阳市","大连市","鞍山市","抚顺市","本溪市","丹东市","锦州市","营口市","阜新市","辽阳市","盘锦市","铁岭市","朝阳市","葫芦岛市"],
    "吉林省": ["长春市","吉林市","四平市","辽源市","通化市","白山市","松原市","白城市","延边朝鲜族自治州"],
    "黑龙江": ["哈尔滨市","齐齐哈尔市","鸡西市","鹤岗市","双鸭山市","大庆市","伊春市","佳木斯市","七台河市","牡丹江市","黑河市","绥化市","大兴安岭地区"],
    "江苏省": ["南京市","无锡市","徐州市","常州市","苏州市","南通市","连云港市","淮安市","盐城市","扬州市","镇江市","泰州市","宿迁市"],
    "浙江省": ["杭州市","宁波市","温州市","嘉兴市","湖州市","绍兴市","金华市","衢州市","舟山市","台州市","丽水市"],
    "安徽省": ["合肥市","芜湖市","蚌埠市","淮南市","马鞍山市","淮北市","铜陵市","安庆市","黄山市","滁州市","阜阳市","宿州市","六安市","亳州市","池州市","宣城市"],
    "福建省": ["福州市","厦门市","莆田市","三明市","泉州市","漳州市","南平市","龙岩市","宁德市"],
    "江西省": ["南昌市","景德镇市","萍乡市","九江市","新余市","鹰潭市","赣州市","吉安市","宜春市","抚州市","上饶市"],
    "山东省": ["济南市","青岛市","淄博市","枣庄市","东营市","烟台市","潍坊市","济宁市","泰安市","威海市","日照市","临沂市","德州市","聊城市","滨州市","菏泽市"],
    "河南省": ["郑州市","开封市","洛阳市","平顶山市","安阳市","鹤壁市","新乡市","焦作市","濮阳市","许昌市","漯河市","三门峡市","南阳市","商丘市","信阳市","周口市","驻马店市"],
    "湖北省": ["武汉市","黄石市","十堰市","宜昌市","襄阳市","鄂州市","荆门市","孝感市","荆州市","黄冈市","咸宁市","随州市","恩施土家族苗族自治州"],
    "湖南省": ["长沙市","株洲市","湘潭市","衡阳市","邵阳市","岳阳市","常德市","张家界市","益阳市","郴州市","永州市","怀化市","娄底市","湘西土家族苗族自治州"],
    "广东省": ["广州市","深圳市","珠海市","汕头市","佛山市","韶关市","湛江市","肇庆市","江门市","茂名市","惠州市","梅州市","汕尾市","河源市","阳江市","清远市","东莞市","中山市","潮州市","揭阳市","云浮市"],
    "广西": ["南宁市","柳州市","桂林市","梧州市","北海市","防城港市","钦州市","贵港市","玉林市","百色市","贺州市","河池市","来宾市","崇左市"],
    "海南省": ["海口市","三亚市","三沙市","儋州市"],
    "四川省": ["成都市","自贡市","攀枝花市","泸州市","德阳市","绵阳市","广元市","遂宁市","内江市","乐山市","南充市","眉山市","宜宾市","广安市","达州市","雅安市","巴中市","资阳市","阿坝藏族羌族自治州","甘孜藏族自治州","凉山彝族自治州"],
    "贵州省": ["贵阳市","六盘水市","遵义市","安顺市","毕节市","铜仁市","黔西南布依族苗族自治州","黔东南苗族侗族自治州","黔南布依族苗族自治州"],
    "云南省": ["昆明市","曲靖市","玉溪市","保山市","昭通市","丽江市","普洱市","临沧市","楚雄彝族自治州","红河哈尼族彝族自治州","文山壮族苗族自治州","西双版纳傣族自治州","大理白族自治州","德宏傣族景颇族自治州","怒江傈僳族自治州","迪庆藏族自治州"],
    "西藏": ["拉萨市","日喀则市","昌都市","林芝市","山南市","那曲市","阿里地区"],
    "陕西省": ["西安市","铜川市","宝鸡市","咸阳市","渭南市","延安市","汉中市","榆林市","安康市","商洛市"],
    "甘肃省": ["兰州市","嘉峪关市","金昌市","白银市","天水市","武威市","张掖市","平凉市","酒泉市","庆阳市","定西市","陇南市","临夏回族自治州","甘南藏族自治州"],
    "青海省": ["西宁市","海东市","海北藏族自治州","黄南藏族自治州","海南藏族自治州","果洛藏族自治州","玉树藏族自治州","海西蒙古族藏族自治州"],
    "宁夏": ["银川市","石嘴山市","吴忠市","固原市","中卫市"],
    "新疆": ["乌鲁木齐市","克拉玛依市","吐鲁番市","哈密市","昌吉回族自治州","博尔塔拉蒙古自治州","巴音郭楞蒙古自治州","阿克苏地区","克孜勒苏柯尔克孜自治州","喀什地区","和田地区","伊犁哈萨克自治州","塔城地区","阿勒泰地区"],
    "台湾省": ["台北市","新北市","桃园市","台中市","台南市","高雄市","基隆市","新竹市","嘉义市"],
    "香港": ["中西区","湾仔区","东区","南区","油尖旺区","深水埗区","九龙城区","黄大仙区","观塘区","葵青区","荃湾区","屯门区","元朗区","北区","大埔区","沙田区","西贡区","离岛区"],
    "澳门": ["花地玛堂区","花王堂区","望德堂区","大堂区","风顺堂区","嘉模堂区","路氹城","圣方济各堂区"],
}


def lunar_to_solar(lunar_year, lunar_month, lunar_day):
    """农历转公历"""
    try:
        lunar = ZhDate(lunar_year, lunar_month, lunar_day)
        solar = lunar.to_datetime()
        return solar.year, solar.month, solar.day
    except Exception:
        return None


def call_llm(prompt: str, max_tokens: int = 1500, temperature: float = 0.5) -> str:
    """调用 LLM API 获取分析结果，失败返回 None"""
    if not LLM_API_KEY:
        return None
    try:
        resp = requests.post(
            f"{LLM_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": LLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            timeout=30
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
        return None
    except Exception:
        return None


def generate_report(year, month, day, hour, minute, gender, target_year=None,
                    location_province=None, location_city=None):
    """完整的推算流程，返回结构化结果"""
    bazi = calculate_bazi(year, month, day, hour, minute, gender)
    if bazi is None:
        return {"error": "八字推算失败，请检查日期格式"}

    if target_year is None:
        target_year = 2026

    # ── 基础信息（排盘数据）──
    gan_zhi_list = [
        bazi.year_pillar.gan_zhi, bazi.month_pillar.gan_zhi,
        bazi.day_pillar.gan_zhi, bazi.hour_pillar.gan_zhi,
    ]

    # ── 五行分析（只取基本数据）──
    strength = analyze_ri_zuo_strong_weak(bazi)
    wx_dist = analyze_wuxing_distribution(bazi)

    # ── 十神 ──
    ss_data = analyze_all_shi_shen(bazi)
    ss_counts = {k: v for k, v in sorted(ss_data["counts"].items(), key=lambda x: -x[1]) if v > 0}
    top_ss = ss_data.get("top_shi_shen", [])

    # ── 格局分析 ──
    ge_ju = analyze_ge_ju(bazi, strength, ss_data)
    print(f"[格局] {ge_ju['name']} ({ge_ju['category']})")

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

    ri_gan = bazi.ri_gan
    ri_wx = TG_WU_XING[ri_gan]

    # ── 四柱基本数据（用于排盘显示，LLM 和规则引擎都需要）──
    yongshen_info = {
        "strong_weak": strength["strong_weak"],
        "useful_god": strength.get("useful_god", []),
        "avoid_god": strength.get("avoid_god", []),
    }
    pillar_analysis = analyze_pillars(bazi, strength, ss_data, yongshen_info)

    # ════════════════════════════════════════════
    #  LLM 模式：排盘 + LLM 命理分析
    # ════════════════════════════════════════════
    if LLM_ENABLED and LLM_API_KEY:
        # ── 加载知识库作为 LLM 参考 ──
        kb_context = ""
        try:
            knowledge = load_all_knowledge()
            # 根据日主五行选择相关章节
            ri_wx_map = {"木": ["00_五行详解", "05_十二长生与旺衰"],
                         "火": ["00_五行详解", "05_十二长生与旺衰"],
                         "土": ["00_五行详解", "05_十二长生与旺衰"],
                         "金": ["00_五行详解", "05_十二长生与旺衰"],
                         "水": ["00_五行详解", "05_十二长生与旺衰"]}
            keys = ["00_五行详解", "02_八字排盘十神大运", "11_格局体系", "04_神煞大全"]
            for key in keys:
                if key in knowledge:
                    kb_context += f"\n### {key}\n{knowledge[key][:400]}\n"
        except Exception:
            kb_context = ""

        # ── 构造 LLM prompt ──
        prompt = f"""你是一位精通子平八字的资深命理师。请根据以下命盘信息，给出详细的命理分析。

## 命盘信息
- 出生时间：{year}年{month}月{day}日 {hour}:{minute}
- 性别：{gender}
- 年柱：{gan_zhi_list[0]}
- 月柱：{gan_zhi_list[1]}
- 日柱：{gan_zhi_list[2]}（{ri_gan}日主）
- 时柱：{gan_zhi_list[3]}
- 日主五行：{ri_wx}
- 身强弱：{strength['strong_weak']}
- 用神：{', '.join(strength.get('useful_god', []))}
- 忌神：{', '.join(strength.get('avoid_god', []))}
- 大运：{dayun_data['direction']}运，起运{dayun_data['start_age']}岁
- 当前大运：{current_dayun['gan_zhi'] if current_dayun else '无'}
- 神煞：{', '.join(list(shensha_result.keys())[:8])}

## 知识库参考
{kb_context}

请分析以下内容（用中文，通俗但不失专业）：
1. 整体格局判断（什么格）
2. 五行旺衰分析
3. 性格特质
4. 事业财运
5. 感情婚姻
6. 当前大运流年运势
7. 开运建议

控制在 500 字以内。"""

        # ── 调用 LLM 获取分析结果 ──
        llm_analysis = call_llm(prompt, max_tokens=1500, temperature=0.5)

        if llm_analysis:
            result_llm = {
                "llm_enabled": True,
                "llm_analysis": llm_analysis,
                "bazi_data": {
                    "gan_zhi": gan_zhi_list,
                    "day_gan": ri_gan,
                    "strong_weak": strength['strong_weak'],
                    "useful_god": strength.get('useful_god', []),
                    "ge_ju": ge_ju,
                }
            }
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
                    "reasoning": strength.get("reasoning", []),
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
                "pillars": pillar_analysis,
                "ge_ju": ge_ju,
                "llm": result_llm,
            }
        # LLM 失败，回退到规则引擎

    # ════════════════════════════════════════════
    #  规则引擎模式（LLM 关闭 或 LLM 失败回退）
    # ════════════════════════════════════════════
    # ── 命格特质分析 ──
    features = analyze_shi_shen_features(bazi.ri_gan, ss_data, strength)

    # ── 贵人评估 ──
    guiren = get_guiren_analysis(shensha_result)
    shaguan_count = ss_data["counts"].get("七杀", 0) + ss_data["counts"].get("正官", 0)
    if shaguan_count > 0:
        is_yong = "为用神" if strength.get("strong_weak") == "身强" else "需印星化杀"
        shaguan_str = f"{shaguan_count:.1f}" if shaguan_count >= 1 else f"{shaguan_count:.2f}"
        guiren["guiren_list"].append({
            "name": "官杀贵人",
            "desc": f"官杀旺（{shaguan_str}）{is_yong}：职场/上司贵人运强",
            "positions": "",
        })

    # ── 月度运势预测（用流年的年干，不是出生年干）──
    liunian_gan = get_liu_nian(target_year)["tian_gan"]
    months = predict_monthly(
        liunian_gan, bazi.ri_gan, bazi.zhi_list,
        strength["strong_weak"], strength.get("useful_god", [])
    )

    # ── 当年整体运势总评 ──
    year_overview = generate_year_overview(
        months, bazi.ri_gan,
        strength["strong_weak"], strength.get("useful_god", []),
        liunian_info["gan_zhi"], TG_WU_XING[bazi.ri_gan],
    )

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

    # ── LLM 质检润色（可选）──
    if LLM_ENABLED:
        result_llm = {"llm_enabled": True}
        try:
            original_text = (
                f"命主为{ri_gan}日主，{strength.get('strong_weak', '')}，"
                f"格局{ge_ju.get('name', '')}（{ge_ju.get('category', '')}）。"
                f"用神为{', '.join(strength.get('useful_god', []))}，"
                f"忌神为{', '.join(strength.get('avoid_god', []))}。"
                f"年柱{gan_zhi_list[0]}，月柱{gan_zhi_list[1]}，"
                f"日柱{gan_zhi_list[2]}，时柱{gan_zhi_list[3]}。"
                f"当前大运：{current_dayun['gan_zhi'] if current_dayun else '无'}。"
                f"流年运势：{year_overview.get('summary', '')}"
            )
            polished = call_llm(
                f"你是一位经验丰富的八字命理师。以下是AI系统对一个命盘的分析结果，请将其改写为更自然、更个性化的命理点评，保持专业但通俗易懂。\n\n"
                f"命盘信息：\n"
                f"- 日主：{ri_gan}\n"
                f"- 格局：{ge_ju.get('name', '')}\n"
                f"- 身强弱：{strength.get('strong_weak', '')}\n"
                f"- 用神：{', '.join(strength.get('useful_god', []))}\n"
                f"- 忌神：{', '.join(strength.get('avoid_god', []))}\n\n"
                f"原始分析：\n{original_text[:1000]}\n\n"
                f"请用中文给出流畅、个性化的命理点评（200字以内），不要提及\"根据AI系统\"等。",
                max_tokens=500, temperature=0.7
            )
            if polished:
                result_llm["polished_text"] = polished
        except Exception:
            pass
    else:
        result_llm = {"llm_enabled": False}

    # 格局详情
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
            "reasoning": strength.get("reasoning", []),
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
        "ge_ju": ge_ju,
        "guiren": guiren,
        "monthly": months,
        "year_overview": year_overview,
        "pillars": pillar_analysis,
        "life_fortune": life_fortune,
        "location": location_result,
        "llm": result_llm,
    }


def generate_ten_year_report(bazi, year, gender, birth_year):
    """生成10年运势预测"""
    strength = analyze_ri_zuo_strong_weak(bazi)
    dayun_data = calculate_da_yun(bazi, birth_time=(
        birth_year,
        int(gender == "女"),
        1, 0, 0
    ))
    return predict_ten_years(
        bazi, bazi.ri_gan, bazi.year_pillar.tian_gan,
        bazi.zhi_list, strength["strong_weak"], strength.get("useful_god", []),
        None, birth_year, gender, year
    )


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    form_values = {
        "year": "1990", "month": "1", "day": "1",
        "hour": "12", "minute": "0", "gender": "男",
        "target_year": "2026", "province": "", "city": "",
        "calendar_type": "solar",
    }
    ten_year_error = None
    ten_year_data = None

    if request.method == "POST":
        form_values["year"] = request.form.get("year", "1990")
        form_values["month"] = request.form.get("month", "1")
        form_values["day"] = request.form.get("day", "1")
        form_values["hour"] = request.form.get("hour", "12")
        form_values["minute"] = request.form.get("minute", "0")
        form_values["gender"] = request.form.get("gender", "男")
        form_values["target_year"] = request.form.get("target_year", "2026")
        form_values["enable_ten_year"] = request.form.get("enable_ten_year", "")
        form_values["ten_year_password"] = request.form.get("ten_year_password", "")
        form_values["province"] = request.form.get("province", "")
        form_values["city"] = request.form.get("city", "")
        form_values["calendar_type"] = request.form.get("calendar_type", "solar")

        try:
            year = int(form_values["year"])
            month = int(form_values["month"])
            day = int(form_values["day"])
            hour = int(form_values["hour"])
            minute = int(form_values["minute"])
            gender = form_values["gender"]
            target_year = int(form_values["target_year"])

            # 农历 → 公历转换
            if form_values["calendar_type"] == "lunar":
                converted = lunar_to_solar(year, month, day)
                if converted:
                    year, month, day = converted
                else:
                    error = "农历日期转换失败，请检查是否输入了有效的农历日期"

            if not error:
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
            if error is None and result is not None:
                enable_ten = request.form.get("enable_ten_year", "")
                if enable_ten == "on":
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
        province_cities=PROVINCE_CITIES,
    )


if __name__ == "__main__":
    print("☯ 八字命理预测系统已启动 → http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
