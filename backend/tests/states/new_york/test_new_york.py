
import unittest
import sys
import os

# Add backend to path (3 levels up to reach backend/ from backend/tests/states/new_york)
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, '../../../'))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from tax_engine.states.new_york import NewYorkStateCalculator

class TestNewYorkTax(unittest.TestCase):
    def setUp(self):
        self.calc = NewYorkStateCalculator()

    def test_standard_deduction_2024(self):
        # 2024 Single Standard Deduction is 8000
        self.assertEqual(self.calc.get_standard_deduction('SINGLE', 2024), 8000.0)

    def test_basic_non_taxable(self):
        # Income below standard deduction
        res = self.calc.calculate({'wages': 7000, 'tax_year': 2024})
        self.assertEqual(res['total_state_tax'], 0.0)

    def test_basic_taxable(self):
        # Income 20,000. Std Ded 8,000. Taxable 12,000.
        # Tax should be > 0
        res = self.calc.calculate({'wages': 20000, 'tax_year': 2024})
        self.assertEqual(res['total_taxable_income'], 12000)
        self.assertTrue(res['total_state_tax'] > 0)

    def test_federal_agi_fallback(self):
        # NY calc uses federal_agi if present, or aggregates components
        res_direct = self.calc.calculate({'federal_agi': 50000, 'tax_year': 2024})
        res_components = self.calc.calculate({'wages': 50000, 'tax_year': 2024})
        
        self.assertAlmostEqual(res_direct['total_state_tax'], res_components['total_state_tax'], places=2)

if __name__ == '__main__':
    unittest.main()
