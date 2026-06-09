import pandas as pd, os

ROOT = r"C:\Users\28129\Desktop\共享1-数据收集与核对"
COORDS = os.path.join(ROOT, "scripts", "company_coordinates.csv")
EXCEL  = os.path.join(ROOT, "核验结果", "最终企业样本名单.xlsx")

coord = pd.read_csv(COORDS, encoding="utf-8-sig")
coord["c"] = coord["code"].apply(lambda x: str(int(x)).zfill(6))

xl = pd.read_excel(EXCEL, header=3).dropna(subset=["序号"])
xl["c"] = xl["股票代码"].apply(lambda x: str(int(x)).zfill(6) if pd.notna(x) else "")
xl_map = xl.set_index("c")

# Show mismatches
for _, row in coord.iterrows():
    c = row["c"]
    if c in xl_map.index:
        xl_grp = xl_map.loc[c, "组别"]
        xl_ind = xl_map.loc[c, "行业"]
        if row["group"] != xl_grp or row["industry"] != xl_ind:
            print("MISMATCH {}: coord({}/{}) -> xl({}/{})  {}".format(
                c, row["industry"], row["group"], xl_ind, xl_grp, row["name"][:25]))

# Fix: update group/industry from Excel
coord["industry"] = coord["c"].map(lambda c: xl_map.loc[c, "行业"] if c in xl_map.index else coord.loc[coord["c"]==c, "industry"].values[0])
coord["group"] = coord["c"].map(lambda c: xl_map.loc[c, "组别"] if c in xl_map.index else coord.loc[coord["c"]==c, "group"].values[0])

# Drop temp col and save
coord = coord.drop(columns=["c"])
coord.to_csv(COORDS, index=False, encoding="utf-8-sig")

# Verify counts
print("\nFinal groups:", coord["group"].value_counts().to_dict())
print("Final industries:", coord["industry"].value_counts().to_dict())
print("Total:", len(coord))
