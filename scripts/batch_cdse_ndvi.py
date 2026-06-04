# -*- coding: utf-8 -*-
"""
CDSE openEO Batch NDVI + NDWI Extraction - Async Batch Jobs
Uses rasterio for GeoTIFF output. No rate-limit issues. Resume-safe.
Requires: openeo, rasterio, pandas, numpy, matplotlib, pillow
"""
import openeo, rasterio, pandas as pd, numpy as np
import matplotlib;

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os, sys, time, warnings, json

warnings.filterwarnings("ignore")

ROOT = r"C:\Users\28129\Desktop\共享1-数据收集与核对"
OUT_DIR = os.path.join(ROOT, "data_competition", "data1", "geo_data")
TIF_DIR = os.path.join(OUT_DIR, "ndvi_chips")
PNG_DIR = os.path.join(OUT_DIR, "ndvi_previews")
os.makedirs(TIF_DIR, exist_ok=True)
os.makedirs(PNG_DIR, exist_ok=True)

COORDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "company_coordinates.csv")
RESULTS_CSV = os.path.join(OUT_DIR, "ndvi_results.csv")
BUFFER_DEG = 0.009;
YEARS = [2019, 2021];
CLOUD_MAX = 20

TOKEN_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cdse_tokens.json")
CLIENT_ID = "cdse-public"
REDIRECT_URI = "http://localhost:8080"
OIDC_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/.well-known/openid-configuration"
CDSE_BACKEND = "https://openeo.dataspace.copernicus.eu"


# ============================================================
def _get_oidc_config():
    import requests
    return requests.get(OIDC_URL, timeout=30).json()


def _refresh_access_token():
    """用本地缓存的 refresh_token 获取新 access_token，成功返回 token 否则 None"""
    import requests
    if not os.path.exists(TOKEN_CACHE):
        return None
    with open(TOKEN_CACHE, "r") as f:
        cached = json.load(f)
    rt = cached.get("refresh_token")
    if not rt:
        return None
    try:
        oidc = _get_oidc_config()
        resp = requests.post(oidc["token_endpoint"], data={
            "grant_type": "refresh_token",
            "refresh_token": rt,
            "client_id": CLIENT_ID,
        }, timeout=30)
        if resp.status_code == 200:
            tokens = resp.json()
            with open(TOKEN_CACHE, "w") as f:
                json.dump(tokens, f)
            return tokens["access_token"]
    except:
        pass
    return None


def _browser_login():
    """弹出浏览器登录，返回 tokens dict"""
    import requests, webbrowser, urllib.parse, http.server, threading, queue

    oidc = _get_oidc_config()
    token_url = oidc["token_endpoint"]
    auth_url = oidc["authorization_endpoint"]

    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid",
        "state": "cdse_auth",
    }
    login_url = auth_url + "?" + urllib.parse.urlencode(params)

    q = queue.Queue()

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            query = urllib.parse.parse_qs(parsed.query)
            q.put(query.get("code", [None])[0])
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Login OK. You may close this window.")

        def log_message(self, format, *args):
            pass

    server = http.server.HTTPServer(("localhost", 8080), Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    print("      Opening browser for login...")
    webbrowser.open(login_url)

    code = q.get(timeout=120)
    server.shutdown()

    if not code:
        raise RuntimeError("Login failed: no authorization code received")

    print("      Exchanging code for token...")
    token_resp = requests.post(token_url, data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
    }, timeout=30)
    token_resp.raise_for_status()
    try:
        return token_resp.json()
    except:
        print("      [ERROR] Token response was not valid JSON:")
        print("      " + token_resp.text[:500])
        raise


def _make_connection(access_token):
    """用 access_token 创建 openEO 连接，带重试"""
    import requests, time
    session = requests.Session()
    session.headers["Authorization"] = "Bearer " + access_token
    for attempt in range(3):
        try:
            conn = openeo.connect(CDSE_BACKEND, session=session)
            # 测试连接是否真的通了
            _ = conn.list_collections()
            return conn
        except Exception as e:
            print(f"      [WARN] Connection attempt {attempt + 1}/3 failed: {e}")
            if attempt < 2:
                time.sleep(5)
    raise RuntimeError("Failed to connect to CDSE after 3 attempts. Check VPN.")


# ============================================================
def connect_cdse():
    print("[1/4] Connecting to CDSE ...")

    # 先尝试用本地缓存静默刷新
    token = _refresh_access_token()
    if token:
        conn = _make_connection(token)
        print("      Connected (cached token refreshed)")
        print()
        return conn

    # 缓存不可用，弹浏览器登录
    tokens = _browser_login()
    with open(TOKEN_CACHE, "w") as f:
        json.dump(tokens, f)

    conn = _make_connection(tokens["access_token"])
    print("      Connected")
    print()
    return conn


def ensure_token_fresh(conn):
    """每 N 家公司调用一次，主动刷新 token"""
    token = _refresh_access_token()
    if token:
        try:
            conn._connection._session.headers["Authorization"] = "Bearer " + token
            print("      [INFO] Token proactively refreshed")
            return True
        except:
            pass
    return False


# ============================================================
def load_coords():
    df = pd.read_csv(COORDS_FILE, encoding="utf-8-sig").dropna(subset=["lat", "lon"])
    df["code"] = df["code"].apply(lambda x: str(int(x)).zfill(6))
    print("[2/4] Loaded {} companies".format(len(df)))
    print()
    return df


def _fail(code, year, idx, reason):
    return {"code": code, "year": year, "index": idx, "status": reason,
            "mean": None, "std": None, "min": None, "max": None,
            "p10": None, "p90": None, "valid_pixels": 0}


def _stats(tif_path, code, year, idx, png_path, cmap, cached=False):
    with rasterio.open(tif_path) as src:
        arr = src.read(1)
        nd = src.nodata
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
        vmin_, vmax_ = {"NDVI": (-0.2, 0.8), "NDWI": (-1.0, 1.0)}.get(idx, (-1.0, 1.0))
        plt.figure(figsize=(6, 6))
        plt.imshow(arr, cmap=cmap, vmin=vmin_, vmax=vmax_)
        plt.colorbar(label=idx)
        plt.title("{} {} {} mean={:.3f}{}".format(code, year, idx, m, tag))
        plt.axis("off");
        plt.savefig(png_path, dpi=100, bbox_inches="tight");
        plt.close()
    except:
        pass
    return s


def process_one(conn, row, year, idx):
    code = row["code"];
    lat, lon = float(row["lat"]), float(row["lon"])
    w, s = lon - BUFFER_DEG, lat - BUFFER_DEG;
    e, n = lon + BUFFER_DEG, lat + BUFFER_DEG
    tif = os.path.join(TIF_DIR, "{}_{}_{}.tif".format(code, year, idx.lower()))
    png = os.path.join(PNG_DIR, "{}_{}_{}.png".format(code, year, idx.lower()))
    cmap = {"NDVI": "RdYlGn", "NDWI": "Blues"}.get(idx, "RdYlGn")

    # Resume: skip if already downloaded
    if os.path.exists(tif) and os.path.getsize(tif) > 1000:
        return _stats(tif, code, year, idx, png, cmap, True)

    bands = ["B04", "B08"] if idx == "NDVI" else ["B03", "B08"]

    def _do_job(c):
        cube = c.load_collection(collection_id="SENTINEL2_L2A",
                                 spatial_extent={"west": w, "south": s, "east": e, "north": n},
                                 temporal_extent=["{}-06-01".format(year), "{}-08-31".format(year)],
                                 bands=bands, max_cloud_cover=CLOUD_MAX)
        if idx == "NDVI":
            result = cube.ndvi(nir="B08", red="B04")
        else:
            result = (cube.band("B03") - cube.band("B08")) / (cube.band("B03") + cube.band("B08"))
        reduced = result.reduce_temporal(reducer="median")
        job = reduced.create_job(title="{}_{}_{}".format(idx.lower(), code, year))
        print("    job {} ...".format(job.job_id), end=" ")
        job.start_and_wait()
        print("done", end=" ")
        job.get_results().download_file(tif)

    try:
        _do_job(conn)
        return _stats(tif, code, year, idx, png, cmap)
    except Exception as e:
        err = str(e)
        if "TokenInvalid" in err or "token has expired" in err or "403" in err:
            # 刷新 token 并重建连接重试
            new_token = _refresh_access_token()
            if new_token:
                try:
                    new_conn = _make_connection(new_token)
                    _do_job(new_conn)
                    return _stats(tif, code, year, idx, png, cmap)
                except Exception as e2:
                    return _fail(code, year, idx, "retry_failed: " + str(e2)[:180])
            else:
                return _fail(code, year, idx, "token_expired_no_refresh")
        return _fail(code, year, idx, err[:200])

def run(conn, df):
    results = [];
    total = len(df);
    indices = ["NDVI", "NDWI"]
    n_jobs = total * len(YEARS) * len(indices)
    print("[3/4] {} cos x {} yrs x {} idx = {} jobs (async batch)".format(
        total, len(YEARS), len(indices), n_jobs))
    print("      ~2 min/job, est ~{:.0f} hours".format(n_jobs * 2.5 / 60))
    print()
    ok = fail = 0
    for i, (_, row) in enumerate(df.iterrows()):
        # 每15家公司主动刷新一次 token
        if i > 0 and i % 15 == 0:
            ensure_token_fresh(conn)

        code = row["code"];
        name = row["name"][:25];
        ind = row["industry"];
        grp = row["group"]
        for year in YEARS:
            for idx_name in indices:
                tag = "[{:02d}/{}] {} {} {}".format(i + 1, total, code, year, idx_name)
                print("  {}  {}/{}  {}".format(tag, ind, grp, name), end=" ")
                r = process_one(conn, row, year, idx_name)
                r["name"] = row["name"];
                r["industry"] = ind;
                r["group"] = grp;
                results.append(r)
                if r["status"] in ("ok", "ok_cached"):
                    ok += 1; print("=> mean={:.4f}".format(r["mean"]))
                else:
                    fail += 1; print("=> {}".format(r["status"]))
                time.sleep(2)
        pd.DataFrame(results).to_csv(RESULTS_CSV, index=False, encoding="utf-8-sig")
        print("      [{}/{} ok, {} fail] saved".format(ok, (i + 1) * len(YEARS) * len(indices), fail))
        print()
    print()
    print("[4/4] Done. ok={}/{}".format(ok, len(results)))
    for r in results:
        if r["status"] not in ("ok", "ok_cached"):
            print("  FAIL {} {} {} {}".format(r["code"], r["year"], r["index"], r["status"]))
    return pd.DataFrame(results)


if __name__ == "__main__":
    print("=" * 60)
    print("  CDSE openEO - NDVI+NDWI Batch (async + rasterio)")
    print("=" * 60)
    run(connect_cdse(), load_coords())