# -*- coding: utf-8 -*-
"""
Batch financial indicator calculation - 75 companies x 12 indicators x 2019-2021.
Output: financial_indicators_wide.csv (one row per company-year, 12 cols)
"""
import pandas as pd, numpy as np, os, glob, warnings
warnings.filterwarnings("ignore")

DATA_DIR = r"C:\Users\28129\Desktop\共享1-数据收集与核对\data_competition\data1\financial_data"
OUT_DIR = r"C:\Users\28129\Desktop\共享1-数据收集与核对\data_competition\data1"
COORDS_FILE = r"C:\Users\28129\Desktop\共享1-数据收集与核对\scripts\company_coordinates.csv"

def calc_indicators(balance_path, income_path, cash_path, code=""):
    bs = pd.read_csv(balance_path); pl = pd.read_csv(income_path); cf = pd.read_csv(cash_path)
    for d in [bs, pl, cf]:
        if "REPORT_DATE" in d.columns: d["REPORT_DATE"] = pd.to_datetime(d["REPORT_DATE"])
    bs_a = bs[bs["REPORT_DATE"].dt.strftime("%m-%d") == "12-31"].copy()
    pl_a = pl[pl["REPORT_DATE"].dt.strftime("%m-%d") == "12-31"].copy()
    cf_a = cf[cf["REPORT_DATE"].dt.strftime("%m-%d") == "12-31"].copy()

    def sd(a, b): return a/b if b and b!=0 and pd.notna(a) and pd.notna(b) else np.nan

    records = []
    for _, b_row in bs_a.iterrows():
        year = b_row["REPORT_DATE"].year
        if year not in [2019, 2020, 2021]: continue
        p_rows = pl_a[pl_a["REPORT_DATE"].dt.year == year]
        c_rows = cf_a[cf_a["REPORT_DATE"].dt.year == year]
        if len(p_rows)==0 or len(c_rows)==0: continue
        p_row = p_rows.iloc[0]; c_row = c_rows.iloc[0]

        ta = b_row.get("TOTAL_ASSETS", np.nan); tl = b_row.get("TOTAL_LIABILITIES", np.nan)
        ca = b_row.get("TOTAL_CURRENT_ASSETS", np.nan); cl = b_row.get("TOTAL_CURRENT_LIAB", np.nan)
        inv = b_row.get("INVENTORY", np.nan); ar = b_row.get("NOTE_ACCOUNTS_RECE", np.nan)
        re = b_row.get("SURPLUS_RESERVE", np.nan); equity = b_row.get("TOTAL_EQUITY", np.nan)
        wc = ca-cl if pd.notna(ca) and pd.notna(cl) else np.nan
        rev = p_row.get("OPERATE_INCOME", np.nan); ebit = p_row.get("TOTAL_PROFIT", np.nan)
        ni = p_row.get("NETPROFIT", np.nan); ocf = c_row.get("NETCASH_OPERATE", np.nan)

        x1 = sd(wc,ta); x2 = sd(re,ta); x3 = sd(ebit,ta); x4 = sd(equity,tl); x5 = sd(rev,ta)
        z = 1.2*x1+1.4*x2+3.3*x3+0.6*x4+0.999*x5 if all(pd.notna(v) for v in [x1,x2,x3,x4,x5]) else np.nan

        records.append({"code":code, "year":year,
            "z_score": round(z,4) if pd.notna(z) else None,
            "current_ratio": round(sd(ca,cl),4), "debt_ratio": round(sd(tl,ta),4),
            "roa": round(sd(ni,ta),6), "roe": round(sd(ni,equity),6),
            "asset_turnover": round(sd(rev,ta),4), "ocf_ratio": round(sd(ocf,cl),4),
            "ocf_to_debt": round(sd(ocf,tl),4), "inv_turnover": round(sd(rev,inv),4),
            "ar_turnover": round(sd(rev,ar),4), "profit_margin": round(sd(ni,rev),6),
            "ocf_to_ni": round(sd(ocf,abs(ni)) if pd.notna(ni) and ni!=0 else np.nan, 4),
        })
    return records

def find_files(subdir):
    files = glob.glob(os.path.join(subdir, "*.csv"))
    bs = next((f for f in files if "balance" in f.lower()), None)
    pl = next((f for f in files if "income" in f.lower()), None)
    cf = next((f for f in files if "cash" in f.lower()), None)
    return bs, pl, cf

def get_code_from_dir(dirname):
    # "sh600011" -> "600011"
    for prefix in ["sh","sz","bj"]:
        if dirname.startswith(prefix): return dirname[len(prefix):]
    return dirname

if __name__ == "__main__":
    all_records = []
    subdirs = [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]
    print("Processing {} company directories...".format(len(subdirs)))

    for d in sorted(subdirs):
        code = get_code_from_dir(d)
        bs, pl, cf = find_files(os.path.join(DATA_DIR, d))
        if not all([bs, pl, cf]):
            print("  SKIP {}: missing files".format(d))
            continue
        try:
            records = calc_indicators(bs, pl, cf, code=code)
            all_records.extend(records)
            print("  {} OK: {} years".format(code, len(records)))
        except Exception as e:
            print("  {} FAIL: {}".format(code, e))

    df = pd.DataFrame(all_records)
    print("\nTotal: {} rows, {} companies".format(len(df), df["code"].nunique()))

    # Save long-format
    df.to_csv(os.path.join(OUT_DIR, "financial_indicators.csv"), index=False, encoding="utf-8-sig")

    # Also pivot to wide: one row per company, cols = {indicator}_{year}
    df_wide = df.pivot(index="code", columns="year", values=[
        "z_score","current_ratio","debt_ratio","roa","roe","asset_turnover",
        "ocf_ratio","ocf_to_debt","inv_turnover","ar_turnover","profit_margin","ocf_to_ni"])
    df_wide.columns = ["{}_{}".format(c[1], c[0]) for c in df_wide.columns]
    df_wide.to_csv(os.path.join(OUT_DIR, "financial_indicators_wide.csv"), encoding="utf-8-sig")

    print("Saved: financial_indicators.csv + financial_indicators_wide.csv")
    print("Sample:\n", df.head(6).to_string())