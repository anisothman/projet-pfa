import base64

with open('reports/diagnostic_samsung_20260412_013842.pdf', 'rb') as f:
    data = base64.b64encode(f.read()).decode()

with open('frontend/src/pdf_data.ts', 'w') as f:
    f.write(f'export const PDF_DATA = "{data}";')

print('Fichier pdf_data.ts créé !')