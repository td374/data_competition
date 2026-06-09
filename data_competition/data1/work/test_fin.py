import pandas as pd, numpy as np, os, warnings
warnings.filterwarnings("ignore")

DATA_DIR = r"C:\Users\28129\Desktop\共享1-数据收集与核对\data_competition\data1\financial_data"
OUT_DIR = r"C:\Users\28129\Documents\Codex\2026-06-02\files-mentioned-by-the-user-doc-4\work"

test_dir = os.path.join(DATA_DIR, "sh600011")
files = os.listdir(test_dir)

# Find the 3 statement files
bs_file = [f for f in files if "balance" in f.lower()][0]
pl_file = [f for f in files if "income" in f.lower()][0]
cf_file = [f for f in files if "cash" in f.lower()][0]

print(f"Balance: {bs_file}")
print(f"Income:  {pl_file}")
print(f"Cash:    {cf_file}")

bs = pd.read_csv(os.path.join(test_dir, bs_file))
pl = pd.read_csv(os.path.join(test_dir, pl_file))
cf = pd.read_csv(os.path.join(test_dir, cf_file))

print(f"\nBalance columns ({len(bs.columns)}): {list(bs.columns[:15])}")
print(f"Income columns ({len(pl.columns)}): {list(pl.columns[:15])}")
print(f"Cash columns ({len(cf.columns)}): {list(cf.columns[:15])}")

# Check date coverage
bs["REPORT_DATE"] = pd.to_datetime(bs["REPORT_DATE"])
years = bs[bs["REPORT_DATE"].dt.strftime("%m-%d")=="12-31"]["REPORT_DATE"].dt.year
print(f"\nAnnual report years: {list(years.unique()[-6:])}")

# Try computing a few indicators
latest = bs[bs["REPORT_DATE"].dt.strftime("%m-%d")=="12-31"].iloc[-3:]
print(f"\nLast 3 annual balance sheets:")
for _, row in latest.iterrows():
    yr = row["REPORT_DATE"].year
    # Try multiple column name patterns
    ta = row.get("TOTAL_ASSETS", row.get("ASSET_TOTAL", 0))
    tl = row.get("TOTAL_LIABILITIES", row.get("LIAB_TOTAL", 0))
    ca = row.get("TOTAL_CURRENT_ASSETS", row.get("CURR_ASSET_TOTAL", 0))
    cl = row.get("TOTAL_CURRENT_LIABILITIES", row.get("CURR_LIAB_TOTAL", 0))
    print(f"  {yr}: TA={ta} TL={tl} CA={ca} CL={cl}")

# Try the actual column names used by AKShare
print(f"\nSearching for key columns...")
for col in bs.columns:
    low = col.lower()
    if any(kw in low for kw in ["total_asset", "asset_total", "liabilit", "current_asset", "current_liab"]):
        val = bs[col].iloc[-3]
        print(f"  {col} = {val}")

result = f"Balance: {bs.shape}, Income: {pl.shape}, Cash: {cf.shape}"
with open(os.path.join(OUT_DIR, "test_fin_indicators.txt"), "w", encoding="utf-8") as f:
    f.write(result + "\nOK - sh600011 data loaded successfully")
print(f"\nResult: {result}")
