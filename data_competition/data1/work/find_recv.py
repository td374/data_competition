import pandas as pd

DATA_DIR = r"C:\Users\28129\Desktop\共享1-数据收集与核对\data_competition\data1\financial_data"
bs = pd.read_csv(f"{DATA_DIR}/sh600011_balance_sheet.csv")

# Find receivable columns
for c in bs.columns:
    low = c.lower()
    if any(kw in low for kw in ["receiv", "note_acc", "bill"]):
        print(f"  {c}")
