"""Joint slope x distance-to-nearest-road histograms per polygon (10 m DEM grid).

Same slope pipeline and pixel-ownership rule as terrain_lib.py. Distance to the nearest existing road (USGS TNM/TIGER roads +
USFS system roads) is computed with a Euclidean distance transform on a grid padded by PAD_PX beyond the DEM window, so roads
outside the DEM tile (or outside the polygon) up to ~3 km away are still seen. Distances > 3000 m fall in the last bin.
"""
import os, pickle, pathlib
import numpy as np
import geopandas as gpd
import rasterio
from affine import Affine
from rasterio import features
from rasterio.windows import from_bounds, Window
from scipy.ndimage import distance_transform_edt
from shapely.geometry import box
from shapely import STRtree
import terrain_lib as T

PAD_PX = 380
DIST_EDGES = np.arange(0, 3050, 50.0)               # 60 bins of 50 m; last bin also absorbs >3000 m
ROADS = None
TREE = None


def init_roads(path="data/processed/roads_study.gpkg", sources=None):
    global ROADS, TREE
    r = gpd.read_file(path)
    if sources is not None:
        r = r[r.mtfcc_code.isin(sources)]
    ROADS = r.geometry.values
    TREE = STRtree(ROADS)


def process_tile_joint(args):
    t, sub, cache_dir = args
    cache = pathlib.Path(cache_dir) / f"{t}.pkl"
    if cache.exists():
        return pickle.load(open(cache, "rb"))
    lat, lon = int(t[1:3]), -int(t[4:7])
    recs = []
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MULTIRANGE="YES", VSI_CACHE="TRUE",
                      GDAL_CACHEMAX=256, GDAL_HTTP_MAX_RETRY=5, GDAL_HTTP_RETRY_DELAY=2):
        with rasterio.open(f"{T.BASE}/{t}/USGS_13_{t}.tif") as ds:
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
                dx = res_x * T.M_PER_DEG_LON_EQ * np.cos(np.radians(ys))
                dy = res_y * T.M_PER_DEG_LAT
                zf = np.where(np.isnan(z), np.nanmean(z), z)
                slope = T.horn_slope_pct(zf, dx, dy)
                slope[np.isnan(z)] = np.nan
                m = features.rasterize([(poly.geometry, 1)], out_shape=(H, W), transform=tr, fill=0, dtype="uint8").astype(bool)
                m &= (xs[None, :] >= lon) & (xs[None, :] < lon + 1) & (ys[:, None] > lat - 1) & (ys[:, None] <= lat) & ~np.isnan(slope)
                if not m.any():
                    continue
                # padded road grid (independent of DEM tile edges)
                trp = Affine(tr.a, 0, tr.c - PAD_PX * tr.a, 0, tr.e, tr.f - PAD_PX * tr.e)
                Hp, Wp = H + 2 * PAD_PX, W + 2 * PAD_PX
                xmin, xmax = trp.c, trp.c + trp.a * Wp
                ymax, ymin = trp.f, trp.f + trp.e * Hp
                cand = TREE.query(box(xmin, ymin, xmax, ymax))
                if len(cand):
                    rmask = features.rasterize([(ROADS[i], 1) for i in cand], out_shape=(Hp, Wp), transform=trp, fill=0,
                                               dtype="uint8", all_touched=True).astype(bool)
                    dist = distance_transform_edt(~rmask, sampling=(float(dy), float(dx.mean())))
                    d = dist[PAD_PX:PAD_PX + H, PAD_PX:PAD_PX + W]
                else:
                    d = np.full((H, W), 1e9)
                cell_acres = ((dx * dy) / T.ACRE_M2)[:, None] * np.ones((1, W))
                s_, d_, a_ = slope[m], d[m], cell_acres[m]
                hist, _, _ = np.histogram2d(np.clip(s_, 0, T.SLOPE_HIST_EDGES[-1] - 1e-6), np.clip(d_, 0, DIST_EDGES[-1] - 1e-6),
                                            bins=[T.SLOPE_HIST_EDGES, DIST_EDGES], weights=a_)
                recs.append({"pid": int(poly.pid), "tile": t, "acres_dem": float(a_.sum()), "acres_x_dist": float((a_ * np.minimum(d_, 3000)).sum()),
                             "joint_hist": hist.astype("float32")})
    pathlib.Path(cache_dir).mkdir(parents=True, exist_ok=True)
    pickle.dump(recs, open(cache, "wb"))
    return recs


def run(gdf, cache_dir, procs=2):
    from multiprocessing import Pool
    tiles = T.tiles_for(gdf)
    jobs = []
    for t in tiles:
        lat, lon = int(t[1:3]), -int(t[4:7])
        jobs.append((t, gdf[gdf.intersects(box(lon, lat - 1, lon + 1, lat))], cache_dir))
    results = []
    with Pool(procs) as p:
        for i, r in enumerate(p.imap_unordered(process_tile_joint, jobs)):
            results += r
            print(f"joint tile {i+1}/{len(jobs)} done", flush=True)
    agg = {}
    for r in results:
        a = agg.setdefault(r["pid"], {"acres_dem": 0.0, "acres_x_dist": 0.0, "joint_hist": np.zeros((len(T.SLOPE_HIST_EDGES) - 1, len(DIST_EDGES) - 1))})
        a["acres_dem"] += r["acres_dem"]; a["acres_x_dist"] += r["acres_x_dist"]; a["joint_hist"] += r["joint_hist"]
    return agg
