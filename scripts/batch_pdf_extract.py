# -*- coding: utf-8 -*-
"""
Batch PDF text extraction for ESG reports and annual reports
Uses pdfplumber for text-extractable PDFs, marks scanned PDFs for OCR
"""
import pdfplumber
import pandas as pd
import os, sys, json
from pathlib import Path

# Config
PDF_ROOTS = [
    r"C:\Users\28129\Desktop\共享1-数据收集与核对\钢铁财报与ESG",
    r"C:\Users\28129\Desktop\共享1-数据收集与核对\建材财报与ESG",
    r"C:\Users\28129\Desktop\共享1-数据收集与核对\data_competition\data1\cninfo_reports\巨潮年报或ESG_2019-2021",
]
OUTPUT_DIR = r"C:\Users\28129\Desktop\共享1-数据收集与核对\data_competition\data1\extracted_text"
MIN_TEXT_CHARS = 100  # PDFs with fewer chars are likely scanned


def extract_pdf_text(pdf_path):
    """Extract text from PDF, return (text, is_scanned, page_count)"""
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


def scan_pdfs(root_dir, output_dir):
    """Walk through directory, extract text from all PDFs"""
    results = []
    pdf_files = list(Path(root_dir).rglob("*.pdf"))
    pdf_files = [p for p in pdf_files if p.stat().st_size > 10000]  # skip tiny files
    
    print(f"Found {len(pdf_files)} PDFs in {root_dir}")
    
    for i, pdf_path in enumerate(pdf_files):
        rel = pdf_path.relative_to(root_dir)
        print(f"  [{i+1}/{len(pdf_files)}] {rel.name[:60]}...", end=" ")
        
        text, is_scanned, pages = extract_pdf_text(str(pdf_path))
        status = "SCANNED" if is_scanned else "OK"
        print(f"({pages}p, {len(text)} chars, {status})")
        
        results.append({
            "path": str(pdf_path),
            "relative": str(rel),
            "pages": pages,
            "chars": len(text) if isinstance(text, str) else 0,
            "scanned": is_scanned,
            "error": text if text.startswith("ERROR") else ""
        })
    
    return results


if __name__ == "__main__":
    all_results = []
    
    for root in PDF_ROOTS:
        if os.path.exists(root):
            print(f"\n{'='*60}")
            print(f"Processing: {root}")
            res = scan_pdfs(root, OUTPUT_DIR)
            all_results.extend(res)
        else:
            print(f"NOT FOUND: {root}")
    
    # Summary
    df = pd.DataFrame(all_results)
    total = len(df)
    scanned = df["scanned"].sum()
    total_chars = df["chars"].sum()
    errors = len(df[df["error"] != ""])
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {total} PDFs")
    print(f"  Text-extractable: {total - scanned} ({(total-scanned)/total*100:.0f}%)")
    print(f"  Scanned/need OCR: {scanned} ({scanned/total*100:.0f}%)")
    print(f"  Errors: {errors}")
    print(f"  Total chars extracted: {total_chars:,}")
    
    # Save manifest
    manifest_path = os.path.join(OUTPUT_DIR, "pdf_manifest.csv")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df.to_csv(manifest_path, index=False, encoding="utf-8-sig")
    print(f"\nManifest saved: {manifest_path}")
