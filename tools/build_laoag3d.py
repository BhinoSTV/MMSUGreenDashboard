#!/usr/bin/env python3
"""Build laoag3d.html: a single, dependency-free page with the Laoag 3D city model.

Usage:  python3 -I tools/build_laoag3d.py <raw_dir> <maplibre_dir> <out_html>
  raw_dir      output of tools/fetch_laoag_overture.py
  maplibre_dir directory holding maplibre-gl.js and maplibre-gl.css (v4.x, BSD-3)
  out_html     e.g. laoag3d.html
Needs:  pip install shapely
Everything (map library, data, fonts, seal) is inlined, the page makes no network request.
"""
import base64, gzip, json, math, re, sys
from pathlib import Path
from shapely.geometry import shape, box, Polygon, MultiPolygon
from shapely.ops import unary_union, transform

RAW, LIB, OUT = map(Path, sys.argv[1:4])
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
meta = json.load(open(RAW / "meta.json"))
W, S, E, N = meta["extent"]
LAT0 = (S + N) / 2
MX = 111_320 * math.cos(math.radians(LAT0))     # metres per degree of longitude
MY = 110_574                                     # metres per degree of latitude
load = lambda n: json.load(open(RAW / f"{n}_raw.geojson"))["features"]

# ---------------------------------------------------------------- buildings
SRC = ["OpenStreetMap", "Google Open Buildings", "Microsoft ML Buildings"]
CLS = ["", "house", "residential", "apartments", "school", "commercial", "retail", "industrial",
       "church", "public", "civic", "hotel", "roof", "other"]
CLS_ALIASES = {"detached": "house", "semidetached_house": "house", "bungalow": "house", "static_caravan": "house",
               "dormitory": "apartments", "university": "school", "college": "school", "kindergarten": "school",
               "office": "commercial", "supermarket": "retail", "warehouse": "industrial", "service": "industrial",
               "cathedral": "church", "chapel": "church", "hospital": "public", "government": "civic",
               "carport": "roof", "garage": "roof", "garages": "roof", "shed": "roof", "greenhouse": "roof",
               "barn": "roof", "kiosk": "roof"}
# Height rules for buildings without a surveyed height or floor count (basis flag q = 0).
# These are assumptions, NOT measurements: tuned for the 1-2 storey fabric typical of Ilocos Norte.
CLASS_H = {"house": 3.5, "residential": 3.5, "apartments": 9.5, "school": 6.5, "commercial": 7, "retail": 7,
           "industrial": 7, "church": 12, "public": 7, "civic": 7, "hotel": 12, "roof": 3}
def estimate_h(cls, area):
    if cls == "house" or cls == "residential":
        return 3.5 if area < 150 else 6.0
    if cls in CLASS_H:
        return CLASS_H[cls]
    return 2.8 if area < 30 else 3.5 if area < 200 else 5.0 if area < 600 else 7.0 if area < 2000 else 8.0

def to_m(ring):  return [((x - W) * MX, (y - S) * MY) for x, y in ring]
def to_int(ring):  # metres -> integer micro-degrees relative to the SW corner
    return [(round((X / MX) * 1e6), round((Y / MY) * 1e6)) for X, Y in ring]

blds, names, dropped = [], {}, 0
n_q = [0, 0, 0]
tot_area = 0.0
for f in load("buildings"):
    p = f["properties"]
    g = shape(f["geometry"])
    polys = list(g.geoms) if isinstance(g, MultiPolygon) else [g]
    for poly in polys:
        m = Polygon(to_m(poly.exterior.coords))
        if not m.is_valid:
            m = m.buffer(0)
            if m.is_empty or m.geom_type != "Polygon":
                dropped += 1; continue
        area = m.area
        if area < 8:
            dropped += 1; continue
        m = m.simplify(0.3, preserve_topology=True)
        if m.is_empty or m.geom_type != "Polygon" or len(m.exterior.coords) < 4:
            dropped += 1; continue
        cls = p["cls"] or ""
        cls = CLS_ALIASES.get(cls, cls)
        cls_i = CLS.index(cls) if cls in CLS else (CLS.index("other") if cls else 0)
        if p["h"]:
            h, q = float(p["h"]), 2
        elif p["fl"]:
            h, q = p["fl"] * 3.2, 1
        else:
            h, q = estimate_h(cls, area), 0
        n_q[q] += 1; tot_area += area
        pts = to_int(list(m.exterior.coords)[:-1])
        enc = [round(h * 10), q, SRC.index(p["src"]), cls_i, round(area), pts[0][0], pts[0][1]]
        for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
            enc += [xb - xa, yb - ya]
        if p["name"]:
            names[len(blds)] = p["name"]
        blds.append(enc)
print(f"buildings kept {len(blds)}, dropped {dropped}; basis surveyed/floors/estimated = {n_q[2]}/{n_q[1]}/{n_q[0]}")

# ---------------------------------------------------------------- roads / water / land
R5 = lambda c: [round(c[0], 5), round(c[1], 5)]
def round_geom(geom):
    t = geom["type"]
    if t == "LineString": return {"type": t, "coordinates": [R5(c) for c in geom["coordinates"]]}
    if t == "Polygon": return {"type": t, "coordinates": [[R5(c) for c in r] for r in geom["coordinates"]]}
    if t == "MultiPolygon": return {"type": t, "coordinates": [[[R5(c) for c in r] for r in p] for p in geom["coordinates"]]}
    raise ValueError(t)
def simp(geom, tol):
    return round_geom(json.loads(json.dumps(shape(geom).simplify(tol, preserve_topology=True).__geo_interface__)))

ROAD_CLASS = {"trunk": 0, "motorway": 0, "primary": 0, "secondary": 1, "tertiary": 2,
              "residential": 3, "unclassified": 3, "service": 3, "living_street": 3, "track": 3, "unknown": 3,
              "footway": 4, "path": 4, "steps": 4, "pedestrian": 4, "cycleway": 4, "bridleway": 4}
roads = [{"type": "Feature", "properties": {"c": ROAD_CLASS.get(f["properties"]["cls"], 3)},
          "geometry": simp(f["geometry"], 0.00001)} for f in load("roads")]

water = []
for f in load("water"):
    p = f["properties"]
    if p["cls"] == "swimming_pool": continue
    water.append({"type": "Feature", "properties": {"k": p["sub"] or "water"}, "geometry": simp(f["geometry"], 0.00002)})

# Land cover: ESA WorldCover 10 m, vectorised by tools/fetch_worldcover.py (classes are mutually exclusive)
ext_box = box(W, S, E, N)
lc_feats = []
for f in json.load(open(RAW / "landcover_wc.geojson"))["features"]:
    lc_feats.append({"type": "Feature", "properties": f["properties"],
                     "geometry": simp(f["geometry"], 0.00002)})
wc = json.load(open(RAW / "wc_stats.json"))

LU = ["park", "recreation", "education", "cemetery", "agriculture", "other"]
LU_MAP = {"park": 0, "recreation": 0, "education": 2, "cemetery": 3, "agriculture": 4}
landuse = []
park_polys = []
for f in load("landuse"):
    p = f["properties"]
    k = LU_MAP.get(p["sub"], 5)
    if k == 5: continue
    g = shape(f["geometry"]).intersection(ext_box)
    if g.is_empty: continue
    if k == 0: park_polys.append(g)
    landuse.append({"type": "Feature", "properties": {"k": k, "n": p["name"] or ""}, "geometry": simp(g.__geo_interface__, 0.00002)})

# ---------------------------------------------------------------- stats
def metres_area(g):
    """Planar area in m2 of a (multi)polygon in lon/lat, holes respected."""
    if g.is_empty: return 0.0
    return transform(lambda x, y, z=None: ((x - W) * MX, (y - S) * MY), g).area
ext_area = (E - W) * MX * (N - S) * MY
cover = {k: v for k, v in wc["share"].items()}          # % of extent, from pixel counts
road_km = 0.0
for f in load("roads"):
    c = f["geometry"]["coordinates"]
    for a, b in zip(c, c[1:]):
        road_km += math.hypot((b[0] - a[0]) * MX, (b[1] - a[1]) * MY) / 1000
stats = {"n": len(blds), "q": n_q, "footprint_ha": tot_area / 1e4, "road_km": road_km,
         "ext_km2": ext_area / 1e6, "cover": cover, "water_share": wc["water_share"], "park_ha": metres_area(unary_union(park_polys)) / 1e4 if park_polys else 0}
print("stats", json.dumps(stats))

# MMSU Campus 2 (CTE / Graduate School / Laboratory Schools): mean of well-supported Overture POIs
KEEP = ("CTE", "Graduate School", "Laboratory", "Teaching Excellence", "College of Teacher Education")
pts = [(p[1], p[2]) for p in json.load(open(RAW / "places.json")) if any(k in p[0] for k in KEEP) and p[3] >= 0.7]
campus2 = [round(sum(p[1] for p in pts) / len(pts), 5), round(sum(p[0] for p in pts) / len(pts), 5)]
print("campus2 marker (lon,lat)", campus2, "from", len(pts), "POIs")

blob = {"extent": [W, S, E, N], "release": meta["release"], "src": SRC, "cls": CLS, "bld": blds, "names": names,
        "roads": {"type": "FeatureCollection", "features": roads},
        "water": {"type": "FeatureCollection", "features": water},
        "lc": {"type": "FeatureCollection", "features": lc_feats},
        "lu": {"type": "FeatureCollection", "features": landuse},
        "stats": stats, "campus2": campus2}
raw = json.dumps(blob, separators=(",", ":")).encode()
gz = gzip.compress(raw, 9)
print(f"data json {len(raw)/1e6:.2f} MB -> gzip {len(gz)/1e6:.2f} MB")

# ---------------------------------------------------------------- brand assets from units.html
units = (ROOT / "units.html").read_text()
fonts = "\n".join(re.findall(r"@font-face\s*\{.*?\}", units, flags=re.S))
seal = re.search(r'class="brand-seal"\s+src="(data:image/png;base64,[^"]+)"', units).group(1)

tpl = (HERE / "laoag3d.template.html").read_text()
js = (LIB / "maplibre-gl.js").read_text().replace("</script", "<\\/script")
page = (tpl.replace("/*{{FONTS}}*/", fonts).replace("/*{{MAPLIBRE_CSS}}*/", (LIB / "maplibre-gl.css").read_text())
          .replace("{{SEAL}}", seal).replace("/*{{MAPLIBRE_JS}}*/", js)
          .replace("{{DATA_B64}}", base64.b64encode(gz).decode()).replace("{{RELEASE}}", meta["release"]))
OUT.write_text(page)
print(f"wrote {OUT} ({len(page)/1e6:.2f} MB)")
