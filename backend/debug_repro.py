
from parsers.payer_db import get_payer_score, POPULAR_PAYERS
from parsers.utils import (
    clean_name,
    looks_like_address,
    is_company_name,
    extract_payer_name_from_text,
    FIELD_LABELS,
    STREET_SUFFIXES
)
import pdfplumber
import re
import sys
import os

# Set up path to import from parsers
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def debug_extraction(pdf_path):
    print(f"--- Debugging {pdf_path} ---")

    with pdfplumber.open(pdf_path) as pdf:
        full_text = ''
        for page in pdf.pages:
            full_text += (page.extract_text() or '') + '\n'

    print("\n--- RAW TEXT START ---")
    print(full_text)
    print("--- RAW TEXT END ---\n")

    # Re-implement the extraction logic with prints
    label_pattern = r'(?:PAYER[^\n]{0,30}name|Name\s*Line\s*1)'
    print(f"Using label pattern: {label_pattern}")

    payer_section = re.search(label_pattern, full_text, re.IGNORECASE)

    if not payer_section:
        print("❌ NO ANCHOR FOUND!")
        return

    print(
        f"✅ Found anchor: '{payer_section.group(0)}' at index {payer_section.start()}")

    candidates_above = []
    candidates_below = []

    # 1. Gather candidates ABOVE
    before = full_text[:payer_section.start()]
    lines_before = [l.strip() for l in before.split('\n') if l.strip()]
    print("\n--- Candidates ABOVE analysis ---")
    for line in reversed(lines_before[-15:]):
        print(f"Checking: '{line}'")
        cleaned = clean_name(line)
        if cleaned:
            print(f"  -> Accepted candidate: '{cleaned}'")
            candidates_above.append(cleaned)
        else:
            print(f"  -> Rejected by clean_name.")
            # Debug why rejected
            if looks_like_address(line):
                print("     (Looks like address)")
            for label in FIELD_LABELS:
                if label in line.lower():
                    print(f"     (Matches label: {label})")
            if re.match(
                r'^(?:City|State|Zip|Address|Street)\s*:',
                line,
                    re.IGNORECASE):
                print("     (Starts with address label)")

    # 2. Gather candidates BELOW
    after = full_text[payer_section.end():]
    lines_after = [l.strip() for l in after.split('\n') if l.strip()]
    print("\n--- Candidates BELOW analysis ---")
    for line in lines_after[:8]:
        print(f"Checking: '{line}'")
        cleaned = clean_name(line)
        if cleaned:
            print(f"  -> Accepted candidate: '{cleaned}'")
            candidates_below.append(cleaned)
        else:
            print(f"  -> Rejected by clean_name.")
            if looks_like_address(line):
                print("     (Looks like address)")
            for label in FIELD_LABELS:
                if label in line.lower():
                    print(f"     (Matches label: {label})")
            if re.match(
                r'^(?:City|State|Zip|Address|Street)\s*:',
                line,
                    re.IGNORECASE):
                print("     (Starts with address label)")

    print("\n--- Final Selection Logic ---")
    all_candidates = candidates_above + candidates_below

    # Priority 0
    for cand in all_candidates:
        score = get_payer_score(cand)
        if score > 50:
            print(f"🏆 WINNER (Database Match): '{cand}'")
            return

    # Priority 1
    for cand in candidates_above:
        if is_company_name(cand):
            print(f"🏆 WINNER (Strong Above): '{cand}'")
            return

    # Priority 2
    for cand in candidates_below:
        if is_company_name(cand):
            print(f"🏆 WINNER (Strong Below): '{cand}'")
            return

    # Priority 3
    if candidates_below:
        print(f"🏆 WINNER (Weak Below): '{candidates_below[0]}'")
        return

    # Priority 4
    if candidates_above:
        print(f"🏆 WINNER (Weak Above): '{candidates_above[0]}'")
        return

    print("❌ NO WINNER SELECTED")


if __name__ == "__main__":
    debug_extraction("debug_last_upload.pdf")
