"""Build the combined existing-road layer used for the access screen.

Sources
  * USGS TNM Transportation (TIGER-derived) road segments, 7 states  -> all public/private vehicle roads incl. state/county
  * USFS National Forest System roads (Trans_RoadCore_FS)              -> forest roads incl. maintenance-level-1 (closed) roads
Kept MTFCC classes: S1100 primary, S1200 secondary, S1400 local, S1630 ramp, S1740 private service road, S1500 4WD vehicular trail.
Dropped: walkways, bike paths, bridle paths, stairways, parking-lot roads, alleys.
Only roads within ~4 km of an IRA or harvest polygon are kept (all that the distance calculation can see).
"""
import geopandas as gpd, pandas as pd, numpy as np, glob, pyogrio
from shapely.geometry import box

KEEP = {"S1100", "S1200", "S1400", "S1630", "S1740", "S1500"}
ira = gpd.read_file("data/processed/ira_core_appalachia.gpkg")[["geometry"]]
hv = pd.read_csv("data/processed/harvest_attributes.csv")  # attributes only; geometry re-read below
hvg = gpd.read_file("data/raw/fs_services/timber_harvest_all_years.geojson")[["geometry"]].set_crs(4326, allow_override=True).to_crs(4269)
study = pd.concat([ira, hvg], ignore_index=True)
study = gpd.GeoDataFrame(study, geometry="geometry", crs=4269)
study_b = study.geometry.buffer(0.045)                 # ~4-5 km
union = study_b.union_all()
minx, miny, maxx, maxy = union.bounds
print("study bounds", union.bounds)

parts = []
for f in sorted(glob.glob("data/raw/tran/*/Shape/Trans_RoadSegment*.shp")):
    g = gpd.read_file(f, bbox=(minx, miny, maxx, maxy), columns=["mtfcc_code"])
    g = g[g.mtfcc_code.isin(KEEP)]
    idx = g.sindex.query(union, predicate="intersects")
    g = g.iloc[idx]
    g["src"] = "USGS_TNM_TIGER"
    parts.append(g[["src", "mtfcc_code", "geometry"]])
    print(f, len(g), flush=True)
z = "data/raw/Trans_RoadCore_FS"
import zipfile, os
if not os.path.exists(z):
    zipfile.ZipFile("data/raw/Trans_RoadCore_FS.zip").extractall(z)
shp = glob.glob(z + "/*.shp")[0]
fs = gpd.read_file(shp, bbox=(minx, miny, maxx, maxy)).to_crs(4269)
idx = fs.sindex.query(union, predicate="intersects")
fs = fs.iloc[idx].copy()
fs["src"] = "USFS_RoadCore"; fs["mtfcc_code"] = "FS"
print("FS roads kept", len(fs), " columns:", [c for c in fs.columns if c != "geometry"][:25])
parts.append(fs[["src", "mtfcc_code", "geometry"]])
roads = pd.concat(parts, ignore_index=True)
roads = gpd.GeoDataFrame(roads, geometry="geometry", crs=4269)
roads.to_file("data/processed/roads_study.gpkg", driver="GPKG")
print(len(roads), "road segments;", roads.src.value_counts().to_dict())
