import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from tax_engine.federal import calculate_federal_tax

def test_medicare_withholding_split():
    # Case: High income earner where Additional Medicare Tax is withheld
    # Wages = $250,000
    # Employer must withhold:
    # 1.45% on all wages: $250,000 * 0.0145 = $3,625
    # 0.9% on wages over $200k: ($250,000 - $200,000) * 0.009 = $450
    # Total Box 6 should be $3,625 + $450 = $4,075
    
    wages = 250000
    w2_medicare_wages = 250000
    w2_medicare_tax = 4075 # $3625 (reg) + $450 (additional)
    
    result = calculate_federal_tax(
        wages=wages,
        w2_medicare_wages=w2_medicare_wages,
        w2_medicare_tax=w2_medicare_tax,
        filing_status='single'
    )
    
    print(f"Wages: ${wages:,}")
    print(f"Medicare Wages (Box 5): ${w2_medicare_wages:,}")
    print(f"Medicare Tax (Box 6): ${w2_medicare_tax:,}")
    print(f"--- Results ---")
    print(f"Additional Medicare Tax Liability: ${result['additional_medicare_tax']:,.2f}")
    print(f"Additional Medicare Tax Withholding (Line 25c): ${result['additional_medicare_withholding']:,.2f}")
    
    # Expected: $450
    assert abs(result['additional_medicare_withholding'] - 450) < 0.01
    print("\n✅ Verification Successful: Line 25c correctly calculated as $450")

if __name__ == "__main__":
    test_medicare_withholding_split()
