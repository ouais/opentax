"""
California State Tax Calculator - Multi-Year Support

Implements California state income tax calculation.
"""

from typing import TypedDict
from ..utils import calculate_tax_from_brackets


class CaliforniaTaxResult(TypedDict):
    """Result of California tax calculation."""
    gross_income: float
    standard_deduction: float
    taxable_income: float
    state_tax: float
    mental_health_surcharge: float
    total_california_tax: float
    effective_rate: float
    marginal_rate: float
    bracket_breakdown: list[dict]


# California tax rates by year
CA_TAX_RATES = {
    2024: {
        'single': {
            'brackets': [
                (10756, 0.01),
                (25499, 0.02),
                (40245, 0.04),
                (55866, 0.06),
                (70606, 0.08),
                (360659, 0.093),
                (432787, 0.103),
                (721314, 0.113),
                (float('inf'), 0.123),
            ],
            'standard_deduction': 5540,
        },
        'joint': {
            'brackets': [
                (21512, 0.01),
                (50998, 0.02),
                (80490, 0.04),
                (111732, 0.06),
                (141212, 0.08),  # Wait, search result said 142976 for 9.3% start. 70606*2=141212.
                (721318, 0.093), # 360659*2=721318
                (865574, 0.103), # 432787*2=865574
                (1442628, 0.113), # 721314*2=1442628
                (float('inf'), 0.123),
            ],
            'standard_deduction': 11080,
        },
    },
    2025: {
        'single': {
            'brackets': [
                (11079, 0.01),
                (26264, 0.02),
                (41452, 0.04),
                (57542, 0.06),
                (72724, 0.08),
                (371479, 0.093),
                (445771, 0.103),
                (742953, 0.113),
                (float('inf'), 0.123),
            ],
            'standard_deduction': 5706,
        },
        'joint': {
            'brackets': [
                (22158, 0.01),
                (52528, 0.02),
                (82904, 0.04),
                (115084, 0.06),
                (145448, 0.08),
                (742958, 0.093),
                (891542, 0.103),
                (1485906, 0.113),
                (float('inf'), 0.123),
            ],
            'standard_deduction': 11412,
        },
    },
}

# Mental Health Services Tax threshold (same for both years)
CA_MENTAL_HEALTH_THRESHOLD = 1000000
CA_MENTAL_HEALTH_RATE = 0.01

# Default tax year
DEFAULT_TAX_YEAR = 2024


# calculate_tax_from_brackets moved to utils.py


def calculate_california_tax(
    wages: float = 0.0,
    interest_income: float = 0.0,
    dividend_income: float = 0.0,
    capital_gains: float = 0.0,
    self_employment_income: float = 0.0,
    tax_year: int = DEFAULT_TAX_YEAR,
    filing_status: str = 'single',
) -> CaliforniaTaxResult:
    """
    Calculate California state tax liability.
    
    Note: California taxes capital gains as ordinary income (no preferential rate).
    
    Args:
        wages: W-2 wages
        interest_income: Interest income
        dividend_income: All dividend income (CA doesn't distinguish qualified)
        capital_gains: All capital gains (both short and long term)
        self_employment_income: 1099-NEC income
        tax_year: The tax year (2024 or 2025)
        filing_status: 'single' or 'joint'
        
    Returns:
        CaliforniaTaxResult with complete tax breakdown
    """
    # Get rates for selected year and filing status
    rates = CA_TAX_RATES[tax_year][filing_status]

    # Calculate gross income - California taxes nearly everything as ordinary income
    gross_income = (
        wages +
        interest_income +
        dividend_income +
        capital_gains +
        self_employment_income
    )
    
    # Apply standard deduction
    standard_deduction = rates['standard_deduction']
    taxable_income = max(0, gross_income - standard_deduction)
    
    # Calculate state tax using brackets
    state_tax, marginal_rate, bracket_breakdown = calculate_tax_from_brackets(
        taxable_income,
        rates['brackets'],
    )
    
    # Mental Health Services Tax (1% on income over $1M)
    mental_health_surcharge = 0.0
    if taxable_income > CA_MENTAL_HEALTH_THRESHOLD:
        mental_health_surcharge = (taxable_income - CA_MENTAL_HEALTH_THRESHOLD) * CA_MENTAL_HEALTH_RATE
    
    # Total California tax
    total_california_tax = state_tax + mental_health_surcharge
    
    # Effective rate
    effective_rate = (total_california_tax / gross_income * 100) if gross_income > 0 else 0.0
    
    return {
        'gross_income': gross_income,
        'standard_deduction': standard_deduction,
        'taxable_income': taxable_income,
        'state_tax': state_tax,
        'mental_health_surcharge': mental_health_surcharge,
        'total_california_tax': total_california_tax,
        'effective_rate': effective_rate,
        'marginal_rate': marginal_rate * 100,
        'bracket_breakdown': bracket_breakdown,
    }


from ..state_interface import StateTaxCalculator, StateTaxInput, StateTaxResult

class CaliforniaStateCalculator(StateTaxCalculator):
    def calculate(self, tax_input: StateTaxInput) -> StateTaxResult:
        # Call Existing Logic
        res = calculate_california_tax(
            wages=tax_input.get('wages', 0.0),
            interest_income=tax_input.get('interest_income', 0.0),
            dividend_income=tax_input.get('dividend_income', 0.0),
            capital_gains=tax_input.get('capital_gains', 0.0),
            self_employment_income=tax_input.get('self_employment_income', 0.0),
            tax_year=tax_input.get('tax_year', 2024),
            filing_status=tax_input.get('filing_status', 'single')
        )
        
        # Map to Generic Result
        return {
            "total_taxable_income": res['taxable_income'],
            "total_state_tax": res['total_california_tax'],
            "standard_deduction": res['standard_deduction'],
            # Preserve CA specific fields (Legacy for Frontend)
            "gross_income": res['gross_income'],
            "taxable_income": res['taxable_income'],
            "state_tax": res['state_tax'],
            "mental_health_surcharge": res['mental_health_surcharge'],
            "total_california_tax": res['total_california_tax'],
            "mental_health_tax": res['mental_health_surcharge'],
            "bracket_breakdown": res['bracket_breakdown'],
            "effective_rate": res['effective_rate'],
            "marginal_rate": res['marginal_rate'],
            "exemption_credit": 0.0
        }

    def get_standard_deduction(self, filing_status: str, tax_year: int) -> float:
        rates = CA_TAX_RATES.get(tax_year, CA_TAX_RATES[2024])
        return rates['standard_deduction']
