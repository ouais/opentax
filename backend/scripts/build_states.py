import os
import glob
import json

STATE_NAMES = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
    'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
    'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
    'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
    'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire',
    'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina',
    'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania',
    'RI': 'Rhode Island', 'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee',
    'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington',
    'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia',
    'PR': 'Puerto Rico', 'GU': 'Guam', 'VI': 'US Virgin Islands', 'AS': 'American Samoa',
    'MP': 'Northern Mariana Islands'
}

DATA_DIR = '/tmp/taxgraphs/data/2024/state'
OUT_FILE = '/Users/ouais/projects/tax-app/backend/tax_engine/data/states.json'

output_states = {}

for filepath in glob.glob(os.path.join(DATA_DIR, '*.json')):
    filename = os.path.basename(filepath)
    state_code = filename.split('.')[0].upper()

    if state_code not in STATE_NAMES:
        continue

    with open(filepath, 'r') as f:
        data = json.load(f)

    taxes = data.get('taxes', {}).get('income', {})
    rate_info = taxes.get('rate')

    state_entry = {
        "name": STATE_NAMES[state_code],
        "has_income_tax": True,
        "2024": {
            "std_deduction": {
                "single": 0.0,
                "joint": 0.0
            },
            "brackets": {
                "single": [],
                "joint": []
            }
        }
    }

    if rate_info is None or rate_info == 0 or rate_info == 0.0:
        state_entry["has_income_tax"] = False
        del state_entry["2024"]
    elif isinstance(rate_info, (int, float)):
        # Flat tax
        rate = float(rate_info)
        state_entry["2024"]["brackets"]["single"] = [[None, rate]]
        state_entry["2024"]["brackets"]["joint"] = [[None, rate]]
    elif isinstance(rate_info, (dict, list)):
        # Progressive brackets
        if isinstance(rate_info, list):
            rate_info = {"single": rate_info, "married": rate_info}

        for status_out, status_in in [("single", "single"), ("joint", "married")]:
            old_brackets = rate_info.get(status_in, [])
            new_brackets = []
            for i in range(len(old_brackets)):
                current_rate = float(old_brackets[i][1])
                upper_limit = float(old_brackets[i + 1][0]) if i + 1 < len(old_brackets) else None
                new_brackets.append([upper_limit, current_rate])

            if not new_brackets:
                # Fallback to single if joint is missing
                if status_out == "joint" and state_entry["2024"]["brackets"]["single"]:
                    state_entry["2024"]["brackets"]["joint"] = state_entry["2024"]["brackets"]["single"].copy()
            else:
                state_entry["2024"]["brackets"][status_out] = new_brackets

    # Handle Deductions safely
    if state_entry.get("has_income_tax"):
        try:
            deduction_amt = taxes.get('deductions', {}).get('standardDeduction', {}).get('amount')
            if isinstance(deduction_amt, (int, float)):
                state_entry["2024"]["std_deduction"]["single"] = float(deduction_amt)
                state_entry["2024"]["std_deduction"]["joint"] = float(deduction_amt)
            elif isinstance(deduction_amt, dict):
                def extract_val(val):
                    while isinstance(val, (list, tuple)) and len(val) > 0:
                        val = val[0]
                    if val is None or isinstance(val, dict):  # if it's still a dict, just return 0.0
                        return 0.0
                    return float(val)

                single_ded = extract_val(deduction_amt.get('single', 0.0))
                joint_ded = extract_val(deduction_amt.get('married', deduction_amt.get('single', 0.0)))

                state_entry["2024"]["std_deduction"]["single"] = single_ded
                state_entry["2024"]["std_deduction"]["joint"] = joint_ded
        except Exception as e:
            print(f"Error processing deductions for {state_code}: {e}")
            print(taxes.get('deductions', {}))
            raise

    output_states[state_code] = state_entry

# Manually add Puerto Rico (PR)
output_states['PR'] = {
    "name": "Puerto Rico",
    "has_income_tax": True,
    "2024": {
        "std_deduction": {
            "single": 0.0,
            "joint": 0.0
        },
        "brackets": {
            "single": [
                [9000, 0.0],
                [25000, 0.07],
                [41500, 0.14],
                [61500, 0.25],
                [None, 0.33]
            ],
            "joint": [
                [18000, 0.0],
                [50000, 0.07],
                [83000, 0.14],
                [123000, 0.25],
                [None, 0.33]
            ]
        }
    }
}

# Add other territories as placeholders
for terr_code in ['GU', 'VI', 'AS', 'MP']:
    if terr_code not in output_states:
        output_states[terr_code] = {
            "name": STATE_NAMES[terr_code],
            "has_income_tax": False,
            "notes": "Territory tax system not yet fully integrated. Using $0 placeholder."
        }

output_states = dict(sorted(output_states.items()))

with open(OUT_FILE, 'w') as f:
    json.dump(output_states, f, indent=2)

print(f"Successfully processed {len(output_states)} states into {OUT_FILE}")
