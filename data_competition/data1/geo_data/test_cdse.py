import openeo

# ============================================
# 1. 连接到 CDSE openEO 后端
# ============================================
print("正在连接 CDSE...")
url = "https://openeo.dataspace.copernicus.eu"
connection = openeo.connect(url)

# 认证（会弹出浏览器窗口，登录你的 CDSE 账号）
print("请在弹出的浏览器中登录 CDSE 账号...")
connection.authenticate_oidc()

print("✅ 连接成功！")

# ============================================
# 2. 定义研究区域（北京天安门附近）
# ============================================
west, south = 116.397, 39.908
east, north = 116.410, 39.916

# ============================================
# 3. 加载 Sentinel-2 L2A 数据
# ============================================
print("正在加载影像数据...")
datacube = connection.load_collection(
    collection_id="SENTINEL2_L2A",
    spatial_extent={"west": west, "south": south, "east": east, "north": north},
    temporal_extent=["2019-06-01", "2019-08-31"],
    bands=["B04", "B08"],           # 红波段和近红外波段
    max_cloud_cover=30,              # 云量低于30%
)

# ============================================
# 4. 计算 NDVI
# ============================================
print("正在计算 NDVI...")
ndvi_cube = datacube.ndvi(nir="B08", red="B04")

# ============================================
# 5. 下载结果（NetCDF 格式）
# ============================================
output_file = "beijing_ndvi_2019.nc"
print(f"正在下载结果到 {output_file}...")
ndvi_cube.download(output_file)

print(f"✅ 完成！NDVI 数据已保存到 {output_file}")