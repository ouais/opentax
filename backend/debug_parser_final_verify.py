
def simulate_parser_logic(cell_lower, value):
    result = {}
    print(f"--- Processing Cell: {repr(cell_lower)} / Val: {value} ---")

    # Logic copied from parsers/w2.py
    if 'medicare' in cell_lower and value > 0:
        print(
            f"DEBUG: Medicare keyword found with value {value}. Checking type...")

        # Determine if this is Wages (Box 5) or Tax (Box 6)
        # STRICT MATCHING: A cell cannot be both.
        # Prioritize TAX because "tax" is a strong signal.

        is_tax = (
            'tax' in cell_lower or 'withheld' in cell_lower or 'box 6' in cell_lower)
        # Only check for '6' if we don't have conflicting signals
        if not is_tax and '6' in cell_lower and 'wages' not in cell_lower:
            is_tax = True

        is_wages = (
            'wages' in cell_lower or 'tips' in cell_lower or 'box 5' in cell_lower)
        # Only check for '5' if we don't have conflicting signals and it's not
        # tax
        if not is_wages and not is_tax and '5' in cell_lower and 'tax' not in cell_lower:
            is_wages = True

        # Tie-breaker: If both matched (unlikely with above logic), prioritize
        # label content
        if is_tax and is_wages:
            if 'tax' in cell_lower:
                is_wages = False
            elif 'wages' in cell_lower:
                is_tax = False

        if is_tax:
            print(f"DEBUG: MATCHED Medicare Tax (Final): {value}")
            result['medicare_tax_withheld'] = value

        elif is_wages:  # ELF - only if not tax
            print(f"DEBUG: MATCHED Medicare Wages (Final): {value}")
            result['medicare_wages'] = value

    return result


# Test Case 1: Box 5 (Wages)
cell_5 = '5medicare wages and tips\n909551.19'
val_5 = 909551.19
res_5 = simulate_parser_logic(cell_5, val_5)
print(f"Result 5: {res_5}\n")

# Test Case 2: Box 6 (Tax) - This contains a '5' in the value!
cell_6 = '6medicare tax withheld\n19574.45'
val_6 = 19574.45
res_6 = simulate_parser_logic(cell_6, val_6)
print(f"Result 6: {res_6}\n")

# Verification
if res_5.get(
        'medicare_wages') == 909551.19 and 'medicare_tax_withheld' not in res_5:
    print("PASS: Box 5 correctly identified as Wages only.")
else:
    print("FAIL: Box 5 identification failed.")

if res_6.get(
        'medicare_tax_withheld') == 19574.45 and 'medicare_wages' not in res_6:
    print("PASS: Box 6 correctly identified as Tax only.")
else:
    print("FAIL: Box 6 identification failed (likely misidentified as Wages).")
