"""Slope distribution of actual Forest Service timber harvest units (FACTS) in the core Appalachian forests,
computed with the same DEM pipeline as the roadless areas (apples-to-apples), plus a lib-based recomputation of IRA slopes
as an internal cross-check against 01_terrain.py."""
import geopandas as gpd, pandas as pd, numpy as np, re
import terrain_lib as T

CORE_FORESTS = ["Allegheny National Forest", "Daniel Boone National Forest", "Monongahela National Forest",
                "National Forests in North Carolina", "George Washington and Jefferson National Forest",
                "Cherokee National Forest", "Chattahoochee-Oconee National Forests"]
h = gpd.read_file("data/raw/fs_services/timber_harvest_all_years.geojson")
h = h[h.admin_forest_name.isin(CORE_FORESTS)].copy()
h = h[~h.activity_name.fillna("").str.contains("Natural Changes|Harvest Without Restocking", case=False)]
h = h[h.treatment_type.fillna("N/A") != "N/A"]
h["fy_completed_int"] = pd.to_numeric(h.fy_completed, errors="coerce")
h = h[h.geometry.notna() & ~h.geometry.is_empty].reset_index(drop=True)
h["pid"] = np.arange(1, len(h) + 1)
print(len(h), "harvest polygons after filtering; completed FY known:", h.fy_completed_int.notna().sum())
h.drop(columns="geometry").to_csv("data/processed/harvest_attributes.csv", index=False)
agg = T.run(h[["pid", "geometry"]], "data/processed/cache_harvest", procs=2)
rows = []
for pid, a in agg.items():
    r = {"pid": pid, "acres_dem": a["acres_dem"], "acres_x_slope": a["acres_x_slope"]}
    r.update({f"s{int(e)}": v for e, v in zip(T.SLOPE_HIST_EDGES[:-1], a["slope_hist"])})
    rows.append(r)
pd.DataFrame(rows).to_csv("data/processed/harvest_slope_hist.csv", index=False)

# cross-check: IRA via the shared library
ira = gpd.read_file("data/processed/ira_core_appalachia.gpkg").reset_index(drop=True)
ira["pid"] = np.arange(1, len(ira) + 1)
agg = T.run(ira[["pid", "geometry"]], "data/processed/cache_ira_lib", procs=2)
rows = []
for pid, a in agg.items():
    r = {"pid": pid, "acres_dem": a["acres_dem"], "acres_x_slope": a["acres_x_slope"]}
    r.update({f"s{int(e)}": v for e, v in zip(T.SLOPE_HIST_EDGES[:-1], a["slope_hist"])})
    rows.append(r)
pd.DataFrame(rows).to_csv("data/processed/ira_slope_hist.csv", index=False)
print("finished")
