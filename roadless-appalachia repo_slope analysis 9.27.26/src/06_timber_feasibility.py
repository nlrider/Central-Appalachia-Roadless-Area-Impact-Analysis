"""Empirical ("revealed") timber-feasibility screen for Appalachian roadless areas.

Idea: instead of assuming a slope cutoff, use where the Forest Service has actually harvested timber in the SAME forest
(FACTS timber-harvest polygons, treatment types = commercial thinning, regeneration cuts, selection, salvage, etc.) and ask what share of
roadless acres lies on ground no steeper than the p90 / p95 / p99 of that forest's own harvest slopes.
Slopes for both come from the same 10 m DEM pipeline, so the comparison is like-for-like.

Outputs: data/processed/timber_by_forest.csv, timber_bootstrap.csv, timber_summary.json
"""
import pandas as pd, numpy as np, json

EDGES = np.arange(0, 200, 5)
COLS = [f"s{e}" for e in EDGES]
FOREST_MAP = {  # IRA FOREST -> harvest admin_forest_name
    "George Washington": "George Washington and Jefferson National Forest", "Jefferson": "George Washington and Jefferson National Forest",
    "Monongahela": "Monongahela National Forest", "Pisgah": "National Forests in North Carolina", "Nantahala": "National Forests in North Carolina",
    "Cherokee": "Cherokee National Forest", "Chattahoochee": "Chattahoochee-Oconee National Forests",
    "Daniel Boone": "Daniel Boone National Forest", "Allegheny": "Allegheny National Forest"}
rng = np.random.default_rng(20260925)

ira_a = pd.read_csv("data/processed/ira_attributes.csv")
ira_s = pd.read_csv("data/processed/ira_slope_hist.csv")
ira = ira_a.merge(ira_s, on="pid")                               # pid is the same 1..n index in both scripts
ira["harv_forest"] = ira.FOREST.map(FOREST_MAP)
hv_a = pd.read_csv("data/processed/harvest_attributes.csv")
hv_s = pd.read_csv("data/processed/harvest_slope_hist.csv")
hv = hv_a.merge(hv_s, on="pid")
hv["fy"] = pd.to_numeric(hv.fy_completed, errors="coerce")

def wpct(hist, p):
    """acre-weighted percentile of slope from a 5-pt-bin histogram (linear interpolation within bin)."""
    c = np.cumsum(hist) / hist.sum()
    i = int(np.searchsorted(c, p))
    lo = EDGES[i]; prev = 0 if i == 0 else c[i - 1]
    return lo + 5 * (p - prev) / max(c[i] - prev, 1e-12)

def share_le(hist, thr):
    """share of acres with slope <= thr (thr interpolated within bin)."""
    c = np.cumsum(hist) / hist.sum()
    i = int(np.searchsorted(EDGES, thr, side="right") - 1)
    prev = 0 if i == 0 else c[i - 1]
    frac = (thr - EDGES[i]) / 5
    return prev + frac * (c[i] - prev)

def share_gt(hist, thr): return 1 - share_le(hist, thr)

HARVEST_SETS = {"FY>=2001": hv[hv.fy >= 2001], "all_years": hv}
rows, boot = [], []
groups = list(ira.groupby("harv_forest")) + [("ALL_CORE", ira)]
for fname, g in groups:
    ih = g[COLS].sum().values
    for hname, hsub in HARVEST_SETS.items():
        hs = hsub if fname == "ALL_CORE" else hsub[hsub.admin_forest_name == fname]
        if len(hs) < 30 or ih.sum() == 0:
            continue
        hh = hs[COLS].sum().values
        rec = {"forest": fname, "harvest_set": hname, "ira_acres": ih.sum(), "harvest_units": len(hs), "harvest_acres": hh.sum(),
               "ira_gt35": share_gt(ih, 35), "ira_gt45": share_gt(ih, 45), "ira_gt60": share_gt(ih, 60),
               "harv_gt35": share_gt(hh, 35), "harv_gt45": share_gt(hh, 45), "harv_gt60": share_gt(hh, 60),
               "ira_mean_slope": (g.acres_x_slope.sum() / g.acres_dem.sum()), "harv_mean_slope": (hs.acres_x_slope.sum() / hs.acres_dem.sum())}
        for p in (0.90, 0.95, 0.99):
            thr = wpct(hh, p)
            rec[f"harv_p{int(p*100)}_slope"] = thr
            rec[f"ira_share_le_harv_p{int(p*100)}"] = share_le(ih, thr)
        rows.append(rec)
        # bootstrap over harvest units (resample units with replacement) -> uncertainty on revealed-feasible share
        H = hs[COLS].values
        b = {p: [] for p in (90, 95, 99)}
        for _ in range(1000):
            idx = rng.integers(0, len(H), len(H))
            hb = H[idx].sum(axis=0)
            for p in b:
                b[p].append(share_le(ih, wpct(hb, p / 100)))
        for p in b:
            lo, hi = np.percentile(b[p], [2.5, 97.5])
            boot.append({"forest": fname, "harvest_set": hname, "pctile": p, "ira_share_le_lo95": lo, "ira_share_le_hi95": hi})
res = pd.DataFrame(rows)
res.to_csv("data/processed/timber_by_forest.csv", index=False)
pd.DataFrame(boot).to_csv("data/processed/timber_bootstrap.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(res[["forest", "harvest_set", "ira_acres", "harvest_units", "ira_gt35", "harv_gt35", "ira_gt60", "harv_gt60", "harv_p90_slope", "ira_share_le_harv_p90", "ira_share_le_harv_p95", "ira_share_le_harv_p99"]].round(3).to_string())
