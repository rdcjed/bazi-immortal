import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bazi_immortal import (
    calculate_bazi,
    bazi_to_string,
    calculate_da_yun,
    get_liu_nian,
    analyze_ri_zuo_strong_weak,
)
from bazi_immortal.cli import parse_time


class TestBaziEngine(unittest.TestCase):
    def test_calculate_bazi_returns_four_pillars(self):
        bazi = calculate_bazi(1990, 5, 15, 12, 0, '男')
        self.assertEqual(len(bazi.si_zhu), 4)
        self.assertEqual(bazi.gender, '男')
        self.assertTrue(all(hasattr(p, 'gan_zhi') for p in bazi.si_zhu))

    def test_bazi_to_string_contains_expected_headers(self):
        bazi = calculate_bazi(1990, 5, 15, 12, 0, '男')
        text = bazi_to_string(bazi)
        self.assertIn('年柱', text)
        self.assertIn('日主', text)
        self.assertIn('性别', text)

    def test_analyze_ri_zuo_strong_weak_returns_required_keys(self):
        bazi = calculate_bazi(1990, 5, 15, 12, 0, '男')
        result = analyze_ri_zuo_strong_weak(bazi)
        self.assertIsInstance(result, dict)
        for key in ['strong_weak', 'useful_god', 'avoid_god', 'distribution', 'score']:
            self.assertIn(key, result)

    def test_calculate_da_yun_has_eight_steps(self):
        bazi = calculate_bazi(1990, 5, 15, 12, 0, '男')
        result = calculate_da_yun(bazi, birth_time=(1990, 5, 15, 12, 0))
        self.assertEqual(result['direction'], '顺排')
        self.assertEqual(len(result['da_yun_list']), 8)
        self.assertAlmostEqual(result['start_age'], round(result['start_age'], 2))

    def test_get_liu_nian_returns_correct_year_and_keys(self):
        result = get_liu_nian(2026)
        self.assertEqual(result['year'], 2026)
        self.assertIn('gan_zhi', result)
        self.assertIn('tian_gan', result)
        self.assertIn('di_zhi', result)


class TestCliUtilities(unittest.TestCase):
    def test_parse_time_hour_minute(self):
        self.assertEqual(parse_time('14:30'), (14, 30))
        self.assertEqual(parse_time('9:05'), (9, 5))

    def test_parse_time_shichen(self):
        self.assertEqual(parse_time('子'), (23, 0))
        self.assertEqual(parse_time('午'), (11, 0))

    def test_parse_time_numeric_hour(self):
        self.assertEqual(parse_time('7'), (7, 0))

    def test_parse_time_default(self):
        self.assertEqual(parse_time(''), (12, 0))


if __name__ == '__main__':
    unittest.main()
