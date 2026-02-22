from tax_engine.calculator import calculate_taxes
from tax_engine.federal import calculate_federal_tax
import sys
import os
import pytest

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


def test_additional_medicare_withholding_calculation():
    """
    Verify that the 0.9% Additional Medicare Tax withholding is correctly
    calculated and separated from the regular 1.45% Medicare tax.
    """
    # Scenario: $250,000 wages (Single filer)
    # Threshold for Additional Medicare Tax: $200,000
    # Expected Additional Tax Liability: ($250,000 - $200,000) * 0.9% = $450

    # Expected Withholding:
    # Regular (1.45% of $250k) = $3,625
    # Additional (0.9% of excess over $200k) = $450
    # Total Box 6 should be $4,075

    wages = 250000
    medicare_wages = 250000
    medicare_tax_withheld = 4075  # $3625 + $450

    print(
        f"DEBUG_TEST: Calling calculate_federal_tax with filing_status='single' wages={wages}")
    result = calculate_federal_tax(
        wages=wages,
        w2_medicare_wages=medicare_wages,
        w2_medicare_tax=medicare_tax_withheld,
        filing_status='single'
    )
    print(
        f"DEBUG_TEST: Result additional_medicare_tax={result.get('additional_medicare_tax')}")

    # Check if calculation identifies the $450 correctly
    assert result['additional_medicare_withholding'] == pytest.approx(
        450.0, abs=0.01)
    assert result['additional_medicare_tax'] == pytest.approx(450.0, abs=0.01)


def test_total_withholding_integrates_medicare_credit():
    """
    Verify that calculate_taxes includes the additional medicare withholding
    in the total_federal_withheld sum.
    """
    # Using the same numbers
    tax_input = {
        'w2_wages': 250000,
        'w2_medicare_wages': 250000,
        'w2_medicare_tax': 4075,  # Contains $450 excess
        'w2_federal_withheld': 50000,  # Arbitrary base withholding
        'filing_status': 'single',
        'tax_year': 2024
    }

    result = calculate_taxes(tax_input)

    # Total withheld should be:
    # Federal Withholding ($50,000) + Additional Medicare Withholding ($450)
    # = $50,450

    expected_withholding = 50000 + 450
    assert result['total_federal_withheld'] == expected_withholding

    # Ensure amount_owed reflects this credit
    # Liability will be calculated by engine -> Amount Owed = Liability - Withheld
    # We just want to check the withholding part drove the result down
    assert result['total_withheld'] >= expected_withholding


if __name__ == "__main__":
    test_additional_medicare_withholding_calculation()
    test_total_withholding_integrates_medicare_credit()
    print("All Medicare withholding tests passed!")
