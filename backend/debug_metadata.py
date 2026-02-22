
import pdfplumber
import sys


def debug_metadata(pdf_path):
    print(f"--- Metadata Debugging {pdf_path} ---")

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        # Inspect annotations (AcroFields)
        if hasattr(page, 'annots') and page.annots:
            print(f"Found {len(page.annots)} annotations.")
            for i, annot in enumerate(page.annots):
                data = annot.get('data', {})
                field_name = str(data.get('T', ''))
                field_val = str(data.get('V', ''))
                print(f"Field {i}: Name='{field_name}', Value='{field_val}'")
        else:
            print("No annotations (AcroFields) found.")


if __name__ == "__main__":
    debug_metadata("debug_last_upload.pdf")
