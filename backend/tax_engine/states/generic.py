import json
import os
from ..state_interface import StateTaxCalculator, StateTaxInput, StateTaxResult
from ..utils import calculate_tax_from_brackets

# Load states.json once when module is imported
DATA_DIR = os.path.dirname(os.path.dirname(__file__))
STATES_FILE = os.path.join(DATA_DIR, 'data', 'states.json')

with open(STATES_FILE, 'r') as f:
    STATES_DATA = json.load(f)

class GenericStateCalculator(StateTaxCalculator):
    def __init__(self, state_code: str):
        self.state_code = state_code.upper()
        self.state_data = STATES_DATA.get(self.state_code)
        if not self.state_data:
            raise ValueError(f"State code {self.state_code} not found in states.json")

    def calculate(self, tax_input: StateTaxInput) -> StateTaxResult:
        has_income_tax = self.state_data.get('has_income_tax', False)
        if not has_income_tax:
            return self._calculate_no_tax(tax_input)

        tax_year = tax_input.get('tax_year', 2024)
        year_str = str(tax_year)

        # Fallback to 2024 if year not found
        if year_str not in self.state_data:
            year_str = "2024"

        year_data = self.state_data.get(year_str, {})

        # Approximate AGI if not provided
        federal_agi = tax_input.get('federal_agi', 0.0)
        if federal_agi == 0.0:
            wages = tax_input.get('wages', 0.0)
            interest = tax_input.get('interest_income', 0.0)
            divs = tax_input.get('dividend_income', 0.0)
            caps = tax_input.get('capital_gains', 0.0)
            se = tax_input.get('self_employment_income', 0.0)
            federal_agi = wages + interest + divs + caps + se

        filing_status = tax_input.get('filing_status', 'single')

        # Standard deduction
        std_deduction_map = year_data.get('std_deduction', {})
        std_deduction = std_deduction_map.get(filing_status, std_deduction_map.get('single', 0.0))

        taxable_income = max(0.0, federal_agi - std_deduction)

        # Brackets
        brackets_map = year_data.get('brackets', {})
        raw_brackets = brackets_map.get(filing_status, brackets_map.get('single', []))

        # Convert null to float('inf')
        brackets = []
        for upper, rate in raw_brackets:
            if upper is None:
                brackets.append((float('inf'), rate))
            else:
                brackets.append((float(upper), float(rate)))

        tax, marginal, breakdown = calculate_tax_from_brackets(taxable_income, brackets)

        return {
            "total_taxable_income": taxable_income,
            "total_state_tax": tax,
            "standard_deduction": std_deduction,
            "exemption_credit": 0.0,
            "bracket_breakdown": breakdown,
            "breakdown": breakdown,  # Alias for compatibility
            "effective_rate": (tax / federal_agi * 100) if federal_agi > 0 else 0.0,
            "marginal_rate": marginal,
            "mental_health_tax": 0.0,

            # Legacy/Frontend compatibility
            "gross_income": federal_agi,
            "taxable_income": taxable_income,
            "state_tax": tax,
            "mental_health_surcharge": 0.0,
            "total_california_tax": tax,
            "total_state_tax": tax
        }

    def _calculate_no_tax(self, tax_input: StateTaxInput) -> StateTaxResult:
        wages = tax_input.get('wages', 0.0)
        federal_agi = tax_input.get('federal_agi', wages)
        notes = self.state_data.get('notes', f"{self.state_data['name']} has no state income tax.")

        return {
            "total_taxable_income": 0.0,
            "total_state_tax": 0.0,
            "standard_deduction": 0.0,
            "exemption_credit": 0.0,
            "bracket_breakdown": [{"bracket": notes, "amount": 0.0, "rate": 0.0, "tax": 0.0}],
            "breakdown": [{"bracket": notes, "amount": 0.0, "rate": 0.0, "tax": 0.0}],
            "effective_rate": 0.0,
            "marginal_rate": 0.0,
            "mental_health_tax": 0.0,
            "gross_income": federal_agi,
            "taxable_income": 0.0,
            "state_tax": 0.0,
            "mental_health_surcharge": 0.0,
            "total_california_tax": 0.0,
            "total_state_tax": 0.0
        }

    def get_standard_deduction(self, filing_status: str, tax_year: int) -> float:
        if not self.state_data.get('has_income_tax', False):
            return 0.0

        year_str = str(tax_year)
        if year_str not in self.state_data:
            year_str = "2024"

        year_data = self.state_data.get(year_str, {})
        std_deduction_map = year_data.get('std_deduction', {})
        return std_deduction_map.get(filing_status, std_deduction_map.get('single', 0.0))
