"""Step 8. Blog post (release/blog/post.html from blog_template.html), blog and Zenodo meta files,
and the Zenodo folder (paper, key CSVs, results.json and a code-and-data zip).
Image placeholders {{IMG|file|alt|caption}} are left for the uploader.
Run: python3 code/08_release.py
"""
import json, os, re, shutil, zipfile
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "04_build_site.py")); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
R = b.R
t = open(os.path.join(HERE, "blog_template.html")).read()
t = re.sub(r"\{\{(?!IMG\|)(.+?)\}\}", b.sub, t)
open(os.path.join(ROOT, "release", "blog", "post.html"), "w").write(t)
for m in re.findall(r"\{\{IMG\|([^|]+)\|", t):
    assert os.path.exists(os.path.join(ROOT, "release", "blog", m)), m

s = R["share"]["1km"]["water"]
title = "Millstreams: Domesday Mill Places, Modern Traces of Mills and the Textile Mills that Went Elsewhere"
meta = dict(
    title="From Domesday mills to modern mills",
    slug="domesday-mills",
    excerpt=(f"Domesday Book's entries count {R['domesday']['mills_total']:,.0f} mills in 1086. Places that had one are {s['ratio']:.1f} times as likely to have a mapped "
             f"watermill within 1 km today, but no likelier to have a windmill, and the textile mills of the Industrial Revolution went somewhere else."),
    seo_description=f"Are today's mills where Domesday's were? Old mill places are {s['ratio']:.1f} times as likely to have a watermill nearby; the textile mills went elsewhere.",
    tags=["Domesday", "watermills", "windmills", "Industrial Revolution", "textile mills", "maps", "open data", "medieval England"],
    header_alt=(f"Title card reading 'Millstreams' on a parchment background, beside a map of England and Wales with light brown circles for Domesday mill places, "
                f"blue dots for watermills mapped today and a cluster of purple dots for textile mills in the North West. Text: places with a mill in 1086 are "
                f"{s['ratio']:.1f} times as likely to have a watermill within 1 km today; the textile mills went somewhere else."))
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
json.dump(meta, open(os.path.join(ROOT, "release", "blog", "meta.json"), "w"), indent=2, ensure_ascii=False)

NAME = "Hotham_Domesday_Mills"
pt = open(os.path.join(ROOT, "release", "paper", NAME + ".tex")).read()
ab = pt.split("\\begin{center}\\textbf{Abstract}\\end{center}")[1].split("\\textbf{Keywords:}")[0].strip()
ab = ab.replace("\\%", "%").replace("$<$", "<")
Z = os.path.join(ROOT, "release", "zenodo"); os.makedirs(Z, exist_ok=True)
zmeta = dict(
    title=title,
    description_html=f"<p>{ab}</p><p>Interactive version: https://tristan-hotham.github.io/domesday-mills/. Data and code: https://github.com/Tristan-Hotham/domesday-mills. Blog post: to follow.</p>",
    keywords=["Domesday Book", "watermills", "windmills", "mills", "persistence", "textile mills", "Industrial Revolution", "OpenStreetMap", "Wikidata", "historical geography"],
    licence="cc-by-nc-sa-4.0",
    related=[
        dict(identifier="https://github.com/Tristan-Hotham/domesday-mills", relation="issupplementedby", resource_type="software"),
        dict(identifier="https://tristan-hotham.github.io/domesday-mills/", relation="issupplementedby", resource_type="other"),
        dict(identifier="https://digitalcollections.hull.ac.uk/collections/3t945r28b", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://github.com/embabel-worlds/realm-domesday", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://opendomesday.org/", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.openstreetmap.org", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.wikidata.org", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.ordnancesurvey.co.uk/products/os-open-names", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.ordnancesurvey.co.uk/products/os-open-rivers", relation="isderivedfrom", resource_type="dataset"),
    ])
json.dump(zmeta, open(os.path.join(Z, "meta.json"), "w"), indent=2, ensure_ascii=False)
shutil.copy(os.path.join(ROOT, "release", NAME + ".pdf"), Z)
for f in ["domesday_places_traces.csv", "modern_mills.csv", "county_mills.csv", "results.json"]:
    shutil.copy(os.path.join(ROOT, "data", f), Z)
with zipfile.ZipFile(os.path.join(Z, "domesday-mills_code_and_data.zip"), "w", zipfile.ZIP_DEFLATED) as zf:
    for sub in ("code", "data"):
        for f in sorted(os.listdir(os.path.join(ROOT, sub))):
            p = os.path.join(ROOT, sub, f)
            if os.path.isfile(p): zf.write(p, f"domesday-mills/{sub}/{f}")
    for f in ("README.md", "LICENSE"): zf.write(os.path.join(ROOT, f), f"domesday-mills/{f}")
print("release files written; post words:", len(re.sub(r"<[^>]+>", " ", re.sub(r"\{\{IMG\|.*?\}\}", "", t)).split()))
