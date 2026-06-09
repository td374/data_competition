import pandas as pd, os, sys
sys.stdout.reconfigure(encoding='utf-8')

base = r"C:\Users\28129\Desktop\共享1-数据收集与核对\核验结果"
for fname in os.listdir(base):
    if fname.endswith('.xlsx'):
        path = os.path.join(base, fname)
        try:
            dfs = pd.read_excel(path, sheet_name=None)
            for sname, df in dfs.items():
                df = df.dropna(how='all').dropna(axis=1, how='all')
                print(f"=== {fname} / sheet={sname} === shape={df.shape}")
                print(f"Columns: {list(df.columns)}")
                print(df.head(15).to_string())
                print()
        except Exception as e:
            print(f"{fname}: {e}")
