#!/usr/bin/env python3
"""Download free Overture Maps data for the Laoag City study extent.

Usage:  python3 -I tools/fetch_laoag_overture.py <out_dir> [release]
Needs:  pip install duckdb      (reads Overture GeoParquet straight from S3, no API key)
Note:   unset AWS_* env vars if present, DuckDB would otherwise sign the anonymous request.
Output: <out_dir>/{buildings,roads,water,landuse}_raw.geojson, places.json, meta.json
"""
import json, os, sys
import duckdb

OUT = sys.argv[1]
REL = sys.argv[2] if len(sys.argv) > 2 else "2026-10-21.0"
W, S, E, N = 120.53, 18.16, 120.63, 18.26          # study extent (lon/lat)
os.makedirs(OUT, exist_ok=True)

con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial;"
            "SET s3_region='us-west-2'; SET s3_url_style='path'; SET s3_endpoint='s3.us-west-2.amazonaws.com';")
B = f"s3://overturemaps-us-west-2/release/{REL}"
bb = f"bbox.xmin<{E} AND bbox.xmax>{W} AND bbox.ymin<{N} AND bbox.ymax>{S}"
pq = lambda theme, typ: f"read_parquet('{B}/theme={theme}/type={typ}/*', hive_partitioning=1)"

def dump(name, sql, cols):
    rows = con.execute(sql).fetchall()
    feats = [{"type": "Feature", "properties": dict(zip(cols, r[:-1])), "geometry": json.loads(r[-1])} for r in rows]
    json.dump({"type": "FeatureCollection", "features": feats}, open(f"{OUT}/{name}_raw.geojson", "w"))
    print(name, len(rows))

dump("buildings", f"""SELECT height, num_floors, class, subtype, names.primary, sources[1].dataset, ST_AsGeoJSON(geometry)
    FROM {pq('buildings','building')} WHERE {bb}""", ["h", "fl", "cls", "sub", "name", "src"])
dump("roads", f"""SELECT class, subtype, names.primary, ST_AsGeoJSON(geometry)
    FROM {pq('transportation','segment')} WHERE {bb} AND subtype='road'""", ["cls", "sub", "name"])
dump("water", f"""SELECT subtype, class, names.primary, sources[1].dataset, ST_AsGeoJSON(geometry)
    FROM {pq('base','water')} WHERE {bb}""", ["sub", "cls", "name", "src"])
dump("landuse", f"""SELECT subtype, class, names.primary, sources[1].dataset, ST_AsGeoJSON(geometry)
    FROM {pq('base','land_use')} WHERE {bb}""", ["sub", "cls", "name", "src"])
places = con.execute(f"""SELECT names.primary, ST_Y(geometry), ST_X(geometry), confidence
    FROM {pq('places','place')}
    WHERE bbox.xmin BETWEEN {W} AND {E} AND bbox.ymin BETWEEN {S} AND {N}
      AND (names.primary ILIKE '%mariano marcos%' OR names.primary ILIKE '%mmsu%')""").fetchall()
json.dump(places, open(f"{OUT}/places.json", "w"))
json.dump({"release": REL, "extent": [W, S, E, N]}, open(f"{OUT}/meta.json", "w"))
print("places", len(places), "release", REL)
