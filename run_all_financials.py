import sys, os, time
sys.path.insert(0, r"C:\Users\28129\Desktop\共享1-数据收集与核对\scripts")
os.chdir(r"C:\Users\28129\Desktop\共享1-数据收集与核对")
import batch_financials as bf
import pandas as pd

df = pd.read_csv(bf.MASTER_LIST, encoding="utf-8-sig")
df["symbol"] = df["code"].apply(bf.normalize_code)
valid = df[df["symbol"].str.match(r"^s[hz]\d{6}$")]
skipped = df[~df.index.isin(valid.index)]
print(f"Loaded {len(df)} companies, {len(valid)} valid, {len(skipped)} skipped")
for _, row in skipped.iterrows():
    print(f"  SKIP: {row['code']} - {row['name']}")

symbols = valid["symbol"].tolist()
print(f"\nStarting full batch: {len(symbols)} companies")
success, fail = 0, 0
for i, sym in enumerate(symbols):
    name = valid[valid["symbol"] == sym]["name"].values[0]
    print(f"\n[{i+1}/{len(symbols)}] {sym} {name}")
    results = bf.fetch_financials(sym, bf.OUTPUT_DIR)
    for k, v in results.items():
        print(f"  {k}: {v}")
    if all(not str(v).startswith("FAIL") for v in results.values()):
        success += 1
    else:
        fail += 1

sep = "=" * 50
print(f"\n{sep}")
print(f"DONE: {success} success, {fail} failed out of {len(symbols)}")
print(f"Output: {bf.OUTPUT_DIR}")
