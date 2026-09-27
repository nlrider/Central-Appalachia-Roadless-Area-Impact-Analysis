"""Run the joint slope x road-distance histograms for IRA polygons and for harvest units (same filters as 03)."""
import numpy as np, pandas as pd, geopandas as gpd, sys
import terrain_joint as J

J.init_roads()
ira = gpd.read_file("data/processed/ira_core_appalachia.gpkg").reset_index(drop=True)
ira["pid"] = np.arange(1, len(ira) + 1)
agg = J.run(ira[["pid", "geometry"]], "data/processed/cache_joint_ira", procs=2)
np.savez_compressed("data/processed/joint_ira.npz", pids=np.array(list(agg)), hist=np.stack([agg[p]["joint_hist"] for p in agg]),
                    acres=np.array([agg[p]["acres_dem"] for p in agg]))
print("IRA done", flush=True)

# harvest units: identical filtering/pid assignment as 03_harvest_slopes.py
CORE_FORESTS = ["Allegheny National Forest", "Daniel Boone National Forest", "Monongahela National Forest",
                "National Forests in North Carolina", "George Washington and Jefferson National Forest",
                "Cherokee National Forest", "Chattahoochee-Oconee National Forests"]
h = gpd.read_file("data/raw/fs_services/timber_harvest_all_years.geojson")
h = h[h.admin_forest_name.isin(CORE_FORESTS)].copy()
h = h[~h.activity_name.fillna("").str.contains("Natural Changes|Harvest Without Restocking", case=False)]
h = h[h.treatment_type.fillna("N/A") != "N/A"]
h = h[h.geometry.notna() & ~h.geometry.is_empty].reset_index(drop=True)
h["pid"] = np.arange(1, len(h) + 1)
chk = pd.read_csv("data/processed/harvest_attributes.csv")
assert len(chk) == len(h) and (chk.facts_id.fillna("").astype(str).values == h.facts_id.fillna("").astype(str).values).all(), "harvest pid alignment mismatch"
agg = J.run(h[["pid", "geometry"]], "data/processed/cache_joint_harvest", procs=2)
np.savez_compressed("data/processed/joint_harvest.npz", pids=np.array(list(agg)), hist=np.stack([agg[p]["joint_hist"] for p in agg]),
                    acres=np.array([agg[p]["acres_dem"] for p in agg]))
print("harvest done", flush=True)
