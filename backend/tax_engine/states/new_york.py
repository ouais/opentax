from ..state_interface import StateTaxCalculator, StateTaxInput, StateTaxResult
from ..utils import calculate_tax_from_brackets

NY_TAX_RATES = {
    2024: {
        'single_standard_deduction': 8000.0,
        # Simplified Brackets for 2024 (Approximate)
        'brackets': [
            (8500, 0.0400),
            (11700, 0.0450),
            (13900, 0.0525),
            (80650, 0.0585),
            (215400, 0.0625), # 6.25%
            (1077550, 0.0685),
            (5000000, 0.0965),
            (25000000, 0.1030),
            (float('inf'), 0.1090),
        ]
    }
}

class NewYorkStateCalculator(StateTaxCalculator):
    def calculate(self, tax_input: StateTaxInput) -> StateTaxResult:
        tax_year = tax_input.get('tax_year', 2024)
        rates = NY_TAX_RATES.get(tax_year, NY_TAX_RATES[2024])
        
        # NY uses Federal AGI as starting point usually, but with modifications.
        # For MVP, we'll start with Federal AGI if available, else standard calculation.
        federal_agi = tax_input.get('federal_agi', 0.0)
        
        # If federal AGI not passed (e.g. some tests), reconstruct:
        if federal_agi == 0.0:
             # Fallback
             wages = tax_input.get('wages', 0.0)
             interest = tax_input.get('interest_income', 0.0)
             divs = tax_input.get('dividend_income', 0.0)
             caps = tax_input.get('capital_gains', 0.0)
             se = tax_input.get('self_employment_income', 0.0)
             federal_agi = wages + interest + divs + caps + se # Rough approximation
        
        # Deductions
        std_deduction = rates['single_standard_deduction']
        taxable_income = max(0.0, federal_agi - std_deduction)
        
        # Calculate Tax
        tax, marginal, breakdown = calculate_tax_from_brackets(taxable_income, rates['brackets'])
        
        return {
            "total_taxable_income": taxable_income,
            "total_state_tax": tax,
            "standard_deduction": std_deduction,
            "exemption_credit": 0.0,
            "bracket_breakdown": breakdown,
            "effective_rate": (tax / federal_agi * 100) if federal_agi > 0 else 0.0,
            "marginal_rate": marginal, # Required by Frontend
            "mental_health_tax": 0.0,
            
            # Frontend Compatibility (Legacy Keys)
            "gross_income": federal_agi,
            "taxable_income": taxable_income,
            "state_tax": tax,
            "mental_health_surcharge": 0.0,
            "total_california_tax": 0.0
        }
        
    def get_standard_deduction(self, filing_status: str, tax_year: int) -> float:
        rates = NY_TAX_RATES.get(tax_year, NY_TAX_RATES[2024])
        return rates['single_standard_deduction']
