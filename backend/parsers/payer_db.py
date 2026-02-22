
# List of popular payer names to cross-reference against
# This list helps prioritize known financial institutions over random text.

POPULAR_PAYERS = [
    # Major Banks
    "JPMORGAN CHASE BANK", "CHASE BANK", "J.P. MORGAN", "WELLS FARGO", "BANK OF AMERICA",
    "CITIBANK", "U.S. BANK", "PNC BANK", "TRUIST BANK", "GOLDMAN SACHS", "CAPITAL ONE",
    "TD BANK", "BANK OF THE WEST", "BMO HARRIS BANK", "FIFTH THIRD BANK", "KEYBANK",
    "M&T BANK", "HUNTINGTON NATIONAL BANK", "REGIONS BANK", "CITIZENS BANK",
    "ALLY BANK", "DISCOVER BANK", "SYNCHRONY BANK", "BARCLAYS BANK DELAWARE",
    "AMERICAN EXPRESS NATIONAL BANK", "CHARLES SCHWAB BANK", "MORGAN STANLEY PRIVATE BANK",

    # Brokerages & Investment Firms
    "VANGUARD", "VANGUARD GROUP", "VANGUARD MARKETING CORPORATION",
    "FIDELITY INVESTMENTS", "FIDELITY BROKERAGE SERVICES", "NATIONAL FINANCIAL SERVICES",
    "CHARLES SCHWAB & CO", "TD AMERITRADE", "E*TRADE", "ETRADE", "MORGAN STANLEY",
    "MERRILL LYNCH", "EDWARD JONES", "RAYMOND JAMES", "LPL FINANCIAL",
    "INTERACTIVE BROKERS", "ROBINHOOD", "ROBINHOOD SECURITIES", "ROBINHOOD FINANCIAL",
    "WEBULL", "COINBASE", "GEMINI TRUST COMPANY", "BLOCKFI", "KRAKEN",
    "BETTERMENT", "WEALTHFRONT", "ACORNS", "STASH", "M1 FINANCE",
    "T. ROWE PRICE", "BLACKROCK", "INVESCO", "FRANKLIN TEMPLETON",
    "AMERICAN FUNDS", "PIMCO", "JANUS HENDERSON",

    # Credit Unions (Generic top ones)
    "NAVY FEDERAL CREDIT UNION", "STATE EMPLOYEES' CREDIT UNION", "PENTAGON FEDERAL CREDIT UNION",
    "BECU", "SCHOOLSFIRST FEDERAL CREDIT UNION", "GOLDEN 1 CREDIT UNION",
    "ALLIANT CREDIT UNION", "FIRST TECH FEDERAL CREDIT UNION",

    # Fintech / Neobanks
    "CHIME", "VARO BANK", "SOFI BANK", "REVOLUT", "CURRENT", "ASPIRATION",
    "PAYPAL", "SQUARE", "BLOCK", "CASH APP", "STRIPE", "ADYEN",

    # Government / Treasury
    "DEPARTMENT OF THE TREASURY", "INTERNAL REVENUE SERVICE", "US TREASURY",

    # Common Variations
    "VANGUARD MARKETING CORP", "FIDELITY BROKERAGE SERVICES LLC",
    "CHARLES SCHWAB & CO INC", "TD AMERITRADE CLEARING", "NATIONAL FINANCIAL SERVICES LLC",
]


def get_payer_score(text: str) -> int:
    """
    Return a score for the text based on its match with popular payers.
    High score = likely a real payer. 0 = no match.
    """
    upper = text.upper()

    # Exact match
    if upper in POPULAR_PAYERS:
        return 100

    # Substring match (e.g. "Vanguard" in "The Vanguard Group")
    for payer in POPULAR_PAYERS:
        if payer in upper:
            # If the known payer is a significant part of the text
            return 90

    # Fuzzy match logic could go here, but substring is usually enough for
    # "Top 1k" concept
    return 0
