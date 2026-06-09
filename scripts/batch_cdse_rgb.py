# -*- coding: utf-8 -*-
"""
CDSE openEO Batch True-Color RGB Export - uses correct factory coordinates.
Same approach as batch_cdse_ndvi.py - CDSE async batch jobs, no VPN needed.
Requires: openeo, rasterio, pandas, numpy, matplotlib
"""
import openeo, rasterio, pandas as pd, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os, time, warnings
warnings.filterwarnings("ignore")

ROOT = r"C:\Users\28129\Desktop\共享1-数据收集与核对"
OUT_DIR = os.path.join(ROOT, "data_competition", "data1", "geo_data")
TIF_DIR = os.path.join(OUT_DIR, "rgb_chips")
PNG_DIR = os.path.join(OUT_DIR, "rgb_previews")
os.makedirs(TIF_DIR, exist_ok=True)
os.makedirs(PNG_DIR, exist_ok=True)

COORDS_FILE = os.path.join(ROOT, "scripts", "company_coordinates.csv")
RESULTS_CSV = os.path.join(OUT_DIR, "rgb_results.csv")
BUFFER_DEG = 0.009; YEARS = [2019, 2021]; CLOUD_MAX = 20

def connect_cdse():
    print("[1/3] Connecting to CDSE ...")
    conn = openeo.connect("https://openeo.dataspace.copernicus.eu")
    conn.authenticate_oidc()
    print("      Connected\n")
    return conn

def load_coords():
    df = pd.read_csv(COORDS_FILE, encoding="utf-8-sig").dropna(subset=["lat","lon"])
    df["code"] = df["code"].apply(lambda x: str(int(x)).zfill(6))
    print("[2/3] Loaded {} companies\n".format(len(df)))
    return df

def render_png(tif_path, png_path, code, name, year):
    try:
        with rasterio.open(tif_path) as src:
            rgb = np.stack([src.read(1), src.read(2), src.read(3)], axis=-1).astype(np.float32)
            rgb = np.clip(rgb, 0, 3000)
            p_low, p_high = np.percentile(rgb, (2, 98))
            rgb = (rgb - p_low) / max(p_high - p_low, 1)
            rgb = np.clip(rgb, 0, 1)
        plt.figure(figsize=(8,8))
        plt.imshow(rgb)
        plt.title("{} {} {}".format(code, name[:20], year))
        plt.axis("off"); plt.savefig(png_path, dpi=120, bbox_inches="tight"); plt.close()
    except: pass

def process_one(conn, row, year):
    code = row["code"]; name = row["name"]
    lat, lon = float(row["lat"]), float(row["lon"])
    w, s = lon-BUFFER_DEG, lat-BUFFER_DEG; e, n = lon+BUFFER_DEG, lat+BUFFER_DEG
    tif = os.path.join(TIF_DIR, "{}_{}_rgb.tif".format(code, year))
    png = os.path.join(PNG_DIR, "{}_{}_rgb.png".format(code, year))
    if os.path.exists(tif) and os.path.getsize(tif) > 1000:
        render_png(tif, png, code, name, year)
        return {"code": code, "name": name, "year": year, "status": "ok_cached"}
    try:
        cube = conn.load_collection(collection_id="SENTINEL2_L2A",
            spatial_extent={"west":w,"south":s,"east":e,"north":n},
            temporal_extent=["{}-06-01".format(year),"{}-08-31".format(year)],
            bands=["B04","B03","B02"], max_cloud_cover=CLOUD_MAX)
        reduced = cube.reduce_temporal(reducer="median")
        job = reduced.create_job(title="rgb_{}_{}".format(code, year))
        job.start_and_wait()
        job.get_results().download_file(tif)
        render_png(tif, png, code, name, year)
        return {"code": code, "name": name, "year": year, "status": "ok"}
    except Exception as e:
        return {"code": code, "name": name, "year": year, "status": str(e)[:150]}

def run(conn, df):
    results = []; total = len(df); n_jobs = total * len(YEARS)
    print("[3/3] {} cos x {} yrs = {} jobs, est ~{:.0f}h\n".format(total, len(YEARS), n_jobs, n_jobs*2.5/60))
    ok = fail = 0
    for i, (_, row) in enumerate(df.iterrows()):
        code = row["code"]; name = row["name"][:25]
        for year in YEARS:
            tag = "[{:02d}/{}] {} {} {}".format(i+1, total, code, name, year)
            print("  {}".format(tag), end=" ", flush=True)
            r = process_one(conn, row, year); results.append(r)
            if r["status"] in ("ok","ok_cached"): ok+=1; print("OK")
            else: fail+=1; print("FAIL: {}".format(r["status"]))
            time.sleep(2)
        pd.DataFrame(results).to_csv(RESULTS_CSV, index=False, encoding="utf-8-sig")
        print("      [{}/{} ok]\n".format(ok, i*2+2))
    print("\nDone. ok={}/{}".format(ok, len(results)))
    for r in results:
        if r["status"] not in ("ok","ok_cached"): print("  FAIL {} {}: {}".format(r["code"], r["year"], r["status"]))

if __name__ == "__main__":
    print("="*60)
    print("  CDSE openEO - True-Color RGB Batch (correct coords)")
    print("="*60)
    run(connect_cdse(), load_coords())