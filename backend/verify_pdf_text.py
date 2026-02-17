
import os
from pypdf import PdfReader

# Use absolute path
base_dir = os.path.dirname(os.path.abspath(__file__))
pdf_path = os.path.join(base_dir, "forms/f1040.pdf")

reader = PdfReader(pdf_path)
reader = PdfReader(pdf_path)

def analyze_page(page_num):
    print(f"\n=== Analyzing Page {page_num + 1} ===")
    page = reader.pages[page_num]
    
    # 1. Get Fields and their Y-coordinates
    fields = {}
    if '/Annots' in page:
        for annot in page['/Annots']:
            obj = annot.get_object()
            if obj and '/T' in obj:
                rect = obj['/Rect']
                x_coord = int(rect[0])
                y_coord = int(rect[1])
                fields[obj['/T']] = (x_coord, y_coord)

    # 2. Extract Text
    def visitor_body(text, cm, tm, fontDict, fontSize):
        y = tm[5]
        if y > 0 and len(text.strip()) > 0:
            keywords = [
                "Tax-exempt interest", "Taxable interest", "Qualified dividends", "Ordinary dividends",
                "Wage"
            ]
            text_lower = text.lower()
            if any(k.lower() in text_lower for k in keywords):
                print(f"Found TEXT: '{text.strip()}' at Y={y}")

    print("--- Searching for Labels ---")
    page.extract_text(visitor_text=visitor_body)

    print("\n--- Field Coordinates (Sample) ---")
    if page_num == 0:
        fields_to_check = [f"f1_{i:02d}[0]" for i in range(40, 80)]
    else:
        fields_to_check = [f"f2_{i:02d}[0]" for i in range(1, 60)]

    for f in fields_to_check:
        if f in fields:
            print(f"Field {f} is at {fields[f]}")

analyze_page(0)
analyze_page(1)

