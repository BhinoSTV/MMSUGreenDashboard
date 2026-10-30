# SDG 15 evidence documents — what to finish before upload

Documents: `pdf/` (one PDF per THE indicator, plus `SDG15_Evidence_Compendium_2025.pdf`) and the
Word version `MMSU_SDG15_Life_on_Land_Evidence_2025.docx`.
Rebuild after any change: `python3 build.py && node build_docx.js` (or `python3 build.py --no-urls`
for upload PDFs).

## 0. Scope

Each indicator document lists the **2025 evidence first**, then a **Continuing implementation** section
with policies and programmes that began earlier and are still in place (land use policy and Sirmata 2040,
2021; Integrated Pollution and Waste Management Program, revised 2020; No Bottled Water memoranda, 2022
and 2023; the Kalbario-Patapat TWG appointment, 2023; the mangrove NbS project, 2024–2026; the graduation
tree planting, 2024–2026; the Dingras bambusetum, Sep 2026). THE accepts policies already in place; a policy
created or reviewed inside its window earns one more point, so each older policy still needs a 2025 review
or a confirmed date inside the window.

Peer evidence supports this approach: Visayas State University (91st of 658 in SDG 15, 2026) mixes 2025
items with older ones (2013 and 2022 memoranda, 2019 and 2023 events) in its evidence files.
Confirm the window with THE before upload.

## 1. Photos and document images

All photo frames are filled (13 October 2026). Photos for the 2025 MMSU events were captured
from the original MMSU news articles (MMSU STRATCOM / MMSU photos); the Pasuquin item uses a
capture of The Manila Times report (its photo belongs to TMP Foundation, so replace it with an
MMSU photo if one exists). Policy sections show page images of MMSU's own documents: the
Sirmata 2040 land use, zoning and water policies, the revised IPWMP, the 2022 and 2023
No Bottled Water memoranda, the groundwater quality report and DENR-PENRO Special Order
No. 2023-024. Replace any image with a better original by saving it in `assets/` under the
same filename and rebuilding.

## 2. Facts to confirm (affect points)

- [ ] **Free access** for the 2025 mangrove seminar, alukon training and Pinili bamboo training.
  THE gives full credit for free programmes and 0.25 for charged ones (15.2.4, 15.2.5). No article
  states it. If free, add one sentence such as "The training was offered free of charge."
- [ ] **Pasuquin agreement:** exact signing date and a copy of the signed tripartite MOA. The
  documents say "late 2025" because the news reports (4 and 10 Dec 2025) give no event date.
- [ ] **MMSU–DENR Region 1 MOU (Oct 2024)** and the ILAARRDEC dialogue date. Both come from
  MMSU's 2025 report; no independent record was found. The 15.2.3 text says the dialogue was in
  2025 and does not give the day.
- [ ] **Biodiversity Day photo contest:** add the official announcement or results post URL, and
  the number of entries if known.
- [ ] **Pinili training dates** (the article gives none) and the **number of participants** at the
  mangrove seminar.
- [ ] **Approval pages:** attach the Board of Regents resolution or approval page for Sirmata 2040
  (land use, zoning and water policies) and for the revised IPWMP, so 15.3.1, 15.3.3, 15.4.2 and
  15.4.3 show an approval date within 2020–2025. The documents quoted are MMSU's published versions.
- [ ] **School-on-the-Air:** free enrolment, number of completers, and the lesson list.
- [ ] **Attendance sheets and programmes** for each 2025 event, to keep on file.
- [ ] **Policies still in force:** confirm that the land use policy, Sirmata 2040, the IPWMP and the
  No Bottled Water policy have not been repealed or replaced, and whether the 2024 and 2025 editions of the
  No Bottled Water memorandum exist (only 2022 and 2023 are on file).
- [ ] **Policy review window:** check whether the 2020 IPWMP revision falls inside THE's 2027 window
  for the "created or reviewed" point.
- [ ] **Graduation planting:** photos for the July 2024 Salinged Park planting (not captured).

## 3. Before uploading to THE

- [ ] Confirm the 2027 data year with THE (impact@timeshighereducation.com or the portal
  introduction page). These documents assume calendar 2025.
- [ ] Upload **one PDF per indicator**, not the compendium. The compendium is for internal review
  and the MMSU website.
- [ ] The 2026 methodology says documents containing many links are rejected and reviewers do not
  open links. The PDFs are written to stand on their own; build upload copies with
  `python3 build.py --no-urls` if you want the web addresses removed.
- [ ] Publish the final PDFs on the MMSU evidence portal and keep them online until the next
  data-collection cycle.

## 4. Indicators still without evidence

- **15.2.2** (sustainably farmed food) asks for a policy. None was found, and MMSU's practices (vermicast,
  GAP training, indigenous food plant foodscapes) do not replace one, so no section is included.
- **15.2.6** (tourism land-management outreach) is a draft (`DRAFT_SDG15_15.2.6_…pdf`): it holds only the
  Biodiversity Conservation Learning Center and the KPNP role. Find a community programme before submitting.
- **15.3.2** (IUCN and national-list species policy) and **15.3.4** (alien species policy): nothing found.
- **15.3.1, 15.3.3, 15.4.3** are covered only by pre-2025 policies (continuing) and have no 2025 item.
