"""Select core Appalachian national-forest roadless areas from the 2001 IRA inventory."""
import geopandas as gpd, math, json

CORE = {  # (FOREST, STATE) pairs treated as core Appalachian (documented in README)
 ("George Washington","VA"),("George Washington","WV"),("Jefferson","VA"),("Jefferson","WV"),
 ("Monongahela","WV"),("Pisgah","NC"),("Nantahala","NC"),("Cherokee","TN"),
 ("Chattahoochee","GA"),("Daniel Boone","KY"),("Allegheny","PA"),
}
ira = gpd.read_file("data/raw/BdyPlan_RoadlessArea_2001/S_USA.BdyPlan_RoadlessArea_2001.shp")
sel = ira[[ (f,s) in CORE for f,s in zip(ira.FOREST, ira.STATE)]].copy()
sel.to_file("data/processed/ira_core_appalachia.gpkg", driver="GPKG")
print(len(sel), "polygons;", round(sel.ACRES.sum()), "acres;", round(100*sel.ACRES.sum()/ira.ACRES.sum(),2), "% of national IRA acres")
minx,miny,maxx,maxy = sel.total_bounds
tiles=[]
for lat in range(math.floor(miny)+1, math.floor(maxy)+2):
    for lon in range(math.floor(minx), math.floor(maxx)+1):
        tiles.append(f"n{lat:02d}w{abs(lon):03d}")
print(sel.total_bounds, len(tiles), "candidate 1x1 deg tiles")
json.dump(tiles, open("data/processed/tiles_candidates.json","w"))
