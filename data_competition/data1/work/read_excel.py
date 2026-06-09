import pandas as pd
import os, sys
sys.stdout.reconfigure(encoding='utf-8')

base = r"C:\Users\28129\Desktop\共享1-数据收集与核对\新建文件夹"
for fname in os.listdir(base):
    if fname.endswith('.xlsx'):
        path = os.path.join(base, fname)
        try:
            df = pd.read_excel(path)
            print(f"=== {fname} === shape={df.shape}")
            print(f"Columns: {list(df.columns)[:15]}")
            print(df.head(3))
            print()
        except Exception as e:
            print(f"{fname}: {e}")
