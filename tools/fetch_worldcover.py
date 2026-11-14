#!/usr/bin/env python3
"""Read ESA WorldCover 10 m (2021, v200, CC BY 4.0) for the Laoag extent straight from its public COG on S3.

Usage:  python3 -I tools/fetch_worldcover.py <out_dir>
Needs:  pip install rasterio shapely
Output: <out_dir>/landcover_wc.geojson (vectorised classes, property k) and wc_stats.json (pixel-count shares)
Class index k: 0 tree cover, 1 shrubland, 2 grassland, 3 cropland, 4 bare/sparse, 5 built-up, 6 wetland/mangrove
Permanent water (class 80) is left out on purpose: the water layer comes from OpenStreetMap.
"""
import json, os, sys
import numpy as np, rasterio
from rasterio.features import shapes, sieve
from rasterio.windows import from_bounds
from shapely.geometry import shape

OUT = sys.argv[1]
W, S, E, N = json.load(open(f"{OUT}/meta.json"))["extent"]
URL = ("/vsicurl/https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
       "ESA_WorldCover_10m_2021_v200_N18E120_Map.tif")
MAP = {10: 0, 20: 1, 30: 2, 40: 3, 60: 4, 50: 5, 90: 6, 95: 6}
os.environ.setdefault("CURL_CA_BUNDLE", "/root/.ccr/ca-bundle.crt")
with rasterio.Env(GDAL_HTTP_MULTIRANGE="YES", AWS_NO_SIGN_REQUEST="YES"):
    with rasterio.open(URL) as ds:
        win = from_bounds(W, S, E, N, ds.transform)
        arr = ds.read(1, window=win)
        tr = ds.window_transform(win)
print("window", arr.shape)

k = np.full(arr.shape, 255, np.uint8)
for code, idx in MAP.items():
    k[arr == code] = idx
valid = (k != 255)
counts = {i: int((k == i).sum()) for i in range(7)}
water_px = int((arr == 80).sum())
total = arr.size
stats = {"px_total": total, "water_px": water_px, "share": {i: counts[i] / total * 100 for i in counts},
         "water_share": water_px / total * 100, "pixel_m": [9.27, 9.21]}
json.dump(stats, open(f"{OUT}/wc_stats.json", "w"))
print("shares %", {i: round(v, 2) for i, v in stats["share"].items()}, "water", round(stats["water_share"], 2))

k = sieve(k, 6, connectivity=4)                      # drop clusters under 6 px (~500 m2) for a cleaner map
feats = []
for geom, val in shapes(k, mask=(k != 255), transform=tr, connectivity=4):
    g = shape(geom).simplify(0.00003, preserve_topology=True)
    if g.is_empty: continue
    feats.append({"type": "Feature", "properties": {"k": int(val)}, "geometry": g.__geo_interface__})
json.dump({"type": "FeatureCollection", "features": feats}, open(f"{OUT}/landcover_wc.geojson", "w"))
print("polygons", len(feats))
