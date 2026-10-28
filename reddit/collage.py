"""r/dataisbeautiful collage: Domesday mills and the mills on today's map.
Light parchment, blue rivers (OS Open Rivers), brown Domesday mill places, millwheel motif.
Every number comes from ../data/results.json. Run from this folder: python3 collage.py
"""
import json, math, os, sqlite3
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.collections import LineCollection
from matplotlib.patches import Polygon, Circle, Rectangle
from matplotlib.lines import Line2D
from pyproj import Transformer
from shapely import wkb

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
F = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts") + "/"
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    fm.fontManager.addfont(F + f)
DISP = fm.FontProperties(fname=F + "FrauncesVar.ttf", weight=900)
SER = "Source Serif 4"; MONO = "IBM Plex Mono"
BG = "#F4EEDF"; FG = "#211D17"; MUT = "#6B6253"; LAND = "#E6DCC6"; COAST = "#CDBF9F"
STONE = "#8A5A1E"; STONEL = "#C99A55"; BLUE = "#1F5D8C"; RIVER = "#8DB3D3"; BRICK = "#A8432F"; MAUVE = "#7A4F93"
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
P = json.load(open(os.path.join(ROOT, "data", "page_data.json")))
tr = Transformer.from_crs(4326, 27700, always_xy=True)

# ---- data
DM = pd.DataFrame(P["dm"], columns=["la", "lo", "name", "mills", "hh", "county", "dbuilt", "dwater", "dname", "od"])
DM["x"], DM["y"] = tr.transform(DM.lo.values, DM.la.values)
MM = pd.DataFrame(P["mm"], columns=["la", "lo", "kind", "name", "src", "id"])
MM["x"], MM["y"] = tr.transform(MM.lo.values, MM.la.values)
land = []
for g in json.load(open(os.path.join(ROOT, "..", "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json"))):
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        a = np.array(poly[0])
        if (a[:, 1].min() < 49.6 and a[:, 0].max() > 1.0) or (a[:, 0].mean() < -5.4 and a[:, 1].mean() < 55.4):
            continue  # France and Ireland
        X, Y = tr.transform(a[:, 0], a[:, 1]); land.append(np.c_[X, Y])
con = sqlite3.connect("file:/home/claude/hist/osrivers/Data/oprvrs_gb.gpkg?mode=ro", uri=True)
riv = []
for blob, in con.execute("select geometry from watercourse_link where form in ('inlandRiver','tidalRiver') and watercourse_name is not null"):
    flags = blob[3]; env = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[(flags >> 1) & 7]
    g = wkb.loads(bytes(blob[8 + env:]))
    for ls in (g.geoms if g.geom_type == "MultiLineString" else [g]):
        riv.append(np.asarray(ls.coords)[:, :2])
con.close()

fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)


def wheel(ax, cx, cy, r, col, lw=2.2):
    ax.add_patch(Circle((cx, cy), r, fill=False, ec=col, lw=lw * 1.6))
    ax.add_patch(Circle((cx, cy), r * .62, fill=False, ec=col, lw=lw * .8))
    ax.add_patch(Circle((cx, cy), r * .14, fc=col, ec="none"))
    for i in range(16):
        a = i / 16 * 2 * math.pi
        ax.plot([cx + r * math.cos(a), cx + r * 1.28 * math.cos(a)], [cy + r * math.sin(a), cy + r * 1.28 * math.sin(a)], color=col, lw=lw * 2.4, solid_capstyle="butt")
        if i % 2 == 0:
            ax.plot([cx + r * .14 * math.cos(a), cx + r * math.cos(a)], [cy + r * .14 * math.sin(a), cy + r * math.sin(a)], color=col, lw=lw * .9)


# ---- title block
tx = fig.add_axes([0, .86, 1, .14]); tx.axis("off"); tx.set_xlim(0, 1); tx.set_ylim(0, 1)
tx.text(.04, .74, "Are today's mills where", fontproperties=DISP, fontsize=44, color=FG, va="center")
tx.text(.04, .40, "Domesday's mills were?", fontproperties=DISP, fontsize=44, color=FG, va="center")
tx.text(.04, .08, f"Domesday Book (1086) recorded mills manor by manor. I set {R['sample']['mill_places']:,} Domesday mill places against\n"
        "the watermills, windmills and textile mills on today's open maps.", family=SER, fontsize=15, color=FG, va="center", linespacing=1.35)
wx = fig.add_axes([.82, .875, .13, .104]); wx.set_xlim(-1.5, 1.5); wx.set_ylim(-1.5, 1.5); wx.set_aspect("equal"); wx.axis("off")
wheel(wx, 0, 0, 1, STONE, 2.0)
xs = np.linspace(-1.5, 1.5, 100); wx.fill_between(xs, -1.5, -0.95 + .08 * np.sin(xs * 4), color=RIVER, alpha=.55, lw=0)
wx.plot(xs, -0.95 + .08 * np.sin(xs * 4), color=BLUE, lw=2.2)

# ---- hero map
ax = fig.add_axes([.0, .29, .62, .55]); ax.axis("off"); ax.set_aspect("equal")
for a in land:
    ax.add_patch(Polygon(a, closed=True, fc=LAND, ec=COAST, lw=.5, zorder=0))
ax.add_collection(LineCollection(riv, colors=RIVER, linewidths=.35, alpha=.9, zorder=1))
s = DM.sort_values("mills", ascending=False)
ax.scatter(s.x, s.y, s=3 + s.mills * 7, c=STONEL, alpha=.6, lw=.35, edgecolors=STONE, zorder=2)
w = MM[MM.kind == "water"]; ax.scatter(w.x, w.y, s=7, c=BLUE, lw=0, zorder=3)
t = MM[MM.kind == "textile"]; ax.scatter(t.x, t.y, s=22, c=MAUVE, lw=.6, edgecolors="white", zorder=4)
ax.set_xlim(130000, 660000); ax.set_ylim(0, 600000)
h = [Line2D([], [], marker="o", ls="", ms=10, mfc=STONEL, mec=STONE, label="Domesday mill place, sized by mills"),
     Line2D([], [], marker="o", ls="", ms=5.5, mfc=BLUE, mec=BLUE, label="Watermill mapped today"),
     Line2D([], [], marker="o", ls="", ms=7.5, mfc=MAUVE, mec="white", label="Textile mill (Wikidata)"),
     Line2D([], [], color=RIVER, lw=2, label="Named river")]
ax.legend(handles=h, loc="upper left", bbox_to_anchor=(.0, .995), frameon=True, facecolor=BG, edgecolor=BG, framealpha=.92, prop={"family": MONO, "size": 11}, handletextpad=.4)
ax.annotate(f"textile mills cluster where\nDomesday recorded just\n{R['region_domesday']['North West']['mill_places']} mill places (North West)",
            xy=(385000, 400000), xytext=(150000, 315000), family=MONO, fontsize=10.5, color=FG,
            arrowprops=dict(arrowstyle="-", color=FG, lw=.8))

# ---- big numbers
nx = fig.add_axes([.62, .29, .36, .55]); nx.axis("off"); nx.set_xlim(0, 1); nx.set_ylim(0, 1)
S = R["share"]["1km"]
items = [
    (f"{R['domesday']['mills_total']:,.0f}", STONE, f"mills in the Domesday entries\n({R['domesday']['entries_with_mills']:,} entries; often quoted: 5,624)"),
    (f"{S['water']['ratio']:.1f}×", BLUE, f"as likely to have a watermill within\n1 km today: {S['water']['mill'] * 100:.1f}% of mill places,\n{S['water']['nomill'] * 100:.1f}% of other Domesday places"),
    (f"{S['wind']['ratio']:.1f}×", BRICK, "for windmills, a later technology:\nno link. What lasts is the\nwater-power site"),
    (f"{R['textile']['textile']['med_km']:.0f} km", MAUVE, f"median distance from a textile mill\nto a Domesday mill place\n(watermills: {R['textile']['water']['med_km']:.1f} km)"),
]
y = .97
for big, col, small in items:
    nx.text(.02, y, big, fontproperties=DISP, fontsize=46, color=col, va="top")
    nx.text(.02, y - .095, small, family=SER, fontsize=13.5, color=FG, va="top", linespacing=1.3)
    y -= .245

# ---- small multiples
c1 = fig.add_axes([.07, .115, .38, .13]); c2 = fig.add_axes([.56, .115, .40, .13])
V = R["curve"]; xk = [v["km"] for v in V]
for k, col in (("water", BLUE), ("wind", BRICK)):
    c1.plot(xk, [v[k + "_mill"] * 100 for v in V], color=col, lw=2.6)
    c1.plot(xk, [v[k + "_nomill"] * 100 for v in V], color=col, lw=2, ls="--")
c1.legend(handles=[Line2D([], [], color=BLUE, lw=2.6, label="watermill"), Line2D([], [], color=BRICK, lw=2.6, label="windmill"),
                   Line2D([], [], color=FG, lw=2, label="mill in 1086"), Line2D([], [], color=FG, lw=1.6, ls="--", label="no mill")],
          loc="upper left", frameon=False, ncol=2, prop={"family": MONO, "size": 9.5}, columnspacing=1, handlelength=1.8)
c1.set_ylim(0, 40)
c1.set_title("Domesday places with a mill nearby today", family=SER, fontsize=13, loc="left", color=FG, pad=8)
c1.set_xlabel("km from the Domesday place", family=MONO, fontsize=10.5); c1.set_ylabel("% of places", family=MONO, fontsize=10.5)
B = R["textile"]["bands"]; E = B["edges"]; xb = np.arange(len(E) - 1)
for j, (k, col) in enumerate((("water", BLUE), ("wind", BRICK), ("textile", MAUVE))):
    c2.bar(xb + (j - 1) * .27, np.array(B[k]) * 100, .27, color=col)
c2.set_xticks(xb); c2.set_xticklabels(["under\n1"] + [f"{E[i]}\nto {E[i + 1]}" for i in xb[1:-1]] + ["50\nor more"], family=MONO, fontsize=9.5)
c2.legend(handles=[Rectangle((0, 0), 1, 1, color=c) for c in (BLUE, BRICK, MAUVE)], labels=["watermills", "windmills", "textile mills"],
          loc="upper left", frameon=False, prop={"family": MONO, "size": 9.5}, ncol=3, columnspacing=1, handlelength=1)
c2.set_ylim(0, 58)
c2.set_title("How far is each kind of mill from Domesday?", family=SER, fontsize=13, loc="left", color=FG, pad=8)
c2.set_xlabel("km to the nearest Domesday mill place (% of each kind)", family=MONO, fontsize=10.5)
for c in (c1, c2):
    c.set_facecolor(BG); c.spines[["top", "right"]].set_visible(False); c.spines[["left", "bottom"]].set_color(MUT)
    c.tick_params(colors=FG, labelsize=10); c.grid(axis="y", color="#DCD2BD", lw=.7); c.set_axisbelow(True)
    for tl in c.get_yticklabels() + c.get_xticklabels(): tl.set_fontfamily(MONO)

# ---- footer
fig.text(.04, .018, "Data: Hull Domesday Project (Palmer, Slater, University of Hull; CC BY-NC-SA) via realm-domesday and Open Domesday; OpenStreetMap (ODbL);\n"
         "Wikidata (CC0); OS Open Names and OS Open Rivers, Contains OS data © Crown copyright and database right 2026 (OGL v3); Natural Earth.\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib. Modern mills are traces in uneven open data, not a census.",
         family=MONO, fontsize=9.2, color=MUT, va="bottom", linespacing=1.5)
fig.savefig(os.path.join(HERE, "domesday_mills.png"), dpi=200, facecolor=BG)
print("written")
