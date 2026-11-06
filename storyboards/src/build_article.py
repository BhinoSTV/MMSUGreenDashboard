# -*- coding: utf-8 -*-
"""Article edition in the MMSU SDG template look: one Word article per SDG 15 indicator.
Cover -> the question -> 1 Introduction -> 2 Body (itemised, with photos) -> 3 Conclusion -> 4 Resources.
Usage: python3 -I build_article.py <template.docx> <out_dir>"""
import ast, copy, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_report as R           # reuses helpers; reads the same argv (template, out_dir)
import docx
from docx.oxml import parse_xml
from docx.oxml.ns import qn

C, para, run, heading1 = R.C, R.para, R.run, R.heading1
COMMIT = 'MMSU’s commitment is to take an active role in protecting and promoting sustainable use of terrestrial ecosystems, responsible land use, and biodiversity conservation.'

# conclusions and one-line stories come from the story edition's chapter copy
_src = open(os.path.join(HERE, 'build_story.py')).read()
_tree = ast.parse(_src)
_node = next(n for n in _tree.body if isinstance(n, ast.Assign) and getattr(n.targets[0], 'id', '') == 'CH')
CH = eval(compile(ast.Expression(_node.value), 'CH', 'eval'), {'dict': dict})
CH['15.3.4'] = dict(
    story='No item is recorded yet for this question.',
    close='A memorandum from the Office of the President requiring native species in campus planting and the control of invasive species would answer it. The native planting already under way in the forest reserves, the mangroves and the Learning Center would then sit under a written policy.')
REPL = [('Continuing implementation', 'Ongoing programme'), ('Continuing role', 'Ongoing role'), ('SDG 15 evidence page', 'SDG 15 page'),
        (' (see the 2025 frame)', ''), (' (see the 2025 evidence for this indicator)', ''), (' The 2025 activities are shown in the 15.2.3 and 15.2.4 frames.', ''), (' · date to confirm', '')]


def neu(s):
    for a, b in REPL: s = s.replace(a, b)
    return s


def facts(key):
    """Known facts only (no placeholders) as rows for policy items."""
    if key not in R.RECORD: return []
    labels = ['Policy', 'Approved by', 'Reference no.', 'Date', 'Provisions']
    rows = []
    for lab, v in zip(labels, R.RECORD[key]):
        v = re.sub(r'\s*(Last reviewed|Revision|Board approval):\s*\[to add\]\.?', '', v)
        v = v.split(' The 2026 form')[0].strip().rstrip(';')
        if not v or '[to add]' in v: continue
        rows.append([R.txt(lab, b=True), v])
    return rows


def build_article(ind):
    code = ind['code']; M = CH[code]
    doc = docx.Document(R.TEMPLATE); body = doc.element.body; sect = body.find(qn('w:sectPr'))
    cover = copy.deepcopy(list(body)[34])
    for el in list(body):
        if el is not sect: body.remove(el)
    add = lambda el: sect.addprevious(el)
    title = re.sub(r'\s*\((policy|educational outreach)\)', '', ind['title'])

    # cover
    for p in cover.iter(qn('w:p')):
        t = ''.join(x.text or '' for x in p.iter(qn('w:t')))
        if t == 'EXAMPLE REPORT': R.set_first_text(p, f'SDG {code}')
        elif t == 'Evidence Report 2025':
            R.set_first_text(p, title)
            for sz in p.iter(qn('w:sz')): sz.set(qn('w:val'), '32')
            for sz in p.iter(qn('w:szCs')): sz.set(qn('w:val'), '32')
    add(cover)

    # the question
    add(parse_xml(para(run('The question  ', b=True, color='C55A11', sz=17) + run(ind['wording'], i=True, sz=19), before=160, after=100, left='C9A227', shd='FBF3D5', ind=140)))

    # 1 introduction
    add(heading1('1 · Introduction'))
    add(parse_xml(para(run(COMMIT + ' ' + M['story']), after=100)))

    # 2 body
    add(heading1('2 · Body'))
    res = []            # resources, deduped in order of first use
    def rid(s):
        m = R.URL.search(s); key = m.group(0) if m else s
        for i, (k, _) in enumerate(res):
            if k == key: return i + 1
        res.append((key, R.src_line(neu(s)))); return len(res)
    order = [s for s in ind['stories'] if s['section'] != 'continuing'] + [s for s in ind['stories'] if s['section'] == 'continuing']
    if not order:
        add(parse_xml(para(run('No items yet.', i=True, color='5B5B57'), after=100)))
    for n, st in enumerate(order, 1):
        key = C.skey(st['title'])
        add(parse_xml(para(run(f'2.{n} · {neu(st["title"])}', b=True, color='1B4D3E', sz=22), before=200, after=80, jc='center', keep=True)))
        if st['section'] == 'continuing' and st['tag']:
            add(parse_xml(para(run(neu(st['tag']), i=True, color='5B5B57', sz=15), after=60, jc='center', keep=True)))
        if st['images']:
            add(R.photo_table(doc, st['images'])); add(parse_xml(para('', after=60)))
        rows = facts(key)
        if rows:
            add(R.table([2600, 7480], None, rows, label_first=True)); add(parse_xml(para('', after=60)))
        for t in st['paras']: add(parse_xml(para(run(neu(t)), after=100)))
        ids = sorted({rid(s) for s in st['sources']})
        if ids: add(parse_xml(para(run('Resources: ' + ', '.join(map(str, ids)), i=True, color='5B5B57', sz=15), before=40, after=60)))

    # 3 conclusion
    add(heading1('3 · Conclusion'))
    add(parse_xml(para(run(M['close']), after=100)))

    # 4 resources
    add(heading1('4 · Resources'))
    if res:
        for i, (_, line) in enumerate(res, 1): add(parse_xml(para(run(f'{i}.  {line}', sz=15), after=30, ind=300)))
    else:
        add(parse_xml(para(run('None yet.', i=True, color='5B5B57', sz=15), after=30)))

    for sec in doc.sections:
        for t in sec.footer._element.iter(qn('w:t')):
            if t.text and 'SDG 15' in t.text: t.text = t.text.replace('SDG 15', f'SDG 15 · {code}')
    doc.core_properties.title = f'SDG {code} · {title} · MMSU'
    path = os.path.join(R.OUT, f'SDG-{code}_Article.docx'); doc.save(path); return path


if __name__ == '__main__':
    for ind in R.DATA: print(build_article(ind))
