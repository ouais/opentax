import sys
import os
sys.path.append(os.path.abspath("backend"))
from tax_engine.federal import calculate_federal_tax

res = calculate_federal_tax(wages=300000, long_term_gains=50000, filing_status='single')
print(res)
