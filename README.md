# MMSU Rankings Monitoring Board

A single-page monitoring dashboard for **Mariano Marcos State University**'s standing in
four international ranking systems:

| System | What it measures | Latest result on the board |
|---|---|---|
| [UI GreenMetric World University Rankings](https://greenmetric.ui.ac.id/) | Campus sustainability (6 indicators, 10,000 pts) | **#200 global** (2025), 1st among PH SUCs |
| [WURI](https://www.wuri.world/) — World's Universities with Real Impact | Innovation & real-world impact | **#89 global** (2025), Global Top 100 |
| [THE Impact Rankings](https://www.timeshighereducation.com/impactrankings) | Contributions to the UN SDGs | **601–800 bracket** (2025), PH #1 for SDG 8 (2023–2024) |
| [QS](https://www.topuniversities.com/universities/mariano-marcos-state-university) | Asia University Rankings & QS Stars rating | **1401–1500** Asia bracket (2026, new entry), **4★** QS Stars (2024) |

## Viewing

The whole dashboard is one dependency-free file — open `index.html` in any browser,
or serve it with GitHub Pages (Settings → Pages → deploy from branch, root folder).
It adapts automatically to light and dark mode.

## Updating the data

All figures live in the clearly-marked `DATA` block near the top of the `<script>`
section in `index.html`. When a new ranking edition is released:

1. **UI GreenMetric** — append `{ year, rank }` to `greenMetric.trend`; update
   `categoryYear`, the six `categories` scores, and `totalScore` from MMSU's
   [GreenMetric profile](https://uigreenmetric.com/university/mmsu.edu.ph).
2. **WURI** — append `{ year, rank }` to `wuri.trend` and add the new edition's
   category standings to `wuri.categories`.
3. **THE Impact** — append `{ year, lo, hi }` (the published bracket) to
   `theImpact.trend`; if THE publishes a new SDG-level score breakdown, replace
   `sdgs`, `sdgYear`, and `overallScore`.
4. **QS** — update `qs.asia` (edition + bracket) and `qs.stars`.
5. Update `asOf`, and add any new announcement links to `sources`.

Charts, KPI tiles, data tables, and deltas re-render from the data automatically.

## Data notes

- Rank charts draw the axis **inverted** (a rising line = an improving rank), since
  lower rank numbers are better.
- THE Impact results are published as brackets, so they are drawn as range bars.
- The SDG score breakdown shown is the 2022 edition — the most recent edition for
  which MMSU's per-SDG scores were published.
- Sources for every figure are linked in the dashboard footer.
