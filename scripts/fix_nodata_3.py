# -*- coding: utf-8 -*-
"""补爬 3 家 NoData 企业的 NDVI/NDWI —— 放宽云量+扩大时间窗口"""
import openeo, rasterio, pandas as pd, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os, warnings
warnings.filterwarnings("ignore")

ROOT = r"C:\Users\28129\Desktop\共享1-数据收集与核对"
TIF_DIR = os.path.join(ROOT, "data_competition", "data1", "geo_data", "ndvi_chips")
PNG_DIR = os.path.join(ROOT, "data_competition", "data1", "geo_data", "ndvi_previews")
os.makedirs(TIF_DIR, exist_ok=True)
os.makedirs(PNG_DIR, exist_ok=True)
OUT_CSV = os.path.join(ROOT, "核验结果", "nodata_3家_补爬结果.csv")

# Relaxed params
BUFFER_DEG = 0.009
YEARS = [2019, 2021]
CLOUD_MAX = 50       # 放宽到50%
MONTHS = (4, 10)     # 4-10月 (扩大窗口)

TARGETS = [
    ("600025", "华能澜沧江水电", 24.70, 100.09, "发电", "标杆"),
    ("600157", "永泰能源", 22.72, 114.67, "发电", "独立测试集"),
    ("000807", "云南铝业", 24.91, 102.82, "有色", "标杆"),
]

conn = openeo.connect("https://openeo.dataspace.copernicus.eu")
conn.authenticate_oidc()
print("Connected\n")

results = []
for code, name, lat, lon, ind, grp in TARGETS:
    w, s = lon-BUFFER_DEG, lat-BUFFER_DEG
    e, n = lon+BUFFER_DEG, lat+BUFFER_DEG
    for year in YEARS:
        for idx in ["NDVI","NDWI"]:
            tif = os.path.join(TIF_DIR, "{}_{}_{}.tif".format(code, year, idx.lower()))
            if os.path.exists(tif) and os.path.getsize(tif) > 1000:
                print("  {} {} {} SKIP (cached)".format(code, year, idx))
                continue
            bands = ["B04","B08"] if idx=="NDVI" else ["B03","B08"]
            try:
                cube = conn.load_collection(collection_id="SENTINEL2_L2A",
                    spatial_extent={"west":w,"south":s,"east":e,"north":n},
                    temporal_extent=["{}-{:02d}-01".format(year, MONTHS[0]), "{}-{:02d}-31".format(year, MONTHS[1])],
                    bands=bands, max_cloud_cover=CLOUD_MAX)
                if idx=="NDVI": result = cube.ndvi(nir="B08", red="B04")
                else: result = (cube.band("B03")-cube.band("B08"))/(cube.band("B03")+cube.band("B08"))
                reduced = result.reduce_temporal(reducer="median")
                job = reduced.create_job(title="fix_{}_{}_{}".format(idx.lower(), code, year))
                print("  {} {} {} job {} ...".format(code, year, idx, job.job_id), end=" ")
                job.start_and_wait()
                job.get_results().download_file(tif)
                # Quick stats
                with rasterio.open(tif) as src:
                    arr = src.read(1)
                    nd = src.nodata
                vals = arr.flatten()
                if nd is not None and not (isinstance(nd, float) and np.isnan(nd)):
                    vals = vals[vals != nd]
                vals = vals[~np.isnan(vals)]
                m = np.mean(vals) if len(vals) else 0
                print("OK mean={:.4f} n={}".format(m, len(vals)))
                results.append({"code":code,"name":name,"year":year,"index":idx,"mean":round(m,4),"n":len(vals),"status":"ok"})
            except Exception as e:
                print("FAIL: {}".format(str(e)[:100]))
                results.append({"code":code,"name":name,"year":year,"index":idx,"mean":None,"n":0,"status":str(e)[:150]})

pd.DataFrame(results).to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
print("\nDone. Results ->", OUT_CSV)