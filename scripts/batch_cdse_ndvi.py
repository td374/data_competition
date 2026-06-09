# -*- coding: utf-8 -*-
"""
CDSE openEO Batch NDVI + NDWI Extraction - Async Batch Jobs
Same simple approach as batch_cdse_rgb.py (authenticate_oidc, no custom auth).
Requires: openeo, rasterio, pandas, numpy, matplotlib
"""
import openeo, rasterio, pandas as pd, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os, time, warnings
warnings.filterwarnings("ignore")

ROOT = r"C:\Users\28129\Desktop\共享1-数据收集与核对"
OUT_DIR = os.path.join(ROOT, "data_competition", "data1", "geo_data")
TIF_DIR = os.path.join(OUT_DIR, "ndvi_chips")
PNG_DIR = os.path.join(OUT_DIR, "ndvi_previews")
os.makedirs(TIF_DIR, exist_ok=True)
os.makedirs(PNG_DIR, exist_ok=True)

COORDS_FILE = os.path.join(ROOT, "scripts", "company_coordinates.csv")
RESULTS_CSV = os.path.join(OUT_DIR, "ndvi_results.csv")
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

def _fail(code, year, idx, reason):
    return {"code": code, "year": year, "index": idx, "status": reason,
            "mean": None, "std": None, "min": None, "max": None,
            "p10": None, "p90": None, "valid_pixels": 0}

def _stats(tif_path, code, year, idx, png_path, cmap, cached=False):
    with rasterio.open(tif_path) as src:
        arr = src.read(1); nd = src.nodata
    vals = arr.flatten()
    if nd is not None and not (isinstance(nd, float) and np.isnan(nd)):
        vals = vals[vals != nd]
    vals = vals[~np.isnan(vals)]
    if len(vals) == 0: return _fail(code, year, idx, "all_nan")
    m = round(float(np.mean(vals)), 4)
    tag = " (cached)" if cached else ""
    s = {"code": code, "year": year, "index": idx, "mean": m,
         "std": round(float(np.std(vals)), 4),
         "min": round(float(np.min(vals)), 4),
         "max": round(float(np.max(vals)), 4),
         "p10": round(float(np.percentile(vals, 10)), 4),
         "p90": round(float(np.percentile(vals, 90)), 4),
         "valid_pixels": int(len(vals)),
         "status": "ok_cached" if cached else "ok"}
    try:
        vmin_, vmax_ = {"NDVI":(-0.2,0.8),"NDWI":(-1.0,1.0)}.get(idx, (-1.0,1.0))
        plt.figure(figsize=(6,6))
        plt.imshow(arr, cmap=cmap, vmin=vmin_, vmax=vmax_)
        plt.colorbar(label=idx)
        plt.title("{} {} {} mean={:.3f}{}".format(code, year, idx, m, tag))
        plt.axis("off"); plt.savefig(png_path, dpi=100, bbox_inches="tight"); plt.close()
    except: pass
    return s

def process_one(conn, row, year, idx):
    code = row["code"]; name = row["name"]
    lat, lon = float(row["lat"]), float(row["lon"])
    w, s = lon-BUFFER_DEG, lat-BUFFER_DEG; e, n = lon+BUFFER_DEG, lat+BUFFER_DEG
    tif = os.path.join(TIF_DIR, "{}_{}_{}.tif".format(code, year, idx.lower()))
    png = os.path.join(PNG_DIR, "{}_{}_{}.png".format(code, year, idx.lower()))
    cmap = {"NDVI":"RdYlGn","NDWI":"Blues"}.get(idx, "RdYlGn")

    if os.path.exists(tif) and os.path.getsize(tif) > 1000:
        return _stats(tif, code, year, idx, png, cmap, True)

    bands = ["B04","B08"] if idx=="NDVI" else ["B03","B08"]
    try:
        cube = conn.load_collection(collection_id="SENTINEL2_L2A",
            spatial_extent={"west":w,"south":s,"east":e,"north":n},
            temporal_extent=["{}-06-01".format(year),"{}-08-31".format(year)],
            bands=bands, max_cloud_cover=CLOUD_MAX)
        if idx=="NDVI": result = cube.ndvi(nir="B08", red="B04")
        else: result = (cube.band("B03")-cube.band("B08"))/(cube.band("B03")+cube.band("B08"))
        reduced = result.reduce_temporal(reducer="median")
        job = reduced.create_job(title="{}_{}_{}".format(idx.lower(), code, year))
        job.start_and_wait()
        job.get_results().download_file(tif)
        return _stats(tif, code, year, idx, png, cmap)
    except Exception as e:
        return _fail(code, year, idx, str(e)[:150])

def run(conn, df):
    results = []; total = len(df); indices = ["NDVI","NDWI"]
    n_jobs = total * len(YEARS) * len(indices)
    print("[3/3] {} cos x {} yrs x {} idx = {} jobs, est ~{:.0f}h\n".format(
        total, len(YEARS), len(indices), n_jobs, n_jobs*2.5/60))
    ok = fail = 0
    for i, (_, row) in enumerate(df.iterrows()):
        code = row["code"]; name = row["name"][:25]; ind = row["industry"]; grp = row["group"]
        for year in YEARS:
            for idx_name in indices:
                tag = "[{:02d}/{}] {} {} {}".format(i+1, total, code, year, idx_name)
                print("  {}  {}/{}  {}".format(tag, ind, grp, name), end=" ", flush=True)
                r = process_one(conn, row, year, idx_name)
                r["name"]=row["name"]; r["industry"]=ind; r["group"]=grp; results.append(r)
                if r["status"] in ("ok","ok_cached"): ok+=1; print("=> mean={:.4f}".format(r["mean"]))
                else: fail+=1; print("=> {}".format(r["status"]))
                time.sleep(2)
        pd.DataFrame(results).to_csv(RESULTS_CSV, index=False, encoding="utf-8-sig")
        print("      [{}/{} ok, {} fail] saved\n".format(ok, (i+1)*len(YEARS)*len(indices), fail))
    print("\nDone. ok={}/{}".format(ok, len(results)))
    for r in results:
        if r["status"] not in ("ok","ok_cached"):
            print("  FAIL {} {} {} {}".format(r["code"], r["year"], r["index"], r["status"]))

if __name__ == "__main__":
    print("="*60)
    print("  CDSE openEO - NDVI+NDWI Batch (async, simple auth)")
    print("="*60)
    run(connect_cdse(), load_coords())