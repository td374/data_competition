import pdfplumber, sys
sys.stdout.reconfigure(encoding='utf-8')
try:
    with pdfplumber.open(r'C:\Users\28129\Desktop\共享1-数据收集与核对\建材财报与ESG\2019北新建材ESG.pdf') as pdf:
        pages = len(pdf.pages)
        t = pdf.pages[0].extract_text() or ''
        c = len(t)
        print(f'  Pages={pages}, Page1_chars={c}')
        print(f'  First 150 chars: {t[:150]}')
except Exception as e:
    print(f'  ERROR: {e}')
