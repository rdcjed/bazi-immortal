# 命运道士 (BaZi Immortal) ☯

> **云中子** · 八字命理推算引擎 + AI智能体知识库

一个基于子平八字命理体系的完整 Python 推算引擎，输入公历生日就能推算出完整的八字命盘、五行分析、十神配置、大运流年、神煞等运势信息。

---

## ✨ 功能

| 功能 | 说明 |
|------|------|
| 🔢 **排四柱** | 年柱/月柱/日柱/时柱，立春分界、节气分月、日干支公式精准计算 |
| 🌳 **五行分析** | 五行分布统计、月令十二长生、得令/得地/得势三维度定身强身弱 |
| 🔮 **十神分析** | 比肩/劫财/食神/伤官/正财/偏财/正官/七杀/正印/偏印，完整十神配置 |
| ⭐ **神煞推算** | 天乙贵人/文昌/天德/月德/桃花/驿马/华盖/羊刃等15+神煞 |
| 🚀 **大运流年** | 阳男阴女顺排/阴男阳女逆排、起运年龄、流年与四柱的合冲刑害 |
| 🤖 **AI提示词** | 可以直接给大语言模型用的「命运道士」系统提示词 |

---

## 🚀 快速上手

### 安装

```bash
# 克隆项目
git clone https://github.com/rdcjed/bazi-immortal.git
cd bazi-immortal

# 安装
pip install -e .
```

### LLM 模式

如果要启用 LLM 增强分析，请按照以下步骤配置：

```bash
copy .env.example .env
# 编辑 .env 中的 API Key
```

`.env` 文件内容示例：

```ini
SENSENOVA_API_KEY=your_api_key_here
LLM_QUALITY_CHECK=true
```

然后运行：

```bash
python web/app.py
```

或使用 `start_llm.bat` 启动（会自动读取 `.env`）：

```bash
start_llm.bat
```

### 使用

```bash
# 命令行（输入公历生日 + 时间 + 性别）
bazi 1990 5 15 12:00 男

# 简写（默认中午12点 + 男）
bazi 1990 5 15

# 指定流年
bazi 1990 5 15 午 女 --year 2026

# 用时辰名称
bazi 1990 5 15 子 女
```

### 输出示例

```
============================================================
     ☯ 命运道士 - 八字命理运势报告 ☯
============================================================

【八字排盘】
           年柱       月柱       日柱       时柱
----------------------------------------
天干      庚      辛      庚      壬
地支      午      巳      辰      午
藏干     丁己    丙庚戊    戊乙癸     丁己

日主: 庚（金）  性别: 男
...
```

### Python API

```python
from bazi_immortal import (
    calculate_bazi, bazi_to_string,
    analyze_ri_zuo_strong_weak,
    analyze_all_shi_shen,
    calculate_da_yun, get_liu_nian,
    find_shen_sha,
)

# 计算八字
bazi = calculate_bazi(1990, 5, 15, 12, 0, "男")
print(bazi_to_string(bazi))

# 五行分析
wx = analyze_ri_zuo_strong_weak(bazi)
print(f"身强身弱: {wx['strong_weak']}")
print(f"用神: {', '.join(wx['useful_god'])}")
print(f"忌神: {', '.join(wx['avoid_god'])}")

# 十神分析
ss = analyze_all_shi_shen(bazi)
print(f"十神特征: {ss['summary']}")

# 大运
dy = calculate_da_yun(bazi)
for yun in dy['da_yun_list']:
    print(f"{yun['range']}: {yun['gan_zhi']}{yun['shi_shen']}")

# 流年
ln = get_liu_nian(2026)
print(f"2026年流年: {ln['gan_zhi']}")
```

---

## 🧪 测试与开发

项目支持两类测试：

1. `unittest` 核心单元测试（新引入）：

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

2. 现有命例验证脚本，用于回归命理逻辑和名人案例验证：

```bash
python tests/test_cases.py
python tests/validate_logic.py
```

如果需要运行全部验证脚本，也可以直接执行：

```bash
python tests/validate_massive.py
```

以上脚本会输出详细报告，并在 `tests/validation_report.json` 中保存结果。

## 🌐 Web 应用与部署

Web 示例位于 `web/app.py`，提供一个交互式界面用于输入出生信息并查看运势分析。

```bash
pip install flask zhdate requests
python web/app.py
```

然后打开：

```bash
http://localhost:5000
```

若使用 LLM 增强模式，请先复制并编辑 `.env.example`：

```bash
copy .env.example .env
```

在 `.env` 中填入你的 `SENSENOVA_API_KEY`，然后启动：

```bash
start_llm.bat
```

## 🐳 Docker 部署

项目已包含 `Dockerfile` 和 `docker-compose.yml`，可以直接构建并启动：

```bash
docker compose up -d
```

应用会在 `http://localhost:5000` 提供 Web 服务。

---

## 📂 项目结构

```
bazi-immortal/
├── bazi_immortal/            # Python 核心引擎
│   ├── __init__.py           # 包入口
│   ├── cli.py                # 命令行工具
│   ├── calculator.py         # 排四柱（年/月/日/时柱计算）
│   ├── constants.py          # 天干地支/藏干/六十甲子/纳音/神煞等常量
│   ├── wuxing.py             # 五行分析 + 身强身弱 + 用神忌神
│   ├── shisheng.py           # 十神分析
│   ├── dayun.py              # 大运流年
│   └── shensha.py            # 神煞推算
├── knowledge_base/           # 知识库（AI知识库文件）
│   ├── README.md             # 知识库索引
│   ├── 八字命理知识库/        # 八字命理部分（8个文件）
│   └── 周易知识库/           # 周易/风水/面相部分（9个文件）
├── prompts/                  # AI提示词
│   └── 命运道士AI提示词.md    # 完整的智能体系统提示词
├── tests/                    # 测试
├── pyproject.toml            # 项目配置
└── README.md                 # 本文件
```

---

## 📖 知识库总览

项目包含 **18个知识库文件**，覆盖：

| 类别 | 文件数 | 说明 |
|------|:------:|------|
| 🔯 八字命理（核心） | 7个 | 五行→干支→排盘→十神→特殊→神煞→十二长生 |
| 🕮 八字参考 | 1个 | 周公解梦摘要 |
| ☯️ 周易（核心） | 4个 | 六十四卦→起卦体用→面相手相→八卦风水 |
| 🕮 周易参考 | 5个 | 易经原文/梅花易数/风水入门等 |

知识库路径：`knowledge_base/`，可直接作为 AI 智能体的检索知识库。

---

## 🤖 AI 智能体模式

除了命令行工具，本项目的 prompts 目录下包含一个完整的 **命运道士 AI 提示词**，可以直接给任何大语言模型使用。

提示词特点：
- **推理优先**：不是查表输出，而是按命理公式一步步推算
- **大白话**：术语必解释，让普通人听得懂
- **完整流程**：排盘→五行→十神→神煞→大运→流年→综合解读
- **输出模板**：标准运势报告格式
- **伦理边界**：明确能算什么不能算什么

使用方法：

```
把 prompts/命运道士AI提示词.md 的内容作为 system prompt
配合 knowledge_base/ 目录下的18个知识库文件
即可创建一个完整的命运道士AI智能体
```

---

## 🌐 Web Demo

> 一个漂亮的暗色主题网页版，支持交互式运势查询

```bash
# 安装 Flask
pip install flask

# 启动
python web/app.py

# 浏览器打开
open http://localhost:5000
```

Web 版功能：
- 表单输入出生年月日时+性别
- 完整的运势报告展示（八字/五行/十神/神煞/大运/流年/建议）
- 手机端自适应

### Docker 部署（一行命令）

```bash
docker run -d -p 5000:5000 --name bazi-immortal ghcr.io/rdcjed/bazi-immortal:latest
```

或自己构建：

```bash
git clone https://github.com/rdcjed/bazi-immortal.git
cd bazi-immortal
docker compose up -d
# 浏览器打开 http://localhost:5000
```

---

## 📦 依赖

- Python 3.9+
- 标准库（引擎无需第三方依赖）
- Flask（仅 Web Demo 需要，`pip install flask`）

---

## 📜 许可

MIT License

## 🙏 说明

命理推算基于传统子平八字理论体系，结果仅供参考娱乐。人生充满变数，最重要的永远是自己的选择和努力。

> ⚠️ **安全警告**：`.env` 文件包含敏感 API 密钥，请**不要**将其提交到 Git 仓库。建议将 `.env` 添加到 `.gitignore` 中以防止意外泄露。

---

*命运道士 · 云中子 · 2026*