"""Figure 5 (hazard): Helene landslide density and USGS susceptibility; Figure 6 (water): drinking-water context of roadless watersheds."""
import numpy as np, pandas as pd, json
import matplotlib.pyplot as plt
from scipy.stats import chi2
import style as S
S.apply()


def poisson_ci(k, exposure, alpha=0.05):
    lo = 0.0 if k == 0 else chi2.ppf(alpha / 2, 2 * k) / 2
    hi = chi2.ppf(1 - alpha / 2, 2 * (k + 1)) / 2
    return lo / exposure, hi / exposure


# ---------------- hazard ----------------
d = pd.read_csv("data/processed/hazard_helene_strata.csv")
hist = pd.read_csv("data/processed/hazard_susc_hist.csv").set_index("group")
summ = json.load(open("data/processed/hazard_summary.json"))
LAB = {"all_points": "All mapped landslides", "sentinel2_only": "Satellite-only detections", "no_road_building_impact": "Excluding road- and\nbuilding-impact points"}
fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.6), gridspec_kw=dict(width_ratios=[1.25, 1]))
ax = axs[0]
rows = []
for v, g in d.groupby("variant"):
    for grp, gg in g.groupby("group"):
        k, ac = gg.landslides.sum(), gg.acres.sum()
        rate = 1000 * k / ac
        lo, hi = poisson_ci(k, ac / 1000)
        rows.append((v, grp, k, ac, rate, lo, hi))
res = pd.DataFrame(rows, columns=["variant", "group", "landslides", "acres", "rate", "lo", "hi"])
res.to_csv("data/processed/hazard_helene_rates.csv", index=False)
ypos = {"all_points": 2, "sentinel2_only": 1, "no_road_building_impact": 0}
for v, y in ypos.items():
    for grp, col, off in [("IRA", S.BLUE, 0.16), ("NFS_nonIRA", S.ORANGE, -0.16)]:
        r = res[(res.variant == v) & (res.group == grp)].iloc[0]
        ax.barh(y + off, r.rate, height=0.28, color=col, zorder=2)
        ax.plot([r.lo, r.hi], [y + off, y + off], color=S.INK, lw=1.0, zorder=3)
        ax.text(r.hi + 0.015, y + off, f"{r.rate:.2f}  (n={int(r.landslides)})", va="center", fontsize=7.5, color=S.INK)
ax.set_yticks(list(ypos.values())); ax.set_yticklabels([LAB[v] for v in ypos], fontsize=8)
ax.set_xlabel("Helene landslides per 1,000 acres (95% interval)")
ax.set_xlim(0, 0.75); ax.grid(axis="x", color=S.GRID, lw=0.6); ax.set_axisbelow(True)
ax.set_title("Landslide density in the Helene area", fontsize=10)
ax.text(0.98, 0.04, "Blue = roadless areas\nOrange = other national forest land", transform=ax.transAxes, ha="right", va="bottom", fontsize=7.8, color=S.INK2)
ax = axs[1]
bins = [c for c in hist.columns if c.startswith("bin")]
x = np.arange(len(bins))
for grp, col, off, lab in [("IRA", S.BLUE, -0.19, "Roadless"), ("NFS_nonIRA", S.ORANGE, 0.19, "Other national forest")]:
    v = hist.loc[grp, bins].values.astype(float); v = 100 * v / v.sum()
    ax.bar(x + off, v, width=0.36, color=col, label=lab, zorder=2)
ax.set_xticks(x); ax.set_xticklabels([b.replace("bin", "") for b in bins], fontsize=7)
ax.set_xlabel("Susceptible share of each 90 m cell (%, bin start)")
ax.set_ylabel("Share of acres (%)"); ax.grid(axis="y", color=S.GRID, lw=0.6); ax.set_axisbelow(True)
ax.set_title("USGS landslide susceptibility", fontsize=10)
ax.legend(loc="upper left", fontsize=7.8)
fig.suptitle("Roadless areas sit on failure-prone ground; Helene landslides were mapped\nthere at about five times the density", x=0.012, y=0.985, ha="left", va="top", fontsize=11.5, fontweight="bold", linespacing=1.25)
fig.subplots_adjust(left=0.19, right=0.985, top=0.80, bottom=0.2, wspace=0.28)
S.footer(fig, "Sources: USGS preliminary Helene landslide inventory (Burgi et al. 2024, point data, reviewed version); USGS slope-relief landslide susceptibility (Mirus et al. 2024, n10 model); USFS ownership and IRA layers.\nDescriptive only: rainfall, slope, mapping effort and canopy differ between areas. Inventory is preliminary and incomplete. Not evidence that logging or roads caused any landslide.", y=0.008)
fig.savefig("figures/fig5_hazard.png", dpi=220); fig.savefig("figures/fig5_hazard.pdf")
print(res.round(3).to_string())

# ---------------- water ----------------
t = pd.read_csv("data/processed/water_huc_ira_overlap.csv")
w = json.load(open("data/processed/water_summary.json"))
fig, axs = plt.subplots(1, 2, figsize=(9.6, 4.6), gridspec_kw=dict(width_ratios=[1.2, 1]))
ax = axs[0]
top = t[t.sum_pop > 0].sort_values("sum_pop", ascending=False).head(10).iloc[::-1]
labels = [f"{n.title()} ({s})" for n, s in zip(top.name, top.states)]
ax.barh(range(len(top)), top.sum_pop / 1000, color=S.BLUE, height=0.62, zorder=2)
for i, (p, sh) in enumerate(zip(top.sum_pop, top.ira_share)):
    ax.text(p / 1000 + 2, i, f"{p/1000:,.0f}k  ({100*sh:.0f}% roadless)", va="center", fontsize=7.4, color=S.INK)
ax.set_yticks(range(len(top))); ax.set_yticklabels(labels, fontsize=7.6)
ax.set_xlabel("People served by surface-water intakes located in the watershed (thousands)")
ax.set_xlim(0, 190); ax.grid(axis="x", color=S.GRID, lw=0.6); ax.set_axisbelow(True)
ax.set_title("Ten largest drinking-water watersheds that contain roadless land", fontsize=10)
ax = axs[1]; ax.axis("off")
big = [(f"{w['n_huc12_with_ira']:,}", "HUC12 watersheds contain\n500+ acres of roadless land"),
       (f"{int(w['sw_intakes_in_ira_huc12']):,}", "surface-water intakes\nlocated in them"),
       (f"{w['sum_pop_in_ira_huc12']/1000:,.0f}k", "people served by\nthose intakes"),
       (f"{w['unique_sum_pop_in_or_downstream_hops_5']/1e6:.1f}M", "served in or within 5\nwatersheds downstream\n(lower bound)")]
y = 0.90
for big_n, txt in big:
    ax.text(0.02, y, big_n, fontsize=22, fontweight="bold", color=S.BLUE, va="center", transform=ax.transAxes)
    ax.text(0.36, y, txt, fontsize=7.6, color=S.INK2, va="center", transform=ax.transAxes, linespacing=1.25)
    y -= 0.19
sens = pd.read_csv("data/processed/water_sensitivity.csv")
lo, hi = sens.population_served.min(), sens.population_served.max()
ax.text(0.02, 0.12, f"Depending on how much roadless land a\nwatershed must contain, population served\nranges from {lo/1000:,.0f}k to {hi/1000:,.0f}k. For comparison, the DEIS\n(Table 35) reports 378 intakes serving 614,600\npeople for the whole Southern Region.", fontsize=7.6, color=S.INK2, va="top", transform=ax.transAxes)
fig.suptitle("Drinking water: hundreds of thousands of people draw from watersheds containing roadless land", x=0.012, y=0.985, ha="left", fontsize=11.5, fontweight="bold")
fig.subplots_adjust(left=0.235, right=0.985, top=0.86, bottom=0.17, wspace=0.12)
S.footer(fig, "Sources: USFS Forests to Faucets 2.0 (HUC12; SDWIS-derived intake counts and populations); 2001 IRA inventory.\nPopulations count consumers of intakes located in each watershed; they are not estimates of people affected by land use.", y=0.008)
fig.savefig("figures/fig6_water.png", dpi=220); fig.savefig("figures/fig6_water.pdf")
print("ok")
