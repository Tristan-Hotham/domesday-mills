"""Step 2. Modern traces of mills, and the setting of every point.

Inputs (read in place, not included):
  _data11/wd_osm_bundle11.json.gz  keys osm_mills (OpenStreetMap, ODbL) and wd_mills (Wikidata, CC0)
  osnames_gb.tsv                   OS Open Names (OGL v3): names containing the word Mill or Mills
  osrivers/Data/oprvrs_gb.gpkg     OS Open Rivers (OGL v3): distance to the nearest watercourse
  DEM (see dem.py)                 elevation and local relief within 1 km
Writes:
  data/modern_mills.csv            one row per OSM object, Wikidata item or OS Open Names feature
  work/domesday_setting.csv        river distance, elevation and relief for each Domesday place
Kinds: water (watermill, water mill, tide mill, corn and flour mills), wind (windmill, post, smock and
tower mills), textile (cotton mill class, or a label naming cotton, wool, woollen, worsted, silk, flax,
linen, lace, spinning, weaving, carding, fustian, shoddy or textile), industry (saw, paper, gunpowder,
bobbin, fulling, brass, flint, bone, snuff, smelt, slitting, blade, needle, forge), mill (unspecified),
name (an OS Open Names feature with Mill or Mills as a word).
"""
import csv, gzip, io, json, os, re, sqlite3, sys
import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree
from shapely import wkb, points
from shapely.strtree import STRtree

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from dem import DEM

H = "/home/claude/hist"
B = json.load(gzip.open(f"{H}/_data11/wd_osm_bundle11.json.gz"))["results"]
T = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)


def tsv(k):
    r = list(csv.reader(io.StringIO(B[k]["tsv"]), delimiter="\t", quoting=csv.QUOTE_NONE))
    return [dict(zip([c.lstrip("?") for c in r[0]], x)) for x in r[1:]]


def lit(s):
    m = re.match(r'^"(.*)"(@\w+|\^\^.*)?$', s or "")
    return m.group(1) if m else (s or "")


TEXTILE = re.compile(r"\b(cotton|wool|woollen|worsted|silk|flax|linen|lace|spinning|weaving|carding|fustian|shoddy|textile|mohair|jute|hosiery)\b", re.I)
INDUSTRY = re.compile(r"\b(saw|sawmill|paper|gunpowder|powder|bobbin|fulling|brass|flint|bone|snuff|smelt|slitting|blade|needle|forge|iron|steel|lead|bark|tuck|walk)\b", re.I)
WATER = re.compile(r"\b(water ?mill|watermill|corn|flour|grist|tide mill)\b", re.I)
WIND = re.compile(r"\b(windmill|post mill|smock mill|tower mill)\b", re.I)

rows = []
# ---- OpenStreetMap
seen = set()
for x in tsv("osm_mills"):
    osm = x["osm"].strip("<>")
    if osm in seen:
        continue
    seen.add(osm)
    v = lit(x["v"]); name = lit(x["name"])
    if v in ("windmill",):
        kind = "wind"
    elif v in ("watermill", "water_mill", "tide_mill"):
        kind = "water"
    else:
        kind = "textile" if TEXTILE.search(name) else "wind" if WIND.search(name) else "water" if WATER.search(name) else "industry" if INDUSTRY.search(name) else "mill"
    rows.append(dict(source="OSM", id=osm, name=name, kind=kind, detail=f"{x['k'].split(':')[-1].rstrip('>')}={v}",
                     lat=float(x["lat"]), lon=float(x["lon"]), start=lit(x["start"])))
# ---- Wikidata
items = {}
for x in tsv("wd_mills"):
    if not x["coord"]:
        continue
    it = items.setdefault(x["s"].strip("<>"), dict(label=lit(x["label"]), coord=x["coord"], cls=set(), inc=lit(x["inc"]), her=bool(x["herit"])))
    it["cls"].add(lit(x["clsl"]))
    it["her"] = it["her"] or bool(x["herit"])
for q, it in items.items():
    c = it["cls"]; lab = it["label"]
    if c & {"cotton mill", "textile mill", "woollen mill"} or TEXTILE.search(lab):
        kind = "textile"
    elif c & {"windmill", "tower mill", "post mill", "smock mill"} or WIND.search(lab):
        kind = "wind"
    elif c & {"watermill", "water mill", "tide mill", "corn mill", "flour mill"} or WATER.search(lab):
        kind = "water"
    elif c & {"sawmill", "paper mill", "gunpowder mill", "bobbin mill", "fulling mill", "horse mill"} or INDUSTRY.search(lab):
        kind = "industry"
    else:
        kind = "mill"
    lon, lat = map(float, re.findall(r"[-\d.]+", it["coord"])[:2])
    rows.append(dict(source="Wikidata", id=q, name=lab, kind=kind, detail="; ".join(sorted(c)), lat=lat, lon=lon,
                     start=it["inc"][:10], heritage=it["her"]))
# ---- OS Open Names
O = pd.read_csv(f"{H}/osnames_gb.tsv", sep="\t", keep_default_na=False, dtype=str)
O["lat"] = O.lat.astype(float); O["lon"] = O.lon.astype(float)
mill = O[O.name1.str.contains(r"\bMills?\b", regex=True)]
for _, x in mill.iterrows():
    rows.append(dict(source="OS Open Names", id=f"{x['x']}_{x['y']}", name=x["name1"], kind="name", detail=f"{x['type']}: {x['local_type']}",
                     lat=x["lat"], lon=x["lon"], start=""))
M = pd.DataFrame(rows)
M = M[(M.lat > 49.8) & (M.lat < 61) & (M.lon > -8.7) & (M.lon < 2)].reset_index(drop=True)
M["x"], M["y"] = T.transform(M.lon.values, M.lat.values)

# ---- country and region: Northern Ireland by longitude box, otherwise nearest OS populated place
pp = O[O.type == "populatedPlace"].reset_index(drop=True)
px, py = T.transform(pp.lon.values, pp.lat.values)
tree = cKDTree(np.c_[px, py])


def where(df):
    d, i = tree.query(np.c_[df.x.values, df.y.values])
    ctry = pp.country.values[i].copy(); reg = pp.region.values[i].copy(); cty = pp.county.values[i].copy()
    ni = (df.lon.values < -5.35) & (df.lat.values > 53.9) & (df.lat.values < 55.5)
    ctry[ni] = "Northern Ireland"; reg[ni] = "Northern Ireland"; cty[ni] = ""
    return ctry, reg, cty


M["country"], M["region"], M["os_county"] = where(M)

# ---- Domesday places and their setting
DP = pd.read_csv(os.path.join(ROOT, "data", "domesday_mill_places.csv"), dtype={"placeId": str})
DP["lon"] = DP.lng
DP["x"], DP["y"] = T.transform(DP.lng.values, DP.lat.values)
DP["country"], DP["region"], DP["os_county"] = where(DP)
dtree = cKDTree(np.c_[DP.x.values, DP.y.values])
d, i = dtree.query(np.c_[M.x.values, M.y.values])
M["domesday_county"] = np.where(d < 10000, DP.countyName.values[i], "")
M["nearest_domesday_place_km"] = (d / 1000).round(3)
mp = DP[DP.mills1086 > 0]
mtree = cKDTree(np.c_[mp.x.values, mp.y.values])
d2, j = mtree.query(np.c_[M.x.values, M.y.values])
M["nearest_domesday_mill_place"] = mp.name.values[j]
M["nearest_domesday_mill_km"] = (d2 / 1000).round(3)

# ---- rivers: every watercourse link (inland, tidal, canal); named rivers separately
con = sqlite3.connect(f"file:{H}/osrivers/Data/oprvrs_gb.gpkg?mode=ro", uri=True)
allr, named = [], []
for blob, form, nm in con.execute("select geometry, form, watercourse_name from watercourse_link where form in ('inlandRiver','tidalRiver','canal')"):
    flags = blob[3]; env = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[(flags >> 1) & 7]
    g = wkb.loads(bytes(blob[8 + env:]))
    if form == "canal":
        continue
    allr.append(g)
    if nm:
        named.append(g)
con.close()
ta, tn = STRtree(allr), STRtree(named)
print("watercourse links", len(allr), "named", len(named))


def setting(df, dem):
    pts = points(df.x.values, df.y.values)
    ia = ta.nearest(pts); inn = tn.nearest(pts)
    df["river_m"] = [round(p.distance(allr[k])) for p, k in zip(pts, ia)]
    df["named_river_m"] = [round(p.distance(named[k])) for p, k in zip(pts, inn)]
    la, lo = df.lat.values, df.lon.values
    df["elev_m"] = np.round(dem.elev(la, lo), 1)
    ring = []
    for r in (300, 600, 1000):
        for a in np.arange(0, 360, 30):
            dx, dy = r * np.sin(np.radians(a)), r * np.cos(np.radians(a))
            ring.append(dem.elev(la + dy / 111320, lo + dx / (111320 * np.cos(np.radians(la)))))
    ring = np.vstack(ring + [df.elev_m.values])
    df["relief1km_m"] = np.round(ring.max(0) - ring.min(0), 1)
    return df


dem = DEM()
GB = M.country != "Northern Ireland"
M.loc[GB, ["river_m", "named_river_m", "elev_m", "relief1km_m"]] = setting(M[GB].copy(), dem)[["river_m", "named_river_m", "elev_m", "relief1km_m"]]
DP = setting(DP, dem)
M = M.drop(columns=["x", "y"])
M.to_csv(os.path.join(ROOT, "data", "modern_mills.csv"), index=False)
DP.drop(columns=["x", "y", "lon"]).to_csv(os.path.join(ROOT, "work", "domesday_setting.csv"), index=False)
print(M.groupby(["source", "kind"]).size())
print(M.groupby("country").size())
