import pandas as pd

bs = pd.read_csv(r"C:\Users\28129\Desktop\共享1-数据收集与核对\data_competition\data1\financial_data\sh600011_balance_sheet.csv")
bs["REPORT_DATE"] = pd.to_datetime(bs["REPORT_DATE"])
annual = bs[bs["REPORT_DATE"].dt.strftime("%m-%d")=="12-31"]

# Check current liability columns
for col in ["CURRENT_LIAB_BALANCE", "TOTAL_CURRENT_LIABILITIES", "CURRENT_LIABILITIES"]:
    if col in bs.columns:
        vals = annual[col].head(5)
        print(f"{col}: {list(vals)}")
    else:
        print(f"{col}: NOT IN COLUMNS")

# Also check for any column with "current" and "liab"
for c in bs.columns:
    if "current" in c.lower() and "liab" in c.lower():
        print(f"FOUND: {c} = {list(annual[c].head(3))}")
