# Millstreams

From Domesday mills to modern mills. Domesday Book (1086) recorded England's mills manor by manor. Are today's traces of mills in the same places, 940 years later? And did the textile mills of the Industrial Revolution reuse the old mill places, or go somewhere new?

**Interactive version:** https://tristan-hotham.github.io/domesday-mills/

This repository holds the interactive page, derived data and the analysis code for the data study *Millstreams: Domesday mill places, modern traces of mills and the textile mills that went elsewhere* by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349). Paper and archived release: https://doi.org/10.5281/zenodo.23727140

## Headline results

- The Domesday entries, as coded by the Hull Domesday Project, record {{domesday.mills_total|f2c}} mills in {{domesday.entries_with_mills|int}} entries ({{domesday.entries_fractional|int}} with a fraction of a mill). The figure usually quoted is {{domesday.quoted_5624|int}}, and a later estimate cited by Wikipedia is {{domesday.quoted_6082|int}}; I cannot reconcile the totals line by line, but counting rules for shares of mills and shared mills probably explain much of the gap.
- {{sample.mill_places|int}} of {{sample.places|int}} Domesday places with an entry and a location have at least part of a mill. Wiltshire has the most mills per head: {{counties.by_name.Wiltshire.mills_per_100hh|f1}} per 100 recorded households.
- Within 1 km, {{share.1km.water.mill|pct1}} of Domesday mill places have a watermill mapped in OpenStreetMap or Wikidata today, against {{share.1km.water.nomill|pct1}} of other Domesday places ({{share.1km.water.ratio|f1}} times; {{share.1km.water.ratio_local|f1}} times the rate among places of similar size in the same county). Logistic regression with county fixed effects, households, distance to a watercourse and local relief: odds ratio {{models_1km.water.or_|f2}} (95% CI {{models_1km.water.lo|f2}} to {{models_1km.water.hi|f2}}).
- Windmills, a technology that arrived after Domesday, show no such link: {{share.1km.wind.mill|pct1}} against {{share.1km.wind.nomill|pct1}}, odds ratio {{models_1km.wind.or_|f2}} ({{models_1km.wind.lo|f2}} to {{models_1km.wind.hi|f2}}).
- The more mills in 1086, the likelier a watermill today: {{dose.4.water1|pct1}} of places with three or more mills, {{dose_ratio_water_3plus_vs_none|f1}} times the rate for places with none. Features named Mill on OS Open Names: {{share.1km.name.mill|pct1}} against {{share.1km.name.nomill|pct1}} (odds ratio {{models_1km.name.or_|f2}}).
- County by county, Domesday mills and mapped mills today correlate only weakly (Spearman {{counties.spearman.traces_built.rho|f2}}, {{counties.spearman.traces_built.p|p}}): modern mapping is uneven.
- Textile mills ({{textile.textile.n|int}} in England in Wikidata, {{textile.north_share|pct0}} in the North West or Yorkshire) stand a median {{textile.textile.med_km|f1}} km from the nearest Domesday mill place, against {{textile.water.med_km|f1}} km for mapped watermills; {{textile.textile.within2|pct0}} are within 2 km against {{textile.water.within2|pct0}}. Domesday records only {{region_domesday.North West.mill_places|int}} mill places in what is now the North West.

## Files

- `index.html`: the interactive page (Leaflet map, search, charts). Data are embedded, so it works as a single file.
- `header.png`: social card (1200 by 630).
- `data/domesday_mill_places.csv`: every Domesday place with a location ({{domesday.places_with_coords|int}}): county, grid reference, coordinates, households and mills in 1086 (entry mills shared equally among the places an entry describes), Open Domesday path.
- `data/domesday_places_traces.csv`: the {{sample.places|int}} places used in the tests (places with an entry; same-name places in one grid square merged), with distance to a watercourse, elevation, local relief and distance to the nearest modern trace of each kind.
- `data/modern_mills.csv`: {{modern.rows|int}} modern traces of mills: OpenStreetMap objects, Wikidata items and OS Open Names features, with kind, country, region, nearest Domesday place and mill place, and setting.
- `data/county_mills.csv`: Domesday mills, households and modern traces by Domesday county.
- `data/results.json`: every number quoted on the page, in the paper, the blog post and the collage.
- `data/page_data.json`: compact data for the page.
- `code/01_domesday.py`: sums the mills in every Domesday entry and shares them among places.
- `code/02_modern.py`: reads and classifies the modern traces, places every point, measures rivers and terrain.
- `code/03_analysis.py`: all statistics; writes results.json and the derived tables.
- `code/04_build_site.py`: fills `page_template.html` and `README_template.md` from results.json.
- `code/05_header.py`: renders header.png with Playwright.
- `code/06_figures.py`, `code/07_paper.py`, `code/08_release.py`: blog and paper figures, the paper PDF via xelatex (from `paper_template.tex`), the blog post (from `blog_template.html`) and the Zenodo files.
- `release/`: the paper PDF and its source, blog post and figures, Zenodo files.
- `reddit/`: the r/dataisbeautiful collage and its script.
- `code/dem.py`: terrain reader, reused from my Within Sight study.

## How to rerun

Python 3 with pandas, numpy, scipy, statsmodels, shapely, pyproj, pyyaml and matplotlib (Playwright for the header). Inputs are read in place and are not included: the realm-domesday repository (https://github.com/embabel-worlds/realm-domesday), `domesday-destiny/data/domesday_places.csv` from my Domesday Destiny study, the Wikidata and OpenStreetMap extract (QLever queries, 28 October 2026), OS Open Names, OS Open Rivers and the terrain tiles.

```
python3 code/01_domesday.py /path/to/realm-domesday
python3 code/02_modern.py
python3 code/03_analysis.py
python3 code/04_build_site.py
FONT_DIR=/path/to/fonts python3 code/05_header.py
python3 code/06_figures.py && python3 code/07_paper.py && python3 code/08_release.py
```

`01` and `02` write intermediate files to `work/`, which `03` reads; `work/` is not kept in the repository.

## Method and caveats

- Modern traces are what someone has mapped or listed, not a census of mills. Coverage differs by county, so tests compare places within counties.
- Domesday places sit at the centre of their 1 km grid square, so distances under about 700 m are within the precision of the location.
- Kinds of modern mill come from OpenStreetMap tags and Wikidata classes and labels. Many mills are of unstated kind; I cannot tell water-powered from steam-powered textile mills.
- Domesday is thin for Yorkshire, partial for Lancashire and absent for the far north.
- A watermill near a Domesday mill place is consistent with continuity of the site, not proof that it is the same mill.

## Sources and licence

- Domesday: Hull Domesday Project, Professor J.J.N. Palmer, George Slater and the University of Hull (CC BY-NC-SA), via the realm-domesday repository by embabel-worlds (https://github.com/embabel-worlds/realm-domesday) and Open Domesday by Anna Powell-Smith (https://opendomesday.org/).
- Modern mills: © OpenStreetMap contributors (ODbL 1.0, https://www.openstreetmap.org/copyright); Wikidata (CC0). Retrieved via QLever on 28 October 2026.
- OS Open Names and OS Open Rivers: Ordnance Survey, Open Government Licence v3.0. Contains OS data © Crown copyright and database right 2026.
- Terrain: AWS Terrain Tiles by Mapzen/Tilezen (terrarium encoding, zoom 10). Attribution: https://github.com/tilezen/joerd/blob/master/docs/attribution.md
- Context: Wikipedia, *Domesday Book*, *Watermill* and *Windmill* (CC BY-SA 4.0).
- Base map tiles on the page: Esri. Map library: Leaflet.

Because the derived data include Hull Domesday Project figures (CC BY-NC-SA), the derived data and the page text are released under CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/). `data/modern_mills.csv` contains OpenStreetMap-derived points, which remain under the ODbL. Code is MIT (see `LICENSE`).

Companion studies: [Is Domesday destiny?](https://tristan-hotham.github.io/domesday-destiny/) and [Minted: the Anglo-Saxon mint towns](https://tristan-hotham.github.io/saxon-mints/).

## Citation

Hotham, T. (2026) *Millstreams: Domesday mill places, modern traces of mills and the textile mills that went elsewhere*. Zenodo. https://doi.org/10.5281/zenodo.23727140

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
