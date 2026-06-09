import pandas as pd, os
xl = r"C:\Users\28129\Desktop\共享1-数据收集与核对\核验结果\最终企业样本名单.xlsx"
df = pd.read_excel(xl, header=None)
# Title row inspection
for i in range(min(6, len(df))):
    row = df.iloc[i]
    print("Row {}:".format(i))
    for j, v in enumerate(row):
        if pd.notna(v):
            print("  col{}: {}".format(j, v))
print("---")
print("Total rows:", len(df))
