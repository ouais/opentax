"""
W-2 PDF Parser

Extracts key wage and tax information from W-2 forms.
Optimized for standard W-2 PDF formats including Google's format.
"""

import re
import pdfplumber
from .utils import extract_payer_from_fields, extract_payer_name_from_text, looks_like_address, clean_name


def extract_value_from_cell(cell_text: str) -> float:
    """
    Extract the numeric value from a W-2 table cell.
    Cells are typically formatted as "BoxLabel\\nValue" or just "Value".
    """
    if not cell_text:
        return 0.0

    # Split by newline and take the last numeric part
    parts = cell_text.strip().split('\n')

    for part in reversed(parts):
        # Look for dollar amounts - handle both comma-separated and non-comma formats
        # Pattern matches: 687835.81 or 687,835.81 or $687,835.81
        # First try to find numbers with optional commas and decimals
        match = re.search(r'[\$]?\s*(\d[\d,]*(?:\.\d{2})?)', part)
        if match:
            try:
                value_str = match.group(1).replace(',', '')
                value = float(value_str)
                # Only return if it looks like a reasonable dollar amount (> 0)
                if value > 0:
                    return value
            except ValueError:
                pass

    return 0.0


def parse_w2_tables(pdf) -> dict:
    """
    Extract W-2 data from table cells.
    Standard W-2 table cells contain "BoxLabel\\nValue" format.
    """
    result = {}

    for page in pdf.pages:
        tables = page.extract_tables()

        for table in tables:
            if not table:
                continue

            for row in table:
                if not row:
                    continue

                for cell in row:
                    if not cell:
                        continue

                    cell_lower = cell.lower()
                    value = extract_value_from_cell(cell)
                    print(f"DEBUG: Cell: {repr(cell_lower)} / Val: {value}")

                    # Box 1: Wages, tips, other compensation
                    if ('1wages' in cell_lower or 'wages, tips' in cell_lower or
                            'wages,tips' in cell_lower or 'other compensation' in cell_lower):
                        if value > 0 and 'wages' not in result:
                            result['wages'] = value

                    # Box 2: Federal income tax withheld
                    elif ('2federal' in cell_lower or
                          ('federal' in cell_lower and 'withheld' in cell_lower)):
                        if value > 0 and 'federal_tax_withheld' not in result:
                            result['federal_tax_withheld'] = value

                    # Box 3: Social security wages
                    elif ('3social' in cell_lower or
                          ('social security wages' in cell_lower)):
                        if value > 0 and 'social_security_wages' not in result:
                            result['social_security_wages'] = value

                    # Box 4: Social security tax withheld
                    elif ('4social' in cell_lower or
                          ('social security tax' in cell_lower and 'withheld' in cell_lower)):
                        if value > 0 and 'social_security_tax_withheld' not in result:
                            result['social_security_tax_withheld'] = value

                    if 'medicare' in cell_lower and value > 0:
                        print(
                            f"DEBUG: Medicare keyword found with value {value}. Checking type...")

                        # Determine if this is Wages (Box 5) or Tax (Box 6)
                        # STRICT MATCHING: A cell cannot be both.
                        # Prioritize TAX because "tax" is a strong signal.

                        is_tax = (
                            'tax' in cell_lower or 'withheld' in cell_lower or 'box 6' in cell_lower)
                        # Only check for '6' if we don't have conflicting
                        # signals
                        if not is_tax and '6' in cell_lower and 'wages' not in cell_lower:
                            is_tax = True

                        is_wages = (
                            'wages' in cell_lower or 'tips' in cell_lower or 'box 5' in cell_lower)
                        # Only check for '5' if we don't have conflicting
                        # signals and it's not tax
                        if not is_wages and not is_tax and '5' in cell_lower and 'tax' not in cell_lower:
                            is_wages = True

                        # Tie-breaker: If both matched (unlikely with above
                        # logic), prioritize label content
                        if is_tax and is_wages:
                            if 'tax' in cell_lower:
                                is_wages = False
                            elif 'wages' in cell_lower:
                                is_tax = False

                        if is_tax:
                            print(
                                f"DEBUG: MATCHED Medicare Tax (Final): {value}")
                            if 'medicare_tax_withheld' not in result:
                                result['medicare_tax_withheld'] = value

                        elif is_wages:  # ELF - only if not tax
                            print(
                                f"DEBUG: MATCHED Medicare Wages (Final): {value}")
                            if 'medicare_wages' not in result:
                                result['medicare_wages'] = value

                    # Box 5: Medicare wages and tips (Legacy/Fallback)
                    # Loop validation ensures we don't overwrite if already found?
                    # Actually, the above block handles it. We can remove the
                    # old complex block.

                    # Box 16: State wages
                    elif ('16state' in cell_lower or 'state wages' in cell_lower):
                        if value > 0 and 'state_wages' not in result:
                            result['state_wages'] = value

                    # Box 17: State income tax
                    elif ('17state' in cell_lower or 'state income tax' in cell_lower):
                        if value > 0 and 'state_tax_withheld' not in result:
                            result['state_tax_withheld'] = value

                    # Box 14/19: CASDI/SDI (California State Disability
                    # Insurance)
                    elif ('casdi' in cell_lower or 'sdi' in cell_lower or
                          'state disability' in cell_lower or 'ca sdi' in cell_lower or
                          '19local' in cell_lower or 'local tax' in cell_lower):
                        if value > 0 and 'casdi' not in result:
                            result['casdi'] = value

                    # Employer name
                    elif "employer's name" in cell_lower or 'cemployer' in cell_lower:
                        lines = cell.split('\n')
                        for line in lines[1:]:  # Skip the label line
                            line = line.strip()
                            if line:
                                cleaned = clean_name(line)
                                if cleaned:
                                    if 'employer_name' not in result:
                                        result['employer_name'] = cleaned
                                        break

    return result


def parse_w2(pdf_path: str) -> dict:
    """
    Parse a W-2 PDF and extract relevant tax information.
    """
    result = {
        'form_type': 'W-2',
        'wages': 0.0,
        'federal_tax_withheld': 0.0,
        'social_security_wages': 0.0,
        'social_security_tax_withheld': 0.0,
        'medicare_wages': 0.0,
        'medicare_tax_withheld': 0.0,
        'state_wages': 0.0,
        'state_tax_withheld': 0.0,
        'casdi': 0.0,  # California State Disability Insurance (Box 14/19)
        'employer_name': '',
        'raw_text': '',
        'parse_confidence': 'low',
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Get full text for reference
            full_text = ''
            for page in pdf.pages:
                text = page.extract_text() or ''
                full_text += text + '\n'

            result['raw_text'] = full_text

            # Verify this is a W-2
            if 'w-2' not in full_text.lower() and 'w2' not in full_text.lower():
                result['parse_confidence'] = 'low'
                return result

            # Parse using table extraction (most reliable for standard W-2s)
            table_data = parse_w2_tables(pdf)

            # Apply parsed values
            for field in [
                'wages',
                'federal_tax_withheld',
                'social_security_wages',
                'social_security_tax_withheld',
                'medicare_wages',
                'medicare_tax_withheld',
                'state_wages',
                'state_tax_withheld',
                'casdi',
                    'employer_name']:
                if field in table_data:
                    result[field] = table_data[field]

            # Fallback for employer name if not found in tables
            if not result['employer_name']:
                result['employer_name'] = extract_payer_from_fields(pdf)

            if not result['employer_name']:
                # Look for 'Employer...' or 'Employer's name...'
                result['employer_name'] = extract_payer_name_from_text(
                    full_text,
                    label_pattern=r'(?:Employer.s?\s*name|Employer.s?\s*address|Employer\s*name)')

            # Calculate confidence based on fields found
            fields_found = sum(
                1 for f in [
                    'wages',
                    'federal_tax_withheld',
                    'social_security_wages',
                    'medicare_wages',
                    'state_wages',
                    'state_tax_withheld'] if result.get(
                    f,
                    0) > 0)

            if fields_found >= 5:
                result['parse_confidence'] = 'high'
            elif fields_found >= 3:
                result['parse_confidence'] = 'medium'
            elif fields_found >= 1:
                result['parse_confidence'] = 'low'
            else:
                result['parse_confidence'] = 'failed'

    except Exception as e:
        result['error'] = str(e)
        result['parse_confidence'] = 'failed'

    return result
