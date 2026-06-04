# -*- coding: utf-8 -*-
"""
GEE Sentinel-2 NDVI/NDBI extraction - 75 companies x 2 years
Usage: python gee_remote_sensing.py --project YOUR_GCP_PROJECT_ID
"""
import ee, pandas as pd, numpy as np, os, sys, time, argparse, warnings
warnings.filterwarnings("ignore")

ROOT = r"C:\Users\28129\Desktop\共享1-数据收集与核对"
OUT_DIR = os.path.join(ROOT, "data_competition", "data1", "geo_data")
os.makedirs(OUT_DIR, exist_ok=True)

COORDS_FILE = os.path.join(os.path.dirname(__file__), "company_coordinates.csv")

def load_company_coords(csv_path=None):
    if csv_path is None:
        csv_path = COORDS_FILE
    df = pd.read_csv(csv_path, encoding="utf-8-sig").dropna(subset=["lat","lon"])
    coords = {}
    for _, row in df.iterrows():
        coords[str(row["code"])] = {
            "lat": float(row["lat"]), "lon": float(row["lon"]),
            "name": row["name"], "facility": row["facility"],
            "industry": row["industry"], "group": row["group"]
        }
    print(f"Loaded {len(coords)} companies from {csv_path}")
    return coords

def extract_indices(lat, lon, year, buffer_m=1000, cloud_max=20):
    point = ee.Geometry.Point([lon, lat])
    region = point.buffer(buffer_m)
    start = f"{year}-06-01"
    end = f"{year}-08-31"

    collection = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                  .filterBounds(point)
                  .filterDate(start, end)
                  .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_max))
                  .select(["B4","B8","B11","SCL"]))

    count = collection.size().getInfo()
    if count == 0:
        return {"ndvi_mean": None, "ndbi_mean": None, "image_count": 0, "error": "no images"}

    def add_indices(img):
        ndvi = img.normalizedDifference(["B8","B4"]).rename("NDVI")
        ndbi = img.normalizedDifference(["B11","B8"]).rename("NDBI")
        return img.addBands([ndvi, ndbi])

    composite = collection.map(add_indices).select(["NDVI","NDBI"]).median()

    try:
        stats = composite.reduceRegion(
            reducer=ee.Reducer.mean().combine(ee.Reducer.stdDev(),"",True),
            geometry=region, scale=10, maxPixels=1e9
        ).getInfo()
    except Exception as e:
        return {"ndvi_mean": None, "ndbi_mean": None, "image_count": count, "error": str(e)}

    return {
        "ndvi_mean": round(stats.get("NDVI_mean",0), 4),
        "ndvi_std":  round(stats.get("NDVI_stdDev",0), 4),
        "ndbi_mean": round(stats.get("NDBI_mean",0), 4),
        "ndbi_std":  round(stats.get("NDBI_stdDev",0), 4),
        "image_count": count
    }

def batch_extract(coords, years=[2019,2021], output_csv=None):
    if output_csv is None:
        output_csv = os.path.join(OUT_DIR, "sentinel2_indices.csv")
    results = []
    items = [(code, info) for code, info in coords.items()]
    total = len(items) * len(years)
    idx = 0

    for code, info in items:
        lat, lon = info["lat"], info["lon"]
        for year in years:
            idx += 1
            print(f"[{idx}/{total}] {code} {info['name'][:20]} {year} ({lat},{lon})...", end=" ", flush=True)
            r = extract_indices(lat, lon, year)
            r["code"] = code
            r["year"] = year
            r["name"] = info["name"]
            r["industry"] = info["industry"]
            r["group"] = info["group"]
            results.append(r)
            if r["ndvi_mean"] is not None:
                print(f"NDVI={r['ndvi_mean']:.4f} NDBI={r['ndbi_mean']:.4f} (n={r['image_count']})")
            else:
                print(f"SKIP: {r.get('error','?')}")
            time.sleep(0.3)

    df = pd.DataFrame(results)
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"\nSaved: {output_csv}")
    return df

def compute_change(df):
    df19 = df[df["year"]==2019].set_index("code")
    df21 = df[df["year"]==2021].set_index("code")
    ch = pd.DataFrame({
        "ndvi_2019": df19["ndvi_mean"], "ndvi_2021": df21["ndvi_mean"],
        "ndbi_2019": df19["ndbi_mean"], "ndbi_2021": df21["ndbi_mean"]
    })
    ch["ndvi_change"] = ch["ndvi_2021"] - ch["ndvi_2019"]
    ch["ndvi_change_pct"] = (ch["ndvi_change"] / ch["ndvi_2019"].abs() * 100).round(1)
    ch["ndbi_change"] = ch["ndbi_2021"] - ch["ndbi_2019"]
    ch["trend"] = "stable"
    ch.loc[ch["ndvi_change_pct"] > 10, "trend"] = "greening"
    ch.loc[ch["ndvi_change_pct"] < -10, "trend"] = "degrading"
    return ch.reset_index()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, help="GCP project ID with Earth Engine enabled")
    parser.add_argument("--years", default="2019,2021", help="Years to extract (comma-separated)")
    args = parser.parse_args()

    print("Initializing GEE...")
    ee.Initialize(project=args.project)
    print("OK")

    years = [int(y) for y in args.years.split(",")]
    coords = load_company_coords()
    df = batch_extract(coords, years)
    ch = compute_change(df)
    ch_path = os.path.join(OUT_DIR, "sentinel2_change.csv")
    ch.to_csv(ch_path, index=False, encoding="utf-8-sig")
    print(f"Change stats saved: {ch_path}")
    print(ch[["code","ndvi_2019","ndvi_2021","ndvi_change_pct","trend"]].to_string())
