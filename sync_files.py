import pandas as pd, os
os.chdir(r'C:\Users\28129\Desktop\共享1-数据收集与核对')

# 1. Update master_company_list.csv
df = pd.read_excel(r'核验结果\最终企业样本名单.xlsx', header=None)
rows = []
for i in range(4, len(df)):
    r = df.iloc[i]
    rows.append({
        'industry': str(r[1]).strip(),
        'group': str(r[2]).strip(),
        'code': str(int(r[3])).zfill(6) if isinstance(r[3],(int,float)) else str(r[3]).strip().zfill(6),
        'name': str(r[4]).split('(')[0].strip()
    })

master = pd.DataFrame(rows)
master.to_csv(r'scripts\master_company_list.csv', index=False, encoding='utf-8-sig')
print(f'master_company_list.csv: {len(master)} companies')

# 2. Update groups in company_coordinates.csv  
coords = pd.read_csv(r'scripts\company_coordinates.csv', encoding='utf-8-sig', dtype={'code': str})
for _, row in master.iterrows():
    mask = coords['code'].astype(str).str.strip() == row['code'].strip()
    if mask.any():
        coords.loc[mask, 'group'] = row['group']
coords.to_csv(r'scripts\company_coordinates.csv', index=False, encoding='utf-8-sig')
print(f'company_coordinates.csv: groups synced')

# 3. Verify counts
print(f'\nGroup distribution:')
print(master['group'].value_counts().to_string())
print(f'\nTotal: {len(master)}')
