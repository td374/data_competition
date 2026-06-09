import pandas as pd, os, json

base = r"C:\Users\28129\Desktop\共享1-数据收集与核对\核验结果"
records = []

# 1. 核验.xlsx - 钢铁+建材
df1 = pd.read_excel(os.path.join(base, "核验.xlsx"), sheet_name="Sheet1")
for _, row in df1.iterrows():
    industry = str(row.iloc[0]).strip()
    group = str(row.iloc[1]).strip()
    code = str(row.iloc[2]).strip()
    name = str(row.iloc[3]).strip()
    if industry in ["钢铁", "建材"] and code.isdigit():
        records.append({"industry": industry, "group": group, "code": code, "name": name})

# 2. 有色、石化行业-绿色工厂核验表.xlsx
df2 = pd.read_excel(os.path.join(base, "有色、石化行业-绿色工厂核验表.xlsx"))
for _, row in df2.iterrows():
    industry = str(row.iloc[0]).strip()
    group = str(row.iloc[1]).strip()
    code = str(int(row.iloc[2])) if pd.notna(row.iloc[2]) else ""
    name = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ""
    if industry in ["有色行业", "有色", "石化行业", "石化"] and code.isdigit():
        ind = "有色" if "有色" in industry else "石化"
        records.append({"industry": ind, "group": group, "code": code, "name": name})

# 3. 航空与发电企业核对结果表.xlsx
xl3 = pd.ExcelFile(os.path.join(base, "航空与发电企业核对结果表.xlsx"))
for sname in ["航空", "电力"]:
    df3 = xl3.parse(sname)
    for _, row in df3.iterrows():
        group = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        code = str(int(row.iloc[1])) if pd.notna(row.iloc[1]) else ""
        name = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
        ind = "航空" if sname == "航空" else "发电"
        if code.isdigit():
            records.append({"industry": ind, "group": group, "code": code, "name": name})

df = pd.DataFrame(records)
# Deduplicate by code
df = df.drop_duplicates(subset=["code"])
print(f"Total companies: {len(df)}")
print(f"By industry: {df['industry'].value_counts().to_dict()}")
print(f"By group: {df['group'].value_counts().to_dict()}")

# Save
out = r"C:\Users\28129\Documents\Codex\2026-06-02\files-mentioned-by-the-user-doc-4\outputs\master_company_list.csv"
df.to_csv(out, index=False, encoding="utf-8-sig")
print(f"\nSaved to: {out}")
print(df.to_string())
