import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from parsers.w2 import parse_w2

def debug_parser():
    pdf_path = "backend/debug_last_upload.pdf"
    if not os.path.exists(pdf_path):
        print("Debug PDF not found")
        return

    result = parse_w2(pdf_path)
    print("--- Extracted Data ---")
    print(f"Wages (Box 1): {result.get('wages')}")
    print(f"Federal Tax (Box 2): {result.get('federal_tax_withheld')}")
    print(f"SS Wages (Box 3): {result.get('social_security_wages')}")
    print(f"Medicare Wages (Box 5): {result.get('medicare_wages')}")
    print(f"Medicare Tax (Box 6): {result.get('medicare_tax_withheld')}")
    
    if result.get('medicare_wages') == 0 or result.get('medicare_wages') is None:
        print("\n[FAIL] Medicare Wages (Box 5) not extracted.")
    else:
        print("\n[PASS] Medicare Wages extracted.")

    if result.get('medicare_tax_withheld') == 0 or result.get('medicare_tax_withheld') is None:
        print("[FAIL] Medicare Tax (Box 6) not extracted.")
    else:
        print("[PASS] Medicare Tax extracted.")

if __name__ == "__main__":
    debug_parser()
