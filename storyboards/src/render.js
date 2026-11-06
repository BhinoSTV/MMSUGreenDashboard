// node render.js <html_dir> <pdf_dir>  — prints each deck to PDF with Chromium and reports overflowing pages
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
(async () => {
  const [hd, pd] = process.argv.slice(2); fs.mkdirSync(pd, { recursive: true });
  const b = await chromium.launch(); const only = process.argv[4];
  for (const f of fs.readdirSync(hd).filter(f => f.endsWith('.html') && (!only || f.includes(only))).sort()) {
    const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
    await p.goto('file://' + path.resolve(hd, f)); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(300);
    const bad = await p.evaluate(() => [...document.querySelectorAll('.page')].flatMap((pg, i) =>
      [...pg.querySelectorAll('.copy,.visual,.cr,.l,.r,.vpanel,.cmt,.lk,.srcs,.cover aside')].filter(el => el.scrollHeight > el.clientHeight + 2 || el.scrollWidth > el.clientWidth + 2)
        .map(el => `p${i + 1}:${el.className.split(' ')[0] || el.tagName}(+${el.scrollHeight - el.clientHeight})`)));
    await p.pdf({ path: path.join(pd, f.replace('.html', '.pdf')), width: '1280px', height: '720px', printBackground: true, preferCSSPageSize: true });
    console.log(f, bad.length ? 'OVERFLOW ' + bad.join(' ') : 'ok'); await p.close();
  }
  await b.close();
})();
