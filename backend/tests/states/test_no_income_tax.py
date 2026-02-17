
import unittest
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from backend.tax_engine.registry import StateTaxRegistry

class TestNoIncomeTaxStates(unittest.TestCase):
    def test_no_income_tax_states(self):
        # List of states that should have 0 income tax
        no_tax_states = ['TX', 'FL', 'WA', 'TN', 'NV', 'SD', 'WY', 'AK', 'NH']
        
        # Standard input that would trigger tax in CA/NY
        input_data = {
            'wages': 100000,
            'interest_income': 500,
            'dividend_income': 1000,
            'capital_gains': 5000,
            'self_employment_income': 0,
            'tax_year': 2024,
            'federal_agi': 106500,
            'federal_taxable_income': 91900,
            'filing_status': 'single'
        }

        for state in no_tax_states:
            with self.subTest(state=state):
                calc = StateTaxRegistry.get_calculator(state)
                result = calc.calculate(input_data)
                
                self.assertEqual(result['total_california_tax'], 0, f"{state} should have 0 tax")
                # Note: valid because NoIncomeTaxState returns a structure compatible with standard result keys
                # typically 'total_state_tax' or similar. 
                # Let's check NoIncomeTaxState implementation if it returns 'total_california_tax' 
                # or if that key is just a remnant of using the CA model.
                # Actually, calculator.py uses `result['total_california_tax']` line 195. 
                # So NoIncomeTaxState MUST return that key.
                
if __name__ == '__main__':
    unittest.main()
