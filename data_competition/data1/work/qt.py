import pdfplumber, os, time
pdf = r"C:\Users\28129\Desktop\共享1-数据收集与核对\建材财报与ESG\2019中国巨石ESG.pdf"
sz = os.path.getsize(pdf)/1024
start = time.time()
with pdfplumber.open(pdf) as p:
    pages = len(p.pages)
    t = "\n".join([pg.extract_text() or "" for pg in p.pages])
elapsed = time.time() - start
out = f"File: {sz:.0f}KB\nPages: {pages}\nChars: {len(t)}\nTime: {elapsed:.1f}s\nFirst 200: {t[:200]}"
with open(r"C:\Users\28129\Documents\Codex\2026-06-02\files-mentioned-by-the-user-doc-4\work\quicktest.txt", "w", encoding="utf-8") as f:
    f.write(out)
