import akshare as ak, sys
sys.stdout.reconfigure(encoding='utf-8')
sym = 'sh600011'
print(f'Testing AKShare: {sym}')
try:
    df = ak.stock_balance_sheet_by_report_em(symbol=sym)
    print(f'Balance sheet: {df.shape[0]} rows, {df.shape[1]} cols')
    print(f'Dates: {df["REPORT_DATE"].min()} to {df["REPORT_DATE"].max()}')
    print(f'OK - AKShare works')
except Exception as e:
    print(f'FAIL: {e}')
