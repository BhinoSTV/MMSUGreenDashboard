# MMSU Sustainability (SDG) site: SDG 15 pilot

`index.html` is one self-contained file (open it in a browser, or host it on any static server).
Flow: **Home** (SDG tiles) → click **SDG 15** → indicator list → click **15.1** → entries.
**15.1** (14 hand-written entries) and **15.2.1 to 15.2.6** (36 entries generated from the compendium) are filled in;
the remaining indicators open with "No entries yet". Regenerate the 15.2 entries after changing the compendium:
`python3 import_entries.py && node build_site.js`.

## Design standard followed
Taken from mmsu.edu.ph's SDG pages: Figtree text and Garamond headings, dark green `#0C4B05`,
active yellow `#FACC15`, zinc-grey top bar and sidebar buttons, SDG 15 title in `#3FF500`, the
"MMSU Sustainability" and "Sustainable Development Goals" sidebars, the "ON THIS PAGE" column
and the dark-green footer. The MMSU seal, SDG wheel and SDG 15 icon come from mmsu.edu.ph.

## Adding entries
* In the browser: open an indicator, press **+ Add entry**. It is saved in that browser only;
  **Export added entries** downloads `sdg15-added-entries.json`.
* For everyone: add the entry to `src/sdg15_data.json` under `entries` > the indicator code,
  then rebuild: `NODE_PATH=<folder with react, react-dom, react-icons, sharp> node build_site.js`.

Each entry has: `years`, `sortYear`, `type`, `title`, `people`, `summary`, `sourceLabel`,
`sourceUrl`, `status` ("Verified on the source page", "Search summary only", "To verify"), and an
optional `note`.

## Notes
* 15.1 is measured by THE from Scopus data, so these entries are MMSU's research record and a
  check on author affiliations; they are not uploaded to THE. Confirm the exact 15.1 definition
  in THE's 2027 methodology.
* Top-bar, main-menu and footer links open mmsu.edu.ph. Search and the chat buttons from the
  live site are not part of the pilot.

## Hosted copy

`artifact.html` is the same page as a fragment for the claude.ai artifact host (hash routes `#sdg-15`, `#ind-15-1`; the entry export is a copyable text box because the host blocks downloads). Rebuild both files with `node build_site.js`. `index.html` is the standalone version for any static host, such as GitHub Pages or MMSU web hosting.

## One-page version

`all.html` (standalone) and `artifact_all.html` (hosted) show the same entries without the indicator-by-indicator drill-down: the SDG 15 tile opens one page with every entry in full, grouped by indicator, with search, filters and jump links. Built by the same `node build_site.js`; the page switches on `window.SDG_ALL`.
