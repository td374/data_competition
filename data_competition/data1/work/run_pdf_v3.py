import pdfplumber, os, time, json
from pathlib import Path

PDF_ROOTS = [
    r"C:\Users\28129\Desktop\共享1-数据收集与核对\钢铁财报与ESG",
    r"C:\Users\28129\Desktop\共享1-数据收集与核对\建材财报与ESG",
    r"C:\Users\28129\Desktop\共享1-数据收集与核对\data_competition\data1\cninfo_reports\巨潮年报或ESG_2019-2021",
]
OUT = r"C:\Users\28129\Documents\Codex\2026-06-02\files-mentioned-by-the-user-doc-4\work"
MANIFEST = os.path.join(OUT, "pdf_manifest.csv")
LOG = os.path.join(OUT, "pdf_log.txt")
MAX_MB = 15
os.makedirs(OUT, exist_ok=True)

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

with open(LOG, "w", encoding="utf-8") as log:
    log.write(f"Total PDFs: {len(all_pdfs)}\n")
    skipped = sum(1 for s,_,_,_ in all_pdfs if s > MAX_MB*1024*1024)
    log.write(f"Skipping >{MAX_MB}MB: {skipped}\n\n")

    results = []
    to_process = [(p,n,r) for s,p,n,r in all_pdfs if s <= MAX_MB*1024*1024]
    
    for i, (pdf_path, name, root) in enumerate(to_process):
        sz_mb = os.path.getsize(pdf_path)/1024/1024
        start = time.time()
        try:
            with pdfplumber.open(pdf_path) as pdf:
                pages = len(pdf.pages)
                t = "\n".join([pg.extract_text() or "" for pg in pdf.pages])
                chars = len(t.strip())
                scanned = chars < 100
                elapsed = time.time() - start
                line = f"[{i+1:3d}/{len(to_process)}] {elapsed:5.1f}s {sz_mb:5.1f}MB {pages:3d}p {chars:7d}ch {'SCAN' if scanned else 'OK  '} {name[:55]}"
                log.write(line + "\n")
                results.append({"file":name,"root":root,"path":pdf_path,"size_mb":round(sz_mb,1),
                              "pages":pages,"chars":chars,"scanned":scanned,"error":""})
        except Exception as e:
            elapsed = time.time() - start
            line = f"[{i+1:3d}/{len(to_process)}] {elapsed:5.1f}s {sz_mb:5.1f}MB ERROR {str(e)[:80]}"
            log.write(line + "\n")
            results.append({"file":name,"root":root,"path":pdf_path,"size_mb":round(sz_mb,1),
                          "pages":0,"chars":0,"scanned":True,"error":str(e)[:200]})
        log.flush()

    import pandas as pd
    df = pd.DataFrame(results)
    df.to_csv(MANIFEST, index=False, encoding="utf-8-sig")
    ok = int((~df["scanned"]).sum())
    scanned = int(df["scanned"].sum())
    log.write(f"\nDONE: {len(results)}, OK={ok}, SCANNED={scanned}, CHARS={df['chars'].sum():,}\n")

print("DONE")
