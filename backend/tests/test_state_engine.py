import pytest
from tax_engine.calculator import calculate_taxes

def test_no_income_tax_state():
    tax_input = {
        'w2_wages': 100000,
        'state': 'TX',
        'filing_status': 'single',
        'tax_year': 2024
    }
    result = calculate_taxes(tax_input)
    assert result['california']['total_state_tax'] == 0.0
    assert result['california']['effective_rate'] == 0.0

def test_new_york_state_tax():
    tax_input = {
        'w2_wages': 100000,
        'state': 'NY',
        'filing_status': 'single',
        'tax_year': 2024
    }
    result = calculate_taxes(tax_input)
    # AGI = 100,000. Std Ded = 8000. Taxable = 92,000.
    # Brackets:
    # 8500 * 0.04 = 340
    # (11700 - 8500 = 3200) * 0.045 = 144
    # (13900 - 11700 = 2200) * 0.0525 = 115.5
    # (80650 - 13900 = 66750) * 0.0585 = 3904.875
    # (92000 - 80650 = 11350) * 0.0625 = 709.375
    # Total = 340 + 144 + 115.5 + 3904.875 + 709.375 = 5213.75
    calc_state = result['california']
    assert calc_state['standard_deduction'] == 8000.0
    assert calc_state['total_taxable_income'] == 92000.0
    assert abs(calc_state['total_state_tax'] - 5213.75) < 0.1
    assert calc_state['marginal_rate'] == 0.0625

def test_unknown_state_fallback():
    # Test a placeholder territory like Guam (GU) which we set has_income_tax=False
    tax_input = {
        'w2_wages': 100000,
        'state': 'GU',
        'filing_status': 'single',
        'tax_year': 2024
    }
    result = calculate_taxes(tax_input)
    assert result['california']['total_california_tax'] == 0.0
    assert "Territory tax system not yet fully integrated" in result['california']['breakdown'][0]['bracket']

def test_puerto_rico_tax():
    # PR Single 2024:
    # 0-9000: 0%
    # 9001-25000: 7%
    # 25000 wages
    # 0-9000: 0
    # 9000-25000: 16000 * 0.07 = 1120
    tax_input = {
        'w2_wages': 25000,
        'state': 'PR',
        'filing_status': 'single',
        'tax_year': 2024
    }
    result = calculate_taxes(tax_input)
    assert result['california']['total_california_tax'] == 1120.0

def test_colorado_flat_tax():
    # CO 2024: 4.4% flat tax, $14,600 std deduction
    # 100,000 wages
    # Taxable: 100,000 - 14,600 = 85,400
    # Tax: 85,400 * 0.044 = 3757.6
    tax_input = {
        'w2_wages': 100000,
        'state': 'CO',
        'filing_status': 'single',
        'tax_year': 2024
    }
    result = calculate_taxes(tax_input)
    assert round(result['california']['total_california_tax'], 2) == 3757.60
