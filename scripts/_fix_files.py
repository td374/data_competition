import pandas as pd, os

ROOT = r"C:\Users\28129\Desktop\共享1-数据收集与核对"
COORDS = os.path.join(ROOT, "scripts", "company_coordinates.csv")
MASTER = os.path.join(ROOT, "scripts", "master_company_list.csv")
EXCEL  = os.path.join(ROOT, "核验结果", "最终企业样本名单.xlsx")

# ====== 1. Update coordinates CSV ======
df = pd.read_csv(COORDS, encoding="utf-8-sig")
print("Before:", len(df))

# Remove old
df = df[~df["code"].astype(str).str.zfill(6).isin(["000554", "002511"])]

# Add new: 000488 晨鸣纸业 - 寿光造纸基地
# Add new: 600256 广汇能源 - 哈密淖毛湖煤化工基地
new_rows = pd.DataFrame([
    {"seq": 0, "industry": "造纸", "group": "独立测试集", "code": "000488",
     "name": "山东晨鸣纸业集团股份有限公司", "facility": "晨鸣纸业寿光造纸基地",
     "lat": 36.88, "lon": 118.79, "city": "山东潍坊寿光",
     "coord_source": "Manual-research", "verified": "NEEDS-VERIFY"},
    {"seq": 0, "industry": "石化", "group": "独立测试集", "code": "600256",
     "name": "广汇能源股份有限公司", "facility": "广汇能源哈密淖毛湖煤化工基地",
     "lat": 43.99, "lon": 94.99, "city": "新疆哈密伊吾",
     "coord_source": "Manual-research", "verified": "NEEDS-VERIFY"},
])
df = pd.concat([df, new_rows], ignore_index=True)
# Re-number seq
df["seq"] = range(1, len(df)+1)
# Sort by industry then code
industry_order = {"发电":1,"钢铁":2,"建材":3,"有色":4,"石化":5,"化工":6,"造纸":7,"航空":8}
df["_sort"] = df["industry"].map(industry_order).fillna(9)
df = df.sort_values(["_sort","code"]).drop(columns=["_sort"])
df["seq"] = range(1, len(df)+1)

df.to_csv(COORDS, index=False, encoding="utf-8-sig")
print("After:", len(df))
print("Added: 000488, 600256 | Removed: 000554, 002511")

# ====== 2. Re-export master CSV from Excel ======
xl = pd.read_excel(EXCEL, header=3)
xl = xl.dropna(subset=["序号"])
# Clean: proper columns
xl_out = xl[["序号","行业","组别","股票代码","企业全称","绿色工厂资质","核验状态","选取理由/入选依据","核验批次/备注","修改记录"]].copy()
xl_out["股票代码"] = xl_out["股票代码"].apply(lambda x: str(int(x)).zfill(6) if pd.notna(x) else "")
xl_out.to_csv(MASTER, index=False, encoding="utf-8-sig")
print("Master CSV re-exported:", len(xl_out), "companies")

# ====== 3. Verify ======
verify = pd.read_csv(COORDS, encoding="utf-8-sig")
verify["c"] = verify["code"].apply(lambda x: str(int(x)).zfill(6))
codes = set(verify["c"])
print("\nFinal coord codes:", len(codes))
print("Contains 000488:", "000488" in codes)
print("Contains 600256:", "600256" in codes)
print("Removed 000554:", "000554" not in codes)
print("Removed 002511:", "002511" not in codes)
print("\nGroups:", verify["group"].value_counts().to_dict())
