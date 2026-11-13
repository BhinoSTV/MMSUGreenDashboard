# Weather understanding at MMSU: Pandora + satellite-based data

A reproducible analysis of how a ground-based **Pandora spectrometer** (Pandonia Global
Network instrument #219, installed at Mariano Marcos State University, Batac) and
satellite-based / satellite-assimilating products describe the local weather and
atmospheric state, Jan 2025 – Nov 2026.

```bash
pip install pandas numpy matplotlib scipy
python3 fetch_data.py --out data          # ~160 MB, kept out of git
python3 weather_understanding.py --data data --out .   # writes figures/ and metrics.json
python3 agreement_stats.py --data data --out .         # writes tables/, agreement_stats.json, fig7
python3 calibrate_era5.py --data data --out .          # writes calibration.json, calibrated series, fig8
```

## What Pandora can and cannot tell you about weather

Pandora is a **direct-sun / sky-scan UV–VIS spectrometer**. It does not measure temperature,
rain, wind or clouds. It measures **column amounts** of gases, and one of them,
**total column water vapour** (the quantity meteorologists call precipitable water, PWV), is a
first-order weather variable: it fuels convection, marks monsoon phases, and rises ahead of and
inside tropical systems. The other products (NO₂, O₃) describe air composition and
transport, and are weather-modulated (washout, advection, photochemistry). The analysis therefore
treats Pandora as the **column-moisture and air-quality anchor**, and uses satellite-based products
for everything Pandora cannot see (rain, cloud, radiation, aerosol, synoptic structure).

| Role | Product | Nature |
|---|---|---|
| Anchor | Pandora #219 L2 `rwvt1` (H₂O), `rnvh3` (NO₂, trop.), `rout2` (O₃) | ground-based remote sensing, 421k water-vapour samples |
| Column-moisture reference | ERA5 TCWV (hourly) | reanalysis (assimilates satellite radiances) |
| Rain, clearness | NASA POWER: MERRA-2 rain bias-corrected with satellite-gauge precipitation; CERES-based all-sky surface shortwave | model + satellite blend |
| Aerosol | CAMS AOD 550 nm | analysis assimilating satellite AOD (MODIS and others) |
| Synoptic rain structure | GPM IMERG rain rate via NASA GIBS | satellite microwave/IR, direct observation |

Himawari-9 AHI (10-min geostationary IR/visible) is the right tool for live cloud monitoring,
but GIBS keeps only ~1 month of it, so it cannot support a historical case; IMERG was used instead.

## Findings

### 1. Pandora water vapour is physically credible and tracks independent products (Fig 1)
Against ERA5 (4,282 hourly matches, 524 days): **r = 0.979, bias −2.1 mm (−4.6 %), RMSE 3.1 mm**,
OLS slope 0.92 (full statistics in the next section). The bias is always negative (−0.9 to −4.1 mm per month)
and somewhat larger in 2026 and in wet months.
It is a stable dry offset rather than noise; correct or flag it before using absolute values.

### 2. It resolves the monsoon cycle (Fig 2)
Monthly median water vapour: **34 mm (Jan–Apr) → 55 mm (Jun–Sep), a 20 mm swing**, matching the
rainfall (NASA POWER) and clearness cycles. The 2026 onset is visible as a jump from 30 mm (Apr) to
46 mm (May), versus 40 → 50 mm in 2025.

### 3. Water vapour is a strong rain-probability indicator (Fig 3)
Spearman ρ = 0.79 with same-day rain (481 days). Share of days with ≥ 10 mm rain: **≈ 0 % below
45 mm, 6 % at 45–50, 15 % at 50–55, 39 % at 55–60, 100 % above 60 mm** (only 14 days in the top bin).
This is the tropical "precipitation pickup" relationship (rain onset above a moisture threshold).
Direct-sun yield, normalised for scheduling, is also a usable sunshine proxy (ρ = 0.52 with CERES
clearness, −0.47 with cloud amount).

### 4. Diurnal cycle (Fig 4)
Water vapour rises from the morning minimum to an early-afternoon maximum (~14:00 local). ERA5, as an
independent check, shows the same shape (wet season −2.4 → +2.2 mm); Pandora's amplitude is damped
(−1.5 → +0.9 mm), consistent with clear-sky sampling. Trust the timing, not the amplitude.

### 5. Air composition seasonality (Fig 5)
* Tropospheric NO₂ column: **≈ 0.9 ×10¹⁵ molec/cm² in Dec–Apr vs 0.5 in Jun–Sep (1.8×)**.
* Ozone column: 236–290 DU, minimum Dec–Feb, maximum Apr–Jul, a typical subtropical cycle.
* CAMS AOD peaks in Mar–May (0.29 in Apr 2025, 0.40 in Apr 2026) and bottoms out in Dec.

*Hypothesis, not tested here:* the dry-season NO₂ and aerosol maximum reflects reduced washout plus
continental / biomass-burning outflow under the NE monsoon, while the wet season brings clean maritime air.
Back-trajectories and fire counts (e.g. VIIRS) would be needed to test this.

### 6. Case study: heavy-rain event of 22 Sep 2025 (Fig 6)
ERA5 shows surface pressure falling from ~1006 to 988.6 hPa, hourly wind up to 66 km/h and 169 mm of
rain on the day (NASA POWER independently: 155 mm). The IMERG frame puts the rain core over the site.
**Pandora recorded nothing on 22–23 Sep** (no direct sun). Before the event it saw ~56 mm; by 27–30 Sep
it had dropped to ~42 mm. Across the 15 days with ≥ 50 mm rain there is **no useful moistening lead signal**
(`event_composite` in `metrics.json`: anomaly ≈ −1 mm at days −3/−2, +2.8 mm only the day after).

### Agreement statistics: Pandora vs ERA5 (Fig 7, `agreement_stats.py`)
Pandora = test, ERA5 = reference, d = Pandora − ERA5, units mm. Hourly Pandora medians (≥ 5 samples)
are matched to ERA5 at the window centre (hh:30). 95 % CIs come from a **day-block bootstrap** (2,000
resamples), because hourly errors are autocorrelated.

| Metric | Hourly (n = 4,282) | Daily mean (n = 486) |
|---|---|---|
| Bias (MBE) | **−2.10** [−2.24, −1.95] (−4.6 %) | −2.09 [−2.24, −1.94] |
| MAE / median AE | 2.47 [2.35, 2.58] / 2.02 | 2.23 / 1.91 |
| RMSE (relative) | **3.14** [3.00, 3.27] (6.9 %) | 2.69 (5.8 %) |
| Unbiased RMSE (SD of d) | 2.34 | 1.69 |
| 90th-percentile abs. error | 5.1 | 4.3 |
| Pearson r / R² / Spearman ρ | 0.979 [0.976, 0.982] / 0.959 / 0.978 | 0.990 / 0.980 / 0.989 |
| OLS slope, intercept | 0.921 [0.911, 0.932], +1.50 | 0.936, +0.87 |
| Orthogonal (Deming) slope, intercept | 0.939, +0.67 | 0.945, +0.45 |
| Lin's CCC / Willmott d / KGE | 0.960 / 0.980 / 0.922 | 0.971 / 0.985 / 0.929 |
| Bland–Altman limits (±1.96 SD) | −6.7 to +2.5 | −5.4 to +1.2 |
| Within ±3 mm / ±5 mm / ±10 % | 68 % / 89 % / 88 % | 72 % / 95 % / 93 % |

Reading the numbers:
* **Precision is excellent, accuracy shows a stable offset.** Correlation is 0.98 and unbiased RMSE is
  2.3 mm, but the bias (−4.6 %) is statistically distinct from zero. The offset is partly **proportional**:
  the Bland–Altman slope is −0.06 mm per mm (p < 0.001) and the regression slope is 0.92–0.94.
* **Sensitivity to collocation:** matching ERA5 at the top of the hour instead of the window centre
  gives bias −1.9 mm and RMSE 3.09 mm (see `tables/agreement_overall.csv`, column `hourlabel`). Report the
  collocation rule with the statistics.
* **By regime** (`tables/agreement_strata.csv`): bias −1.5 mm (dry) vs −2.7 mm (wet), but relative RMSE
  stays at 6–8 % everywhere, so the error is roughly multiplicative. Afternoon (13–17 h) is worst
  (bias −2.6 mm, RMSE 3.7 mm = 8.0 %, only 83 % within ±10 %), consistent with ERA5 having a larger diurnal
  amplitude than Pandora's clear-sky-sampled data. 2026 is somewhat worse than 2025 (RMSE 7.9 % vs 6.2 %),
  but the two years have different seasonal mixes, so do not read it as drift without a seasonally matched test.
* **Caution for the narrow moisture bin (40–50 mm):** r drops to 0.78 and the orthogonal slope to 1.37 purely
  from range restriction, not because the instrument misbehaves there. Do not interpret slopes within narrow
  strata.
* These are *agreement* statistics against a model product, not Pandora accuracy.

### ERA5 calibrated to Pandora (Fig 8, `calibrate_era5.py`)
Pandora is treated as the **reference** and ERA5 TCWV is bias-corrected to it. Eight candidate models were
fitted on the hourly pairs and scored **only on held-out data** (leave-one-month-out CV, plus train-2025 →
test-2026 and dry ↔ wet season transfer). The simplest model within 2 % of the best CV RMSE is selected.

| Model (params) | Held-out RMSE, mm [95 % CI] | Bias, mm | 2025 → 2026 RMSE | dry → wet | wet → dry |
|---|---|---|---|---|---|
| Raw ERA5 (0) | 3.14 [3.01, 3.28] | +2.10 | 3.30 | 3.62 | 2.64 |
| Offset (1) | 2.36 | 0.00 | 2.48 | 2.67 | 2.48 |
| **Scale (1), selected** | **2.20 [2.11, 2.28]** | −0.09 | 2.31 | 2.36 | 2.10 |
| Scale by season (2) | 2.20 | −0.06 | 2.31 | 2.36 | 2.10 |
| Scale by hour (3) | 2.17 | −0.09 | 2.31 | 2.32 | 2.10 |
| Scale by season × hour (6) | 2.16 | −0.06 | 2.30 | 2.36 | 2.10 |
| Linear (2) | 2.17 | 0.00 | 2.31 | 2.29 | 2.05 |
| Quantile mapping (99) | 2.19 | 0.00 | 2.32 | 2.46 | 2.44 |

**Calibrated ERA5 = 0.952 × ERA5** (95 % CI 0.949–0.955, day-block bootstrap). Held-out RMSE falls from 3.14 to
2.20 mm (−30 %) and bias from +2.10 to −0.09 mm. Richer models are statistically indistinguishable from the
single factor, so the one-parameter form is retained; it also transfers best across seasons and years.

What remains after correction:
* **A diurnal residual.** The corrected bias is about −0.6 mm at 10:00 and +1.0 mm at 16:00 local. ERA5's
  afternoon moistening is stronger than what Pandora sees; one factor cannot remove a shape difference.
  Scale-by-hour improves RMSE only marginally (2.17 vs 2.20, inside the CI). For applications sensitive to
  the diurnal cycle, treat afternoon corrected values as ≈ 1 mm high.
* **Residual regime bias is small** (−0.4 to +0.2 mm across moisture classes, vs +1.5 to +2.7 mm raw).
* **A floor of ≈ 2.2 mm** that no calibration can remove: Pandora noise, ERA5 error and point-vs-grid
  representativeness.

Outputs: `calibration.json` (model, coefficient and CI, full CV table), `tables/era5_calibration_cv.csv`,
`tables/era5_tcwv_calibrated.csv` (hourly, 2025-01 → 2026-11; flag `in_calibration_domain`).

**How to use and not use this.**
* Report the CV numbers above, never in-sample statistics of the calibrated series; evaluating it against the
  same Pandora pairs it was fitted on would overstate skill.
* The calibration holds for **local hours 07–16 only** (where Pandora data exist). Night-time and
  early/late hours (about 58 % of rows) are extrapolations and are flagged `in_calibration_domain = False`.
* The correction inherits Pandora's own status: **not-assured**, with a possible bias of its own. It makes
  ERA5 consistent with this instrument, which is only as good as the instrument. An independent reference
  (GNSS, radiosonde) is needed to show the instrument is the better anchor.
* Pandora samples clear-sun conditions only, so the factor is calibrated for those and applied to cloudy and
  rainy hours by extrapolation. The sensitivity of the factor to sky condition could not be tested directly.

## Limitations that matter

1. **All Pandora data from this instrument are "not-assured"** (QA flags 10/11/12; none are 0–2).
   PGN lists the instrument as "operational with issue", and file headers read *"OOB session based on lab
   session 101"*. Treat results as provisional and confirm calibration status with the site PI listed in the
   PGN metadata. Agreement with ERA5 is evidence of usefulness, not a substitute for assured status.
2. **Direct-sun sampling bias.** No data in heavy rain or thick cloud, so the instrument systematically
   under-samples the wettest states (only 3 of the 15 extreme-rain days have any Pandora data on the day itself). Rain statistics describe moisture
   conditions on days with at least partial sun.
3. **Pandora's own AOD estimate is unusable** (negative median), so CAMS AOD is used instead; CAMS is a
   model analysis, not a measurement at the site.
4. **NO₂/O₃ are not independently validated here**, and NO₂ uses only ~27k samples; no satellite
   (TROPOMI) comparison was made because those products need credentials not available in this session.
5. **Short record** (~22 months, 2 monsoons, June 2026 missing): seasonal statements are indicative, not climatology.
6. Screening: 5–90 mm range, SZA < 70°, QA ≤ 11, relative uncertainty < 20 % keep 336,626 of 421,079 samples.
   ERA5 and POWER grids are 0.25–0.5°; the site (34 m a.s.l.) is a point inside them.
7. Event naming: the 22 Sep 2025 system is not identified by name here; check PAGASA bulletins.

## Files

* `fetch_data.py`: downloads all inputs (PGN API, POWER, ERA5, CAMS, GIBS).
* `pgn_load.py`: parser for PGN L2 bulk files (BlickP p1-8 column layout).
* `weather_understanding.py`: screening, statistics, figures, `metrics.json`.
* `agreement_stats.py`: full Pandora-vs-ERA5 agreement statistics with day-block bootstrap CIs, strata, `fig7`.
* `calibrate_era5.py`: calibrates ERA5 TCWV to Pandora with cross-validated model selection, `fig8`.
* `figures/fig1…fig8*.png`, `metrics.json`, `agreement_stats.json`, `calibration.json`, `tables/*.csv`: outputs.

Note: PGN's legacy download tree (`data.pandonia-global-network.org`) was retired on 8 Sep 2026; this
code uses the new API (`api.pandonia-global-network.org`). Follow the PGN data-use guidelines when publishing.
