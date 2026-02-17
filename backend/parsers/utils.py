
import re

# Known PDF field labels that should never be accepted as institution names
FIELD_LABELS = [
    'name line', 'street address', 'city or town', 'state or province',
    'zip code', 'postal code', 'country', 'phone', 'fax', 'tin',
    'taxpayer', 'identification', 'recipient', 'account', 'facta',
    'fatca', 'form 1099', 'corrected', 'void', 'omb no', 'copy',
    'department of', 'internal revenue', 'payer', 'borrower',
    'box ', 'interest income', 'federal income', 'early withdrawal',
    'u.s. savings', 'foreign tax', 'tax-exempt', 'specified private',
    'market discount', 'bond premium', 'investment expenses',
    'employer', 'address', 'employee', 'control number',
    'social security', 'medicare', 'w-2', 
]

# US state abbreviations for address detection
STATE_ABBREVS = {
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC',
}


def looks_like_address(text: str) -> bool:
    """Return True if text looks like a street address or city/state/zip line."""
    stripped = text.strip()
    if not stripped:
        return True
    # Starts with digits (street number) — e.g. "123 Main St"
    if re.match(r'^\d+\s', stripped):
        return True
    # Contains P.O. Box, Suite, Floor, Apt
    if re.search(r'\b(?:P\.?O\.?\s*Box|Suite|Ste\.?|Floor|Fl\.?|Apt\.?|Unit)\b', stripped, re.IGNORECASE):
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
    if re.search(r'(?:phone|tel|fax|cell).*[\d\-]{7,}', stripped, re.IGNORECASE):
        return True
    
    # Emails or URLs
    if re.search(r'@[\w\.-]+|\.com\b|\.org\b|\.net\b', stripped, re.IGNORECASE):
        return True
        
    return False


def clean_name(name: str) -> str:
    """Return the name if it looks like a real institution, or empty string."""
    stripped = name.strip()
    if not stripped or len(stripped) < 2:
        return ''
    lower = stripped.lower()
    # Reject if it matches a known field label
    if any(label in lower for label in FIELD_LABELS):
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
                if field_val and ('payer' in field_name or 'employer' in field_name or 'name' in field_name):
                    # Be strict about "name" fields, ensure they aren't addresses
                    cleaned = clean_name(field_val)
                    if cleaned:
                        return cleaned
    except Exception:
        pass
    return ''


def extract_payer_name_from_text(full_text: str, label_pattern=r'(?:PAYER.S?\s*name|PAYER.S?\s*,)') -> str:
    """Extract payer/institution name from PDF text, skipping labels and addresses."""
    # Strategy 1: Look for text BEFORE the label line
    # In many pre-printed PDFs, the company name is above the label
    payer_section = re.search(label_pattern, full_text, re.IGNORECASE)
    
    if payer_section:
        before = full_text[:payer_section.start()]
        # Check the last few non-empty lines before the label
        # Scan up to 15 lines to skip past addresses, phone numbers, department names, etc.
        lines_before = [l.strip() for l in before.split('\n') if l.strip()]
        for line in reversed(lines_before[-15:]):
            cleaned = clean_name(line)
            if cleaned:
                return cleaned

    # Strategy 2: Look for text AFTER the label (fallback)
    if payer_section:
        after = full_text[payer_section.end():]
        for line in after.split('\n')[:8]:
            cleaned = clean_name(line)
            if cleaned:
                return cleaned

    return ''
