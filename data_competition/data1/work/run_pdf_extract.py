import pdfplumber, pandas as pd, os, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

PDF_ROOTS = [
    r"C:\Users\28129\Desktop\共享1-数据收集与核对\钢铁财报与ESG",
    r"C:\Users\28129\Desktop\共享1-数据收集与核对\建材财报与ESG",
    r"C:\Users\28129\Desktop\共享1-数据收集与核对\data_competition\data1\cninfo_reports\巨潮年报或ESG_2019-2021",
]
OUTPUT_DIR = r"C:\Users\28129\Desktop\共享1-数据收集与核对\data_competition\data1\extracted_text"
MIN_TEXT_CHARS = 100

def extract_pdf_text(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages_text = []
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    pages_text.append(t)
            full_text = "\n".join(pages_text)
            is_scanned = len(full_text.strip()) < MIN_TEXT_CHARS
            return full_text, is_scanned, len(pdf.pages)
    except Exception as e:
        return f"ERROR: {e}", True, 0

all_results = []
for root in PDF_ROOTS:
    if not os.path.exists(root):
        print(f"NOT FOUND: {root}")
        continue
    pdf_files = sorted(Path(root).rglob("*.pdf"))
    pdf_files = [p for p in pdf_files if p.stat().st_size > 10000]
    print(f"\n{root}")
    print(f"  PDFs: {len(pdf_files)}")
    for i, pdf_path in enumerate(pdf_files):
        rel = pdf_path.name
        text, scanned, pages = extract_pdf_text(str(pdf_path))
        chars = len(text) if isinstance(text, str) else 0
        status = "SCANNED" if scanned else "OK"
        pct = ""
        if chars > 500:
            pct = text[:80].replace('\n',' ')
        print(f"  [{i+1:3d}/{len(pdf_files)}] {status:7s} {pages:3d}p {chars:7d}ch  {rel[:60]}")
        if pct:
            print(f"         preview: {pct}...")
        all_results.append({
            "file": rel, "path": str(pdf_path), "root": root,
            "pages": pages, "chars": chars, "scanned": scanned
        })

df = pd.DataFrame(all_results)
os.makedirs(OUTPUT_DIR, exist_ok=True)
df.to_csv(os.path.join(OUTPUT_DIR, "pdf_manifest.csv"), index=False, encoding="utf-8-sig")

total = len(df)
scanned = int(df["scanned"].sum())
ok = total - scanned
print(f"\n{'='*50}")
print(f"DONE: {total} PDFs, {ok} OK ({ok*100//total}%), {scanned} scanned ({scanned*100//total}%)")
print(f"Total chars: {df['chars'].sum():,}")
print(f"Manifest: {OUTPUT_DIR}/pdf_manifest.csv")
