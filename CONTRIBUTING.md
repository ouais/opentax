# Contributing to OpenTax

This guide explains how to add features and state tax support to OpenTax.

## Architecture Overview

```
tax-app/
├── backend/
│   ├── main.py              # FastAPI server + API endpoints
│   ├── tax_engine.py         # Tax calculation orchestrator
│   ├── pdf_generator.py      # PDF form generation (1040, 540)
│   ├── forms/                # Blank PDF templates
│   ├── parsers/              # Document parsers (W-2, 1099s, etc.)
│   ├── states/               # State tax calculators
│   │   ├── california.py
│   │   ├── new_york.py
│   │   ├── texas.py
│   │   └── ...
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Main app with all views
│   │   ├── index.css         # Design system + styles
│   │   └── components/
│   │       ├── TaxForms.jsx  # PDF preview + download
│   │       └── TaxForms.css
│   └── index.html
```

## Adding a New State

### 1. Create the State Calculator

Add a new file at `backend/states/<state_name>.py`. Follow the existing pattern:

```python
# backend/states/oregon.py

def calculate_oregon_tax(federal_results, income_data):
    """Calculate Oregon state taxes.
    
    Args:
        federal_results: Dict with federal calculation output (AGI, deductions, etc.)
        income_data: Dict with raw income inputs from the user.
    
    Returns:
        Dict with keys:
            - gross_income: State gross income
            - standard_deduction: State standard deduction amount
            - taxable_income: State taxable income
            - state_tax: Calculated state income tax
            - marginal_rate: Top marginal rate applied (percent)
            - effective_rate: Effective rate (percent)
            - total_<state>_tax: Total state tax liability
            - bracket_breakdown: List of { rate, income_in_bracket, tax_in_bracket }
    """
    agi = federal_results.get('gross_income', 0)
    
    # Oregon standard deduction for Single filer (2025)
    standard_deduction = 2745
    
    taxable_income = max(0, agi - standard_deduction)
    
    # Oregon 2025 brackets (Single)
    brackets = [
        (4300, 0.0475),
        (10750, 0.0675),
        (125000, 0.0875),
        (float('inf'), 0.099),
    ]
    
    tax = 0
    remaining = taxable_income
    breakdown = []
    
    for limit, rate in brackets:
        if remaining <= 0:
            break
        income_in_bracket = min(remaining, limit)
        tax_in_bracket = income_in_bracket * rate
        tax += tax_in_bracket
        breakdown.append({
            'rate': rate,
            'income_in_bracket': income_in_bracket,
            'tax_in_bracket': tax_in_bracket,
        })
        remaining -= income_in_bracket
    
    effective_rate = (tax / agi * 100) if agi > 0 else 0
    marginal_rate = brackets[-1][1] * 100
    for limit, rate in brackets:
        if taxable_income <= limit:
            marginal_rate = rate * 100
            break
    
    return {
        'gross_income': agi,
        'standard_deduction': standard_deduction,
        'taxable_income': taxable_income,
        'state_tax': round(tax, 2),
        'marginal_rate': round(marginal_rate, 2),
        'effective_rate': round(effective_rate, 2),
        'total_oregon_tax': round(tax, 2),
        'bracket_breakdown': breakdown,
    }
```

### 2. Register the State in the Tax Engine

Open `backend/tax_engine.py` and:

1. Import your calculator at the top:
   ```python
   from states.oregon import calculate_oregon_tax
   ```

2. Add it to the state dispatch map (look for WHERE states are mapped to functions):
   ```python
   'OR': calculate_oregon_tax,
   ```

### 3. Add to the Frontend State Selector

Open `frontend/src/App.jsx` and add to `STATE_CONFIG`:

```javascript
const STATE_CONFIG = {
  // ... existing states ...
  OR: { name: 'Oregon' },
};
```

### 4. Write Tests

Create `backend/tests/test_oregon.py`:

```python
import pytest
from states.oregon import calculate_oregon_tax


def test_basic_oregon_calculation():
    federal = {
        'gross_income': 100000,
        'taxable_income': 86150,
    }
    income = {'state': 'OR'}
    
    result = calculate_oregon_tax(federal, income)
    
    assert result['standard_deduction'] == 2745
    assert result['taxable_income'] == 97255
    assert result['state_tax'] > 0
    assert result['effective_rate'] > 0


def test_zero_income():
    federal = {'gross_income': 0, 'taxable_income': 0}
    income = {'state': 'OR'}
    
    result = calculate_oregon_tax(federal, income)
    
    assert result['state_tax'] == 0
    assert result['effective_rate'] == 0
```

Run with: `cd backend && python -m pytest tests/test_oregon.py -v`

### 5. (Optional) Add State PDF Form Generation

To generate a fillable PDF for your state:

1. Download the blank PDF form from the state's tax agency website
2. Place it in `backend/forms/` (e.g., `or40.pdf`)
3. Run the debug script to identify field names:
   ```python
   from pypdf import PdfReader
   reader = PdfReader('forms/or40.pdf')
   for name, field in reader.get_fields().items():
       if '/Tx' in str(field.get('/FT', '')):
           print(name)
   ```
4. Add a generator function in `pdf_generator.py` following the `generate_540` pattern
5. Import and wire it up in `main.py`

## Adding a New Document Parser

Parsers live in `backend/parsers/`. Each exports a `parse_<form_type>(pdf_path)` function that returns structured data from an uploaded PDF.

Look at existing parsers like `form_w2.py` or `form_1099_int.py` for the pattern.

## Running the App

```bash
# Backend
cd backend
source venv/bin/activate
python main.py
# Runs at http://localhost:8000

# Frontend (dev mode)
cd frontend
npm run dev
# Runs at http://localhost:5173

# Frontend (production build)
cd frontend
npm run build
# Output goes to frontend/dist/, served by the backend
```

## Tech Stack

- **Frontend**: React, Vite, vanilla CSS
- **Backend**: Python, FastAPI, pypdf
- **PDF Generation**: pypdf with AcroForm field filling
