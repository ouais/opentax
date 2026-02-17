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
