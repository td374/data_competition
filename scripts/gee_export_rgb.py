# -*- coding: utf-8 -*-
"""
GEE Sentinel-2 True-Color Image Export
Exports 1km RGB chips for all 75 companies (2019 + 2021 summer).
Saves to Google Drive as GeoTIFF (for ResNet) + local PNG previews.

Usage: python gee_export_rgb.py --project YOUR_GCP_PROJECT_ID
"""
import ee, pandas as pd, os, sys, time, argparse, warnings
warnings.filterwarnings("ignore")

ROOT = r"C:\Users\28129\Desktop\共享1-数据收集与核对"
OUT_DIR = os.path.join(ROOT, "data_competition", "data1", "geo_data", "rgb_chips")
os.makedirs(OUT_DIR, exist_ok=True)

COORDS_FILE = os.path.join(os.path.dirname(__file__), "company_coordinates.csv")

# Sentinel-2 RGB bands (10m resolution)
RGB_BANDS = ["B4", "B3", "B2"]  # Red, Green, Blue
SCALE = 10  # meters per pixel
BUFFER = 500  # 500m radius = 1km x 1km chip

def load_coords(csv_path=None):
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
    print(f"Loaded {len(coords)} companies")
    return coords

def export_rgb_chip(code, info, year, drive_folder="sentinel2_rgb"):
    """Export a 1km RGB chip to Google Drive as GeoTIFF."""
    lat, lon = info["lat"], info["lon"]
    point = ee.Geometry.Point([lon, lat])
    region = point.buffer(BUFFER)
    
    start = f"{year}-06-01"
    end = f"{year}-08-31"
    
    collection = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                  .filterBounds(point)
                  .filterDate(start, end)
                  .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
                  .select(RGB_BANDS))
    
    count = collection.size().getInfo()
    if count == 0:
        print(f"  [{code}] {year}: NO IMAGES (cloud<20%)")
        return None
    
    # Median composite for cloud-free result
    composite = collection.median()
    
    # Visualize: brighten (Sentinel-2 values are 0-10000, divide by 10000 for reflectance)
    vis_params = {
        "min": 0,
        "max": 3000,  # Adjust for brightness
        "gamma": 1.4
    }
    
    # Export to Google Drive
    filename = f"{code}_{info['industry']}_{info['group']}_{year}"
    task = ee.batch.Export.image.toDrive(
        image=composite.visualize(**vis_params),
        description=filename,
        folder=drive_folder,
        fileNamePrefix=filename,
        scale=SCALE,
        region=region,
        maxPixels=1e9,
        fileFormat="GeoTIFF"
    )
    task.start()
    print(f"  [{code}] {year}: submitted (n={count} images) -> Drive/{drive_folder}/{filename}.tif")
    return task

def batch_export(coords, years=[2019, 2021], drive_folder="sentinel2_rgb"):
    """Export RGB chips for all companies."""
    results = []
    items = [(code, info) for code, info in coords.items()]
    total = len(items)
    
    for i, (code, info) in enumerate(items):
        print(f"[{i+1}/{total}] {code} {info['name'][:25]} ({info['industry']}/{info['group']})")
        for year in years:
            task = export_rgb_chip(code, info, year, drive_folder)
            results.append({
                "code": code, "name": info["name"], "year": year,
                "industry": info["industry"], "group": info["group"],
                "status": "submitted" if task else "no_images"
            })
            time.sleep(1)  # Rate limit
    
    # Save log
    log_path = os.path.join(OUT_DIR, "export_log.csv")
    pd.DataFrame(results).to_csv(log_path, index=False, encoding="utf-8-sig")
    print(f"\nLog saved: {log_path}")
    print(f"All tasks submitted. Check Google Drive folder: {drive_folder}")
    print(f"Monitor tasks: https://code.earthengine.google.com/tasks")
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, help="GCP project ID with Earth Engine enabled")
    parser.add_argument("--years", default="2019,2021", help="Years to export")
    parser.add_argument("--drive-folder", default="sentinel2_rgb", help="Google Drive folder name")
    args = parser.parse_args()
    
    print("Initializing GEE...")
    ee.Initialize(project=args.project)
    print("OK\n")
    
    years = [int(y) for y in args.years.split(",")]
    coords = load_coords()
    batch_export(coords, years, args.drive_folder)
