import validate_logic


def test_validate_logic_runs_without_errors():
    results = validate_logic.analyze()
    assert isinstance(results, dict)
    assert results, "Expected at least one category of celebrity results"


def test_validate_logic_contains_chinese_politics():
    results = validate_logic.analyze()
    assert "中国政界" in results
    assert any(item["name"] == "毛泽东" for item in results["中国政界"])


def test_validate_logic_results_structure():
    results = validate_logic.analyze()
    total = 0
    for category, items in results.items():
        assert isinstance(items, list)
        assert items, f"Category {category} should contain at least one item"
        for item in items:
            assert "name" in item
            assert "strong_weak" in item
            assert "useful" in item
            assert "avoid" in item
            assert "cat_counts" in item
            total += 1
    assert total == len(validate_logic.CELEBRITIES)
