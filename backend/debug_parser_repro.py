
import re


def extract_value_from_cell(cell_text: str) -> float:
    if not cell_text:
        return 0.0

    parts = cell_text.strip().split('\n')

    for part in reversed(parts):
        match = re.search(r'[\$]?\s*(\d[\d,]*(?:\.\d{2})?)', part)
        if match:
            try:
                value_str = match.group(1).replace(',', '')
                value = float(value_str)
                if value > 0:
                    return value
            except ValueError:
                pass
    return 0.0


cell_lower = '5medicare wages and tips\n909551.19'
value = 909551.19

print(f"Cell: {repr(cell_lower)}")
print(f"Value: {value}")
print(f"'medicare' in cell: {'medicare' in cell_lower}")
print(f"'wages' in cell: {'wages' in cell_lower}")
print(f"'5' in cell: {'5' in cell_lower}")

condition_1 = ('medicare' in cell_lower and 'wages' in cell_lower)
condition_2 = ('box 5' in cell_lower)
condition_3 = ('5' in cell_lower and 'medicare' in cell_lower)

print(f"Condition 1 (medicare + wages): {condition_1}")
print(f"Condition 2 (box 5): {condition_2}")
print(f"Condition 3 (5 + medicare): {condition_3}")
print(f"Final OR: {condition_1 or condition_2 or condition_3}")
