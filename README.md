# MMSU Rankings Monitoring Board

A single-page monitoring dashboard for **Mariano Marcos State University**'s standing in
four international ranking systems:

| System | What it measures | Latest result on the board |
|---|---|---|
| [UI GreenMetric World University Rankings](https://greenmetric.ui.ac.id/) | Campus sustainability (6 indicators, 10,000 pts) | **#200 global** (2025), 1st among PH SUCs |
| [WURI](https://www.wuri.world/) — World's Universities with Real Impact | Innovation & real-world impact | **#89 global** (2025), Global Top 100 |
| [THE Impact Rankings](https://www.timeshighereducation.com/impactrankings) | Contributions to the UN SDGs | **601–800 bracket** (2025), PH #1 for SDG 8 (2023–2024) |
| [QS](https://www.topuniversities.com/universities/mariano-marcos-state-university) | Asia University Rankings & QS Stars rating | **1401–1500** Asia bracket (2026, new entry), **4★** QS Stars (2024) |

## Pages

- `index.html` — university-level rankings monitoring board (the table above).
- `units.html` — **Colleges & Units green scoreboard**: MMSU's 11 recognized
  academic units (CAFSD, CAS, CBEA, COE, CHS, COM, COL, CTE, GS, CIT, CASAT)
  across its 6 campuses, each scored against the six UI GreenMetric indicator
  areas with the official weighting. Includes a campus filter, composite
  ranking, unit × indicator heatmap, and a per-unit detail view against the
  university average.

  > ⚠️ The unit roster, campuses, and locations on that page are official MMSU
  > data; the per-unit indicator **scores are sample values** for demonstration.
  > Replace them in the `DATA` block of `units.html` with each unit's actual
  > self-assessment or audit results.

## Viewing

Each page is one dependency-free file — open `index.html` or `units.html` in any
browser, or serve them with GitHub Pages (Settings → Pages → deploy from branch,
root folder). Everything, including the official MMSU seal and display typeface,
is inlined as data URIs, so the pages work offline with no external requests.
Both adapt automatically to light and dark mode.

## Branding

The masthead on both pages uses MMSU's actual visual identity, sourced from
[mmsu.edu.ph](https://www.mmsu.edu.ph/):

- **Seal** — the official university seal (`/images/mmsuTransLogo.png` on the
  live site), embedded as a compressed data URI.
- **Color** — deep forest green (`#0c4b05`) and gold (`#ffb800`), sampled from
  the seal itself; this matches the green→gold gradient MMSU uses for its own
  hero headings. Chart/data colors are unchanged and still pass the
  colorblind-safety validator — brand color is used only for identity chrome
  (headings, eyebrow label, accent bar, footer mark), never for data series.
- **Type** — EB Garamond (open-source, embedded as a variable-weight woff2 data
  URI) for page headings, echoing the `font-garamond` / `font-garamond-pro`
  display treatment used on the official site; body copy stays on the existing
  system-ui sans for dashboard legibility.

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
