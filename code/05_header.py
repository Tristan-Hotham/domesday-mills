"""Step 5. Render ../header.png (1200x630 social card) with Playwright Chromium.

Fonts: pass a folder holding FrauncesVar.ttf, SourceSerif4-Regular.ttf, IBMPlexMono-Regular.ttf and
IBMPlexMono-Medium.ttf as FONT_DIR (from github.com/google/fonts); otherwise system serif is used.
Coastline: Natural Earth 1:10m land for the British Isles, as extracted for the lighthouse project.
Run: FONT_DIR=/path/to/fonts python3 05_header.py
"""
import json, math, os
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
P = json.load(open(os.path.join(ROOT, "data", "page_data.json")))
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
FD = os.environ.get("FONT_DIR", "")
K = math.cos(math.radians(52.5))
X0, X1, Y0, Y1 = -5.9 * K, 1.9 * K, -55.3, -49.9
Hh = 600; Ww = Hh * (X1 - X0) / (Y1 - Y0)


def pr(lat, lon):
    return (lon * K - X0) / (Y1 - Y0) * Hh, (-lat - Y0) / (Y1 - Y0) * Hh


COAST = os.path.join(ROOT, "..", "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json")
land = ""
for g in json.load(open(COAST)):
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        ring = poly[0]
        if min(q[1] for q in ring) < 49.6 and max(q[0] for q in ring) > 1.0:
            continue
        land += "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in (pr(q[1], q[0]) for q in ring)) + "Z"
dots = ""
for d in sorted(P["dm"], key=lambda d: -d[3]):
    x, y = pr(d[0], d[1]); r = 1.2 + math.sqrt(d[3]) * 1.3
    dots += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#B98A4A" fill-opacity=".55"/>'
for la, lo, k, *_ in P["mm"]:
    if k in ("water", "textile"):
        x, y = pr(la, lo)
        c = "#1F5D8C" if k == "water" else "#7A4F93"
        dots += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{2.6 if k == "textile" else 1.9}" fill="{c}" fill-opacity=".9"/>'
ff = ""
if FD:
    ff = "".join(f"@font-face{{font-family:'{n}';src:url('file://{FD}/{f}');font-weight:{w};}}" for n, f, w in [
        ("Fraunces", "FrauncesVar.ttf", "100 900"), ("Source Serif 4", "SourceSerif4-Regular.ttf", "400"),
        ("IBM Plex Mono", "IBMPlexMono-Regular.ttf", "400"), ("IBM Plex Mono", "IBMPlexMono-Medium.ttf", "500")])
s = R["share"]["1km"]["water"]
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{ff}
body{{margin:0;width:1200px;height:630px;background:radial-gradient(circle at 78% 50%,#F7F3EA 0%,#F2EDE2 55%,#E6DECD 100%);color:#211D17;overflow:hidden;position:relative;font-family:'Source Serif 4',Georgia,serif}}
.k{{position:absolute;left:70px;top:78px;font:500 15px/1 'IBM Plex Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:#655D50;display:flex;gap:12px;align-items:center}}
.k b{{background:#1F5D8C;color:#F2EDE2;padding:7px 9px;font-weight:500}}
h1{{position:absolute;left:64px;top:122px;margin:0;font:900 116px/.9 Fraunces,Georgia,serif;letter-spacing:-.02em;color:#211D17}}
h1 em{{font-style:normal;color:#1F5D8C}}
p{{position:absolute;left:70px;top:290px;width:610px;margin:0;font-size:28px;line-height:1.36;color:#211D17}}
p b.s{{color:#8A5A1E}} p b.b{{color:#1F5D8C}} p b.m{{color:#7A4F93}}
.f{{position:absolute;left:70px;bottom:44px;font:400 14px/1 'IBM Plex Mono',monospace;letter-spacing:.12em;text-transform:uppercase;color:#655D50}}
svg{{position:absolute;right:20px;top:15px}}
</style></head><body>
<div class="k"><b>Data study</b><span>Domesday × mills today · 1086 to 2026</span></div>
<h1>Mill<em>streams</em></h1>
<p>Places with a <b class="s">mill in 1086</b> are {s['ratio']:.1f} times as likely to have a <b class="b">watermill</b> within 1 km today. The <b class="m">textile mills</b> went somewhere else.</p>
<div class="f">Dr Tristan Hotham · Independent researcher</div>
<svg width="{Ww:.0f}" height="{Hh}" viewBox="0 0 {Ww:.0f} {Hh}"><path d="{land}" fill="#E2DACA" stroke="#C4B9A3" stroke-width="1"/>{dots}</svg>
</body></html>"""
os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)
tmp = os.path.join(ROOT, "work", "header.html"); open(tmp, "w").write(html)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1200, "height": 630})
    pg.goto("file://" + os.path.abspath(tmp)); pg.wait_for_timeout(500)
    pg.screenshot(path=os.path.join(ROOT, "header.png")); b.close()
os.remove(tmp)
print("header.png written")
