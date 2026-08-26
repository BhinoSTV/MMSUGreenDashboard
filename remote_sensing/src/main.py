"""Orchestrates stage 2 (acquisition) + stage 3 (index computation) for one
epoch and exports the resulting feature stack.

Usage (from remote_sensing/, with the venv active):
    python src/main.py --year 2025 --season dry --out exports/2025_dry_stack.tif
"""
import argparse
import os

import ee
import geemap

import acquisition
import config
import indices
from ee_auth import init_ee


def season_dates(year: int, season: str) -> tuple[str, str]:
    start_md, end_md = config.DRY_SEASON if season == "dry" else config.WET_SEASON
    return f"{year}-{start_md}", f"{year}-{end_md}"


def build_epoch_stack(aoi: ee.FeatureCollection, year: int, season: str) -> ee.Image:
    start, end = season_dates(year, season)

    optical = acquisition.landsat_composite(aoi, start, end)
    if year >= 2016:  # Sentinel-2 SR archive starts effectively 2015-2016
        s2 = acquisition.sentinel2_composite(aoi, start, end)
        optical = s2.unmask(optical)  # prefer 10 m Sentinel-2, fall back to Landsat

    s1 = acquisition.sentinel1_composite(aoi, start, end)
    dem_img = acquisition.dem(aoi)
    lst_img = acquisition.modis_lst_composite(aoi, start, end)
    precip_img = acquisition.chirps_total(aoi, start, end)

    return indices.feature_stack(optical, s1, dem_img, lst_img, precip_img)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=config.CURRENT_YEAR)
    parser.add_argument("--season", choices=["dry", "wet"], default="dry")
    parser.add_argument("--out", default="exports/stack.tif")
    args = parser.parse_args()

    init_ee()
    aoi = acquisition.build_aoi()
    stack = build_epoch_stack(aoi, args.year, args.season)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    region = aoi.geometry()
    print(f"Exporting {args.year} {args.season}-season feature stack to {args.out} ...")
    geemap.ee_export_image(
        stack,
        filename=args.out,
        scale=config.OUTPUT_SCALE_M,
        region=region,
        crs=config.OUTPUT_CRS,
        file_per_band=False,
    )
    print("Done. Bands:", stack.bandNames().getInfo())


if __name__ == "__main__":
    main()
