# SDG 15 storyboards (THE Impact Rankings 2027)

One storyboard PDF per THE SDG 15 indicator in `sdg15/`, built from the
*SDG 15 Life on Land Evidence Compendium 2025* (final consolidated edition, v4, 4 Nov 2026).

Each PDF (16:9) contains:

1. **Cover frame**: the THE question, MMSU's commitment, storyline, filmstrip of frames, key figures, and the
   compendium status (2025 evidence / Continuing only / Draft / No entry yet).
2. **One frame per evidence story**: photo or document, three narrative beats, key figures, the "lens" the story takes
   for that indicator, and source. Green frames are 2025 evidence; blue frames are continuing implementation;
   dashed amber frames mark evidence still to be produced.
3. **Submission panel**: recommended answer, a draft THE comment (checked to be 1,000 characters or fewer),
   policy created/reviewed years where THE asks for them, items to confirm before submitting, and all evidence links.

| File | Status in v4 |
|---|---|
| `SDG-15.2.1` Events about sustainable use of land | 2025 evidence |
| `SDG-15.2.2` Sustainably farmed food on campus (policy) | Draft |
| `SDG-15.2.3` Maintain and extend biodiversity | 2025 evidence |
| `SDG-15.2.4` Educational programmes on ecosystems | 2025 evidence |
| `SDG-15.2.5` Land management for agriculture (outreach) | 2025 evidence |
| `SDG-15.2.6` Land management for tourism (outreach) | Draft |
| `SDG-15.3.1` Conservation, restoration, sustainable use (policy) | Continuing only |
| `SDG-15.3.2` IUCN and national-list species (policy) | Draft |
| `SDG-15.3.3` Local biodiversity in planning | Continuing only |
| `SDG-15.3.4` Alien species (policy) | No entry yet |
| `SDG-15.3.5` Collaboration for shared land ecosystems | 2025 evidence |
| `SDG-15.4.1` Water discharge standards | 2025 evidence |
| `SDG-15.4.2` Plastic waste reduction (policy) | 2025 evidence |
| `SDG-15.4.3` Hazardous waste disposal (policy) | Continuing only |

## Regenerating

```bash
cd storyboards/src
python3 -I extract.py <compendium.docx> .          # compendium -> data.json + assets/ (photos)
python3 -I build.py /tmp/sb-html                    # data.json + content.py -> one HTML deck per indicator
NODE_PATH=$(npm root -g) node render.js /tmp/sb-html ../sdg15   # Chromium -> PDF (also reports overflow)
```

`content.py` holds the hand-written beats, key figures, per-indicator "lens" lines, draft comments and
to-confirm lists. Captions, photos, tags and source lines come straight from the compendium.
Lines marked *Proposed* or *Illustrative* (e.g. the 15.3.4 frames) are suggestions, not compendium content.

## Story edition (`sdg15-stories/`)

13 further PDFs tell the same activities as a plain narrative of MMSU's work on land: chapters by theme,
no indicator numbers, status labels, draft comments or to-do lists. Each has a cover, one frame per activity
(2025 or ongoing programme), and a closing page with what the activities add up to and the sources.
Chapter 15.3.4 (alien species) has no activities yet, so it has no story chapter.

```bash
python3 -I build_story.py /tmp/story-html
NODE_PATH=$(npm root -g) node render.js /tmp/story-html ../sdg15-stories
```

## Evidence-report edition (`sdg15-evidence-reports/`)

14 Word reports (+ PDF copies), one per indicator, following the *MMSU SDG Evidence Compendium TEMPLATE*:
cover and team block, 1 Sites and platforms explored, Not yet explored, 2 Indicators to report, 3 Optional peers
(only where the compendium links a peer to that indicator), 4 Evidence by indicator (submission pick, items with photos,
narrative and sources; policy record tables for policies), 5 Before submission checklist and open items.
Built on the template file itself, so its styles and footer carry over. Orange brackets mark facts still to add.

```bash
cd storyboards/src
python3 -I build_report.py <template.docx> ../sdg15-evidence-reports   # then: soffice --headless --convert-to pdf *.docx
```

## Article edition (`sdg15-articles/`)

14 short Word articles (+ PDF) in the template look, one per indicator: cover, the question, 1 Introduction,
2 Body (itemised, with photos and numbered resource references), 3 Conclusion, 4 Resources. No sites-searched,
peer or checklist pages, and no placeholders. 15.3.4 has no items yet and says so.

```bash
cd storyboards/src && python3 -I build_article.py <template.docx> ../sdg15-articles   # then convert to PDF with soffice
```
