"""Sensitivity check: how much does DEM resolution (10 m vs 30 m) change the share of roadless acres above the agency's slope thresholds?
Uses the local 1 arc-second (~30 m) tiles. Same Horn slope + pixel-ownership rules as terrain_lib.py."""
import numpy as np, pandas as pd, geopandas as gpd, rasterio, json
from rasterio import features
from rasterio.windows import from_bounds, Window
from shapely.geometry import box
import terrain_lib as T

ira = gpd.read_file("data/processed/ira_core_appalachia.gpkg").reset_index(drop=True)
ira["pid"] = np.arange(1, len(ira) + 1)
tiles = json.load(open("data/processed/tiles_needed.json"))
edges = np.array([0, 20, 35, 40, 45, 60, 70, 80, 1e9])
acc = np.zeros(len(edges) - 1)
for t in tiles:
    lat, lon = int(t[1:3]), -int(t[4:7])
    sub = ira[ira.intersects(box(lon, lat - 1, lon + 1, lat))]
    with rasterio.open(f"data/raw/dem30/USGS_1_{t}.tif") as ds:
        rx, ry = ds.res
        for _, poly in sub.iterrows():
            minx, miny, maxx, maxy = poly.geometry.bounds
            minx, miny, maxx, maxy = max(minx, lon), max(miny, lat - 1), min(maxx, lon + 1), min(maxy, lat)
            if minx >= maxx or miny >= maxy:
                continue
            w = from_bounds(minx - 3 * rx, miny - 3 * ry, maxx + 3 * rx, maxy + 3 * ry, ds.transform).round_offsets().round_lengths()
            w = w.intersection(Window(0, 0, ds.width, ds.height))
            z = ds.read(1, window=w, masked=True).astype("float32").filled(np.nan)
            tr = ds.window_transform(w)
            H, W = z.shape
            ys = tr.f + tr.e * (np.arange(H) + .5); xs = tr.c + tr.a * (np.arange(W) + .5)
            dx = rx * T.M_PER_DEG_LON_EQ * np.cos(np.radians(ys)); dy = ry * T.M_PER_DEG_LAT
            zf = np.where(np.isnan(z), np.nanmean(z), z)
            s = T.horn_slope_pct(zf, dx, dy); s[np.isnan(z)] = np.nan
            m = features.rasterize([(poly.geometry, 1)], out_shape=(H, W), transform=tr, fill=0, dtype="uint8").astype(bool)
            m &= (xs[None, :] >= lon) & (xs[None, :] < lon + 1) & (ys[:, None] > lat - 1) & (ys[:, None] <= lat) & ~np.isnan(s)
            a = ((dx * dy) / T.ACRE_M2)[:, None] * np.ones((1, W))
            h, _ = np.histogram(s[m], bins=edges, weights=a[m]); acc += h
tot = acc.sum()
res = {"acres_30m": float(tot), "share_lt40_30m": float(acc[:3].sum() / tot), "share_gt40_30m": float(acc[3:].sum() / tot),
       "share_gt70_30m": float(acc[6:].sum() / tot), "share_gt35_30m": float(acc[2:].sum() / tot)}
# 10 m reference from ira_slope_hist (5-pt bins; 35/40/70 are bin-aligned)
h10 = pd.read_csv("data/processed/ira_slope_hist.csv")
cols = [c for c in h10.columns if c.startswith("s") and c[1:].isdigit()]
e = np.array([int(c[1:]) for c in cols]); v = h10[cols].sum().values
res.update({"share_gt40_10m": float(v[e >= 40].sum() / v.sum()), "share_gt70_10m": float(v[e >= 70].sum() / v.sum()), "share_gt35_10m": float(v[e >= 35].sum() / v.sum())})
json.dump(res, open("data/processed/dem_resolution_check.json", "w"), indent=1)
print(json.dumps(res, indent=1))
