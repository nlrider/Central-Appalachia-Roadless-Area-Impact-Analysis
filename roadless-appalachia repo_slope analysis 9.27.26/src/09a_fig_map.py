"""Figure 1: study-area map - hillshade, national forest boundaries, and core-Appalachian inventoried roadless areas."""
import numpy as np, geopandas as gpd, rasterio
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from rasterio.windows import from_bounds
import style as S
S.apply()

EXT = (-85.2, -77.6, 34.3, 42.1)   # lon0, lon1, lat0, lat1
with rasterio.open("data/processed/dem90_mosaic.tif") as ds:
    w = from_bounds(EXT[0], EXT[2], EXT[1], EXT[3], ds.transform).round_offsets().round_lengths()
    from rasterio.enums import Resampling
    f = 3
    z = ds.read(1, window=w, out_shape=(int(w.height) // f, int(w.width) // f), resampling=Resampling.average).astype("float32")
z[z < -1000] = np.nan
zf = np.where(np.isnan(z), 0, z)
lat_mid = 38.0
dx = 270 * np.cos(np.radians(lat_mid)); dy = 270
ls = LightSource(azdeg=315, altdeg=38)
hs = ls.hillshade(zf, vert_exag=4, dx=dx, dy=dy)
hs = np.where(np.isnan(z), np.nan, hs)

forests = gpd.read_file("data/raw/BdyAdm_LSRS_AdministrativeForest/S_USA.BdyAdm_LSRS_AdministrativeForest.shp").to_crs(4269)
NAMES = {"Allegheny National Forest": "Allegheny", "Daniel Boone National Forest": "Daniel Boone", "Monongahela National Forest": "Monongahela",
         "National Forests in North Carolina": "Pisgah &\nNantahala", "George Washington and Jefferson National Forest": "George Washington\n& Jefferson",
         "Cherokee National Forest": "Cherokee", "Chattahoochee-Oconee National Forests": "Chattahoochee"}
forests = forests[forests.FORESTNAME.isin(NAMES)]
ira = gpd.read_file("data/processed/ira_core_appalachia.gpkg").to_crs(4269)

import textwrap
fig = plt.figure(figsize=(7.4, 7.9))
ax = fig.add_axes([0.02, 0.07, 0.96, 0.80])
MAIN = (-85.3, -77.7, 34.3, 40.45)

def base(a, lim):
    a.imshow(hs, extent=(EXT[0], EXT[1], EXT[2], EXT[3]), cmap="gray", vmin=0.1, vmax=1.15, alpha=0.5, origin="upper", zorder=0, interpolation="nearest")
    forests.boundary.plot(ax=a, color=S.INK2, linewidth=0.5, zorder=2)
    ira.plot(ax=a, facecolor=S.BLUE, edgecolor="#0d366b", linewidth=0.25, alpha=0.9, zorder=3)
    a.set_xlim(lim[0], lim[1]); a.set_ylim(lim[2], lim[3]); a.set_aspect(1 / np.cos(np.radians(lat_mid)))
base(ax, MAIN)
ax.axis("off")
# labels with leader lines: (anchor lon/lat, text position, ha)
LAB = {"Monongahela": ((-79.88, 38.51), (-81.9, 39.75), "right"),
       "George Washington": ((-79.2, 38.3), (-77.85, 39.35), "right"),
       "Jefferson": ((-80.81, 37.19), (-82.15, 37.35), "right"),
       "Daniel Boone": ((-83.62, 37.85), (-84.7, 38.55), "left"),
       "Cherokee": ((-82.86, 35.97), (-84.55, 36.75), "left"),
       "Pisgah": ((-82.28, 35.76), (-80.75, 35.2), "left"),
       "Nantahala": ((-83.71, 35.19), (-85.2, 35.55), "left"),
       "Chattahoochee": ((-83.91, 34.83), (-82.75, 34.5), "left")}
for k, (pt, tx, ha) in LAB.items():
    ax.annotate(k, xy=pt, xytext=tx, fontsize=8, color=S.INK, ha=ha, va="center", fontweight="bold", zorder=6,
                arrowprops=dict(arrowstyle="-", color=S.INK2, lw=0.6, shrinkA=2, shrinkB=0),
                bbox=dict(boxstyle="round,pad=0.15", fc=S.SURFACE, ec="none", alpha=0.8))
# scale bar (100 km)
x0, y0 = -85.1, 34.45
dlon = 100 / (111.32 * np.cos(np.radians(lat_mid)))
ax.plot([x0, x0 + dlon], [y0, y0], color=S.INK, lw=2, solid_capstyle="butt", zorder=6)
ax.text(x0 + dlon / 2, y0 + 0.06, "100 km", fontsize=7, color=S.INK2, ha="center", va="bottom", zorder=6)
# Allegheny inset (top-left of the empty NW corner)
ins = fig.add_axes([0.03, 0.62, 0.27, 0.24])
base(ins, (-80.45, -78.55, 41.15, 42.05))
for sp in ins.spines.values():
    sp.set_visible(True); sp.set_color(S.INK3); sp.set_linewidth(0.8)
ins.set_xticks([]); ins.set_yticks([])
ins.text(0.03, 0.95, "Allegheny (PA)", transform=ins.transAxes, fontsize=8, fontweight="bold", va="top", ha="left",
         bbox=dict(boxstyle="round,pad=0.15", fc=S.SURFACE, ec="none", alpha=0.85), zorder=6)
fig.text(0.03, 0.965, "Inventoried roadless areas in the core Appalachian national forests", fontsize=12, fontweight="bold", va="top")
fig.text(0.03, 0.932, f"{len(ira)} areas, {ira.ACRES.sum():,.0f} acres, 11 forest units: about 1.6% of the 58.5 million roadless acres nationally", fontsize=8.5, color=S.INK2, va="top")
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
ax.legend(handles=[Patch(fc=S.BLUE, ec="#0d366b", lw=0.5, alpha=0.9, label="Inventoried roadless area (2001 rule)"),
                   Line2D([0], [0], color=S.INK2, lw=0.8, label="National forest administrative boundary")],
          loc="lower right", fontsize=7.5, handlelength=1.6, bbox_to_anchor=(1.0, 0.0))
S.footer(fig, "Sources: USDA Forest Service EDW (2001 IRA inventory; administrative forest boundaries); USGS 3DEP elevation (hillshade).")
fig.savefig("figures/fig1_map.png", dpi=220); fig.savefig("figures/fig1_map.pdf")
print("ok")
