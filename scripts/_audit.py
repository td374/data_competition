import pandas as pd

# 1. Read Excel properly
xl = pd.read_excel(
    r"C:\Users\28129\Desktop\共享1-数据收集与核对\核验结果\最终企业样本名单.xlsx",
    header=3  # row 3 is the column header
)
xl = xl.dropna(subset=["序号"])
xl["code6"] = xl["股票代码"].apply(lambda x: str(int(x)).zfill(6) if pd.notna(x) else "???")
xl_codes = set(xl["code6"])
print("Excel: {} companies".format(len(xl)))
print("Groups:", xl["组别"].value_counts().to_dict())

# 2. Read coordinates CSV
coord = pd.read_csv(r"C:\Users\28129\Desktop\共享1-数据收集与核对\scripts\company_coordinates.csv")
coord["code6"] = coord["code"].apply(lambda x: str(int(x)).zfill(6))
coord_codes = set(coord["code6"])
print("\nCoords CSV: {} companies".format(len(coord)))

# 3. Read master CSV (raw export, skip title rows)
master = pd.read_csv(
    r"C:\Users\28129\Desktop\共享1-数据收集与核对\scripts\master_company_list.csv",
    header=None, skiprows=4
)
master.columns = ["序号","行业","组别","股票代码","企业全称","绿色工厂资质","核验状态","选取理由","核验批次","修改记录"]
master = master.dropna(subset=["序号"])
master["code6"] = master["股票代码"].apply(lambda x: str(int(x)).zfill(6) if pd.notna(x) else "???")
master_codes = set(master["code6"])
print("Master CSV: {} companies".format(len(master)))

# 4. Diff
print("\n=== DIFFS ===")
print("In Excel NOT in Coords:", sorted(xl_codes - coord_codes))
print("In Coords NOT in Excel:", sorted(coord_codes - xl_codes))
print("In Excel NOT in Master:", sorted(xl_codes - master_codes))
print("In Master NOT in Excel:", sorted(master_codes - xl_codes))

# 5. Show the diff companies
diff_codes = (xl_codes - coord_codes) | (coord_codes - xl_codes)
if diff_codes:
    print("\n--- Diff company details ---")
    for c in sorted(diff_codes):
        in_xl = c in xl_codes
        in_coord = c in coord_codes
        in_master = c in master_codes
        name = ""
        if in_xl:
            name = xl[xl["code6"]==c]["企业全称"].values[0]
        elif in_coord:
            name = coord[coord["code6"]==c]["name"].values[0]
        print("  {}  XL={} Coord={} Master={}  {}".format(c, in_xl, in_coord, in_master, name))

# 6. Check financial data dirs
import os
fin_dir = r"C:\Users\28129\Desktop\共享1-数据收集与核对\data_competition\data1\financial_data"
fin_dirs = set(os.listdir(fin_dir))
print("\n=== FINANCIAL DATA CHECK ===")
missing_fin = []
for c in sorted(xl_codes):
    found = False
    for prefix in ["sh","sz","bj"]:
        if prefix + c in fin_dirs:
            found = True; break
    if not found:
        missing_fin.append(c)
print("Missing financial data for {} companies:".format(len(missing_fin)))
for c in missing_fin:
    name = xl[xl["code6"]==c]["企业全称"].values[0] if c in xl_codes else "?"
    print("  {}  {}".format(c, name))
