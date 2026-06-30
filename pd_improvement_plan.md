# PD 改进方案：bazi-immortal 与 DeepSeek 网页端准确度差距解决

## 总体思路

**"知识库激活 + LLM 辅助 + 排盘补缺"三管齐下**：第一阶段将 19 篇命理知识库从"装饰文件"转化为真正的规则源和推理素材；第二阶段引入 LLM 推理层（可选但效果最优），绕过纯规则模板天花板；第三阶段补齐排盘细节偏差。核心哲学是"让引擎有据可查、有料可说"。

---

## 阶段1：知识库激活（优先级 P0，工作量：中）

### 1.1 知识库加载器 — 从 md 文件读取规则数据

- **做什么**：当前 19 篇 md 文件放在 `knowledge_base/` 下，代码完全不读。新建 `bazi_immortal/knowledge_loader.py`，将 md 文件解析为结构化 Python 对象。
- **技术方案**：

  新建文件：`bazi_immortal/knowledge_loader.py`

  ```python
  import os, re
  from typing import Dict, List

  KNOWLEDGE_DIR = os.path.join(
      os.path.dirname(__file__), '..',
      'knowledge_base', '八字命理知识库'
  )

  def load_all_knowledge() -> Dict[str, str]:
      """加载所有 md 文件内容"""
      result = {}
      if not os.path.isdir(KNOWLEDGE_DIR):
          return result
      for fname in sorted(os.listdir(KNOWLEDGE_DIR)):
          if fname.endswith('.md'):
              key = fname.replace('.md', '')
              fpath = os.path.join(KNOWLEDGE_DIR, fname)
              with open(fpath, 'r', encoding='utf-8') as f:
                  result[key] = f.read()
      return result
  ```

- **预期效果**：引擎首次能读取命理知识库内容，为后续推理提供原始素材。
- **工作量评估**：约 150-200 行代码。

### 1.2 空亡 / 纳音 / 六破 规则补全

- **做什么**：`constants.py` 已有 `NA_YIN_FULL`、`DZ_LIU_HE`、`DZ_LIU_CHONG`、`DZ_SAN_XING`，缺少**六破**。空亡和纳音有数据但未被推理使用。
- **技术方案**：补充 `DZ_LIU_PO`，在 `get_zhi_relations()` 中添加六破检测。
- **文件改动**：`bazi_immortal/constants.py` + `bazi_immortal/predictions.py`
- **工作量评估**：约 60 行。**低工作量，高性价比**。

### 1.3 节气日期精确化

- **做什么**：`_get_lichun()` 只返回 2020-2030 缓存，改为调用 `jieqi.get_term_date()`。
- **文件改动**：`bazi_immortal/calculator.py` 第 127-129 行
- **预期效果**：年柱分界覆盖 1900-2100，直接影响 15-20% 跨边界命例准确度。
- **工作量评估**：约 20 行。

---

## 阶段2：推理增强 — 预制模板 → 数据驱动推理（P1）

### 2.1 六领域预测从 if/else 枚举改为知识库驱动

- **做什么**：`_gen_month_categories_v3()` 有 500+ 行 if/else，改为知识库驱动+动态组合。
- **技术方案**：在 `knowledge_loader.py` 建立十神-领域描述字典，各领域文本根据命局特征动态组合。
- **文件改动**：`predictions.py` + `knowledge_loader.py`
- **工作量评估**：约 200-300 行。**不确定性**：纯规则组合能否产生真正的个性化效果。
- **建议**：完成后用 `tests/celebrities_data.py` 做 A/B 对比，统计文本"去重率"。

### 2.2 评分系统层次化

- **做什么**：`_calc_enhanced_score()` 改为分级评分：基础分(0-4) + 用神分(0-3) + 季节分(0-2) + 冲刑扣分(0-2)
- **文件改动**：`bazi_immortal/predictions.py`
- **工作量评估**：约 80 行。

---

## 阶段3：格局完善（P1）

### 3.1 化气格检测增强

- **做什么**：当前仅检测日主+月干/时干合化，漏掉日主+年干、月干+时干、年干+日干合化。
- **文件改动**：`bazi_immortal/wuxing.py` 第 633-647 行
- **工作量评估**：约 50 行。

### 3.2 从格阈值调整

- **做什么**：印比≥80%→75%，官杀≤15%→20%。增加"假从"中间类别 + `confidence` 字段。
- **文件改动**：`bazi_immortal/wuxing.py` 第 756-771 行
- **需验证**：用 `tests/validate_massive.py` 做回归测试，避免过度检出。

---

## 阶段4：LLM 辅助推理（P2，效果最佳但需 API key）

### 4.1 LLM 作为推理质检员

- **做什么**：规则引擎做硬排盘，LLM 做软推理润色。
- **文件改动**：`web/app.py`（新增可选开关，配置 API key 后开启）
- **预期效果**：文本从"模板填空"变"个性化撰写"，单个改动效果最明显。
- **⚠️ 不确定点**：API key 管理、延迟 1-3s、用户隐私。

### 4.2 RAG 知识库检索（建议延后）

- 将 md 分段+embeddings，推理时检索 Top-3 注入 LLM prompt。
- 需 sentence-transformers/向量存储，架构复杂度高。

---

## 整体路线图

| 阶段 | 优先级 | 工作量 | 效果预期 | 风险 |
|------|--------|--------|---------|------|
| 1.3 节气精确化 | P0 | 低(20行) | 年柱错误减少50%+ | 低风险 |
| 1.2 空亡/六破 | P0 | 低(60行) | 排盘完整+10% | 低风险 |
| 1.1 知识库加载器 | P0 | 中(200行) | 知识库可用 | md格式不统一 |
| 3.1 化气格增强 | P1 | 低(50行) | 特殊格+10% | 需回归 |
| 3.2 从格调优 | P1 | 低(40行) | 从格对齐 | 过度检出风险 |
| 2.2 评分层次化 | P1 | 低(80行) | 评分可追溯 | 低风险 |
| 2.1 数据驱动推理 | P1 | 中高(300行) | 个性化+50% | 纯规则上限有限 |
| 4.1 LLM推理质检 | P2 | 中(100行) | **效果最明显** | API key/延迟 |
| 4.2 RAG检索 | P2 | 高 | 深度知识利用 | 架构复杂 |

**推荐执行顺序**：1.3 → 1.2 → 1.1 → 3.1+3.2 → 2.2 → 2.1 → 4.1

---

## 自检清单

- [x] 方案有具体文件/代码路径
- [x] 方案可执行（每项都有改动方向和示例）
- [x] 标注了不确定/需要验证的部分
- [x] 区分"立即可做"(P0)和"需要调研"(P2)
- [x] 给出了推荐执行顺序和路线图
- [ ] **仍需验证**：阶段2.1的去重率测试、阶段3.2的回归测试

---

## 附录：关键文件改动速览

| 文件 | 改动 | 行数 |
|------|------|------|
| `bazi_immortal/knowledge_loader.py` | 新建 | 150-200 |
| `bazi_immortal/constants.py` | 补充 DZ_LIU_PO | 15 |
| `bazi_immortal/predictions.py` | 重写评分+预测 | 400-500 |
| `bazi_immortal/wuxing.py` | 格局检测增强 | 80-100 |
| `bazi_immortal/calculator.py` | 节气精确化 | 20 |
| `web/app.py` | LLM 质检开关 | 80-100 |
