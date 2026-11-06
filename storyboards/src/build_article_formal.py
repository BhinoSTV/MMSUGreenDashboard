# -*- coding: utf-8 -*-
"""Formal typographic edition of the article format. Same content, cover, footer, page set-up and typeface (Arial)
as the MMSU template; only sizes, spacing, alignment and some colours are refined.
Usage: python3 -I build_article_formal.py <template.docx> <out_dir>"""
import copy, os, re, sys
from xml.sax.saxutils import escape
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_article as A      # content, helpers (also imports build_report as R)
from intro import INTRO        # opening statements: answers of at most 1,000 characters
import build_report as R
import docx
from docx.oxml import parse_xml
from docx.oxml.ns import qn, nsdecls
from docx.shared import Inches
from docx.table import Table
from PIL import Image


# ---- additions from the team's SDG-15_1.docx (write-ups and links; tracking codes removed)
WRITEUP_3_2 = ("The Mariano Marcos State University (MMSU), in collaboration with local government units (LGUs) and other stakeholders, implements policies adopted by the Regional Development Council (RDC) to promote the conservation and sustainable utilization of indigenous food plants (IFPs). RDC Resolution No. 7, Series of 2017, promotes habitat protection for endemic and rare species, establishment of community seedbanks, and integration of IFPs into local greening initiatives. The MMSU\u2013SEARCA inventory of 46 IFPs in Ilocos Norte identifies priority conservation species, including Sphaeropteris glauca (pusa-pusa), classified as Endangered in the Philippine national list, and Dillenia philippinensis (palali), assessed as Near Threatened by the IUCN. In support of these policies, MMSU has conducted alokon propagation training in Sarrat, established community gardens and seedbanks with LGUs and elementary schools, promoted alokon planting in urban gardens, including Quezon City, and maintained the Indigenous Food Plants Botanical Garden (IFPBG) for germplasm conservation and research. These initiatives translate regional policies into concrete actions for the identification, monitoring, propagation, and protection of indigenous plant species and their habitats.")
WRITEUP_3_4 = ("The Mariano Marcos State University (MMSU), while guided by its existing University Environmental Policies, University Research and Development Agenda (URDA) 2024\u20132028, and the goals and objectives of the Natural Resources Conservation and Management Center (NRCMC), continues to strengthen its commitment to biodiversity protection and sustainable natural resource management. These institutional frameworks serve as guiding principles for addressing the potential impacts of alien and invasive species on campus ecosystems. Specifically, the NRCMC aims to sustain natural resource health and ecosystem services and establish in situ and ex situ conservation initiatives for Ilocos flora and fauna through interdisciplinary, multisectoral, and interagency collaboration. In support of SDG 15.3.4, these directions provide the technical basis for biodiversity assessment, identification and monitoring of alien and potentially invasive species, appropriate management interventions, and promotion of native species in campus landscaping and rehabilitation to minimize ecological impacts and protect native biodiversity.")
EXTRA_ITEMS = {
 '15.3.2': [dict(title='Regional Policy and Priority Species for Indigenous Food Plants', section='continuing', tag='Ongoing programme \u00b7 RDC Resolution No. 7, Series of 2017', images=[], paras=[WRITEUP_3_2],
                 sources=['Philippine Daily Inquirer, \u201cIlocos Norte farmers step up preservation of indigenous plants\u201d https://newsinfo.inquirer.net/2081767/ilocos-norte-farmers-step-up-preservation-of-indigenous-plants',
                          'MMSU Research and Development, Facebook post. https://www.facebook.com/MMSU.RD.Official/posts/pfbid0Ku2MrGU25FiYuxsUcfe2D3j13ohv7QwefDuaZPbUBhS472ATFfGzTXiNfcKMiYf7l'])],
 '15.3.4': [dict(title='Institutional Frameworks that Guide the Management of Alien and Invasive Species', section='continuing', tag='Ongoing programme \u00b7 University Research and Development Agenda 2024\u20132028', images=[], paras=[WRITEUP_3_4],
                 sources=['MMSU, Institutional Profile. https://www.mmsu.edu.ph/page/3/1/institutional-profile',
                          'MMSU Research Directorate, Natural Resources Conservation and Management Center (NRCMC). https://research.mmsu.edu.ph/centers/nrcmc'])],
}
EXTRA_SOURCES = {
 ('15.2.2', 'greenhouse'): ['MMSU Research Directorate, Facebook post, \u201cRD personnel undergo greenhouse training\u201d https://www.facebook.com/share/p/18mfoUpkDM/'],
 ('15.2.2', 'parambak'): ['MMSU College of Teacher Education, Facebook post, \u201cHappening now: Parambak Ditoy MMSU 2025\u201d https://www.facebook.com/MMSUCTeacherEducation/posts/\U0001d407\U0001d400\U0001d40f\U0001d40f\U0001d404\U0001d40d\U0001d408\U0001d40d\U0001d406-\U0001d40d\U0001d40e\U0001d416-\U0001d40f\U0001d41a\U0001d42b\U0001d41a\U0001d426\U0001d41b\U0001d41a\U0001d424-\U0001d403\U0001d422\U0001d42d\U0001d428\U0001d432-\U0001d40c\U0001d40c\U0001d412\U0001d414-\U0001d7d0\U0001d7ce\U0001d7d0\U0001d7d3the-mmsu-college-of-teacher-education-led-/1172901604836051/'],
 ('15.2.6', 'paddy'): ['Facebook photo post on the 2025 rice paddy art, Batac. https://www.facebook.com/photo/?fbid=2304367663341474&set=pcb.2304369626674611'],
}
A.CH['15.3.4']['close'] = ('These frameworks set the direction. A memorandum from the Office of the President requiring native species in campus planting and the control of invasive species would turn that direction into a written rule; the native planting already under way in the forest reserves, the mangroves and the Learning Center would then sit under it.')

W = nsdecls('w')
GREEN, GOLD, BRONZE, INK, GREY, MIST, CREAM, LINK = '1B4D3E', 'C9A227', '8A6A12', '2B2B28', '5B5B57', 'EAF2EE', 'FAF6E8', '2F6F86'


def r2(text, b=False, i=False, color=None, sz=None, sp=None, caps=False):
    pr = ''
    if b: pr += '<w:b/><w:bCs/>'
    if i: pr += '<w:i/><w:iCs/>'
    if caps: pr += '<w:caps/>'
    if color: pr += f'<w:color w:val="{color}"/>'
    if sp: pr += f'<w:spacing w:val="{sp}"/>'
    if sz: pr += f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>'
    return f'<w:r>{"<w:rPr>" + pr + "</w:rPr>" if pr else ""}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


def p2(runs='', before=0, after=120, line=288, jc=None, keep=False, bottom=None, left=None, shd=None, ind=None, hanging=None, pad=None, lines=False):
    ppr = ('<w:keepNext/>' if keep else '') + ('<w:keepLines/>' if lines else '')
    b = ''
    if bottom: b += f'<w:bottom w:val="single" w:sz="{bottom[1]}" w:space="5" w:color="{bottom[0]}"/>'
    if left: b += f'<w:left w:val="single" w:sz="{left[1]}" w:space="{pad or 8}" w:color="{left[0]}"/>'
    if b: ppr += f'<w:pBdr>{b}</w:pBdr>'
    if shd: ppr += f'<w:shd w:val="clear" w:color="auto" w:fill="{shd}"/>'
    ppr += f'<w:spacing w:before="{before}" w:after="{after}" w:line="{line}" w:lineRule="auto"/>'
    if ind or hanging: ppr += f'<w:ind w:left="{ind or 0}"' + (f' w:hanging="{hanging}"' if hanging else '') + '/>'
    if jc: ppr += f'<w:jc w:val="{jc}"/>'
    return parse_xml(f'<w:p {W}><w:pPr>{ppr}</w:pPr>{runs}</w:p>')


def heading(num, text):
    return p2(r2(num + '  ', b=True, color=GOLD, sz=30, sp=6) + r2(text, b=True, color=GREEN, sz=30, sp=6), before=360, after=140, keep=True, bottom=(GOLD, 8))


def photos(doc, images):
    n = len(images); cols = 2 if n >= 2 else 1; widths = [5040, 5040] if cols == 2 else [10080]
    nb = ''.join(f'<w:{s} w:val="none" w:sz="0" w:space="0" w:color="FFFFFF"/>' for s in ('top', 'left', 'bottom', 'right'))
    x = f'<w:tbl {W}>{R.TBLPR}<w:tblGrid>' + ''.join(f'<w:gridCol w:w="{w}"/>' for w in widths) + '</w:tblGrid>'
    for rr in range((n + cols - 1) // cols):
        x += '<w:tr><w:trPr><w:cantSplit/></w:trPr>'
        for c in range(cols):
            k = rr * cols + c
            cap = r2(images[k]['caption'], i=True, color=GREY, sz=15) if k < n else ''
            x += (f'<w:tc><w:tcPr><w:tcW w:w="{widths[c]}" w:type="dxa"/><w:tcBorders>{nb}</w:tcBorders>{R.MAR}</w:tcPr>'
                  '<w:p><w:pPr><w:spacing w:after="60"/><w:jc w:val="center"/></w:pPr></w:p>'
                  f'<w:p><w:pPr><w:spacing w:after="40"/><w:jc w:val="center"/></w:pPr>{cap}</w:p></w:tc>')
        x += '</w:tr>'
    el = parse_xml(x + '</w:tbl>'); t = Table(el, doc._body)
    for k, im in enumerate(images):
        path = os.path.join(A.R.ASSETS, im['file']); docl = im['caption'].startswith(('Document:', 'Capture:'))
        w, h = R.fit(path, 2.5, 2.3) if cols == 2 else R.fit(path, 4.0, 2.7 if not docl else 3.3)
        t.rows[k // cols].cells[k % cols].paragraphs[0].add_run().add_picture(path, width=Inches(w), height=Inches(h))
    return el


def facts_table(rows):
    body = [[R.txt(lab[0][0][0], b=True, color=GREEN, sz=18), R.txt(val, sz=18, color=INK)] for lab, val in rows]
    return R.table([2300, 7780], None, body, label_first=True)


def resource_par(i, line):
    m = R.URL.search(line)
    text, url = (line[:m.start()].rstrip(), m.group(0)) if m else (line, '')
    runs = r2(f'{i}.\t', b=True, color=GREEN, sz=16) + r2(text + (' ' if url else ''), sz=16, color=INK) + (r2(url, sz=15, color=LINK) if url else '')
    return p2(runs, after=50, line=264, ind=380, hanging=380)


def build(ind):
    code = ind['code']; M = A.CH[code]
    doc = docx.Document(R.TEMPLATE); body = doc.element.body; sect = body.find(qn('w:sectPr'))
    cover = copy.deepcopy(list(body)[34])
    for el in list(body):
        if el is not sect: body.remove(el)
    add = lambda el: sect.addprevious(el)
    title = re.sub(r'\s*\((policy|educational outreach)\)', '', ind['title'])
    for p in cover.iter(qn('w:p')):
        t = ''.join(x.text or '' for x in p.iter(qn('w:t')))
        if t == 'EXAMPLE REPORT': R.set_first_text(p, f'SDG {code}')
        elif t == 'Evidence Report 2025':
            R.set_first_text(p, title)
            for tag in ('w:sz', 'w:szCs'):
                for sz in p.iter(qn(tag)): sz.set(qn('w:val'), '34')
    add(cover)

    add(p2(r2('The question', b=True, color=BRONZE, sz=15, sp=24, caps=True) , before=240, after=20, keep=True, line=252, left=(GOLD, 28), shd=CREAM, ind=160, pad=10))
    add(p2(r2(ind['wording'], i=True, color=INK, sz=22), after=200, line=300, left=(GOLD, 28), shd=CREAM, ind=160, pad=10))

    add(heading('1', 'Introduction'))
    stmt = INTRO[code]
    lead = 'Yes.' if stmt.startswith('Yes. ') else None
    runs = (r2('Yes.', b=True, color=GREEN, sz=21) + r2(stmt[4:], sz=21)) if lead else r2(stmt, sz=21)
    add(p2(runs, jc='both'))

    add(heading('2', 'Body'))
    res = []
    def rid(s):
        m = R.URL.search(s); key = m.group(0) if m else s
        for i, (k, _) in enumerate(res):
            if k == key: return i + 1
        res.append((key, R.src_line(A.neu(s)))); return len(res)
    order = [s for s in ind['stories'] if s['section'] != 'continuing'] + [s for s in ind['stories'] if s['section'] == 'continuing']
    for st_ in order: st_['sources'] = st_['sources'] + EXTRA_SOURCES.get((code, R.C.skey(st_['title'])), [])
    order = EXTRA_ITEMS.get(code, []) + order
    if not order: add(p2(r2('No items yet.', i=True, color=GREY, sz=21), after=100))
    for n, st in enumerate(order, 1):
        key = st.get('key') or ''
        add(p2(r2(f'2.{n}', b=True, color=BRONZE, sz=24, sp=6) + r2('   ' + A.neu(st['title']), b=True, color=GREEN, sz=24), before=300, after=70, keep=True, jc='center', line=264))
        if st['section'] == 'continuing' and st['tag']:
            add(p2(r2(A.neu(st['tag']), i=True, color=GREY, sz=16), after=90, keep=True, jc='center', line=252))
        if st['images']:
            add(photos(doc, st['images'])); add(p2('', after=80, line=240))
        rows = A.facts(R.C.skey(st['title']) if not st.get('paras') or st in ind['stories'] else '')
        if rows: add(facts_table(rows)); add(p2('', after=80, line=240))
        for t in st['paras']: add(p2(r2(A.neu(t), sz=20), jc='both'))
        ids = sorted({rid(s) for s in st['sources']})
        if ids: add(p2(r2('Resources  ', b=True, color=BRONZE, sz=15, sp=12, caps=True) + r2(', '.join(map(str, ids)), b=True, color=GREEN, sz=16), before=40, after=100, line=252, bottom=('D9D9D4', 4)))

    add(heading('3', 'Conclusion'))
    add(p2(r2(M['close'], sz=21, color=INK), after=120, line=300, jc='both', left=(GREEN, 36), shd=MIST, ind=200, pad=12, lines=True))

    add(heading('4', 'Resources'))
    if res:
        for i, (_, line) in enumerate(res, 1): add(resource_par(i, line))
    else:
        add(p2(r2('None yet.', i=True, color=GREY, sz=17)))

    for sec in doc.sections:
        for t in sec.footer._element.iter(qn('w:t')):
            if t.text and 'SDG 15' in t.text: t.text = t.text.replace('SDG 15', f'SDG 15 · {code}')
    doc.core_properties.title = f'SDG {code} · {title} · MMSU'
    path = os.path.join(R.OUT, f'SDG-{code}_Article.docx'); doc.save(path); return path


if __name__ == '__main__':
    for ind in R.DATA: print(build(ind))
