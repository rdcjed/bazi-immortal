# 🛠 RA 体验问题修复方案

> PD 设计文档 · 针对 5 个 RA 体验检查发现的问题

---

## 🔴 问题 1：CSS 变量 `--bg-gold` 未定义

### 问题描述
`web/templates/index.html` 第 390、397 行使用 `background:var(--bg-gold)`，但 `:root` CSS 变量块中只定义了 `--gold` 和 `--gold-dim`，从未定义 `--bg-gold`。LLM 分析区域实际显示为透明白色背景（fallback），与本应呈现的金色调背景不符。

### 修改方案

**文件**：`web/templates/index.html`

**改动 A（推荐）：在 `:root` 中添加 `--bg-gold` 变量**

第 11 行附近，在 `:root{}` 块中新增：

```css
--bg:#0d0d12;--card:#16161e;--card2:#1c1c28;
--border:#2a2a3a;--gold:#d4a853;--gold-dim:#a8853a;
--bg-gold:rgba(212,168,83,.08);   /* ← 新增：金调半透明背景 */
```

**改动 B（备选）：直接修改两处 inline style，用已知变量替换**

若不想新增变量，可将两处 `background:var(--bg-gold)` 替换为：
- 方案 B1：`background:var(--card2)`（保持与其它卡片一致）
- 方案 B2：`background:rgba(212,168,83,.08)`（手动硬编码）

**推荐方案 A**，原因：
1. `--bg-gold` 语义明确，符合设计意图
2. 新增 CSS 变量不破坏任何现有代码
3. 未来其他金色背景元素也可复用

---

## 🟡 问题 2：周易知识库完全闲置

### 问题描述
- `knowledge_base/周易知识库/` 下 9 个文件（含核心 4 个 + 参考 5 个）从未被加载
- `knowledge_loader.py` 只从 `knowledge_base/八字命理知识库/` 读取
- `web/app.py` 第 173-187 行加载知识库时只取了 4 个 key（五行详解、八字排盘、格局体系、神煞大全）
- LLM prompt 从未注入周易/梅花易数/风水/面相手相等知识

### 修改方案

**文件 1**：`bazi_immortal/knowledge_loader.py`

#### 改动 1a：扩展 `_get_knowledge_dir()` 为多目录支持

新增一个函数以获取周易知识库路径：

```python
def _get_zhouyi_knowledge_dir() -> str:
    """获取周易知识库目录路径"""
    import bazi_immortal
    return os.path.join(
        os.path.dirname(os.path.dirname(bazi_immortal.__file__)),
        'knowledge_base', '周易知识库'
    )
```

#### 改动 1b：扩展 `load_all_knowledge()` 合并两个知识库

```python
def load_all_knowledge() -> Dict[str, str]:
    """
    加载所有知识库文件（八字命理 + 周易）
    Returns:
        Dict[str, str]: key 为文件名（不含 .md），value 为全文
    """
    result = {}
    # 加载八字命理知识库
    for dir_name in ['八字命理知识库', '周易知识库']:
        knowledge_dir = os.path.join(
            os.path.dirname(os.path.dirname(bazi_immortal.__file__)),
            'knowledge_base', dir_name
        )
        try:
            if not os.path.isdir(knowledge_dir):
                continue
            for fname in os.listdir(knowledge_dir):
                if not fname.endswith('.md'):
                    continue
                key = fname[:-3]
                fpath = os.path.join(knowledge_dir, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        result[key] = f.read()
                except Exception:
                    continue
        except Exception:
            continue
    return result
```

#### 改动 1c（可选）：保留 `_get_knowledge_dir()` 兼容性

```python
def _get_knowledge_dir() -> str:
    """保留兼容性的旧函数，行为不变"""
    import bazi_immortal
    return os.path.join(
        os.path.dirname(os.path.dirname(bazi_immortal.__file__)),
        'knowledge_base', '八字命理知识库'
    )
```

**文件 2**：`web/app.py`

#### 改动 2a：在 LLM prompt 中包含周易知识

第 182 行附近，修改知识库选择逻辑：

```python
keys = [
    "00_五行详解", "02_八字排盘十神大运", "11_格局体系", "04_神煞大全",
    # ── 新增：周易知识库 ──
    "01_六十四卦详解", "02_起卦体用断卦", "04_八卦详解与风水基础",
]
```

#### 改动 2b：在 prompt 正文中增加周易知识引用段落

第 208 行附近，在 "## 知识库参考" 段落后增加周易专门的引用块：

```
## 周易参考
{kb_zhouyi_context}

## 知识库参考
{kb_context}
```

相应地在 Python 代码中构造 `kb_zhouyi_context`：

```python
# 周易知识（独立注入）
kb_zhouyi_context = ""
zhouyi_keys = ["01_六十四卦详解", "02_起卦体用断卦", "04_八卦详解与风水基础"]
for key in zhouyi_keys:
    if key in knowledge:
        kb_zhouyi_context += f"\n### {key}\n{knowledge[key][:400]}\n"
```

#### 改动 2c：修改 prompt 的「请分析以下内容」部分，提示可使用周易

在第 210 行后，添加：

```
8. 如需，可参考周易卦象和风水原则辅助判断
```

---

## 🟡 问题 3：异常降级不完整

### 问题描述
`web/app.py` 第 500 行 `except (ValueError, TypeError):` 只捕获两种异常。当表单处理中出现 `KeyError`（如缺失字段）、`AttributeError` 等时，会传播到 Flask 导致 500 错误页面，而非返回友好的错误提示。

### 修改方案

**文件**：`web/app.py`

#### 改动：扩大异常捕获范围

第 500 行：

```python
# 原来：
except (ValueError, TypeError):
    error = "请填写有效的数字格式"

# 改为：
except (ValueError, TypeError, KeyError, AttributeError):
    error = "提交数据格式异常，请检查输入"
```

**更推荐的方案（捕获所有 Exception）：**

```python
except Exception as e:
    error = f"数据处理异常：{str(e)[:80]}"
```

原因：`request.form.get()` 有默认值不会主动抛 KeyError，但 `form_values` 字典的字段可能在代码逻辑中缺失。捕获 `Exception` 并截断消息是最稳健的做法，避免用户看到 raw traceback。

---

## 🟢 问题 4：ten-summary 无 CSS 样式

### 问题描述
`web/templates/index.html` 第 774 行 `<div class="ten-summary">{{ ten_year.summary }}</div>` 未定义对应的 CSS 类。10 年运势摘要直接显示纯文字，无背景色、无边框、无内边距，与其他卡片样式不协调。

### 修改方案

**文件**：`web/templates/index.html`

#### 改动：在第 228 行后新增 `.ten-summary` CSS 规则

在 `/* 10年运势 */` 区块的 `.year-detail` 样式之后（约 228 行），新增：

```css
.ten-summary{
  background:linear-gradient(135deg,var(--card2),rgba(212,168,83,.06));
  border:1px solid var(--border);
  border-radius:10px;padding:16px 18px;
  margin-bottom:14px;
  font-size:14px;line-height:1.8;
  color:var(--text-bright);
  border-left:3px solid var(--gold);
}
```

设计思路：
- 使用 `--gold` 左边框延续金色视觉语言
- `linear-gradient` 轻微金色底纹区分于其他卡片
- 统一的圆角、边距与 section-body 内其他元素对齐

---

## 🟢 问题 5：地点推荐逻辑欠完善

### 问题描述
`web/templates/index.html` 第 755 行：

```html
{% if result.location.is_recommended %}{% else %}
<div class="stat-row"><span class="label">是否推荐</span><span class="value">❌ 不推荐</span></div>
{% endif %}
```

- `is_recommended=True` 时：**什么都不显示**（无「✅ 推荐」行）
- `is_recommended=False` 时：显示「❌ 不推荐」
- 显示不对称，用户体验不一致

### 修改方案

**文件**：`web/templates/index.html`

#### 改动：对称显示推荐状态

第 755 行：

```html
{% if result.location.is_recommended %}
<div class="stat-row"><span class="label">是否推荐</span><span class="value">✅ 推荐</span></div>
{% else %}
<div class="stat-row"><span class="label">是否推荐</span><span class="value">❌ 不推荐</span></div>
{% endif %}
```

两种情况下都显示「是否推荐」行，值分别为「✅ 推荐」和「❌ 不推荐」，完全对称。

---

## 📋 改动汇总

| # | 优先级 | 文件 | 改动类型 | 影响范围 | 估算行 |
|---|--------|------|----------|----------|--------|
| 1 | 🔴 | `web/templates/index.html` | 在 `:root` 新增 CSS 变量 `--bg-gold` | LLM 分析区域背景色修复 | +1 |
| 2a | 🟡 | `bazi_immortal/knowledge_loader.py` | 改造 `load_all_knowledge()` 支持多目录 | 周易知识库被 LLM 使用 | ~+20 |
| 2b | 🟡 | `web/app.py` | LLM prompt 注入周易知识 | 深度命理分析质量提升 | ~+15 |
| 3 | 🟡 | `web/app.py` | 扩大 `except` 捕获范围 | 全局表单异常容错 | ~±2 |
| 4 | 🟢 | `web/templates/index.html` | 新增 `.ten-summary` CSS 类 | 10年运势摘要视觉改善 | ~+8 |
| 5 | 🟢 | `web/templates/index.html` | 对称化 `is_recommended` 模板逻辑 | 地点推荐显示一致性 | ~±2 |

## 🔧 实施建议

1. **先修 🔴 问题 1**：只改动 CSS 变量定义，无风险
2. **再修 🟢 问题 4+5**：纯模板/CSS 改动，无逻辑风险
3. **再修 🟡 问题 3**：异常捕获扩大，微改动
4. **最后修 🟡 问题 2**：涉及模块改造和 prompt 优化，需要验证 LLM 输出质量

每个问题都可以独立上线，互不依赖。