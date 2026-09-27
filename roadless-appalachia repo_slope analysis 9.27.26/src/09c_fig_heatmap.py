"""Figure 3: where roadless acres fall in the Forest Service's own operability space (slope x distance to nearest road)."""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm
from matplotlib.patches import Rectangle, Polygon
import style as S
import agency_screen as A
S.apply()

pids, H = A.load("ira")
tot = H.sum(axis=0)                       # (40 slope bins, 60 dist bins)
r = A.screen(tot)
share = {k: r[k] / r["total"] for k in ("operable", "complex", "not_operable")}
MI = A.MI
xs = A.S_EDGES[:21]                       # 0..100 %
ys = A.D_EDGES[:49] / MI                  # 0..~1.5 mi
Z = tot[:20, :48].T                       # (dist, slope)

fig = plt.figure(figsize=(9.2, 5.6))
ax = fig.add_axes([0.075, 0.15, 0.60, 0.67])
pm = ax.pcolormesh(xs, ys, Z, cmap="Blues", norm=PowerNorm(0.5, vmin=0, vmax=Z.max()), shading="flat", rasterized=True)
lw = 1.6
# operable box
ax.add_patch(Rectangle((0, 0), 40, 0.5, fill=False, ec=S.INK, lw=lw, zorder=4))
# complex L-shape: (40-70 & <0.5mi) U (<70 & 0.5-1mi)
ax.add_patch(Polygon([(40, 0), (70, 0), (70, 1.0), (0, 1.0), (0, 0.5), (40, 0.5)], closed=True, fill=False, ec=S.INK, lw=lw, ls=(0, (5, 3)), zorder=4))
ax.text(20, 0.25, f"Likely operable\n{100*share['operable']:.0f}% of acres", ha="center", va="center", fontsize=9, fontweight="bold", color="white", zorder=5)
ax.text(55, 0.25, f"Operable but complex", ha="center", va="center", fontsize=8, color=S.INK, zorder=5)
ax.text(35, 0.75, f"Operable but complex (0.5-1 mile)", ha="center", va="center", fontsize=8, color=S.INK, zorder=5)
ax.text(85, 0.75, f"Likely not operable\n{100*share['not_operable']:.0f}% of acres", ha="center", va="center", fontsize=9, fontweight="bold", color=S.INK, zorder=5)
ax.text(35, 1.3, "Likely not operable (over 1 mile from a road)", ha="center", va="center", fontsize=8, color=S.INK2)
ax.set_xlim(0, 100); ax.set_ylim(0, 1.5)
ax.set_xlabel("Slope (%)"); ax.set_ylabel("Distance to nearest existing road (miles)")
ax.set_xticks([0, 20, 40, 60, 70, 80, 100]); ax.set_yticks([0, 0.5, 1.0, 1.5])
cb = fig.colorbar(pm, ax=ax, pad=0.015, fraction=0.04)
cb.set_label("Roadless acres per cell (5% slope x 50 m)", fontsize=7.5); cb.ax.tick_params(labelsize=7)
# right panel: share bars
bx = fig.add_axes([0.76, 0.15, 0.20, 0.67])
bx.axis("off")
bx.text(0, 1.0, "Share of core-Appalachian\nroadless acres", fontsize=9, fontweight="bold", va="bottom", transform=bx.transAxes)
y0 = 0.0
for k, lab in [("not_operable", "Likely not operable"), ("complex", "Operable but complex"), ("operable", "Likely operable")]:
    h = share[k]
    bx.add_patch(Rectangle((0.0, y0), 0.30, h, transform=bx.transAxes, fc=S.RAMP[k], ec=S.SURFACE, lw=2))
    bx.text(0.36, y0 + h / 2, f"{lab}\n{100*h:.0f}%  ({r[k]/1000:,.0f}k acres)", transform=bx.transAxes, fontsize=8, va="center", color=S.INK)
    y0 += h
bx.text(0, -0.03, "Slope and road-distance criteria only.\nExcludes site productivity and forest-plan\nrestrictions, so 'operable' is an upper bound.", transform=bx.transAxes, fontsize=6.8, color=S.INK2, va="top")
fig.text(0.012, 0.975, "By the Forest Service's own screen, terrain and road access do not rule out\nmost Appalachian roadless land", fontsize=11.5, fontweight="bold", va="top", linespacing=1.25)
fig.text(0.012, 0.888, "Draft EIS criteria: operable = under 0.5 mi from a road and under 40% slope; complex = up to 70% slope within 1 mi", fontsize=7.6, color=S.INK2, va="top")
S.footer(fig, "Sources: USFS 2001 IRA inventory; USGS 3DEP 10 m DEM (Horn slope); USGS TNM/TIGER roads and USFS system roads. Distance beyond 1.5 mi not shown (counted as not operable).\nThe DEIS does not state its DEM resolution; 30 m terrain data would classify more land as operable.", y=0.01)
fig.savefig("figures/fig3_operability_space.png", dpi=220); fig.savefig("figures/fig3_operability_space.pdf")
print({k: round(v, 3) for k, v in share.items()}, "acres beyond 1.5mi shown-range share:", round(tot[:, 48:].sum() / tot.sum(), 3))
