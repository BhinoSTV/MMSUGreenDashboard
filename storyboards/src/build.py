# -*- coding: utf-8 -*-
"""Build one storyboard deck (HTML, 1280x720 pages) per SDG 15 indicator from data.json + content.py.
Usage: python3 -I build.py <html_out_dir>      then: node render.js <html_out_dir> <pdf_out_dir>"""
import json, os, re, sys, html
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content as C

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, 'assets')
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
data = json.load(open(os.path.join(HERE, 'data.json')))
e = lambda s: html.escape(str(s), quote=True)
URL = re.compile(r'https?://\S+')

STATUS_COL = {'2025 evidence': '#146622', 'Continuing only': '#2a78d6', 'Draft': '#b97a00', 'No entry yet': '#c9432c'}
COMMIT = 'Take an active role in protecting and promoting sustainable use of terrestrial ecosystems, responsible land use, and biodiversity conservation.'

CSS = open(os.path.join(HERE, 'style.css')).read().replace('{{ASSETS}}', 'file://' + ASSETS)


def img_info(fn):
    im = Image.open(os.path.join(ASSETS, fn)); return im.size


def is_doc(cap):
    return cap.startswith(('Document:', 'Capture:'))


def src_short(s):
    return URL.sub('', s).strip().rstrip('<>').strip()


# ---------------------------------------------------------------------------- frames
def build_frames(ind):
    code = ind['code']; frames = []
    meta = C.IND[code]
    for g in meta.get('gap', []):
        frames.append(dict(kind='slot', label=g['label'], text=g['text'], hint=g['hint'], tier='gap'))
    for st in ind['stories']:
        k = C.skey(st['title']); tier = 'cont' if st['section'] == 'continuing' else '2025'
        lens = C.L.get(code, {}).get(k)
        for i, fr in enumerate(C.F[k]):
            imgs = st['images']
            if 'img' in fr: imgs = [imgs[j] for j in fr['img'] if j < len(imgs)]
            visual = fr.get('visual') or dict(type='images' if imgs else 'none', hint='Add a photo or document scan.')
            frames.append(dict(kind='story', key=k, title=fr.get('title', st['title']), kicker=fr['kicker'], beats=fr['beats'], figs=fr.get('figs', []),
                               images=imgs, visual=visual, tier=tier, tag=st['tag'], sources=st['sources'],
                               lens=lens if i == 0 else None, part=(i + 1, len(C.F[k]))))
    return frames


# ---------------------------------------------------------------------------- pieces
def seal():
    return f'<img class="seal" src="file://{ASSETS}/seal.png" alt="">'


def topbar(code, title, right, tier=None):
    chip = ''
    if tier == '2025': chip = '<span class="chip c2025">2025 EVIDENCE</span>'
    elif tier == 'cont': chip = '<span class="chip ccont">CONTINUING IMPLEMENTATION</span>'
    elif tier == 'gap': chip = '<span class="chip cgap">EVIDENCE NEEDED</span>'
    return f'''<header class="bar">{seal()}<div class="bt"><b>MMSU</b> · SDG 15 Life on Land · Storyboard</div>
      <div class="bi">Indicator <b>{e(code)}</b></div><div class="spacer"></div>{chip}<div class="bn">{e(right)}</div></header>'''


def footbar(n, N):
    return f'<footer class="pg">Mariano Marcos State University · THE Impact Rankings 2027 · SDG 15 · Evidence year 2025<span>{n} / {N}</span></footer>'


def visual_html(fr):
    v = fr['visual']; t = v['type']
    if t == 'images':
        imgs = fr['images']; figs = []
        landscape = all(img_info(i['file'])[0] / img_info(i['file'])[1] > 1.1 for i in imgs)
        for im in imgs:
            w, h = img_info(im['file']); doc = is_doc(im['caption'])
            fit = 'contain'
            if not doc and len(imgs) == 1 and w / h > 1.2: fit = 'cover' if (w / h) < 1.75 else 'contain'
            figs.append(f'<figure class="{"doc" if doc else ""}"><div class="ib"><img class="{fit}" src="file://{ASSETS}/{im["file"]}" alt=""></div><figcaption>{e(im["caption"])}</figcaption></figure>')
        cls = 'stack' if (len(imgs) == 1 or landscape) else 'row'
        return f'<div class="visual {cls}">{"".join(figs)}</div>'
    if t == 'none':
        return f'<div class="visual"><div class="nophoto"><div class="np-ic">▣</div><b>VISUAL NEEDED</b><p>{e(v.get("hint", ""))}</p></div></div>'
    if t == 'timeline':
        rows = ''.join(f'<li class="{"hl" if h else ""}"><span class="d">{e(d)}</span><span class="x">{e(x)}</span></li>' for d, x, h in v['items'])
        return f'<div class="visual"><div class="vpanel"><div class="vt">TIMELINE · HOW THE POLICY BUILT UP</div><ol class="tl">{rows}</ol></div></div>'
    if t == 'steps':
        rows = ''.join(f'<li><span class="n">{i + 1}</span><div><b>{e(a)}</b><span>{e(b)}</span></div></li>' for i, (a, b) in enumerate(v['items']))
        return f'<div class="visual"><div class="vpanel"><div class="vt">{e(v.get("sub", "PROCESS"))}</div><ol class="steps">{rows}</ol></div></div>'
    if t == 'quotes':
        rows = ''.join(f'<blockquote><span>{e(a)}</span>{e(b)}</blockquote>' for a, b in v['items'])
        return f'<div class="visual"><div class="vpanel quotes"><div class="vt">IN THE POLICY’S OWN WORDS</div>{rows}</div></div>'
    if t == 'funnel':
        mx = max(x[1] for x in v['items'])
        rows = ''.join(f'<div class="fr {x[2] or ""}"><div class="fl">{e(x[0])}</div><div class="fb"><i style="width:{x[1] / mx * 100:.0f}%"></i><b>{x[1]}</b></div></div>' for x in v['items'])
        return f'<div class="visual"><div class="vpanel"><div class="vt">{e(v["sub"])}</div>{rows}</div></div>'
    raise ValueError(t)


def frame_page(ind, fr, num, total_frames, n, N):
    code = ind['code']
    if fr['kind'] == 'slot':
        vis = f'<div class="visual"><div class="slot"><div class="plus">+</div><b>{e(fr["label"])}</b><p>{e(fr["text"])}</p></div></div>'
        copy = f'''<div class="kick">Frame to be produced</div><h2>{e(fr["text"])}</h2>
          <div class="beats"><div class="beat"><i>1</i><div><u>WHY IT IS MISSING</u><p>{e(ind["note"] or "No item yet.")}</p></div></div>
          <div class="beat"><i>2</i><div><u>WHAT IT MUST SHOW</u><p>{e(fr["hint"])}</p></div></div></div>'''
        tier = 'gap'; srcs = '<b>Sources:</b> none yet'
    else:
        vis = visual_html(fr)
        beats = ''.join(f'<div class="beat"><i>{i + 1}</i><div><u>{e(a)}</u><p>{e(b)}</p></div></div>' for i, (a, b) in enumerate(fr['beats']))
        figs = ''.join(f'<div class="fig"><b>{e(a)}</b><span>{e(b)}</span></div>' for a, b in fr['figs'])
        figs = f'<div class="figs">{figs}</div>' if figs else ''
        lens = f'<div class="lens"><u>LENS FOR {e(code)}</u>{e(fr["lens"])}</div>' if fr['lens'] else ''
        tag = f'<div class="tag">{e(fr["tag"])}</div>' if fr['tag'] and fr['tier'] == 'cont' else ''
        part = f' <span class="part">part {fr["part"][0]} of {fr["part"][1]}</span>' if fr['part'][1] > 1 else ''
        copy = f'<div class="kick">{e(fr["kicker"])}{part}</div><h2>{e(fr["title"])}</h2>{tag}<div class="beats">{beats}</div>{figs}{lens}'
        tier = fr['tier']
        ss = [src_short(s) for s in fr['sources']]
        extra = f' <i>+{len(ss) - 3} more on the submission panel</i>' if len(ss) > 3 else ''
        srcs = '<b>Source:</b> ' + ' · '.join(e(s) for s in ss[:3]) + extra
    dense = ' dense' if (fr['kind'] == 'story' and sum(len(b[1]) for b in fr['beats']) + len(fr['title']) > 640) else ''
    return f'''<section class="page frame t-{tier}{dense}">{topbar(code, ind["title"], f"FRAME {num} / {total_frames}", tier)}
      <div class="main">{vis}<div class="copy">{copy}</div></div><div class="srcs">{srcs}</div>{footbar(n, N)}</section>'''


def thumb(fr, num):
    if fr['kind'] == 'story' and fr['images']:
        im = fr['images'][0]; c = 'doc' if is_doc(im['caption']) else ''
        inner = f'<img class="{c}" src="file://{ASSETS}/{im["file"]}" alt="">'
    elif fr['kind'] == 'story' and fr['visual']['type'] in ('timeline', 'steps', 'quotes', 'funnel'):
        inner = f'<div class="tx">{fr["visual"]["type"].upper()}</div>'
    elif fr['kind'] == 'slot':
        inner = '<div class="tx plus2">+</div>'
    else:
        inner = '<div class="tx">NO PHOTO</div>'
    return f'<div class="th t-{fr["tier"]}"><div class="ti">{inner}</div><span>{num}</span></div>'


def cover_page(ind, frames, n, N):
    code = ind['code']; M = C.IND[code]; col = STATUS_COL[ind['status']]
    th = ''.join(thumb(f, i + 1) for i, f in enumerate(frames))
    tw = 118 if len(frames) <= 5 else 104 if len(frames) <= 7 else 92 if len(frames) <= 9 else 80
    note = f'<div class="note" style="border-color:{col}"><u style="color:{col}">COMPENDIUM NOTE · {e(ind["status"]).upper()}</u>{e(ind["note"])}</div>' if ind['note'] else \
        f'<div class="note" style="border-color:{col}"><u style="color:{col}">{e(ind["status"]).upper()}</u>{e(C.STATUS_NOTE[ind["status"]])}</div>'
    glance = ''.join(f'<div class="fig"><b>{e(a)}</b><span>{e(b)}</span></div>' for a, b in M['glance'])
    n25 = sum(1 for f in frames if f['tier'] == '2025'); nc = sum(1 for f in frames if f['tier'] == 'cont'); ng = sum(1 for f in frames if f['tier'] == 'gap')
    mix = f'{n25} × 2025 evidence' + (f' · {nc} × continuing' if nc else '') + (f' · {ng} × to be produced' if ng else '')
    return f'''<section class="page cover">
      <aside><div class="ab">{seal()}<div><b>Mariano Marcos State University</b><span>THE Impact Rankings 2027 · SDG 15 Life on Land</span></div></div>
        <div class="big"><span>STORYBOARD · INDICATOR</span><h1>{e(code)}</h1><h3>{e(ind["title"])}</h3>
        <div class="badge" style="background:{col}">{e(ind["status"]).upper()}</div></div>
        <div class="meta"><div>Evidence year <b>2025</b></div><div>Data submission due <b>9 Nov 2026</b></div><div>{e(mix)}</div></div>
        <img class="sdgic" src="file://{ASSETS}/image1.png" alt="SDG 15 Life on Land"></aside>
      <div class="cr"><div class="blk"><u>THE ASKS</u><p class="q">{e(ind["wording"])}</p></div>
        <div class="blk"><u>MMSU’S COMMITMENT</u><p class="cm">{e(COMMIT)}</p></div>
        <div class="blk"><u>STORYLINE</u><p class="sl">{e(M["story"])}</p></div>
        {note}
        <div class="blk"><u>THE FILMSTRIP · {len(frames)} FRAME{"S" if len(frames) != 1 else ""}</u><div class="strip" style="--tw:{tw}px">{th}</div></div>
        <div class="blk"><u>AT A GLANCE</u><div class="figs">{glance}</div></div></div>
      {footbar(n, N)}</section>'''


def submission_page(ind, frames, n, N):
    code = ind['code']; M = C.IND[code]; col = STATUS_COL[ind['status']]
    seen = []; links = []
    for st in ind['stories']:
        for s in st['sources']:
            m = URL.search(s); key = m.group(0) if m else s
            if key in seen: continue
            seen.append(key); links.append((src_short(s), m.group(0).rstrip('>.,)') if m else None))
    li = ''.join(f'<li><span>{e(t)}</span>{f"<code>{e(u)}</code>" if u else "<code class=nolink>no public link yet</code>"}</li>' for t, u in links) or '<li><span>No sources yet.</span></li>'
    cf = ''.join(f'<li>{e(x)}</li>' for x in M['confirm'] + C.COMMON_CONFIRM)
    pol = ''
    if 'policy' in M:
        pol = f'<div class="pol"><u>POLICY YEARS (THE FORM ASKS FOR BOTH)</u><div><b>Created (yyyy)</b>{e(M["policy"]["created"])}</div><div><b>Reviewed (yyyy)</b>{e(M["policy"]["reviewed"])}</div></div>'
    cm = M['comment']
    return f'''<section class="page sub">{topbar(code, ind["title"], "SUBMISSION PANEL")}
      <div class="main sm"><div class="l">
        <div class="ans"><u>RECOMMENDED ANSWER ON THE THE FORM</u><b style="color:{col}">{e(M["answer"])}</b><span class="badge" style="background:{col}">{e(ind["status"]).upper()}</span></div>
        <div class="cmt"><u>DRAFT COMMENT <em>{len(cm):,} / 1,000 characters</em></u><p>{e(cm)}</p></div>{pol}</div>
        <div class="r"><div class="cf"><u>BEFORE YOU SUBMIT</u><ul>{cf}</ul></div>
        <div class="lk{" two" if len(links) > 8 else ""}"><u>EVIDENCE LINKS ({len(links)})</u><ol>{li}</ol></div></div></div>{footbar(n, N)}</section>'''


def deck(ind):
    frames = build_frames(ind); N = len(frames) + 2
    pages = [cover_page(ind, frames, 1, N)]
    for i, fr in enumerate(frames): pages.append(frame_page(ind, fr, i + 1, len(frames), i + 2, N))
    pages.append(submission_page(ind, frames, N, N))
    title = f'SDG {ind["code"]} Storyboard · MMSU'
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{e(title)}</title><style>{CSS}</style></head><body>{"".join(pages)}</body></html>', len(frames)


if __name__ == '__main__':
    for ind in data:
        h, n = deck(ind)
        open(os.path.join(OUT, f'SDG-{ind["code"]}_Storyboard.html'), 'w').write(h)
        print(ind['code'], n, 'frames')
