"""Forests to Faucets 2.0 (HUC12) via objectId chunks; robust to server 500s on large geometries."""
import requests, json, time, datetime, pathlib
URL = "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_ForeststoFaucets_02/MapServer/2"
BBOX = "-84.7,34.5,-78.2,42.1"
out = pathlib.Path("data/raw/fs_services")
base = dict(where="1=1", geometry=BBOX, geometryType="esriGeometryEnvelope", inSR=4326, spatialRel="esriSpatialRelIntersects")
ids = requests.get(URL + "/query", params=dict(base, returnIdsOnly="true", f="json"), timeout=120).json()["objectIds"]
print(len(ids), "objects", flush=True)


def get(idlist, prec=5):
    p = dict(objectIds=",".join(map(str, idlist)), outFields="*", outSR=4326, returnGeometry="true", f="geojson", geometryPrecision=prec)
    for a in range(4):
        try:
            r = requests.post(URL + "/query", data=p, timeout=180)
            r.raise_for_status()
            return r.json()["features"]
        except Exception:
            time.sleep(2)
    return None


feats, failed = [], []
CH = 100
for i in range(0, len(ids), CH):
    chunk = ids[i:i + CH]
    r = get(chunk)
    if r is None:  # fall back to one-by-one so a single bad feature does not sink the chunk
        r = []
        for oid in chunk:
            x = get([oid])
            if x is None:
                failed.append(oid)
            else:
                r += x
    feats += r
    print(i + len(chunk), len(feats), "failed", len(failed), flush=True)
json.dump({"type": "FeatureCollection", "features": feats}, open(out / "forests_to_faucets_2.geojson", "w"))
json.dump({"layer_url": URL, "bbox_wgs84": BBOX, "retrieved_utc": datetime.datetime.utcnow().isoformat() + "Z",
           "n_features": len(feats), "n_ids_requested": len(ids), "failed_object_ids": failed},
          open(out / "forests_to_faucets_2.provenance.json", "w"), indent=1)
