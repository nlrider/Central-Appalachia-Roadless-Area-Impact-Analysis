"""Download Forest Service EDW layers (paged ArcGIS REST queries) clipped to the study bbox.
Writes GeoJSON + a small provenance JSON (URL, query, date, feature count)."""
import requests, json, sys, time, datetime, pathlib
BBOX = "-84.7,34.5,-78.2,42.1"
OUT = pathlib.Path("data/raw/fs_services"); OUT.mkdir(parents=True, exist_ok=True)
LAYERS = {
  "timber_harvest_all_years": "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_TimberHarvest_01/MapServer/8",
  "forests_to_faucets_2": "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_ForeststoFaucets_02/MapServer/2",
}
def pull(name, url, page=1000):
    feats, off = [], 0
    while True:
        p = dict(where="1=1", geometry=BBOX, geometryType="esriGeometryEnvelope", inSR=4326, spatialRel="esriSpatialRelIntersects",
                 outFields="*", outSR=4326, returnGeometry="true", f="geojson", resultOffset=off, resultRecordCount=page,
                 geometryPrecision=6)
        for attempt in range(5):
            try:
                r = requests.get(url + "/query", params=p, timeout=180); r.raise_for_status(); j = r.json(); break
            except Exception as e:
                print("retry", name, off, e, flush=True); time.sleep(3)
        else: raise RuntimeError("failed")
        fs = j.get("features", [])
        feats += fs; off += len(fs)
        print(name, off, flush=True)
        if len(fs) == 0 or not j.get("properties", {}).get("exceededTransferLimit", len(fs) == page): break
    json.dump({"type": "FeatureCollection", "features": feats}, open(OUT / f"{name}.geojson", "w"))
    json.dump({"layer_url": url, "bbox_wgs84": BBOX, "retrieved_utc": datetime.datetime.utcnow().isoformat() + "Z", "n_features": len(feats)},
              open(OUT / f"{name}.provenance.json", "w"), indent=1)
for n, u in LAYERS.items(): pull(n, u)
