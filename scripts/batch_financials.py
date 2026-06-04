# -*- coding: utf-8 -*-
"""
Batch financial data collection via AKShare
Reads master_company_list.csv, fetches 3 financial statements for 2019-2021
"""
import akshare as ak
import pandas as pd
import os, sys, time

# Config
MASTER_LIST = r"C:\Users\28129\Desktop\共享1-数据收集与核对\scripts\master_company_list.csv"
OUTPUT_DIR = r"C:\Users\28129\Desktop\共享1-数据收集与核对\data_competition\data1\financial_data"
YEARS = [2019, 2020, 2021]
SLEEP_TIME = 1.5  # seconds between API calls to avoid rate limiting

def normalize_code(code):
    """Normalize stock code to AKShare format (sh600011 / sz000709)"""
    code = str(int(float(code))) if '.' in str(code) else str(code)
    code = code.zfill(6)
    if code.startswith(('6', '9')):
        return f"sh{code}"
    elif code.startswith(('0', '3', '2')):
        return f"sz{code}"
    else:
        return f"sh{code}"

def fetch_financials(symbol, output_dir):
    """Fetch 3 financial statements for a given stock symbol"""
    company_dir = os.path.join(output_dir, symbol)
    os.makedirs(company_dir, exist_ok=True)
    
    results = {}
    
    # Balance Sheet
    try:
        df_bs = ak.stock_balance_sheet_by_report_em(symbol=symbol)
        df_bs = df_bs.sort_values("REPORT_DATE", ascending=False)
        path = os.path.join(company_dir, f"{symbol}_balance_sheet.csv")
        df_bs.to_csv(path, index=False, encoding="utf-8-sig")
        results["balance_sheet"] = len(df_bs)
    except Exception as e:
        results["balance_sheet"] = f"FAIL: {e}"
    
    time.sleep(SLEEP_TIME)
    
    # Income Statement
    try:
        df_is_ = ak.stock_profit_sheet_by_report_em(symbol=symbol)
        df_is_ = df_is_.sort_values("REPORT_DATE", ascending=False)
        path = os.path.join(company_dir, f"{symbol}_income_statement.csv")
        df_is_.to_csv(path, index=False, encoding="utf-8-sig")
        results["income_statement"] = len(df_is_)
    except Exception as e:
        results["income_statement"] = f"FAIL: {e}"
    
    time.sleep(SLEEP_TIME)
    
    # Cash Flow
    try:
        df_cf = ak.stock_cash_flow_sheet_by_report_em(symbol=symbol)
        df_cf = df_cf.sort_values("REPORT_DATE", ascending=False)
        path = os.path.join(company_dir, f"{symbol}_cash_flow.csv")
        df_cf.to_csv(path, index=False, encoding="utf-8-sig")
        results["cash_flow"] = len(df_cf)
    except Exception as e:
        results["cash_flow"] = f"FAIL: {e}"
    
    return results

if __name__ == "__main__":
    df = pd.read_csv(MASTER_LIST, encoding="utf-8-sig")
    print(f"Loaded {len(df)} companies from master list")
    
    # Normalize codes
    df["symbol"] = df["code"].apply(normalize_code)
    
    # Filter out non-A-share codes (like 03323 which is HK)
    valid = df[df["symbol"].str.match(r"^s[hz]\d{6}$")]
    skipped = df[~df.index.isin(valid.index)]
    
    if len(skipped) > 0:
        print(f"Skipping {len(skipped)} non-A-share companies:")
        for _, row in skipped.iterrows():
            print(f"  {row['code']} - {row['name']}")
    
    # Quick test: fetch first 3 companies
    test_symbols = valid["symbol"].head(3).tolist()
    print(f"\nTesting with first 3 companies: {test_symbols}")
    
    for sym in test_symbols:
        name = valid[valid["symbol"] == sym]["name"].values[0]
        print(f"\n--- {sym} {name} ---")
        results = fetch_financials(sym, OUTPUT_DIR)
        for k, v in results.items():
            print(f"  {k}: {v}")
    
    print(f"\nFull batch: {len(valid)} companies ready")
    print(f"Output directory: {OUTPUT_DIR}")
    print("Run with --all flag to process all companies")
