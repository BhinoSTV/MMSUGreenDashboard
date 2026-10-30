// Builds the SDG 15 team update deck.
// Usage: NODE_PATH=<dir with pptxgenjs, react, react-dom, react-icons, sharp> node build_update.js
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const RDS = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");
const { applyTheme } = require("/root/.claude/skills/synced/80af2b21-4bdb-4232-8a38-3073c1ef1596_1f53c6f9-dfd6-4ee6-a8c3-4c8eca6e5386/pptx/scripts/apply_theme.js");

const ASSETS = path.join(__dirname, "..", "evidence-docs", "assets");
const OUT = path.join(__dirname, "SDG15_Team_Update_2026-10-30.pptx");

// ---------------------------------------------------------------- theme
const THEME = {
  name: "MMSU SDG 15",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1D1D1B", lt1: "FFFFFF", dk2: "0B4A16", lt2: "EEF6EA",
    accent1: "3FAA3A", accent2: "56C02B", accent3: "B45309", accent4: "2C6E2A", accent5: "5B5B57", accent6: "E3B04B",
    hlink: "2C6E2A", folHlink: "5B5B57",
  },
};
const HEX = { green: "3FAA3A", moss: "97BC62", gold: "E3B04B", amber: "B45309", dark: "0B4A16" };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33" x 7.5"
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "SDG 15 Life on Land: evidence update";
pres.author = "SDG 15 focal persons, Mariano Marcos State University";
const C = pres.SchemeColor;
const W = 13.333;

// ---------------------------------------------------------------- layouts
pres.defineSlideMaster({
  title: "TITLE", background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.2, w: 8.4, h: 1.9, fontSize: 48, bold: true, color: C.background1, valign: "top", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "subtitle", type: "body", x: 0.8, y: 4.3, w: 8.4, h: 1.0, fontSize: 22, color: C.background2, valign: "top", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "meta", type: "body", x: 0.8, y: 6.1, w: 8.4, h: 0.6, fontSize: 16, color: C.accent6, valign: "top", align: "left", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: C.background1 },
  slideNumber: { x: 12.2, y: 7.02, w: 0.6, h: 0.3, fontSize: 11, color: C.accent5, align: "right" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 1.05, fontSize: 34, bold: true, color: C.text2, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: "MMSU · THE Impact Rankings 2027 · SDG 15 Life on Land", options: { x: 0.6, y: 7.02, w: 8, h: 0.3, fontSize: 11, color: C.accent5, margin: 0, isTextBox: true } } },
  ],
});
pres.defineSlideMaster({
  title: "CLOSE", background: { color: C.text2 },
  slideNumber: { x: 12.2, y: 7.02, w: 0.6, h: 0.3, fontSize: 11, color: C.background2, align: "right" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 1.05, fontSize: 34, bold: true, color: C.background1, valign: "middle", align: "left", margin: 0 }, text: "" } },
  ],
});

// ---------------------------------------------------------------- helpers
async function icon(Comp, color) {
  const svg = RDS.renderToStaticMarkup(React.createElement(Comp, { color: "#" + color, size: "256" }));
  const buf = await sharp(Buffer.from(svg)).resize(256, 256, { fit: "contain", background: { r: 0, g: 0, b: 0, alpha: 0 } }).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}
function badge(slide, img, x, y, d, name, fill) {
  slide.addShape(pres.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color: fill || C.accent1 }, line: { color: fill || C.accent1, width: 0 }, objectName: name + " badge" });
  const p = d * 0.26;
  slide.addImage({ data: img, x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p, objectName: name + " icon", altText: name });
}
const txt = (slide, t, o) => slide.addText(t, { isTextBox: true, margin: 0, valign: "top", color: C.text1, ...o });

function card(slide, x, y, w, h, name, fill) {
  slide.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.12, fill: { color: fill || C.background2 }, line: { color: fill || C.background2, width: 0 }, objectName: name });
}

(async () => {
  const I = {
    tree: await icon(fa.FaTree, "FFFFFF"), file: await icon(fa.FaFileAlt, "FFFFFF"), check: await icon(fa.FaClipboardCheck, "FFFFFF"),
    book: await icon(fa.FaBookOpen, "FFFFFF"), globe: await icon(fa.FaGlobeAsia, "FFFFFF"), balance: await icon(fa.FaBalanceScale, "FFFFFF"),
    news: await icon(fa.FaNewspaper, "FFFFFF"), fb: await icon(fa.FaThumbsUp, "FFFFFF"), memo: await icon(fa.FaEnvelopeOpenText, "FFFFFF"),
    warn: await icon(fa.FaExclamationTriangle, "FFFFFF"), cal: await icon(fa.FaCalendarAlt, "FFFFFF"), search: await icon(fa.FaSearch, "FFFFFF"),
    flag: await icon(fa.FaFlagCheckered, "FFFFFF"), layer: await icon(fa.FaLayerGroup, "FFFFFF"),
  };

  // ---- 1. Title
  pres.addSection({ title: "Opening" });
  let s = pres.addSlide({ masterName: "TITLE", sectionTitle: "Opening" });
  s.addText("SDG 15 Life on Land", { placeholder: "title" });
  s.addText("Evidence update for the THE Impact Rankings 2027", { placeholder: "subtitle" });
  s.addText("THE Core Team (SO No. 26-649) · update as of 30 October 2026", { placeholder: "meta" });
  s.addImage({ path: path.join(ASSETS, "_sdg15_tile.png"), x: 9.6, y: 2.2, w: 3.0, h: 3.0, altText: "SDG 15 Life on Land tile", objectName: "SDG 15 tile" });
  s.addNotes("Purpose of this update: where the SDG 15 evidence package stands, what we learned from VSU, and what we need from the team before the 3 to 5 November workshop and the 9 November data deadline.");

  // ---- 2. Where we stand
  pres.addSection({ title: "Status" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Status" });
  s.addText("Ten of 14 questions have evidence; three have none", { placeholder: "title" });
  s.addChart(pres.charts.DOUGHNUT, [{ name: "Indicators", labels: ["2025 evidence", "Pre-2025 policy only", "Draft only", "No evidence yet"], values: [7, 3, 1, 3] }], {
    x: 0.6, y: 1.55, w: 5.2, h: 5.2, holeSize: 62, chartColors: [HEX.green, HEX.moss, HEX.gold, HEX.amber],
    showLegend: false, showTitle: false, showValue: true, showPercent: false, dataLabelColor: "FFFFFF", dataLabelFontSize: 16, dataLabelFontBold: true, dataLabelFontFace: "+mn-lt",
    dataBorder: { pt: 2, color: "FFFFFF" },
  });
  txt(s, [{ text: "14", options: { fontSize: 54, bold: true, color: C.text2, breakLine: true, fontFace: "+mj-lt" } }, { text: "indicators", options: { fontSize: 16, color: C.accent5 } }], { x: 2.2, y: 3.45, w: 2.0, h: 1.4, align: "center", objectName: "Chart centre label" });
  const rows = [
    ["7", "2025 evidence", "15.2.1, 15.2.3, 15.2.4, 15.2.5, 15.3.5, 15.4.1, 15.4.2", HEX.green],
    ["3", "Pre-2025 policy only", "15.3.1, 15.3.3, 15.4.3", HEX.moss],
    ["1", "Draft only", "15.2.6: no 2025 programme found", HEX.gold],
    ["3", "No evidence yet", "15.2.2, 15.3.2, 15.3.4", HEX.amber],
  ];
  rows.forEach((r, i) => {
    const y = 1.75 + i * 1.28;
    card(s, 6.3, y, 6.4, 1.1, "Status card " + r[1]);
    s.addShape(pres.ShapeType.roundRect, { x: 6.5, y: y + 0.2, w: 0.7, h: 0.7, rectRadius: 0.1, fill: { color: r[3] }, line: { color: r[3], width: 0 }, objectName: "Count chip " + r[1] });
    txt(s, r[0], { x: 6.5, y: y + 0.2, w: 0.7, h: 0.7, fontSize: 28, bold: true, color: C.background1, align: "center", valign: "middle", fontFace: "+mj-lt" });
    txt(s, r[1], { x: 7.45, y: y + 0.15, w: 5.1, h: 0.4, fontSize: 20, bold: true, color: C.text2 });
    txt(s, r[2], { x: 7.45, y: y + 0.58, w: 5.1, h: 0.45, fontSize: 14, color: C.accent5 });
  });
  s.addNotes("Seven indicators have dated 2025 evidence. Three more (15.3.1, 15.3.3, 15.4.3) are covered only by policies adopted before 2025. 15.2.6 is a draft because no 2025 community programme on land management for tourism was found. 15.2.2, 15.3.2 and 15.3.4 have nothing yet.");

  // ---- 3. What the package contains
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Status" });
  s.addText("The package lists 2025 first, then what continues", { placeholder: "title" });
  card(s, 0.6, 1.65, 5.7, 1.9, "Tier 1 card", C.accent1);
  txt(s, "1  Evidence from 2025", { x: 0.9, y: 1.85, w: 5.1, h: 0.5, fontSize: 24, bold: true, color: C.background1, fontFace: "+mj-lt" });
  txt(s, "Dated activities with photos, figures and sources.", { x: 0.9, y: 2.5, w: 5.1, h: 0.8, fontSize: 18, color: C.background1 });
  s.addShape(pres.ShapeType.downArrow, { x: 3.1, y: 3.65, w: 0.7, h: 0.55, fill: { color: C.accent4 }, line: { color: C.accent4, width: 0 }, objectName: "Arrow down" });
  card(s, 0.6, 4.3, 5.7, 1.9, "Tier 2 card", C.text2);
  txt(s, "2  Continuing implementation", { x: 0.9, y: 4.5, w: 5.1, h: 0.5, fontSize: 24, bold: true, color: C.background1, fontFace: "+mj-lt" });
  txt(s, "Policies still in force and 2024 to 2026 activity that shows the work is ongoing.", { x: 0.9, y: 5.15, w: 5.1, h: 0.9, fontSize: 18, color: C.background1 });
  const items = [
    [I.file, "11 indicator PDFs", "One per indicator, written to stand alone. 15.2.6 is marked as a draft."],
    [I.book, "46-page Word compendium", "Editable version with every photo and source, for the team to revise."],
    [I.check, "Checklist", "Facts to confirm before upload, and what each missing item would earn."],
  ];
  items.forEach((it, i) => {
    const y = 1.65 + i * 1.7;
    badge(s, it[0], 6.9, y, 0.9, it[1]);
    txt(s, it[1], { x: 8.05, y: y + 0.02, w: 4.7, h: 0.45, fontSize: 22, bold: true, color: C.text2 });
    txt(s, it[2], { x: 8.05, y: y + 0.5, w: 4.7, h: 0.9, fontSize: 16, color: C.text1 });
  });
  s.addNotes("The first edition kept only 2025 items. After comparing with VSU we added a Continuing implementation section to every indicator so that pre-2025 policies and 2024 to 2026 activity are visible. All files are in the repository under submission/sdg15/evidence-docs.");

  // ---- 4. 2025 highlights
  pres.addSection({ title: "Evidence" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Evidence" });
  s.addText("What we can already show from 2025", { placeholder: "title" });
  const cards = [
    ["forest_reserve_planting_2025.jpg", 1600, 1067, "250 seedlings and propagules", "CAFSD graduands plant native trees and bamboo in the University Forest Reserves, 2 July 2025"],
    ["pasuquin_mou_2025.jpg", 1600, 1200, "1,750 mangrove propagules", "Agreement with TMP Foundation, DENR and LGU-Pasuquin signed 29 November 2025"],
    ["mangrove_seminar_2025.jpg", 1600, 900, "4 municipalities trained", "Mangrove propagation seminar for Currimao, Pasuquin, Badoc and Burgos, 27 to 28 October 2025"],
  ];
  cards.forEach((c, i) => {
    const x = 0.6 + i * 4.15, w = 3.85;
    s.addImage({ path: path.join(ASSETS, c[0]), x, y: 1.6, w, h: 2.6, sizing: { type: "cover", w, h: 2.6 }, altText: c[4], objectName: "Photo " + c[3] });
    txt(s, c[3], { x, y: 4.32, w, h: 0.5, fontSize: 22, bold: true, color: C.accent4 });
    txt(s, c[4], { x, y: 4.85, w, h: 0.9, fontSize: 14, color: C.text1 });
  });
  card(s, 0.6, 5.95, 12.1, 0.8, "Also strip");
  txt(s, [{ text: "Also in the package: ", options: { bold: true, color: C.text2 } }, { text: "School-on-the-Air (1,000 enrollees), Pinili bamboo training (46 participants), alukon training (64 farmers), Badoc mangrove planting (280 propagules)." }], { x: 0.85, y: 6.05, w: 11.6, h: 0.6, fontSize: 15, valign: "middle" });
  s.addNotes("These are examples, not the full list. Each has a dated source article and photos from MMSU STRATCOM. The Pasuquin item still needs a copy of the signed agreement. Free-access wording for the trainings is also still to be confirmed.");

  // ---- 5. VSU
  pres.addSection({ title: "Benchmark" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Benchmark" });
  s.addText("VSU placed 91st in SDG 15 with multi-year evidence", { placeholder: "title" });
  card(s, 0.6, 1.65, 4.3, 3.6, "VSU stat card");
  txt(s, "91st", { x: 0.85, y: 1.85, w: 3.8, h: 1.5, fontSize: 80, bold: true, color: C.text2, fontFace: "+mj-lt" });
  txt(s, "of 658 universities in SDG 15, THE Impact Rankings 2026", { x: 0.85, y: 3.4, w: 3.8, h: 0.9, fontSize: 18, color: C.text1 });
  txt(s, "Overall 301 to 400 band; top state university in the Philippines.", { x: 0.85, y: 4.35, w: 3.8, h: 0.8, fontSize: 14, color: C.accent5 });
  const vsu = [
    [I.file, "One PDF per indicator", "Six to 20 pages each, public on VSU's SDG portal, covering all 14 indicators."],
    [I.layer, "Years are mixed", "2025 items sit beside older ones: 2013 and 2022 memoranda, 2019 and 2023 events."],
    [I.balance, "Policy answers cite law and a memo", "National laws such as RA 9147 and RA 9275, plus a dated university memorandum."],
  ];
  vsu.forEach((it, i) => {
    const y = 1.65 + i * 1.25;
    badge(s, it[0], 5.3, y, 0.8, it[1]);
    txt(s, it[1], { x: 6.35, y, w: 6.35, h: 0.4, fontSize: 20, bold: true, color: C.text2 });
    txt(s, it[2], { x: 6.35, y: y + 0.42, w: 6.35, h: 0.7, fontSize: 15, color: C.text1 });
  });
  card(s, 0.6, 5.55, 12.1, 1.15, "Takeaway card", C.text2);
  txt(s, [{ text: "For MMSU: ", options: { bold: true, color: C.accent6 } }, { text: "keep 2025 first, then add dated policies and programmes that continue. A policy that only restates national law should not be our model." }], { x: 0.9, y: 5.65, w: 11.5, h: 0.95, fontSize: 18, color: C.background1, valign: "middle" });
  s.addNotes("VSU's 2026 result comes from its June 2026 announcement. VSU's evidence files are public. They mix years, which is why we added a Continuing implementation section. We cannot tell from outside how much of VSU's rank came from the documents versus its research metrics, so treat this as a pattern, not proof.");

  // ---- 6. Continuing implementation table
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Benchmark" });
  s.addText("Continuing implementation fills the policy gaps", { placeholder: "title" });
  const hdr = (t) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: C.text2 }, fontSize: 16 } });
  const cell = (t, o = {}) => ({ text: t, options: { fontSize: 16, ...o } });
  const trows = [
    [hdr("Indicator"), hdr("What continues"), hdr("Since")],
    [cell("15.3.1", { bold: true }), cell("Land use policy: conserve, restore and protect university lands"), cell("2021")],
    [cell("15.3.3", { bold: true }), cell("Sirmata 2040: protected land and forest reserve kept no-build"), cell("2021")],
    [cell("15.4.1", { bold: true }), cell("Water policy against pollution; groundwater monitoring of 17 farm wells"), cell("2021; to June 2025")],
    [cell("15.4.2", { bold: true }), cell("Styrofoam and plastic rules; No Bottled Water memoranda"), cell("2009 to 2023")],
    [cell("15.4.3", { bold: true }), cell("Hazardous waste storage and disposal under the IPWMP"), cell("Revised 2020")],
    [cell("15.2.1", { bold: true }), cell("Graduation tree planting by CAFSD classes"), cell("2024, 2025, 2026")],
    [cell("15.2.3", { bold: true }), cell("Mangrove nature-based solutions project, Badoc and Currimao"), cell("Jun 2024 to Apr 2026")],
  ];
  s.addTable(trows, { x: 0.6, y: 1.55, w: 12.1, colW: [1.4, 7.9, 2.8], border: { type: "solid", color: "D5E6CF", pt: 0.75 }, fill: { color: C.background1 }, color: C.text1, valign: "middle", margin: [0.06, 0.12, 0.06, 0.12], rowH: 0.56 });
  txt(s, [{ text: "Catch: ", options: { bold: true, color: C.accent3 } }, { text: "THE adds a point for a policy created or reviewed inside its window, so each older policy needs a 2025 review or reiteration." }], { x: 0.6, y: 6.25, w: 12.1, h: 0.55, fontSize: 16 });
  s.addNotes("These items come from the MMSU Sirmata 2040 documents, the Integrated Pollution and Waste Management Program and news articles. We have not confirmed that each policy is still in force or when THE's review window starts. The 2020 IPWMP revision is the one most at risk of falling outside it.");

  // ---- 7. Bottled water
  pres.addSection({ title: "Findings" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Findings" });
  s.addText("No Bottled Water: what shows it is applied", { placeholder: "title" });
  const bw = [
    [I.news, "Public article", "CAFSD Waste and Pollution Management launch, 15 October 2024: plastic bottled water banned in its auxiliary building; reusable tumblers encouraged."],
    [I.fb, "Facebook posts MMSU cites", "CCIS SipSmart campaign, BioCircle Society refilling station, hydration stations of academic units. Behind a login, so screenshots with dates are needed."],
    [I.memo, "Presidential memos", "OP Memo 24-075 (16 Feb 2024) and 24-088 (29 Feb 2024) tell employees to bring their own tumbler or water bottle."],
  ];
  bw.forEach((b, i) => {
    const x = 0.6 + i * 4.15, w = 3.85;
    card(s, x, 1.6, w, 3.9, "Evidence card " + b[1]);
    badge(s, b[0], x + 0.25, 1.85, 0.8, b[1]);
    txt(s, b[1], { x: x + 0.25, y: 2.8, w: w - 0.5, h: 0.45, fontSize: 20, bold: true, color: C.text2 });
    txt(s, b[2], { x: x + 0.25, y: 3.3, w: w - 0.5, h: 2.1, fontSize: 15, color: C.text1 });
  });
  card(s, 0.6, 5.75, 12.1, 1.0, "Missing card", "FDF1E3");
  txt(s, [{ text: "Missing: ", options: { bold: true, color: C.accent3 } }, { text: "the 2024 and 2025 reiterations of the policy and Administrative Council minutes. No public post covers the 2022 or 2023 memoranda themselves." }], { x: 0.85, y: 5.85, w: 11.6, h: 0.8, fontSize: 16, valign: "middle" });
  s.addNotes("We scanned all 2,866 articles on the MMSU news site (2007 to October 2026) and found no post about the memoranda. The best public item is the CAFSD article. MMSU's own SDG pages cite three Facebook posts that we could not open without logging in. The two memos are in the focal person's mailbox.");

  // ---- 8. Gaps and risks
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Findings" });
  s.addText("Four gaps and four risks to settle", { placeholder: "title" });
  const colX = [0.6, 6.85], colW = 5.85;
  [["Gaps", I.search, C.accent3, [
    ["15.2.2", "Needs a policy on sustainably farmed campus food. Our farm practices do not replace it."],
    ["15.2.6", "No 2025 community programme on land management for tourism."],
    ["15.3.2", "No threatened-species policy or register."],
    ["15.3.4", "No alien-species policy."],
  ]], ["Risks", I.warn, C.accent4, [
    ["Data year", "THE has not confirmed it for 2027; we assume 2025."],
    ["Review window", "Older policies may fall outside it (IPWMP 2020, Sirmata 2021)."],
    ["Links", "Reviewers do not follow links, so each PDF must stand alone."],
    ["Free access", "Not stated for the 2025 trainings; charged programmes score 0.25."],
  ]]].forEach((col, ci) => {
    const x = colX[ci];
    card(s, x, 1.55, colW, 5.2, col[0] + " card");
    badge(s, col[1], x + 0.3, 1.8, 0.7, col[0], col[2]);
    txt(s, col[0], { x: x + 1.2, y: 1.85, w: 3.5, h: 0.6, fontSize: 26, bold: true, color: C.text2, valign: "middle", fontFace: "+mj-lt" });
    col[3].forEach((r, i) => {
      const y = 2.75 + i * 1.0;
      txt(s, r[0], { x: x + 0.3, y, w: 1.5, h: 0.4, fontSize: 17, bold: true, color: col[2] });
      txt(s, r[1], { x: x + 1.85, y, w: colW - 2.15, h: 0.9, fontSize: 15, color: C.text1 });
    });
  });
  s.addNotes("The gaps are where no document exists. 15.2.2 asks for a policy, so submitting farm practices would mislead reviewers. The risks are decisions or confirmations rather than missing documents.");

  // ---- 9. Asks
  pres.addSection({ title: "Actions" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Actions" });
  s.addText("What we need from the team", { placeholder: "title" });
  const arows = [
    [hdr("#"), hdr("Action"), hdr("Proposed owner")],
    [cell("1", { bold: true }), cell("Confirm the 2027 data year and policy-review window with THE"), cell("Chair and Co-Chair")],
    [cell("2", { bold: true }), cell("Screenshot the three Facebook posts; find the 2024 and 2025 bottled-water reiterations and council minutes"), cell("CCIS, BioCircle, University Secretary")],
    [cell("3", { bold: true }), cell("Free-access statements, attendance sheets and the signed Pasuquin agreement"), cell("Extension and Research Directorates")],
    [cell("4", { bold: true }), cell("A 2025 review or reiteration of the land use, water and waste policies"), cell("Planning and General Services")],
    [cell("5", { bold: true }), cell("A policy or programme for 15.2.2, 15.2.6, 15.3.2 and 15.3.4"), cell("SDG 15 focal persons with CAFSD")],
  ];
  s.addTable(arows, { x: 0.6, y: 1.55, w: 12.1, colW: [0.6, 7.4, 4.1], border: { type: "solid", color: "D5E6CF", pt: 0.75 }, fill: { color: C.background1 }, color: C.text1, valign: "middle", margin: [0.06, 0.12, 0.06, 0.12], rowH: [0.55, 0.75, 0.95, 0.9, 0.8, 0.8] });
  txt(s, "Owners are proposals for discussion, not assignments.", { x: 0.6, y: 6.6, w: 12.1, h: 0.35, fontSize: 14, color: C.accent5 });
  s.addNotes("Owners are suggestions based on who is likely to hold each record. Please correct them in the meeting.");

  // ---- 10. Close
  s = pres.addSlide({ masterName: "CLOSE", sectionTitle: "Actions" });
  s.addText("Next steps to the 9 November deadline", { placeholder: "title" });
  const steps = [
    [I.search, "Now to 3 Nov", "Collect the missing records and confirm the data year"],
    [I.cal, "3 to 5 Nov", "Locked-in workshop: finalise one PDF per indicator"],
    [I.flag, "9 Nov", "THE data due: upload the final PDFs"],
  ];
  steps.forEach((st, i) => {
    const x = 0.6 + i * 4.15, w = 3.85;
    card(s, x, 1.9, w, 3.4, "Step card " + st[1], C.accent4);
    badge(s, st[0], x + 0.3, 2.15, 0.9, st[1], C.accent1);
    txt(s, st[1], { x: x + 0.3, y: 3.25, w: w - 0.6, h: 0.5, fontSize: 26, bold: true, color: C.background1, fontFace: "+mj-lt" });
    txt(s, st[2], { x: x + 0.3, y: 3.85, w: w - 0.6, h: 1.3, fontSize: 18, color: C.background1 });
  });
  txt(s, "The Special Order also lists a session on 29 November, after the deadline. Please verify that date.", { x: 0.6, y: 5.8, w: 12.1, h: 0.5, fontSize: 16, color: C.accent6 });
  s.addNotes("Dates from Special Order 26-649 and the data deadline recorded earlier in this project. The 29 November session falls after the 9 November data deadline, so one of the two dates may be wrong.");

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
