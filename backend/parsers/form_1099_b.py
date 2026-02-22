"""
1099-B PDF Parser

Extracts capital gains/losses information from 1099-B forms.
Note: 1099-B forms can be complex with multiple transactions.
This parser extracts summary totals when available.
"""

import re
import pdfplumber


def parse_1099_b(pdf_path: str) -> dict:
    """
    Parse a 1099-B PDF and extract capital gains/losses information.

    Returns a dictionary with the following fields:
    - short_term_proceeds: Total proceeds from short-term transactions
    - short_term_cost_basis: Total cost basis for short-term transactions
    - short_term_gain_loss: Net short-term gain/loss
    - long_term_proceeds: Total proceeds from long-term transactions
    - long_term_cost_basis: Total cost basis for long-term transactions
    - long_term_gain_loss: Net long-term gain/loss
    - federal_tax_withheld: Federal income tax withheld
    - broker_name: Name of the broker
    """
    result = {
        'form_type': '1099-B',
        'short_term_proceeds': 0.0,
        'short_term_cost_basis': 0.0,
        'short_term_gains': 0.0,
        'long_term_proceeds': 0.0,
        'long_term_cost_basis': 0.0,
        'long_term_gains': 0.0,
        'federal_tax_withheld': 0.0,
        'broker_name': '',
        'transactions': [],
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

            # Look for summary sections - these vary widely by broker
            # Try to find short-term and long-term summary lines

            # Pattern for summary amounts (proceeds, cost basis, gain/loss)
            money_pattern = r'[\$]?\s*(-?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'

            # Try to find short-term totals (1099-B or Schedule D)
            short_term_patterns = [
                r'Short[\-\s]?term.*?total[s]?.*?' +
                money_pattern,
                r'Total\s+short[\-\s]?term.*?' +
                money_pattern,
                r'Net\s+short[\-\s]?term\s+capital\s+gain\s+or\s+\(loss\).*?' +
                money_pattern,
            ]

            long_term_patterns = [
                r'Long[\-\s]?term.*?total[s]?.*?' +
                money_pattern,
                r'Total\s+long[\-\s]?term.*?' +
                money_pattern,
                r'Net\s+long[\-\s]?term\s+capital\s+gain\s+or\s+\(loss\).*?' +
                money_pattern,
            ]

            # Try to find gain/loss amounts
            for pattern in short_term_patterns:
                matches = re.findall(
                    pattern, full_text, re.IGNORECASE | re.DOTALL)
                if matches:
                    # Take the last match as it's likely the gain/loss
                    value_str = matches[-1].replace(',', '').replace('$', '')
                    try:
                        result['short_term_gains'] = float(value_str)
                    except ValueError:
                        pass
                    break

            for pattern in long_term_patterns:
                matches = re.findall(
                    pattern, full_text, re.IGNORECASE | re.DOTALL)
                if matches:
                    value_str = matches[-1].replace(',', '').replace(
                        '$', '').replace('(', '-').replace(')', '')
                    try:
                        result['long_term_gains'] = float(value_str)
                    except ValueError:
                        pass
                    break

            # Look for federal tax withheld
            withheld_pattern = r'(?:Federal\s*(?:income\s*)?tax\s*withheld|Box\s*4)[^\d]*' + money_pattern
            withheld_match = re.search(
                withheld_pattern, full_text, re.IGNORECASE)
            if withheld_match:
                value_str = withheld_match.group(1).replace(',', '')
                result['federal_tax_withheld'] = float(value_str)

            # Try to extract broker name
            broker_pattern = r'(?:PAYER.S?\s*name|Broker)[^\n]*\n([A-Z][A-Za-z0-9\s,\.]+)'
            broker_match = re.search(broker_pattern, full_text, re.IGNORECASE)
            if broker_match:
                result['broker_name'] = broker_match.group(1).strip()[:100]

            # Set confidence - 1099-B is complex, so we're more conservative
            has_short = result['short_term_gains'] != 0
            has_long = result['long_term_gains'] != 0

            if has_short or has_long:
                result['parse_confidence'] = 'medium'
            else:
                result['parse_confidence'] = 'low'

    except Exception as e:
        result['error'] = str(e)
        result['parse_confidence'] = 'failed'

    return result
