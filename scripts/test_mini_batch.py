import openeo, os, sys, time, traceback
ROOT = r'C:\Users\28129\Desktop\共享1-数据收集与核对'
OUT_DIR = os.path.join(ROOT, 'data_competition', 'data1', 'geo_data')
NC_DIR = os.path.join(OUT_DIR, 'ndvi_chips')
os.makedirs(NC_DIR, exist_ok=True)
BUFFER_DEG = 0.009

# Wait for any residual rate-limit to clear
print('Waiting 10s for rate-limit reset...', flush=True)
time.sleep(10)

conn = openeo.connect('https://openeo.dataspace.copernicus.eu')
conn.authenticate_oidc()
print('Connected', flush=True)

def download_with_retry(result, nc_path, max_retries=3):
    for attempt in range(max_retries):
        try:
            result.download(nc_path)
            return
        except Exception as e:
            if '429' in str(e) and attempt < max_retries - 1:
                wait = (attempt + 1) * 10
                print(f'(429 retry {attempt+1}/{max_retries-1} in {wait}s)', end=' ', flush=True)
                time.sleep(wait)
            else:
                raise

def process_one(code, lat, lon, year, index_name):
    w, s = lon - BUFFER_DEG, lat - BUFFER_DEG
    e, n = lon + BUFFER_DEG, lat + BUFFER_DEG
    nc_path = os.path.join(NC_DIR, f'{code}_{year}_{index_name.lower()}.nc')
    bands = ['B04', 'B08'] if index_name == 'NDVI' else ['B03', 'B08']
    cube = conn.load_collection(
        collection_id='SENTINEL2_L2A',
        spatial_extent={'west': w, 'south': s, 'east': e, 'north': n},
        temporal_extent=[f'{year}-06-01', f'{year}-08-31'],
        bands=bands, max_cloud_cover=20,
    )
    if index_name == 'NDVI':
        result = cube.ndvi(nir='B08', red='B04')
    else:
        result = (cube.band('B03') - cube.band('B08')) / (cube.band('B03') + cube.band('B08'))
    download_with_retry(result, nc_path)
    return os.path.getsize(nc_path)

companies = [('600011', 28.15, 121.28), ('600900', 30.83, 111.0)]
for code, lat, lon in companies:
    for year in [2019, 2021]:
        for idx in ['NDVI', 'NDWI']:
            print(f'{code} {year} {idx} ...', end=' ', flush=True)
            try:
                sz = process_one(code, lat, lon, year, idx)
                print(f'OK {sz}', flush=True)
            except Exception as e:
                print(f'FAIL: {type(e).__name__}: {str(e)[:120]}', flush=True)
            time.sleep(6)  # 6s between calls
print('DONE', flush=True)