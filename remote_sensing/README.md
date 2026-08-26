# Coastal Ilocos Norte Salinity — RS Pipeline

Implements stage 2 (acquisition) and stage 3 (index computation) of the
saline-affected agricultural area assessment: pulls Landsat + Sentinel-2 +
Sentinel-1 + MODIS + CHIRPS composites for the coastal municipalities,
harmonizes bands, and stacks NDVI/salinity/SAR/thermal/rainfall features
into one exportable image.

## Setup in VS Code

1. Open this `remote_sensing/` folder in VS Code (`code .`), and install the
   recommended extensions when prompted (Python, Pylance, Jupyter).
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. In VS Code, run **Python: Select Interpreter** and pick `.venv`
   (already the default via `.vscode/settings.json`).
4. Copy `.env.example` to `.env` and set `EE_PROJECT` to a GCP project that
   has the Earth Engine API enabled (create one free at
   https://code.earthengine.google.com/).
5. First run will open a browser window for `ee.Authenticate()` — sign in
   with the Google account tied to that project.

## Run

From the integrated terminal (or press F5 — the `launch.json` config is
already wired up):

```bash
python src/main.py --year 2025 --season dry --out exports/2025_dry_stack.tif
```

This exports a single multi-band GeoTIFF (optical bands + all indices from
stage 3 + SAR ratio + elevation + LST + rainfall) for the given year/season,
clipped to the buffered coastal-municipality AOI. Open it in QGIS, or in a
VS Code Jupyter notebook via `geemap.Map()` for an interactive preview.

Run it once per epoch you need (baseline vs. current, dry vs. wet season) to
build the time series described in the methodology.

## Files

- `src/config.py` — AOI municipalities, seasonal windows, cloud thresholds,
  collection IDs, band-name maps. Edit this first for any AOI/date change.
- `src/acquisition.py` — stage 2: per-sensor composite builders (cloud
  masking, SAR speckle filter, band harmonization).
- `src/indices.py` — stage 3: NDVI/SAVI/NDWI/MNDWI, salinity indices
  (SI1-3, NDSI, VSSI, CRSI, BI), SAR ratio, and the combined feature stack.
- `src/main.py` — CLI entry point tying acquisition + indices together and
  exporting the result.

## Next steps not yet in this script

- Field EC sampling to calibrate/validate the salinity indices (stage 4).
- Random Forest / SVM classifier trained on the exported stack + EC labels
  (stage 5) — not included here since it depends on your field data.
