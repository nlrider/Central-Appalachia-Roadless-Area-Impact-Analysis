"""Figure 4: the Forest Service's DEIS operability screen applied to roadless areas and to where the agency has actually harvested."""
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
import style as S
S.apply()

r = pd.read_csv("data/processed/agency_screen_by_forest.csv")
order = S.FOREST_ORDER + ["ALL"]
lab = {"ALL": "All core Appalachian\nforests", "GW&J": "George Washington &\nJefferson", "Pisgah-Nantahala": "Pisgah-Nantahala"}
classes = [("operable", "Likely operable"), ("complex", "Operable but complex"), ("not_operable", "Likely not operable")]
fig, ax = plt.subplots(figsize=(9.4, 6.0))
y = 0; yt = []; ytl = []
for g in order:
    for kind, name in [("IRA", "Roadless"), ("harvest_FY>=2001", "Harvested since 2001")]:
        row = r[(r.kind == kind) & (r.group == g)]
        if row.empty:
            continue
        row = row.iloc[0]
        left = 0
        for k, _ in classes:
            v = 100 * row[f"share_{k}"]
            ax.barh(y, v, left=left, height=0.72, color=S.RAMP[k], ec=S.SURFACE, lw=1.5, zorder=2)
            if v >= 6:
                ax.text(left + v / 2, y, f"{v:.0f}", ha="center", va="center", fontsize=7.6,
                        color="white" if k != "not_operable" else S.INK, zorder=3)
            left += v
        ax.text(-1.2, y, name, ha="right", va="center", fontsize=7.4, color=S.INK2)
        y -= 1
    yt.append(y + 1.5); ytl.append(lab.get(g, g))
    y -= 0.7
ax.set_yticks(yt); ax.set_yticklabels(ytl, fontsize=8.6, fontweight="bold")
ax.tick_params(axis="y", length=0, pad=95)
ax.set_xlim(0, 100); ax.set_ylim(y + 0.3, 1.2)
ax.set_xlabel("Share of acres (%)", labelpad=3)
ax.xaxis.set_ticks([0, 25, 50, 75, 100]); ax.spines["left"].set_visible(False)
h = [plt.Rectangle((0, 0), 1, 1, color=S.RAMP[k]) for k, _ in classes]
ax.legend(h, [n for _, n in classes], loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, fontsize=8.2, handlelength=1.2)
fig.text(0.012, 0.985, "Recent harvest has occurred almost entirely on 'likely operable' ground; most roadless land\nfalls in the costlier 'operable but complex' class", fontsize=11.5, fontweight="bold", va="top", linespacing=1.25)
fig.subplots_adjust(left=0.30, right=0.985, top=0.84, bottom=0.155)
S.footer(fig, "Slope and road-distance criteria from the Draft EIS (p. 74); site productivity and forest-plan restrictions not applied. Harvested = FACTS timber harvest units completed FY2001+ in the same forests.\nSources: USFS 2001 IRA inventory and FACTS; USGS 3DEP 10 m DEM; USGS TNM/TIGER and USFS roads. Roads are current, so harvest near roads is partly by construction (roads are built to harvest).", y=0.008)
fig.savefig("figures/fig4_screen_by_forest.png", dpi=220); fig.savefig("figures/fig4_screen_by_forest.pdf")
print(r[r.group == "ALL"][["kind", "share_operable", "share_complex", "share_not_operable"]].round(3))
