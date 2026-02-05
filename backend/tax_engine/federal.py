"""
Federal Tax Calculator - Tax Year 2024

Implements federal income tax calculation including:
- Ordinary income tax brackets
- Long-term capital gains tax rates
- Qualified dividend tax rates
- Self-employment tax
- Additional Medicare Tax (0.9% on wages over $200k)
"""

from typing import TypedDict


class FederalTaxResult(TypedDict):
    """Result of federal tax calculation."""
    gross_income: float
    standard_deduction: float
    taxable_income: float
    ordinary_income_tax: float
    capital_gains_tax: float
    self_employment_tax: float
    additional_medicare_tax: float
    total_federal_tax: float
    effective_rate: float
    marginal_rate: float
    bracket_breakdown: list[dict]


# Tax rates by year
TAX_RATES = {
    2024: {
        'brackets': [
            (11600, 0.10),
            (47150, 0.12),
            (100525, 0.22),
            (191950, 0.24),
            (243725, 0.32),
            (609350, 0.35),
            (float('inf'), 0.37),
        ],
        'standard_deduction': 14600,
        'ltcg_brackets': [
            (47025, 0.00),
            (518900, 0.15),
            (float('inf'), 0.20),
        ],
        'ss_wage_base': 168600,
    },
    2025: {
        'brackets': [
            (11925, 0.10),
            (48475, 0.12),
            (103350, 0.22),
            (197300, 0.24),
            (250525, 0.32),
            (626350, 0.35),
            (float('inf'), 0.37),
        ],
        'standard_deduction': 15750,
        'ltcg_brackets': [
            (48350, 0.00),
            (533400, 0.15),
            (float('inf'), 0.20),
        ],
        'ss_wage_base': 176100,
    },
}

# Constants that don't change by year
SE_TAX_RATE_SOCIAL_SECURITY = 0.124  # 12.4%
SE_TAX_RATE_MEDICARE = 0.029  # 2.9%
SE_TAX_RATE_ADDITIONAL_MEDICARE = 0.009  # 0.9%
SE_ADDITIONAL_MEDICARE_THRESHOLD_SINGLE = 200000

# Default tax year
DEFAULT_TAX_YEAR = 2024


def calculate_tax_from_brackets(
    taxable_income: float,
    brackets: list[tuple[float, float]],
) -> tuple[float, float, list[dict]]:
    """
    Calculate tax using progressive tax brackets.
    
    Args:
        taxable_income: The taxable income amount
        brackets: List of (upper_limit, rate) tuples
        
    Returns:
        Tuple of (total_tax, marginal_rate, bracket_breakdown)
    """
    if taxable_income <= 0:
        return 0.0, brackets[0][1], []
    
    total_tax = 0.0
    previous_limit = 0.0
    marginal_rate = 0.0
    breakdown = []
    
    for upper_limit, rate in brackets:
        if taxable_income <= previous_limit:
            break
            
        bracket_income = min(taxable_income, upper_limit) - previous_limit
        if bracket_income > 0:
            tax_in_bracket = bracket_income * rate
            total_tax += tax_in_bracket
            marginal_rate = rate
            breakdown.append({
                'range_start': previous_limit,
                'range_end': min(taxable_income, upper_limit),
                'rate': rate,
                'income_in_bracket': bracket_income,
                'tax_in_bracket': tax_in_bracket,
            })
        
        previous_limit = upper_limit
    
    return total_tax, marginal_rate, breakdown


def calculate_capital_gains_tax(
    taxable_income: float,
    long_term_gains: float,
    qualified_dividends: float,
    tax_year: int = DEFAULT_TAX_YEAR,
) -> float:
    """
    Calculate tax on long-term capital gains and qualified dividends.
    
    These get preferential rates but stack on top of ordinary income
    to determine which bracket applies.
    """
    if long_term_gains <= 0 and qualified_dividends <= 0:
        return 0.0
    
    total_preferential_income = long_term_gains + qualified_dividends
    if total_preferential_income <= 0:
        return 0.0
    
    # The starting point for capital gains is the end of ordinary income
    starting_income = taxable_income
    ending_income = taxable_income + total_preferential_income
    
    total_tax = 0.0
    previous_limit = 0.0
    
    ltcg_brackets = TAX_RATES[tax_year]['ltcg_brackets']
    for upper_limit, rate in ltcg_brackets:
        # Skip brackets below our starting point
        if upper_limit <= starting_income:
            previous_limit = upper_limit
            continue
        
        # Calculate the portion of gains in this bracket
        bracket_start = max(starting_income, previous_limit)
        bracket_end = min(ending_income, upper_limit)
        
        if bracket_end > bracket_start:
            gains_in_bracket = bracket_end - bracket_start
            total_tax += gains_in_bracket * rate
        
        if ending_income <= upper_limit:
            break
            
        previous_limit = upper_limit
    
    return total_tax


def calculate_self_employment_tax(
    self_employment_income: float,
    w2_social_security_wages: float = 0.0,
    tax_year: int = DEFAULT_TAX_YEAR,
) -> tuple[float, float, float]:
    """
    Calculate self-employment tax (Social Security + Medicare).
    
    Args:
        self_employment_income: Net self-employment income
        w2_social_security_wages: Social Security wages from W-2s
        tax_year: The tax year for rate selection
        
    Returns:
        Tuple of (total_se_tax, social_security_portion, medicare_portion)
    """
    if self_employment_income <= 0:
        return 0.0, 0.0, 0.0
    
    # Net SE earnings = 92.35% of net SE income (accounts for employer portion)
    net_se_earnings = self_employment_income * 0.9235
    
    # Social Security portion (12.4%)
    # Reduced by any W-2 SS wages already paid
    ss_wage_base = TAX_RATES[tax_year]['ss_wage_base']
    ss_wage_room = max(0, ss_wage_base - w2_social_security_wages)
    ss_taxable = min(net_se_earnings, ss_wage_room)
    ss_tax = ss_taxable * SE_TAX_RATE_SOCIAL_SECURITY
    
    # Medicare portion (2.9% on all SE earnings)
    medicare_tax = net_se_earnings * SE_TAX_RATE_MEDICARE
    
    # Additional Medicare tax (0.9% on SE income over threshold)
    if net_se_earnings > SE_ADDITIONAL_MEDICARE_THRESHOLD_SINGLE:
        additional_medicare = (net_se_earnings - SE_ADDITIONAL_MEDICARE_THRESHOLD_SINGLE) * SE_TAX_RATE_ADDITIONAL_MEDICARE
        medicare_tax += additional_medicare
    
    total_se_tax = ss_tax + medicare_tax
    
    return total_se_tax, ss_tax, medicare_tax


def calculate_federal_tax(
    wages: float = 0.0,
    interest_income: float = 0.0,
    ordinary_dividends: float = 0.0,
    qualified_dividends: float = 0.0,
    short_term_gains: float = 0.0,
    long_term_gains: float = 0.0,
    self_employment_income: float = 0.0,
    w2_social_security_wages: float = 0.0,
    tax_year: int = DEFAULT_TAX_YEAR,
) -> FederalTaxResult:
    """
    Calculate total federal tax liability for a Single filer.
    
    Args:
        wages: W-2 wages
        interest_income: Interest income (1099-INT)
        ordinary_dividends: Non-qualified dividends (1099-DIV Box 1a - 1b)
        qualified_dividends: Qualified dividends (1099-DIV Box 1b)
        short_term_gains: Short-term capital gains (taxed as ordinary income)
        long_term_gains: Long-term capital gains
        self_employment_income: 1099-NEC income
        w2_social_security_wages: Box 3 from W-2s (for SE tax calculation)
        tax_year: The tax year (2024 or 2025)
        
    Returns:
        FederalTaxResult with complete tax breakdown
    """
    # Get rates for the selected year
    rates = TAX_RATES[tax_year]
    
    # Calculate gross income
    # Note: Capital losses are limited to $3,000 offset against ordinary income
    net_st = short_term_gains
    net_lt = long_term_gains
    total_net_capital_gains = net_st + net_lt
    
    # Schedule D Netting Logic
    taxable_ordinary_capital_gain = 0.0
    taxable_preferential_capital_gain = 0.0
    
    if total_net_capital_gains < 0:
        # Net Capital Loss: Deduct up to $3,000 against ordinary income
        deductible_loss = max(total_net_capital_gains, -3000.0)
        taxable_ordinary_capital_gain = deductible_loss
        taxable_preferential_capital_gain = 0.0
    else:
        # Net Capital Gain
        if net_st > 0 and net_lt > 0:
            # Both positive: Tax separately
            taxable_ordinary_capital_gain = net_st
            taxable_preferential_capital_gain = net_lt
        elif net_st > 0 and net_lt <= 0:
            # ST Gain absorbs LT Loss: Tax excess as ordinary
            taxable_ordinary_capital_gain = total_net_capital_gains
            taxable_preferential_capital_gain = 0.0
        elif net_st <= 0 and net_lt > 0:
            # LT Gain absorbs ST Loss: Tax excess as preferential
            taxable_ordinary_capital_gain = 0.0
            taxable_preferential_capital_gain = total_net_capital_gains
    
    # Gross income includes total NET capital gain (or deductible loss)
    # The limit applies to how much can be deducted from OTHER income types, 
    # but for gross income definition it's usually just the sum. 
    # However, for tax calculation flow, using the deductible amount is safer for AGI.
    gross_income_capital_component = taxable_ordinary_capital_gain + taxable_preferential_capital_gain
    
    gross_income = (
        wages +
        interest_income +
        ordinary_dividends +
        qualified_dividends +
        gross_income_capital_component +
        self_employment_income
    )
    
    # Self-employment deduction (half of SE tax)
    se_tax_total, se_ss_tax, se_medicare_tax = calculate_self_employment_tax(
        self_employment_income,
        w2_social_security_wages,
        tax_year,
    )
    se_deduction = se_tax_total / 2
    
    # Adjusted Gross Income
    agi = gross_income - se_deduction
    
    # Apply standard deduction
    standard_deduction = rates['standard_deduction']
    taxable_income_before_preferential = max(0, agi - standard_deduction)
    
    # Ordinary income (taxed at regular rates)
    ordinary_income = (
        wages +
        interest_income +
        ordinary_dividends +  # Non-qualified dividends
        taxable_ordinary_capital_gain + # Net ST gain or deductible loss
        self_employment_income -
        se_deduction -
        standard_deduction
    )
    ordinary_income = max(0, ordinary_income)
    
    # Calculate ordinary income tax
    ordinary_tax, marginal_rate, bracket_breakdown = calculate_tax_from_brackets(
        ordinary_income,
        rates['brackets'],
    )
    
    # Calculate capital gains tax (on LTCG + qualified dividends)
    capital_gains_tax = calculate_capital_gains_tax(
        ordinary_income,
        taxable_preferential_capital_gain, # Net LT gain
        qualified_dividends,
        tax_year,
    )
    
    # Total federal income tax
    total_income_tax = ordinary_tax + capital_gains_tax
    
    # Additional Medicare Tax (0.9% on W-2 wages over $200k) - Schedule 2, Part I
    additional_medicare_tax = 0.0
    if wages > SE_ADDITIONAL_MEDICARE_THRESHOLD_SINGLE:
        additional_medicare_tax = (wages - SE_ADDITIONAL_MEDICARE_THRESHOLD_SINGLE) * SE_TAX_RATE_ADDITIONAL_MEDICARE
    
    # Total federal tax (income tax + SE tax + Additional Medicare Tax)
    total_federal_tax = total_income_tax + se_tax_total + additional_medicare_tax
    
    # Effective rate
    effective_rate = (total_federal_tax / gross_income * 100) if gross_income > 0 else 0.0
    
    return {
        'gross_income': gross_income,
        'standard_deduction': standard_deduction,
        'taxable_income': taxable_income_before_preferential,
        'ordinary_income_tax': ordinary_tax,
        'capital_gains_tax': capital_gains_tax,
        'self_employment_tax': se_tax_total,
        'additional_medicare_tax': additional_medicare_tax,
        'total_federal_tax': total_federal_tax,
        'effective_rate': effective_rate,
        'marginal_rate': marginal_rate * 100,
        'bracket_breakdown': bracket_breakdown,
    }

