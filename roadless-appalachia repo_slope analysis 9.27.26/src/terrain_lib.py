"""Shared terrain routines: windowed reads of USGS 3DEP 1/3 arc-second tiles, Horn slope, per-polygon slope histograms.

Pixel ownership rule: a pixel is counted in a tile only if its centre lies inside that tile's nominal 1x1 degree box
(3DEP tiles carry overlap margins), so no pixel is double counted across tiles.
"""
import os, pickle, pathlib
import numpy as np
import rasterio
from rasterio import features
from rasterio.windows import from_bounds, Window
from shapely.geometry import box

os.environ.setdefault("GDAL_HTTP_CAINFO", "/root/.ccr/ca-bundle.crt")
os.environ.setdefault("CURL_CA_BUNDLE", "/root/.ccr/ca-bundle.crt")
BASE = "/vsicurl/https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current"
M_PER_DEG_LAT = 110574.0
M_PER_DEG_LON_EQ = 111320.0
ACRE_M2 = 4046.8564224
SLOPE_HIST_EDGES = np.arange(0, 205, 5.0)          # percent slope, 5-point bins, last bin open-ended via clip
ELEV_EDGES = np.arange(0, 2200, 100.0)


def horn_slope_pct(z, dx, dy):
    """Horn (1981) slope in percent. dx is a per-row vector (m), dy scalar (m)."""
    zp = np.pad(z, 1, mode="edge")
    a, b, c = zp[:-2, :-2], zp[:-2, 1:-1], zp[:-2, 2:]
    d, f = zp[1:-1, :-2], zp[1:-1, 2:]
    g, h, i = zp[2:, :-2], zp[2:, 1:-1], zp[2:, 2:]
    dzdx = ((c + 2 * f + i) - (a + 2 * d + g)) / (8 * dx[:, None])
    dzdy = ((g + 2 * h + i) - (a + 2 * b + c)) / (8 * dy)
    return 100.0 * np.hypot(dzdx, dzdy)


def tile_name(lat_top, lon_west):
    return f"n{lat_top:02d}w{abs(lon_west):03d}"


def tiles_for(gdf):
    import math
    minx, miny, maxx, maxy = gdf.total_bounds
    out = []
    for lat in range(math.floor(miny) + 1, math.floor(maxy) + 2):
        for lon in range(math.floor(minx), math.floor(maxx) + 1):
            if gdf.intersects(box(lon, lat - 1, lon + 1, lat)).any():
                out.append(tile_name(lat, lon))
    return out


def process_tile(args):
    """args: (tile, gdf_subset(with 'pid'), cache_dir). Returns list of per-polygon-part records with slope/elev histograms."""
    t, sub, cache_dir = args
    cache = pathlib.Path(cache_dir) / f"{t}.pkl"
    if cache.exists():
        return pickle.load(open(cache, "rb"))
    lat, lon = int(t[1:3]), -int(t[4:7])
    recs = []
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MULTIRANGE="YES", VSI_CACHE="TRUE",
                      GDAL_CACHEMAX=256, GDAL_HTTP_MAX_RETRY=5, GDAL_HTTP_RETRY_DELAY=2):
        with rasterio.open(f"{BASE}/{t}/USGS_13_{t}.tif") as ds:
            res_x, res_y = ds.res
            pad = 3 * res_x
            for _, poly in sub.iterrows():
                minx, miny, maxx, maxy = poly.geometry.bounds
                minx, miny = max(minx, lon), max(miny, lat - 1)
                maxx, maxy = min(maxx, lon + 1), min(maxy, lat)
                if minx >= maxx or miny >= maxy:
                    continue
                w = from_bounds(minx - pad, miny - pad, maxx + pad, maxy + pad, ds.transform).round_offsets().round_lengths()
                w = w.intersection(Window(0, 0, ds.width, ds.height))
                z = ds.read(1, window=w, masked=True).astype("float32").filled(np.nan)
                tr = ds.window_transform(w)
                H, W = z.shape
                ys = tr.f + tr.e * (np.arange(H) + 0.5)
                xs = tr.c + tr.a * (np.arange(W) + 0.5)
                dx = res_x * M_PER_DEG_LON_EQ * np.cos(np.radians(ys))
                dy = res_y * M_PER_DEG_LAT
                zf = np.where(np.isnan(z), np.nanmean(z), z)
                slope = horn_slope_pct(zf, dx, dy)
                slope[np.isnan(z)] = np.nan
                m = features.rasterize([(poly.geometry, 1)], out_shape=(H, W), transform=tr, fill=0, dtype="uint8").astype(bool)
                m &= (xs[None, :] >= lon) & (xs[None, :] < lon + 1) & (ys[:, None] > lat - 1) & (ys[:, None] <= lat) & ~np.isnan(slope)
                if not m.any():
                    continue
                cell_acres = ((dx * dy) / ACRE_M2)[:, None] * np.ones((1, W))
                s_, e_, a_ = slope[m], z[m], cell_acres[m]
                sh, _ = np.histogram(np.clip(s_, 0, SLOPE_HIST_EDGES[-1] - 1e-6), bins=SLOPE_HIST_EDGES, weights=a_)
                eh, _ = np.histogram(np.clip(e_, 0, ELEV_EDGES[-1] - 1e-6), bins=ELEV_EDGES, weights=a_)
                recs.append({"pid": int(poly.pid), "tile": t, "acres_dem": float(a_.sum()), "acres_x_slope": float((a_ * s_).sum()),
                             "acres_x_elev": float((a_ * e_).sum()), "slope_hist": sh.astype("float32"), "elev_hist": eh.astype("float32")})
    pathlib.Path(cache_dir).mkdir(parents=True, exist_ok=True)
    pickle.dump(recs, open(cache, "wb"))
    return recs


def run(gdf, cache_dir, procs=2):
    """gdf must have unique integer column 'pid'. Returns dict pid -> aggregated arrays."""
    from multiprocessing import Pool
    tiles = tiles_for(gdf)
    jobs = []
    for t in tiles:
        lat, lon = int(t[1:3]), -int(t[4:7])
        sub = gdf[gdf.intersects(box(lon, lat - 1, lon + 1, lat))]
        jobs.append((t, sub, cache_dir))
    with Pool(procs) as p:
        results = []
        for i, r in enumerate(p.imap_unordered(process_tile, jobs)):
            results += r
            print(f"tile batch {i+1}/{len(jobs)} done", flush=True)
    agg = {}
    for r in results:
        a = agg.setdefault(r["pid"], {"acres_dem": 0.0, "acres_x_slope": 0.0, "acres_x_elev": 0.0,
                                      "slope_hist": np.zeros(len(SLOPE_HIST_EDGES) - 1), "elev_hist": np.zeros(len(ELEV_EDGES) - 1)})
        a["acres_dem"] += r["acres_dem"]; a["acres_x_slope"] += r["acres_x_slope"]; a["acres_x_elev"] += r["acres_x_elev"]
        a["slope_hist"] += r["slope_hist"]; a["elev_hist"] += r["elev_hist"]
    return agg
