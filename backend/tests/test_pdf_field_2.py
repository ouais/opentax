
from pdf_generator import generate_1040
import unittest
import sys
import os
import io
from pypdf import PdfReader

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestPDFField2(unittest.TestCase):
    def test_interest_fields(self):
        # Setup Input Data for Line 2a/2b
        # 2a (Tax Exempt) = f1_56[0] (Hypothesis)
        # 2b (Taxable) = f1_57[0] (Confirmed)

        # Setup test data
        pii = {'firstName': "Test", 'lastName': "User", 'ssn': "000"}
        exempt_val = 1111.11
        taxable_val = 2222.22

        tax_results = {
            'federal': {'gross_income': 50000},
            'total_interest': taxable_val,
            'total_tax_exempt_interest': exempt_val
        }

        # Generate
        pdf_stream = generate_1040(tax_results, pii)
        reader = PdfReader(io.BytesIO(pdf_stream.getvalue()))

        # Verify
        found_exempt = None
        found_taxable = None

        for page in reader.pages:
            if '/Annots' in page:
                for annot in page['/Annots']:
                    obj = annot.get_object()
                    t = obj.get('/T')
                    v = obj.get('/V')
                    if t == 'f1_56[0]':
                        found_exempt = v
                    if t == 'f1_57[0]':
                        found_taxable = v

        print(f"2a (Exempt) Found: {found_exempt}, Expected: {exempt_val}")
        print(f"2b (Taxable) Found: {found_taxable}, Expected: {taxable_val}")

        self.assertEqual(found_exempt, f"{exempt_val:.2f}")
        self.assertEqual(found_taxable, f"{taxable_val:.2f}")

    def test_dividends_empty(self):
        # Test 3a/3b empty behavior
        pii = {'firstName': "Test", 'lastName': "User", 'ssn': "000"}
        tax_results = {
            'federal': {'qualified_dividends': 0},
            'total_dividends': 0
        }

        pdf_stream = generate_1040(tax_results, pii)
        reader = PdfReader(io.BytesIO(pdf_stream.getvalue()))

        # Helper check
        def get_val(field):
            for p in reader.pages:
                if '/Annots' in p:
                    for a in p['/Annots']:
                        o = a.get_object()
                        if o.get('/T') == field:
                            return o.get('/V')
            return None

        v3a = get_val('f1_58[0]')
        v3b = get_val('f1_59[0]')

        print(f"3a (0 input): '{v3a}'")
        print(f"3b (0 input): '{v3b}'")


if __name__ == '__main__':
    unittest.main()
