"""Step 7. Build the paper PDF: fill paper_template.tex with numbers and tables from data/results.json,
write release/paper/Hotham_Domesday_Mills.tex and compile it with xelatex (figures from 06_figures.py).
Placeholders: {{path|fmt}} as in 04_build_site.py, with % escaped for LaTeX.
Run: python3 code/07_paper.py
"""
import json, os, re, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Domesday_Mills"


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "pct0": return f"{v * 100:.0f}\\%"
    if f == "pct1": return f"{v * 100:.1f}\\%"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    if f == "f2c": return f"{v:,.2f}"
    if f == "p": return "p $<$ 0.001" if v < 0.001 else f"p = {v:.3f}"
    return str(v)


def sub(m):
    path, _, f = m.group(1).partition("|")
    return fmt(get(path.strip()), f.strip() or "raw")


S = R["share"]; Mo = R["models_1km"]
rows = ""
for k, lab in [("water", "Watermill"), ("wind", "Windmill"), ("built", "Any mill building"), ("name", "Mill name (OS)")]:
    a = S["500m"][k]; b = S["1km"][k]; c = S["2km"][k]; m = Mo[k]
    rows += (f"{lab} & {a['mill'] * 100:.1f} / {a['nomill'] * 100:.1f} & {b['mill'] * 100:.1f} / {b['nomill'] * 100:.1f} & {c['mill'] * 100:.1f} / {c['nomill'] * 100:.1f} & "
             f"{b['ratio_local']:.2f} & {m['or_']:.2f} ({m['lo']:.2f} to {m['hi']:.2f})\\\\\n")
TS = ("\\begin{table}[tbp]\\centering\\small\\caption{Share of Domesday places with a modern trace of a mill nearby (\\%, places with a mill in 1086 / places without). "
      "Local ratio: observed share for mill places over the share among places without a mill in the same county and fifth by households, at 1 km. "
      "Odds ratio: logistic regression at 1 km with county fixed effects, log households, log distance to a watercourse and log local relief (95\\% interval).}\\label{tab:share}"
      "\\resizebox{\\textwidth}{!}{\\begin{tabular}{lrrrrr}\\toprule Trace & Within 500 m & Within 1 km & Within 2 km & Local ratio & Odds ratio\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}}\\end{table}")
T = R["textile"]; rows = ""
for lab, v, n in [("Watermills", T["water"], T["water"]["n"]), ("Windmills", T["wind"], T["wind"]["n"]), ("Unspecified mills", T["mill"], T["mill"]["n"]),
                  ("Textile mills", T["textile"], T["textile"]["n"]), ("Domesday mill places", T["domesday_mill_places"], R["sample"]["mill_places"])]:
    rows += (f"{lab} & {n:,} & {v['river_m']:,.0f} & {v['elev_m']:.0f} & {v['relief_m']:.0f} & "
             + (f"{v['med_km']:.1f} & {v['within2'] * 100:.1f}" if "med_km" in v else " & ") + "\\\\\n")
TT = ("\\begin{table}[tbp]\\centering\\small\\caption{Setting of mapped mills in England and of Domesday mill places (medians). Watercourse: OS Open Rivers river or tidal link. "
      "Relief: highest minus lowest ground within 1 km. Last two columns: distance to the nearest Domesday mill place.}\\label{tab:setting}"
      "\\resizebox{\\textwidth}{!}{\\begin{tabular}{lrrrrrr}\\toprule Kind & Number & To watercourse (m) & Elevation (m) & Relief (m) & To Domesday mill (km) & Within 2 km (\\%)\\\\\\midrule\n"
      + rows + "\\bottomrule\\end{tabular}}\\end{table}")
s = open(os.path.join(HERE, "paper_template.tex")).read()
s = s.replace("{{TABLE_SHARE}}", TS).replace("{{TABLE_SETTING}}", TT)
s = re.sub(r"\{\{(.+?)\}\}", sub, s)
assert "{{" not in s
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w").write(s)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
print(r.stdout[-600:])
for ext in (".aux", ".log", ".out"):
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p): os.remove(p)
shutil.move(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
