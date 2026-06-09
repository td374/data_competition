import pandas as pd
xl = pd.read_excel(r"C:\Users\28129\Desktop\共享1-数据收集与核对\核验结果\最终企业样本名单.xlsx", header=3)
xl = xl.dropna(subset=["序号"])
xl["code6"] = xl["股票代码"].apply(lambda x: str(int(x)).zfill(6) if pd.notna(x) else "???")
for c in ["000488","600256","000554","002511"]:
    row = xl[xl["code6"]==c]
    if len(row):
        r = row.iloc[0]
        with open(r"C:\Users\28129\Desktop\共享1-数据收集与核对\scripts\_xl_info.txt", "a", encoding="utf-8") as f:
            f.write(f"\n{c}: industry={r['行业']} group={r['组别']} name={r['企业全称']}\n")
            f.write(f"   reason: {r['选取理由/入选依据']}\n")
    else:
        with open(r"C:\Users\28129\Desktop\共享1-数据收集与核对\scripts\_xl_info.txt", "a", encoding="utf-8") as f:
            f.write(f"\n{c}: NOT IN EXCEL\n")
print("Done")
