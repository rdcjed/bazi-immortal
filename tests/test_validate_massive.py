import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_massive


def test_validate_massive_all_pass():
    """Validate that the massive celebrity test suite has no failures."""
    results, stats = validate_massive.run_test()
    assert stats["failed"] == 0, f"Massive validation failed with {stats['failed']} cases"
    assert stats["passed"] == stats["total"]
