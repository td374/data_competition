import pandas as pd

xl = r"C:\Users\28129\Desktop\共享1-数据收集与核对\核验结果\最终企业样本名单.xlsx"
df_raw = pd.read_excel(xl, header=None)

# Write to file directly (avoid console encoding)
with open(r"C:\Users\28129\Desktop\共享1-数据收集与核对\scripts\_xl_dump.txt", "w", encoding="utf-8") as f:
    f.write("Total rows: {}\n\n".format(len(df_raw)))
    for i in range(min(8, len(df_raw))):
        f.write("--- Row {} ---\n".format(i))
        row = df_raw.iloc[i]
        for j, v in enumerate(row):
            if pd.notna(v):
                f.write("  col{}: {}\n".format(j, v))
    
    # Now parse data rows (row 3 = header, rows 4+ = data)
    # Filter data: col0 is numeric
    data_rows = []
    for i in range(4, len(df_raw)):
        val = df_raw.iloc[i, 0]
        if pd.notna(val):
            try:
                int(val)
                data_rows.append(i)
            except:
                pass
    
    f.write("\n--- Data rows: {} ---\n".format(len(data_rows)))
    
    # Count by group (col2)
    groups = {}
    industries = {}
    for r in data_rows:
        grp = str(df_raw.iloc[r, 2])
        ind = str(df_raw.iloc[r, 1])
        groups[grp] = groups.get(grp, 0) + 1
        industries[ind] = industries.get(ind, 0) + 1
    
    f.write("Groups:\n")
    for k, v in sorted(groups.items()): f.write("  {}: {}\n".format(k, v))
    f.write("Industries:\n")
    for k, v in sorted(industries.items()): f.write("  {}: {}\n".format(k, v))
    
    # List all codes
    codes = []
    for r in data_rows:
        code = df_raw.iloc[r, 3]
        codes.append(str(int(code)).zfill(6) if pd.notna(code) else "???")
    f.write("\nCodes ({}):\n".format(len(codes)))
    f.write(", ".join(codes))

print("Written to _xl_dump.txt")
