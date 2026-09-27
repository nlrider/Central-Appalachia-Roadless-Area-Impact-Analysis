"""Drinking-water context of core-Appalachian roadless areas using Forests to Faucets 2.0 (HUC12).

Outputs:
  data/processed/water_huc_ira_overlap.csv  - HUC12s intersecting IRAs, with IRA share and F2F attributes
  data/processed/water_summary.json         - headline numbers
Caveats built in: study bbox truncates downstream traversal (lower bound); SUM_POP counts consumers of intakes
located in a HUC12, not people 'affected' by upstream land use.
"""
import geopandas as gpd, pandas as pd, numpy as np, json

huc = gpd.read_file("data/raw/fs_services/forests_to_faucets_2.geojson").set_crs(4326).to_crs(5070)
ira = gpd.read_file("data/processed/ira_core_appalachia.gpkg").to_crs(5070)
huc["geometry"] = huc.geometry.make_valid()
ira["geometry"] = ira.geometry.make_valid()
huc["huc_area_ac"] = huc.geometry.area / 4046.8564224
ira_u = ira.geometry.union_all().buffer(0)
inter = huc.copy()
inter["ira_ac"] = huc.geometry.intersection(ira_u).area / 4046.8564224
inter["ira_share"] = inter.ira_ac / inter.huc_area_ac
MATERIAL_AC = 500   # primary definition: a HUC12 'contains roadless land' if >= 500 IRA acres (sensitivity table covers 1 ac to 10% of area)
touch_any = inter[inter.ira_ac > 1].copy()
touch = inter[inter.ira_ac >= MATERIAL_AC].copy()
print(len(touch), f"HUC12s contain >= {MATERIAL_AC} acres of roadless area (", len(touch_any), "with any overlap) of", len(huc), "HUC12s in bbox")

# downstream traversal (within bbox only)
to = dict(zip(huc.huc12, huc.tohuc))
pop = dict(zip(huc.huc12, huc.sum_pop.fillna(0)))
def downstream(h, maxhops=None):
    """HUC12s hydrologically downstream of h (within the study bbox), following TOHUC links."""
    out, cur, hops = [], h, 0
    visited = {h}
    while maxhops is None or hops < maxhops:
        nxt = to.get(cur)
        if nxt is None or nxt in visited or nxt not in pop:
            break
        out.append(nxt); visited.add(nxt); cur = nxt; hops += 1
    return out
summ = {}
own = set(touch.huc12)
summ["n_huc12_with_ira"] = len(own)
summ["ira_acres_total_in_huc_overlay"] = float(touch.ira_ac.sum())
summ["huc12_acres_total"] = float(touch.huc_area_ac.sum())
summ["sw_intakes_in_ira_huc12"] = int(touch.sw.fillna(0).sum())
summ["sum_pop_in_ira_huc12"] = float(touch.sum_pop.fillna(0).sum())
summ["n_huc12_with_ira_and_intake"] = int((touch.sw.fillna(0) > 0).sum())
for hops in (1, 3, 5, None):
    ds = set()
    for h in own:
        ds.update(downstream(h, hops))
    ds = ds | own
    key = f"unique_sum_pop_in_or_downstream_hops_{hops}"
    summ[key] = float(sum(pop.get(h, 0) for h in ds))
    summ[f"n_huc12_in_or_downstream_hops_{hops}"] = len(ds)
# reference: how do IRA-containing HUC12s rank on F2F 'important area for surface drinking water' (IMP_R 0-100 quantile) vs other HUC12s in the same states
bbox_all = huc[huc.level_.notna()]
summ["imp_r_mean_ira_huc12"] = float(touch.imp_r.mean())
summ["imp_r_mean_other_huc12"] = float(inter[inter.ira_ac <= 1].imp_r.mean())
sens = []
for lab, m in [("any overlap (>1 ac)", inter.ira_ac > 1), (">=100 ac", inter.ira_ac >= 100), (">=500 ac (primary)", inter.ira_ac >= 500), (">=1,000 ac", inter.ira_ac >= 1000), (">=5% of watershed", inter.ira_share >= .05), (">=10% of watershed", inter.ira_share >= .10)]:
    q = inter[m]; sens.append({"definition": lab, "n_huc12": len(q), "ira_acres": q.ira_ac.sum(), "intakes": q.sw.fillna(0).sum(), "population_served": q.sum_pop.fillna(0).sum(), "huc12_with_intake": int((q.sw.fillna(0) > 0).sum())})
pd.DataFrame(sens).to_csv("data/processed/water_sensitivity.csv", index=False)
summ["apcw_r_mean_ira_huc12"] = float(touch.apcw_r.mean())
summ["apcw_r_mean_other_huc12"] = float(inter[inter.ira_ac <= 1].apcw_r.mean())
summ["per_forest_mean_ira_huc12"] = float(touch.per_for.mean())
# independent cross-check of agency wildfire-hazard framing: IRA-acre-weighted share of HUC12 with high/very-high Wildfire Hazard Potential (F2F PER_WFP)
w = touch.ira_ac / touch.ira_ac.sum()
summ["ira_weighted_per_wfp_high_vhigh"] = float((w * touch.per_wfp.fillna(0)).sum())
summ["ira_weighted_per_idrisk"] = float((w * touch.per_idrisk.fillna(0)).sum())
summ["ira_weighted_per_impv"] = float((w * touch.per_impv.fillna(0)).sum())
json.dump(summ, open("data/processed/water_summary.json", "w"), indent=1)
cols = ["huc12", "name", "states", "huc_area_ac", "ira_ac", "ira_share", "sw", "sw_pop", "sum_pop", "pop_ds", "imp_r", "apcw_r", "per_for", "per_fornfs", "per_impv", "level_", "tohuc"]
touch[cols].sort_values("ira_share", ascending=False).to_csv("data/processed/water_huc_ira_overlap.csv", index=False)
print(json.dumps(summ, indent=1))
