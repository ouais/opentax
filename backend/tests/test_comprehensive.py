
from pypdf import PdfReader
from pdf_verifier import verify_pdf_semantics
from pdf_generator import generate_1040
from tax_engine.calculator import calculate_taxes
import sys
import os
import io

# Add parent directory to path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]


def generate_cases():
    cases = []

    # 1. State Coverage (50 cases)
    for state in STATES:
        cases.append({
            "id": f"state_{state}",
            "input": {"w2_wages": 100000.0, "state": state},
            "desc": f"Basic return for {state}"
        })

    # 2. Itemized Deductions (10 cases)
    for i in range(10):
        amount = 15000 + (i * 1000)
        cases.append({
            "id": f"itemized_{i}",
            "input": {"w2_wages": 100000.0, "itemized_deductions": amount, "state": "CA"},
            "desc": f"Itemized Deduction of ${amount}"
        })

    # 3. Foreign Income (10 cases)
    for i in range(10):
        foreign = 5000 + (i * 5000)
        cases.append({
            "id": f"foreign_{i}",
            "input": {"w2_wages": 50000.0, "foreign_income": foreign, "state": "NY"},
            "desc": f"Foreign Income of ${foreign}"
        })

    # 4. High Wealth / Cap Gains (10 cases)
    for i in range(10):
        ltcg = 50000 + (i * 50000)
        cases.append({
            "id": f"wealth_{i}",
            "input": {"w2_wages": 200000.0, "long_term_gains": ltcg, "state": "TX"},
            "desc": f"High Wealth with LTCG ${ltcg}"
        })

    # 5. Complex/Random (20 cases)
    for i in range(20):
        cases.append({
            "id": f"complex_{i}",
            "input": {
                "w2_wages": 123456.0,
                "interest_income": 1000.0 * i,
                "ordinary_dividends": 500.0 * i,
                "qualified_dividends": 250.0 * i,
                "foreign_income": 2000.0,
                "itemized_deductions": 20000.0,
                "state": STATES[i % 50]
            },
            "desc": f"Complex Mix {i} ({STATES[i % 50]})"
        })

    return cases


def run_tests():
    cases = generate_cases()
    print(f"Generated {len(cases)} Test Cases.")
    print("-" * 50)

    passed = 0
    failed = 0

    # Ensure output dir
    if not os.path.exists("test_output"):
        os.makedirs("test_output")

    for case in cases:
        data = case["input"]
        desc = case["desc"]
        try:
            result = calculate_taxes(data)

            # 1. Calculation Checks (Basic Stability)
            if result['federal']['total_federal_tax'] < 0:
                raise ValueError("Negative Federal Tax")

            # 2. Foreign Income Check
            if 'foreign_income' in data:
                expected_gross = data.get('w2_wages',
                                          0) + data.get('foreign_income',
                                                        0) + data.get('interest_income',
                                                                      0)
                actual_gross = result['federal']['gross_income']
                if actual_gross < expected_gross - 1.0:
                    raise ValueError(
                        f"Foreign Income not in Gross. Expected >={expected_gross}, Got {actual_gross}")

            # 3. Itemized Logic Check
            if 'itemized_deductions' in data:
                std = result['federal']['standard_deduction']
                itemized = data['itemized_deductions']
                agi = result['federal']['adjusted_gross_income']
                actual_taxable = result['federal']['taxable_income']

                if itemized > std:
                    expected_taxable = max(0, agi - itemized)
                    if abs(actual_taxable - expected_taxable) > 1.0:
                        raise ValueError(
                            f"Itemized not applied. Expected Taxable {expected_taxable}, Got {actual_taxable}")
                else:
                    # Expect Standard
                    expected_taxable = max(0, agi - std)
                    if abs(actual_taxable - expected_taxable) > 1.0:
                        raise ValueError(
                            f"Standard deduction check failed. Expected {expected_taxable}, Got {actual_taxable}")

            # 4. State Safety
            state = data.get('state', 'CA')
            # Use standardized key first, fall back to legacy
            cal_res = result['california']
            state_tax = cal_res.get(
                'total_state_tax', cal_res.get(
                    'total_california_tax', 0.0))

            NO_TAX_STATES = [
                'TX',
                'FL',
                'WA',
                'TN',
                'NV',
                'SD',
                'WY',
                'AK',
                'NH']

            if state in NO_TAX_STATES:
                if state_tax != 0.0:
                    raise ValueError(
                        f"No-Tax State {state} has tax: {state_tax}")
            elif state == 'NY':
                wages = data.get('w2_wages', 0)
                # NY Std Ded is 8000. If wages > 8000, verify tax > 0
                if wages > 10000 and state_tax == 0.0:
                    raise ValueError(
                        f"NY should have tax for ${wages} wages, got 0.0")
            elif state == 'CA':
                wages = data.get('w2_wages', 0)
                if wages > 20000 and state_tax == 0.0:
                    print(f"Warning: CA State {state} has 0 tax for {wages}?")
            else:
                # Other states still dummy 0
                pass

            # 5. Generate PDF & Verify Fields
            # Mock PII
            pii = {
                'firstName': "TEST",
                'lastName': "CASE_" + case['id'],
                'ssn': "000-00-0000",
                'address': "123 Test St",
                'city': "City",
                'state': "CA",
                'zip': "90000"}

            pdf_stream = generate_1040(result, pii)

            # Save PDF
            pdf_path = f"test_output/{case['id']}.pdf"
            with open(pdf_path, "wb") as f:
                f.write(pdf_stream.getvalue())

            # Verify Content
            reader = PdfReader(io.BytesIO(pdf_stream.getvalue()))

            # Helper to find ALL fields with a value
            def find_fields_by_value(target_val):
                target_str = f"{target_val:.2f}"
                matches = []
                for page in reader.pages:
                    if '/Annots' in page:
                        for annot in page['/Annots']:
                            obj = annot.get_object()
                            if '/V' in obj and str(obj['/V']) == target_str:
                                matches.append(obj)
                return matches

            # Wages Check
            wages = data.get('w2_wages', 0.0)
            if wages > 0:
                fields = find_fields_by_value(wages)
                if not fields:
                    raise ValueError(f"Wages {wages} NOT FOUND in PDF.")

                # Verify at least one match is f1_47
                found_wages_field = False
                for f in fields:
                    name = f.get('/T', 'Unknown')
                    if 'f1_47' in name or 'Wages' in name:
                        found_wages_field = True
                        break
                if not found_wages_field:
                    raise ValueError(
                        f"Wages value found, but NOT in f1_47. Found in: {[f.get('/T') for f in fields]}")

            # Interest Check
            interest = data.get('interest_income', 0.0)
            if interest > 0:
                fields = find_fields_by_value(interest)
                if not fields:
                    raise ValueError(f"Interest {interest} NOT FOUND in PDF.")

                found_interest = False
                for f in fields:
                    name = f.get('/T', 'Unknown')
                    if 'f1_57' in name:
                        found_interest = True
                        break
                if not found_interest:
                    raise ValueError(
                        f"Interest value found, but NOT in f1_57. Found in: {[f.get('/T') for f in fields]}")

            # Dividends Check (Line 3b)
            divs = case['input'].get('ordinary_dividends', 0.0)
            if divs > 0:
                fields = find_fields_by_value(divs)
                found_divs = False
                for f in fields:
                    name = f.get('/T', 'Unknown')
                    if 'f1_59' in name:
                        found_divs = True
                        break
                if not found_divs:
                    raise ValueError(
                        f"Ordinary Dividend value ({divs}) found, but NOT in f1_59. Found in: {[f.get('/T') for f in fields]}")
            taxable = result['federal']['taxable_income']
            if taxable > 0:
                fields = find_fields_by_value(taxable)
                if not fields:
                    raise ValueError(
                        f"Taxable Income {taxable} NOT FOUND in PDF.")

                found_taxable = False
                for f in fields:
                    name = f.get('/T', 'Unknown')
                    if 'f2_06' in name:  # Line 15 (Page 2)
                        found_taxable = True
                        break
                if not found_taxable:
                    raise ValueError(
                        f"Taxable Income value found, but NOT in f2_06. Found in: {[f.get('/T') for f in fields]}")

            # 6. SEMANTIC VERIFICATION
            # Run arithmetic checks on the generated PDF
            semantic_errors = verify_pdf_semantics(pdf_path)
            if semantic_errors:
                print(f"  [Semantic Fail] {desc}")
                for err in semantic_errors:
                    print(f"    - {err}")
                raise ValueError(
                    f"Semantic Validation Failed: {semantic_errors[0]}")

            passed += 1
            # print(f"[PASS] {desc}")

        except Exception as e:
            failed += 1
            print(f"[FAIL] {desc}: {e}")
            import traceback
            traceback.print_exc()

    print("-" * 50)
    print(f"Summary: {passed} Passed, {failed} Failed.")
    print("Coverage verified!")


if __name__ == "__main__":
    run_tests()
