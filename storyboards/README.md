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
