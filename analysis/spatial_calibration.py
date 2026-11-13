#!/usr/bin/env python3
"""Can the Pandora-based ERA5 calibration be used for SPATIAL variability?

    python3 spatial_calibration.py --data data --out .

A scale factor fitted at one point only rescales ERA5's spatial pattern; it cannot repair it. Two
things must therefore be shown before a calibrated ERA5 is used across space:
  A. TRANSFER: a factor fitted at some sites works at a site it has never seen
     (Ilocos factor -> other sites; leave-one-site-out pooled factor).
  B. GRADIENTS: ERA5 reproduces the DIFFERENCES between sites that Pandora measures
     (scale-free test of spatial variability), before and after calibration with an *external*
     factor (fitted only on sites outside the pair).

Sites: the four Philippine PGN Pandoras (Ilocos 18.1N, Quezon City 14.6N, Palawan 9.8N, Cebu 10.4N).
Pandora = reference; ERA5 = product being calibrated. All PGN data here are 'not-assured'.
Outputs: spatial_calibration.json, tables/spatial_*.csv, figures/fig9_spatial_transfer.png
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

import agreement_stats as A
import fetch_data as F
import pgn_load as L
import weather_understanding as W

SITES = list(F.NETWORK)          # Ilocos, QuezonCity, Palawan, Cebu
PRETTY = {"Ilocos": "Ilocos (18.1°N)", "QuezonCity": "Quezon City (14.6°N)", "Palawan": "Palawan (9.8°N)", "Cebu": "Cebu (10.4°N)"}
PGN_FILE = {"Ilocos": "pgn_rwvt1.txt", **{s: f"pgn_rwvt1_{s}.txt" for s in SITES if s != "Ilocos"}}


def load_site(d, name):
    w = L.load_l2(d / PGN_FILE[name], "rwvt1")
    w["pwv"] = w.wv_col * W.MW_H2O
    ok = (w.pwv.between(5, 90) & (w.qa <= 11) & (w.sza < 70) & (w.wv_unc > 0) & (w.wv_unc < w.wv_col * 0.2))
    w = w[ok].copy()
    e = pd.DataFrame(json.load(open(d / f"era5_{name}.json"))["hourly"])
    e.index = pd.to_datetime(e.pop("time"), utc=True)
    j = A.collocate(w, e)
    j["site"] = name
    return j


def fit_scale(x, p):
    return float((x * p).sum() / (x * x).sum())


def boot_scale(j, n=1000, seed=3):
    x, p = j.e_mid.values, j.p.values
    codes, u = pd.factorize(j.day.values)
    idx = [np.flatnonzero(codes == k) for k in range(len(u))]
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        sel = np.concatenate([idx[i] for i in rng.integers(0, len(idx), len(idx))])
        out.append(fit_scale(x[sel], p[sel]))
    return [float(np.quantile(out, .025)), float(np.quantile(out, .975))]


def err(obs, pred):
    d = pred - obs
    return dict(bias=float(d.mean()), rmse=float(np.sqrt((d ** 2).mean())), mae=float(np.abs(d).mean()),
                rmse_pct=float(100 * np.sqrt((d ** 2).mean()) / obs.mean()), r=float(np.corrcoef(obs, pred)[0, 1]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", default=".")
    a = ap.parse_args()
    d, root = Path(a.data), Path(a.out)
    (root / "tables").mkdir(exist_ok=True, parents=True)
    (root / "figures").mkdir(exist_ok=True, parents=True)

    J = {s: load_site(d, s) for s in SITES}
    R = {"sites": {}}

    # ---------------- per-site agreement and factor
    rows = []
    for s, j in J.items():
        f = fit_scale(j.e_mid.values, j.p.values)
        wet = j.month.isin([5, 6, 7, 8, 9, 10])
        e0 = err(j.p.values, j.e_mid.values)
        rows.append(dict(site=s, n_hours=len(j), n_days=int(j.day.nunique()), mean_pandora=j.p.mean(), mean_era5=j.e_mid.mean(),
                         era5_bias=e0["bias"], era5_rmse=e0["rmse"], era5_rmse_pct=e0["rmse_pct"], r=e0["r"],
                         factor=f, factor_lo=boot_scale(j)[0], factor_hi=boot_scale(j)[1],
                         factor_dry=fit_scale(j[~wet].e_mid.values, j[~wet].p.values),
                         factor_wet=fit_scale(j[wet].e_mid.values, j[wet].p.values)))
    S = pd.DataFrame(rows)
    S.round(4).to_csv(root / "tables" / "spatial_site_factors.csv", index=False)
    R["sites"] = S.round(4).to_dict(orient="records")

    # ---------------- A. transfer of the factor to unseen sites
    ilo_f = float(S.set_index("site").loc["Ilocos", "factor"])
    rows = []
    for t in SITES:
        jt = J[t]
        x, p = jt.e_mid.values, jt.p.values
        others = pd.concat([J[s] for s in SITES if s != t])
        pooled = fit_scale(others.e_mid.values, others.p.values)
        own = fit_scale(x, p)
        r_raw, r_own, r_pool = err(p, x), err(p, x * own), err(p, x * pooled)
        row = dict(target=t, n=len(jt), raw_rmse=r_raw["rmse"], raw_bias=r_raw["bias"], raw_rmse_pct=r_raw["rmse_pct"],
                   own_factor=own, own_rmse=r_own["rmse"],
                   loso_factor=pooled, loso_rmse=r_pool["rmse"], loso_bias=r_pool["bias"], loso_rmse_pct=r_pool["rmse_pct"])
        if t != "Ilocos":
            r_ilo = err(p, x * ilo_f)
            row.update(ilocos_factor_rmse=r_ilo["rmse"], ilocos_factor_bias=r_ilo["bias"], ilocos_factor_rmse_pct=r_ilo["rmse_pct"])
        rows.append(row)
    Tr = pd.DataFrame(rows)
    Tr.round(3).to_csv(root / "tables" / "spatial_transfer.csv", index=False)
    R["transfer"] = Tr.round(3).to_dict(orient="records")
    gain_loss = ((Tr.loso_rmse - Tr.own_rmse) / Tr.own_rmse * 100)
    R["uniform_factor_justified"] = bool((Tr.loso_rmse <= Tr.own_rmse * 1.10).all())
    R["loso_vs_own_rmse_excess_pct"] = {t: round(float(v), 1) for t, v in zip(Tr.target, gain_loss)}
    R["pooled_all_sites_factor"] = fit_scale(pd.concat(J.values()).e_mid.values, pd.concat(J.values()).p.values)

    # ---------------- A2. is the odd site (Quezon City) a sampling artefact? factor by hour/cloud/half-year
    diag = []
    for s_, j in J.items():
        jj = j.copy()
        jj["half"] = jj.year.astype(str) + "H" + ((jj.month > 6) + 1).astype(str)
        jj["hwin"] = pd.cut(jj.hour, [6, 10, 13, 17], right=False).astype(str)
        jj["cwin"] = pd.cut(jj.cloud, [-1, 30, 70, 101]).astype(str)
        for kind in ("hwin", "cwin", "half"):
            for k, g in jj.groupby(kind):
                if len(g) >= 150:
                    diag.append(dict(site=s_, split=kind, group=k, n=len(g), factor=fit_scale(g.e_mid.values, g.p.values)))
    pd.DataFrame(diag).round(4).to_csv(root / "tables" / "spatial_diagnostics.csv", index=False)
    m_ = J["QuezonCity"][["p", "e_mid"]].join(J["Ilocos"][["p", "e_mid"]], how="inner", lsuffix="_q", rsuffix="_i")
    R["same_hours_QC_vs_Ilocos"] = dict(n=int(len(m_)), era5_minus_pandora_QC=float((m_.e_mid_q - m_.p_q).mean()),
                                        era5_minus_pandora_Ilocos=float((m_.e_mid_i - m_.p_i).mean()))

    # ---------------- A3. the three mutually consistent sites as a group (leave-one-site-out inside the group)
    grp = ["Ilocos", "Palawan", "Cebu"]
    gp = pd.concat([J[s_] for s_ in grp])
    R["group3_factor"] = fit_scale(gp.e_mid.values, gp.p.values)
    rows3 = []
    for t in grp:
        oth = pd.concat([J[s_] for s_ in grp if s_ != t])
        ft = fit_scale(oth.e_mid.values, oth.p.values)
        e_raw = err(J[t].p.values, J[t].e_mid.values)
        e_cal = err(J[t].p.values, J[t].e_mid.values * ft)
        rows3.append(dict(target=t, factor_from_other_two=ft, raw_rmse=e_raw["rmse"], cal_rmse=e_cal["rmse"],
                          raw_bias=e_raw["bias"], cal_bias=e_cal["bias"], cal_rmse_pct=e_cal["rmse_pct"]))
    pd.DataFrame(rows3).round(3).to_csv(root / "tables" / "spatial_group3_loso.csv", index=False)
    R["group3_loso"] = pd.DataFrame(rows3).round(3).to_dict(orient="records")

    # ---------------- B. gradients: does ERA5 reproduce between-site differences?
    pairs = [("Ilocos", "QuezonCity"), ("Ilocos", "Palawan"), ("QuezonCity", "Palawan")]
    rows, store = [], {}
    for a_, b_ in pairs:
        m = J[a_][["p", "e_mid", "month"]].join(J[b_][["p", "e_mid"]], how="inner", lsuffix="_a", rsuffix="_b").dropna()
        ext = pd.concat([J[s] for s in SITES if s not in (a_, b_)])
        fext = fit_scale(ext.e_mid.values, ext.p.values)       # external factor: sites outside the pair
        dP = (m.p_a - m.p_b).values
        dE = (m.e_mid_a - m.e_mid_b).values
        for label, mask in (("all", np.ones(len(m), bool)), ("dry", ~m.month.isin([5, 6, 7, 8, 9, 10]).values),
                            ("wet", m.month.isin([5, 6, 7, 8, 9, 10]).values)):
            if mask.sum() < 100:
                continue
            e_raw, e_cal = err(dP[mask], dE[mask]), err(dP[mask], fext * dE[mask])
            sl = stats.linregress(dE[mask], dP[mask])
            rows.append(dict(pair=f"{a_} − {b_}", season=label, n=int(mask.sum()), mean_diff_pandora=dP[mask].mean(),
                             mean_diff_era5=dE[mask].mean(), mean_diff_era5_cal=fext * dE[mask].mean(),
                             raw_bias=e_raw["bias"], raw_rmse=e_raw["rmse"], cal_bias=e_cal["bias"], cal_rmse=e_cal["rmse"],
                             r=e_raw["r"], slope_pandora_on_era5=sl.slope, external_factor=fext, sd_pandora=dP[mask].std()))
        store[(a_, b_)] = (dE, dP, fext)
    G = pd.DataFrame(rows)
    G.round(3).to_csv(root / "tables" / "spatial_gradients.csv", index=False)
    R["gradients"] = G.round(3).to_dict(orient="records")
    json.dump(R, open(root / "spatial_calibration.json", "w"), indent=1, default=float)

    figure(S, Tr, store, root / "figures" / "fig9_spatial_transfer.png")
    pd.set_option("display.width", 250, "display.max_columns", 30)
    print(S.round(3).to_string(index=False)); print(); print(Tr.round(3).to_string(index=False)); print()
    print(G.round(3).to_string(index=False)); print(pd.DataFrame(rows3).round(3).to_string(index=False)); print("group3 factor", round(R["group3_factor"],4))
    print("uniform factor justified:", R["uniform_factor_justified"], R["loso_vs_own_rmse_excess_pct"])


def figure(S, Tr, store, path):
    fig, ax = plt.subplots(2, 2, figsize=(12, 8.6))
    a = ax[0, 0]
    y = np.arange(len(S))[::-1]
    a.errorbar(S.factor, y, xerr=[S.factor - S.factor_lo, S.factor_hi - S.factor], fmt="o", color=W.BLUE, ms=8, ecolor=W.INK2, capsize=3)
    a.axvline(1, color=W.INK2, lw=1, ls="--")
    a.plot(S.factor_dry, y + .17, "s", color=W.ORANGE, ms=5, label="dry season")
    a.plot(S.factor_wet, y - .17, "D", color=W.AQUA, ms=5, label="wet season")
    a.set_yticks(y, [PRETTY[s] for s in S.site], fontsize=9)
    a.set(xlabel="best-fit factor (Pandora ≈ factor × ERA5)", title="(a) Site factors (blue = all data, 95 % CI)", xlim=(0.944, 1.003))
    a.legend(fontsize=8.5, loc="upper right")
    a.grid(axis="y", visible=False)

    b = ax[0, 1]
    x = np.arange(len(Tr))
    w = .2
    b.bar(x - 1.5 * w, Tr.raw_rmse, w, color=W.INK2, label="raw ERA5")
    ilo = Tr.get("ilocos_factor_rmse")
    b.bar(x - .5 * w, ilo.fillna(0), w, color=W.AQUA, label="Ilocos factor")
    b.bar(x + .5 * w, Tr.loso_rmse, w, color=W.BLUE, label="leave-one-site-out factor")
    b.bar(x + 1.5 * w, Tr.own_rmse, w, color=W.ORANGE, label="own-site factor (best case)")
    b.set_xticks(x, [PRETTY[t].split(" (")[0] for t in Tr.target])
    b.set(ylabel="RMSE vs Pandora (mm)", title="(b) Does the factor transfer to a site it has not seen?")
    b.set_ylim(0, 4.6)
    b.legend(fontsize=8, loc="upper center", ncol=2)
    b.grid(axis="x", visible=False)

    for k, ((a_, b_), (dE, dP, f)) in enumerate(list(store.items())[:2]):
        c = ax[1, k]
        c.hexbin(dE, dP, gridsize=34, cmap=W.SEQ, mincnt=1, linewidths=.2, edgecolors=W.SURF)
        lim = np.array([min(dE.min(), dP.min()), max(dE.max(), dP.max())])
        c.plot(lim, lim, color=W.INK2, ls="--", lw=1)
        sl = stats.linregress(dE, dP)
        c.plot(lim, sl.slope * lim + sl.intercept, color=W.ORANGE, lw=1.6)
        c.text(.04, .96, f"n = {len(dE):,} hours\nr = {np.corrcoef(dE, dP)[0, 1]:.2f}, slope = {sl.slope:.2f}\n"
                         f"mean ΔERA5 = {dE.mean():+.1f} mm\nmean ΔPandora = {dP.mean():+.1f} mm", transform=c.transAxes, va="top", fontsize=9)
        c.set(xlabel=f"ERA5 difference (mm)", ylabel="Pandora difference (mm)", title=f"({'cd'[k]}) {a_} − {b_}")
    fig.tight_layout()
    fig.savefig(path, dpi=170)
    plt.close(fig)


if __name__ == "__main__":
    main()
