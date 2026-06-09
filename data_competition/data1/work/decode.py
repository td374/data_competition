import pandas as pd

# Key: read 航空与发电核对结果表 with readable encoding
path = r"C:\Users\28129\Desktop\共享1-数据收集与核对\核验结果\航空与发电企业核对结果表.xlsx"
xl = pd.ExcelFile(path)

for sname in ["航空", "电力"]:
    df = xl.parse(sname)
    df = df.dropna(how='all')
    print(f"\n=== {sname}行业 ({len(df)}家) ===")
    for _, row in df.iterrows():
        code = row.iloc[1] if pd.notna(row.iloc[1]) else ""
        name = row.iloc[2] if pd.notna(row.iloc[2]) else ""
        reason = row.iloc[4] if len(row) > 4 and pd.notna(row.iloc[4]) else ""
        group = row.iloc[0] if pd.notna(row.iloc[0]) else ""
        print(f"  {group:6s} | {str(code):>8s} | {str(name)[:30]} | {str(reason)[:60]}")

# Read 核验.xlsx for steel+building materials
path2 = r"C:\Users\28129\Desktop\共享1-数据收集与核对\核验结果\核验.xlsx"
df2 = pd.read_excel(path2, sheet_name='Sheet1')
df2 = df2.dropna(how='all')
print(f"\n=== 钢铁+建材 核验 ({len(df2)}行) ===")
for _, row in df2.iterrows():
    industry = str(row.iloc[0])[:20] if pd.notna(row.iloc[0]) else ""
    group = str(row.iloc[1])[:10] if pd.notna(row.iloc[1]) else ""
    code = str(row.iloc[2])[:10] if pd.notna(row.iloc[2]) else ""
    name = str(row.iloc[3])[:30] if pd.notna(row.iloc[3]) else ""
    penalty = str(row.iloc[5])[:20] if len(row) > 5 and pd.notna(row.iloc[5]) else ""
    print(f"  {industry:8s} | {group:6s} | {code:>10s} | {name} | 处罚={penalty}")
