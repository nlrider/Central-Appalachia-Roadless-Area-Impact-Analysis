"""Mosaic the 1 arc-second tiles to a ~90 m basemap DEM (3 arc-second average) for hillshade figures."""
import glob, rasterio, numpy as np
from rasterio.merge import merge
from rasterio.enums import Resampling
files = sorted(glob.glob("data/raw/dem30/USGS_1_*.tif"))
srcs = [rasterio.open(f) for f in files]
arr, tr = merge(srcs, res=3/3600, resampling=Resampling.average, nodata=-9999, dtype="float32")
prof = dict(driver="GTiff", height=arr.shape[1], width=arr.shape[2], count=1, dtype="float32", crs=srcs[0].crs, transform=tr, nodata=-9999, compress="deflate", tiled=True)
with rasterio.open("data/processed/dem90_mosaic.tif", "w", **prof) as dst:
    dst.write(arr)
print(arr.shape, tr)
