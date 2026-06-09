# -*- coding: utf-8 -*-
"""剩余 45 家企业 NDVI/NDWI 补爬 —— 纯跑，无跳过检查"""
import openeo, rasterio, pandas as pd, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os, time, traceback, warnings
warnings.filterwarnings("ignore")

ROOT = r"C:\Users\28129\Desktop\共享1-数据收集与核对"
TIF_DIR = os.path.join(ROOT, "data_competition", "data1", "geo_data", "ndvi_chips")
PNG_DIR = os.path.join(ROOT, "data_competition", "data1", "geo_data", "ndvi_previews")
os.makedirs(TIF_DIR, exist_ok=True)
os.makedirs(PNG_DIR, exist_ok=True)

COORDS_FILE = os.path.join(ROOT, "核验结果", "剩余企业厂区坐标.csv")
RESULTS_CSV = os.path.join(ROOT, "核验结果", "补爬结果.csv")
BUFFER_DEG = 0.009; YEARS = [2019, 2021]; CLOUD_MAX = 20

NODATA_CODES = {"600025", "600157", "000807"}
NODATA_CLOUD = 50
NODATA_MONTHS = (4, 10)

conn = openeo.connect("https://openeo.dataspace.copernicus.eu")
conn.authenticate_oidc()
print("Connected\n")

df = pd.read_csv(COORDS_FILE, encoding="utf-8-sig").dropna(subset=["lat","lon"])
df["code"] = df["code"].apply(lambda x: str(int(x)).zfill(6))
total = len(df); results = []; ok = fail = 0

print("{} companies, {} jobs\n".format(total, total*4))

for i, (_, row) in enumerate(df.iterrows()):
    code = row["code"]; name = row["name"][:25]; ind = row["industry"]; grp = row["group"]
    lat, lon = float(row["lat"]), float(row["lon"])
    west, south = lon-BUFFER_DEG, lat-BUFFER_DEG
    east, north = lon+BUFFER_DEG, lat+BUFFER_DEG

    is_nodata = code in NODATA_CODES
    cloud = NODATA_CLOUD if is_nodata else CLOUD_MAX
    months = NODATA_MONTHS if is_nodata else (6, 8)

    for year in YEARS:
        for idx_name in ["NDVI","NDWI"]:
            tag = "[{:02d}/{}] {} {} {}".format(i+1, total, code, year, idx_name)
            print("  {}  {}/{}  {}".format(tag, ind, grp, name), end=" ")
            tif = os.path.join(TIF_DIR, "{}_{}_{}.tif".format(code, year, idx_name.lower()))
            png = os.path.join(PNG_DIR, "{}_{}_{}.png".format(code, year, idx_name.lower()))
            bands = ["B04","B08"] if idx_name=="NDVI" else ["B03","B08"]
            cmap = {"NDVI":"RdYlGn","NDWI":"Blues"}.get(idx_name, "RdYlGn")
            err_msg = ""
            try:
                cube = conn.load_collection(collection_id="SENTINEL2_L2A",
                    spatial_extent={"west":west,"south":south,"east":east,"north":north},
                    temporal_extent=["{}-{:02d}-01".format(year,months[0]),"{}-{:02d}-31".format(year,months[1])],
                    bands=bands, max_cloud_cover=cloud)
                if idx_name=="NDVI": res = cube.ndvi(nir="B08", red="B04")
                else: res = (cube.band("B03")-cube.band("B08"))/(cube.band("B03")+cube.band("B08"))
                reduced = res.reduce_temporal(reducer="median")
                job = reduced.create_job(title="{}_{}_{}".format(idx_name.lower(), code, year))
                job.start_and_wait()
                job.get_results().download_file(tif)
                with rasterio.open(tif) as src:
                    arr = src.read(1); nd = src.nodata
                vals = arr.flatten()
                if nd is not None and not (isinstance(nd, float) and np.isnan(nd)):
                    vals = vals[vals != nd]
                vals = vals[~np.isnan(vals)]
                m = float(np.mean(vals)) if len(vals) else float('nan')
                r = {"code":code,"name":row["name"],"year":year,"index":idx_name,
                     "mean":round(m,4),"n":len(vals),"status":"ok"}
                try:
                    vmin_,vmax_ = {"NDVI":(-0.2,0.8),"NDWI":(-1.0,1.0)}[idx_name]
                    plt.figure(figsize=(6,6)); plt.imshow(arr,cmap=cmap,vmin=vmin_,vmax=vmax_)
                    plt.colorbar(label=idx_name)
                    plt.title("{} {} {} mean={:.3f}".format(code,year,idx_name,m))
                    plt.axis("off"); plt.savefig(png,dpi=100,bbox_inches="tight"); plt.close()
                except: pass
                ok+=1; print("=> mean={:.4f}".format(m))
            except Exception:
                err_msg = traceback.format_exc().splitlines()[-1][:150]
                r = {"code":code,"name":row["name"],"year":year,"index":idx_name,
                     "mean":None,"n":0,"status":err_msg}
                fail+=1; print("=> {}".format(err_msg[:80]))
            results.append(r); time.sleep(2)
    pd.DataFrame(results).to_csv(RESULTS_CSV, index=False, encoding="utf-8-sig")
    print("      [{}/{} ok]\n".format(ok, (i+1)*4))

print("Done. ok={}/{}".format(ok, len(results)))