#!/usr/bin/env python3
"""Calibrate ERA5 total column water vapour to Pandora #219 (Pandora = reference).

    python3 calibrate_era5.py --data data --out .

Candidate correction models are fitted on Pandora/ERA5 hourly pairs (see agreement_stats.collocate)
and scored ONLY on held-out data:
  * leave-one-month-out (LOMO) cross-validation (primary)
  * train 2025 -> test 2026, and dry <-> wet season transfer (stress tests)
The simplest model within 2 % of the best LOMO RMSE is selected, refitted on all pairs and applied to
the whole hourly ERA5 record. Output rows carry a flag saying whether they are inside the calibration
domain (daytime hours where Pandora direct-sun data exist); outside it the correction is an extrapolation.

Outputs: calibration.json, tables/era5_calibration_cv.csv, tables/era5_tcwv_calibrated.csv,
         figures/fig8_era5_calibration.png

Interpretation limits (also in README): the calibrated series inherits Pandora's own bias, its
"not-assured" status, and its clear-sun sampling. Statistics of the calibrated product must be reported
out-of-sample only (the CV numbers below), never in-sample.
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import agreement_stats as A
import weather_understanding as W

HOUR_BINS = [(0, 10), (10, 13), (13, 24)]   # local hour; first/last bins absorb early/late hours


def hbin(h):
    h = np.asarray(h)
    return np.digitize(h, [10, 13])            # 0,1,2


def season(m):
    return np.isin(np.asarray(m), [5, 6, 7, 8, 9, 10]).astype(int)   # 1 = wet


# ---------------------------------------------------------------- models: fit(x, y, meta) -> predictor
# x = ERA5, y = Pandora, meta = DataFrame(hour, month). predictor(x, meta) -> corrected ERA5
def m_none(x, y, m):
    return lambda xv, mv: xv


def m_offset(x, y, m):
    b = (y - x).mean()
    return lambda xv, mv: xv + b


def m_scale(x, y, m):
    s = (x * y).sum() / (x * x).sum()
    return lambda xv, mv: xv * s


def m_linear(x, y, m):
    s, i = np.polyfit(x, y, 1)
    return lambda xv, mv: xv * s + i


def _grouped_scale(keyf):
    def fit(x, y, m):
        k = keyf(m)
        s = {g: (x[k == g] * y[k == g]).sum() / (x[k == g] ** 2).sum() for g in np.unique(k)}
        glob = (x * y).sum() / (x * x).sum()
        return lambda xv, mv: xv * np.array([s.get(g, glob) for g in keyf(mv)])
    return fit


m_scale_season = _grouped_scale(lambda m: season(m.month.values))
m_scale_hour = _grouped_scale(lambda m: hbin(m.hour.values))
m_scale_season_hour = _grouped_scale(lambda m: season(m.month.values) * 3 + hbin(m.hour.values))


def m_quantile(x, y, m):
    q = np.linspace(0.01, 0.99, 99)
    qx, qy = np.quantile(x, q), np.quantile(y, q)
    lo, hi = qy[0] - qx[0], qy[-1] - qx[-1]       # constant shift beyond the fitted range

    def f(xv, mv):
        out = np.interp(xv, qx, qy)
        out = np.where(xv < qx[0], xv + lo, out)
        return np.where(xv > qx[-1], xv + hi, out)
    return f


MODELS = {            # name: (fit function, number of parameters)
    "none (raw ERA5)": (m_none, 0),
    "offset": (m_offset, 1),
    "scale": (m_scale, 1),
    "scale by season": (m_scale_season, 2),
    "scale by hour": (m_scale_hour, 3),
    "scale by season×hour": (m_scale_season_hour, 6),
    "linear": (m_linear, 2),
    "quantile mapping": (m_quantile, 99),
}


def cv_predict(df, fit, blocks):
    x, y, meta = df.e_mid.values, df.p.values, df[["hour", "month"]]
    pred = np.empty_like(y)
    for b in np.unique(blocks):
        te = blocks == b
        f = fit(x[~te], y[~te], meta[~te])
        pred[te] = f(x[te], meta[te])
    return pred


def split_eval(df, fit, tr, te):
    x, y, meta = df.e_mid.values, df.p.values, df[["hour", "month"]]
    f = fit(x[tr], y[tr], meta[tr])
    return f(x[te], meta[te])


def metrics(obs, pred):
    d = pred - obs
    return dict(rmse=float(np.sqrt((d ** 2).mean())), mae=float(np.abs(d).mean()), bias=float(d.mean()),
                r=float(np.corrcoef(obs, pred)[0, 1]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", default=".")
    a = ap.parse_args()
    root = Path(a.out)
    (root / "tables").mkdir(exist_ok=True, parents=True)
    (root / "figures").mkdir(exist_ok=True, parents=True)
    wv, o3, no, P, E, C, meta = W.load_all(Path(a.data))
    j = A.collocate(wv, E).reset_index(drop=True)
    y = j.p.values
    blocks = (j.year * 100 + j.month).values
    dry = ~(season(j.month.values).astype(bool))
    tr25 = (j.year == 2025).values

    rows, cv_pred = [], {}
    for name, (fit, npar) in MODELS.items():
        pred = cv_predict(j, fit, blocks)
        cv_pred[name] = pred
        mm = metrics(y, pred)
        ci = A.boot_ci(y, pred, j.day.values, n_boot=500)      # x=obs, y=pred -> bias = pred - obs
        row = dict(model=name, n_params=npar, lomo_rmse=mm["rmse"], lomo_rmse_lo=ci["rmse"][0], lomo_rmse_hi=ci["rmse"][1],
                   lomo_mae=mm["mae"], lomo_bias=mm["bias"], lomo_r=mm["r"])
        # stress tests
        p = split_eval(j, fit, tr25, ~tr25)
        row["train2025_test2026_rmse"] = metrics(y[~tr25], p)["rmse"]
        row["train2025_test2026_bias"] = metrics(y[~tr25], p)["bias"]
        p = split_eval(j, fit, dry, ~dry)
        row["dry_to_wet_rmse"] = metrics(y[~dry], p)["rmse"]
        p = split_eval(j, fit, ~dry, dry)
        row["wet_to_dry_rmse"] = metrics(y[dry], p)["rmse"]
        rows.append(row)
    T = pd.DataFrame(rows)
    T.round(3).to_csv(root / "tables" / "era5_calibration_cv.csv", index=False)

    best = T.lomo_rmse.min()
    cand = T[(T.lomo_rmse <= best * 1.02) & (T.model != "none (raw ERA5)")].sort_values("n_params")
    chosen = cand.iloc[0].model
    fit = MODELS[chosen][0]

    # final fit on all pairs; apply to the whole hourly ERA5 record
    f = fit(j.e_mid.values, y, j[["hour", "month"]])
    e = E.total_column_integrated_water_vapour.copy()
    loc = e.index.tz_convert(None) + pd.Timedelta(hours=8)
    mfull = pd.DataFrame({"hour": loc.hour, "month": loc.month}, index=e.index)
    cal = pd.DataFrame({"era5_tcwv_mm": e.values, "era5_calibrated_mm": f(e.values, mfull)}, index=e.index)
    cal["local_hour"] = loc.hour
    # calibration domain: local hours where Pandora direct-sun data are plentiful
    hh = j.groupby("hour").size()
    ok_hours = set(hh[hh >= 0.02 * len(j)].index)
    cal["in_calibration_domain"] = cal.local_hour.isin(ok_hours)
    cal.round(3).to_csv(root / "tables" / "era5_tcwv_calibrated.csv", index_label="utc")

    # coefficients of the chosen model (human-readable)
    coef = {}
    x_, meta_ = j.e_mid.values, j[["hour", "month"]]
    if chosen == "scale":
        coef = {"factor": float((x_ * y).sum() / (x_ * x_).sum())}
        codes, uniq = pd.factorize(j.day.values)                  # day-block bootstrap of the factor
        idx = [np.flatnonzero(codes == k) for k in range(len(uniq))]
        rng = np.random.default_rng(1)
        bs = []
        for _ in range(2000):
            sel = np.concatenate([idx[i] for i in rng.integers(0, len(idx), len(idx))])
            bs.append((x_[sel] * y[sel]).sum() / (x_[sel] ** 2).sum())
        coef["factor_ci95"] = [float(np.quantile(bs, .025)), float(np.quantile(bs, .975))]
    elif chosen == "offset":
        coef = {"add_mm": float((y - x_).mean())}
    elif chosen == "linear":
        s, i = np.polyfit(x_, y, 1)
        coef = {"slope": float(s), "intercept_mm": float(i)}
    elif chosen in ("scale by season", "scale by hour", "scale by season×hour"):
        key = {"scale by season": season(meta_.month.values),
               "scale by hour": hbin(meta_.hour.values),
               "scale by season×hour": season(meta_.month.values) * 3 + hbin(meta_.hour.values)}[chosen]
        coef = {f"group_{int(g)}": float((x_[key == g] * y[key == g]).sum() / (x_[key == g] ** 2).sum()) for g in np.unique(key)}
        coef["groups"] = ("0=dry,1=wet" if chosen == "scale by season" else
                          "0=<10h,1=10-13h,2=>=13h" if chosen == "scale by hour" else "season*3+hourbin (season 0=dry,1=wet)")
    json.dump(dict(reference="Pandora #219 (not-assured)", target="ERA5 TCWV (Open-Meteo point)",
                   chosen=chosen, coefficients=coef, domain_hours=sorted(int(h) for h in ok_hours),
                   n_pairs=int(len(j)), selection_rule="simplest model within 2 % of best leave-one-month-out RMSE",
                   cv_table=T.round(3).to_dict(orient="records")), open(root / "calibration.json", "w"), indent=1)

    figure(j, y, cv_pred, chosen, T, root / "figures" / "fig8_era5_calibration.png")
    pd.set_option("display.width", 220)
    print(T.round(3).to_string(index=False))
    print("chosen:", chosen, coef)
    print("calibrated hours:", len(cal), " in-domain:", int(cal.in_calibration_domain.sum()))


def figure(j, y, cv_pred, chosen, T, path):
    raw, cor = cv_pred["none (raw ERA5)"], cv_pred[chosen]
    fig, ax = plt.subplots(2, 2, figsize=(12, 8.4))
    # (a) CV RMSE by model
    a = ax[0, 0]
    t = T.sort_values("lomo_rmse", ascending=False).reset_index(drop=True)
    cols = [W.ORANGE if m == chosen else W.BLUE for m in t.model]
    a.barh(t.index, t.lomo_rmse, color=cols, height=.62)
    a.errorbar(t.lomo_rmse, t.index, xerr=[t.lomo_rmse - t.lomo_rmse_lo, t.lomo_rmse_hi - t.lomo_rmse], fmt="none", ecolor=W.INK2, lw=1, capsize=2)
    a.set_yticks(t.index, t.model, fontsize=9)
    for i, v in zip(t.index, t.lomo_rmse):
        a.text(v + .17, i, f"{v:.2f}", va="center", fontsize=8.5, color=W.INK2)
    a.set(xlabel="held-out RMSE vs Pandora (mm), leave-one-month-out", title="(a) Candidate corrections (orange = selected)", xlim=(0, 4.2))
    a.grid(axis="y", visible=False)
    # (b) held-out scatter
    b = ax[0, 1]
    b.hexbin(y, cor, gridsize=34, cmap=W.SEQ, mincnt=1, linewidths=.2, edgecolors=W.SURF)
    b.plot([10, 80], [10, 80], color=W.INK2, ls="--", lw=1)
    m = metrics(y, cor); m0 = metrics(y, raw)
    b.text(.04, .96, f"held-out, {chosen}\nRMSE {m['rmse']:.2f} (raw {m0['rmse']:.2f})\nbias {m['bias']:+.2f} (raw {m0['bias']:+.2f})\nr {m['r']:.3f}",
           transform=b.transAxes, va="top", fontsize=9)
    b.set(xlim=(10, 80), ylim=(10, 80), xlabel="Pandora #219 (mm)", ylabel="calibrated ERA5, held-out (mm)", title="(b) Calibrated ERA5 vs Pandora")
    # (c) bias by local hour
    c = ax[1, 0]
    d = pd.DataFrame({"h": j.hour.values, "raw": raw - y, "cor": cor - y})
    g = d.groupby("h")[["raw", "cor"]].mean()
    g = g[g.index.isin(range(7, 17))]
    c.plot(g.index, g.raw, color=W.INK2, marker="s", ms=5, ls="--", lw=1.4, label="raw ERA5")
    c.plot(g.index, g.cor, color=W.BLUE, marker="o", ms=6, label="calibrated (held-out)")
    c.axhline(0, color=W.INK2, lw=1)
    c.set(xlabel="local hour", ylabel="ERA5 − Pandora (mm)", title="(c) Bias by hour of day")
    c.legend(fontsize=8.5, loc="upper left")
    # (d) bias by moisture bin
    e = ax[1, 1]
    bins = pd.cut(y, [10, 30, 40, 50, 60, 90])
    d2 = pd.DataFrame({"b": bins, "raw": raw - y, "cor": cor - y}).groupby("b", observed=True)[["raw", "cor"]].mean()
    xs = np.arange(len(d2))
    e.bar(xs - .2, d2.raw, .38, color=W.INK2, label="raw ERA5")
    e.bar(xs + .2, d2.cor, .38, color=W.BLUE, label="calibrated (held-out)")
    e.axhline(0, color=W.INK2, lw=1)
    e.set_xticks(xs, [f"{int(i.left)}–{int(i.right)}" for i in d2.index])
    e.set(xlabel="Pandora water vapour (mm)", ylabel="ERA5 − Pandora (mm)", title="(d) Bias by moisture regime")
    e.legend(fontsize=8.5, loc="lower left")
    e.grid(axis="x", visible=False)
    fig.tight_layout()
    fig.savefig(path, dpi=170)
    plt.close(fig)


if __name__ == "__main__":
    main()
