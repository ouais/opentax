
import io
import sys
import os
# Add parent directory to path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# import pytest (Running as script)
from pypdf import PdfReader
from pdf_generator import generate_1040

def test_1040_field_mapping_and_layout():
    """
    Verifies that fields are populated with correct values AND are in the correct visual order.
    """
    # 1. Setup Test Data with Unique Values
    summary = {
        'total_wages': 111111.0,
        'total_interest': 22222.0,
        'total_dividends': 33333.0,
        'total_capital_gains': 44444.0,
        
        'federal': {
            'gross_income': 55555.0, # Total Income / AGI
            'standard_deduction': 77777.0,
            'taxable_income': 88888.0,
            'ordinary_income_tax': 1000.0,
            'capital_gains_tax': 2000.0,
            'total_federal_tax': 99999.0, # Final Tax
            'qualified_dividends': 11111.0,
            'total_ordinary_dividends': 33333.0,
        },
        'total_federal_withheld': 101010.0,
        'estimated_tax_payments': 121212.0,
        'other_withholding': 0.0,
        'amount_owed': 131313.0
    }
    
    pii = {
        'firstName': "TEST", 'lastName': "USER",
        'ssn': "123-00-1234",
        'address': "123 Test Lane",
        'city': "TestCity", 'state': "TS", 'zip': "99999"
    }

    # 2. Generate PDF
    pdf_stream = generate_1040(summary, pii)
    reader = PdfReader(io.BytesIO(pdf_stream.getvalue()))

    # 3. Extract Field Data (Name, Value, Rect)
    field_map = {}
    
    # Helper to find which field contains a specific value string
    def find_field_by_value(target_val):
        target_str = f"{target_val:.2f}"
        for page in reader.pages:
            if '/Annots' in page:
                for annot in page['/Annots']:
                    obj = annot.get_object()
                    if '/V' in obj and str(obj['/V']) == target_str:
                         return obj
        return None

    # 4. Verify Content, Field Names & Placement
    
    # Wages (1z) -> Expect f1_47
    wages_field = find_field_by_value(summary['total_wages'])
    assert wages_field, "Wages value not found in PDF"
    wages_name = wages_field.get('/T', 'Unknown')
    assert 'f1_47' in wages_name or 'Wages' in wages_name, f"Wages in wrong field: {wages_name}"
    wages_y = wages_field['/Rect'][1]
    print(f"Wages Field: {wages_name}, Y: {wages_y}")

    # Interest (2b) -> Expect f1_49
    interest_field = find_field_by_value(summary['total_interest'])
    assert interest_field, "Interest value not found in PDF"
    interest_name = interest_field.get('/T', 'Unknown')
    assert 'f1_49' in interest_name, f"Interest in wrong field: {interest_name}"
    interest_y = interest_field['/Rect'][1]
    
    # Assert Wages is ABOVE Interest (Higher Y)
    assert wages_y > interest_y, f"Wages (Y={wages_y}) should be above Interest (Y={interest_y})"

    # Dividends (3b) -> Expect f1_51 (uses federal total_ordinary_dividends)
    div_field = find_field_by_value(summary['federal']['total_ordinary_dividends'])
    assert div_field, "Dividends value not found"
    div_name = div_field.get('/T', 'Unknown')
    assert 'f1_51' in div_name, f"Dividends in wrong field: {div_name}"
    div_y = div_field['/Rect'][1]
    
    # Assert Interest ABOVE Dividends
    assert interest_y > div_y, "Interest should be above Dividends"

    # Taxable Income (15) -> Expect f1_69
    taxable_field = find_field_by_value(summary['federal']['taxable_income'])
    assert taxable_field, "Taxable Income not found"
    taxable_name = taxable_field.get('/T', 'Unknown')
    assert 'f1_69' in taxable_name, f"Taxable Income in wrong field: {taxable_name}"
    
    # Total Tax (24) -> Expect f2_10 (and/or f2_02 for Line 16)
    # The summary has total_federal_tax = 99999.0.
    # We mapped it to both Line 16 (f2_02) and Line 24 (f2_10).
    # find_field_by_value returns the *first* one found.
    # We should verify both exist if possible, or just that *one* valid tax field has it.
    
    total_tax_field = find_field_by_value(summary['federal']['total_federal_tax'])
    assert total_tax_field, "Total Tax not found"
    tax_name = total_tax_field.get('/T', 'Unknown')
    assert 'f2_02' in tax_name or 'f2_10' in tax_name, f"Tax in wrong field: {tax_name}"

    print("Test Passed: Values are in Correct Fields and Layout Order is Logical.")

def test_3a_3b_dividend_split():
    """
    Verifies that Line 3a has qualified dividends and Line 3b has
    ordinary dividends (always >= qualified per IRS rules).
    Covers the edge case where the parser sets ordinary_dividends=0
    but qualified_dividends > 0.
    """
    # Case 1: Normal case — ordinary > qualified
    summary1 = {
        'total_wages': 75000.0,
        'total_interest': 500.0,
        'total_dividends': 3000.0,  # raw ordinary dividends from 1099-DIV
        'total_capital_gains': 0.0,
        'federal': {
            'gross_income': 79500.0,
            'standard_deduction': 14600.0,
            'taxable_income': 64900.0,
            'ordinary_income_tax': 9500.0,
            'capital_gains_tax': 150.0,
            'total_federal_tax': 9650.0,
            'qualified_dividends': 1000.0,
        },
        'total_federal_withheld': 8000.0,
        'estimated_tax_payments': 0.0,
        'other_withholding': 0.0,
        'amount_owed': 1650.0,
    }

    pii = {
        'firstName': 'Jane', 'lastName': 'Doe',
        'ssn': '000-00-0000',
        'address': '456 Oak Ave',
        'city': 'Anytown', 'state': 'CA', 'zip': '90000',
    }

    pdf_stream = generate_1040(summary1, pii)
    reader = PdfReader(io.BytesIO(pdf_stream.getvalue()))

    fields = {}
    for page in reader.pages:
        if '/Annots' in page:
            for annot in page['/Annots']:
                obj = annot.get_object()
                name = str(obj.get('/T', ''))
                value = str(obj.get('/V', ''))
                if name and value:
                    fields[name] = value

    def get_field_value(target_name):
        for name, value in fields.items():
            if target_name in name:
                return value
        return None

    # 3a = qualified, 3b = ordinary (>= qualified)
    assert get_field_value('f1_50') == '1000.00', \
        f"Case 1: Line 3a expected '1000.00', got '{get_field_value('f1_50')}'"
    assert get_field_value('f1_51') == '3000.00', \
        f"Case 1: Line 3b expected '3000.00', got '{get_field_value('f1_51')}'"

    print("Case 1 Passed: Normal dividend split correct.")

    # Case 2: Edge case — ordinary_dividends=0 in parser but qualified > 0
    summary2 = {
        'total_wages': 80000.0,
        'total_interest': 0.0,
        'total_dividends': 0.0,  # parser set ordinary to 0
        'total_capital_gains': 0.0,
        'federal': {
            'gross_income': 80656.22,
            'standard_deduction': 14600.0,
            'taxable_income': 66056.22,
            'ordinary_income_tax': 9700.0,
            'capital_gains_tax': 100.0,
            'total_federal_tax': 9800.0,
            'qualified_dividends': 656.22,  # qualified present
        },
        'total_federal_withheld': 10000.0,
        'estimated_tax_payments': 0.0,
        'other_withholding': 0.0,
        'amount_owed': -200.0,
    }

    pdf_stream2 = generate_1040(summary2, pii)
    reader2 = PdfReader(io.BytesIO(pdf_stream2.getvalue()))

    fields2 = {}
    for page in reader2.pages:
        if '/Annots' in page:
            for annot in page['/Annots']:
                obj = annot.get_object()
                name = str(obj.get('/T', ''))
                value = str(obj.get('/V', ''))
                if name and value:
                    fields2[name] = value

    def get_field_value2(target_name):
        for name, value in fields2.items():
            if target_name in name:
                return value
        return None

    # 3a = 656.22, 3b should also be 656.22 (not empty!)
    assert get_field_value2('f1_50') == '656.22', \
        f"Case 2: Line 3a expected '656.22', got '{get_field_value2('f1_50')}'"
    assert get_field_value2('f1_51') == '656.22', \
        f"Case 2: Line 3b expected '656.22', got '{get_field_value2('f1_51')}'"

    print("Case 2 Passed: Edge case (ordinary=0, qualified>0) handled correctly.")


if __name__ == "__main__":
    test_1040_field_mapping_and_layout()
    test_3a_3b_dividend_split()
