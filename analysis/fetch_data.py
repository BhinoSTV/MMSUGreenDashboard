#!/usr/bin/env python3
"""Download every input used by weather_understanding.py into a data directory.

Sources (all public, no key needed for the ones below):
  * Pandonia Global Network (PGN) Pandora #219 "Ilocos" @ MMSU, L2 bulk files
    (water vapour rwvt1, NO2/profile rnvh3, ozone rout2) - https://api.pandonia-global-network.org
  * NASA POWER daily (MERRA-2 / CERES-based)          - https://power.larc.nasa.gov
  * ERA5 hourly via Open-Meteo archive API             - https://open-meteo.com
  * CAMS global atmospheric composition via Open-Meteo - https://open-meteo.com
  * NASA GIBS WMS (IMERG precipitation rate frame)     - https://gibs.earthdata.nasa.gov

Usage:  python3 fetch_data.py --out data [--start 2025-01-01] [--end 2026-11-10]

Transport is `curl` so that an HTTPS proxy / custom CA bundle configured in the
environment is honoured. Existing files are kept unless --force is given.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

LAT, LON = 18.0582, 120.5451  # PGN site "Ilocos" (Mariano Marcos State University)
PAN_ID = 219
PGN = "https://api.pandonia-global-network.org/v1/download/bulk_l2"
EVENT_TIME = "2025-09-22T10:00:00Z"  # IMERG frame at peak rain, see weather_understanding.py


# Philippine PGN network (water vapour only) for the spatial-transfer analysis
NETWORK = {  # name: (pan_id, lat, lon, alt_m)
    "Ilocos": (219, 18.0582, 120.5451, 34),
    "QuezonCity": (224, 14.635, 121.078, 63),
    "Palawan": (221, 9.7915, 118.734, 56),
    "Cebu": (225, 10.3551, 123.9111, 67),
}


def get(url, dest, force, timeout=600):
    if dest.exists() and dest.stat().st_size > 0 and not force:
        print(f"  keep   {dest.name}")
        return
    print(f"  fetch  {dest.name}")
    for attempt, wait in enumerate((0, 30, 90, 180, 300)):    # back off on HTTP 429 (API rate limits)
        if wait:
            print(f"  retry in {wait}s (attempt {attempt + 1})")
            time.sleep(wait)
        r = subprocess.run(["curl", "-sS", "-f", "-m", str(timeout), "-o", str(dest), url])
        if r.returncode == 0:
            return
    dest.unlink(missing_ok=True)
    sys.exit(f"download failed: {url}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data")
    ap.add_argument("--start", default="2025-01-01")
    ap.add_argument("--end", default="2026-11-10")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    s, e = a.start, a.end
    s8, e8 = s.replace("-", ""), e.replace("-", "")

    # PGN L2: the API defaults to pan_id=106, so pan_id must be passed explicitly.
    for code in ("rwvt1", "rnvh3", "rout2"):
        get(f"{PGN}?start_datetime={s}T00:00:00&end_datetime={e}T00:00:00"
            f"&pan_id={PAN_ID}&location=Ilocos&spectrometer=1&code={code}",
            out / f"pgn_{code}.txt", a.force)

    get("https://power.larc.nasa.gov/api/temporal/daily/point?parameters="
        "T2M,RH2M,PRECTOTCORR,PW,CLOUD_AMT,ALLSKY_SFC_SW_DWN,ALLSKY_KT,WS10M"
        f"&community=AG&longitude={LON}&latitude={LAT}&start={s8}&end={e8}&format=JSON",
        out / "power.json", a.force)

    get("https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={LAT}&longitude={LON}&start_date={s}&end_date={e}"
        "&hourly=precipitation,cloud_cover,surface_pressure,wind_speed_10m,"
        "wind_direction_10m,total_column_integrated_water_vapour&timezone=UTC",
        out / "era5.json", a.force)

    get("https://air-quality-api.open-meteo.com/v1/air-quality?"
        f"latitude={LAT}&longitude={LON}&start_date={s}&end_date={e}"
        "&hourly=nitrogen_dioxide,ozone,aerosol_optical_depth,pm2_5,dust&timezone=UTC",
        out / "cams.json", a.force)

    # other Philippine Pandora sites + ERA5 TCWV/cloud at each site (for spatial_calibration.py)
    for name, (pan, lat, lon, _) in NETWORK.items():
        if name != "Ilocos":
            get(f"{PGN}?start_datetime={s}T00:00:00&end_datetime={e}T00:00:00"
                f"&pan_id={pan}&location={name}&spectrometer=1&code=rwvt1",
                out / f"pgn_rwvt1_{name}.txt", a.force)
        get("https://archive-api.open-meteo.com/v1/archive?"
            f"latitude={lat}&longitude={lon}&start_date={s}&end_date={e}"
            "&hourly=total_column_integrated_water_vapour,cloud_cover,precipitation&timezone=UTC",
            out / f"era5_{name}.json", a.force)

    wms = ("https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?SERVICE=WMS&REQUEST=GetMap"
           "&VERSION=1.1.1&SRS=EPSG:4326&BBOX=114,10,128,24&WIDTH=1120&HEIGHT=1120"
           "&FORMAT=image/png&STYLES=&TRANSPARENT=TRUE")
    get(f"{wms}&LAYERS=IMERG_Precipitation_Rate&TIME={EVENT_TIME}", out / "imerg_event.png", a.force)
    get(f"{wms}&LAYERS=Coastlines_15m", out / "coastlines.png", a.force)
    print("done ->", out.resolve())


if __name__ == "__main__":
    main()
