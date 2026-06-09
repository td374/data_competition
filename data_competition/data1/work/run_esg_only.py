import pdfplumber, os, time, pandas as pd
from pathlib import Path

PDF_ROOTS = [
    r"C:\Users\28129\Desktop\共享1-数据收集与核对\钢铁财报与ESG",
    r"C:\Users\28129\Desktop\共享1-数据收集与核对\建材财报与ESG",
    r"C:\Users\28129\Desktop\共享1-数据收集与核对\data_competition\data1\cninfo_reports\巨潮年报或ESG_2019-2021",
]
OUT_DIR = r"C:\Users\28129\Documents\Codex\2026-06-02\files-mentioned-by-the-user-doc-4\work"

# Only ESG reports + small PDFs (<5MB)
all_pdfs = []
for root in PDF_ROOTS:
    if not os.path.exists(root):
        continue
    for pdf_path in Path(root).rglob("*.pdf"):
        sz = pdf_path.stat().st_size
        name = pdf_path.name.lower()
        is_esg = 'esg' in name or 'ESG' in pdf_path.name or '社会责任' in pdf_path.name or '环境' in pdf_path.name
        if sz < 5*1024*1024 and sz > 10000 and is_esg:
            all_pdfs.append((sz, str(pdf_path), pdf_path.name, root))
        elif sz < 5*1024*1024 and sz > 10000 and '年报' not in pdf_path.name and '年度报告' not in pdf_path.name:
            all_pdfs.append((sz, str(pdf_path), pdf_path.name, root))

all_pdfs.sort()
print(f"Found {len(all_pdfs)} ESG/small PDFs")

results = []
for i, (sz, pdf_path, name, root) in enumerate(all_pdfs):
    sz_mb = os.path.getsize(pdf_path)/1024/1024
    start = time.time()
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages = len(pdf.pages)
            t = "\n".join([pg.extract_text() or "" for pg in pdf.pages])
            chars = len(t.strip())
            scanned = chars < 100
            elapsed = time.time() - start
            print(f"[{i+1:3d}/{len(all_pdfs)}] {elapsed:4.1f}s {sz_mb:4.1f}MB {pages:3d}p {chars:7d}ch {'SCAN' if scanned else 'OK'} {name[:50]}")
            results.append({"file":name,"root":root,"path":pdf_path,"size_mb":round(sz_mb,1),
                          "pages":pages,"chars":chars,"scanned":scanned,"error":""})
    except Exception as e:
        print(f"[{i+1:3d}/{len(all_pdfs)}] ERROR: {str(e)[:60]}")
        results.append({"file":name,"root":root,"path":pdf_path,"size_mb":round(sz_mb,1),
                      "pages":0,"chars":0,"scanned":True,"error":str(e)[:200]})

df = pd.DataFrame(results)
manifest = os.path.join(OUT_DIR, "pdf_esg_manifest.csv")
df.to_csv(manifest, index=False, encoding="utf-8-sig")
ok = int((~df["scanned"]).sum())
print(f"\nDone: {len(results)} ESG PDFs, {ok} OK, {df['scanned'].sum()} scanned, {df['chars'].sum():,} chars total")
print(f"Saved: {manifest}")
