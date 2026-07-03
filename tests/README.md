# Tests

本目录包含命理推算验证脚本和测试用例。

## 新增单元测试

`tests/test_core.py` 使用 Python 内置 `unittest` 执行基础功能验证。

运行方式：

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

## Pytest

新增的标准测试可以使用 `pytest` 运行：

```bash
python -m pytest -q
```

## 现有验证脚本

这些脚本用于验证命理规则、名人案例和大规模数据：

- `tests/test_cases.py`：基础命例断言集合
- `tests/validate_logic.py`：名人八字与行业规则验证
- `tests/validate_massive.py`：大规模名人八字验证报告

运行方式：

```bash
python tests/test_cases.py
python tests/validate_logic.py
python tests/validate_massive.py
```

## 推荐流程

1. 先运行 `python -m unittest discover -s tests -p 'test_*.py'` 验证核心引擎接口。
2. 再运行 `python tests/test_cases.py` 和 `python tests/validate_logic.py` 验证命理逻辑。
3. 若需要全面回归，运行 `python tests/validate_massive.py`。
