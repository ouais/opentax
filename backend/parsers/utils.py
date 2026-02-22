
from .payer_db import get_payer_score
import re

# Known PDF field labels that should never be accepted as institution names
# Validated against actual IRS forms (1099-INT, DIV, NEC, W-2)
FIELD_LABELS = [
    'name line', 'street address', 'city or town', 'state or province',
    'zip code', 'postal code', 'country', 'phone', 'fax', 'tin',
    'taxpayer', 'identification', 'recipient', 'recipient\'s', 'account', 'facta',
    'fatca', 'form 1099', 'corrected', 'void', 'omb no', 'copy',
    'department of', 'internal revenue', 'payer', 'borrower',
    'box ', 'interest income', 'federal income', 'early withdrawal',
    'u.s. savings', 'foreign tax', 'tax-exempt', 'specified private',
    'market discount', 'bond premium', 'investment expenses',
    'employer', 'address', 'employee', 'control number',
    'social security', 'medicare', 'w-2', 'tax year', 'calendar year',
    'tax form', 'statement', 'financial institution', 'transcript',
]

# US state abbreviations for address detection
STATE_ABBREVS = {
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC',
}


# Common street suffixes to detect addresses
STREET_SUFFIXES = [
    'rd', 'road', 'st', 'street', 'ave', 'avenue', 'blvd', 'boulevard',
    'ln', 'lane', 'dr', 'drive', 'way', 'ct', 'court', 'pl', 'place',
    'cir', 'circle', 'pk', 'pike', 'pkwy', 'parkway', 'ste', 'suite',
    'hwy', 'highway', 'box', 'po box'
]


def looks_like_address(text: str) -> bool:
    """Return True if text looks like a street address or city/state/zip line."""
    stripped = text.strip()
    lower = stripped.lower()
    if not stripped:
        return True

    # Starts with digits (street number) — e.g. "123 Main St"
    if re.match(r'^\d+\s', stripped):
        return True

    # Contains P.O. Box, Suite, Floor, Apt
    if re.search(
        r'\b(?:P\.?O\.?\s*Box|Suite|Ste\.?|Floor|Fl\.?|Apt\.?|Unit)\b',
        stripped,
            re.IGNORECASE):
        return True

    # Contains street suffix (e.g. "Washington Blvd")
    # Check if any word is a street suffix
    words = re.split(r'[ ,.]+', lower)
    if any(w in STREET_SUFFIXES for w in words):
        # To be safe, require at least one digit in the string OR it matches
        # specific pattern
        if any(c.isdigit() for c in stripped):
            return True
        # Or if it ends with a suffix and has multiple words
        if len(words) > 2 and words[-1] in STREET_SUFFIXES:
            return True

    # City, STATE ZIP pattern — e.g. "San Francisco, CA 94102"
    if re.search(r',\s*[A-Z]{2}\s+\d{5}', stripped):
        return True

    # Ends with a zip code
    if re.search(r'\b\d{5}(?:-\d{4})?\s*$', stripped):
        return True

    # Contains just a state abbreviation with comma — e.g. "Boston, MA"
    words = stripped.replace(',', ' ').split()
    if any(w.upper() in STATE_ABBREVS for w in words if len(w) == 2):
        # Only flag if it also has a comma (city, state pattern)
        if ',' in stripped:
            return True

    # Phone numbers
    if re.search(
        r'(?:phone|tel|fax|cell).*[\d\-]{7,}',
        stripped,
            re.IGNORECASE):
        return True

    # Emails or URLs
    if re.search(
        r'@[\w\.-]+|\.com\b|\.org\b|\.net\b',
        stripped,
            re.IGNORECASE):
        return True

    return False


def clean_name(name: str) -> str:
    """Return the name if it looks like a real institution, or empty string."""
    stripped = name.strip()
    if not stripped or len(stripped) < 2:
        return ''
    lower = stripped.lower()

    # Reject if it starts with "City:", "State:", "Zip:", etc.
    if re.match(
        r'^(?:City|State|Zip|Address|Street)\s*:',
        stripped,
            re.IGNORECASE):
        return ''

    # Try to strip common Name/Payer prefixes if they exist with a value
    # e.g. "Name Line 1: Vanguard" -> "Vanguard"
    match = re.match(
        r'^(?:Name\s*Line\s*\d+|Payer(?:\'?s)?(?:\s*Name)?|Employer(?:\'?s)?(?:\s*Name)?|Recipient(?:\'?s)?(?:\s*Name)?)\s*[:.]?\s*(.+)',
        stripped,
        re.IGNORECASE)
    if match:
        potential_value = match.group(1).strip()
        if potential_value:
            stripped = potential_value
            lower = stripped.lower()

    # Reject if it matches a known field label
    # Use word boundary check for short labels to avoid false positives (e.g.
    # 'tin' in 'Marketing')
    for label in FIELD_LABELS:
        if len(label) <= 4:
            # Short labels must match as whole words
            if re.search(r'\b' + re.escape(label) + r'\b', lower):
                return ''
        else:
            # Longer labels can match as substrings
            if label in lower:
                # Exception: "Financial Services" contains "Financial", but we want to keep it?
                # "Financial Institution" is banned. "Financial" is in entity suffixes? Yes.
                # If label is 'financial institution', it won't match 'Vanguard
                # Financial Services'.
                if label in ['financial institution', 'tax form', 'statement']:
                    if label in lower:
                        return ''
                elif label in lower:
                    return ''

    # Reject if it's mostly digits (TIN, zip, etc.)
    digit_ratio = sum(c.isdigit() for c in stripped) / len(stripped)
    if digit_ratio > 0.5:
        return ''

    # Reject if it looks like an address
    if looks_like_address(stripped):
        return ''

    return stripped[:100]


def extract_payer_from_fields(pdf) -> str:
    """Try to extract payer name from PDF form fields (AcroForm)."""
    try:
        for page in pdf.pages:
            # Try page-level annotations
            for annot in (page.annots or []):
                data = annot.get('data', {})
                field_name = str(data.get('T', '')).lower()
                field_val = str(data.get('V', '') or '').strip()
                if field_val and (
                        'payer' in field_name or 'employer' in field_name or 'name' in field_name):
                    # explicit exclude common address fields
                    if any(
                        x in field_name for x in [
                            'address',
                            'addr',
                            'city',
                            'state',
                            'zip',
                            'street']):
                        continue

                    # Be strict about "name" fields, ensure they aren't
                    # addresses
                    cleaned = clean_name(field_val)
                    if cleaned:
                        return cleaned
    except Exception:
        pass
    return ''


# Common company suffixes for strong matching
ENTITY_SUFFIXES = [
    'inc', 'inc.', 'corp', 'corp.', 'corporation', 'llc', 'l.l.c.',
    'ltd', 'ltd.', 'limitada', 'limited', 'co.', 'company',
    'bank', 'fund', 'trust', 'association', 'group', 'holdings',
    'credit union', 'fcu', 'n.a.', 'fsb', 'brokerage', 'services',
    'securities', 'advisors', 'management', 'capital', 'financial',
]


def is_company_name(text: str) -> bool:
    """Return True if text ends with or contains a common company suffix."""
    lower = text.lower()
    # Check for suffix at end of string (most common)
    for suffix in ENTITY_SUFFIXES:
        if lower.endswith(
            ' ' +
            suffix) or lower.endswith(
            ',' +
                suffix) or lower == suffix:
            return True

    # Check for strong keywords anywhere (Bank, Credit Union)
    if 'bank' in lower or 'credit union' in lower or 'trust' in lower:
        return True

    return False


def extract_payer_name_from_text(
        full_text: str,
        label_pattern=r'(?:PAYER[^\n]{0,30}name|Name\s*Line\s*1)') -> str:
    """Extract payer/institution name from PDF text, skipping labels and addresses."""
    # Strategy 1: Look for text BEFORE the label line (candidates_above)
    # Strategy 2: Look for text AFTER the label line (candidates_below)

    # Find the "PAYER'S name" label
    payer_section = re.search(label_pattern, full_text, re.IGNORECASE)

    if payer_section:
        candidates_above = []
        candidates_below = []

        # 1. Gather candidates ABOVE
        before = full_text[:payer_section.start()]
        # Check the last few non-empty lines before the label
        lines_before = [l.strip() for l in before.split('\n') if l.strip()]
        for line in reversed(lines_before[-15:]):
            cleaned = clean_name(line)
            if cleaned:
                candidates_above.append(cleaned)

        # 2. Gather candidates BELOW
        after = full_text[payer_section.end():]
        lines_after = [l.strip() for l in after.split('\n') if l.strip()]
        for line in lines_after[:8]:
            cleaned = clean_name(line)
            if cleaned:
                candidates_below.append(cleaned)

        # Priority 0: Known Popular Payer (Database Match) - Highest Priority
        all_candidates = candidates_above + candidates_below
        for cand in all_candidates:
            if get_payer_score(cand) > 50:
                return cand

        # Priority 1: Strong Company Match ABOVE (e.g. Vanguard Marketing Corp)
        for cand in candidates_above:
            if is_company_name(cand):
                return cand

        # Priority 2: Strong Company Match BELOW
        for cand in candidates_below:
            if is_company_name(cand):
                return cand

        # Priority 3: Weak Match BELOW (User Preference for standard forms)
        # If we have a candidate below, it's likely the intended name in a
        # standard form
        if candidates_below:
            return candidates_below[0]

        # Priority 4: Weak Match ABOVE (Fallback for headers without suffixes)
        if candidates_above:
            return candidates_above[0]

    return ''
