"""Step 1. Domesday mills, entry by entry and place by place.

Reads the realm-domesday reference YAML (Hull Domesday Project coding, CC BY-NC-SA) and
the place table of the Domesday Destiny study, and writes:
  data/domesday_mill_places.csv  one row per Domesday place with coordinates: mills in 1086
                                 (entry figures shared equally among the places an entry
                                 describes), households in 1086, county.
  work/domesday_counts.json      entry-level totals used in results.json.

Run: python3 code/01_domesday.py [/path/to/realm-domesday]
"""
import glob, json, os, sys
from collections import defaultdict, Counter
import pandas as pd
import yaml

L = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/hist/realm-domesday"
DD = "/home/claude/hist/domesday-destiny/data/domesday_places.csv"
os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)

tot = 0.0; n_entries = 0; n_frac = 0; no_place = 0.0
by_cty = Counter(); by_cty_entries = Counter(); by_ed = Counter()
alloc = defaultdict(float); dist = Counter()
for f in sorted(glob.glob(os.path.join(REPO, "reference", "05-entries-*.yml"))):
    for d in yaml.load(open(f, encoding="utf-8"), Loader=L) or []:
        e = d["data"]; m = e.get("mills")
        if m is None or isinstance(m, bool) or float(m) <= 0:
            continue
        m = float(m)
        tot += m; n_entries += 1; by_cty[e["county"]] += m; by_cty_entries[e["county"]] += 1
        by_ed[e.get("edition")] += m
        if m != int(m):
            n_frac += 1
        dist["1" if m == 1 else "2" if m == 2 else "half or 1.5" if m in (0.5, 1.5) else "3 or more" if m >= 3 else "other"] += 1
        t = [r["to"]["placeId"] for r in d.get("relations", []) if r["predicate"] == "DESCRIBES" and r["to"].get("type") == "DomesdayPlace"]
        if not t:
            no_place += m; continue
        for pid in t:
            alloc[str(pid)] += m / len(t)

P = pd.read_csv(DD, dtype={"placeId": str}, keep_default_na=False)
P["mills1086"] = P.placeId.map(alloc).fillna(0).round(3)
P["households1086"] = pd.to_numeric(P.households1086, errors="coerce")
P["lat"] = pd.to_numeric(P.lat, errors="coerce"); P["lng"] = pd.to_numeric(P.lng, errors="coerce")
P["has_entries"] = P.entries.astype(int) > 0
keep = ["placeId", "name", "county", "countyName", "gridRef", "lat", "lng", "has_entries", "households1086", "mills1086", "openDomesdayPath"]
P = P[keep]
out = P[P.lat.notna()].copy()
out.to_csv(os.path.join(ROOT, "data", "domesday_mill_places.csv"), index=False)

cn = dict(zip(P.county, P.countyName))
res = dict(
    mills_total=round(tot, 2), entries_with_mills=n_entries, entries_fractional=n_frac,
    mills_no_place=round(no_place, 2), mills_little_domesday=round(by_ed.get("Little Domesday", 0), 2),
    mills_great_domesday=round(by_ed.get("Great Domesday", 0), 2),
    entry_size_dist=dict(dist),
    places_total=int(len(P)), places_with_coords=int(len(out)),
    places_with_mill=int((out.mills1086 > 0).sum()), places_with_mill_all=int((P.mills1086 > 0).sum()),
    mills_on_placed=round(float(out.mills1086.sum()), 2),
    by_county=[dict(code=k, name=cn.get(k, k), mills=round(v, 2), entries=by_cty_entries[k]) for k, v in by_cty.most_common()],
)
json.dump(res, open(os.path.join(ROOT, "work", "domesday_counts.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "by_county"}, indent=1))
