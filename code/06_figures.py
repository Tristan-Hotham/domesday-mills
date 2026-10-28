"""Step 6. Static figures for the paper (release/paper/f_*.png) and the blog (release/blog/b_*.png, 1520 px wide).
Maps are drawn from coordinates over the Natural Earth 1:10m land outline (no web tiles).
Run: FONT_DIR=/path/to/fonts python3 code/06_figures.py
"""
import json, math, os
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
FD = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf"]:
    if os.path.exists(os.path.join(FD, f)): fm.fontManager.addfont(os.path.join(FD, f))
plt.rcParams.update({"font.family": "Source Serif 4", "font.size": 13, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#655D50", "axes.labelcolor": "#211D17", "xtick.color": "#3F392F", "ytick.color": "#3F392F"})
BG = "#F2EDE2"; FG = "#211D17"; MUT = "#655D50"; STONE = "#8A5A1E"; STONEL = "#C99A55"; BLUE = "#1F5D8C"; BRICK = "#A8432F"; MAUVE = "#7A4F93"
MOSS = "#5E7A35"; LAND = "#E2DACA"; RULE = "#D6CDBB"; GREY = "#9C9384"
MONO = "IBM Plex Mono"
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
P = json.load(open(os.path.join(ROOT, "data", "page_data.json")))
PO = os.path.join(ROOT, "release", "paper"); BO = os.path.join(ROOT, "release", "blog")
os.makedirs(PO, exist_ok=True); os.makedirs(BO, exist_ok=True)
K = math.cos(math.radians(52.5))
LAND_POLYS = []
for g in json.load(open(os.path.join(ROOT, "..", "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json"))):
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        a = np.array(poly[0]); LAND_POLYS.append(np.c_[a[:, 0] * K, a[:, 1]])
# reference towns for the northern map, placed at their OS Open Names point
_O = pd.read_csv("/home/claude/hist/osnames_gb.tsv", sep="\t", usecols=["name1", "local_type", "lat", "lon"])
CITIES = [(n, *_O[(_O.name1 == n) & (_O.local_type == "City")][["lat", "lon"]].iloc[0].tolist()) for n in ("Manchester", "Leeds", "Sheffield", "Derby", "Preston")]
DM = pd.DataFrame(P["dm"], columns=["la", "lo", "name", "mills", "hh", "county", "dbuilt", "dwater", "dname", "od"])
MM = pd.DataFrame(P["mm"], columns=["la", "lo", "kind", "name", "src", "id"])


def basemap(ax, ext):
    for a in LAND_POLYS:
        ax.add_patch(Polygon(a, closed=True, fc=LAND, ec="#C4B9A3", lw=.5, zorder=0))
    ax.set_xlim(ext[0] * K, ext[1] * K); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")


def save(fig, name, blog):
    out = os.path.join(BO if blog else PO, name)
    fig.savefig(out, dpi=160 if blog else 200, facecolor=fig.get_facecolor(), bbox_inches=None if blog else "tight", pad_inches=.15)
    plt.close(fig)


def style(ax):
    ax.set_facecolor(BG); ax.grid(axis="y", color=RULE, lw=.8); ax.set_axisbelow(True)
    ax.tick_params(labelsize=12)
    for t in ax.get_xticklabels() + ax.get_yticklabels(): t.set_fontfamily(MONO)


# ---------- 1. map
def fig_map(blog):
    W, H = (9.5, 11.2) if blog else (7.2, 8.6)
    fig = plt.figure(figsize=(W, H), facecolor=BG if blog else "white")
    ax = fig.add_axes([0, 0, 1, 1]); basemap(ax, (-5.9, 1.9, 49.85, 55.9))
    w = MM[MM.kind == "water"]; t = MM[MM.kind == "textile"]
    s = DM.sort_values("mills", ascending=False)
    ax.scatter(s.lo * K, s.la, s=4 + s.mills * 9, c=STONEL, alpha=.55, lw=.3, edgecolors=STONE, zorder=2)
    ax.scatter(w.lo * K, w.la, s=7, c=BLUE, lw=0, zorder=3)
    ax.scatter(t.lo * K, t.la, s=16, c=MAUVE, lw=.5, edgecolors="white", zorder=4)
    h = [Line2D([], [], marker="o", ls="", ms=9, mfc=STONEL, mec=STONE, label=f"Domesday mill place, sized by mills ({R['sample']['mill_places']:,})"),
         Line2D([], [], marker="o", ls="", ms=5, mfc=BLUE, mec=BLUE, label=f"Mapped watermill today ({R['modern']['uk_by_kind']['water']:,} in the UK)"),
         Line2D([], [], marker="o", ls="", ms=7, mfc=MAUVE, mec="white", label=f"Textile mill in Wikidata ({R['modern']['uk_by_kind']['textile']:,} in the UK)")]
    lg = ax.legend(handles=h, loc="upper right", bbox_to_anchor=(.99, .985), frameon=False, prop={"family": MONO, "size": 11 if blog else 9})
    save(fig, "b_map.png" if blog else "f_map.png", blog)


# ---------- 2. distance curves
def fig_curve(blog):
    V = R["curve"]; fig, axs = plt.subplots(1, 2, figsize=(9.5, 4.6) if blog else (7.2, 3.4), facecolor=BG if blog else "white", sharey=True)
    for ax, (k, c, tt) in zip(axs, [("water", BLUE, "Watermills"), ("wind", BRICK, "Windmills")]):
        style(ax); x = [v["km"] for v in V]
        ax.plot(x, [v[k + "_mill"] for v in V], color=c, lw=2.6, marker="o", label="Mill in 1086")
        ax.plot(x, [v[k + "_nomill"] for v in V], color=c, lw=2, ls="--", marker="o", mfc="white", label="No mill in 1086")
        ax.set_title(tt, family="Source Serif 4", fontsize=15 if blog else 12, loc="left", color=FG)
        ax.set_xlabel("distance from the Domesday place (km)", family=MONO, fontsize=11 if blog else 9)
        ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
        ax.legend(frameon=False, prop={"family": MONO, "size": 10 if blog else 8}, loc="upper left")
    axs[0].set_ylabel("share of places with a trace", family=MONO, fontsize=11 if blog else 9)
    fig.tight_layout(pad=1.2)
    save(fig, "b_curve.png" if blog else "f_curve.png", blog)


# ---------- 3. dose
def fig_dose(blog):
    V = R["dose"]; fig, ax = plt.subplots(figsize=(9.5, 4.6) if blog else (6.4, 3.2), facecolor=BG if blog else "white"); style(ax)
    lab = [f"{a}\n{v['n']:,} places" for a, v in zip(["none", "part of one", "1", "2", "3 or more"], V)]
    for i, v in enumerate(V):
        ax.bar(i - .2, v["water1"], .4, color=GREY if i == 0 else BLUE, label="Watermill within 1 km" if i == 1 else None)
        ax.bar(i + .2, v["wind1"], .4, color=BRICK, alpha=.8, label="Windmill within 1 km" if i == 1 else None)
        ax.text(i - .2, v["water1"] + .003, f"{v['water1'] * 100:.1f}%", ha="center", family=MONO, fontsize=11 if blog else 8)
    ax.set_xticks(range(5)); ax.set_xticklabels(lab, family=MONO, fontsize=11 if blog else 7.5); ax.set_ylim(0, .12)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0)); ax.set_yticks([0, .04, .08, .12])
    ax.set_xlabel("mills in the place's Domesday entries", family=MONO, fontsize=11 if blog else 9, labelpad=8)
    ax.legend(frameon=False, prop={"family": MONO, "size": 10 if blog else 8}, loc="upper left")
    fig.tight_layout(pad=1.2)
    save(fig, "b_dose.png" if blog else "f_dose.png", blog)


# ---------- 4. counties
def fig_counties(blog):
    V = R["counties"]["rows"]; fig, ax = plt.subplots(figsize=(9.5, 9.5) if blog else (7.0, 7.4), facecolor=BG if blog else "white"); style(ax)
    ax.grid(axis="y", visible=False); ax.grid(axis="x", color=RULE)
    y = np.arange(len(V))[::-1]
    ax.barh(y, [v["mills1086"] for v in V], color=STONE, height=.7)
    for yy, v in zip(y, V):
        ax.text(v["mills1086"] + 6, yy, f"{v['mills1086']:,.0f}  ({v['mills_per_100hh']:.1f} per 100 hh)", va="center", family=MONO, fontsize=10 if blog else 7.5)
    ax.set_yticks(y); ax.set_yticklabels([v["county"] for v in V], fontsize=11 if blog else 8.5, family="Source Serif 4")
    ax.set_xlim(0, 760); ax.set_xlabel("mills in the Domesday entries, 1086", family=MONO, fontsize=11 if blog else 9)
    fig.tight_layout(pad=1.2)
    save(fig, "b_counties.png" if blog else "f_counties.png", blog)


# ---------- 5. textile distance bands
def fig_bands(blog):
    B = R["textile"]["bands"]; E = B["edges"]; fig, ax = plt.subplots(figsize=(9.5, 4.8) if blog else (7.0, 3.4), facecolor=BG if blog else "white"); style(ax)
    ks = [("water", "Watermills", BLUE), ("wind", "Windmills", BRICK), ("textile", "Textile mills", MAUVE)]
    x = np.arange(len(E) - 1)
    for j, (k, n, c) in enumerate(ks):
        ax.bar(x + (j - 1) * .27, B[k], .27, color=c, label=f"{n} ({R['textile'][k]['n']:,})")
    ax.set_xticks(x); ax.set_xticklabels([f"{E[i]} to {E[i + 1]}" if E[i + 1] < 1000 else "50+" for i in x], family=MONO, fontsize=11 if blog else 8)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
    ax.set_xlabel("km to the nearest place with a mill in 1086", family=MONO, fontsize=11 if blog else 9)
    ax.legend(frameon=False, prop={"family": MONO, "size": 10 if blog else 8}, loc="upper center")
    fig.tight_layout(pad=1.2)
    save(fig, "b_textile.png" if blog else "f_textile.png", blog)


# ---------- 6. the north: Domesday mill places and textile mills
def fig_north(blog):
    W, H = (9.5, 7.6) if blog else (7.0, 5.6)
    fig = plt.figure(figsize=(W, H), facecolor=BG if blog else "white")
    ax = fig.add_axes([0, 0, 1, 1]); ext = (-3.4, -0.4, 52.6, 54.4); basemap(ax, ext)
    s = DM; ax.scatter(s.lo * K, s.la, s=10 + s.mills * 16, c=STONEL, alpha=.65, lw=.4, edgecolors=STONE, zorder=2)
    w = MM[MM.kind == "water"]; ax.scatter(w.lo * K, w.la, s=16, c=BLUE, zorder=3)
    t = MM[MM.kind == "textile"]; ax.scatter(t.lo * K, t.la, s=34, c=MAUVE, lw=.6, edgecolors="white", zorder=4)
    for nm, la, lo in CITIES:
        ax.text(lo * K + .02, la + .02, nm, family=MONO, fontsize=11 if blog else 8, color=FG, zorder=5)
        ax.plot(lo * K, la, marker="s", ms=4, color=FG, zorder=5)
    h = [Line2D([], [], marker="o", ls="", ms=9, mfc=STONEL, mec=STONE, label="Domesday mill place"),
         Line2D([], [], marker="o", ls="", ms=5, mfc=BLUE, mec=BLUE, label="Mapped watermill"),
         Line2D([], [], marker="o", ls="", ms=7, mfc=MAUVE, mec="white", label="Textile mill (Wikidata)")]
    ax.legend(handles=h, loc="lower left", frameon=True, facecolor=BG, edgecolor=RULE, prop={"family": MONO, "size": 11 if blog else 8})
    save(fig, "b_north.png" if blog else "f_north.png", blog)


for blog in (False, True):
    fig_map(blog); fig_curve(blog); fig_dose(blog); fig_counties(blog); fig_bands(blog); fig_north(blog)
print("figures written")
