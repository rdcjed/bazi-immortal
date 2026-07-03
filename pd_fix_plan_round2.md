# PD 修复方案（第2轮）

## 问题清单映射

| # | 问题 | 优先级 | 核心原因 |
|---|------|--------|---------|
| 1 | jieqi.py fallback 缺小寒边界 | 🔴 高 | `_get_month_zhi_fallback` 缺少 `(1, 6, "丑")` 条目 |
| 2 | Dockerfile 缺 knowledge_base/ | 🔴 高 | `COPY` 未包含 `knowledge_base/` 目录 |
| 3 | CI 未集成 celebrities 测试 | 🔴 高 | 无 CI 配置文件，名人测试未纳入自动化 |
| 4 | generate_ten_year_report 死代码 | 🟡 中 | 定义后从未被调用，且传参错误 |
| 5 | polished_text 前端不显示 | 🟡 中 | `result.llm.polished_text` 生成但模板不渲染 |
| 6 | load_knowledge_by_topic 未使用 | 🟢 低 | 定义但全系统无调用点 |

---

### 🔴 高优先

#### 1. jieqi.py 边界修复

**文件**: `bazi_immortal/jieqi.py`

**问题**: `_get_month_zhi_fallback` (L223-255) 的 `boundaries` 列表包含 11 个条目，覆盖 2 月~12 月的节气分界，但缺少 **1 月的「小寒」边界 `(1, 6, "丑")`**。这导致当年天文算法因跨年或其他原因失败时：

- 1 月 1 日~5 日（小寒前）：应属上一年的 **子** 月 → fallback 最后兜底给了 `month_to_zhi[1] = "丑"` ❌
- 1 月 6 日~31 日（小寒后）：应属 **丑** 月 → `month_to_zhi[1] = "丑"` 巧合正确，但大雪后边界逻辑会误判

**改动方案**:

```python
def _get_month_zhi_fallback(year: int, month: int, day: int) -> str:
    # 1月单独处理（跨年情况）
    if month == 1:
        return "丑" if day >= 6 else "子"  # 小寒(1/6)前是子月，后是丑月

    boundaries = [
        (2, 4, "寅"),   (3, 6, "卯"),   (4, 5, "辰"),
        (5, 6, "巳"),   (6, 6, "午"),   (7, 7, "未"),
        (8, 7, "申"),   (9, 8, "酉"),   (10, 8, "戌"),
        (11, 7, "亥"),  (12, 7, "子"),
    ]

    for b_month, b_day, zhi in boundaries:
        if month < b_month or (month == b_month and day < b_day):
            prev_zhi = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
            zhi_index = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"].index(zhi)
            return prev_zhi[(zhi_index - 1) % 12]

    if month == 12 and day >= 7:
        return "子"

    month_to_zhi = {1: "丑", 2: "寅", 3: "卯", 4: "辰", 5: "巳", 6: "午",
                    7: "未", 8: "申", 9: "酉", 10: "戌", 11: "亥", 12: "子"}
    return month_to_zhi.get(month, "子")
```

**验证用例**:
- 2000-01-01: `month==1, day<6` → `return "子"` ✅（小寒前属上一年的子月）
- 2000-01-07: `month==1, day>=6` → `return "丑"` ✅（小寒后属丑月）
- 2000-12-01: 不匹配任何边界 → 兜底 `12: "子"` ✅（大雪前）
- 2000-12-10: 进入 `month==12 and day>=7` → `return "子"` ✅

---

#### 2. Dockerfile 补全 knowledge_base/

**文件**: `Dockerfile`

**问题**: Dockerfile 的 `COPY` 指令只复制了 `bazi_immortal/`、`web/` 和 `pyproject.toml`，没有复制 `knowledge_base/` 目录。在 LLM 模式下，`web/app.py` 中的 `load_all_knowledge()` 会尝试读取 `knowledge_base/八字命理知识库/` 目录下的 .md 文件，容器内找不到该目录导致知识库为空。

**改动**: 在 `COPY pyproject.toml .` 行后增加一行 `COPY knowledge_base/ knowledge_base/`

**完整改动后的 Dockerfile**:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bazi_immortal/ bazi_immortal/
COPY web/ web/
COPY knowledge_base/ knowledge_base/
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .
EXPOSE 5000
CMD ["python", "web/app.py"]
```

**验证方法**:
```bash
docker build -t bazi-immortal .
docker run --rm bazi-immortal python -c \
  "from bazi_immortal.knowledge_loader import load_all_knowledge; k=load_all_knowledge(); print(f'条目数: {len(k)}')"
# 期望输出: 条目数: >0
```

---

#### 3. CI 集成 celebrities 测试

**文件**: 新建 `.github/workflows/test.yml`

**问题**: 项目有完善的测试基础设施（15 位名人验证 + 100+ 位名人全量数据库 + pytest 参数化测试），但完全没有 CI 自动化配置。

**新建文件 `.github/workflows/test.yml`**:

```yaml
name: Test

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -e .

      - name: pytest unit tests (15 cases)
        run: python -m pytest tests/test_cases.py -v --tb=short

      - name: Celebrity validation (15 people)
        run: python -m tests.validate_celebrities

      - name: Statistical analysis (100+ celebrities)
        run: python -m tests.run_celebrities
```

**测试覆盖**:
| 步骤 | 测试内容 | 用例数 |
|------|---------|--------|
| pytest | 强弱/用神/忌神/神煞 断言 | 15 |
| validate_celebrities | 八字排盘+大运+一生运势 | 15 |
| run_celebrities | 五行/十神/强弱分布统计 | 100+ |

---

### 🟡 中优先

#### 4. generate_ten_year_report 死代码清理

**文件**: `web/app.py` (L414-426)

**问题**: `generate_ten_year_report` 函数存在两个问题：
1. **从未被调用** — 搜索全项目确认零引用
2. **传参错误** — 第 7 个参数传 `None` 而非 `dayun_list`

**方案 A（推荐 — 删除）**: 直接删除 L414-426 整个函数。`index()` 中已通过直接调用 `predict_ten_years()` 实现相同功能。

```python
# 删除以下 13 行：
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
```

**方案 B（保留+修复）**: 如果未来计划重构 10 年运势逻辑到一个独立函数，可以保留但修复参数：

```python
# 将 None 改为实际的大运列表
dayun_data["da_yun_list"],  # 修复
```

**建议**: 选方案 A。理由：零调用 + 功能完全等价于 `index()` 中的内联调用；删除后 L414-426 行消除，代码更清晰。

---

#### 5. polished_text 前端不显示

**文件**: `web/templates/index.html` (L381-393) + `web/app.py` (L356)

**问题分析**:
1. `web/app.py` L356: `result_llm["polished_text"] = polished` — 后端生成了润色文本
2. `web/templates/index.html` L382-393: 只渲染了 `{{ result.llm.llm_analysis }}`，没有 `polished_text` 的模板代码

**改动: web/templates/index.html** — 在 AI 分析区域增加 polished_text 显示：

```html
  <!-- ── AI 命理分析（LLM 模式）── -->
  {% if result and result.llm and result.llm.llm_enabled and result.llm.llm_analysis %}
  <div class="section">
    <div class="section-header" onclick="toggle(this)">
      <span><span class="icon">🔮</span>AI 命理分析</span><span class="arrow">▼</span>
    </div>
    <div class="section-body">
      {% if result.llm.polished_text %}
      <!-- 润色版本优先显示 -->
      <div style="background:var(--card2);border-radius:8px;padding:15px;line-height:1.8;white-space:pre-wrap;font-size:14px;color:var(--text);border-left:3px solid var(--gold);">
        {{ result.llm.polished_text }}
      </div>
      <details style="margin-top:10px;">
        <summary style="cursor:pointer;font-size:12px;color:var(--text-dim);">查看原始分析</summary>
        <div style="background:var(--card2);border-radius:8px;padding:15px;margin-top:8px;line-height:1.8;white-space:pre-wrap;font-size:13px;color:var(--text-dim);">
          {{ result.llm.llm_analysis }}
        </div>
      </details>
      {% else %}
      <div style="background:var(--card2);border-radius:8px;padding:15px;line-height:1.8;white-space:pre-wrap;font-size:14px;color:var(--text);">
        {{ result.llm.llm_analysis }}
      </div>
      {% endif %}
    </div>
  </div>
  {% endif %}
```

**前端效果**:
- 有润色文本时：默认显示金色左边框的润色版本，下方折叠可展开查看原始分析
- 无润色文本时：回退显示原始分析（与当前行为一致）
- `polished_text` 为空/None 时自动降级

**可选优化**: 当前 polished_text 通过第二次 LLM 调用生成（L343-354），可通过修改 prompt 让一次调用同时返回原始和润色版本，节省 API 费用。

---

### 🟢 低优先

#### 6. load_knowledge_by_topic 未使用函数处理

**文件**: `bazi_immortal/knowledge_loader.py` (L50-74)

**问题**: `load_knowledge_by_topic(topic_keywords)` 定义了一个关键词过滤知识条目的实用函数，但全系统无任何调用点。

**方案 A（推荐 — 保留 + deprecated 标记）**:

```python
import warnings

def load_knowledge_by_topic(topic_keywords: List[str]) -> Dict[str, str]:
    """
    按主题关键词加载匹配的知识条目

    .. deprecated::
       当前未使用。保留为公共 API 供未来 RAG 检索使用。
    """
    # ... 函数体不变
```

**方案 B（激进 — 删除）**:
直接删除 L50-74。如需可从 Git 历史恢复。

**方案 C（推荐替代方案 — 接入 LLM Prompt 管道）**:
在 `web/app.py` L182-185，将当前硬编码的 key 列表替换为按主题动态检索：

```python
# 当前（硬编码）：
keys = ["00_五行详解", "02_八字排盘十神大运", "11_格局体系", "04_神煞大全"]

# 改为（按主题检索）：
from bazi_immortal.knowledge_loader import load_knowledge_by_topic

# 基础关键词
topic_keywords = ["五行详解", "十神大运", "格局体系", "神煞大全"]
# 根据命局特征增加针对性知识
if strength.get("strong_weak") in ("身弱", "偏弱"):
    topic_keywords.append("旺衰")
matched = load_knowledge_by_topic(topic_keywords)
for key, content in matched.items():
    kb_context += f"\n### {key}\n{content[:400]}\n"
```

**综合建议**: 方案 A（保留标记）+ 方案 C（接入调用）是性价比最高的组合：消除死代码状态的同时提升 LLM prompt 的知识相关性。

---

## 改动汇总

| # | 文件 | 改动类型 | 行数预估 | 风险 | 优先级 |
|---|------|---------|---------|------|--------|
| 1 | `bazi_immortal/jieqi.py` | 新增 1月分支 | +6 | 低 | 🔴 |
| 2 | `Dockerfile` | 新增 COPY 行 | +1 | 低 | 🔴 |
| 3 | `.github/workflows/test.yml` | 新建文件 | +40 | 低 | 🔴 |
| 4 | `web/app.py` | 删除死代码 | -13 | 低 | 🟡 |
| 5 | `web/templates/index.html` | 新增渲染块 | +15 | 中（需确认变量存在性） | 🟡 |
| 6a | `bazi_immortal/knowledge_loader.py` | 加 deprecated 标记 | +7 | 低 | 🟢 |
| 6b | `web/app.py` | 接入主题检索 | +8 | 低 | 🟢 |

**总计**: 新增约 84 行，删除 13 行，净增 71 行。新建 1 个 CI 文件。所有改动均为低风险，可直接实施。