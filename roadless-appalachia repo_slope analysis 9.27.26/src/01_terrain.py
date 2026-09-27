"""Terrain metrics for core-Appalachian Inventoried Roadless Areas (IRAs).

Reads USGS 3DEP 1/3 arc-second DEM tiles remotely (windowed reads), computes Horn slope,
and tabulates, per IRA polygon, planimetric acres by percent-slope class plus elevation stats.
Pixel ownership rule: a pixel is counted in a tile only if its centre lies inside that tile's
nominal 1x1 degree box (3DEP tiles carry overlap margins), so no pixel is double counted.
"""
import os, json, sys, time
import numpy as np, pandas as pd, geopandas as gpd
import rasterio
from rasterio import features
from rasterio.windows import from_bounds, Window
from shapely.geometry import box

os.environ["GDAL_HTTP_CAINFO"] = "/root/.ccr/ca-bundle.crt"
os.environ["CURL_CA_BUNDLE"] = "/root/.ccr/ca-bundle.crt"
BASE = "/vsicurl/https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current"
M_PER_DEG_LAT = 110574.0
M_PER_DEG_LON_EQ = 111320.0
SLOPE_BINS_PCT = [0, 20, 35, 45, 60, 80, 1e9]   # percent slope; fine bins so thresholds can be varied later
ELEV_BINS_M = list(range(0, 2200, 100))

ira = gpd.read_file("data/processed/ira_core_appalachia.gpkg").reset_index(drop=True)
ira["pid"] = np.arange(1, len(ira) + 1)
tiles = json.load(open("data/processed/tiles_needed.json"))

def horn_slope_pct(z, dx, dy):
    """Horn (1981) slope in percent. z: 2D array; dx, dy: cell size (m), dx may be per-row vector."""
    zp = np.pad(z, 1, mode="edge")
    a, b, c = zp[:-2, :-2], zp[:-2, 1:-1], zp[:-2, 2:]
    d, f = zp[1:-1, :-2], zp[1:-1, 2:]
    g, h, i = zp[2:, :-2], zp[2:, 1:-1], zp[2:, 2:]
    dzdx = ((c + 2 * f + i) - (a + 2 * d + g)) / (8 * dx[:, None])
    dzdy = ((g + 2 * h + i) - (a + 2 * b + c)) / (8 * dy)
    return 100.0 * np.hypot(dzdx, dzdy)


import pickle, pathlib
pathlib.Path("data/processed/cache").mkdir(parents=True, exist_ok=True)
rows, elev_rows = [], []
t_start = time.time()
for t in tiles:
    cache = pathlib.Path(f"data/processed/cache/{t}.pkl")
    if cache.exists():
        r, e = pickle.load(open(cache, "rb")); rows += r; elev_rows += e
        print(f"{t} cached", flush=True); continue
    lat, lon = int(t[1:3]), -int(t[4:7])
    tilebox = box(lon, lat - 1, lon + 1, lat)
    sub = ira[ira.intersects(tilebox)]
    trow, telev = [], []
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MULTIRANGE="YES", VSI_CACHE="TRUE",
                      GDAL_CACHEMAX=256, GDAL_HTTP_MAX_RETRY=5, GDAL_HTTP_RETRY_DELAY=2):
        with rasterio.open(f"{BASE}/{t}/USGS_13_{t}.tif") as ds:
            res_x, res_y = ds.res
            pad = 3 * res_x
            for _, poly in sub.iterrows():
                minx, miny, maxx, maxy = poly.geometry.bounds
                minx, miny = max(minx, lon), max(miny, lat - 1); maxx, maxy = min(maxx, lon + 1), min(maxy, lat)
                if minx >= maxx or miny >= maxy: continue
                w = from_bounds(minx - pad, miny - pad, maxx + pad, maxy + pad, ds.transform).round_offsets().round_lengths()
                w = w.intersection(Window(0, 0, ds.width, ds.height))
                z = ds.read(1, window=w, masked=True).astype("float32").filled(np.nan)
                tr = ds.window_transform(w)
                H, W = z.shape
                ys = tr.f + tr.e * (np.arange(H) + 0.5); xs = tr.c + tr.a * (np.arange(W) + 0.5)
                dx = res_x * M_PER_DEG_LON_EQ * np.cos(np.radians(ys)); dy = res_y * M_PER_DEG_LAT
                zf = np.where(np.isnan(z), np.nanmean(z), z)
                slope = horn_slope_pct(zf, dx, dy); slope[np.isnan(z)] = np.nan
                m = features.rasterize([(poly.geometry, 1)], out_shape=(H, W), transform=tr, fill=0, dtype="uint8").astype(bool)
                m &= (xs[None, :] >= lon) & (xs[None, :] < lon + 1) & (ys[:, None] > lat - 1) & (ys[:, None] <= lat) & ~np.isnan(slope)
                if not m.any(): continue
                cell_acres = ((dx * dy) / 4046.8564224)[:, None] * np.ones((1, W))
                s_, e_, a_ = slope[m], z[m], cell_acres[m]
                cls = np.digitize(s_, SLOPE_BINS_PCT[1:-1])
                rec = {"pid": int(poly.pid), "tile": t, "acres_dem": float(a_.sum()), "acres_x_slope": float((a_ * s_).sum()),
                       "acres_x_elev": float((a_ * e_).sum()), "elev_min": float(e_.min()), "elev_max": float(e_.max())}
                for k in range(len(SLOPE_BINS_PCT) - 1):
                    rec[f"ac_slope_{k}"] = float(a_[cls == k].sum())
                trow.append(rec)
                eb = np.clip(np.digitize(e_, ELEV_BINS_M) - 1, 0, None)
                for k in np.unique(eb):
                    telev.append({"pid": int(poly.pid), "elev_bin_m": ELEV_BINS_M[k], "acres": float(a_[eb == k].sum())})
    pickle.dump((trow, telev), open(cache, "wb"))
    rows += trow; elev_rows += telev
    print(f"{t} done: {len(trow)} polygon-parts, {round(time.time()-t_start)} s elapsed", flush=True)

pd.DataFrame(rows).to_csv("data/processed/terrain_by_tile_polygon.csv", index=False)
pd.DataFrame(elev_rows).to_csv("data/processed/elev_hist_by_tile_polygon.csv", index=False)
ira.drop(columns="geometry").to_csv("data/processed/ira_attributes.csv", index=False)
print("finished", round(time.time() - t_start), "s")
