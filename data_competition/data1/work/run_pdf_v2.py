import pdfplumber, pandas as pd, os, sys, signal, time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, TimeoutError as FuturesTimeout

sys.stdout.reconfigure(encoding='utf-8')

PDF_ROOTS = [
    r"C:\Users\28129\Desktop\共享1-数据收集与核对\钢铁财报与ESG",
    r"C:\Users\28129\Desktop\共享1-数据收集与核对\建材财报与ESG",
    r"C:\Users\28129\Desktop\共享1-数据收集与核对\data_competition\data1\cninfo_reports\巨潮年报或ESG_2019-2021",
]
OUTPUT_DIR = r"C:\\Users\\28129\\Documents\\Codex\\2026-06-02\\files-mentioned-by-the-user-doc-4\\work\\extracted_text"
os.makedirs(OUTPUT_DIR, exist_ok=True)
MANIFEST = os.path.join(OUTPUT_DIR, "pdf_manifest.csv")
TIMEOUT_SEC = 60
MAX_SIZE_MB = 20

# Collect all PDFs sorted by size (small first)
all_pdfs = []
for root in PDF_ROOTS:
    if not os.path.exists(root):
        continue
    for pdf_path in Path(root).rglob("*.pdf"):
        sz = pdf_path.stat().st_size
        if sz < 10000:
            continue
        all_pdfs.append((sz, str(pdf_path), pdf_path.name, root))

all_pdfs.sort()
print(f"Total PDFs: {len(all_pdfs)}")
print(f"Skipping >{MAX_SIZE_MB}MB: {sum(1 for s,_,_,_ in all_pdfs if s > MAX_SIZE_MB*1024*1024)}")

# Process only up to MAX_SIZE_MB
to_process = [(p,n,r) for s,p,n,r in all_pdfs if s <= MAX_SIZE_MB*1024*1024]
print(f"Processing: {len(to_process)} PDFs")

results = []
for i, (pdf_path, name, root) in enumerate(to_process):
    sz_mb = os.path.getsize(pdf_path)/1024/1024
    print(f"[{i+1}/{len(to_process)}] {sz_mb:.1f}MB {name[:55]}", end=" ", flush=True)
    
    start = time.time()
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages_text = []
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    pages_text.append(t)
            full_text = "\n".join(pages_text)
            chars = len(full_text.strip())
            scanned = chars < 100
            elapsed = time.time() - start
            status = "SCAN" if scanned else "OK"
            print(f"-> {len(pdf.pages)}p {chars}ch {status} ({elapsed:.1f}s)")
            results.append({
                "file": name, "root": root, "path": pdf_path,
                "size_mb": round(sz_mb, 1), "pages": len(pdf.pages),
                "chars": chars, "scanned": scanned, "error": ""
            })
    except Exception as e:
        elapsed = time.time() - start
        print(f"-> ERROR ({elapsed:.1f}s): {str(e)[:80]}")
        results.append({
            "file": name, "root": root, "path": pdf_path,
            "size_mb": round(sz_mb, 1), "pages": 0,
            "chars": 0, "scanned": True, "error": str(e)[:200]
        })

# Save
df = pd.DataFrame(results)
df.to_csv(MANIFEST, index=False, encoding="utf-8-sig")

total = len(df)
ok = int((~df["scanned"]).sum())
scanned = int(df["scanned"].sum())
print(f"\nDONE: {total} PDFs, {ok} OK ({ok*100//total}%), {scanned} scanned")
print(f"Total chars: {df['chars'].sum():,}")
print(f"Manifest: {MANIFEST}")
