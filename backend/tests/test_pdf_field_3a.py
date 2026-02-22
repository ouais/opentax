
from pdf_generator import generate_1040
import unittest
import sys
import os
import io
from pypdf import PdfReader

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestPDFField3a(unittest.TestCase):
    def test_qualified_dividends_field(self):
        # 1. Setup Input Data
        # We want to test Line 3a (Qualified Dividends) which maps to f1_50[0]
        test_val = 1234.56

        tax_results = {
            'federal': {
                'gross_income': 50000,
                'qualified_dividends': test_val,
                'taxable_income': 40000,
                'total_federal_tax': 5000
            },
            'amount_owed': 5000.0,
            'total_dividends': 2500.00,  # Line 3b (Ordinary Dividends)
            'total_wages': 45000.0
        }

        pii = {
            'firstName': "Test", 'lastName': "User",
            'ssn': "000-00-0000"
        }

        # 2. Generate PDF
        pdf_stream = generate_1040(tax_results, pii)

        # Save to file for manual inspection
        output_path = "test_output/test_field_3a.pdf"
        if not os.path.exists("test_output"):
            os.makedirs("test_output")

        with open(output_path, "wb") as f:
            f.write(pdf_stream.getvalue())
        print(f"\nGenerated PDF saved to: {output_path}")

        # 3. Read PDF and Verify Field
        reader = PdfReader(io.BytesIO(pdf_stream.getvalue()))

        # Helper to find field value
        found_value = None
        target_field_leaf = 'f1_58[0]'  # Line 3a

        # Manual iteration to avoid get_fields() issues
        for page in reader.pages:
            if '/Annots' in page:
                for annot in page['/Annots']:
                    obj = annot.get_object()
                    if obj and '/T' in obj:
                        # print(f"Found Code Field: {obj['/T']} Value: {obj.get('/V')}")
                        if obj['/T'] == target_field_leaf:
                            found_value = obj.get('/V')
                            break
            if found_value is not None:
                break

        print(f"\nChecked Field (Line 3a) '{target_field_leaf}'")
        print(f"Expected: {test_val:.2f}")
        print(f"Found:    {found_value}")

        self.assertEqual(str(found_value), f"{test_val:.2f}")

        # Verify Line 3b (Ordinary Dividends) - f1_59[0]
        target_field_3b = 'f1_59[0]'
        found_val_3b = None
        for page in reader.pages:
            if '/Annots' in page:
                for annot in page['/Annots']:
                    obj = annot.get_object()
                    if obj and '/T' in obj and obj['/T'] == target_field_3b:
                        found_val_3b = obj.get('/V')
                        break

        expected_3b = 2500.00
        print(f"\nChecked Field (Line 3b) '{target_field_3b}'")
        print(f"Expected: {expected_3b:.2f}")
        print(f"Found:    {found_val_3b}")

        self.assertEqual(str(found_val_3b), f"{expected_3b:.2f}")


if __name__ == '__main__':
    unittest.main()
