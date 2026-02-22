import pytest
import sys
import os

# Add parent directory to path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tax_engine.calculator import calculate_taxes

def test_filing_status_differences():
    """
    Verify that Single and Married Filing Jointly statuses yield the correct
    standard deductions and tax liabilities for the same income in 2024.
    """

    # Identical income profile
    income_profile = {
        'tax_year': 2024,
        'state': 'CA',
        'w2_wages': 100000.0,
        'w2_federal_withheld': 10000.0,
    }

    # 1. Test Single Filer
    single_input = {**income_profile, 'filing_status': 'single'}
    single_result = calculate_taxes(single_input)

    # 2. Test Joint Filer
    joint_input = {**income_profile, 'filing_status': 'joint'}
    joint_result = calculate_taxes(joint_input)

    # Assert Standard Deductions were picked up correctly (2024 values)
    assert single_result['federal']['standard_deduction'] == 14600.0
    assert joint_result['federal']['standard_deduction'] == 29200.0

    # Single taxable income should be higher due to a lower deduction
    assert single_result['federal']['taxable_income'] > joint_result['federal']['taxable_income']

    # Joint filer should owe less federal tax for the same total income
    assert single_result['federal']['total_federal_tax'] > joint_result['federal']['total_federal_tax']
