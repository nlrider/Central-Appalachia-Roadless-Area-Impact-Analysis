"""Download USGS 3DEP 1 arc-second (~30 m) tiles for the study area: used for hillshade basemaps and a DEM-resolution sensitivity check."""
import json, requests, pathlib, hashlib
tiles = json.load(open("data/processed/tiles_needed.json"))
# add neighbors so the hillshade basemap covers forest extents around IRAs (bbox of core forests)
import geopandas as gpd, math
f = gpd.read_file("data/raw/BdyAdm_LSRS_AdministrativeForest/S_USA.BdyAdm_LSRS_AdministrativeForest.shp")
names = ["Allegheny National Forest","Daniel Boone National Forest","Monongahela National Forest","National Forests in North Carolina","George Washington and Jefferson National Forest","Cherokee National Forest","Chattahoochee-Oconee National Forests"]
f = f[f.FORESTNAME.isin(names)]
minx, miny, maxx, maxy = f.total_bounds
allt = []
for lat in range(math.floor(miny)+1, math.floor(maxy)+2):
    for lon in range(math.floor(minx), math.floor(maxx)+1):
        allt.append(f"n{lat:02d}w{abs(lon):03d}")
print(len(allt), "tiles for basemap")
out = pathlib.Path("data/raw/dem30"); man = {}
for t in allt:
    p = out / f"USGS_1_{t}.tif"
    if not p.exists():
        r = requests.get(f"https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1/TIFF/current/{t}/USGS_1_{t}.tif", timeout=600)
        if r.status_code != 200:
            print("skip", t, r.status_code); continue
        p.write_bytes(r.content)
    man[t] = hashlib.sha256(p.read_bytes()).hexdigest()
    print(t, "ok", flush=True)
json.dump(man, open(out / "manifest_sha256.json", "w"), indent=1)
