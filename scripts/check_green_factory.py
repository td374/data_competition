# -*- coding: utf-8 -*-
"""
Green factory verification script
Cross-references master company list against MIIT green factory lists (batches 1-4)
"""
import pandas as pd, os

MASTER = r"C:\Users\28129\Desktop\共享1-数据收集与核对\scripts\master_company_list.csv"
GF_DIR = r"C:\Users\28129\Desktop\共享1-数据收集与核对\新建文件夹"
OUT = r"C:\Users\28129\Desktop\共享1-数据收集与核对\scripts\green_factory_check.csv"

# Load master list
master = pd.read_csv(MASTER, encoding="utf-8-sig")
print(f"Master: {len(master)} companies")

# Load all green factory batches
gf_all = []
for batch_file in ["第一批.xlsx", "第二批.xlsx", "第三批.xlsx", "第四批.xlsx"]:
    path = os.path.join(GF_DIR, batch_file)
    if os.path.exists(path):
        df = pd.read_excel(path)
        df["batch"] = batch_file.replace(".xlsx","")
        gf_all.append(df)
        print(f"  {batch_file}: {len(df)} factories")

gf = pd.concat(gf_all, ignore_index=True)
print(f"Total green factories: {len(gf)}")

# Search for matches: check if master company names appear in green factory lists
results = []
for _, row in master.iterrows():
    code = str(row["code"]).zfill(6)
    name = str(row["name"])
    industry = row["industry"]
    group = row["group"]
    
    # Search for company name in green factory lists
    matched = False
    matched_batches = []
    for _, gf_row in gf.iterrows():
        # Check all string columns for company name match
        for col in gf.columns:
            val = str(gf_row[col]) if pd.notna(gf_row[col]) else ""
            if len(name) >= 4 and name[:4] in val:
                matched = True
                batch = gf_row.get("batch", "")
                if batch and batch not in matched_batches:
                    matched_batches.append(str(batch))
    
    results.append({
        "industry": industry,
        "group": group,
        "code": code,
        "name": name,
        "in_green_factory": matched,
        "batches": ",".join(matched_batches) if matched_batches else ""
    })

result_df = pd.DataFrame(results)
result_df.to_csv(OUT, index=False, encoding="utf-8-sig")

found = result_df["in_green_factory"].sum()
print(f"\nGreen factory match: {found}/{len(result_df)}")
print(f"By group:")
for g in ["绿色", "争议", "棕色", "独立测试集", "标杆"]:
    subset = result_df[result_df["group"] == g]
    if len(subset) > 0:
        match = subset["in_green_factory"].sum()
        print(f"  {g}: {match}/{len(subset)} matched")
print(f"Saved: {OUT}")
