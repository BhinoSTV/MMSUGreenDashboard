# Weather understanding at MMSU: Pandora + satellite-based data

A reproducible analysis of how a ground-based **Pandora spectrometer** (Pandonia Global
Network instrument #219, installed at Mariano Marcos State University, Batac) and
satellite-based / satellite-assimilating products describe the local weather and
atmospheric state, Jan 2025 – Nov 2026.

```bash
pip install pandas numpy matplotlib scipy
python3 fetch_data.py --out data          # ~160 MB, kept out of git
python3 weather_understanding.py --data data --out .   # writes figures/ and metrics.json
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
Against ERA5 (4,282 hourly matches): **r = 0.978, bias −1.9 mm (−4 %), RMSE 3.1 mm**, slope 0.92.
The bias is always negative (−0.8 to −3.7 mm per month) and somewhat larger in 2026 and in wet months.
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
* `figures/fig1…fig6*.png`, `metrics.json`: outputs.

Note: PGN's legacy download tree (`data.pandonia-global-network.org`) was retired on 8 Sep 2026; this
code uses the new API (`api.pandonia-global-network.org`). Follow the PGN data-use guidelines when publishing.
