# -*- coding: utf-8 -*-
"""
Financial indicator calculation from AKShare CSVs.
Computes 12 financial early-warning indicators for 2019-2021.
Column names verified against real AKShare data (sh600011).
"""
import pandas as pd, numpy as np, os, glob, warnings
warnings.filterwarnings("ignore")

DATA_DIR = r"C:\Users\28129\Desktop\共享1-数据收集与核对\data_competition\data1\financial_data"
OUT_DIR = r"C:\Users\28129\Desktop\共享1-数据收集与核对\outputs"
os.makedirs(OUT_DIR, exist_ok=True)

def calc_indicators(balance_path, income_path, cash_path, code=""):
    """Calculate 12 financial indicators from 3 statements."""
    bs = pd.read_csv(balance_path)
    pl = pd.read_csv(income_path)
    cf = pd.read_csv(cash_path)
    
    for df in [bs, pl, cf]:
        if "REPORT_DATE" in df.columns:
            df["REPORT_DATE"] = pd.to_datetime(df["REPORT_DATE"])
    
    # Filter annual reports only
    bs_a = bs[bs["REPORT_DATE"].dt.strftime("%m-%d") == "12-31"].copy()
    pl_a = pl[pl["REPORT_DATE"].dt.strftime("%m-%d") == "12-31"].copy()
    cf_a = cf[cf["REPORT_DATE"].dt.strftime("%m-%d") == "12-31"].copy()
    
    records = []
    for _, b_row in bs_a.iterrows():
        year = b_row["REPORT_DATE"].year
        if year < 2017 or year > 2022:
            continue
        
        p_rows = pl_a[pl_a["REPORT_DATE"].dt.year == year]
        c_rows = cf_a[cf_a["REPORT_DATE"].dt.year == year]
        if len(p_rows) == 0 or len(c_rows) == 0:
            continue
        p_row = p_rows.iloc[0]
        c_row = c_rows.iloc[0]
        
        def safe_div(a, b):
            return a / b if b and b != 0 and pd.notna(a) and pd.notna(b) else np.nan
        
        # Verified AKShare column names
        ta = b_row.get("TOTAL_ASSETS", np.nan)
        tl = b_row.get("TOTAL_LIABILITIES", np.nan)
        ca = b_row.get("TOTAL_CURRENT_ASSETS", np.nan)
        cl = b_row.get("TOTAL_CURRENT_LIAB", np.nan)
        inv = b_row.get("INVENTORY", np.nan)
        ar = b_row.get("NOTE_ACCOUNTS_RECE", np.nan)
        re = b_row.get("SURPLUS_RESERVE", np.nan)
        equity = b_row.get("TOTAL_EQUITY", np.nan)
        wc = ca - cl if pd.notna(ca) and pd.notna(cl) else np.nan
        
        rev = p_row.get("OPERATE_INCOME", np.nan)
        ebit = p_row.get("TOTAL_PROFIT", np.nan)
        ni = p_row.get("NETPROFIT", np.nan)
        
        ocf = c_row.get("NETCASH_OPERATE", np.nan)
        
        # 12 Indicators
        x1 = safe_div(wc, ta)
        x2 = safe_div(re, ta)
        x3 = safe_div(ebit, ta)
        x4 = safe_div(equity, tl)
        x5 = safe_div(rev, ta)
        z_score = 1.2*x1 + 1.4*x2 + 3.3*x3 + 0.6*x4 + 0.999*x5 if all(pd.notna(v) for v in [x1,x2,x3,x4,x5]) else np.nan
        
        current_ratio = safe_div(ca, cl)
        debt_ratio = safe_div(tl, ta)
        roa = safe_div(ni, ta)
        roe = safe_div(ni, equity)
        asset_turnover = safe_div(rev, ta)
        ocf_ratio = safe_div(ocf, cl)
        ocf_to_debt = safe_div(ocf, tl)
        inv_turnover = safe_div(rev, inv)
        ar_turnover = safe_div(rev, ar)
        profit_margin = safe_div(ni, rev)
        ocf_to_ni = safe_div(ocf, abs(ni)) if pd.notna(ni) and ni != 0 else np.nan
        
        records.append({
            "code": code, "year": year,
            "z_score": round(z_score, 4) if pd.notna(z_score) else None,
            "current_ratio": round(current_ratio, 4) if pd.notna(current_ratio) else None,
            "debt_ratio": round(debt_ratio, 4) if pd.notna(debt_ratio) else None,
            "roa": round(roa, 6) if pd.notna(roa) else None,
            "roe": round(roe, 6) if pd.notna(roe) else None,
            "asset_turnover": round(asset_turnover, 4) if pd.notna(asset_turnover) else None,
            "ocf_ratio": round(ocf_ratio, 4) if pd.notna(ocf_ratio) else None,
            "ocf_to_debt": round(ocf_to_debt, 4) if pd.notna(ocf_to_debt) else None,
            "inv_turnover": round(inv_turnover, 4) if pd.notna(inv_turnover) else None,
            "ar_turnover": round(ar_turnover, 4) if pd.notna(ar_turnover) else None,
            "profit_margin": round(profit_margin, 6) if pd.notna(profit_margin) else None,
            "ocf_to_ni": round(ocf_to_ni, 4) if pd.notna(ocf_to_ni) else None,
        })
    return records

if __name__ == "__main__":
    # Test on sh600011
    bs_file = os.path.join(DATA_DIR, "sh600011_balance_sheet.csv")
    pl_file = os.path.join(DATA_DIR, "sh600011_income_statement.csv")
    cf_file = os.path.join(DATA_DIR, "sh600011_cash_flow.csv")
    
    if os.path.exists(bs_file):
        results = calc_indicators(bs_file, pl_file, cf_file, code="600011")
        df = pd.DataFrame(results)
        print(f"sh600011: {len(df)} years of indicators (2017-2022)")
        print(df.to_string())
        out = os.path.join(OUT_DIR, "test_financial_indicators.csv")
        df.to_csv(out, index=False, encoding="utf-8-sig")
        print(f"\nSaved: {out}")
    else:
        print("sh600011 data not found. Run batch_financials.py first.")
    
    print("\nReady for batch processing of all companies.")
