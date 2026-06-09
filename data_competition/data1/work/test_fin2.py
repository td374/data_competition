import pandas as pd, numpy as np, os, warnings
warnings.filterwarnings("ignore")

DATA_DIR = r"C:\Users\28129\Desktop\共享1-数据收集与核对\data_competition\data1\financial_data"

files = os.listdir(DATA_DIR)
print(f"Files in financial_data: {files}")

# Load sh600011 data directly
bs = pd.read_csv(os.path.join(DATA_DIR, "sh600011_balance_sheet.csv"))
pl = pd.read_csv(os.path.join(DATA_DIR, "sh600011_income_statement.csv"))
cf = pd.read_csv(os.path.join(DATA_DIR, "sh600011_cash_flow.csv"))

print(f"Balance: {bs.shape}")
print(f"Income:  {pl.shape}")
print(f"Cash:    {cf.shape}")

# Check date range
bs["REPORT_DATE"] = pd.to_datetime(bs["REPORT_DATE"])
annual = bs[bs["REPORT_DATE"].dt.strftime("%m-%d")=="12-31"]
print(f"Annual reports: {len(annual)}, years: {sorted(annual['REPORT_DATE'].dt.year.unique())}")

# Explore column names
key_cols = []
for col in bs.columns:
    low = col.lower()
    if any(kw in low for kw in ["asset", "liabilit", "equity", "current", "inventor", "receiv", "retain", "profit"]):
        key_cols.append(col)

print(f"\nKey balance sheet columns found: {len(key_cols)}")
for c in key_cols[:15]:
    print(f"  {c}")

# Try actual computation
row = annual.iloc[-3]  # 3 years back
print(f"\nSample row (year {row['REPORT_DATE'].year}):")
for c in ["TOTAL_ASSETS", "TOTAL_LIABILITIES", "TOTAL_CURRENT_ASSETS", "TOTAL_CURRENT_LIABILITIES"]:
    if c in bs.columns:
        print(f"  {c} = {row[c]:,.0f}")

result = "sh600011 data validated - ready for indicator calculation"
with open(r"C:\Users\28129\Documents\Codex\2026-06-02\files-mentioned-by-the-user-doc-4\work\fin_test_result.txt", "w", encoding="utf-8") as f:
    f.write(result)
print(f"\n{result}")
