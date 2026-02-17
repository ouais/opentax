
import unittest
import sys
import os

# Add backend to path (3 levels up to reach backend/ from backend/tests/states/california)
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, '../../../'))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from tax_engine.states.california import CaliforniaStateCalculator

class TestCaliforniaTax(unittest.TestCase):
    def setUp(self):
        self.calc = CaliforniaStateCalculator()

    def test_standard_deduction_2024(self):
        # 2024 Single Standard Deduction is 5540
        self.assertEqual(self.calc.get_standard_deduction('SINGLE', 2024), 5540)

    def test_basic_tax_calculation(self):
        # Income below standard deduction -> 0 tax
        res = self.calc.calculate({'wages': 5000, 'tax_year': 2024})
        self.assertEqual(res['total_state_tax'], 0.0)
        self.assertEqual(res['taxable_income'], 0.0)

    def test_taxable_income_calculation(self):
        # Income 10,000. Std Ded 5,540. Taxable 4,460.
        res = self.calc.calculate({'wages': 10000, 'tax_year': 2024})
        self.assertEqual(res['taxable_income'], 10000 - 5540)
        # Tax verified roughly
        self.assertTrue(res['state_tax'] > 0)

    def test_mental_health_surcharge(self):
        # Income > 1M. 1% surcharge.
        # Gross = 2,000,000. Taxable ~ 1,994,460.
        # Surcharge on (1,994,460 - 1,000,000) = 994,460 * 0.01 = 9,944.60
        res = self.calc.calculate({'wages': 2000000, 'tax_year': 2024})
        
        expected_surcharge = (res['taxable_income'] - 1000000) * 0.01
        self.assertAlmostEqual(res['mental_health_surcharge'], expected_surcharge, places=2)
        self.assertTrue(res['mental_health_surcharge'] > 0)

    def test_capital_gains_are_ordinary(self):
        # CA taxes cap gains as ordinary
        res_wages = self.calc.calculate({'wages': 50000, 'tax_year': 2024})
        res_cap = self.calc.calculate({'capital_gains': 50000, 'tax_year': 2024})
        
        # Tax should be identical for same dollar amount
        self.assertAlmostEqual(res_wages['total_state_tax'], res_cap['total_state_tax'], places=2)

if __name__ == '__main__':
    unittest.main()
