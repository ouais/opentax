
from tax_engine.no_income_tax import NoIncomeTaxState
from tax_engine.new_york import NewYorkStateCalculator
import sys
import os

# Add parent directory to path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def verify():
    print("Verifying NoIncomeTaxState keys...")
    calc_no = NoIncomeTaxState()
    res_no = calc_no.calculate({'wages': 100000.0, 'tax_year': 2024})
    check_keys(res_no, "NoIncomeTaxState")

    print("\nVerifying NewYorkStateCalculator keys...")
    calc_ny = NewYorkStateCalculator()
    # NY needs federal_agi
    res_ny = calc_ny.calculate(
        {'wages': 100000.0, 'tax_year': 2024, 'federal_agi': 100000.0})
    check_keys(res_ny, "NewYorkStateCalculator")

    print("\nVerifying FederalTaxResult keys...")
    from tax_engine.federal import calculate_federal_tax
    res_fed = calculate_federal_tax(wages=100000.0)
    check_federal_keys(res_fed, "FederalCalculator")

    print("\nVerifying Main Calculator (Integration)...")
    from tax_engine.calculator import calculate_taxes
    # Standard input simulating full flow
    tax_input = {
        'w2_wages': 100000.0,
        'tax_year': 2024,
        'state': 'NY',  # Test NY Integration
        'w2_state_withheld': 5000.0,
        'w2_federal_withheld': 10000.0
    }
    res_main = calculate_taxes(tax_input)
    check_main_keys(res_main, "MainCalculator")


def check_federal_keys(res, name):
    required = [
        "gross_income", "total_federal_tax", "bracket_breakdown",
        "effective_rate", "marginal_rate", "ordinary_income_tax",
        "capital_gains_tax", "self_employment_tax", "standard_deduction",
        "taxable_income"
    ]
    check_generic(res, name, required)


def check_main_keys(res, name):
    required_top = [
        "federal", "california", "total_state_withheld", "amount_owed",
        "total_federal_withheld", "refund_or_owed"
    ]
    check_generic(res, name, required_top)

    # Check nested Federal
    check_federal_keys(res['federal'], f"{name}.federal")
    # Check nested State (NY in this case)
    # Reuse check_keys from before
    check_keys(res['california'], f"{name}.california")


def check_generic(res, name, required):
    missing = []
    for k in required:
        if k not in res:
            missing.append(k)
        elif res[k] is None:
            print(f"[{name}] Warning: Key '{k}' is None")

    if missing:
        print(f"[{name}] CRITICAL: Missing keys: {missing}")
    else:
        print(f"[{name}] All keys present.")

    # Check breakdown items
    if "bracket_breakdown" in res:
        breakdown = res["bracket_breakdown"]
        if not isinstance(breakdown, list):
            print(f"[{name}] CRITICAL: bracket_breakdown is not a list")
            return

        required_item = [
            "rate",
            "range_start",
            "range_end",
            "tax_in_bracket",
            "income_in_bracket"]
        for i, item in enumerate(breakdown):
            for k in required_item:
                if k not in item:
                    print(f"[{name}] CRITICAL: Item {i} missing '{k}'")
                elif item[k] is None:
                    print(f"[{name}] CRITICAL: Item {i} key '{k}' is None")
                elif not isinstance(item[k], (int, float)):
                    print(
                        f"[{name}] CRITICAL: Item {i} key '{k}' has bad type {type(item[k])}")


def check_keys(res, name):
    required = [
        "total_taxable_income",
        "total_state_tax",
        "standard_deduction",
        "bracket_breakdown",
        "effective_rate",
        "marginal_rate",
        "mental_health_tax",

        # Legacy/Compat
        "gross_income",
        "taxable_income",
        "state_tax",
        "mental_health_surcharge",
        "total_california_tax"
    ]

    missing = []
    for k in required:
        if k not in res:
            missing.append(k)
        elif res[k] is None:
            print(f"[{name}] Warning: Key '{k}' is None")

    if missing:
        print(f"[{name}] CRITICAL: Missing keys: {missing}")
    else:
        print(f"[{name}] All required keys present.")
        # Print breakdown to verify type
        print(f"[{name}] Breakdown type: {type(res['bracket_breakdown'])}")
        print(f"[{name}] Marginal Rate: {res.get('marginal_rate')}")


if __name__ == "__main__":
    verify()
