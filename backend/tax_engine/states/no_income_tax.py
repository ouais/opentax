from ..state_interface import StateTaxCalculator, StateTaxInput, StateTaxResult


class NoIncomeTaxState(StateTaxCalculator):
    def calculate(self, tax_input: StateTaxInput) -> StateTaxResult:
        return {
            "total_taxable_income": 0.0,
            "total_state_tax": 0.0,
            "standard_deduction": 0.0,
            "exemption_credit": 0.0,
            "bracket_breakdown": [],
            "effective_rate": 0.0,
            "marginal_rate": 0.0,  # Required by Frontend
            "mental_health_tax": 0.0,

            # Frontend Compatibility (Legacy Keys)
            "gross_income": tax_input.get('wages', 0.0),  # Approximate
            "taxable_income": 0.0,
            "state_tax": 0.0,
            "mental_health_surcharge": 0.0,
            "total_california_tax": 0.0
        }

    def get_standard_deduction(
            self,
            filing_status: str,
            tax_year: int) -> float:
        return 0.0
