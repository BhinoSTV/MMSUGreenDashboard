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

Both pages implement the **MMSU Design System** (a Claude Design project built
from the official *MMSU Brand Standards Manual 2024* cover plate plus the live
mmsu.edu.ph site), imported via the `claude_design` MCP:

- **Seal** — the official university seal, embedded as a compressed data URI.
- **Color** — the design system's official ramp: primary green `#0B4A16`
  (`--green-700`) and accent gold `#EFA900` (`--gold-500`), used only as
  identity chrome (headings, eyebrow label, accent bar, buttons, badges,
  footer mark) — never as a gradient blend, per the source manual's flat,
  print-derived visual language (the accent bar is a hard two-tone split, not
  a blend). Neutrals follow the system's `ink`/`line`/`surface` scale, with a
  few values (e.g. the eyebrow-label gold, dark-mode green) deliberately
  darkened or brightened past the source spec where needed to clear WCAG AA
  text contrast — the manual's own tokens target a light-only print product,
  not an accessible two-theme dashboard. Chart/data colors are **untouched**
  and still pass the colorblind-safety validator; brand color never touches a
  data series.
- **Type** — the system's three-typeface stack, self-hosted as variable-weight
  woff2 data URIs: **Noto Serif** for the masthead (its stand-in for the
  manual's formal wordmark serif), **Montserrat** for section headings,
  eyebrow labels, buttons, and stat numbers (its stand-in for the manual's
  geometric bold sans), and **Work Sans** for body copy and chart labels.
- **Components** — the campus filter chips (`units.html`) follow the design
  system's Button spec (outline, filling solid green when active/pressed);
  the sample-data notice follows its Alert spec (flat gold-tinted panel, bold
  colored title, no border); the highlight chips follow its Badge "outline"
  variant (green border, transparent fill).

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
