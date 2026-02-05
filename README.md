# Tax Calculator 2025

A personal web application for calculating 2025 federal and California state taxes.

## Features

- **PDF Upload & Parsing**: Upload W-2, 1099-INT, 1099-DIV, 1099-B, and 1099-NEC forms
- **Automatic Data Extraction**: Extracts key fields from tax documents
- **Manual Entry**: Review and edit extracted data or enter manually
- **Federal Tax Calculation**: 2025 brackets, standard deduction, capital gains, qualified dividends
- **California Tax Calculation**: 2025 brackets, standard deduction
- **Self-Employment Tax**: Social Security and Medicare tax for 1099-NEC income
- **Refund/Owed Summary**: Compare withholdings to liability

## Tech Stack

- **Backend**: Python FastAPI
- **Frontend**: React + Vite
- **PDF Parsing**: pdfplumber

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

The API will be available at http://localhost:8000

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The app will be available at http://localhost:5173

## API Endpoints

- `GET /api/health` - Health check
- `POST /api/upload` - Upload and parse a PDF tax document
- `POST /api/calculate` - Calculate taxes from income data

## 2025 Tax Rates

### Federal (Single Filer)
| Rate | Income Range |
|------|--------------|
| 10% | $0 - $11,925 |
| 12% | $11,926 - $48,475 |
| 22% | $48,476 - $103,350 |
| 24% | $103,351 - $197,300 |
| 32% | $197,301 - $250,525 |
| 35% | $250,526 - $626,350 |
| 37% | Over $626,350 |

**Standard Deduction**: $15,000

### California (Single Filer)
| Rate | Income Range |
|------|--------------|
| 1.0% | $0 - $11,079 |
| 2.0% | $11,079 - $26,264 |
| 4.0% | $26,264 - $41,452 |
| 6.0% | $41,452 - $57,542 |
| 8.0% | $57,542 - $72,724 |
| 9.3% | $72,724 - $371,479 |
| 10.3% | $371,479 - $445,771 |
| 11.3% | $445,771 - $742,953 |
| 12.3% | Over $742,953 |

**Standard Deduction**: $5,706

## Disclaimer

This calculator is for estimation purposes only and should not be used as a substitute for professional tax advice.
