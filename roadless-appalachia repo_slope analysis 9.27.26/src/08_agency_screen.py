"""Apply the Forest Service's own DEIS operability screen to Appalachian roadless areas, and validate it against actual harvests.

DEIS Vol. I (pp. 73-74) defines, for forested IRA land:
  Likely operable          : < 0.5 mi from a road AND slope < 40 %  (+ productive site, no statutory restriction)
  Likely operable, complex : (< 0.5 mi AND 40-70 % slope)  OR  (0.5-1 mi AND slope < 70 %)
  Likely not operable      : everything else
We can apply the slope and road-distance parts (not site productivity or statutory restrictions), so the shares below are UPPER BOUNDS
on operability relative to the agency's full screen.

Inputs : data/processed/joint_ira.npz, joint_harvest.npz  (slope-bin x road-distance-bin acre histograms per polygon)
Outputs: data/processed/agency_screen_by_forest.csv, agency_screen_sensitivity.csv
"""
import numpy as np, pandas as pd, sys

S_EDGES = np.arange(0, 205, 5.0)          # 40 slope bins (percent)
D_EDGES = np.arange(0, 3050, 50.0)        # 60 distance bins (m); last bin also holds > 3000 m
MI = 1609.344


def cdf_axis(edges, thr):
    """Weights (per bin) giving the fraction of each bin lying below thr (uniform within bin)."""
    lo, hi = edges[:-1], edges[1:]
    w = np.clip((thr - lo) / (hi - lo), 0, 1)
    return w


def screen(hist, s_op=40, s_cx=70, d_op=0.5 * MI, d_cx=1.0 * MI):
    """hist: (..., n_slope, n_dist) acres. Returns dict of acres in each class."""
    ws_op, ws_cx = cdf_axis(S_EDGES, s_op), cdf_axis(S_EDGES, s_cx)
    wd_op, wd_cx = cdf_axis(D_EDGES, d_op), cdf_axis(D_EDGES, d_cx)
    tot = hist.sum(axis=(-1, -2))
    def a(ws, wd): return np.einsum("...sd,s,d->...", hist, ws, wd)
    operable = a(ws_op, wd_op)
    near_cx = a(ws_cx, wd_op) - operable                 # <0.5mi & 40-70 %
    mid_cx = a(ws_cx, wd_cx) - a(ws_cx, wd_op)           # 0.5-1 mi & <70 %
    cx = near_cx + mid_cx
    return {"total": tot, "operable": operable, "complex": cx, "not_operable": tot - operable - cx,
            "gt_slope_op": tot - a(ws_op, np.ones_like(wd_op)), "gt_dist_op": tot - a(np.ones_like(ws_op), wd_op)}


FOREST_MAP = {"George Washington": "GW&J", "Jefferson": "GW&J", "Monongahela": "Monongahela", "Pisgah": "Pisgah-Nantahala",
              "Nantahala": "Pisgah-Nantahala", "Cherokee": "Cherokee", "Chattahoochee": "Chattahoochee", "Daniel Boone": "Daniel Boone",
              "Allegheny": "Allegheny"}
HARV_MAP = {"George Washington and Jefferson National Forest": "GW&J", "Monongahela National Forest": "Monongahela",
            "National Forests in North Carolina": "Pisgah-Nantahala", "Cherokee National Forest": "Cherokee",
            "Chattahoochee-Oconee National Forests": "Chattahoochee", "Daniel Boone National Forest": "Daniel Boone",
            "Allegheny National Forest": "Allegheny"}


def load(tag):
    z = np.load(f"data/processed/joint_{tag}.npz")
    return z["pids"], z["hist"].astype(np.float64)


def by_group(hist, groups, **kw):
    rows = []
    for g in sorted(set(groups)) + ["ALL"]:
        m = np.ones(len(groups), bool) if g == "ALL" else np.array([x == g for x in groups])
        h = hist[m].sum(axis=0)
        r = screen(h, **kw)
        r = {k: float(v) for k, v in r.items()}
        rows.append({"group": g, **r, **{f"share_{k}": r[k] / r["total"] for k in ("operable", "complex", "not_operable", "gt_slope_op", "gt_dist_op")}})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ira_a = pd.read_csv("data/processed/ira_attributes.csv")
    pids, H = load("ira")
    fg = ira_a.set_index("pid").loc[pids].FOREST.map(FOREST_MAP).tolist()
    out = by_group(H, fg).assign(kind="IRA")
    frames = [out]
    try:
        hp, HH = load("harvest")
        hv = pd.read_csv("data/processed/harvest_attributes.csv").set_index("pid").loc[hp]
        hv["fy"] = pd.to_numeric(hv.fy_completed, errors="coerce")
        for name, mask in [("harvest_FY>=2001", hv.fy >= 2001), ("harvest_all", np.ones(len(hv), bool))]:
            m = np.asarray(mask)
            g = hv.admin_forest_name.map(HARV_MAP).values[m].tolist()
            frames.append(by_group(HH[m], g).assign(kind=name))
    except FileNotFoundError:
        print("harvest joint results not available yet")
    res = pd.concat(frames, ignore_index=True)
    res.to_csv("data/processed/agency_screen_by_forest.csv", index=False)
    pd.set_option("display.width", 250)
    print(res[["kind", "group", "total", "share_operable", "share_complex", "share_not_operable", "share_gt_slope_op", "share_gt_dist_op"]].round(3).to_string())
    # sensitivity of the IRA result to thresholds (slope +-10 pts, distance +-0.25 mi)
    sens = []
    for s_op, s_cx, d_op, d_cx, lab in [(40, 70, .5, 1, "agency"), (30, 60, .5, 1, "slope -10"), (50, 80, .5, 1, "slope +10"),
                                       (40, 70, .25, .75, "distance -0.25 mi"), (40, 70, .75, 1.25, "distance +0.25 mi")]:
        r = screen(H.sum(axis=0), s_op=s_op, s_cx=s_cx, d_op=d_op * MI, d_cx=d_cx * MI)
        sens.append({"scenario": lab, **{k: float(v) / float(r["total"]) for k, v in r.items() if k in ("operable", "complex", "not_operable")}})
    sens = pd.DataFrame(sens); sens.to_csv("data/processed/agency_screen_sensitivity.csv", index=False)
    print(sens.round(3).to_string())
