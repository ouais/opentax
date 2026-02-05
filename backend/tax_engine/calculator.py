"""
Unified Tax Calculator

Combines federal and California tax calculations into a single API.
"""

from typing import TypedDict
from .federal import calculate_federal_tax, FederalTaxResult
from .california import calculate_california_tax, CaliforniaTaxResult


class TaxInput(TypedDict, total=False):
    """Input for tax calculation."""
    # W-2 income
    w2_wages: float
    w2_federal_withheld: float
    w2_state_withheld: float
    w2_social_security_wages: float
    
    # Interest income (1099-INT)
    interest_income: float
    interest_federal_withheld: float
    
    # Dividend income (1099-DIV)
    ordinary_dividends: float
    qualified_dividends: float
    capital_gain_distributions: float
    dividend_federal_withheld: float
    
    # Capital gains (1099-B)
    short_term_gains: float
    long_term_gains: float
    
    # Self-employment (1099-NEC)
    self_employment_income: float
    self_employment_federal_withheld: float
    
    # Tax Year
    tax_year: int
    
    # Validation / Additional Payments
    estimated_tax_payments: float
    other_withholding: float


class TaxSummary(TypedDict):
    """Complete tax calculation summary."""
    # Income totals
    total_wages: float
    total_interest: float
    total_dividends: float
    total_capital_gains: float
    total_self_employment: float
    gross_income: float
    
    # Federal
    federal: FederalTaxResult
    
    # California
    california: CaliforniaTaxResult
    
    # Withholding
    total_federal_withheld: float
    total_state_withheld: float
    
    # Bottom line
    total_tax_liability: float
    total_withheld: float
    amount_owed: float  # positive = owe, negative = refund
    refund_or_owed: str  # "refund" or "owed"


def calculate_taxes(tax_input: TaxInput) -> TaxSummary:
    """
    Calculate complete federal and California tax liability.
    
    Args:
        tax_input: Dictionary with all income and withholding amounts
        
    Returns:
        TaxSummary with complete breakdown
    """
    # Extract values with defaults
    w2_wages = tax_input.get('w2_wages', 0.0)
    w2_federal_withheld = tax_input.get('w2_federal_withheld', 0.0)
    w2_state_withheld = tax_input.get('w2_state_withheld', 0.0)
    w2_social_security_wages = tax_input.get('w2_social_security_wages', 0.0)
    w2_casdi = tax_input.get('w2_casdi', 0.0)  # CA State Disability Insurance
    
    
    estimated_tax_payments = tax_input.get('estimated_tax_payments', 0.0)
    other_withholding = tax_input.get('other_withholding', 0.0)
    
    interest_income = tax_input.get('interest_income', 0.0)
    interest_federal_withheld = tax_input.get('interest_federal_withheld', 0.0)
    
    ordinary_dividends = tax_input.get('ordinary_dividends', 0.0)
    qualified_dividends = tax_input.get('qualified_dividends', 0.0)
    capital_gain_distributions = tax_input.get('capital_gain_distributions', 0.0)
    dividend_federal_withheld = tax_input.get('dividend_federal_withheld', 0.0)
    
    short_term_gains = tax_input.get('short_term_gains', 0.0)
    long_term_gains = tax_input.get('long_term_gains', 0.0)
    
    self_employment_income = tax_input.get('self_employment_income', 0.0)
    self_employment_federal_withheld = tax_input.get('self_employment_federal_withheld', 0.0)
    
    # Calculate totals
    total_wages = w2_wages
    total_interest = interest_income
    total_dividends = ordinary_dividends  # qualified is subset of ordinary
    total_capital_gains = short_term_gains + long_term_gains + capital_gain_distributions
    total_self_employment = self_employment_income
    
    gross_income = (
        total_wages +
        total_interest +
        total_dividends +
        total_capital_gains +
        total_self_employment
    )
    
    # Calculate federal tax
    # Note: ordinary_dividends includes qualified, so we subtract to get non-qualified
    non_qualified_dividends = ordinary_dividends - qualified_dividends
    
    federal_result = calculate_federal_tax(
        wages=w2_wages,
        interest_income=interest_income,
        ordinary_dividends=non_qualified_dividends,
        qualified_dividends=qualified_dividends,
        short_term_gains=short_term_gains,
        long_term_gains=long_term_gains + capital_gain_distributions,
        self_employment_income=self_employment_income,
        w2_social_security_wages=w2_social_security_wages,
        tax_year=tax_year,
    )
    
    # Calculate California tax
    california_result = calculate_california_tax(
        wages=w2_wages,
        interest_income=interest_income,
        dividend_income=ordinary_dividends,
        capital_gains=total_capital_gains,
        self_employment_income=self_employment_income,
        tax_year=tax_year,
    )
    
    # Calculate withholding totals
    total_federal_withheld = (
        w2_federal_withheld +
        interest_federal_withheld +
        dividend_federal_withheld +
        self_employment_federal_withheld +
        estimated_tax_payments + 
        other_withholding
    )
    # Include CASDI in state withholding (it's a California-specific payment)
    total_state_withheld = w2_state_withheld + w2_casdi
    
    # Calculate bottom line
    total_tax_liability = federal_result['total_federal_tax'] + california_result['total_california_tax']
    total_withheld = total_federal_withheld + total_state_withheld
    amount_owed = total_tax_liability - total_withheld
    
    return {
        'total_wages': total_wages,
        'total_interest': total_interest,
        'total_dividends': total_dividends,
        'total_capital_gains': total_capital_gains,
        'total_self_employment': total_self_employment,
        'gross_income': gross_income,
        'federal': federal_result,
        'california': california_result,
        'total_federal_withheld': total_federal_withheld,
        'total_state_withheld': total_state_withheld,
        'total_tax_liability': total_tax_liability,
        'total_withheld': total_withheld,
        'amount_owed': amount_owed,
        'refund_or_owed': 'refund' if amount_owed < 0 else 'owed',
    }
