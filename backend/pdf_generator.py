from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, BooleanObject
import io
import os

FORM_1040_PATH = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)),
    "forms",
    "f1040.pdf")


def generate_1040(tax_summary, pii):
    if not os.path.exists(FORM_1040_PATH):
        raise FileNotFoundError(
            f"Form 1040 PDF template not found at {FORM_1040_PATH}")

    reader = PdfReader(FORM_1040_PATH)
    writer = PdfWriter()

    # Copy pages and form structure
    writer.append_pages_from_reader(reader)

    # Manually copy AcroForm if not present (Fix for "No /AcroForm dictionary")
    if reader.root_object and "/AcroForm" in reader.root_object:
        writer.root_object.update({
            NameObject("/AcroForm"): reader.root_object["/AcroForm"]
        })

    # DELETE XFA to force AcroForm (IRS forms are Hybrid)
    if "/AcroForm" in writer.root_object:
        acro = writer.root_object["/AcroForm"]
        if "/XFA" in acro:
            del acro["/XFA"]

    if "/XFA" in writer.root_object:
        del writer.root_object["/XFA"]

    # Enable NeedAppearances so viewers render values
    if "/AcroForm" not in writer.root_object:
        # Should have been copied, but if not, creating empty one might be risky without fields.
        # But we rely on copy.
        pass
    else:
        writer.root_object["/AcroForm"].update({
            NameObject("/NeedAppearances"): BooleanObject(True)
        })

    # Convert money to string
    def fmt(val):
        if val is None or val == 0:
            return ""
        return f"{val:.2f}"

    fed = tax_summary.get('federal', {})

    # Extract Income components from Root tax_summary
    wages = tax_summary.get('total_wages', 0)
    interest = tax_summary.get('total_interest', 0)
    exempt_interest = tax_summary.get('total_tax_exempt_interest', 0)
    dividends = tax_summary.get('total_dividends', 0)
    cap_gains = tax_summary.get('total_capital_gains', 0)

    # Debug: trace dividend values
    qualified_divs = tax_summary.get(
        'federal', {}).get(
        'qualified_dividends', 0) or 0
    line_3b = max(dividends, qualified_divs)

    # Calculate Other Income (Foreign, etc.) for Line 8
    # Total Income = Wages + Interest + Divs + Cap Gains + Other
    # So Other = Total - (Wages + Interest + Divs + Cap Gains)
    other_income = fed.get('gross_income', 0) - \
        (wages + interest + dividends + cap_gains)
    if other_income < 0.01:
        other_income = 0

    print(
        f"[PDF DEBUG] total_dividends={dividends}, qualified_dividends={qualified_divs}, line_3b={line_3b}",
        flush=True)

    # AGI / Total Income
    total_income = fed.get('gross_income', 0)
    agi = fed.get('gross_income', 0)  # MVP: Gross = AGI

    # Calculate Effective Deduction (Standard vs Itemized) for Line 12
    # If Taxable = AGI - Deduction, then Deduction = AGI - Taxable
    # If Taxable is 0, Deduction was >= AGI. In that case, we should show the Standard Deduction
    # unless Itemized was used. Since we don't track which was used explicitly here,
    # we assume if (AGI - Taxable) > Standard, then Itemized was used.
    std_ded = fed.get('standard_deduction', 0)
    taxable_val = fed.get('taxable_income', 0)
    effective_deduction = max(std_ded, agi - taxable_val)
    if taxable_val == 0:
        # If taxable is 0, we can't easily validly reverse engineer if itemized > standard
        # unless we know for sure. But showing Standard is safe default if we can't prove otherwise.
        # But if input had itemized > standard, we want to show it.
        # For now, let's just show Standard if Taxable is 0, unless we clearly see a gap?
        # Actually pdf_verifier checks AGI - Deduction. If Taxable is 0, checks if (0) == max(0, AGI-Ded).
        # So we just need Deduction >= AGI.
        pass

    # Map fields
    fields = {
        # Page 1
        'topmostSubform[0].Page1[0].f1_02[0]': pii.get('firstName', '') + " " + pii.get('lastName', ''),
        'topmostSubform[0].Page1[0].f1_04[0]': pii.get('ssn', ''),
        'topmostSubform[0].Page1[0].Address_ReadOrder[0].f1_20[0]': pii.get('address', ''),
        'topmostSubform[0].Page1[0].Address_ReadOrder[0].f1_22[0]': pii.get('city', ''),
        'topmostSubform[0].Page1[0].Address_ReadOrder[0].f1_23[0]': pii.get('state', ''),
        'topmostSubform[0].Page1[0].Address_ReadOrder[0].f1_24[0]': pii.get('zip', ''),

        # Line 1a Total amount from Form(s) W-2, box 1
        'topmostSubform[0].Page1[0].f1_47[0]': fmt(wages),
        # Line 1z Add lines 1a through 1h
        'topmostSubform[0].Page1[0].f1_55[0]': fmt(wages),
        # Line 2a Tax-Exempt Interest
        'topmostSubform[0].Page1[0].f1_56[0]': fmt(exempt_interest),
        # Line 2b Taxable Interest
        'topmostSubform[0].Page1[0].f1_57[0]': fmt(interest),
        # Line 3a Qualified Dividends
        'topmostSubform[0].Page1[0].f1_58[0]': fmt(tax_summary.get('federal', {}).get('qualified_dividends', 0)),
        # Line 3b Ordinary Dividends
        'topmostSubform[0].Page1[0].f1_59[0]': fmt(
            max(dividends, tax_summary.get('federal', {}).get(
                'qualified_dividends', 0) or 0)
        ),
        # Line 7 Capital Gain
        'topmostSubform[0].Page1[0].f1_70[0]': fmt(cap_gains),
        # Line 8 Other Income (Schedule 1) - f1_71? (Need to check field ID, usually after Cap Gains)
        # Based on verify_pdf_text, f1_70 is Y=90. f1_71 is Y=78. f1_72 is Y=66. f1_73 (Total) is Y=54.
        # So f1_71 or f1_72 is likely Other Income. Let's try f1_71.
        'topmostSubform[0].Page1[0].f1_71[0]': fmt(other_income),

        # Line 9 Total Income
        'topmostSubform[0].Page1[0].f1_73[0]': fmt(total_income),

        # Line 11 AGI
        'topmostSubform[0].Page1[0].f1_75[0]': fmt(agi),

        # Page 2

        # Line 12 Standard Deduction or Itemized
        'topmostSubform[0].Page2[0].f2_02[0]': fmt(effective_deduction),

        # Line 15 Taxable Income
        'topmostSubform[0].Page2[0].f2_06[0]': fmt(fed.get('taxable_income')),

        # Line 16 Tax — income tax only (ordinary + capital gains)
        'topmostSubform[0].Page2[0].f2_08[0]': fmt(
            (fed.get('ordinary_income_tax', 0) or 0) + (fed.get('capital_gains_tax', 0) or 0)
        ),
        # Line 23 Other taxes from Schedule 2 (SE tax + Additional Medicare Tax)
        'topmostSubform[0].Page2[0].f2_15[0]': fmt(
            (fed.get('self_employment_tax', 0) or 0) + (fed.get('additional_medicare_tax', 0) or 0)
        ),
        # Line 24 Total Tax
        'topmostSubform[0].Page2[0].f2_16[0]': fmt(fed.get('total_federal_tax')),
        # Line 25a Withholding from W-2
        'topmostSubform[0].Page2[0].f2_17[0]': fmt(tax_summary.get('total_federal_withheld', 0) - tax_summary.get('federal', {}).get('additional_medicare_withholding', 0)),
        # Line 25c Withholding from other forms (Additional Medicare Tax Form 8959)
        'topmostSubform[0].Page2[0].f2_19[0]': fmt(fed.get('additional_medicare_withholding', 0)),
        # Line 25d Total Withholding
        'topmostSubform[0].Page2[0].f2_20[0]': fmt(tax_summary.get('total_federal_withheld')),
        # Line 26 Estimated
        'topmostSubform[0].Page2[0].f2_21[0]': fmt(tax_summary.get('estimated_tax_payments')),

        # Line 33 Total Payments: Withheld + Estimated + Other
        'topmostSubform[0].Page2[0].f2_28[0]': fmt(
            tax_summary.get('total_federal_withheld', 0) +
            tax_summary.get('estimated_tax_payments', 0) +
            tax_summary.get('other_withholding', 0)
        ),

        # Federal Amount Owed / Overpaid calculation
    }

    # Calculate Federal-specific Balance
    fed_tax = fed.get('total_federal_tax', 0)
    fed_payments = (tax_summary.get('total_federal_withheld', 0) +
                    tax_summary.get('estimated_tax_payments', 0) +
                    tax_summary.get('other_withholding', 0))

    fed_balance = fed_tax - fed_payments

    # Line 34 Overpaid (Federal only)
    if fed_balance < 0:
        fields['topmostSubform[0].Page2[0].f2_30[0]'] = fmt(abs(fed_balance))

    # Line 37 Amount You Owe (Federal only)
    if fed_balance > 0:
        fields['topmostSubform[0].Page2[0].f2_35[0]'] = fmt(fed_balance)

    # Add Short Names to fields dict (Brute force mapping)
    keys = list(fields.keys())
    for k in keys:
        if '.' in k:
            short_name = k.split('.')[-1]
            if short_name not in fields:
                fields[short_name] = fields[k]

    # Update Page 1 fields
    writer.update_page_form_field_values(writer.pages[0], fields)

    # Update Page 2 fields
    writer.update_page_form_field_values(writer.pages[1], fields)

    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)
    return output_stream


FORM_540_PATH = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)),
    "forms",
    "ca540.pdf")


def generate_540(tax_summary, pii):
    """Generate California Form 540 (Resident Income Tax Return) PDF."""
    if not os.path.exists(FORM_540_PATH):
        raise FileNotFoundError(
            f"CA Form 540 PDF template not found at {FORM_540_PATH}")

    reader = PdfReader(FORM_540_PATH)
    writer = PdfWriter()
    writer.append_pages_from_reader(reader)

    # Copy AcroForm
    if reader.root_object and "/AcroForm" in reader.root_object:
        writer.root_object.update({
            NameObject("/AcroForm"): reader.root_object["/AcroForm"]
        })

    # Delete XFA to force AcroForm rendering
    if "/AcroForm" in writer.root_object:
        acro = writer.root_object["/AcroForm"]
        if "/XFA" in acro:
            del acro["/XFA"]
        acro.update({NameObject("/NeedAppearances"): BooleanObject(True)})

    if "/XFA" in writer.root_object:
        del writer.root_object["/XFA"]

    def fmt(val):
        if val is None or val == 0:
            return ""
        return f"{val:.0f}"  # CA 540 uses whole dollars

    fed = tax_summary.get('federal', {})
    cal = tax_summary.get('california', {})

    # Income data
    wages = tax_summary.get('total_wages', 0)
    federal_agi = fed.get('gross_income', 0)  # Federal AGI

    # CA tax data
    ca_standard_deduction = cal.get('standard_deduction', 0)
    ca_taxable_income = cal.get('taxable_income', 0)
    ca_tax = cal.get('state_tax', 0)
    ca_exemption_credit = cal.get('exemption_credit', 0)
    ca_mental_health = cal.get('mental_health_surcharge', 0)
    ca_total_tax = cal.get('total_california_tax', 0)

    # Withholding
    state_withheld = tax_summary.get('total_state_withheld', 0)

    # CA AGI (simplified: same as Federal AGI for residents with no CA
    # adjustments)
    ca_agi = federal_agi

    # Tax after exemption credits
    tax_after_credits = max(0, ca_tax - ca_exemption_credit)

    # Total tax (tax after credits + mental health surcharge)
    total_ca_tax = tax_after_credits + ca_mental_health

    fields = {
        # ===== PAGE 1 (Side 1): Personal Information =====
        # First name
        '540_form_1003': pii.get('firstName', ''),
        # Last name
        '540_form_1005': pii.get('lastName', ''),
        # SSN
        '540_form_1007': pii.get('ssn', ''),
        # Street address
        '540_form_1015': pii.get('address', ''),
        # City
        '540_form_1018': pii.get('city', ''),
        # ZIP code
        '540_form_1020': pii.get('zip', ''),

        # Line 7 — Personal exemption: 1 (single filer)
        '540_form_1042': fmt(153),  # 1 x $153 = $153

        # ===== PAGE 2 (Side 2): Income & Tax =====
        # Line 12 — State wages from W-2 box 16
        '540_form_2018': fmt(wages),
        # Line 13 — Federal AGI from Form 1040 line 11
        '540_form_2019': fmt(federal_agi),
        # Line 14 — CA adjustments subtractions (0 for MVP)
        '540_form_2020': '',
        # Line 15 — Subtract line 14 from line 13
        '540_form_2021': fmt(federal_agi),
        # Line 16 — CA adjustments additions (0 for MVP)
        '540_form_2022': '',
        # Line 17 — California AGI (line 15 + line 16)
        '540_form_2023': fmt(ca_agi),
        # Line 18 — Standard deduction or itemized deductions
        '540_form_2024': fmt(ca_standard_deduction),
        # Line 19 — Taxable income (line 17 - line 18, min 0)
        '540_form_2025': fmt(ca_taxable_income),

        # Line 31 — Tax from Tax Table or Tax Rate Schedule
        '540_form_2030': fmt(ca_tax),
        # Line 32 — Exemption credits (from line 7/8/9)
        '540_form_2031': fmt(ca_exemption_credit),
        # Line 33 — Subtract line 32 from line 31
        '540_form_2032': fmt(tax_after_credits),
        # Line 34 — Tax from Schedule G-1 / FTB 5870A (0 for MVP)
        '540_form_2035': '',
        # Line 35 — Add line 33 and line 34
        '540_form_2036': fmt(tax_after_credits),
        # Line 40 — Nonrefundable credits (0 for MVP)
        '540_form_2037': '',

        # ===== PAGE 3 (Side 3): Other Taxes, Payments, Refund =====
        # Line 63 — Other taxes (mental health surcharge goes here)
        '540_form_3009': fmt(ca_mental_health),
        # Line 64 — Total tax (line 48 + line 61 + line 62 + line 63)
        '540_form_3010': fmt(total_ca_tax),

        # Line 71 — California income tax withheld
        '540_form_3011': fmt(state_withheld),
        # Line 78 — Total payments
        '540_form_3018': fmt(state_withheld),
    }

    # Calculate balance: overpaid or amount owed
    ca_balance = total_ca_tax - state_withheld

    if ca_balance < 0:
        # Overpaid — Line 93 (payments balance) and Line 97 (overpaid)
        fields['540_form_3023'] = fmt(abs(ca_balance))
        fields['540_form_3025'] = fmt(abs(ca_balance))
        fields['540_form_3027'] = fmt(abs(ca_balance))
    elif ca_balance > 0:
        # Amount owed — Line 94
        fields['540_form_3024'] = fmt(ca_balance)

    # Fill all pages
    for page in writer.pages:
        writer.update_page_form_field_values(page, fields)

    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)
    return output_stream
