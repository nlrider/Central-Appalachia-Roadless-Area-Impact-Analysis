"""Landslide susceptibility (USGS slope-relief, n10 model) and Hurricane Helene landslide inventory overlays.

Susceptibility raster value = number of 10-m susceptible cells inside each 90-m cell (0-81) => fraction = value/81.
All rasters are handled on the susceptibility raster's own 90-m grid (EPSG:4269).
Outputs: data/processed/hazard_*.csv
"""
import numpy as np, pandas as pd, geopandas as gpd, rasterio, json
from rasterio import features
from rasterio.windows import from_bounds
from shapely.geometry import box

SUSC = "data/raw/landslide/n10_susc/n10_conus.tif"
CORE_FORESTS = ["Allegheny National Forest", "Daniel Boone National Forest", "Monongahela National Forest",
                "National Forests in North Carolina", "George Washington and Jefferson National Forest",
                "Cherokee National Forest", "Chattahoochee-Oconee National Forests"]

ira = gpd.read_file("data/processed/ira_core_appalachia.gpkg").to_crs(4269).reset_index(drop=True)
forests = gpd.read_file("data/raw/BdyAdm_LSRS_AdministrativeForest/S_USA.BdyAdm_LSRS_AdministrativeForest.shp").to_crs(4269)
forests = forests[forests.FORESTNAME.isin(CORE_FORESTS)].copy()
print(sorted(forests.FORESTNAME.unique()))
minx, miny, maxx, maxy = forests.total_bounds
with rasterio.open(SUSC) as ds:
    w = from_bounds(minx, miny, maxx, maxy, ds.transform).round_offsets().round_lengths()
    susc = ds.read(1, window=w).astype("float32")
    tr = ds.window_transform(w)
    H, W = susc.shape
print("susc window", susc.shape)
frac = susc / 81.0

own = gpd.read_file("data/raw/BdyOwn_LSRS_BasicOwnership/S_USA.BdyOwn_LSRS_BasicOwnership.shp", bbox=(minx, miny, maxx, maxy))
own = own[own.OWNERCLASS == "USDA FOREST SERVICE"].to_crs(4269)
print("FS-owned parcels in bbox:", len(own), round(own.GIS_ACRES.sum()), "acres (all forests in bbox, incl. non-core)")
f_admin = features.rasterize([(g, 1) for g in forests.geometry], out_shape=(H, W), transform=tr, fill=0, dtype="uint8").astype(bool)
own_mask = features.rasterize([(g, 1) for g in own.geometry], out_shape=(H, W), transform=tr, fill=0, dtype="uint8").astype(bool)
# NFS-owned land inside the core forests' administrative boundaries (excludes private inholdings)
f_mask = f_admin & own_mask
i_mask = features.rasterize([(g, 1) for g in ira.geometry], out_shape=(H, W), transform=tr, fill=0, dtype="uint8").astype(bool)
# pixel area (acres) per row
ys = tr.f + tr.e * (np.arange(H) + 0.5)
cell_acres = (abs(tr.a) * 111320 * np.cos(np.radians(ys)) * abs(tr.e) * 110574 / 4046.8564224)
A = np.repeat(cell_acres[:, None], W, axis=1)

ira_ids = features.rasterize([(g, int(i + 1)) for i, g in enumerate(ira.geometry)], out_shape=(H, W), transform=tr, fill=0, dtype="int32")
out = {}
out["susc_frac_mean_IRA_acre_weighted"] = float((frac[i_mask] * A[i_mask]).sum() / A[i_mask].sum())
nonira_nfs = f_mask & ~i_mask
out["susc_frac_mean_NFS_nonIRA_acre_weighted"] = float((frac[nonira_nfs] * A[nonira_nfs]).sum() / A[nonira_nfs].sum())
out["acres_IRA_on_grid"] = float(A[i_mask].sum()); out["acres_NFS_nonIRA_on_grid"] = float(A[nonira_nfs].sum())
# per-polygon
rows = []
for pid in np.unique(ira_ids[ira_ids > 0]):
    m = ira_ids == pid
    rows.append({"pid_index": int(pid - 1), "acres_grid": float(A[m].sum()), "susc_frac_mean": float((frac[m] * A[m]).sum() / A[m].sum())})
pd.DataFrame(rows).to_csv("data/processed/hazard_susc_by_ira.csv", index=False)

# susceptibility distribution (acre-weighted histogram, 10 bins of 10 percentage points)
edges = np.linspace(0, 1.0001, 11)
dist = []
for name, m in [("IRA", i_mask), ("NFS_nonIRA", nonira_nfs)]:
    h, _ = np.histogram(frac[m], bins=edges, weights=A[m])
    dist.append({"group": name, **{f"bin{int(edges[k]*100)}": float(h[k]) for k in range(10)}})
pd.DataFrame(dist).to_csv("data/processed/hazard_susc_hist.csv", index=False)

# ---- Helene ----
hl = gpd.read_file("data/raw/landslide/helene_inventory.geojson").to_crs(4269)
print(len(hl), "Helene points; Source examples", hl.Source.value_counts().head(5).to_dict(), "Impact", hl.Impact.value_counts().to_dict())
hull = hl.union_all().convex_hull
aoi = np.zeros((H, W), dtype=bool)
aoi = features.rasterize([(hull, 1)], out_shape=(H, W), transform=tr, fill=0, dtype="uint8").astype(bool)
def counts(points):
    r, c = rasterio.transform.rowcol(tr, points.geometry.x.values, points.geometry.y.values)
    r, c = np.array(r), np.array(c)
    ok = (r >= 0) & (r < H) & (c >= 0) & (c < W)
    cnt = np.zeros((H, W), dtype="int32")
    np.add.at(cnt, (r[ok], c[ok]), 1)
    return cnt
variants = {
    "all_points": hl,
    "sentinel2_only": hl[hl.Source.astype(str) == "S2"],
    "no_road_building_impact": hl[~hl.Impact.astype(str).isin(["Road", "Building", "Various"])],
}
bins = np.array([0, .2, .4, .6, .8, 1.0001])
sb = np.digitize(frac, bins) - 1
res = []
for vname, pts in variants.items():
    cnt = counts(pts)
    for grp, m in [("IRA", i_mask & aoi), ("NFS_nonIRA", nonira_nfs & aoi)]:
        for k in range(5):
            mm = m & (sb == k)
            if mm.sum() == 0: continue
            res.append({"variant": vname, "group": grp, "susc_bin": f"{int(bins[k]*100)}-{int(min(bins[k+1],1)*100)}%",
                        "acres": float(A[mm].sum()), "landslides": int(cnt[mm].sum())})
pd.DataFrame(res).to_csv("data/processed/hazard_helene_strata.csv", index=False)
json.dump(out, open("data/processed/hazard_summary.json", "w"), indent=1)
print(json.dumps(out, indent=1))
print("helene points inside AOI∩NFS:", int(counts(hl)[aoi & f_mask].sum()), " inside IRA:", int(counts(hl)[aoi & i_mask].sum()))
