#!/usr/bin/env python3
"""Agreement statistics: Pandora #219 water vapour (test) vs ERA5 TCWV (reference).

    python3 agreement_stats.py --data data --out .

Writes tables/agreement_overall.csv, tables/agreement_strata.csv, agreement_stats.json and
figures/fig7_agreement.png.

Conventions
  * x = ERA5 (reference), y = Pandora (test), d = y - x.  Units: mm (kg/m2).
  * Collocation: Pandora screened samples (see weather_understanding.py) are medianed per UTC hour
    (>= 5 samples); ERA5 is the mean of the hourly values bracketing the hour (== value at the
    window centre, hh:30). `hourlabel` (ERA5 at hh:00) is reported as a sensitivity case.
  * Confidence intervals: 95 % percentile bootstrap resampling whole LOCAL DAYS (hours within a day
    are strongly autocorrelated, so a plain bootstrap would give intervals that are far too narrow).
  * ERA5 is a model product, not truth: these are agreement statistics, not Pandora accuracy.
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

import weather_understanding as W

N_BOOT = 2000
RNG = np.random.default_rng(20260513)


# ------------------------------------------------------------------ metrics
def deming(x, y):
    """Orthogonal (Deming, error-variance ratio = 1) regression of y on x."""
    mx, my = x.mean(), y.mean()
    sxx, syy = ((x - mx) ** 2).mean(), ((y - my) ** 2).mean()
    sxy = ((x - mx) * (y - my)).mean()
    slope = (syy - sxx + np.sqrt((syy - sxx) ** 2 + 4 * sxy ** 2)) / (2 * sxy)
    return slope, my - slope * mx


def core(x, y):
    """Point estimates used inside the bootstrap (fast)."""
    d = y - x
    sl = stats.linregress(x, y)
    return dict(bias=d.mean(), mae=np.abs(d).mean(), rmse=np.sqrt((d ** 2).mean()),
                r=np.corrcoef(x, y)[0, 1], slope_ols=sl.slope)


def full(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    d = y - x
    n = len(x)
    mx, my = x.mean(), y.mean()
    sx, sy = x.std(), y.std()
    r = np.corrcoef(x, y)[0, 1]
    rmse = np.sqrt((d ** 2).mean())
    ols = stats.linregress(x, y)
    dem_s, dem_i = deming(x, y)
    # Lin's concordance correlation coefficient: accuracy x precision in one number
    ccc = 2 * r * sx * sy / (sx ** 2 + sy ** 2 + (mx - my) ** 2)
    # Willmott index of agreement (1 = perfect)
    will = 1 - ((d ** 2).sum()) / (((np.abs(y - mx) + np.abs(x - mx)) ** 2).sum())
    # Kling-Gupta efficiency (1 = perfect): correlation, variability ratio, bias ratio
    kge = 1 - np.sqrt((r - 1) ** 2 + (sy / sx - 1) ** 2 + (my / mx - 1) ** 2)
    # Bland-Altman: proportional bias = slope of d on pair mean
    m = (x + y) / 2
    ba = stats.linregress(m, d)
    sd_d = d.std(ddof=1)
    return dict(
        n=n, mean_ref=mx, mean_test=my, sd_ref=sx, sd_test=sy,
        bias=d.mean(), bias_pct=100 * d.mean() / mx, median_diff=float(np.median(d)),
        mae=np.abs(d).mean(), mae_pct=100 * np.abs(d).mean() / mx,
        medae=float(np.median(np.abs(d))), p90_abs_err=float(np.quantile(np.abs(d), .9)),
        rmse=rmse, rmse_pct=100 * rmse / mx, ubrmse=np.sqrt(max(rmse ** 2 - d.mean() ** 2, 0)),
        mape_pct=100 * np.mean(np.abs(d) / x),
        r=r, r2=r ** 2, spearman=stats.spearmanr(x, y)[0],
        slope_ols=ols.slope, intercept_ols=ols.intercept,
        slope_deming=dem_s, intercept_deming=dem_i,
        ccc=ccc, willmott_d=will, kge=kge, std_ratio=sy / sx,
        ba_sd_diff=sd_d, ba_loa_lower=d.mean() - 1.96 * sd_d, ba_loa_upper=d.mean() + 1.96 * sd_d,
        ba_prop_slope=ba.slope, ba_prop_p=ba.pvalue,
        within_2mm=100 * np.mean(np.abs(d) <= 2), within_3mm=100 * np.mean(np.abs(d) <= 3),
        within_5mm=100 * np.mean(np.abs(d) <= 5), within_10pct=100 * np.mean(np.abs(d) <= 0.1 * x),
    )


def boot_ci(x, y, days, n_boot=N_BOOT):
    """Day-block percentile bootstrap CIs for the headline metrics."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    codes, uniq = pd.factorize(days)
    idx = [np.flatnonzero(codes == k) for k in range(len(uniq))]
    out = {k: [] for k in ("bias", "mae", "rmse", "r", "slope_ols")}
    for _ in range(n_boot):
        pick = RNG.integers(0, len(idx), len(idx))
        sel = np.concatenate([idx[i] for i in pick])
        c = core(x[sel], y[sel])
        for k in out:
            out[k].append(c[k])
    return {k: (float(np.quantile(v, .025)), float(np.quantile(v, .975))) for k, v in out.items()}


# ------------------------------------------------------------------ data
def collocate(wv, E):
    ph = wv.pwv.resample("1h").agg(["median", "count"])
    ph.columns = ["p", "n"]
    ph["sza"] = wv.sza.resample("1h").median()
    e = E.total_column_integrated_water_vapour
    cc = E.cloud_cover
    mid = pd.DataFrame({
        "e_mid": (e + e.shift(-1, freq="1h").reindex(e.index)) / 2,   # mean of hh:00 and hh+1:00
        "e_lab": e,
        "cloud": (cc + cc.shift(-1, freq="1h").reindex(cc.index)) / 2,
    })
    j = ph.join(mid, how="inner").dropna()
    j = j[j.n >= 5].copy()
    loc = j.index.tz_convert(None) + pd.Timedelta(hours=8) if j.index.tz is not None else j.index + pd.Timedelta(hours=8)
    j["lt"] = loc
    j["day"] = loc.normalize()
    j["hour"] = loc.hour
    j["month"] = loc.month
    j["year"] = loc.year
    return j


def strata_defs(j):
    yield "all", "all", pd.Series(True, index=j.index)
    yield "season", "dry (Nov–Apr)", j.month.isin([11, 12, 1, 2, 3, 4])
    yield "season", "wet (May–Oct)", j.month.isin([5, 6, 7, 8, 9, 10])
    for y in sorted(j.year.unique()):
        yield "year", str(y), j.year == y
    for lo, hi in [(0, 40), (40, 50), (50, 90)]:
        yield "ERA5 moisture (mm)", f"{lo}–{hi}", (j.e_mid >= lo) & (j.e_mid < hi)
    for lo, hi, lab in [(0, 30, "clear <30 %"), (30, 70, "partly 30–70 %"), (70, 101, "cloudy ≥70 %")]:
        yield "ERA5 cloud cover", lab, (j.cloud >= lo) & (j.cloud < hi)
    for lo, hi in [(7, 10), (10, 13), (13, 17)]:
        yield "local hour", f"{lo:02d}–{hi:02d} h", (j.hour >= lo) & (j.hour < hi)
    for lo, hi in [(0, 35), (35, 50), (50, 70)]:
        yield "solar zenith (°)", f"{lo}–{hi}", (j.sza >= lo) & (j.sza < hi)


# ------------------------------------------------------------------ figure
def figure(j, S, out):
    x, y = j.e_mid.values, j.p.values
    d = y - x
    fig = plt.figure(figsize=(12, 8.6))
    gs = fig.add_gridspec(2, 2, hspace=0.38, wspace=0.42, width_ratios=[1, 1.1])

    a = fig.add_subplot(gs[0, 0])
    h = a.hexbin(x, y, gridsize=36, cmap=W.SEQ, mincnt=1, linewidths=.2, edgecolors=W.SURF)
    t = np.array([10, 80])
    a.plot(t, t, color=W.INK2, lw=1, ls="--", label="1:1")
    a.plot(t, S["slope_ols"] * t + S["intercept_ols"], color=W.ORANGE, lw=1.6, label="OLS")
    a.plot(t, S["slope_deming"] * t + S["intercept_deming"], color=W.AQUA, lw=1.6, label="Orthogonal (Deming)")
    a.set(xlim=(10, 80), ylim=(10, 80), xlabel="ERA5 TCWV (mm)", ylabel="Pandora #219 (mm)", title="(a) Scatter and regression")
    a.legend(loc="lower right", fontsize=8.5)
    a.text(.04, .96, f"y = {S['slope_deming']:.2f}x {S['intercept_deming']:+.1f}  (orthogonal)\n"
                     f"y = {S['slope_ols']:.2f}x {S['intercept_ols']:+.1f}  (OLS)\n"
                     f"CCC = {S['ccc']:.3f}   R² = {S['r2']:.3f}", transform=a.transAxes, va="top", fontsize=9)

    b = fig.add_subplot(gs[0, 1])
    m = (x + y) / 2
    b.hexbin(m, d, gridsize=36, cmap=W.SEQ, mincnt=1, linewidths=.2, edgecolors=W.SURF, extent=(10, 75, -16, 12))
    b.axhline(S["bias"], color=W.INK, lw=1.5)
    for v in (S["ba_loa_lower"], S["ba_loa_upper"]):
        b.axhline(v, color=W.INK2, lw=1.2, ls="--")
    b.axhline(0, color=W.GRID, lw=1)
    b.set(xlabel="mean of Pandora and ERA5 (mm)", ylabel="Pandora − ERA5 (mm)", xlim=(10, 75), ylim=(-16, 12),
          title="(b) Bland–Altman")
    b.text(74, S["ba_loa_upper"] + .5, f"+1.96 SD = {S['ba_loa_upper']:+.1f}", ha="right", fontsize=8.5, color=W.INK2)
    b.text(74, S["ba_loa_lower"] - 1.4, f"−1.96 SD = {S['ba_loa_lower']:+.1f}", ha="right", fontsize=8.5, color=W.INK2)
    b.text(74, S["bias"] + .5, f"bias = {S['bias']:+.1f}", ha="right", fontsize=8.5, color=W.INK)

    c = fig.add_subplot(gs[1, 0])
    c.hist(d, bins=np.arange(-14, 12.5, 1), color=W.BLUE, edgecolor=W.SURF, linewidth=.6)
    c.axvline(0, color=W.INK2, lw=1, ls="--")
    c.axvline(S["bias"], color=W.INK, lw=1.5)
    c.set(xlabel="Pandora − ERA5 (mm)", ylabel="hours", title="(c) Error distribution")
    c.text(.97, .95, f"bias {S['bias']:+.2f} mm\nSD {S['ba_sd_diff']:.2f} mm\nMAE {S['mae']:.2f} mm\nRMSE {S['rmse']:.2f} mm\n"
                     f"within ±3 mm: {S['within_3mm']:.0f} %\nwithin ±10 %: {S['within_10pct']:.0f} %",
           transform=c.transAxes, ha="right", va="top", fontsize=9)

    e = fig.add_subplot(gs[1, 1])
    short = {"season": "Season", "ERA5 moisture (mm)": "Moisture", "ERA5 cloud cover": "Cloud", "local hour": "Hour"}
    rows = [r for r in out if r["group"] in short]
    rows = rows[::-1]
    ypos = np.arange(len(rows))
    e.hlines(ypos, [r["bias"] for r in rows], [r["rmse"] for r in rows], color=W.GRID, lw=2)
    e.plot([r["bias"] for r in rows], ypos, "o", color=W.BLUE, ms=7, label="bias")
    e.plot([r["rmse"] for r in rows], ypos, "D", color=W.ORANGE, ms=6, label="RMSE")
    e.axvline(0, color=W.INK2, lw=1)
    e.set_yticks(ypos, [f"{short[r['group']]} {r['stratum'].split(' (')[0]}  n={r['n']:,}" for r in rows], fontsize=8.5)
    e.set(xlabel="mm", title="(d) Bias and RMSE by regime", xlim=(-3.8, 4.4))
    e.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, fontsize=8.5)
    e.grid(axis="y", visible=False)
    fig.savefig(out_fig, dpi=170, bbox_inches="tight")
    plt.close(fig)


def main():
    global out
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", default=".")
    a = ap.parse_args()
    d_, root = Path(a.data), Path(a.out)
    (root / "tables").mkdir(parents=True, exist_ok=True)
    (root / "figures").mkdir(parents=True, exist_ok=True)
    wv, o3, no, P, E, C, meta = W.load_all(d_)
    j = collocate(wv, E)

    results, rows = {}, []
    for case, col in (("interpolated_to_window_centre", "e_mid"), ("hourlabel", "e_lab")):
        s = full(j[col], j.p)
        ci = boot_ci(j[col].values, j.p.values, j.day.values)
        s["ci95"] = ci
        results[case] = s

    # strata use the primary (window-centre) collocation
    j2 = j.copy()
    out = []
    for grp, lab, mask in strata_defs(j2):
        sub = j2[mask]
        if len(sub) < 100:
            continue
        s = full(sub.e_mid, sub.p)
        out.append(dict(group=grp, stratum=lab, **{k: s[k] for k in (
            "n", "mean_ref", "mean_test", "bias", "bias_pct", "mae", "rmse", "rmse_pct", "ubrmse", "r",
            "slope_ols", "slope_deming", "ccc", "willmott_d", "kge", "within_3mm", "within_10pct")}))
    S = results["interpolated_to_window_centre"]
    S["n_days"] = int(j.day.nunique())

    # daily means (days with >= 4 matched hours), a more independent sample than hourly pairs
    g = j.groupby("day").agg(p=("p", "mean"), e=("e_mid", "mean"), k=("p", "size"))
    g = g[g.k >= 4]
    results["daily_mean"] = full(g.e, g.p)
    results["daily_mean"]["ci95"] = boot_ci(g.e.values, g.p.values, g.index.values)

    # --- outputs
    def clean(o):
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        if isinstance(o, (np.floating, float)):
            return round(float(o), 4)
        if isinstance(o, (np.integer,)):
            return int(o)
        return o

    json.dump(clean(results), open(root / "agreement_stats.json", "w"), indent=1)
    pd.DataFrame(out).round(3).to_csv(root / "tables" / "agreement_strata.csv", index=False)
    ov = pd.DataFrame({k: {m: v for m, v in s.items() if m != "ci95"} for k, s in results.items()}).T
    ov.round(4).to_csv(root / "tables" / "agreement_overall.csv")
    global out_fig
    out_fig = root / "figures" / "fig7_agreement.png"
    figure(j, S, out)

    def line(k, ci=None):
        s = S[k]
        return f"{s:.3f}" if ci is None else f"{s:.3f} [{ci[0]:.3f}, {ci[1]:.3f}]"
    print("n hours", S["n"], "days", S["n_days"])
    for k in ("bias", "mae", "rmse", "r", "slope_ols"):
        print(f"{k:10s}", line(k, S["ci95"][k]))
    print("wrote tables/, agreement_stats.json, figures/fig7_agreement.png")


if __name__ == "__main__":
    main()
