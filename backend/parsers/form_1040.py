"""
Form 1040 PDF Parser

Extracts key information from Form 1040 to validate calculations or capture summary data.
Specifically targets:
- Wages (Line 1z) - for cross-comparison
- Total Tax (Line 24) - for validation
- Federal Income Tax Withheld (Line 25d) - total
- Estimated Tax Payments (Line 26)
- Other Payments/Refundable Credits (Line 27-31 summary)
- Amount You Owe (Line 37)
"""

import re
import pdfplumber


def parse_form_1040(pdf_path: str) -> dict:
    """
    Parse a Form 1040 PDF and extract key fields.

    Returns a dictionary with extracted fields.
    """
    result = {
        'form_type': 'Form 1040',
        'wages': 0.0,
        'total_tax': 0.0,
        'federal_withheld': 0.0,
        'estimated_tax_payments': 0.0,
        'other_withholding': 0.0,
        'amount_owed': 0.0,
        'parse_confidence': 'low',
        'raw_text': '',
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ''
            for page in pdf.pages:
                text = page.extract_text() or ''
                full_text += text + '\n'

            result['raw_text'] = full_text

            # Helper to extract money
            def extract_money(pattern, text):
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    val_str = match.group(1).replace(',', '').replace(
                        '$', '').replace('(', '-').replace(')', '')
                    try:
                        return float(val_str)
                    except ValueError:
                        return 0.0
                return 0.0

            money_pattern = r'[\$]?\s*(-?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'

            # 2024 Form 1040 Patterns

            # Line 1z: Wages, salaries, tips, etc.
            # "1z Add lines 1a through 1h... 1z 886,551."
            # OR "1z" ... amount
            result['wages'] = extract_money(
                r'1z\s.*?' + money_pattern, full_text)

            # Line 24: Total Tax. "24 Add lines 22 and 23... 24 310,221."
            result['total_tax'] = extract_money(
                r'24\s+Add\s+lines\s+22\s+and\s+23.*?' + money_pattern, full_text)

            # Line 25d: Total Federal Withholding
            # "25d Add lines 25a through 25c... 277,103."
            result['federal_withheld'] = extract_money(
                r'25d\s+Add\s+lines\s+25a\s+through\s+25c.*?' + money_pattern, full_text)

            # Line 26: 2024 estimated tax payments and amount applied from 2023
            # return
            result['estimated_tax_payments'] = extract_money(
                r'26\s+2024\s+estimated\s+tax\s+payments.*?' + money_pattern, full_text)

            # Line 25c: Other forms
            # This is tricky because it's usually inside the block 25.
            # "25c Other forms (see instructions)..."
            match_25c = re.search(
                r'25c\s+Other\s+forms.*?' +
                money_pattern,
                full_text)
            if match_25c:
                result['other_withholding'] = float(
                    match_25c.group(1).replace(
                        ',', '').replace(
                        '$', ''))

            # Line 37: Amount you owe
            result['amount_owed'] = extract_money(
                r'37\s+Amount\s+you\s+owe.*?' + money_pattern, full_text)

            # Confidence check
            # If we found Total Tax or Amount Owed, fairly confident it's a
            # 1040
            if result['total_tax'] > 0 or result['amount_owed'] > 0 or result['federal_withheld'] > 0:
                result['parse_confidence'] = 'medium'

            # Special logic for "other_withholding" to be generic "Additional"
            # If we explicitly found estimated payments, great.
            # If we found 25d (Total Withheld) and we know W-2 withheld from other parsers...
            # The aggregation logic in main.py will sum them.
            # BUT 1040 Line 25d INCLUDES W-2 Line 25a.
            # If main.py sums W-2 parser (Line 25a) AND 1040 parser (Line 25d),
            # WE DOUBLE COUNT!

            # CRITICAL: 1040 Parser should ONLY return the DELTA (Other + Estimated) or
            # main.py needs to handle 1040 specially.

            # Since main.py sums everything, 1040 parser should NOT return "federal_withheld" (Line 25d)!
            # It should only return "estimated_tax_payments" (Line 26) and "other_withholding" (Line 25c).
            # Line 25a is W-2. Line 25b is 1099. We have parsers for those.

            # So I will RESET 'federal_withheld' in the result to Avoid Double Counting,
            # OR map Line 25d to a variable that is used for Validation only.

            # Let's keep it in result but name it 'validation_total_withheld'
            # so it doesn't get summed into 'w2_federal_withheld'
            result['validation_total_withheld'] = result.pop(
                'federal_withheld')
            result['validation_total_tax'] = result.pop('total_tax')

            # 'other_withholding' (25c) and 'estimated_tax_payments' (26) are additive to W-2/1099 parsers.
            # So we keep them.

    except Exception as e:
        result['error'] = str(e)
        result['parse_confidence'] = 'failed'

    return result
