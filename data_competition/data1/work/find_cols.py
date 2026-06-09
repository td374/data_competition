import pandas as pd

DATA_DIR = r"C:\Users\28129\Desktop\共享1-数据收集与核对\data_competition\data1\financial_data"
bs = pd.read_csv(f"{DATA_DIR}/sh600011_balance_sheet.csv")
pl = pd.read_csv(f"{DATA_DIR}/sh600011_income_statement.csv")
cf = pd.read_csv(f"{DATA_DIR}/sh600011_cash_flow.csv")

# Find the exact column names we need
needed = {
    "total_assets": ["TOTAL_ASSETS", "ASSET_TOTAL"],
    "total_liabilities": ["TOTAL_LIABILITIES", "LIAB_TOTAL"],
    "current_assets": ["TOTAL_CURRENT_ASSETS", "CURR_ASSET_TOTAL"],
    "current_liabilities": ["TOTAL_CURRENT_LIABILITIES", "CURRENT_LIAB_BALANCE", "CURR_LIAB_TOTAL"],
    "inventory": ["INVENTORY", "INVENTORIES"],
    "accounts_receivable": ["ACCOUNTS_RECEIVABLE", "ACCT_RCV", "NOTE_ACCT_RCV"],
    "retained_earnings": ["RETAINED_EARNINGS", "RETAINED_PROFIT", "SURPLUS_RESERVE"],
    "equity": ["TOTAL_EQUITY", "EQUITY_TOTAL", "SHAREHOLDER_EQUITY"],
    "revenue": ["OPERATING_REVENUE", "TOTAL_OPERATE_REVENUE", "OPERATE_REVENUE", "BUSINESS_REVENUE"],
    "total_profit": ["TOTAL_PROFIT", "TOTAL_OPERATE_PROFIT", "OPERATE_PROFIT", "EBIT"],
    "net_profit": ["NET_PROFIT", "NET_INCOME", "NETPROFIT_MARGIN", "PARENT_NET_PROFIT"],
    "ocf": ["NET_CASH_FLOW_FROM_OPERATING", "NET_OPERATE_CASH_FLOW", "CASH_FLOW_FROM_OPERATING"],
}

print("=== AKShare Column Name Mapping ===")
for key, candidates in needed.items():
    found = []
    for df_name, df in [("BS", bs), ("PL", pl), ("CF", cf)]:
        for c in candidates:
            if c in df.columns:
                found.append(f"{df_name}.{c}")
    if found:
        print(f"  {key:25s} -> {found[0]}")
    else:
        # Search for closest match
        for df_name, df in [("BS", bs), ("PL", pl), ("CF", cf)]:
            matches = [c for c in df.columns if key.replace("_","")[:6] in c.lower().replace("_","")[:8]]
            if matches:
                print(f"  {key:25s} -> {df_name}.{matches[0]} (fuzzy)")
                break
        else:
            print(f"  {key:25s} -> NOT FOUND")
