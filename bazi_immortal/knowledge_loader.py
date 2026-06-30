"""
知识库加载器 - 从 knowledge_base/八字命理知识库/ 读取 .md 文件
"""

import os
from typing import Dict, List


def _get_knowledge_dir() -> str:
    """获取知识库目录路径"""
    import bazi_immortal
    return os.path.join(
        os.path.dirname(os.path.dirname(bazi_immortal.__file__)),
        'knowledge_base', '八字命理知识库'
    )


def load_all_knowledge() -> Dict[str, str]:
    """
    加载所有知识库文件

    Returns:
        Dict[str, str]: key 为文件名（不含 .md），value 为全文
        加载失败时返回空字典
    """
    result = {}
    knowledge_dir = _get_knowledge_dir()

    try:
        if not os.path.isdir(knowledge_dir):
            return result

        for fname in os.listdir(knowledge_dir):
            if not fname.endswith('.md'):
                continue
            key = fname[:-3]  # 去掉 .md 后缀
            fpath = os.path.join(knowledge_dir, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    result[key] = f.read()
            except Exception:
                # 单个文件失败不影响其他文件
                continue
    except Exception:
        pass

    return result


def load_knowledge_by_topic(topic_keywords: List[str]) -> Dict[str, str]:
    """
    按主题关键词加载匹配的知识条目

    Args:
        topic_keywords: 关键词列表，匹配文件名（与关键词至少有一个匹配）

    Returns:
        Dict[str, str]: 匹配的知识条目
    """
    try:
        all_knowledge = load_all_knowledge()
        if not all_knowledge:
            return {}

        matched = {}
        for key, content in all_knowledge.items():
            for kw in topic_keywords:
                if kw in key:
                    matched[key] = content
                    break

        return matched
    except Exception:
        return {}


# ─── 十神描述字典（数据驱动推理用） ───
# 结构化：{十神名: {"positive_career": ..., "negative_career": ...}}

SHI_SHEN_DESCRIPTIONS: Dict[str, Dict[str, str]] = {
    "正官": {
        "positive_career": "官星（管理掌控之力）值月为喜→事业上有明确方向和贵人指引。上级赏识，升职或加薪机会显现。这个月工作上有人赏识你，适合申请升职加薪",
        "negative_career": "官星（管理掌控之力）为忌→职场压力增大。上级要求严格、规则约束多。注意工作细节，避免失误被放大。这个月领导盯得紧，做事细心点别出错",
    },
    "七杀": {
        "positive_career": "七杀（攻坚挑战之力）为喜→压力转化动力！适合接手挑战性任务，能在高压下取得突破性成果。这个月越有压力越出成绩，别怕难",
        "negative_career": "七杀（攻坚挑战之力）为忌！事业阻力大增。可能有岗位调整、职责加重或小人作祟。不宜硬扛，学会借力。这个月压力特别大，别硬撑，找人帮忙分担",
    },
    "正印": {
        "positive_career": "印星（庇护学习之力）护身→事业平稳上升。适合学习充电、考取证书、夯实专业基础。这个月适合读书学习，提升自己比啥都强",
        "negative_career": "印星（庇护学习之力）为忌→依赖心增强。做事拖沓效率低，需主动推进工作，不要被动等待。这个月容易犯懒，别等着别人催，自己动起来",
    },
    "偏印": {
        "positive_career": "偏印（偏门智慧之力）为喜→思路独特创意涌现。策划、研发、创意类工作如有神助。这个月灵感爆棚，适合搞创意和策划",
        "negative_career": "偏印（偏门智慧之力）为忌→想法怪异不被理解。职场人际关系紧张，建议收敛锋芒，多听少说。这个月少发表奇思妙想，低调做人",
    },
    "正财": {
        "positive_career": "财星（稳定收入之力）为喜→正职收入稳定。工作表现受认可，付出有对等回报。这个月干活值钱，努力就有回报",
        "negative_career": "财星（稳定收入之力）为忌→为赚钱而劳累。工作强度增大但收入增长有限，注意性价比。这个月钱不好赚，别拿健康换钱",
    },
    "偏财": {
        "positive_career": "偏财（意外进账之力）为喜→主业之外有额外收入机会。多劳多得，适合拓展副业。这个月适合搞搞副业，有机会赚外快",
        "negative_career": "偏财（意外进账之力）为忌→主业外投入精力过多反而得不偿失。专注本职工作。这个月别搞副业了，专心做好主业",
    },
    "比肩": {
        "positive_career": "比肩（平辈帮衬之力）帮身→同事朋友大力相助。团队协作效果极佳，借力使力。这个月团队给力，有朋友同事帮忙，事情好办",
        "negative_career": "比肩（平辈帮衬之力）为忌→同事间暗涌竞争。合作中注意明确分工和权益保护。这个月同事关系微妙，做好自己的事就行",
    },
    "劫财": {
        "positive_career": "劫财（竞争破财力）为喜→竞争转化为动力。良性竞争促使共同进步，但注意利益分配。有竞争是好事但钱的事要分清楚",
        "negative_career": "劫财（竞争破财力）为忌！职场竞争激烈且小人潜伏。做好分内事不参与是非，留好工作记录。这个月防小人！什么事都留个证据",
    },
    "食神": {
        "positive_career": "食神（才华输出之力）泄秀→才华充分展现。表达和创意能力突出，适合内容输出。这个月表达能力在线，做内容/演讲/写作都很顺",
        "negative_career": "食神（才华输出之力）为忌→过度放松影响工作状态。需收心专注，按计划推进。这个月别太安逸，收收心干活",
    },
    "伤官": {
        "positive_career": "伤官（创新突破之力）为喜→创新能力强。适合开拓新项目和打破常规。保持谦逊，避免锋芒太露。这个月脑子好使但别太嘚瑟，低调做事最稳妥",
        "negative_career": "伤官（创新突破之力）为忌！易出口舌是非，与上级关系紧张。谨言慎行，避免正面冲突。这个月管住嘴，别和领导抬杠",
    },
}


def get_shi_shen_description(ss_name: str, sentiment: str, field: str = "career") -> str:
    """获取十神描述文本

    Args:
        ss_name: 十神名称，如 "正官"
        sentiment: 情感倾向，"positive" 或 "negative"
        field: 领域，默认为 "career"

    Returns:
        描述文本，未找到时返回兜底提示
    """
    ss = SHI_SHEN_DESCRIPTIONS.get(ss_name, {})
    key = f"{sentiment}_{field}"
    return ss.get(key, f"{ss_name}在{field}方面表现{sentiment}。")