"""Figure 2: cumulative slope distributions - roadless areas vs. Forest Service harvest units (FY2001+), by forest."""
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
import style as S
import importlib.util, sys
S.apply()

EDGES = np.arange(0, 200, 5)
COLS = [f"s{e}" for e in EDGES]
sys.path.insert(0, "src")
from importlib import import_module
A = import_module("agency_screen")

ira = pd.read_csv("data/processed/ira_attributes.csv").merge(pd.read_csv("data/processed/ira_slope_hist.csv"), on="pid")
ira["g"] = ira.FOREST.map(A.FOREST_MAP)
hv = pd.read_csv("data/processed/harvest_attributes.csv").merge(pd.read_csv("data/processed/harvest_slope_hist.csv"), on="pid")
hv["fy"] = pd.to_numeric(hv.fy_completed, errors="coerce")
hv = hv[hv.fy >= 2001].copy()
hv["g"] = hv.admin_forest_name.map(A.HARV_MAP)


def ecdf(h):
    c = np.cumsum(h) / h.sum()
    x = np.r_[0, EDGES + 5]
    y = np.r_[0, c]
    return x, y


def share_gt(h, thr):
    e = EDGES; return h[e >= thr].sum() / h.sum()


order = S.FOREST_ORDER
fig, axes = plt.subplots(2, 4, figsize=(9.6, 5.6), sharex=True, sharey=True)
axes = axes.ravel()
for i, g in enumerate(order):
    ax = axes[i]
    hi = ira[ira.g == g][COLS].sum().values
    hh = hv[hv.g == g][COLS].sum().values
    x, y = ecdf(hi); ax.plot(x, y, color=S.BLUE, lw=1.8, solid_capstyle="round")
    x, y = ecdf(hh); ax.plot(x, y, color=S.ORANGE, lw=1.8, solid_capstyle="round")
    for thr in (40, 70):
        ax.axvline(thr, color=S.INK3, lw=0.7, ls=(0, (3, 3)), zorder=0)
    ax.set_xlim(0, 100); ax.set_ylim(0, 1.0); ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_title(g, fontsize=9.5)
    ax.text(0.98, 0.06, f"Roadless {hi.sum()/1000:,.0f}k ac | >40%: {100*share_gt(hi,40):.0f}%\nHarvested {hh.sum()/1000:,.0f}k ac | >40%: {100*share_gt(hh,40):.0f}%",
            transform=ax.transAxes, fontsize=6.6, color=S.INK2, ha="right", va="bottom", linespacing=1.4)
    ax.grid(axis="y", color=S.GRID, lw=0.6)
    ax.set_axisbelow(True)
    if i % 4 == 0: ax.set_yticks([0, .25, .5, .75, 1.0]); ax.set_yticklabels(["0", "25", "50", "75", "100%"])
    if i >= 4: ax.set_xlabel("Slope (%)")
    if i == 0:
        ax.annotate("Roadless\nareas", xy=(58, 0.55), xytext=(66, 0.35), fontsize=8, color=S.INK, ha="left", va="center",
                    arrowprops=dict(arrowstyle="-", color=S.INK3, lw=0.6))
        ax.annotate("Harvested\nunits", xy=(22, 0.70), xytext=(4, 0.95), fontsize=8, color=S.INK, ha="left", va="center",
                    arrowprops=dict(arrowstyle="-", color=S.INK3, lw=0.6))
ax = axes[7]; ax.axis("off")
ax.text(0.0, 0.98, "How to read", fontsize=9, fontweight="bold", va="top")
ax.text(0.0, 0.86, "Each curve shows the share of acres on\nground no steeper than the slope at\nleft. A curve further right = steeper.\n\nDashed lines mark the Forest Service's\nDEIS operability slopes: 40% (ground-\nbased harvest) and 70% (upper limit for\n'operable but complex').\n\nHarvested = Forest Service timber\nharvest units completed since FY2001\n(FACTS), same forest, same 10 m terrain\nmethod.", fontsize=6.9, color=S.INK2, va="top", linespacing=1.35)
from matplotlib.lines import Line2D
handles = [Line2D([0], [0], color=S.BLUE, lw=1.8, solid_capstyle="round"), Line2D([0], [0], color=S.ORANGE, lw=1.8, solid_capstyle="round")]
fig.suptitle("Roadless land is generally steeper than harvested land, but the distributions overlap substantially", x=0.012, y=0.985, ha="left", fontsize=11.5, fontweight="bold")
fig.legend(handles, ["Roadless areas", "Harvested units (FY2001+)"], loc="upper right", bbox_to_anchor=(0.995, 0.925), ncol=2, fontsize=8.4, frameon=False, handlelength=1.6, columnspacing=1.2)
fig.subplots_adjust(left=0.06, right=0.99, top=0.83, bottom=0.11, wspace=0.16, hspace=0.32)
S.footer(fig, "Sources: USFS EDW (2001 IRA inventory; FACTS timber harvest polygons); USGS 3DEP 1/3 arc-second DEM, Horn slope. Daniel Boone has only about 2,800 roadless acres.")
fig.savefig("figures/fig2_slope_ecdf.png", dpi=220); fig.savefig("figures/fig2_slope_ecdf.pdf")
print("ok")
