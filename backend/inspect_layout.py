from pypdf import PdfReader

import os
base_dir = os.path.dirname(os.path.abspath(__file__))
reader = PdfReader(os.path.join(base_dir, "forms/f1040.pdf"))


def inspect_page(page_num):
    print(f"--- Page {page_num + 1} ---")
    page = reader.pages[page_num]
    if '/Annots' in page:
        annots = page['/Annots']
        fields = []
        for annot in annots:
            obj = annot.get_object()
            if '/T' in obj:  # It has a field name
                rect = obj['/Rect']
                name = obj['/T']
                fields.append({'name': name, 'rect': rect})

        # Sort by Y descending (top to bottom), then X ascending
        fields.sort(key=lambda x: (-x['rect'][1], x['rect'][0]))

        for f in fields:
            # Print simplified rect (int)
            r = [int(v) for v in f['rect']]
            print(f"Field: {f['name']} | Y={r[1]} | X={r[0]}")


inspect_page(0)
inspect_page(1)
