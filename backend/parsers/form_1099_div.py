"""
1099-DIV PDF Parser

Extracts dividend income information from 1099-DIV forms.
"""

import re
import pdfplumber
from .utils import extract_payer_from_fields, extract_payer_name_from_text


def parse_1099_div(pdf_path: str) -> dict:
    """
    Parse a 1099-DIV PDF and extract relevant tax information.
    
    Returns a dictionary with the following fields:
    - total_ordinary_dividends: Box 1a - Total ordinary dividends
    - qualified_dividends: Box 1b - Qualified dividends
    - total_capital_gain_dist: Box 2a - Total capital gain distributions
    - federal_tax_withheld: Box 4 - Federal income tax withheld
    - payer_name: Name of the payer
    """
    result = {
        'form_type': '1099-DIV',
        'total_ordinary_dividends': 0.0,
        'qualified_dividends': 0.0,
        'total_capital_gain_dist': 0.0,
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
                'total_ordinary_dividends': [
                    r'(?:Box\s*1a|1a\s+Total\s*ordinary)[^\d]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                    r'Total\s*ordinary\s*dividends[^\d]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                ],
                'qualified_dividends': [
                    r'(?:Box\s*1b|1b\s+Qualified)[^\d]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                    r'Qualified\s*dividends[^\d]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                ],
                'total_capital_gain_dist': [
                    r'(?:Box\s*2a|2a\s+Total\s*capital)[^\d]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                    r'Total\s*capital\s*gain\s*dist[^\d]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
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
            
            if fields_found >= 3:
                result['parse_confidence'] = 'high'
            elif fields_found >= 1:
                result['parse_confidence'] = 'medium'
            else:
                result['parse_confidence'] = 'low'
                
    except Exception as e:
        result['error'] = str(e)
        result['parse_confidence'] = 'failed'
    
    return result
