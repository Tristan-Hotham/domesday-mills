## Title

[OC] Are today's mills where Domesday's were? Domesday Book (1086) records 6,172 mills. Places that had one are 3.9 times as likely to have a watermill mapped within 1 km today, but no likelier to have a windmill, and the textile mills lie a median 20 km from the nearest Domesday mill place

## Body

I added up every mill in the Hull Domesday Project's coding of Domesday Book and set the 3,390 places with a mill against the watermills, windmills and textile mills in OpenStreetMap and Wikidata today.

Within 1 km, 4.8% of Domesday mill places have a mapped watermill, against 1.2% of other Domesday places, and the gap holds within counties and after allowing for size and distance to a river. Windmills, which arrived about a century after Domesday, show no link at all (2.6% against 2.4%), so what lasts seems to be the water-power site. The textile mills mostly went to the North West, where Domesday recorded just 15 mill places.

Caveat: open data hold the mills someone has mapped, so these are traces, not a census, and Domesday places are only located to a 1 km square.

Interactive map: https://tristan-hotham.github.io/domesday-mills/

## Source comment

Source: Hull Domesday Project (Professor J.J.N. Palmer, George Slater and the University of Hull; CC BY-NC-SA), via the realm-domesday repository (https://github.com/embabel-worlds/realm-domesday) and Open Domesday (https://opendomesday.org/); OpenStreetMap mills (© OpenStreetMap contributors, ODbL) and Wikidata mill items (CC0), retrieved via QLever on 28 October 2026; Ordnance Survey OS Open Names and OS Open Rivers (Contains OS data © Crown copyright and database right 2026, Open Government Licence v3.0); Natural Earth coastline (public domain). Windmill date context: Wikipedia, "Windmill" (CC BY-SA 4.0).

Tools: Python (pandas, numpy, scipy, statsmodels, shapely, pyproj, matplotlib).

Interactive version: https://tristan-hotham.github.io/domesday-mills/
Blog post: https://blog.tristanhotham.com/2026/10/28/domesday-mills/
Paper and data: https://doi.org/10.5281/zenodo.23727140
