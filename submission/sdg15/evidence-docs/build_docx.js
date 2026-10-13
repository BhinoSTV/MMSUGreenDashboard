// Build the Word version of the MMSU SDG 15 evidence compendium from content.json
// (written by build.py). Usage: python3 build.py && node build_docx.js
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType,
  AlignmentType, BorderStyle, ShadingType, HeadingLevel, PageBreak, Footer, Header,
  ExternalHyperlink, LevelFormat, PageNumber, VerticalAlign, TableLayoutType,
} = require("docx");

const HERE = __dirname;
const C = JSON.parse(fs.readFileSync(path.join(HERE, "content.json"), "utf8"));
const ASSETS = path.join(HERE, "assets");
const OUT = path.join(HERE, "MMSU_SDG15_Life_on_Land_Evidence_2025.docx");

const GREEN = "3FAA3A", DARK = "0B4A16", LIGHT = "F1F8EE", MUTED = "5B5B57";
const FONT = "Arial";
const W = 12240, MARGIN = 1080, CONTENT = W - 2 * MARGIN; // US Letter, 0.75" margins
const EMU_IN = 96; // docx-js image sizes are in pixels at 96 dpi

const none = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: none, bottom: none, left: none, right: none, insideHorizontal: none, insideVertical: none };
const greenBorder = { style: BorderStyle.SINGLE, size: 18, color: GREEN };
const frameBorders = { top: greenBorder, bottom: greenBorder, left: greenBorder, right: greenBorder };

const run = (text, o = {}) => new TextRun({ text, font: FONT, ...o });
const para = (children, o = {}) => new Paragraph({ children: Array.isArray(children) ? children : [children], ...o });

function fit(name, maxW, maxH) {
  const [w, h] = C.dims[name];
  const s = Math.min(maxW / w, maxH / h);
  return { width: Math.round(w * s), height: Math.round(h * s) };
}

function photoCell(name, widthDxa, maxWpx, maxHpx) {
  const cap = C.photos[name] || "";
  const file = path.join(ASSETS, name);
  const children = [];
  if (fs.existsSync(file)) {
    children.push(para(new ImageRun({
      type: name.endsWith(".png") ? "png" : "jpg", data: fs.readFileSync(file),
      transformation: fit(name, maxWpx, maxHpx), altText: { title: cap, description: cap, name },
    }), { alignment: AlignmentType.CENTER }));
  } else {
    const where = C.photo_source[name] || "MMSU Public Affairs files";
    children.push(
      para(run("PHOTO TO INSERT", { bold: true, color: DARK, size: 18 }), { alignment: AlignmentType.CENTER, spacing: { before: 700 } }),
      para(run(cap, { size: 16, color: MUTED }), { alignment: AlignmentType.CENTER }),
      para(run(`Replace with: ${name}`, { size: 14, color: MUTED }), { alignment: AlignmentType.CENTER }),
      para(run(`Source: ${where}`, { size: 14, color: MUTED }), { alignment: AlignmentType.CENTER, spacing: { after: 700 } }),
    );
  }
  return new TableCell({
    width: { size: widthDxa, type: WidthType.DXA }, borders: frameBorders,
    shading: fs.existsSync(file) ? undefined : { type: ShadingType.CLEAR, fill: "E9F3E5", color: "auto" },
    margins: { top: 60, bottom: 60, left: 60, right: 60 }, verticalAlign: VerticalAlign.CENTER, children,
  });
}

function captionCell(name, widthDxa) {
  return new TableCell({
    width: { size: widthDxa, type: WidthType.DXA }, borders: noBorders,
    margins: { top: 40, bottom: 80, left: 40, right: 40 },
    children: [para(run(C.photos[name] || "", { italics: true, size: 15, color: MUTED }), { alignment: AlignmentType.CENTER })],
  });
}

function photosBlock(names) {
  if (!names.length) return [];
  if (names.length === 1) {
    const w = Math.round(CONTENT * 0.8);
    return [new Table({
      width: { size: w, type: WidthType.DXA }, columnWidths: [w], alignment: AlignmentType.CENTER,
      layout: TableLayoutType.FIXED,
      rows: [new TableRow({ children: [photoCell(names[0], w, 5.0 * EMU_IN, 3.1 * EMU_IN)] }),
             new TableRow({ children: [captionCell(names[0], w)] })],
    })];
  }
  const gap = 240, cw = Math.floor((CONTENT - gap) / 2);
  const spacer = () => new TableCell({ width: { size: gap, type: WidthType.DXA }, borders: noBorders, children: [para(run(""))] });
  return [new Table({
    width: { size: CONTENT, type: WidthType.DXA }, columnWidths: [cw, gap, cw], layout: TableLayoutType.FIXED,
    rows: [
      new TableRow({ children: [photoCell(names[0], cw, 3.0 * EMU_IN, 2.3 * EMU_IN), spacer(), photoCell(names[1], cw, 3.0 * EMU_IN, 2.3 * EMU_IN)] }),
      new TableRow({ children: [captionCell(names[0], cw), spacer(), captionCell(names[1], cw)] }),
    ],
  })];
}

function sourcesBlock(keys) {
  const out = [para(run("Source", { bold: true, size: 16, color: MUTED }), {
    spacing: { before: 60, after: 20 }, border: { top: { style: BorderStyle.SINGLE, size: 4, color: "D5E6CF", space: 4 } },
  })];
  for (const k of keys) {
    const s = C.sources[k];
    const children = [run(s.label, { size: 15, color: MUTED })];
    if (s.url) {
      children.push(run("  ", { size: 15 }), new ExternalHyperlink({
        link: s.url, children: [run(s.url, { size: 14, color: "2C6E2A", underline: {} })],
      }));
    }
    out.push(para(children, { numbering: { reference: "src", level: 0 }, spacing: { after: 20 } }));
  }
  return out;
}

function story(key) {
  const s = C.stories[key];
  return [
    para(run(s.title, { bold: true, color: GREEN, size: 30 }), {
      heading: HeadingLevel.HEADING_2, alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 280, after: 160 },
    }),
    ...photosBlock(s.photos),
    ...s.paras.map((p) => para(run(p, { size: 21 }), { alignment: AlignmentType.JUSTIFIED, spacing: { before: 100, after: 100, line: 300 } })),
    ...sourcesBlock(s.sources),
  ];
}

function header(doc) {
  const tile = new ImageRun({ type: "png", data: fs.readFileSync(path.join(ASSETS, "_sdg15_tile.png")),
    transformation: { width: 1.35 * EMU_IN, height: 1.35 * EMU_IN }, altText: { title: "SDG 15", description: "SDG 15 Life on Land", name: "sdg15" } });
  const tw = 2100, rw = CONTENT - tw;
  const commit = new Table({
    width: { size: CONTENT, type: WidthType.DXA }, columnWidths: [tw, rw], layout: TableLayoutType.FIXED,
    rows: [new TableRow({ children: [
      new TableCell({ width: { size: tw, type: WidthType.DXA }, borders: noBorders, children: [para(tile)] }),
      new TableCell({ width: { size: rw, type: WidthType.DXA }, borders: noBorders, children: [
        para(run("MMSU’s Commitment", { bold: true, color: GREEN, size: 28, underline: {} }), { spacing: { after: 80 } }),
        para(run(C.commitment, { bold: true, italics: true, size: 25 }), { spacing: { line: 320 } }),
      ] }),
    ] })],
  });
  const box = (children) => para(children, {
    shading: { type: ShadingType.CLEAR, fill: LIGHT, color: "auto" },
    border: { left: { style: BorderStyle.SINGLE, size: 36, color: "56C02B", space: 8 } },
    indent: { left: 160 }, spacing: { after: 0 },
  });
  return [
    commit,
    para(run(""), { spacing: { after: 80 } }),
    box(run(`SDG ${doc.code} · ${doc.title}`, { bold: true, color: DARK, size: 22 })),
    box(run(doc.question, { italics: true, size: 18, color: MUTED })),
    box(run(C.evidence_year, { size: 18 })),
  ];
}

function section(doc, first) {
  const out = [];
  if (!first) out.push(para(new PageBreak()));
  out.push(para(run(`SDG ${doc.code} · ${doc.title}`, { size: 2, color: "FFFFFF" }), { heading: HeadingLevel.HEADING_1, spacing: { after: 0 } }));
  out.push(...header(doc));
  for (const k of doc.stories) out.push(...story(k));
  return out;
}

function simpleTable(cols, rows, widths) {
  const head = new TableRow({ tableHeader: true, children: cols.map((c, i) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA }, shading: { type: ShadingType.CLEAR, fill: DARK, color: "auto" },
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    children: [para(run(c, { bold: true, color: "FFFFFF", size: 18 }))],
  })) });
  const body = rows.map((r, ri) => new TableRow({ children: r.map((c, i) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    shading: ri % 2 ? { type: ShadingType.CLEAR, fill: "F7FBF5", color: "auto" } : undefined,
    margins: { top: 70, bottom: 70, left: 100, right: 100 },
    borders: { top: none, left: none, right: none, bottom: { style: BorderStyle.SINGLE, size: 4, color: "D5E6CF" } },
    children: String(c).split("\n").map((line) => para(run(line, { size: 17, bold: i === 0 }))),
  })) }));
  return new Table({ width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
    layout: TableLayoutType.FIXED, rows: [head, ...body] });
}

const h1 = (t) => para(run(t, { bold: true, color: DARK, size: 32 }), { heading: HeadingLevel.HEADING_1, spacing: { before: 120, after: 200 } });
const body = (t, o = {}) => para(run(t, { size: 20, ...o }), { alignment: AlignmentType.JUSTIFIED, spacing: { after: 140, line: 290 } });
const bullet = (t) => para(run(t, { size: 20 }), { numbering: { reference: "bul", level: 0 }, spacing: { after: 60 } });

// ---------------------------------------------------------------- front matter
const allDocs = [...C.docs, C.supporting].filter(Boolean);
const cover = [
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(ASSETS, "_sdg15_tile.png")),
    transformation: { width: 1.6 * EMU_IN, height: 1.6 * EMU_IN }, altText: { title: "SDG 15", description: "SDG 15 Life on Land", name: "sdg15" } }),
    { spacing: { before: 1600, after: 300 } }),
  para(run("SDG 15 Life on Land", { bold: true, color: DARK, size: 56 })),
  para(run("Evidence Compendium 2025", { bold: true, color: DARK, size: 56 }), { spacing: { after: 200 } }),
  para(run("Mariano Marcos State University · THE Sustainability Impact Ratings 2027", { bold: true, color: GREEN, size: 26 }), { spacing: { after: 500 } }),
  para(run("Compiled from MMSU, DOST-PCAARRD and news sources for the 2027 data submission (due 9 November 2026). Each section corresponds to one THE SDG 15 indicator. Evidence year: 2025 (calendar year).", { size: 19, color: MUTED })),
  para(run("Draft for validation, prepared 13 October 2026. Photos marked “PHOTO TO INSERT” and the items on the last pages must be completed before submission.", { size: 19, color: MUTED, italics: true }), { spacing: { before: 120 } }),
  para(new PageBreak()),
];

const contents = [
  h1("Contents by indicator"),
  simpleTable(["Indicator", "THE question", "Evidence in this compendium"],
    allDocs.map((d) => [d.code, d.title, d.stories.map((k) => C.stories[k].title).join("\n")]), [1200, 3300, CONTENT - 4500]),
  para(new PageBreak()),
];

const lessons = [
  h1("What top-rated universities submit for SDG 15"),
  body("Evidence pages of Philippine universities that score well on SDG 15 were reviewed to see what kinds of accomplishments they claim for each indicator. MMSU’s search was then repeated for the same kinds of evidence, including MMSU’s full 2025 news archive. This edition retains only 2025 accomplishments; MMSU policies adopted before 2025 are kept in a separate annex."),
  simpleTable(["University", "What it submits for SDG 15", "Applied to MMSU"], [
    ["Visayas State University (VSU)", "91st of 658 universities in SDG 15 (2026) and the top-rated state university in the Philippines overall (301–400). Evidence includes a Board-approved Policy on Tree Management (BOR Resolution No. 146, s. 2025), forest landscape restoration with ACIAR and DENR, rainforestation training, a forester capacity-building partnership (Project CAPABUILD), and a Technical Working Group led by its International Affairs and Relations Office that compiles evidence for all 17 SDGs.", "MMSU has a 2021 land use policy (in the annex) but no 2025 policy action; a 2025 Board resolution or review on the forest reserves would answer 15.3.1. A standing SDG working group would keep evidence flowing."],
    ["Caraga State University (CarSU)", "An SDG 15 page organised indicator by indicator: forums, a natural science museum launch and an agroforestry field day (15.2.1); a sustainably managed campus farm (15.2.2); biodiversity surveys and a biodiversity-corridor workshop (15.2.3); farmer trainings and seedling distribution (15.2.5); campus planning that consults biodiversity data (15.3.3); agreements with DENR and barangays (15.3.5); an Adopt-an-Estero commitment (15.4.1); and dated memoranda on plastic waste (Memo No. 33, s. 2024) and hazardous waste (Memo No. 50, s. 2024) with EMB seminars (15.4.2, 15.4.3).", "2025 field day, School-on-the-Air, farmer trainings and mangrove plantings added for 15.2.1, 15.2.5 and 15.3.5. MMSU’s plastic and hazardous waste memoranda predate 2025 (annex); a 2025 memorandum or review would restore 15.4.2 and 15.4.3 policy points."],
    ["Eastern Visayas State University (EVSU)", "Lists its Board-approved Land Use Development and Infrastructure Plan and an arboretum among its SDG 15 evidence.", "MMSU’s Sirmata 2040 LUDIP is now presented under 15.3.3; quote its forest-reserve and green-space provisions in the final version."],
    ["University of Manchester", "Ranked first in the world for SDG 15 in 2026 (658 universities ranked) and first overall.", "Shows the weight of documented policies and campus biodiversity management alongside research."],
  ], [2000, 4700, CONTENT - 6700]),
  para(new PageBreak()),
];

// ---------------------------------------------------------------- back matter
const gaps = [
  para(new PageBreak()),
  h1("Indicators still without public evidence"),
  body("The following SDG 15 questions have no 2025 MMSU evidence online. Peer universities answer them with dated policies or programmes; MMSU should retrieve or issue the equivalent documents. MMSU’s SDG 15 page also lists “Number of Seedlings Planted from 2018 to 2024,” “Summary of Tree Inventory for Payao and Dingras, October–December 2023” and “Sustainable Use of Land,” but no file is attached to those links; adding them would strengthen 15.2.3, 15.3.1 and 15.3.2."),
  simpleTable(["Indicator", "What peers submit", "What MMSU should produce"], [
    ["15.2.2 Sustainably farmed food on campus", "Campus farm statement or food sourcing policy", "2025 memorandum on sourcing campus food from MMSU farms and local sustainable growers"],
    ["15.2.6 Tourism land-management outreach", "Training for tourism operators or eco-park stewards", "Community programme linked to the Biodiversity Conservation Learning Center or campus eco-sites"],
    ["15.3.1 Land conservation policy", "Board-approved tree or forest policy (VSU, 2025)", "2025 Board resolution or review of the Sirmata 2040 land use policy (2021, in annex)"],
    ["15.3.2 IUCN and national-list species policy", "Species monitoring policy with a register", "Policy plus a register for the forest reserves"],
    ["15.3.3 Biodiversity in planning", "Planning that consults biodiversity data", "A 2025 project or planning record applying the Sirmata 2040 protected-land rules"],
    ["15.3.4 Alien species policy", "Alien species policy", "Native-species planting and invasive-species control policy"],
    ["15.4.3 Hazardous waste policy", "Dated memorandum and EMB seminar (CarSU, 2024)", "2025 memorandum or review of the IPWMP hazardous waste provisions (2020, in annex)"],
], [2600, 3200, CONTENT - 5800]),
  para(run(""), { spacing: { after: 120 } }),
  h1("To complete before submission"),
  bullet("Free access: state that the 2025 mangrove seminar, alukon training, Pinili bamboo training and School-on-the-Air were free of charge, if true. THE gives full credit only to free programmes (15.2.4, 15.2.5)."),
  bullet("Policies: the land use, plastic and hazardous waste policies predate 2025 and are in the separate annex. Issue or document a 2025 review or reiteration (for example the annual No Bottled Water memorandum for 2025) to bring them into the 2025 set."),
  bullet("Pasuquin agreement (signed 29 November 2025): attach a copy of the signed memorandum of agreement."),
  bullet("Confirm the date of the 2025 MMSU–DENR Region 1 dialogue at ILAARRDEC and add the Biodiversity Day photo contest announcement link."),
  bullet("Confirm the 2027 data year with THE before upload, and upload one file per indicator rather than this compendium. THE rejects evidence that is mainly a list of links."),
];

let content = [...cover, ...contents, ...lessons];
allDocs.forEach((d, i) => content.push(...section(d, i === 0)));
content.push(...gaps);

const doc = new Document({
  creator: "Mariano Marcos State University",
  title: "MMSU SDG 15 Life on Land Evidence Compendium 2025",
  description: "Evidence for THE Sustainability Impact Ratings 2027, SDG 15",
  styles: { default: { document: { run: { font: FONT, size: 20 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, bold: true, color: DARK }, paragraph: { outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, bold: true, color: GREEN }, paragraph: { outlineLevel: 1 } },
    ] },
  numbering: { config: [
    { reference: "src", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 300, hanging: 200 } } } }] },
    { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 400, hanging: 260 } } } }] },
  ] },
  sections: [{
    properties: { page: { size: { width: W, height: 15840 }, margin: { top: 1080, bottom: 1080, left: MARGIN, right: MARGIN } } },
    headers: { default: new Header({ children: [para(run(""), { border: { bottom: { style: BorderStyle.SINGLE, size: 24, color: DARK, space: 2 } } })] }) },
    footers: { default: new Footer({ children: [para([
      run("Mariano Marcos State University · City of Batac, Ilocos Norte    |    THE Sustainability Impact Ratings 2027 · SDG 15 · page ", { size: 14, color: MUTED }),
      new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 14, color: MUTED }),
    ], { border: { top: { style: BorderStyle.SINGLE, size: 24, color: DARK, space: 4 } } })] }) },
    children: content,
  }],
});

Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(OUT, buf); console.log("wrote", OUT); });
