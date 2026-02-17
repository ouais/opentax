
import unittest
from utils import extract_payer_name_from_text, clean_name

class TestVanguardExtraction(unittest.TestCase):
    def test_vanguard_layout(self):
        # Simulated Vanguard 1099-DIV text layout
        # Note: Vanguard often puts the name/address block significantly above the "PAYER'S name" label
        text = """
        Vanguard Marketing Corporation
        P.O. Box 982901
        El Paso, TX 79998-2901
        
        
        
        PAYER'S name, street address, city or town, state or province, country, and ZIP or foreign postal code
        """
        
        name = extract_payer_name_from_text(text)
        print(f"Extracted: '{name}'")
        self.assertEqual(name, "Vanguard Marketing Corporation")

    def test_vanguard_layout_2(self):
        # Another common variation with phone numbers or account info in between
        text = """
        Vanguard Brokage Services
        A division of Vanguard Marketing Corporation
        P.O. Box 982901
        El Paso, TX 79998-2901
        Phone: 800-555-1234
        
        PAYER'S name, street address, city or town, state or province, country, and ZIP or foreign postal code
        """
        
        name = extract_payer_name_from_text(text)
        print(f"Extracted 2: '{name}'")
        self.assertIn("Vanguard", name)

if __name__ == '__main__':
    unittest.main()
