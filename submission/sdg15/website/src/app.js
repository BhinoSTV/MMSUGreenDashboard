(function () {
  "use strict";
  var D = window.SDG_DATA, ICONS = window.SDG_ICONS, IMG = window.SDG_IMG;
  var STORE = "mmsu-sdg15-entries-v1";
  var GOALS = [
    ["No Poverty", "#E5243B"], ["Zero Hunger", "#DDA63A"], ["Good Health and Well-Being", "#4C9F38"],
    ["Quality Education", "#C5192D"], ["Gender Equality", "#FF3A21"], ["Clean Water and Sanitation", "#26BDE2"],
    ["Affordable and Clean Energy", "#FCC30B"], ["Decent Work and Economic Growth", "#A21942"],
    ["Industry, Innovation and Infrastructure", "#FD6925"], ["Reduced Inequalities", "#DD1367"],
    ["Sustainable Cities and Communities", "#FD9D24"], ["Responsible Consumption and Production", "#BF8B2E"],
    ["Climate Action", "#3F7E44"], ["Life Below Water", "#0A97D9"], ["Life on Land", "#56C02B"],
    ["Peace, Justice and Strong Institutions", "#00689D"], ["Partnerships for the Goals", "#19486A"]
  ];
  var SLIDES = [
    { img: "slide1", cap: "Education for Sustainable Development" },
    { img: "slide2", cap: "Life on Land: planting native trees in the University Forest Reserves" },
    { img: "slide3", cap: "Extension that reaches farmers: the President's Farm Field Day" }
  ];
  var ALL = []; D.metrics.forEach(function (m) { m.indicators.forEach(function (i) { i.metric = m; ALL.push(i); }); });
  var byCode = {}; ALL.forEach(function (i) { byCode[i.code] = i; });
  var view = { q: "", type: "All" };

  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function safeUrl(u) { return /^https?:\/\//i.test(u || "") ? u : ""; }
  function loadLocal() { try { return JSON.parse(localStorage.getItem(STORE) || "{}") || {}; } catch (e) { return {}; } }
  function saveLocal(o) { try { localStorage.setItem(STORE, JSON.stringify(o)); return true; } catch (e) { return false; } }
  function entriesFor(code) {
    var base = (D.entries[code] || []).map(function (e) { return Object.assign({}, e, { local: false }); });
    var loc = (loadLocal()[code] || []).map(function (e) { return Object.assign({}, e, { local: true }); });
    return loc.concat(base);
  }
  function groupLabel(e) { return e.years === "Ongoing" ? "Ongoing" : String(e.sortYear); }
  function sorted(list) { return list.slice().sort(function (a, b) { return (b.sortYear || 0) - (a.sortYear || 0); }); }

  /* ---------- shell ---------- */
  var app = document.getElementById("app");
  app.innerHTML =
    '<a class="skip" href="#main">Skip to content</a>' +
    '<div class="govbar"><div class="in"><a class="gov" href="https://www.gov.ph" target="_blank" rel="noopener">GOV.PH</a>' +
    '<ul><li><a href="https://www.mmsu.edu.ph/about/philippine-transparency-seal" target="_blank" rel="noopener">Transparency</a></li>' +
    '<li><a href="https://www.mmsu.edu.ph" target="_blank" rel="noopener">Quality Assurance</a></li>' +
    '<li><a href="https://www.mmsu.edu.ph" target="_blank" rel="noopener">Citizen\'s Charter</a></li></ul>' +
    '<span style="display:flex;align-items:center;gap:14px"><span class="clock" id="clock"></span>' +
    '<button class="search" aria-label="Search (not active in the pilot)" title="Search (not active in the pilot)"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5 21 21"/></svg></button></span></div></div>' +
    '<header class="ident"><a href="#/"><img src="' + IMG.logo + '" alt="MMSU seal"><h1>Mariano Marcos<br>State University</h1></a></header>' +
    '<nav class="mainnav" aria-label="MMSU main"><ul>' +
    ["Home", "University", "Academic", "Research", "Extension", "Global Affairs", "News", "E-Services", "Downloads"].map(function (n) {
      return '<li><a href="https://www.mmsu.edu.ph" target="_blank" rel="noopener">' + n + '</a></li>';
    }).join("") + '</ul></nav>' +
    '<div class="shell"><aside class="side" id="side" aria-label="Sustainability menu"></aside><main class="main" id="main" tabindex="-1"></main></div>' +
    '<footer class="foot"><div class="in">' +
    '<div class="id"><img src="' + IMG.logo + '" alt=""><h2>Mariano Marcos<br>State University</h2><p>Brgy. 16-S Quiling Sur, City of Batac<br>Ilocos Norte, Philippines 2906</p><p>op@mmsu.edu.ph<br>(63)(077) 600 1234</p></div>' +
    '<div><h3>Quick Links</h3><div class="cols">' +
    ["MMSU Citizen's Charter", "Privacy Notice", "Opportunities", "Downloads", "Library", "Document Tracking", "Publication", "Procurement", "MCAT", "Students Portal", "MVLE", "Alumni", "Brand Standards"].map(function (n) {
      return '<a href="https://www.mmsu.edu.ph" target="_blank" rel="noopener">' + esc(n) + '</a>';
    }).join("") + '</div></div>' +
    '<div class="legal">' + ["MFO Accountability Report Card (MARC-I)", "Management Accountability Report Card (MARC-II)", "MMSU Freedom of Information Manual", "MMSU Equal Opportunity Policy", "MMSU Code of Conduct and Discipline", "Data Privacy Manual", "MMSU Sirmata 2040 Land Use Development and Infrastructure Plan"].map(function (n) {
      return '<a href="https://www.mmsu.edu.ph" target="_blank" rel="noopener">' + esc(n) + '</a>';
    }).join("") + '</div></div>' +
    '<div class="bar">Pilot of the MMSU Sustainability (SDG) site. Entries marked "Added locally" are stored only in this browser until exported.</div></footer>';

  var side = document.getElementById("side"), main = document.getElementById("main");

  function tick() {
    var d = new Date();
    document.getElementById("clock").textContent =
      d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) + "  " +
      d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: true });
  }
  tick(); setInterval(tick, 1000);

  /* ---------- sidebars ---------- */
  function sideHome() {
    var items = [["Home", "#/", true], ["Sustainability & Futures Thinking Directorate", "https://www.mmsu.edu.ph", false], ["Roadmap", "https://www.mmsu.edu.ph", false],
      ["Activities", "https://www.mmsu.edu.ph", false], ["Reports", "https://www.mmsu.edu.ph", false], ["ESG Metrics", "https://www.mmsu.edu.ph", false], ["MMSU Facts and Figures", "https://www.mmsu.edu.ph", false]];
    side.innerHTML = '<div class="brand"><img src="' + IMG.wheel + '" alt="Sustainable Development Goals wheel"><h2>MMSU Sustainability</h2></div><ul>' +
      items.map(function (it) {
        return '<li><a href="' + it[1] + '"' + (it[2] ? ' aria-current="page"' : ' target="_blank" rel="noopener"') + '>' + esc(it[0]) + '</a></li>';
      }).join("") + '</ul>' +
      '<div class="contact"><h3>Contact Us</h3><p>Sustainability &amp; Futures Thinking Directorate</p><p>Brgy. 16-S Quiling Sur, City of Batac, Ilocos Norte 2906</p><p>op@mmsu.edu.ph<br>(63)(077) 600 1234</p></div>';
  }
  function sideSdg(active) {
    var li = '<li><a href="#/">Home</a></li>';
    for (var n = 1; n <= 17; n++) li += '<li><a href="#/sdg/' + n + '"' + (n === active ? ' aria-current="page"' : "") + '>SDG ' + n + '</a></li>';
    side.innerHTML = '<div class="brand"><img src="' + IMG.wheel + '" alt="Sustainable Development Goals wheel"><h2>Sustainable Development Goals</h2></div><ul>' + li + '</ul>';
  }

  /* ---------- views ---------- */
  var timer = null, slide = 0;
  function viewHome() {
    document.title = "MMSU Sustainability";
    sideHome();
    main.className = "main";
    main.innerHTML =
      '<section class="carousel" aria-roledescription="carousel" aria-label="Sustainability highlights">' +
      SLIDES.map(function (s, i) { return '<figure class="slide' + (i ? "" : " on") + '"><img src="' + IMG[s.img] + '" alt="' + esc(s.cap) + '"><figcaption>' + esc(s.cap) + '</figcaption></figure>'; }).join("") +
      '<button class="prev" aria-label="Previous slide">&#8249;</button><button class="next" aria-label="Next slide">&#8250;</button></section>' +
      '<h2 class="goals-title">Sustainable Development Goals</h2><nav class="goals" aria-label="Sustainable Development Goals">' +
      GOALS.map(function (g, i) {
        var n = i + 1, live = n === D.sdg.number;
        return '<a class="goal' + (live ? " live" : "") + '" href="#/sdg/' + n + '" style="background:' + g[1] + '" aria-label="SDG ' + n + ': ' + esc(g[0]) + (live ? " (pilot)" : "") + '">' +
          '<span class="n">' + n + '</span><span class="l' + (n > 9 ? " two" : "") + '">' + esc(g[0]) + '</span>' + (ICONS[n] || "") + '</a>';
      }).join("") + '</nav>';
    var slides = main.querySelectorAll(".slide");
    function show(k) { slide = (k + slides.length) % slides.length; slides.forEach(function (s, i) { s.classList.toggle("on", i === slide); }); }
    main.querySelector(".prev").onclick = function () { show(slide - 1); };
    main.querySelector(".next").onclick = function () { show(slide + 1); };
    var car = main.querySelector(".carousel");
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!reduce) {
      var start = function () { stop(); timer = setInterval(function () { show(slide + 1); }, 6500); };
      var stop = function () { if (timer) { clearInterval(timer); timer = null; } };
      car.addEventListener("mouseenter", stop); car.addEventListener("mouseleave", start);
      car.addEventListener("focusin", stop); car.addEventListener("focusout", start); start();
    }
  }

  function count(code) { return entriesFor(code).length; }
  function viewSdg(n) {
    sideSdg(n);
    if (n !== D.sdg.number) {
      document.title = "SDG " + n + " | MMSU Sustainability";
      main.className = "main";
      main.innerHTML = '<div class="crumbs"><a href="#/">Home</a> / SDG ' + n + '</div><h2 style="font-family:var(--serif);font-size:32px;color:var(--green);margin:0 0 10px">SDG ' + n + ': ' + esc(GOALS[n - 1][0]) + '</h2><div class="empty">This pilot covers SDG 15 (Life on Land), indicator 15.1 only. <a href="#/sdg/15" style="color:var(--green);font-weight:700">Open SDG 15</a>.</div>';
      return;
    }
    document.title = "MMSU on Life on Land | MMSU Sustainability";
    main.className = "main with-toc";
    var toc = D.metrics.map(function (m) { return '<li><a href="#m' + m.code.replace(".", "-") + '" title="' + esc(m.heading) + '">' + esc(m.code + " " + (m.short || m.heading)) + '</a></li>'; }).join("");
    var secs = D.metrics.map(function (m, k) {
      return '<section class="section" id="m' + m.code.replace(".", "-") + '"><h2 class="sec">' + esc(m.group) + '</h2><ul class="ind">' +
        m.indicators.map(function (i) {
          var c = count(i.code);
          return '<li><span class="code">' + esc(i.code) + '</span><a href="#/sdg/15/' + i.code + '">' + esc(i.title) + '</a>' +
            '<span class="pill ' + (c ? "have" : "none") + '">' + (c ? c + (c === 1 ? " entry" : " entries") : "No entries yet") + '</span></li>';
        }).join("") + '</ul></section>';
    }).join("");
    main.innerHTML = '<div><div class="sdghead"><img src="' + IMG.sdg15 + '" alt="SDG 15 Life on Land"><div style="flex:1;min-width:260px"><h2>MMSU on Life on Land</h2><h3>MMSU\'s Commitment</h3><p>' + esc(D.sdg.commitment) + '</p></div></div>' + secs + '</div>' +
      '<nav class="toc" aria-label="On this page"><h2>On this page</h2><ul><li><a href="#top-commit" onclick="window.scrollTo(0,0);return false">MMSU\'s Commitment</a></li>' + toc + '</ul></nav>';
  }

  function viewIndicator(code) {
    var ind = byCode[code];
    sideSdg(15);
    if (!ind) { main.className = "main"; main.innerHTML = '<div class="empty">Indicator not found. <a href="#/sdg/15">Back to SDG 15</a></div>'; return; }
    document.title = code + " " + ind.title + " | MMSU Sustainability";
    main.className = "main with-toc";
    view = { q: "", type: "All" };
    main.innerHTML = '<div><div class="crumbs"><a href="#/">Home</a> / <a href="#/sdg/15">SDG 15</a> / ' + esc(code) + '</div>' +
      '<div class="indhead" id="overview"><h2><span class="code">' + esc(code) + '</span>' + esc(ind.title) + '</h2><p>' + esc(ind.question) + '</p></div>' +
      (ind.note ? '<div class="infobox"><b>How this indicator is scored.</b> ' + esc(ind.note) + '</div>' : '') +
      (code === "15.1" ? '' : '<div class="infobox"><b>Pilot.</b> Only indicator 15.1 is filled in this pilot. You can already add an entry here; it is saved in this browser and can be exported.</div>') +
      '<div class="tools" id="entries"><input type="search" id="q" placeholder="Search entries" aria-label="Search entries"><div class="chips" id="chips"></div>' +
      '<span style="flex:1"></span><button class="btn" id="add">+ Add entry</button><button class="btn alt" id="export">Export added entries</button></div>' +
      '<div class="count" id="count" aria-live="polite"></div><div id="list"></div></div>' +
      '<nav class="toc" aria-label="On this page"><h2>On this page</h2><ul><li><a href="#overview" onclick="document.getElementById(\'overview\').scrollIntoView();return false">Overview</a></li><li><a href="#entries" onclick="document.getElementById(\'entries\').scrollIntoView();return false">Entries</a></li></ul></nav>';
    document.getElementById("q").addEventListener("input", function (e) { view.q = e.target.value; renderList(code); });
    document.getElementById("add").onclick = function () { openForm(code); };
    document.getElementById("export").onclick = function () { exportLocal(); };
    renderList(code);
  }

  function renderList(code) {
    var all = entriesFor(code);
    var types = ["All"]; all.forEach(function (e) { if (types.indexOf(e.type) < 0) types.push(e.type); });
    if (types.indexOf(view.type) < 0) view.type = "All";
    var chips = document.getElementById("chips");
    chips.innerHTML = types.map(function (t) { return '<button class="chip" aria-pressed="' + (t === view.type) + '" data-t="' + esc(t) + '">' + esc(t) + '</button>'; }).join("");
    Array.prototype.forEach.call(chips.querySelectorAll(".chip"), function (b) { b.onclick = function () { view.type = b.getAttribute("data-t"); renderList(code); }; });
    var q = view.q.trim().toLowerCase();
    var list = sorted(all.filter(function (e) {
      if (view.type !== "All" && e.type !== view.type) return false;
      if (!q) return true;
      return [e.title, e.people, e.summary, e.type, e.years].join(" ").toLowerCase().indexOf(q) >= 0;
    }));
    document.getElementById("count").textContent = list.length + (list.length === 1 ? " entry" : " entries") + (all.length !== list.length ? " of " + all.length : "");
    var host = document.getElementById("list");
    if (!list.length) {
      host.innerHTML = '<div class="empty">' + (all.length ? "No entries match your search." : "No entries yet for this indicator. Use \"Add entry\" to insert the first one.") + '</div>';
      return;
    }
    var html = "", last = null;
    list.forEach(function (e) {
      var g = groupLabel(e);
      if (g !== last) { html += '<h3 class="yearhead">' + esc(g) + '</h3>'; last = g; }
      var url = safeUrl(e.sourceUrl);
      html += '<article class="entry"><div class="yr">' + esc(e.years) + '<small>' + esc(e.type) + '</small></div><div>' +
        '<h3>' + (url ? '<a href="' + esc(url) + '" target="_blank" rel="noopener">' + esc(e.title) + '</a>' : esc(e.title)) + '</h3>' +
        (e.people ? '<div class="meta">' + esc(e.people) + '</div>' : '') +
        (e.summary ? '<p>' + esc(e.summary) + '</p>' : '') +
        '<div class="tags">' + (e.status ? '<span class="tag ' + (/^Verified/.test(e.status) ? "ok" : "warn") + '">' + esc(e.status) + '</span>' : '') +
        (e.local ? '<span class="tag local">Added locally</span>' : '') +
        (e.note ? '<span class="tag">' + esc(e.note) + '</span>' : '') +
        (url ? '<span class="src">Source: <a href="' + esc(url) + '" target="_blank" rel="noopener">' + esc(e.sourceLabel || url) + '</a></span>' : '') +
        (e.local ? '<button class="rm" data-id="' + esc(e.id) + '">Remove</button>' : '') + '</div></div></article>';
    });
    host.innerHTML = html;
    Array.prototype.forEach.call(host.querySelectorAll(".rm"), function (b) {
      b.onclick = function () {
        var o = loadLocal(); o[code] = (o[code] || []).filter(function (e) { return e.id !== b.getAttribute("data-id"); });
        saveLocal(o); renderList(code); toast("Entry removed");
      };
    });
  }

  /* ---------- add / export ---------- */
  var dlg = document.createElement("dialog"); dlg.setAttribute("aria-labelledby", "dlgt");
  dlg.innerHTML = '<form id="f" novalidate><h2 id="dlgt">Add an entry</h2><p class="hint" id="dlgh"></p>' +
    '<label for="f-title">Title *</label><input id="f-title" required>' +
    '<div class="row"><div><label for="f-years">Year or period *</label><input id="f-years" placeholder="2025 or 2024 to 2026" required></div>' +
    '<div><label for="f-type">Type</label><select id="f-type"><option>Activity</option><option>Policy</option><option>Memorandum</option><option>Publication</option><option>Research project</option><option>Study</option><option>Award</option><option>News</option><option>Other</option></select></div></div>' +
    '<label for="f-people">People or unit</label><input id="f-people">' +
    '<label for="f-summary">Description</label><textarea id="f-summary"></textarea>' +
    '<div class="row"><div><label for="f-label">Source name</label><input id="f-label" placeholder="MMSU News, 4 July 2025"></div><div><label for="f-url">Source link (https://)</label><input id="f-url" type="url" placeholder="https://"></div></div>' +
    '<label for="f-status">Verification</label><select id="f-status"><option>Verified on the source page</option><option>Search summary only</option><option>To verify</option></select>' +
    '<p class="hint" id="f-err" role="alert" style="color:#a11;margin-top:12px"></p>' +
    '<div class="actions"><button type="button" class="btn alt" id="f-cancel">Cancel</button><button type="submit" class="btn">Save entry</button></div></form>';
  document.body.appendChild(dlg);
  var curCode = null;
  function openForm(code) {
    curCode = code;
    document.getElementById("f").reset(); document.getElementById("f-err").textContent = "";
    document.getElementById("dlgh").textContent = "Indicator " + code + " · " + byCode[code].title + ". Saved in this browser; export to share.";
    if (dlg.showModal) dlg.showModal(); else dlg.setAttribute("open", "");
    document.getElementById("f-title").focus();
  }
  document.getElementById("f-cancel").onclick = function () { dlg.close(); };
  document.getElementById("f").addEventListener("submit", function (ev) {
    ev.preventDefault();
    var v = function (id) { return document.getElementById(id).value.trim(); };
    var err = document.getElementById("f-err");
    if (!v("f-title") || !v("f-years")) { err.textContent = "Title and year are required."; return; }
    if (v("f-url") && !safeUrl(v("f-url"))) { err.textContent = "The source link must start with http:// or https://."; return; }
    var m = v("f-years").match(/(19|20)\d{2}/g);
    var entry = { id: "l" + Date.now(), years: v("f-years"), sortYear: m ? +m[m.length - 1] : new Date().getFullYear(), type: v("f-type"), title: v("f-title"),
      people: v("f-people"), summary: v("f-summary"), sourceLabel: v("f-label"), sourceUrl: v("f-url"), status: v("f-status") };
    var o = loadLocal(); (o[curCode] = o[curCode] || []).push(entry);
    if (!saveLocal(o)) { err.textContent = "This browser blocked saving. Use a normal window, or export is unavailable."; return; }
    dlg.close(); renderList(curCode); toast("Entry added to " + curCode);
  });
  function exportLocal() {
    var o = loadLocal(), n = 0; Object.keys(o).forEach(function (k) { n += o[k].length; });
    if (!n) { toast("No added entries to export yet"); return; }
    var blob = new Blob([JSON.stringify({ entries: o }, null, 2)], { type: "application/json" });
    var a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "sdg15-added-entries.json";
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(function () { URL.revokeObjectURL(a.href); }, 500);
  }
  function toast(msg) {
    var t = document.createElement("div"); t.className = "toast"; t.setAttribute("role", "status"); t.textContent = msg;
    document.body.appendChild(t); setTimeout(function () { t.remove(); }, 2400);
  }

  /* ---------- router ---------- */
  function route() {
    if (timer) { clearInterval(timer); timer = null; }
    var h = (location.hash || "#/").replace(/^#/, "");
    var p = h.split("/").filter(Boolean);
    if (p[0] === "sdg" && p[1]) {
      var n = parseInt(p[1], 10);
      if (n >= 1 && n <= 17) { if (p[2]) viewIndicator(p[2]); else viewSdg(n); window.scrollTo(0, 0); return; }
    }
    if (h && h !== "/" && h.charAt(0) === "m") return; /* in-page anchor on the SDG page */
    viewHome(); window.scrollTo(0, 0);
  }
  window.addEventListener("hashchange", route);
  route();
})();
