import pandas as pd

DATA_DIR = r"C:\Users\28129\Desktop\共享1-数据收集与核对\data_competition\data1\financial_data"
pl = pd.read_csv(f"{DATA_DIR}/sh600011_income_statement.csv")
cf = pd.read_csv(f"{DATA_DIR}/sh600011_cash_flow.csv")

# Search for revenue-related columns in PL
print("=== Income Statement: revenue/profit columns ===")
for c in pl.columns:
    low = c.lower()
    if any(kw in low for kw in ["revenu", "operat", "profit", "income", "net"]):
        print(f"  {c}")

print("\n=== Cash Flow: operating cash columns ===")
for c in cf.columns:
    low = c.lower()
    if any(kw in low for kw in ["operat", "cash", "flow"]):
        print(f"  {c}")
