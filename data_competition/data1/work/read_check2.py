import pandas as pd, os

base = r"C:\Users\28129\Desktop\共享1-数据收集与核对\核验结果"

# Read each file and print key stats
for fname in os.listdir(base):
    if not fname.endswith('.xlsx'):
        continue
    path = os.path.join(base, fname)
    xl = pd.ExcelFile(path)
    print(f"\n{'='*60}")
    print(f"FILE: {fname}")
    print(f"Sheets: {xl.sheet_names}")
    for sname in xl.sheet_names:
        df = xl.parse(sname)
        dfc = df.dropna(how='all').dropna(axis=1, how='all')
        print(f"\n--- {sname}: {dfc.shape[0]} rows x {dfc.shape[1]} cols ---")
        # print first column values to get company names
        for ci, col in enumerate(dfc.columns[:4]):
            vals = dfc[col].dropna().unique()
            sample = vals[:10] if len(vals) > 10 else vals
            print(f"  Col{ci} [{col}]: {len(vals)} unique, sample={list(sample)}")
        # count by group if group column exists
        for col in dfc.columns:
            if '组' in str(col) or 'group' in str(col).lower():
                print(f"  GROUP counts: {dfc[col].value_counts().to_dict()}")
