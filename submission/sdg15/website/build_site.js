// Builds website/index.html (one self-contained file) from src/.
// Usage: NODE_PATH=<dir with react, react-dom, react-icons, sharp> node build_site.js
const fs = require("fs");
const path = require("path");
const React = require("react");
const RDS = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");

const HERE = __dirname;
const SRC = path.join(HERE, "src");
const ASSETS = path.join(HERE, "..", "evidence-docs", "assets");   // MMSU photos
const BRAND = path.join(SRC, "brand");                              // logo, SDG wheel and SDG 15 icon from mmsu.edu.ph

const b64 = (buf, mime) => `data:${mime};base64,${buf.toString("base64")}`;

(async () => {
  const data = JSON.parse(fs.readFileSync(path.join(SRC, "sdg15_data.json"), "utf8"));
  const css = fs.readFileSync(path.join(SRC, "styles.css"), "utf8");
  const app = fs.readFileSync(path.join(SRC, "app.js"), "utf8");

  const img = {};
  img.logo = b64(await sharp(path.join(BRAND, "mmsu.png")).resize(240, 240).png({ compressionLevel: 9, palette: true }).toBuffer(), "image/png");
  img.wheel = b64(await sharp(path.join(BRAND, "SDG_Wheel.png")).resize(420, 420).png({ compressionLevel: 9 }).toBuffer(), "image/png");
  img.sdg15 = b64(await sharp(path.join(BRAND, "SDG15_icon.jpg")).resize(450, 450).jpeg({ quality: 82 }).toBuffer(), "image/jpeg");
  const slides = { slide1: "presidents_farm_audience_2025.jpg", slide2: "forest_reserve_planting_2025.jpg", slide3: "presidents_farm_field_day_2025.jpg" };
  for (const [k, f] of Object.entries(slides)) {
    img[k] = b64(await sharp(path.join(ASSETS, f)).resize(1010, 450, { fit: "cover", position: "centre" }).jpeg({ quality: 76 }).toBuffer(), "image/jpeg");
  }

  // every photo referenced by an entry page, keyed by its file name without extension
  const keys = new Set();
  Object.values(data.entries).forEach((list) => list.forEach((e) => ((e.detail && e.detail.photos) || []).forEach((p) => keys.add(p.img))));
  for (const k of keys) {
    const cand = [path.join(SRC, "photos", k + ".jpg"), path.join(ASSETS, k + ".jpg"), path.join(ASSETS, k + ".png")].find((f) => fs.existsSync(f));
    if (!cand) { console.warn("missing photo", k); continue; }
    img[k] = b64(await sharp(cand).resize(720, 480, { fit: "cover", position: "centre" }).jpeg({ quality: 62, mozjpeg: true }).toBuffer(), "image/jpeg");
  }

  const iconSet = [fa.FaUsers, fa.FaUtensils, fa.FaHeartbeat, fa.FaBookOpen, fa.FaVenusMars, fa.FaTint, fa.FaSun, fa.FaChartLine, fa.FaIndustry,
    fa.FaEquals, fa.FaCity, fa.FaRecycle, fa.FaGlobeAsia, fa.FaFish, fa.FaTree, fa.FaBalanceScale, fa.FaHandshake];
  const icons = {};
  iconSet.forEach((C, i) => { icons[i + 1] = RDS.renderToStaticMarkup(React.createElement(C, { color: "#ffffff", "aria-hidden": "true", focusable: "false" })); });

  const json = (o) => JSON.stringify(o).replace(/</g, "\\u003c");
  const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MMSU Sustainability</title>
<meta name="description" content="Pilot of the MMSU Sustainability (SDG) site: SDG 15 Life on Land, indicator 15.1.">
<link rel="icon" href="${img.logo}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:wght@400;600;700&family=Figtree:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
${css}
</style>
</head>
<body>
<div id="app"></div>
<noscript><p style="padding:24px;font-family:sans-serif">This site needs JavaScript to show the SDG pages.</p></noscript>
<script>window.SDG_DATA=${json(data)};window.SDG_ICONS=${json(icons)};window.SDG_IMG=${json(img)};</script>
<script>
${app}
</script>
</body>
</html>
`;
  fs.writeFileSync(path.join(HERE, "index.html"), html);
  // artifact.html: same page as a fragment (no html/head/body tags) for the claude.ai artifact host
  const frag = `<title>MMSU Sustainability</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:wght@400;600;700&family=Figtree:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
${css}
</style>
<div id="app"></div>
<script>window.SDG_DATA=${json(data)};window.SDG_ICONS=${json(icons)};window.SDG_IMG=${json(img)};</script>
<script>
${app}
</script>
`;
  fs.writeFileSync(path.join(HERE, "artifact.html"), frag);
  // One-page version: same page, but the SDG 15 tile opens a single page with every entry shown in full.
  const flag = "<script>window.SDG_ALL=true;</script>\n";
  const allHtml = html.replace("<title>MMSU Sustainability</title>", "<title>MMSU SDG 15 Entries</title>")
    .replace("<script>window.SDG_DATA=", flag + "<script>window.SDG_DATA=");
  fs.writeFileSync(path.join(HERE, "all.html"), allHtml);
  const allFrag = frag.replace("<title>MMSU Sustainability</title>", "<title>MMSU SDG 15 Entries</title>")
    .replace("<script>window.SDG_DATA=", flag + "<script>window.SDG_DATA=");
  fs.writeFileSync(path.join(HERE, "artifact_all.html"), allFrag);
  console.log("wrote index.html", (html.length / 1024).toFixed(0) + " KB");
})();
