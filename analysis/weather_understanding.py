#!/usr/bin/env python3
"""Weather understanding at MMSU (Batac, Ilocos Norte) from Pandora + satellite-based data.

Reads the files produced by fetch_data.py, writes figures/*.png and metrics.json.

    python3 weather_understanding.py --data data --out .

Method summary (see README.md for assumptions and limitations)
  * Pandora #219 water-vapour column (mol/m2 * 18.015e-3 kg/mol = kg/m2 = mm PWV), screened by
    physical range, SZA < 70 deg, L2 quality <= 11 and relative uncertainty < 20 %.
    NOTE: every record from this instrument is "not-assured" (QA 10/11/12) - it is validated here
    against independent products rather than trusted a priori.
  * Reference / context: ERA5 (hourly TCWV, rain, pressure, wind), MERRA-2 + CERES via NASA POWER
    (daily PW, rain bias-corrected with GPCP, clearness index), CAMS (aerosol optical depth),
    GPM IMERG (rain-rate frame through NASA GIBS).
  * All times converted to Manila local time (UTC+8) for day/hour statistics.
"""
import argparse
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.dates as mdates
from matplotlib import image as mimg
from matplotlib.colors import LinearSegmentedColormap
from scipy import stats

import pgn_load as L

MW_H2O = 18.015e-3          # kg/mol  (kg/m2 == mm of liquid water)
DU_PER_MOL_M2 = 1 / 4.4615e-4
NO2_1E15_PER_MOL_M2 = 6.02214e23 / 1e4 / 1e15   # mol/m2 -> 1e15 molec/cm2
LAT, LON = 18.0582, 120.5451

# ---- design tokens (dataviz reference palette, light surface; validated slots 1-3) ----
SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e3e2dd"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
SEQ = LinearSegmentedColormap.from_list("seq", ["#eaf1fb", "#9cc3ee", "#2a78d6", "#123f7a"])

plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
    "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "legend.frameon": False, "lines.linewidth": 1.8,
})


def fmt_dates(ax, months=3):
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=months))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))


def stat(a, b):
    a, b = np.asarray(a), np.asarray(b)
    sl = stats.linregress(b, a)
    return dict(n=int(len(a)), r=float(np.corrcoef(a, b)[0, 1]), bias=float((a - b).mean()),
                bias_pct=float(100 * (a - b).mean() / b.mean()),
                rmse=float(np.sqrt(((a - b) ** 2).mean())), slope=float(sl.slope),
                intercept=float(sl.intercept))


def load_all(d):
    wv = L.load_l2(d / "pgn_rwvt1.txt", "rwvt1")
    o3 = L.load_l2(d / "pgn_rout2.txt", "rout2")
    no = L.load_l2(d / "pgn_rnvh3.txt", "rnvh3")
    wv["pwv"] = wv.wv_col * MW_H2O
    ok = (wv.pwv.between(5, 90) & (wv.qa <= 11) & (wv.sza < 70) & (wv.wv_unc > 0)
          & (wv.wv_unc < wv.wv_col * 0.2))
    meta = dict(wv_total=int(len(wv)), wv_kept=int(ok.sum()),
                wv_qa_counts={str(int(k)): int(v) for k, v in wv.qa.value_counts().items()},
                o3_qa_counts={str(int(k)): int(v) for k, v in o3.qa.value_counts().items()},
                no2_qa_counts={str(int(k)): int(v) for k, v in no.qa_no2.value_counts().items()})
    wv = wv[ok].copy()

    p = json.load(open(d / "power.json"))["properties"]["parameter"]
    P = pd.DataFrame({k: pd.Series(v) for k, v in p.items()})
    P.index = pd.to_datetime(P.index, format="%Y%m%d")
    P = P.replace(-999, np.nan)
    P["PW"] *= 10                                   # POWER PW is in cm -> mm

    e = json.load(open(d / "era5.json"))["hourly"]
    E = pd.DataFrame(e)
    E.index = pd.to_datetime(E.pop("time"), utc=True)
    c = json.load(open(d / "cams.json"))["hourly"]
    C = pd.DataFrame(c)
    C.index = pd.to_datetime(C.pop("time"), utc=True)
    return wv, o3, no, P, E, C, meta


def local(idx):
    return (idx + pd.Timedelta(hours=8)).tz_localize(None)


def fig_validation(wv, E, out, M):
    ph = wv.pwv.resample("1h").median()
    cnt = wv.pwv.resample("1h").count()
    e0 = E.total_column_integrated_water_vapour
    # ERA5 is instantaneous at hh:00; the Pandora hourly median covers hh:00-hh:59, so use the
    # mean of the bracketing ERA5 hours (= value at the window centre, hh:30)
    e = (e0 + e0.shift(-1, freq="1h").reindex(e0.index)) / 2
    j = pd.concat([ph.rename("p"), e.rename("e"), cnt.rename("n")], axis=1, sort=True).dropna()
    j = j[j.n >= 5]
    M["val_hourly_era5"] = stat(j.p, j.e)
    mb = (j.p - j.e).resample("MS").agg(["mean", "count"])
    mb = mb[mb["count"] >= 50]
    M["val_bias_by_month"] = {k.strftime("%Y-%m"): round(float(v), 2) for k, v in mb["mean"].items()}

    fig, ax = plt.subplots(1, 2, figsize=(11, 4.4), gridspec_kw=dict(width_ratios=[1, 1.25]))
    h = ax[0].hexbin(j.e, j.p, gridsize=34, cmap=SEQ, mincnt=1, linewidths=0.2, edgecolors=SURF)
    ax[0].plot([10, 80], [10, 80], color=INK2, lw=1, ls="--")
    s = M["val_hourly_era5"]
    ax[0].text(0.04, 0.96, f"n = {s['n']:,} hours\nr = {s['r']:.3f}\nbias = {s['bias']:+.1f} mm ({s['bias_pct']:+.0f} %)\n"
               f"RMSE = {s['rmse']:.1f} mm", transform=ax[0].transAxes, va="top", color=INK, fontsize=9.5)
    ax[0].set(xlabel="ERA5 total column water vapour (mm)", ylabel="Pandora #219 water vapour (mm)",
              xlim=(10, 80), ylim=(10, 80), title="Hourly agreement")
    cb = fig.colorbar(h, ax=ax[0], pad=0.02, fraction=0.05)
    cb.set_label("hours per cell", color=INK2)
    cb.outline.set_edgecolor(GRID)
    xs = np.arange(len(mb))
    ax[1].bar(xs, mb["mean"], color=BLUE, width=0.62)
    ax[1].axhline(0, color=INK2, lw=1)
    ax[1].set_xticks(xs[::2], [k.strftime("%b\n%Y") if k.month == 1 or i == 0 else k.strftime("%b")
                                for i, k in enumerate(mb.index)][::2])
    ax[1].set(ylabel="Pandora − ERA5 (mm)", title="Monthly bias: always dry (−0.9 to −4.1 mm), larger in 2026")
    ax[1].grid(axis="x", visible=False)
    fig.tight_layout()
    fig.savefig(out / "fig1_validation.png", dpi=170)
    plt.close(fig)


def fig_seasonal(wv, P, E, out, M):
    pl = wv.pwv.copy()
    pl.index = local(pl.index)
    mon = pl.resample("MS").agg(["median", lambda x: x.quantile(.1), lambda x: x.quantile(.9), "count"])
    mon.columns = ["med", "p10", "p90", "n"]
    mon = mon[mon.n >= 500]
    mon = mon.reindex(pd.date_range(mon.index.min(), mon.index.max(), freq="MS"))  # NaN breaks the line at gaps
    el = E.total_column_integrated_water_vapour.copy()
    el.index = local(el.index)
    # ERA5 sampled on days when Pandora has data, so the two curves are comparable
    days = set(pl.index.normalize())
    el = el[el.index.normalize().isin(days)].resample("MS").median()
    rain = P.PRECTOTCORR.resample("MS").sum()
    rain = rain[:"2026-10-01"]       # drop partial current month
    kt = P.ALLSKY_KT.resample("MS").mean()
    M["monthly"] = {
        k.strftime("%Y-%m"): dict(pwv_med=round(float(mon.med.get(k, np.nan)), 1),
                                  rain_mm=round(float(rain.get(k, np.nan)), 0),
                                  kt=round(float(kt.get(k, np.nan)), 2))
        for k in rain.index}
    dry = mon.med[mon.index.month.isin([1, 2, 3, 4])].mean()
    wet = mon.med[mon.index.month.isin([6, 7, 8, 9])].mean()
    M["season_pwv"] = dict(JFMA_mean=round(float(dry), 1), JJAS_mean=round(float(wet), 1),
                           contrast=round(float(wet - dry), 1))
    on = {y: mon.med[(mon.index.year == y) & (mon.index.month.isin([4, 5, 6]))].round(1).to_dict() for y in (2025, 2026)}
    M["onset_AMJ"] = {str(y): {k.strftime("%Y-%m"): v for k, v in d.items()} for y, d in on.items()}

    fig, ax = plt.subplots(3, 1, figsize=(11, 8.4), sharex=True, gridspec_kw=dict(height_ratios=[1.3, 1, 0.8]))
    ax[0].fill_between(mon.index, mon.p10, mon.p90, color=BLUE, alpha=.16, lw=0)
    ax[0].plot(mon.index, mon.med, color=BLUE, marker="o", ms=5)
    ax[0].plot(el.index, el.values, color=INK2, lw=1.2, ls="--")
    ax[0].set(ylabel="water vapour (mm)", title="Pandora column water vapour tracks the monsoon (band = 10th-90th pct of screened samples)")
    ax[0].plot([], [], color=BLUE, marker="o", ms=5, label="Pandora monthly median")
    ax[0].plot([], [], color=INK2, lw=1.2, ls="--", label="ERA5 (same days)")
    ax[0].fill_between([], [], [], color=BLUE, alpha=.16, lw=0, label="Pandora 10th–90th pct")
    ax[0].legend(loc="upper left", ncol=3, fontsize=9)
    ax[0].set_ylim(18, 70)
    ax[0].annotate("no Pandora data\n(Jun 2026)", (pd.Timestamp("2026-06-01"), 24), ha="center", fontsize=8.5, color=INK2)
    ax[1].bar(rain.index, rain.values, width=22, color=ORANGE)
    ax[1].set(ylabel="rainfall (mm / month)", title="Rainfall, MERRA-2 corrected with satellite-gauge precipitation (NASA POWER)")
    ax[2].plot(kt.index, kt.values, color=AQUA, marker="o", ms=4)
    ax[2].set(ylabel="clearness index", ylim=(0.2, 0.75), title="Surface clearness index (CERES-based all-sky shortwave / TOA)")
    ax[2].annotate("lower = cloudier", (pd.Timestamp("2025-07-01"), kt["2025-07-01"]), (10, -4), textcoords="offset points", color=INK, fontsize=9)
    for a in ax:
        a.grid(axis="x", visible=False)
    fmt_dates(ax[2])
    fig.tight_layout()
    fig.savefig(out / "fig2_seasonal.png", dpi=170)
    plt.close(fig)


def fig_rain_pickup(wv, P, out, M):
    pl = wv.pwv.copy()
    pl.index = local(pl.index)
    day = pl.groupby(pl.index.normalize()).agg(["median", "count"])
    day.columns = ["pwv", "n"]
    J = P.join(day, how="left")
    J["n"] = J.n.fillna(0)
    # Sample counts depend on the instrument's measurement schedule, which changed over time, so
    # normalise each day by the 90th percentile of the surrounding 31 days (relative direct-sun yield).
    ref = J.n.rolling(31, center=True, min_periods=10).quantile(0.9)
    J["rel"] = (J.n / ref).clip(0, 1.2)
    a = J[ref > 200].dropna(subset=["ALLSKY_KT"])
    M["sunyield"] = dict(
        n_days=int(len(a)),
        spearman_vs_clearness=float(stats.spearmanr(a.rel, a.ALLSKY_KT)[0]),
        spearman_vs_cloud_amt=float(stats.spearmanr(a.rel, a.CLOUD_AMT)[0]),
        spearman_vs_rain=float(stats.spearmanr(a.rel, a.PRECTOTCORR)[0]))
    d = J.dropna(subset=["pwv", "PRECTOTCORR"])
    d = d[d.n >= 100].copy()
    bins = [0, 35, 40, 45, 50, 55, 60, 80]
    d["b"] = pd.cut(d.pwv, bins)
    t = d.groupby("b", observed=True).agg(days=("pwv", "size"), mean_rain=("PRECTOTCORR", "mean"),
                                          p1=("PRECTOTCORR", lambda x: (x >= 1).mean()),
                                          p10=("PRECTOTCORR", lambda x: (x >= 10).mean()))
    M["rain_pickup"] = dict(spearman=float(stats.spearmanr(d.pwv, d.PRECTOTCORR)[0]), n_days=int(len(d)),
                            bins=[dict(bin=str(k), days=int(r.days), mean_rain=round(float(r.mean_rain), 1),
                                       p_ge1mm=round(float(r.p1), 2), p_ge10mm=round(float(r.p10), 2))
                                  for k, r in t.iterrows()])
    # composite of PWV anomaly (vs monthly median) around days with >= 50 mm rain
    J["anom"] = J.pwv - J.groupby(J.index.month).pwv.transform("median")
    comp = {k: [] for k in range(-5, 3)}
    events = J.index[J.PRECTOTCORR >= 50]
    for ev in events:
        for k in comp:
            t_ = ev + pd.Timedelta(days=k)
            if t_ in J.index and J.loc[t_, "n"] >= 100 and not np.isnan(J.loc[t_, "anom"]):
                comp[k].append(J.loc[t_, "anom"])
    M["event_composite"] = dict(n_events=int(len(events)),
                                lag_days={str(k): dict(n=len(v), mean_anom_mm=round(float(np.mean(v)), 1) if v else None)
                                          for k, v in comp.items()})
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.4), gridspec_kw=dict(width_ratios=[1.35, 1]))
    x = np.arange(len(t))
    w = 0.38
    ax[0].bar(x - w / 2 - 0.01, t.p1 * 100, w, color=BLUE, label="rain ≥ 1 mm/day")
    ax[0].bar(x + w / 2 + 0.01, t.p10 * 100, w, color=ORANGE, label="rain ≥ 10 mm/day")
    for xi, (k, r) in zip(x, t.iterrows()):
        ax[0].text(xi, -11, f"n={int(r.days)}", ha="center", fontsize=8.5, color=INK2)
    ax[0].set_xticks(x, [f"{int(k.left)}–{int(k.right)}" for k in t.index])
    ax[0].set(xlabel="Pandora daily-median water vapour (mm)", ylabel="% of days", ylim=(0, 105),
              title="Rain probability climbs steeply above ~50 mm")
    ax[0].xaxis.labelpad = 16
    ax[0].legend(loc="upper left")
    ax[0].grid(axis="x", visible=False)
    h = ax[1].hexbin(a.ALLSKY_KT, a.rel, gridsize=22, cmap=SEQ, mincnt=1, linewidths=.2, edgecolors=SURF)
    ax[1].set(xlabel="CERES-based clearness index (daily)", ylabel="relative Pandora yield (1 = typical clear day)",
              title="Direct-sun yield as a sunshine proxy")
    ax[1].text(0.04, 0.95, f"Spearman ρ = {M['sunyield']['spearman_vs_clearness']:.2f}\nn = {len(a)} days",
               transform=ax[1].transAxes, va="top", fontsize=9.5)
    fig.tight_layout()
    fig.savefig(out / "fig3_rain_pickup.png", dpi=170)
    plt.close(fig)
    return J


def fig_diurnal(wv, E, out, M):
    g = wv.copy()
    g.index = local(g.index)
    g["day"] = g.index.normalize()
    good = g.groupby("day").pwv.transform("count") >= 300
    days = set(g[good].day.unique())
    g = g[good & (g.sza < 50)].copy()
    g["dev"] = g.pwv - g.groupby("day").pwv.transform("mean")
    g["hr"] = g.index.hour
    g["mon"] = g.index.month
    e = E.total_column_integrated_water_vapour.copy()
    e.index = local(e.index)
    Ed = pd.DataFrame({"e": e})
    Ed["day"] = Ed.index.normalize()
    Ed = Ed[Ed.day.isin(days)].copy()
    Ed["dev"] = Ed.e - Ed.groupby("day").e.transform("mean")
    Ed["hr"] = Ed.index.hour
    Ed["mon"] = Ed.index.month
    seasons = [("Dry season (Nov–Apr)", [11, 12, 1, 2, 3, 4]), ("Wet season (May–Oct)", [5, 6, 7, 8, 9, 10])]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    M["diurnal"] = {}
    for a, (lab, ms) in zip(ax, seasons):
        pg = g[g.mon.isin(ms)].groupby("hr").dev.mean()
        pg = pg[(pg.index >= 8) & (pg.index <= 15)]
        eg = Ed[Ed.mon.isin(ms)].groupby("hr").dev.mean()
        eg = eg[(eg.index >= 8) & (eg.index <= 15)]
        a.plot(pg.index, pg.values, color=BLUE, marker="o", ms=6, zorder=3)
        a.plot(eg.index, eg.values, color=INK2, marker="s", ms=5, ls="--", lw=1.4)
        a.axhline(0, color=GRID, lw=1)
        a.set(title=lab, xlabel="local hour (UTC+8)")
        if a is ax[0]:
            a.plot([], [], color=BLUE, marker="o", ms=6, label="Pandora (SZA < 50°)")
            a.plot([], [], color=INK2, marker="s", ms=5, ls="--", lw=1.4, label="ERA5 (same days)")
            a.legend(loc="upper left", fontsize=9)
        M["diurnal"][lab] = dict(pandora=pg.round(2).to_dict(), era5=eg.round(2).to_dict(),
                                 n_days=int(g[g.mon.isin(ms)].day.nunique()))
    ax[0].set_ylabel("deviation from daily mean (mm)")
    fig.suptitle("Water vapour builds through the morning and peaks near 14:00 local", x=0.01, ha="left", fontweight="bold", fontsize=11)
    fig.tight_layout()
    fig.savefig(out / "fig4_diurnal.png", dpi=170)
    plt.close(fig)


def fig_composition(o3, no, C, P, out, M):
    n2 = no[(no.qa_no2 <= 11) & no.no2_trop.between(-1e-3, 1)].no2_trop * NO2_1E15_PER_MOL_M2
    n2l = n2.copy()
    n2l.index = local(n2l.index)
    n2m = n2l.resample("MS").agg(["median", "count"])
    n2m = n2m[n2m["count"] >= 150]
    ok = (o3.qa <= 11) & o3.o3_col.between(0.08, 0.2) & (o3.sza < 70)
    x = o3[ok].o3_col * DU_PER_MOL_M2
    x.index = local(x.index)
    om = x.resample("MS").agg(["median", "count"])
    om = om[om["count"] >= 150]
    aod = C.aerosol_optical_depth.copy()
    aod.index = local(aod.index)
    am = aod.resample("MS").mean()["2025-01-01":"2026-10-01"]
    pm = C.pm2_5.copy(); pm.index = local(pm.index); pmm = pm.resample("MS").mean()["2025-01-01":"2026-10-01"]
    M["composition"] = dict(
        no2_1e15_molec_cm2={k.strftime("%Y-%m"): round(float(v), 2) for k, v in n2m["median"].items()},
        o3_DU={k.strftime("%Y-%m"): round(float(v), 0) for k, v in om["median"].items()},
        cams_aod550={k.strftime("%Y-%m"): round(float(v), 2) for k, v in am.items()},
        cams_pm25={k.strftime("%Y-%m"): round(float(v), 1) for k, v in pmm.items()})
    dryn = n2m["median"][n2m.index.month.isin([12, 1, 2, 3, 4])].mean()
    wetn = n2m["median"][n2m.index.month.isin([6, 7, 8, 9])].mean()
    M["no2_dry_vs_wet"] = dict(DJFMA=round(float(dryn), 2), JJAS=round(float(wetn), 2), ratio=round(float(dryn / wetn), 2))
    fig, ax = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
    ax[0].bar(n2m.index, n2m["median"], width=22, color=BLUE)
    ax[0].set(ylabel="10¹⁵ molec/cm²", title="Pandora tropospheric NO₂ column (monthly median): ~2× higher in the dry season")
    ax[1].plot(om.index, om["median"], color=BLUE, marker="o", ms=5)
    ax[1].set(ylabel="Dobson units", title="Pandora total ozone column (monthly median): spring–summer maximum")
    ax[2].plot(am.index, am.values, color=ORANGE, marker="o", ms=5)
    ax[2].set(ylabel="AOD at 550 nm", title="CAMS aerosol optical depth (satellite-assimilating analysis): late dry-season haze peak, Mar–May")
    for a in ax:
        a.grid(axis="x", visible=False)
    fmt_dates(ax[2])
    fig.tight_layout()
    fig.savefig(out / "fig5_composition.png", dpi=170)
    plt.close(fig)


def fig_event(wv, E, P, d, out, M):
    t0, t1 = pd.Timestamp("2025-09-17"), pd.Timestamp("2025-10-01")
    pl = wv.pwv.copy()
    pl.index = local(pl.index)
    ph = pl.resample("1h").median()[t0:t1].dropna()
    e = E.copy()
    e.index = local(e.index)
    e = e[t0:t1]
    M["event_20250922"] = dict(
        pressure_min_hpa=float(e.surface_pressure["2025-09-21":"2025-09-24"].min()),
        pressure_before_hpa=float(e.surface_pressure["2025-09-21 00:00":"2025-09-21 12:00"].mean()),
        wind_max_kmh_hourly=float(e.wind_speed_10m["2025-09-21":"2025-09-24"].max()),
        rain_era5_mm_22nd=float(e.precipitation["2025-09-22"].sum()),
        rain_power_mm_22nd=float(P.PRECTOTCORR["2025-09-22"]),
        pwv_before_mm=float(pl["2025-09-15":"2025-09-21"].median()),
        pwv_after_mm=float(pl["2025-09-27":"2025-09-30"].median()),
        pandora_samples_22_23=int(pl["2025-09-22":"2025-09-23"].count()))
    fig = plt.figure(figsize=(12, 7))
    gs = fig.add_gridspec(3, 2, width_ratios=[1, 1.15], hspace=0.35, wspace=0.18)
    am = fig.add_subplot(gs[:, 0])
    img = mimg.imread(d / "imerg_event.png")
    co = mimg.imread(d / "coastlines.png").copy()
    co[..., :3] = 0
    co[..., 3] = np.clip(co[..., 3] * 1.0, 0, 1)
    ext = [114, 128, 10, 24]
    am.imshow(img, extent=ext)
    am.imshow(co, extent=ext)
    am.plot(LON, LAT, marker="*", ms=17, mfc="white", mec="black", mew=1.2, ls="none")
    am.annotate("MMSU Pandora", (LON, LAT), (14, -4), textcoords="offset points", fontsize=9.5, color="black",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=.85))
    am.set(xlim=ext[:2], ylim=ext[2:], xlabel="longitude (°E)", ylabel="latitude (°N)",
           title="GPM IMERG rain rate, 22 Sep 2025 18:00 local")
    am.text(0.5, -0.12, "NASA GIBS default colour ramp, qualitative: green = light, red = heaviest rain.\nWhite = no data.", transform=am.transAxes, ha="center", va="top", fontsize=8.5, color=INK2)
    am.grid(False)
    a1 = fig.add_subplot(gs[0, 1])
    ev = e.total_column_integrated_water_vapour
    a1.plot(ev.index, ev.values, color=INK2, lw=1.2, ls="--")
    a1.plot(ph.index, ph.values, color=BLUE, marker="o", ms=3.5, ls="none")
    a1.set(ylabel="water vapour (mm)", title="Column water vapour")
    a1.plot([], [], color=BLUE, marker="o", ms=4, ls="none", label="Pandora (hourly median)")
    a1.plot([], [], color=INK2, lw=1.2, ls="--", label="ERA5")
    a1.legend(loc="upper right", fontsize=8.5, ncol=2)
    a1.set_ylim(28, 84)
    a1.axvspan(pd.Timestamp("2025-09-22"), pd.Timestamp("2025-09-24"), color=GRID, alpha=.6, lw=0)
    a1.annotate("no direct sun,\nno Pandora data", (pd.Timestamp("2025-09-23 00:00"), 38), ha="center", va="center", fontsize=8.5, color=INK2)
    a2 = fig.add_subplot(gs[1, 1], sharex=a1)
    a2.bar(e.index, e.precipitation, width=1 / 24, color=ORANGE)
    a2.set(ylabel="mm / h", title="ERA5 hourly rain")
    a3 = fig.add_subplot(gs[2, 1], sharex=a1)
    a3.plot(e.index, e.surface_pressure, color=BLUE)
    a3.set(ylabel="hPa", title="Surface pressure (deep low passes ~22 Sep)")
    for a in (a1, a2, a3):
        a.grid(axis="x", visible=False)
    for a in (a1, a2):
        plt.setp(a.get_xticklabels(), visible=False)
    a3.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d %b"))
    fig.savefig(out / "fig6_event_20250922.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", default=".")
    a = ap.parse_args()
    d, out = Path(a.data), Path(a.out)
    (out / "figures").mkdir(parents=True, exist_ok=True)
    figs = out / "figures"
    wv, o3, no, P, E, C, M = load_all(d)
    M["site"] = dict(name="Pandora #219 Ilocos, MMSU", lat=LAT, lon=LON)
    M["period"] = [str(wv.index.min()), str(wv.index.max())]
    fig_validation(wv, E, figs, M)
    fig_seasonal(wv, P, E, figs, M)
    J = fig_rain_pickup(wv, P, figs, M)
    fig_diurnal(wv, E, figs, M)
    fig_composition(o3, no, C, P, figs, M)
    fig_event(wv, E, P, d, figs, M)
    json.dump(M, open(out / "metrics.json", "w"), indent=1)
    print("wrote", figs, "and metrics.json")


if __name__ == "__main__":
    main()
