from pypdf import PdfReader

# Analyze the PDF fields
try:
    reader = PdfReader("forms/f1040.pdf")
    fields = reader.get_fields() 
    if fields:
        for field_name, value in fields.items():
            tooltip = value.get('/TU', 'No Tooltip')
            print(f"Field: {field_name} | Type: {value.get('/FT')} | Tooltip: {tooltip}")
    else:
        print("No fields found.")
except Exception as e:
    print(f"Error: {e}")
