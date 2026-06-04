# -*- coding: utf-8 -*-
"""
Data Quality Check & Gap Report
Validates completeness of collected data and generates a summary report.
"""
import pandas as pd, os, json, glob
from pathlib import Path

MASTER = r"C:\Users\28129\Desktop\共享1-数据收集与核对\scripts\master_company_list.csv"
FIN_DIR = r"C:\Users\28129\Desktop\共享1-数据收集与核对\data_competition\data1\financial_data"
PDF_DIRS = [
    r"C:\Users\28129\Desktop\共享1-数据收集与核对\钢铁财报与ESG",
    r"C:\Users\28129\Desktop\共享1-数据收集与核对\建材财报与ESG",
    r"C:\Users\28129\Desktop\共享1-数据收集与核对\data_competition\data1\cninfo_reports\巨潮年报或ESG_2019-2021",
]
TEXT_MANIFEST = r"C:\Users\28129\Desktop\共享1-数据收集与核对\data_competition\data1\work\pdf_manifest.csv"
REPORT_OUT = r"C:\Users\28129\Desktop\共享1-数据收集与核对\scripts\data_quality_report.csv"

def check_financial_data():
    """Check financial data completeness per company."""
    master = pd.read_csv(MASTER, encoding="utf-8-sig")
    results = []
    
    for _, row in master.iterrows():
        code = str(row["code"]).zfill(6)
        name = row["name"]
        industry = row["industry"]
        group = row["group"]
        
        # Normalize code to AKShare format
        if code.startswith(('6','9')):
            symbol = f"sh{code}"
        else:
            symbol = f"sz{code}"
        
        company_dir = os.path.join(FIN_DIR, symbol)
        
        has_bs = has_pl = has_cf = False
        bs_rows = pl_rows = cf_rows = 0
        
        if os.path.exists(company_dir):
            for f in os.listdir(company_dir):
                if "balance" in f.lower():
                    has_bs = True
                    try:
                        df = pd.read_csv(os.path.join(company_dir, f))
                        bs_rows = len(df)
                    except:
                        pass
                elif "income" in f.lower():
                    has_pl = True
                    try:
                        df = pd.read_csv(os.path.join(company_dir, f))
                        pl_rows = len(df)
                    except:
                        pass
                elif "cash" in f.lower():
                    has_cf = True
                    try:
                        df = pd.read_csv(os.path.join(company_dir, f))
                        cf_rows = len(df)
                    except:
                        pass
        
        complete = has_bs and has_pl and has_cf
        results.append({
            "code": code, "name": name[:20], "industry": industry, "group": group,
            "fin_complete": complete,
            "fin_balance": has_bs, "fin_income": has_pl, "fin_cash": has_cf,
            "fin_bs_rows": bs_rows, "fin_pl_rows": pl_rows, "fin_cf_rows": cf_rows,
        })
    
    return pd.DataFrame(results)

def check_pdf_data():
    """Check PDF availability per company from directory scan."""
    master = pd.read_csv(MASTER, encoding="utf-8-sig")
    results = []
    
    # Build index of all PDF files
    pdf_index = {}
    for pdf_dir in PDF_DIRS:
        if not os.path.exists(pdf_dir):
            continue
        for pdf_path in Path(pdf_dir).rglob("*.pdf"):
            if pdf_path.stat().st_size > 10000:
                pdf_index[pdf_path.name] = str(pdf_path)
    
    for _, row in master.iterrows():
        code = str(row["code"]).zfill(6)
        name = str(row["name"])
        
        # Find PDFs matching this company
        matched_pdfs = []
        for pdf_name, pdf_path in pdf_index.items():
            # Match by stock code or company name keywords
            if code in pdf_name or any(kw in pdf_name for kw in name[:4].split()):
                matched_pdfs.append(pdf_name)
        
        has_esg_2019 = any("2019" in p and ("ESG" in p or "esg" in p or "社会责任" in p) for p in matched_pdfs)
        has_esg_2020 = any("2020" in p and ("ESG" in p or "esg" in p or "社会责任" in p) for p in matched_pdfs)
        has_esg_2021 = any("2021" in p and ("ESG" in p or "esg" in p or "社会责任" in p) for p in matched_pdfs)
        
        results.append({
            "code": code, "name": name[:20],
            "pdf_total": len(matched_pdfs),
            "pdf_esg_2019": has_esg_2019,
            "pdf_esg_2020": has_esg_2020,
            "pdf_esg_2021": has_esg_2021,
        })
    
    return pd.DataFrame(results)

def check_text_extraction():
    """Check text extraction quality from manifest."""
    if not os.path.exists(TEXT_MANIFEST):
        return pd.DataFrame()
    return pd.read_csv(TEXT_MANIFEST, encoding="utf-8-sig")

def generate_report():
    """Generate comprehensive data quality report."""
    print("="*60)
    print("  DATA QUALITY REPORT")
    print("="*60)
    
    # 1. Financial data
    print("\n[1] Financial Data (AKShare)")
    fin = check_financial_data()
    fin_complete = fin["fin_complete"].sum()
    print(f"  Complete: {fin_complete}/{len(fin)} ({fin_complete/len(fin)*100:.0f}%)")
    print(f"  By industry:")
    for ind in fin["industry"].unique():
        sub = fin[fin["industry"] == ind]
        print(f"    {ind}: {sub['fin_complete'].sum()}/{len(sub)}")
    
    # 2. PDF data
    print("\n[2] PDF Reports")
    pdf = check_pdf_data()
    pdf_total = pdf["pdf_total"].sum()
    print(f"  Total PDFs matched: {pdf_total}")
    esg_ok = pdf[(pdf["pdf_esg_2019"]) & (pdf["pdf_esg_2020"]) & (pdf["pdf_esg_2021"])]
    print(f"  Full ESG 2019-2021: {len(esg_ok)}/{len(pdf)}")
    
    # 3. Text extraction
    print("\n[3] Text Extraction Quality")
    text = check_text_extraction()
    if not text.empty:
        ok = int((~text["scanned"]).sum())
        scanned = int(text["scanned"].sum())
        print(f"  Extracted: {len(text)} PDFs")
        print(f"  OK: {ok} ({ok*100//len(text)}%)")
        print(f"  Scanned: {scanned} ({scanned*100//len(text)}%)")
        print(f"  Total chars: {text['chars'].sum():,}")
    
    # 4. Master list gaps
    print("\n[4] Company Coverage Gap Analysis")
    # Merge all checks
    merged = fin[["code", "name", "industry", "group", "fin_complete"]].copy()
    merged = merged.merge(pdf[["code", "pdf_total"]], on="code", how="left")
    
    # Flag gaps
    merged["gap"] = ""
    merged.loc[~merged["fin_complete"], "gap"] += "[财务缺]"
    merged.loc[merged["pdf_total"] == 0, "gap"] += "[PDF缺]"
    
    gaps = merged[merged["gap"] != ""]
    if len(gaps) > 0:
        print(f"  Companies with data gaps: {len(gaps)}")
        for _, r in gaps.iterrows():
            print(f"    {r['code']} {r['name']} {r['gap']}")
    else:
        print("  No data gaps detected!")
    
    # Save full report
    merged.to_csv(REPORT_OUT, index=False, encoding="utf-8-sig")
    print(f"\nFull report saved: {REPORT_OUT}")
    
    return merged

if __name__ == "__main__":
    report = generate_report()
