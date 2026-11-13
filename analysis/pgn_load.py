"""Loaders for Pandonia Global Network (PGN) L2 bulk files (BlickP p1-8).

Column numbers are 1-based and follow the file headers (see the 'Column n:' lines).
Bulk files are concatenations of daily files; only rows starting with yyyymmddT are data.
"""
import re
import numpy as np
import pandas as pd

FILL = -8.9e99  # PGN uses -9e99 for failed retrievals

SPECS = {
    # product code -> {name: 1-based column}
    "rwvt1": dict(sza=4, atmvar=26, aod_c=28, qa_l1=30, qa=36, wv_col=39, wv_unc=40,
                  wv_temp=45, amf=50, diffuse=52),
    "rout2": dict(sza=4, atmvar=26, aod_c=28, qa_l1=30, qa=36, o3_col=39, o3_unc=40,
                  o3_temp=45),
    "rnvh3": dict(sza=4, qa_wv=42, wv_surf=45, wv_surf_idx=47, wv_trop=49, qa_no2=53,
                  no2_surf=56, no2_strat=60, no2_trop=62, no2_trop_unc=63),
}


def load_l2(path, code):
    spec = SPECS[code]
    rows = []
    pat = re.compile(r"^20\d{6}T")
    with open(path, "r", errors="replace") as fh:
        for ln in fh:
            if pat.match(ln):
                p = ln.split()
                rows.append((p[0], [p[c - 1] for c in spec.values()]))
    df = pd.DataFrame([r[1] for r in rows], columns=list(spec.keys()), dtype=float)
    df.insert(0, "utc", pd.to_datetime([r[0] for r in rows], format="%Y%m%dT%H%M%S.%fZ", utc=True))
    df = df.drop_duplicates("utc").set_index("utc").sort_index()
    for c in df.columns:
        df.loc[df[c] < FILL, c] = np.nan
    return df
