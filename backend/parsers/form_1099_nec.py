"""
1099-NEC PDF Parser

Extracts nonemployee compensation from 1099-NEC forms.
"""

import re
import pdfplumber
from .utils import extract_payer_from_fields, extract_payer_name_from_text


def parse_1099_nec(pdf_path: str) -> dict:
    """
    Parse a 1099-NEC PDF and extract nonemployee compensation.

    Returns a dictionary with the following fields:
    - nonemployee_compensation: Box 1 - Nonemployee compensation
    - federal_tax_withheld: Box 4 - Federal income tax withheld
    - payer_name: Name of the payer
    """
    result = {
        'form_type': '1099-NEC',
        'nonemployee_compensation': 0.0,
        'federal_tax_withheld': 0.0,
        'payer_name': '',
        'raw_text': '',
        'parse_confidence': 'low',
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ''
            for page in pdf.pages:
                text = page.extract_text() or ''
                full_text += text + '\n'

            result['raw_text'] = full_text

            patterns = {
                'nonemployee_compensation': [
                    r'(?:Box\s*1|1\s+Nonemployee\s*compensation)[^\d]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                    r'Nonemployee\s*compensation[^\d]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                    r'NEC[^\d]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                ],
                'federal_tax_withheld': [
                    r'(?:Box\s*4|4\s+Federal\s*income\s*tax)[^\d]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                ],
            }

            fields_found = 0
            for field, pattern_list in patterns.items():
                for pattern in pattern_list:
                    match = re.search(pattern, full_text, re.IGNORECASE)
                    if match:
                        value_str = match.group(1).replace(',', '')
                        result[field] = float(value_str)
                        fields_found += 1
                        break

            # Try to extract payer name: first from form fields, then text
            result['payer_name'] = extract_payer_from_fields(pdf)
            if not result['payer_name']:
                result['payer_name'] = extract_payer_name_from_text(full_text)

            if result['nonemployee_compensation'] > 0:
                result['parse_confidence'] = 'high'
            elif fields_found >= 1:
                result['parse_confidence'] = 'medium'
            else:
                result['parse_confidence'] = 'low'

    except Exception as e:
        result['error'] = str(e)
        result['parse_confidence'] = 'failed'

    return result
