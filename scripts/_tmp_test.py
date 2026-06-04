import rasterio, numpy as np, os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = r"C:\Users\28129\Desktop\共享1-数据收集与核对"
NC_DIR = os.path.join(ROOT, "data_competition", "data1", "geo_data", "ndvi_chips")
PNG_DIR = os.path.join(ROOT, "data_competition", "data1", "geo_data", "ndvi_previews")
os.makedirs(PNG_DIR, exist_ok=True)

# Test with the existing GeoTIFF (named .nc but is TIFF)
tif = os.path.join(NC_DIR, "600011_2019_ndvi.nc")
with rasterio.open(tif) as src:
    print(f"Shape: {src.shape}, CRS: {src.crs}, nodata: {src.nodata}", flush=True)
    arr = src.read(1)
    vals = arr.flatten()
    vals = vals[vals != src.nodata] if src.nodata is not None else vals
    vals = vals[~np.isnan(vals)]
    print(f"NDVI mean={np.mean(vals):.4f} std={np.std(vals):.4f} n={len(vals)}", flush=True)

# Render PNG
plt.figure(figsize=(6,6))
plt.imshow(arr, cmap="RdYlGn", vmin=-0.2, vmax=0.8)
plt.colorbar(label="NDVI")
plt.title(f"600011 2019 NDVI mean={np.mean(vals):.3f}")
plt.axis("off")
png = os.path.join(PNG_DIR, "600011_2019_ndvi.png")
plt.savefig(png, dpi=100, bbox_inches="tight")
plt.close()
print(f"PNG saved: {os.path.getsize(png)} bytes", flush=True)