"""Step 3. Every statistic: writes data/results.json, data/domesday_places_traces.csv,
data/county_mills.csv and data/page_data.json.

Run: python3 code/03_analysis.py
"""
import json, os
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from pyproj import Transformer
from scipy.spatial import cKDTree
from scipy.stats import spearmanr, mannwhitneyu

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
R = {}
CNT = json.load(open(os.path.join(ROOT, "work", "domesday_counts.json")))
R["domesday"] = {k: v for k, v in CNT.items() if k != "by_county"}
R["domesday"]["quoted_5624"] = 5624
R["domesday"]["quoted_6082"] = 6082
R["domesday"]["diff_vs_5624"] = round(CNT["mills_total"] - 5624, 2)
R["domesday"]["diff_vs_6082"] = round(CNT["mills_total"] - 6082, 2)

D = pd.read_csv(os.path.join(ROOT, "work", "domesday_setting.csv"), dtype={"placeId": str})
M = pd.read_csv(os.path.join(ROOT, "data", "modern_mills.csv"), keep_default_na=False)
for c in ["lat", "lon", "river_m", "named_river_m", "elev_m", "relief1km_m", "nearest_domesday_mill_km", "nearest_domesday_place_km"]:
    M[c] = pd.to_numeric(M[c], errors="coerce")
M["x"], M["y"] = T.transform(M.lon.values, M.lat.values)
D["x"], D["y"] = T.transform(D.lng.values, D.lat.values)
D["has_mill"] = D.mills1086 > 0
D["hh"] = D.households1086.fillna(0)

# ---------------- counts of modern traces
UK = M
EN = M[M.country == "England"]
R["modern"] = dict(
    rows=int(len(M)), osm=int((M.source == "OSM").sum()), wikidata=int((M.source == "Wikidata").sum()),
    osnames=int((M.source == "OS Open Names").sum()),
    by_country={k: int(v) for k, v in M.groupby("country").size().items()},
    england_by_kind={k: int(v) for k, v in EN.groupby("kind").size().items()},
    england_by_source_kind={f"{a}|{b}": int(v) for (a, b), v in EN.groupby(["source", "kind"]).size().items()},
    uk_by_kind={k: int(v) for k, v in M.groupby("kind").size().items()},
)

# ---------------- trace layers and distances from Domesday places
LAYERS = {
    "built": M.kind.isin(["water", "wind", "textile", "industry", "mill"]),
    "water": M.kind == "water",
    "wind": M.kind == "wind",
    "name": M.kind == "name",
    "any": M.kind.notna(),
}
for k, mask in LAYERS.items():
    S = M[mask]
    tr = cKDTree(np.c_[S.x.values, S.y.values])
    d, _ = tr.query(np.c_[D.x.values, D.y.values])
    D[f"d_{k}_m"] = np.round(d)
DE = D[D.has_entries].copy()  # places with a Domesday entry describing them
# Hull sometimes lists two places of the same name in the same grid square (separate holdings):
# merge them into one place, summing their mills and households.
n_before = len(DE)
agg = {c: "first" for c in DE.columns if c not in ("name", "gridRef", "countyName")}
agg.update(mills1086="sum", hh="sum", households1086="sum")
DE = DE.groupby(["name", "gridRef", "countyName"], as_index=False).agg(agg)
DE["has_mill"] = DE.mills1086 > 0
R_merge = dict(rows_with_entries=n_before, places_after_merge=int(len(DE)), merged=int(n_before - len(DE)))
R["sample"] = dict(**R_merge, places=int(len(DE)), mill_places=int(DE.has_mill.sum()), no_mill_places=int((~DE.has_mill).sum()),
                   england=int((DE.country == "England").sum()))

# households quintile strata for local expectation
DE["hq"] = pd.qcut(DE.hh.rank(method="first"), 5, labels=False)
DE["stratum"] = DE.countyName + "|" + DE.hq.astype(str)


def share_block(km):
    out = {}
    for k in LAYERS:
        hit = DE[f"d_{k}_m"] <= km * 1000
        DE["_h"] = hit.astype(int)
        mill = DE[DE.has_mill]; no = DE[~DE.has_mill]
        # local expectation: share among no-mill places in the same county and households quintile
        sr = no.groupby("stratum")._h.mean()
        exp = mill.stratum.map(sr)
        ok = exp.notna()
        out[k] = dict(mill=round(mill._h.mean(), 4), nomill=round(no._h.mean(), 4), ratio=round(mill._h.mean() / max(no._h.mean(), 1e-9), 3),
                      mill_n=int(mill._h.sum()), nomill_n=int(no._h.sum()),
                      expected_local=round(exp[ok].mean(), 4), obs_matched=round(mill._h[ok].mean(), 4),
                      ratio_local=round(mill._h[ok].mean() / exp[ok].mean(), 3), matched_n=int(ok.sum()))
    return out


R["share"] = {{0.5: "500m", 1: "1km", 2: "2km"}[km]: share_block(km) for km in (0.5, 1, 2)}
# distance curve for the chart
curve = []
for km in (0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4, 5):
    row = dict(km=km)
    for k in ("water", "wind", "name", "built"):
        h = DE[f"d_{k}_m"] <= km * 1000
        row[f"{k}_mill"] = round(h[DE.has_mill].mean(), 4); row[f"{k}_nomill"] = round(h[~DE.has_mill].mean(), 4)
    curve.append(row)
R["curve"] = curve

# dose response by number of mills
DE["mclass"] = pd.cut(DE.mills1086, [-1, 0, 0.99, 1.0, 2.0, 1e9], labels=["none", "part of a mill", "1", "2", "3 or more"])
dose = []
for cl, g in DE.groupby("mclass", observed=True):
    dose.append(dict(cls=str(cl), n=int(len(g)), water1=round((g.d_water_m <= 1000).mean(), 4), any1=round((g.d_any_m <= 1000).mean(), 4),
                     name1=round((g.d_name_m <= 1000).mean(), 4), wind1=round((g.d_wind_m <= 1000).mean(), 4), built1=round((g.d_built_m <= 1000).mean(), 4)))
R["dose"] = dose
R["dose_ratio_water_3plus_vs_none"] = round(dose[-1]["water1"] / dose[0]["water1"], 2)

# logistic regressions with county fixed effects and setting controls
DE["lhh"] = np.log1p(DE.hh); DE["lriver"] = np.log10(DE.river_m + 50); DE["lrel"] = np.log10(DE.relief1km_m + 5)
DE["cty"] = DE.countyName
models = {}
for k in ("water", "built", "name", "wind", "any"):
    DE["y"] = (DE[f"d_{k}_m"] <= 1000).astype(int)
    f = "y ~ has_mill + lhh + lriver + lrel + C(cty)"
    try:
        pos = DE.groupby("cty").y.transform("max") > 0  # drop counties with no trace at all (no variation)
        m = smf.logit(f, data=DE[pos].assign(has_mill=DE[pos].has_mill.astype(int))).fit(disp=0, maxiter=200)
        b = m.params["has_mill"]; lo, hi = m.conf_int().loc["has_mill"]
        models[k] = dict(or_=round(float(np.exp(b)), 2), lo=round(float(np.exp(lo)), 2), hi=round(float(np.exp(hi)), 2), p=float(m.pvalues["has_mill"]),
                         or_river=round(float(np.exp(m.params["lriver"])), 2), n=int(m.nobs))
    except Exception as e:  # pragma: no cover
        models[k] = dict(error=str(e))
R["models_1km"] = models

# setting of mill places
R["setting"] = dict(
    river_m_mill=float(DE[DE.has_mill].river_m.median()), river_m_nomill=float(DE[~DE.has_mill].river_m.median()),
    named_river_m_mill=float(DE[DE.has_mill].named_river_m.median()), named_river_m_nomill=float(DE[~DE.has_mill].named_river_m.median()),
    within500_river_mill=round((DE[DE.has_mill].river_m <= 500).mean(), 4), within500_river_nomill=round((DE[~DE.has_mill].river_m <= 500).mean(), 4),
    hh_mill=float(DE[DE.has_mill].hh.median()), hh_nomill=float(DE[~DE.has_mill].hh.median()),
    relief_mill=float(DE[DE.has_mill].relief1km_m.median()), relief_nomill=float(DE[~DE.has_mill].relief1km_m.median()),
)

# ---------------- counties: 1086 vs today
cnt = pd.DataFrame(CNT["by_county"]).rename(columns={"name": "county", "mills": "mills1086", "entries": "mill_entries"})
hh = DE.groupby("countyName").agg(households1086=("hh", "sum"), places=("placeId", "size"), mill_places=("has_mill", "sum")).reset_index().rename(columns={"countyName": "county"})
E = M[(M.domesday_county != "") & (M.country != "Northern Ireland")]
mod = E.groupby("domesday_county").agg(
    traces_built=("kind", lambda s: int(s.isin(["water", "wind", "textile", "industry", "mill"]).sum())),
    traces_water=("kind", lambda s: int((s == "water").sum())), traces_wind=("kind", lambda s: int((s == "wind").sum())),
    traces_textile=("kind", lambda s: int((s == "textile").sum())), mill_names=("kind", lambda s: int((s == "name").sum()))).reset_index().rename(columns={"domesday_county": "county"})
CT = cnt.merge(hh, on="county", how="left").merge(mod, on="county", how="left").fillna(0)
CT["mills_per_100hh"] = (CT.mills1086 / CT.households1086.replace(0, np.nan) * 100).round(2)
CT = CT.sort_values("mills1086", ascending=False)
CT.to_csv(os.path.join(ROOT, "data", "county_mills.csv"), index=False)
cc = {}
for k in ("traces_built", "traces_water", "traces_wind", "mill_names"):
    r, p = spearmanr(CT.mills1086, CT[k]); cc[k] = dict(rho=round(float(r), 2), p=float(p))
r, p = spearmanr(CT.mills1086, CT.households1086); cc["households1086"] = dict(rho=round(float(r), 2), p=float(p))
R["counties_max_per100"] = CT.sort_values("mills_per_100hh", ascending=False).iloc[0][["county", "mills_per_100hh"]].to_dict()
R["counties"] = dict(n=int(len(CT)), spearman=cc, rows=CT.round(2).to_dict("records"),
                     top=CT.head(5).county.tolist(), by_name={r["county"]: r for r in CT.round(2).to_dict("records")})

# ---------------- textile traces: did they reuse old mill places?
EN = M[M.country == "England"].copy()
grp = {"textile": EN.kind == "textile", "water": EN.kind == "water", "wind": EN.kind == "wind", "mill": EN.kind == "mill"}
tex = {}
for k, mask in grp.items():
    S = EN[mask]
    tex[k] = dict(n=int(len(S)), med_km=round(float(S.nearest_domesday_mill_km.median()), 2),
                  within1=round(float((S.nearest_domesday_mill_km <= 1).mean()), 4), within2=round(float((S.nearest_domesday_mill_km <= 2).mean()), 4),
                  med_place_km=round(float(S.nearest_domesday_place_km.median()), 2),
                  river_m=float(S.river_m.median()), elev_m=float(S.elev_m.median()), relief_m=float(S.relief1km_m.median()),
                  regions={a: int(b) for a, b in S.region.value_counts().items()})
R["textile"] = tex
T_ = EN[EN.kind == "textile"]
R["textile"]["north_share"] = round(float(T_.region.isin(["North West", "Yorkshire and the Humber"]).mean()), 4)
R["textile"]["river100"] = {k: round(float((EN[grp[k]].river_m <= 100).mean()), 4) for k in grp}
R["textile"]["north_west_n"] = int((T_.region == "North West").sum())
# same-region comparison: North West and Yorkshire only
NR = EN[EN.region.isin(["North West", "Yorkshire and the Humber"])]
same = {}
for k in ("textile", "water", "wind", "mill"):
    S = NR[NR.kind == k]
    same[k] = dict(n=int(len(S)), med_km=round(float(S.nearest_domesday_mill_km.median()), 2), within2=round(float((S.nearest_domesday_mill_km <= 2).mean()), 4))
u = mannwhitneyu(NR[NR.kind == "textile"].nearest_domesday_mill_km, NR[NR.kind == "water"].nearest_domesday_mill_km)
same["p_textile_vs_water"] = float(u.pvalue)
R["textile"]["north"] = same
# Domesday coverage by region: mill places and mills
DR = DE[DE.country == "England"].groupby("region").agg(places=("placeId", "size"), mill_places=("has_mill", "sum"), mills=("mills1086", "sum")).reset_index()
R["region_domesday"] = {r.region: dict(places=int(r.places), mill_places=int(r.mill_places), mills=round(float(r.mills), 1)) for r in DR.itertuples()}
# textile mills inside the area Domesday covered well: within 5 km of any Domesday place
cov = T_[T_.nearest_domesday_place_km <= 5]
R["textile"]["in_coverage"] = dict(n=int(len(cov)), within2=round(float((cov.nearest_domesday_mill_km <= 2).mean()), 4), med_km=round(float(cov.nearest_domesday_mill_km.median()), 2))
wcov = EN[(EN.kind == "water") & (EN.nearest_domesday_place_km <= 5)]
R["textile"]["water_in_coverage"] = dict(n=int(len(wcov)), within2=round(float((wcov.nearest_domesday_mill_km <= 2).mean()), 4), med_km=round(float(wcov.nearest_domesday_mill_km.median()), 2))
# terrain at Domesday mill places for comparison
R["textile"]["domesday_mill_places"] = dict(river_m=float(DE[DE.has_mill].river_m.median()), elev_m=float(DE[DE.has_mill].elev_m.median()), relief_m=float(DE[DE.has_mill].relief1km_m.median()))
edges = [0, 1, 2, 5, 10, 20, 50, 1000]
R["textile"]["bands"] = dict(edges=edges, **{k: [round(float(v), 4) for v in np.histogram(EN[grp[k]].nearest_domesday_mill_km.clip(0, 999), bins=edges)[0] / grp[k].sum()] for k in grp})
# examples of textile traces nearest to a Domesday mill place
ex = T_.sort_values("nearest_domesday_mill_km").head(8)
R["textile"]["closest"] = [dict(name=r.name, place=r.nearest_domesday_mill_place, km=round(float(r.nearest_domesday_mill_km), 2), source=r.source) for r in ex.itertuples()]
R["textile"]["farthest_example"] = [dict(name=r.name, km=round(float(r.nearest_domesday_mill_km), 1)) for r in T_.sort_values("nearest_domesday_mill_km", ascending=False).head(5).itertuples()]

# ---------------- headline places: biggest mill places and whether a trace survives
big = DE.sort_values("mills1086", ascending=False).head(25)
R["top_places"] = [dict(name=r.name, county=r.countyName, mills=round(float(r.mills1086), 2), hh=round(float(r.hh)),
                        water1=bool(r.d_water_m <= 1000), built1=bool(r.d_built_m <= 1000), name1=bool(r.d_name_m <= 1000),
                        nearest_built_m=int(r.d_built_m)) for r in big.itertuples()]
R["examples"] = {r.name: dict(mills=round(float(r.mills1086), 2), hh=round(float(r.hh)), d_water_m=int(r.d_water_m), d_built_m=int(r.d_built_m), d_name_m=int(r.d_name_m))
                  for r in DE[DE.name.isin(["Tealby", "Derby", "Leominster", "Louth", "Alresford", "Bosham"])].sort_values("mills1086").itertuples()}
R["top_places_n"] = len(R["top_places"])
R["top_places_traced"] = int(sum(1 for t in R["top_places"] if t["built1"] or t["name1"]))

# ---------------- write the place table and page data
keep = ["placeId", "name", "county", "countyName", "gridRef", "lat", "lng", "households1086", "mills1086", "openDomesdayPath", "region",
        "river_m", "named_river_m", "elev_m", "relief1km_m", "d_built_m", "d_water_m", "d_wind_m", "d_name_m", "d_any_m"]
DE[keep].to_csv(os.path.join(ROOT, "data", "domesday_places_traces.csv"), index=False)
pg = dict(
    dm=[[round(r.lat, 4), round(r.lng, 4), r.name, round(float(r.mills1086), 2), int(round(r.hh)), r.countyName, int(r.d_built_m), int(r.d_water_m), int(r.d_name_m), r.openDomesdayPath or ""]
        for r in DE[DE.has_mill].itertuples()],
    dn=[[round(r.lat, 3), round(r.lng, 3)] for r in DE[~DE.has_mill].itertuples()],
    mm=[[round(r.lat, 4), round(r.lon, 4), r.kind, r.name, r.source[0], r.id if r.source != "OS Open Names" else ""] for r in M[M.country != "Northern Ireland"].itertuples()],
)
json.dump(pg, open(os.path.join(ROOT, "data", "page_data.json"), "w"), separators=(",", ":"), ensure_ascii=False)


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list):
        return [clean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    return o


json.dump(clean(R), open(os.path.join(ROOT, "data", "results.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps(clean({k: R[k] for k in ("sample", "share", "models_1km", "setting", "textile", "dose")}), indent=1)[:9000])
print(R["counties"]["spearman"]); print(R["top_places_traced"]); print(R["region_domesday"])
