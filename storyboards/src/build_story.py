# -*- coding: utf-8 -*-
"""Neutral 'story' edition: the same activities as the indicator storyboards, told as a plain narrative of
MMSU's work on land. No reference to any ranking, submission, indicator numbering, status or gaps.
Usage: python3 -I build_story.py <html_out_dir>   then: node render.js <html_out_dir> <pdf_out_dir>"""
import os, re, sys, html
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build as b          # reuses data, frame builder and visual renderers (argv[1] = output dir)
import content as C

e = b.e

# ---------------------------------------------------------------- chapter copy
CH = {
 '15.2.1': dict(t='Events about sustainable use of land', slug='Sustainable-Land-Use-Events',
    story='Land stewardship made public: forest and farm, coast and wildlife, in events open to students, farmers and partners.',
    close='From a graduating class planting guijo and yakal, to a field day of climate-resilient rice and a wildlife photo contest, MMSU’s events invite students, farmers and communities into the care of forests, farmland, coasts and wildlife. Several are annual traditions.'),
 '15.2.2': dict(t='Sustainably farmed food on campus', slug='Food-Grown-on-Campus',
    story='Food grown on university land: a new research greenhouse and a farm that opens its harvest and technologies to partners.',
    close='A Php 2.2-million greenhouse for soilless, hydroponic and soil-based crops, trained researchers and farm workers, and a President’s Farm that shares its harvest and technologies show how MMSU produces and demonstrates food crops on its own campus.'),
 '15.2.3': dict(t='Maintaining and extending biodiversity', slug='Extending-Biodiversity',
    story='Three ecosystems, one method: raise the stock locally, plant it with partners and protect what survives: forest, food plants and mangrove.',
    close='Forest reserves, indigenous food plants, mangroves and bamboo: MMSU raises planting stock in its own nurseries, plants with partners, and keeps collections and seedbanks that schools and communities can draw on.'),
 '15.2.4': dict(t='Educating communities about ecosystems', slug='Teaching-Ecosystems',
    story='Teaching communities to grow and guard what the land holds: mangroves, indigenous trees and food plants.',
    close='Coastal towns learn mangrove propagation, Sarrat farmers learn to propagate alukon, and schools and barangays receive learning gardens: knowledge of wild flora and ecosystems goes out to the communities that live beside them.'),
 '15.2.5': dict(t='Sustainable land management for agriculture', slug='Reaching-the-Farmer',
    story='Four channels to the farmer: radio, village training, demonstration plots and on-farm practice.',
    close='Over the air to 1,000 enrollees in all 22 municipalities and cities, and in village trainings, field days and demonstration farms, MMSU carries regenerative and climate-smart farming to where farmers work.'),
 '15.2.6': dict(t='Sustainable land management for tourism', slug='Farm-Tourism',
    story='Farm tourism takes shape: rice paddy art, an approved farm-tourism model, a native-tree learning park and a protected-area communication plan.',
    close='Rice paddy art draws visitors to demonstration fields with students as guides. A farm-tourism model, a native-tree park and a role in a natural park’s communication plan point the same way: tourism built around agriculture, learning and conservation.'),
 '15.3.1': dict(t='Conserving, restoring and sustainably using land', slug='Land-Use-Policy',
    story='A written commitment to conserve, restore and protect university land, adopted in 2021 as part of Sirmata 2040.',
    close='Principles that put science before change, protect designated land from alteration and keep the Forest Reserve a no-build zone give the university’s lands a durable, written safeguard.'),
 '15.3.2': dict(t='Identifying and monitoring threatened species', slug='Threatened-Plants',
    story='Knowing what is at risk: two decades of work identifying, conserving and monitoring threatened indigenous food plants.',
    close='From a 2003 survey to a regional programme, MMSU has identified vanishing plants, kept them in a botanical garden, a genebank and community seedbanks, and brought the work into regional policy.'),
 '15.3.3': dict(t='Local biodiversity in planning and development', slug='Planning-with-Biodiversity',
    story='Biodiversity built into the 20-year land plan: protected land, a no-build forest reserve and science before construction.',
    close='Sirmata 2040 guides where and how the university grows, with protected land, a forest reserve closed to building and an assessment of natural suitability before land is altered.'),
 '15.3.5': dict(t='Collaborating for shared land ecosystems', slug='Shared-Ecosystems',
    story='Shared land, shared work: LGUs, DENR, a service club, a foundation and barangays planting and protecting together.',
    close='Mangroves in Pasuquin, Currimao and Badoc, indigenous food plant foodscapes in Vintar and San Nicolas, a bambusetum in Pinili and a seat on a park working group: MMSU works with LGUs, DENR, a foundation, a service club and barangays on land and coast they share.'),
 '15.4.1': dict(t='Protecting water on university land', slug='Protecting-Water',
    story='A duty to protect university waters, backed by a monitored aquifer on the MMSU Farm.',
    close='The Water Policy shields university waters from pollution, the pollution programme provides for registering wastewater from agro-industrial facilities, and 17 farm wells are monitored month by month.'),
 '15.4.2': dict(t='Reducing plastic waste on campus', slug='Cutting-Plastic',
    story='From a 2009 programme to a 2025 commitment: Styrofoam out, bottled water out, reusables in.',
    close='Programme rules on Styrofoam, annual no-bottled-water memoranda, requests to bring tumblers, a college-level ban, a regional commitment and student clean-ups add up to a campus habit of cutting plastic.'),
 '15.4.3': dict(t='Disposing of hazardous waste safely', slug='Hazardous-Waste',
    story='A hazardous-waste pathway from generator to accredited disposal, made explicit in a 2026 memorandum.',
    close='Registered generators, labelled and centrally stored wastes, DENR-accredited disposal and a PCB inventory with written clearance give hazardous materials a traceable path.'),
}
ORDER = list(CH)
NUM = {c: i + 1 for i, c in enumerate(ORDER)}

# ---------------------------------------------------------------- neutral wording
REPL = [(' The 2025 activities are shown in the 15.2.3 and 15.2.4 frames.', ''), (', the hook for a dated review (see the submission panel)', ''),
        (' (see the 2025 frame)', ''), (' (see the 2025 frame).', '.'), (' · date to confirm', ''), ('THE CAVEAT', 'METHOD NOTE'),
        ('Continuing implementation', 'Ongoing programme'), ('Continuing role', 'Ongoing role'), ('SDG 15 evidence page', 'SDG 15 page'),
        ('IPWMP hazardous waste pathway, as described in the compendium', 'Hazardous waste pathway under the IPWMP'),
        ('Illustrative reading of Policies 9.1, 7.1, 10.1 and 11.1 for a proposed new building', 'How Policies 9.1, 7.1, 10.1 and 11.1 apply to a new building'),
        ('more on the submission panel', 'more on the last page')]


def neu(s):
    for a, c in REPL: s = s.replace(a, c)
    return s


def clean_frames(ind):
    out = []
    for fr in b.build_frames(ind):
        if fr['kind'] == 'slot': continue
        fr['lens'] = None
        fr['kicker'] = neu(fr['kicker']); fr['tag'] = neu(fr['tag'])
        fr['beats'] = [(neu(x), neu(y)) for x, y in fr['beats']]
        fr['title'] = neu(fr['title'])
        v = fr['visual']
        if v.get('sub'): v['sub'] = neu(v['sub'])
        if v['type'] == 'none': fr['visual'] = dict(type='figpanel')
        out.append(fr)
    return out


# ---------------------------------------------------------------- patched renderers
_vis = b.visual_html


def visual_html(fr):
    if fr['visual']['type'] == 'figpanel':
        tiles = ''.join(f'<div class="ft"><b>{e(x)}</b><span>{e(y)}</span></div>' for x, y in fr['figs'])
        return f'<div class="visual"><div class="figpanel"><div class="vt">{e(fr["kicker"])}</div><div class="fts">{tiles}</div></div></div>'
    return _vis(fr)


def topbar(code, title, right, tier=None):
    chip = ''
    if tier == '2025': chip = '<span class="chip c2025">2025</span>'
    elif tier == 'cont': chip = '<span class="chip ccont">ONGOING PROGRAMME</span>'
    return f'''<header class="bar">{b.seal()}<div class="bt"><b>MMSU</b> · SDG 15 Life on Land · Storyboard</div>
      <div class="bi">Chapter <b>{NUM[code]:02d}</b> · {e(CH[code]["t"])}</div><div class="spacer"></div>{chip}<div class="bn">{e(right)}</div></header>'''


def footbar(n, N):
    return f'<footer class="pg">Mariano Marcos State University · SDG 15 Life on Land · Storyboard<span>{n} / {N}</span></footer>'


def cover(code, ind, frames, n, N):
    M = CH[code]; glance = C.IND[code]['glance']
    th = ''.join(b.thumb(f, i + 1) for i, f in enumerate(frames))
    tw = 118 if len(frames) <= 5 else 104 if len(frames) <= 7 else 92 if len(frames) <= 9 else 80
    gl = ''.join(f'<div class="fig"><b>{e(x)}</b><span>{e(y)}</span></div>' for x, y in glance)
    has_c = any(f['tier'] == 'cont' for f in frames)
    legend = '<span class="lg"><i style="background:var(--c25)"></i>2025</span>' + ('<span class="lg"><i style="background:var(--cc)"></i>Ongoing programme</span>' if has_c else '')
    return f'''<section class="page cover">
      <aside><div class="ab">{b.seal()}<div><b>Mariano Marcos State University</b><span>SDG 15 · Life on Land</span></div></div>
        <div class="big"><span>STORYBOARD · CHAPTER {NUM[code]:02d} OF {len(ORDER)}</span><h1 class="ch">{NUM[code]:02d}</h1><h3>{e(M["t"])}</h3></div>
        <div class="meta"><div>{len(frames)} frame{"s" if len(frames) != 1 else ""}</div></div>
        <img class="sdgic" src="file://{b.ASSETS}/image1.png" alt="SDG 15 Life on Land"></aside>
      <div class="cr"><div class="blk"><u>THE STORY</u><p class="sl2">{e(M["story"])}</p></div>
        <div class="blk"><u>MMSU’S COMMITMENT</u><p class="cm">{e(b.COMMIT)}</p></div>
        <div class="blk"><u>THE FILMSTRIP · {len(frames)} FRAME{"S" if len(frames) != 1 else ""} {legend}</u><div class="strip" style="--tw:{tw}px">{th}</div></div>
        <div class="blk"><u>AT A GLANCE</u><div class="figs">{gl}</div></div></div>
      {footbar(n, N)}</section>'''


def closing(code, ind, frames, n, N):
    M = CH[code]; seen = []; links = []
    for st in ind['stories']:
        for s in st['sources']:
            m = b.URL.search(s); key = m.group(0) if m else s
            if key in seen: continue
            seen.append(key); links.append((neu(b.src_short(s)), m.group(0).rstrip('>.,)') if m else None))
    rows = ''.join(f'<li><i>{i + 1}</i><div><b>{e(f["title"])}</b><span>{e(f["kicker"].split(" · ")[0][:40])}</span></div></li>' for i, f in enumerate(frames))
    li = ''.join(f'<li><span>{e(t)}</span>{f"<code>{e(u)}</code>" if u else ""}</li>' for t, u in links)
    glance = ''.join(f'<div class="fig"><b>{e(x)}</b><span>{e(y)}</span></div>' for x, y in C.IND[code]['glance'])
    two = ' two' if len(links) > 8 else ''
    return f'''<section class="page sub">{topbar(code, M["t"], "THE STORY SO FAR")}
      <div class="main sm"><div class="l"><div class="ending"><u>WHERE THE STORY LANDS</u><p>{e(M["close"])}</p><div class="figs">{glance}</div></div>
        <div class="frames{" two" if len(frames) > 5 else ""}"><u>THE FRAMES</u><ol>{rows}</ol></div></div>
        <div class="r"><div class="lk{two}"><u>SOURCES ({len(links)})</u><ol>{li}</ol></div></div></div>{footbar(n, N)}</section>'''


EXTRA = '''
.big h1.ch{font:800 120px/1 'Montserrat';color:var(--gold);letter-spacing:-.03em;margin:6px 0 10px}
.sl2{font:600 21px/1.4 'Noto Serif';color:var(--green)}
.lg{margin-left:14px;font:600 10px 'Montserrat';letter-spacing:.04em;color:var(--ink2);display:inline-flex;align-items:center;gap:5px}.lg i{width:10px;height:10px;border-radius:2px;display:inline-block}
.figpanel{flex:1;background:#fff;border:1px solid var(--grid);border-radius:8px;padding:22px;display:flex;flex-direction:column;gap:14px}
.fts{flex:1;display:flex;flex-direction:column;justify-content:center;gap:16px}
.ft{background:var(--page);border-left:5px solid var(--gold);border-radius:4px;display:flex;flex-direction:column;justify-content:center;padding:12px 20px}
.ft b{font:800 38px/1.1 'Montserrat';color:var(--green)}.ft span{font-size:14px;color:var(--muted);margin-top:3px}
.ending{background:#fff;border:1px solid var(--grid);border-top:4px solid var(--gold);border-radius:8px;padding:16px 22px;display:flex;flex-direction:column;gap:12px}
.ending p{font:600 17.5px/1.45 'Noto Serif';color:var(--green)}
.frames{background:#fff;border:1px solid var(--grid);border-radius:8px;padding:14px 20px;flex:1;min-height:0;overflow:hidden}
.frames ol{list-style:none;display:flex;flex-direction:column;gap:7px}
.frames.two ol{display:grid;grid-template-columns:1fr 1fr;gap:8px 22px;align-content:start}
.frames li{display:grid;grid-template-columns:26px 1fr;gap:10px;align-items:start}
.frames i{width:22px;height:22px;border-radius:50%;background:var(--green);color:#fff;font:800 11px/22px 'Montserrat';font-style:normal;text-align:center}
.frames b{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;font:700 11.8px/1.25 'Work Sans';color:var(--ink)}.frames span{display:block;font-size:10.5px;color:var(--muted)}
'''

if __name__ == '__main__':
    b.CSS += EXTRA
    b.visual_html = visual_html; b.topbar = topbar; b.footbar = footbar
    _ss = b.src_short; b.src_short = lambda x: neu(_ss(x))
    for code in ORDER:
        ind = next(i for i in b.data if i['code'] == code)
        if not ind['stories']: continue
        frames = clean_frames(ind); N = len(frames) + 2
        pages = [cover(code, ind, frames, 1, N)]
        pages += [b.frame_page(ind, fr, i + 1, len(frames), i + 2, N) for i, fr in enumerate(frames)]
        pages.append(closing(code, ind, frames, N, N))
        pages = [neu(p) for p in pages]
        title = f'MMSU Life on Land · Story {NUM[code]:02d} · {CH[code]["t"]}'
        doc = f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{e(title)}</title><style>{b.CSS}</style></head><body>{"".join(pages)}</body></html>'
        name = f'MMSU-LifeOnLand_Story-{NUM[code]:02d}_{CH[code]["slug"]}.html'
        open(os.path.join(b.OUT, name), 'w').write(doc); print(name, len(frames), 'frames')
