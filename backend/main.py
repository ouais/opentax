"""
Tax Calculator API

FastAPI backend for the 2025 tax calculator application.
"""

import io
import os
import tempfile
import zipfile
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from parsers.w2 import parse_w2
from parsers.form_1099_int import parse_1099_int
from parsers.form_1099_div import parse_1099_div
from parsers.form_1099_b import parse_1099_b
from parsers.form_1099_nec import parse_1099_nec
from parsers.form_1040 import parse_form_1040
from tax_engine import calculate_taxes
from pdf_generator import generate_1040, generate_540


app = FastAPI(
    title="Tax Calculator API",
    description="2025 Federal and California tax calculator with PDF parsing",
    version="1.0.0",
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TaxCalculationRequest(BaseModel):
    """Request body for tax calculation."""
    # W-2 fields
    w2_wages: float = 0.0
    w2_federal_withheld: float = 0.0
    w2_state_withheld: float = 0.0
    w2_social_security_wages: float = 0.0
    w2_casdi: float = 0.0  # California State Disability Insurance
    
    # 1099-INT fields
    interest_income: float = 0.0
    tax_exempt_interest: float = 0.0
    interest_federal_withheld: float = 0.0
    
    # 1099-DIV fields
    ordinary_dividends: float = 0.0
    qualified_dividends: float = 0.0
    capital_gain_distributions: float = 0.0
    dividend_federal_withheld: float = 0.0
    
    # 1099-B fields
    short_term_gains: float = 0.0
    long_term_gains: float = 0.0
    
    # 1099-NEC fields
    self_employment_income: float = 0.0
    self_employment_federal_withheld: float = 0.0
    
    # Validation / Additional Payments
    estimated_tax_payments: float = 0.0
    other_withholding: float = 0.0
    tax_year: int = 2024
    
    # Advanced
    itemized_deductions: float = 0.0
    foreign_income: float = 0.0
    state: str = "CA"

class Pii(BaseModel):
    firstName: str = ""
    lastName: str = ""
    ssn: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    zip: str = ""

class PdfRequest(TaxCalculationRequest):
    pii: Pii


class ParsedDocument(BaseModel):
    """Response for a parsed document."""
    form_type: str
    parse_confidence: str
    data: dict
    raw_text: Optional[str] = None


@app.post("/api/upload", response_model=ParsedDocument)
async def upload_document(
    file: UploadFile = File(...),
    form_type: Optional[str] = None,
):
    """
    Upload a tax document PDF and extract data.
    
    Args:
        file: The PDF file to parse
        form_type: Optional hint for the form type (w2, 1099-int, 1099-div, 1099-b, 1099-nec)
    
    Returns:
        ParsedDocument with extracted data
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Determine which parser to use
        filename_lower = file.filename.lower()
        form_type_lower = (form_type or '').lower()
        
        # Try to auto-detect form type from filename
        if form_type_lower == 'w2' or 'w-2' in filename_lower or 'w2' in filename_lower:
            result = parse_w2(tmp_path)
        elif form_type_lower == '1099-int' or '1099-int' in filename_lower or '1099int' in filename_lower:
            result = parse_1099_int(tmp_path)
        elif form_type_lower == '1099-div' or '1099-div' in filename_lower or '1099div' in filename_lower:
            result = parse_1099_div(tmp_path)
        elif form_type_lower == '1099-b' or '1099-b' in filename_lower or '1099b' in filename_lower:
            result = parse_1099_b(tmp_path)
        elif form_type_lower == '1099-nec' or '1099-nec' in filename_lower or '1099nec' in filename_lower:
            result = parse_1099_nec(tmp_path)
        else:
            # Run all parsers and aggregate results
            parsers = [
                parse_w2,
                parse_1099_int,
                parse_1099_div,
                parse_1099_nec,
                parse_1099_b,
                parse_form_1040,
            ]
            
            aggregated_data = {}
            found_types = []
            highest_confidence = 'failed'
            confidence_scores = {'high': 3, 'medium': 2, 'low': 1, 'failed': 0}
            
            for parser in parsers:
                try:
                    parser_result = parser(tmp_path)
                    
                    # If parser found something relevant (confidence > failed)
                    if parser_result.get('parse_confidence', 'failed') != 'failed':
                        # Update confidence
                        conf = parser_result.get('parse_confidence', 'failed')
                        if confidence_scores.get(conf, 0) > confidence_scores.get(highest_confidence, 0):
                            highest_confidence = conf
                        
                        # Track found form types
                        if parser_result.get('form_type'):
                            found_types.append(parser_result['form_type'])
                            
                        # Merge numeric fields
                        for key, value in parser_result.items():
                            if isinstance(value, (int, float)) and value != 0:
                                current_val = aggregated_data.get(key, 0.0)
                                aggregated_data[key] = current_val + value
                            elif key not in aggregated_data and value:
                                agg_val = aggregated_data.get(key)
                                if not agg_val:
                                     aggregated_data[key] = value
                except Exception:
                    continue
            
            if not aggregated_data:
                # Fallback if nothing found
                aggregated_data = parse_w2(tmp_path)
                result = aggregated_data # raw dict
                result['form_type'] = 'W-2' # Default
                result['parse_confidence'] = 'failed'
            else:
                # Construct final result
                aggregated_data['form_type'] = '+'.join(set(found_types)) if found_types else 'Unknown'
                aggregated_data['parse_confidence'] = highest_confidence
                result = aggregated_data
        
        # Extract raw_text for response (truncate if too long)
        raw_text = result.pop('raw_text', '')
        if len(raw_text) > 5000:
            raw_text = raw_text[:5000] + '...[truncated]'
        
        # Return merged result nested
        return ParsedDocument(
            form_type=result.get('form_type', 'unknown'),
            parse_confidence=result.get('parse_confidence', 'failed'),
            data=result,
            raw_text=raw_text
        )
        
    finally:
        # Clean up temp file
        os.unlink(tmp_path)


@app.post("/api/calculate")
async def calculate_tax(request: TaxCalculationRequest):
    """
    Calculate federal and California taxes based on provided income data.
    
    Returns complete tax breakdown including:
    - Federal tax with bracket breakdown
    - California state tax
    - Self-employment tax (if applicable)
    - Withholding comparison
    - Amount owed or refund due
    """
    tax_input = {
        'w2_wages': request.w2_wages,
        'w2_federal_withheld': request.w2_federal_withheld,
        'w2_state_withheld': request.w2_state_withheld,
        'w2_social_security_wages': request.w2_social_security_wages,
        'w2_casdi': request.w2_casdi,
        'interest_income': request.interest_income,
        'tax_exempt_interest': request.tax_exempt_interest,
        'interest_federal_withheld': request.interest_federal_withheld,
        'ordinary_dividends': request.ordinary_dividends,
        'qualified_dividends': request.qualified_dividends,
        'capital_gain_distributions': request.capital_gain_distributions,
        'dividend_federal_withheld': request.dividend_federal_withheld,
        'short_term_gains': request.short_term_gains,
        'long_term_gains': request.long_term_gains,
        'self_employment_income': request.self_employment_income,
        'self_employment_federal_withheld': request.self_employment_federal_withheld,
        'estimated_tax_payments': request.estimated_tax_payments,
        'other_withholding': request.other_withholding,
        'tax_year': request.tax_year,
        'itemized_deductions': request.itemized_deductions,
        'foreign_income': request.foreign_income,
        'state': request.state,
    }
    
    result = calculate_taxes(tax_input)
    return result


@app.post("/api/generate-pdf")
async def generate_pdf_endpoint(request: PdfRequest, form_type: str = "all"):
    tax_input = request.dict(exclude={'pii'})
    pii_dict = request.pii.dict()
    
    try:
        result = calculate_taxes(tax_input)
        
        if form_type == "1040":
            pdf_stream = generate_1040(result, pii_dict)
            return Response(
                content=pdf_stream.read(),
                media_type="application/pdf",
                headers={"Content-Disposition": "attachment; filename=form1040_2025.pdf"}
            )
        elif form_type == "540":
            pdf_stream = generate_540(result, pii_dict)
            return Response(
                content=pdf_stream.read(),
                media_type="application/pdf",
                headers={"Content-Disposition": "attachment; filename=ca540_2025.pdf"}
            )
        else:
            # Generate both and bundle as ZIP
            pdf_1040 = generate_1040(result, pii_dict)
            pdf_540 = generate_540(result, pii_dict)
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.writestr('form1040_2025.pdf', pdf_1040.read())
                zf.writestr('ca540_2025.pdf', pdf_540.read())
            zip_buffer.seek(0)
            
            return Response(
                content=zip_buffer.read(),
                media_type="application/zip",
                headers={"Content-Disposition": "attachment; filename=tax_forms_2025.zip"}
            )
    except Exception as e:
        print(f"PDF Generation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Serve React Frontend
# Mount assets
if os.path.exists("../frontend/dist/assets"):
    app.mount("/assets", StaticFiles(directory="../frontend/dist/assets"), name="assets")

# SPA Fallback for all other routes (excluding /api)
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    # API routes are handled above. This catches everything else.
    # Serve index.html for React Router
    if os.path.exists("../frontend/dist/index.html"):
        return FileResponse("../frontend/dist/index.html")
    return {"error": "Frontend not found. Please build frontend first."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
