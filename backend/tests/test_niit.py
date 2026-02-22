import pytest
import sys
import os

# Add parent directory to path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tax_engine.federal import calculate_federal_tax

def test_no_niit_below_threshold():
    """Verify no NIIT is charged if MAGI is below the threshold."""
    result = calculate_federal_tax(
        wages=50000,
        long_term_gains=100000,  # Lots of investment income!
        filing_status='single'
    )

    # MAGI = 150000. Threshold = 200000. NIIT should be 0.
    assert result['net_investment_income_tax'] == 0.0

def test_no_niit_no_investment_income():
    """Verify no NIIT is charged if there is $0 investment income, even with high wages."""
    result = calculate_federal_tax(
        wages=300000,  # High earner!
        long_term_gains=0,
        interest_income=0,
        ordinary_dividends=0,
        qualified_dividends=0,
        filing_status='joint'
    )

    # MAGI = 300000. Threshold = 250000. But NII = 0.
    assert result['net_investment_income_tax'] == 0.0

def test_niit_applied_to_lesser_amount():
    """Verify NIIT is 3.8% on the *lesser* of NII or MAGI over threshold."""
    # Case 1: MAGI overage < NII
    result1 = calculate_federal_tax(
        wages=200000,
        long_term_gains=100000,
        filing_status='joint'  # Threshold: 250000
    )
    # MAGI = 300000. Threshold = 250000. Overage = 50000.
    # NII = 100000. Lesser is 50000.
    # NIIT = 50000 * 0.038 = 1900
    assert result1['net_investment_income_tax'] == 1900.0

    # Case 2: NII < MAGI overage
    result2 = calculate_federal_tax(
        wages=300000,
        interest_income=10000,
        filing_status='single'  # Threshold: 200000
    )
    # MAGI = 310000. Threshold = 200000. Overage = 110000.
    # NII = 10000. Lesser is 10000.
    # NIIT = 10000 * 0.038 = 380
    assert result2['net_investment_income_tax'] == 380.0
