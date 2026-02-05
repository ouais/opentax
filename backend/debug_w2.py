"""
Debug script to analyze W-2 PDF content.
Run with: python debug_w2.py /path/to/your/w2.pdf
"""

import sys
import pdfplumber


def debug_pdf(pdf_path: str):
    print(f"\n{'='*60}")
    print(f"Analyzing: {pdf_path}")
    print('='*60)
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            print(f"\n--- Page {i+1} ---\n")
            
            # Extract text
            text = page.extract_text()
            print("=== EXTRACTED TEXT ===")
            print(text if text else "(no text extracted)")
            print()
            
            # Extract tables
            tables = page.extract_tables()
            if tables:
                print("=== TABLES ===")
                for j, table in enumerate(tables):
                    print(f"\nTable {j+1}:")
                    for row in table:
                        print(f"  {row}")
            else:
                print("=== NO TABLES FOUND ===")
            
            # Extract words with positions
            words = page.extract_words()
            if words:
                print(f"\n=== WORDS ({len(words)} total) ===")
                # Group by approximate y position
                rows = {}
                for word in words:
                    y_key = round(word['top'] / 20) * 20
                    if y_key not in rows:
                        rows[y_key] = []
                    rows[y_key].append(word)
                
                for y_key in sorted(rows.keys()):
                    row_words = sorted(rows[y_key], key=lambda w: w['x0'])
                    row_text = ' | '.join(f"{w['text']}" for w in row_words)
                    print(f"Y={y_key}: {row_text}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_w2.py /path/to/w2.pdf")
        sys.exit(1)
    
    debug_pdf(sys.argv[1])
