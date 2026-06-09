# -*- coding: utf-8 -*-
"""剩余 41 家企业 RGB 真彩色补爬"""
import openeo, rasterio, pandas as pd, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os, time, traceback, warnings
warnings.filterwarnings("ignore")

ROOT = r"C:\Users\28129\Desktop\共享1-数据收集与核对"
TIF_DIR = os.path.join(ROOT, "data_competition", "data1", "geo_data", "rgb_chips")
PNG_DIR = os.path.join(ROOT, "data_competition", "data1", "geo_data", "rgb_previews")
os.makedirs(TIF_DIR, exist_ok=True)
os.makedirs(PNG_DIR, exist_ok=True)

COORDS_FILE = os.path.join(ROOT, "核验结果", "剩余企业厂区坐标_RGB.csv")
RESULTS_CSV = os.path.join(ROOT, "核验结果", "补爬结果_RGB.csv")
BUFFER_DEG = 0.009; YEARS = [2019, 2021]; CLOUD_MAX = 20

conn = openeo.connect("https://openeo.dataspace.copernicus.eu")
conn.authenticate_oidc()
print("Connected\n")

df = pd.read_csv(COORDS_FILE, encoding="utf-8-sig").dropna(subset=["lat","lon"])
df["code"] = df["code"].apply(lambda x: str(int(x)).zfill(6))
total = len(df); results = []; ok = fail = 0

print("{} companies, {} jobs\n".format(total, total*2))

for i, (_, row) in enumerate(df.iterrows()):
    code = row["code"]; name = row["name"][:25]; ind = row["industry"]; grp = row["group"]
    lat, lon = float(row["lat"]), float(row["lon"])
    west, south = lon-BUFFER_DEG, lat-BUFFER_DEG
    east, north = lon+BUFFER_DEG, lat+BUFFER_DEG

    for year in YEARS:
        tag = "[{:02d}/{}] {} {} RGB".format(i+1, total, code, year)
        print("  {}  {}/{}  {}".format(tag, ind, grp, name), end=" ")
        tif = os.path.join(TIF_DIR, "{}_{}_rgb.tif".format(code, year))
        png = os.path.join(PNG_DIR, "{}_{}_rgb.png".format(code, year))
        try:
            cube = conn.load_collection(collection_id="SENTINEL2_L2A",
                spatial_extent={"west":west,"south":south,"east":east,"north":north},
                temporal_extent=["{}-06-01".format(year),"{}-08-31".format(year)],
                bands=["B04","B03","B02"], max_cloud_cover=CLOUD_MAX)
            reduced = cube.reduce_temporal(reducer="median")
            job = reduced.create_job(title="rgb_{}_{}".format(code, year))
            job.start_and_wait()
            job.get_results().download_file(tif)
            # PNG preview
            try:
                with rasterio.open(tif) as src:
                    rgb = np.stack([src.read(1),src.read(2),src.read(3)], axis=-1).astype(np.float32)
                    rgb = np.clip(rgb, 0, 3000)
                    p2, p98 = np.percentile(rgb, (2, 98))
                    rgb = (rgb-p2)/max(p98-p2, 1); rgb = np.clip(rgb, 0, 1)
                plt.figure(figsize=(8,8)); plt.imshow(rgb)
                plt.title("{} {} RGB {}".format(code, name[:20], year))
                plt.axis("off"); plt.savefig(png, dpi=120, bbox_inches="tight"); plt.close()
            except: pass
            r = {"code":code,"name":row["name"],"year":year,"status":"ok"}
            ok+=1; print("OK")
        except Exception:
            err = traceback.format_exc().splitlines()[-1][:120]
            r = {"code":code,"name":row["name"],"year":year,"status":err}
            fail+=1; print("=> {}".format(err[:60]))
        results.append(r); time.sleep(2)
    pd.DataFrame(results).to_csv(RESULTS_CSV, index=False, encoding="utf-8-sig")
    print("      [{}/{} ok]\n".format(ok, (i+1)*2))

print("Done. ok={}/{}".format(ok, len(results)))