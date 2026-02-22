
from pypdf import PdfReader
import logging

logger = logging.getLogger(__name__)


def parse_currency(value_str):
    """Parses a currency string like '1,234.56' into a float. Returns 0.0 if empty."""
    if not value_str:
        return 0.0
    try:
        return float(value_str.replace(',', '').strip())
    except ValueError:
        return 0.0


def verify_pdf_semantics(pdf_path):
    """
    Verifies that the values in the PDF are arithmetically consistent.
    Returns a list of error messages. If empty, verification passed.
    """
    reader = PdfReader(pdf_path)
    fields = {}

    # Extract all fields from all pages
    for page in reader.pages:
        if '/Annots' in page:
            for annot in page['/Annots']:
                obj = annot.get_object()
                if obj and '/T' in obj and '/V' in obj:
                    key = obj['/T']
                    val = obj['/V']
                    # Handle indirect objects if necessary, usually pypdf
                    # resolves /V string
                    fields[key] = str(val)

    errors = []

    def get_val(key_suffix):
        # Scan for key ending in suffix (since full names are long)
        for k, v in fields.items():
            if k.endswith(key_suffix):
                return parse_currency(v)
        return 0.0

    # --- Page 1 Checks ---

    # --- Page 1 Checks ---

    # 1. Income Components
    wages_1z = get_val("f1_55[0]")  # Line 1z
    interest = get_val("f1_57[0]")  # Line 2b
    ord_divs = get_val("f1_59[0]")  # Line 3b
    qual_divs = get_val("f1_58[0]")  # Line 3a
    cap_gains = get_val("f1_70[0]")  # Line 7
    other_income = get_val("f1_71[0]")  # Line 8
    total_income = get_val("f1_73[0]")  # Line 9

    # Check 1: Qualified <= Ordinary Dividends
    if qual_divs > ord_divs:
        errors.append(
            f"Semantic Error: Qualified Dividends ({qual_divs}) > Ordinary Dividends ({ord_divs})")

    # Check 2: Total Income Sum (Line 9 = 1z + 2b + 3b + 7 + 8)
    calculated_total = wages_1z + interest + ord_divs + cap_gains + other_income
    if abs(calculated_total - total_income) > 1.0:
        errors.append(
            f"Semantic Error: Line 9 Total Income ({total_income}) != Sum of components ({calculated_total})")

    # Check 3: AGI (Line 11)
    # Line 10 (Adjustments) - assuming 0 for MVP
    adjustments = get_val("f1_74[0]")
    agi = get_val("f1_75[0]")  # Line 11

    if abs((total_income - adjustments) - agi) > 1.0:
        errors.append(
            f"Semantic Error: Line 11 AGI ({agi}) != Line 9 ({total_income}) - Line 10 ({adjustments})")

    # --- Page 2 Checks ---

    # Check 4: Taxable Income (Line 15)
    std_deduction = get_val("f2_02[0]")  # Line 12
    taxable_income = get_val("f2_06[0]")  # Line 15

    expected_taxable = max(0.0, agi - std_deduction)
    if abs(taxable_income - expected_taxable) > 1.0:
        errors.append(
            f"Semantic Error: Line 15 Taxable Income ({taxable_income}) != Line 11 ({agi}) - Line 12 ({std_deduction})")

    # Check 5: Total Tax (Line 24)
    tax = get_val("f2_08[0]")  # Line 16
    other_taxes = get_val("f2_15[0]")  # Line 23 (approx)
    total_tax = get_val("f2_16[0]")  # Line 24

    if abs(total_tax - (tax + other_taxes)) > 1.0:
        errors.append(
            f"Semantic Error: Line 24 Total Tax ({total_tax}) != Line 16 ({tax}) + Line 23 ({other_taxes})")

    # Check 6: Total Payments (Line 33)
    withheld = get_val("f2_20[0]")  # Line 25d
    estimated = get_val("f2_21[0]")  # Line 26
    total_payments = get_val("f2_28[0]")  # Line 33

    # Note: Other credits might exist, so Total Payments >= Withheld +
    # Estimated
    if total_payments < (withheld + estimated) - 1.0:
        errors.append(
            f"Semantic Error: Line 33 Total Payments ({total_payments}) < Withheld ({withheld}) + Estimated ({estimated})")

    # Check 7: Amount Owed (Line 37) or Overpaid (Line 34)
    amount_owed = get_val("f2_35[0]")  # Line 37
    overpaid = get_val("f2_30[0]")  # Line 34

    if amount_owed > 0 and overpaid > 0:
        errors.append(
            "Semantic Error: Cannot have both Amount Owed and Overpaid")

    if amount_owed > 0:
        expected_owed = total_tax - total_payments
        if abs(amount_owed - expected_owed) > 1.0:
            errors.append(
                f"Semantic Error: Line 37 Amount Owed ({amount_owed}) != Total Tax ({total_tax}) - Payments ({total_payments})")

    if overpaid > 0:
        expected_overpaid = total_payments - total_tax
        if abs(overpaid - expected_overpaid) > 1.0:
            errors.append(
                f"Semantic Error: Line 34 Overpaid ({overpaid}) != Payments ({total_payments}) - Total Tax ({total_tax})")

    return errors
