# -*- coding: utf-8 -*-
"""One Evidence Report (.docx) per SDG 15 indicator, following the MMSU SDG Evidence Compendium TEMPLATE
(cover, 1 Sites and platforms explored, 2 Indicators to report, 3 Optional peers, 4 Evidence by indicator,
5 Before submission). Content comes from data.json (parsed from Compendium v4) and content.py.
Usage: python3 -I build_report.py <template.docx> <out_dir>"""
import copy, json, os, re, sys
from xml.sax.saxutils import escape
import docx
from docx.oxml import parse_xml
from docx.oxml.ns import qn, nsdecls
from docx.shared import Inches
from docx.table import Table
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import content as C

TEMPLATE, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
ASSETS = os.path.join(HERE, 'assets')
DATA = json.load(open(os.path.join(HERE, 'data.json')))
URL = re.compile(r'https?://\S+')
PREPARED = '6 November 2026'
W = nsdecls('w')

# ------------------------------------------------------------------ XML helpers (mirror the template's direct formatting)
def run(text, b=False, i=False, color=None, sz=None):
    pr = ''
    if b: pr += '<w:b/><w:bCs/>'
    if i: pr += '<w:i/><w:iCs/>'
    if color: pr += f'<w:color w:val="{color}"/>'
    if sz: pr += f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>'
    return f'<w:r>{"<w:rPr>" + pr + "</w:rPr>" if pr else ""}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


def para(runs='', before=None, after=None, jc=None, keep=False, pagebreak=False, bottom=None, shd=None, left=None, ind=None):
    ppr = ''
    if keep: ppr += '<w:keepNext/>'
    if pagebreak: ppr += '<w:pageBreakBefore/>'
    if bottom: ppr += f'<w:pBdr><w:bottom w:val="single" w:sz="12" w:space="4" w:color="{bottom}"/></w:pBdr>'
    if left: ppr += f'<w:pBdr><w:left w:val="single" w:sz="24" w:space="6" w:color="{left}"/></w:pBdr>'
    if shd: ppr += f'<w:shd w:val="clear" w:color="auto" w:fill="{shd}"/>'
    sp = ''
    if before is not None: sp += f' w:before="{before}"'
    if after is not None: sp += f' w:after="{after}"'
    if sp: ppr += f'<w:spacing{sp}/>'
    if ind: ppr += f'<w:ind w:left="{ind}"/>'
    if jc: ppr += f'<w:jc w:val="{jc}"/>'
    return f'<w:p {W}>{"<w:pPr>" + ppr + "</w:pPr>" if ppr else ""}{runs}</w:p>'


def heading1(text, pagebreak=False):
    return parse_xml(para(run(text, b=True, color='1B4D3E', sz=28), before=None if pagebreak else 200, after=80, keep=True, pagebreak=pagebreak, bottom='1B4D3E'))


def intro(text):
    return parse_xml(para(run(text, sz=17), after=80))


BORD = ''.join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/>' for s in ('top', 'left', 'bottom', 'right'))
MAR = '<w:tcMar><w:top w:w="60" w:type="dxa"/><w:left w:w="100" w:type="dxa"/><w:bottom w:w="60" w:type="dxa"/><w:right w:w="100" w:type="dxa"/></w:tcMar>'
TBLPR = ('<w:tblPr><w:tblW w:w="10080" w:type="dxa"/><w:tblBorders>' + ''.join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="auto"/>' for s in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV')) +
         '</w:tblBorders><w:tblCellMar><w:left w:w="10" w:type="dxa"/><w:right w:w="10" w:type="dxa"/></w:tblCellMar><w:tblLook w:val="0000" w:firstRow="0" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" w:noHBand="0" w:noVBand="0"/></w:tblPr>')


def cell(w, content, fill=None, hdr=False, center=False, label=False):
    """content: str | list of run-xml-lists. str -> plain 8pt text."""
    shd = f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>' if fill else ''
    va = '<w:vAlign w:val="center"/>' if hdr else ''
    if isinstance(content, str):
        content = [[(content, {})]]
    ps = ''
    for line in content:
        rs = ''.join(run(t, **({'sz': 16} | ({'b': True, 'color': 'FFFFFF'} if hdr else {}) | ({'b': True} if label else {}) | o)) for t, o in line)
        ppr = '<w:pPr><w:jc w:val="center"/></w:pPr>' if center else ''
        ps += f'<w:p>{ppr}{rs}</w:p>'
    return f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/><w:tcBorders>{BORD}</w:tcBorders>{shd}{MAR}{va}</w:tcPr>{ps}</w:tc>'


def table(widths, header, rows, label_first=False, fills=None):
    grid = ''.join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    x = f'<w:tbl {W}>{TBLPR}<w:tblGrid>{grid}</w:tblGrid>'
    if header:
        x += '<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>' + ''.join(cell(w, h, fill='1B4D3E', hdr=True) for w, h in zip(widths, header)) + '</w:tr>'
    for r in rows:
        x += '<w:tr><w:trPr><w:cantSplit/></w:trPr>' + ''.join(
            cell(w, c, fill=('EAF2EE' if (label_first and j == 0) else None), label=(label_first and j == 0)) for j, (w, c) in enumerate(zip(widths, r))) + '</w:tr>'
    return parse_xml(x + '</w:tbl>')


def txt(s, **o): return [[(s, o)]]
def orange(s): return [[(s, {'color': 'C55A11'})]]


def set_first_text(p, text, drop_color=False):
    rs = p.findall(qn('w:r'))
    for extra in rs[1:]: p.remove(extra)
    for pe in p.findall(qn('w:proofErr')): p.remove(pe)
    t = rs[0].find(qn('w:t')); t.text = text
    t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    if drop_color:
        pr = rs[0].find(qn('w:rPr'))
        if pr is not None and pr.find(qn('w:color')) is not None: pr.remove(pr.find(qn('w:color')))


# ------------------------------------------------------------------ content helpers
DESC = {}
_t = docx.Document(TEMPLATE)
for _tb in _t.tables:      # the example 'Contents' table: code + description
    for tr in _tb.rows:
        c = [x.text.strip() for x in tr.cells]
        if len(c) == 2 and re.match(r'15\.\d\.\d$', c[0]) and not c[1].startswith('EXAMPLE'): DESC[c[0]] = c[1]

PICK = {  # story key, label, optional extra note
 '15.2.1': ('cafsd', 'CAFSD graduands planting', 'news/2468/cafsd', ''),
 '15.2.3': ('ifp', 'Indigenous Food Plants Program', 'news/show/389', ''),
 '15.2.4': ('mangtrain', 'Mangrove seminar-workshop', 'news/2670/mmsu-trains', ' Confirm that the seminar was free of charge.'),
 '15.2.5': ('soa', 'School-on-the-Air', 'mmsu-draws-1k-enrollees', ' Confirm that the programme was free of charge.'),
 '15.2.6': ('paddy', 'Rice paddy art', 'news/2527', ' Weak fit: a farm-tourism attraction with student guides, not a structured training for communities. Add visitor or tour numbers and any briefing given to visitors.'),
 '15.3.1': ('sirmata_land', 'Sirmata 2040 Land Use Policy', '19uycXrgcO_iXPdPpMQwdCRxmoD1U5i60/view', ' Open the link without a login and confirm the policy sections show on the page.'),
 '15.3.2': ('ifp_vanishing', 'Indigenous Food Plants Program', 'wins-best-paper-at-suc-acap-2025', ' Weak fit: a research programme, not a policy to identify, monitor and protect IUCN Red List and national-list species. The 2003 classification applied IUCN criteria locally; it is not the IUCN Red List. Attach the RDC resolution and any MMSU policy or species register.'),
 '15.3.3': ('sirmata_plan', 'Sirmata 2040 LUDIP', '19uycXrgcO_iXPdPpMQwdCRxmoD1U5i60/view', ' No 2025 planning record is attached; the plan was in force by 2025.'),
 '15.3.5': ('pasuquin', 'Pasuquin agreement', 'mmsu-ties-up-with-toyota-and-denr', ''),
 '15.4.1': ('waterpolicy', 'MMSU Water Policy (Sirmata 2040)', '19uycXrgcO_iXPdPpMQwdCRxmoD1U5i60/view', ' The groundwater report below is supporting only: it compares well water with drinking-water standards and is not a discharge standard.'),
 '15.4.2': ('iwmp', 'Plastic Waste Management page', '1NU-Qda9KG0J-PIOgKZwPKC4h_TU05zcm/data', ''),
 '15.4.3': ('ipwmp', 'Hazardous Waste Disposal page', '1jo6-3cVqxRAIllIxEhnSCgyT5ef5LGOW/data', ' Memorandum No. 26-370 (30 Sep 2026) has no public page yet.'),
}
NO_PICK = {  # indicators with no submission pick: (note, searched/missing/follow-up)
 '15.2.2': ('None yet. No dated MMSU policy that food on campus is sustainably farmed was found. Attach the policy, or a Business Directorate sourcing memorandum, before submitting.',
            ('MMSU news, extension and research pages (supporting items below).', 'A dated policy or sourcing memorandum in force by 2025.', 'Business Directorate and the campus farm units.')),
 '15.3.4': ('None yet. Nothing was found in MMSU’s public sources, the focal person’s mailbox or the links supplied by the team.',
            ('MMSU public sources, the focal person’s mailbox and the links supplied by the team.', 'A policy to reduce the impact of alien species on campus.',
             'Office of the President: a memorandum requiring native species in campus planting and the control of invasive species would answer it.')),
}
EVYEAR = {c: '2025 (calendar year)' for c in ('15.2.1', '15.2.3', '15.2.4', '15.2.5', '15.2.6', '15.3.5')}
NOTE = {
 'gradcont': 'Continuing programme, 2024 to 2026. The 2 July 2025 planting is the dated evidence; the 2024 and 2026 entries show the programme is ongoing.',
 'ifpgarden': 'Dated 6 June 2026, after the data year. Internal evidence only; the 2025 foodscape items carry the claim.',
 'nbscont': 'Project term 1 May 2024 to 30 April 2026, which covers the data year.',
 'bambusetums': 'Dingras launch dated 30 September 2026, after the data year. Internal evidence only.',
 'bclc': 'In place since 2023. No photo is attached yet.',
 'talon': 'Site visit of 15 January 2026, after the data year. Internal evidence only.',
 'kpnp': 'Appointment of 29 March 2023, still in effect as far as the records show.',
 'sirmata_land': 'Policy in force since 2021.', 'sirmata_plan': 'Plan in force since 2021.',
 'ifp_vanishing': '2025 activities, with continuing implementation since 2003.',
 'memo26370': 'Dated 30 September 2026, after the data year. Internal evidence only; no public page yet.',
 'waterpolicy': 'In force since 2021 (Sirmata 2040); the IPWMP was revised in 2020.',
 'iwmp': 'Policies from 2009 to 2023, with 2024 and 2025 actions; in force by the data year.',
 'tumbler': 'February 2024 memoranda, in force by the data year.',
 'ipwmp': 'IPWMP revised in 2020; in force by the data year.',
}
O = '[to add]'
RECORD = {  # policy record: title, approved by, reference, date, section answering
 'sirmata_land': ('MMSU Land Use, Zoning, Water and Energy Policies (Sirmata 2040 LUDIP), Land Use Policy', O, O, '2021 (prepared under RA 11396). Last reviewed: ' + O, 'Policies 1.3, 7.1, 9.1, 10.2 and 4.3'),
 'sirmata_plan': ('Sirmata 2040: Land Use Development and Infrastructure Plan (LUDIP)', 'Endorsed by the CHED Technical Working Group after validation visits. Board approval: ' + O, O, '2021 (20-year plan). Last reviewed: ' + O, 'Zoning policy, Protected Land (Policy 9.1); Forest Reserve no-build zone; Policies 7.1, 10.1 and 11.1'),
 'waterpolicy': ('MMSU Water Policy (Sirmata 2040 LUDIP) and Integrated Pollution and Waste Management Program', O, O, 'Water Policy 2021; IPWMP revised 2020. Last reviewed: ' + O, 'Water Policy 2.6–2.9 (2.9 protection from pollution; 2.8 rehabilitation); IPWMP registration for wastewater discharge (RA 9275)'),
 'iwmp': ('Integrated Waste Management Program, revised as the Integrated Pollution and Waste Management Program (IPWMP)', 'Board of Regents (2009; amended 2015). Revision: ' + O, O, '2009; amended 2015; Styrofoam and plastic packaging policy 11 Feb 2016; IPWMP revised 2020', 'Styrofoam and plastic provisions; “No Bottled Water” Memoranda No. 22-148A and 23-189'),
 'ipwmp': ('Integrated Pollution and Waste Management Program (IPWMP)', O, O, '2020 (compendium). The 2026 form entered 2021: confirm the year. Last reviewed: ' + O, 'Hazardous waste provisions: focal persons, labelling, central storage, DENR-accredited disposal (RA 6969)'),
 'memo26370': ('Memorandum No. 26-370, University Environmental Compliance and Pollution Prevention Program', 'University President Virgilio Julius P. Manzano Jr.', '26-370', '30 September 2026', 'Environmental Compliance Procedures; PCB-containing equipment procedure'),
}
PEERS = {
 '15.2.1': [('Caraga State University', '15.2.1: forums, a natural science museum launch and an agroforestry field day', 'MMSU 2025 events: CAFSD graduands planting, President’s Farm Field Day, mangrove and coconut plantings, wildlife photo contest.')],
 '15.2.2': [('Caraga State University', '15.2.2: a sustainably managed campus farm', 'A Business Directorate sourcing memorandum or a campus-farm statement; none found yet.')],
 '15.2.3': [('Caraga State University', '15.2.3: biodiversity surveys and a biodiversity-corridor workshop', 'Surveys or inventories of the forest reserves and mangrove sites, if any exist.')],
 '15.2.5': [('Caraga State University', '15.2.5: farmer trainings and seedling distribution', 'MMSU 2025 trainings and outreach: School-on-the-Air, Pinili bamboo training, Pasuquin onion trainings.')],
 '15.3.1': [('Visayas State University', '15.3.1: Board-approved Policy on Tree Management (BOR Resolution No. 146, s. 2025)', 'A 2025 Board resolution or review of the 2021 land use policy, or of the forest reserves, would add the review point.')],
 '15.3.3': [('Caraga State University', '15.3.3: campus planning that consults biodiversity data', 'Sirmata 2040 LUDIP, with its protected-land and forest-reserve provisions quoted.'),
            ('Eastern Visayas State University', '15.3.3: Board-approved Land Use Development and Infrastructure Plan', 'Sirmata 2040 LUDIP presented as the plan in force; quote its forest-reserve and green-space provisions.')],
 '15.3.5': [('Caraga State University', '15.3.5: agreements with DENR and barangays', 'MMSU 2025 agreements and plantings: Pasuquin MOA, Badoc, Currimao, and the DENR MOU.')],
 '15.4.1': [('Caraga State University', '15.4.1: an Adopt-an-Estero commitment', 'A comparable water-body commitment, or a discharge or effluent standard.')],
 '15.4.2': [('Caraga State University', '15.4.2: dated memorandum on plastic waste (Memo No. 33, s. 2024)', 'A 2025 memorandum or review of the plastic policies would add the review point.')],
 '15.4.3': [('Caraga State University', '15.4.3: dated memorandum on hazardous waste (Memo No. 50, s. 2024) with EMB seminars', 'A 2025 memorandum or review would add the review point; Memorandum No. 26-370 (30 Sep 2026) is the latest.')],
}
SITES = [  # (url fragment, site, url)
 ('extension.mmsu.edu.ph', 'MMSU Extension Directorate', 'https://extension.mmsu.edu.ph/news'),
 ('research.mmsu.edu.ph', 'MMSU Research Directorate', 'https://research.mmsu.edu.ph/news'),
 ('mmsu.edu.ph/resources', 'MMSU SDG 15 and policy resource pages', 'https://www.mmsu.edu.ph/resources'),
 ('mmsu.edu.ph', 'MMSU News', 'https://www.mmsu.edu.ph/news'),
 ('pcaarrd.dost.gov.ph', 'DOST-PCAARRD', 'https://www.pcaarrd.dost.gov.ph'),
 ('manilatimes.net', 'The Manila Times', 'https://www.manilatimes.net'),
 ('philstar.com', 'The Philippine Star', 'https://philstar.com'),
 ('searca.org', 'SEARCA publications', 'https://www.searca.org/pubs'),
 ('facebook.com/pnagovph', 'Philippine News Agency (Facebook)', 'https://www.facebook.com/pnagovph'),
]


def site_of(src):
    m = URL.search(src)
    if m:
        for frag, name, url in SITES:
            if frag in m.group(0): return name, url
        return 'Other website', m.group(0)
    if 'Office of the President' in src or 'Memorandum' in src: return 'Office of the President (memoranda)', 'Office records, not public'
    if 'Office of Sustainability' in src or 'SDG 15 Life on Land report' in src: return 'Office of Sustainability and Futures Thinking', 'Internal SDG 15 report (2025)'
    return 'Other source', 'n/a'


def src_line(s):
    m = URL.search(s)
    if not m: return s.strip()
    return s[:m.start()].strip().rstrip('.,') + '. ' + m.group(0).rstrip('>.,)')


def find_url(ind, frag):
    for st in ind['stories']:
        for s in st['sources']:
            m = URL.search(s)
            if m and frag in m.group(0): return m.group(0).rstrip('>.,)').replace('\\_', '_')
    raise KeyError(frag)


# ------------------------------------------------------------------ images
def fit(path, wmax, hmax):
    w, h = Image.open(path).size; k = min(wmax / w, hmax / h); return w * k, h * k


def photo_table(doc, images):
    n = len(images); cols = 2 if n >= 2 else 1; widths = [5040, 5040] if cols == 2 else [10080]
    rows = (n + cols - 1) // cols; x = f'<w:tbl {W}>{TBLPR}<w:tblGrid>' + ''.join(f'<w:gridCol w:w="{w}"/>' for w in widths) + '</w:tblGrid>'
    nb = ''.join(f'<w:{s} w:val="none" w:sz="0" w:space="0" w:color="FFFFFF"/>' for s in ('top', 'left', 'bottom', 'right'))
    for r in range(rows):
        x += '<w:tr><w:trPr><w:cantSplit/></w:trPr>'
        for c in range(cols):
            k = r * cols + c
            x += f'<w:tc><w:tcPr><w:tcW w:w="{widths[c]}" w:type="dxa"/><w:tcBorders>{nb}</w:tcBorders>{MAR}</w:tcPr><w:p><w:pPr><w:spacing w:after="40"/><w:jc w:val="center"/></w:pPr></w:p>'
            x += '<w:p><w:pPr><w:jc w:val="center"/></w:pPr>' + (run(images[k]['caption'], i=True, color='5B5B57', sz=14) if k < n else '') + '</w:p></w:tc>'
        x += '</w:tr>'
    el = parse_xml(x + '</w:tbl>'); t = Table(el, doc._body)
    for k, im in enumerate(images):
        path = os.path.join(ASSETS, im['file'])
        doc_like = im['caption'].startswith(('Document:', 'Capture:'))
        w, h = fit(path, 2.45, 2.2) if cols == 2 else fit(path, 3.7, 2.5 if not doc_like else 3.3)
        t.rows[k // cols].cells[k % cols].paragraphs[0].add_run().add_picture(path, width=Inches(w), height=Inches(h))
    return el


# ------------------------------------------------------------------ report
def build(ind, proto):
    code = ind['code']; M = C.IND[code]
    doc = docx.Document(TEMPLATE); body = doc.element.body; sect = body.find(qn('w:sectPr'))
    P = {k: copy.deepcopy(v) for k, v in proto(doc).items()}
    for el in list(body):
        if el is not sect: body.remove(el)
    add = lambda el: sect.addprevious(el)

    # ---- cover
    cov = P['cover']
    for p in cov.iter(qn('w:p')):
        t = ''.join(x.text or '' for x in p.iter(qn('w:t')))
        if t == 'EXAMPLE REPORT': set_first_text(p, f'INDICATOR {code}')
    add(cov)
    add(parse_xml(para(run(f'Data year 2025 · Draft for validation · prepared {PREPARED}', i=True, sz=17), before=120, after=80)))
    info = P['info']; cells = list(info.iter(qn('w:tc')))
    vals = {1: ('SDG 15 · Life on Land', True), 3: ('2025', True), 7: (PREPARED, True)}
    for k, (v, dc) in vals.items(): set_first_text(cells[k].find(qn('w:p')), v, drop_color=dc)
    add(info)

    # ---- 1 sites explored
    add(heading1('1 · Sites and platforms explored'))
    add(intro('Every site and office where evidence for this indicator was found, and where nothing was found. A list of sites is not evidence; it only shows where the team has looked.'))
    rows = []; seen = {}
    for st in ind['stories']:
        for s in st['sources']:
            name, url = site_of(s); seen.setdefault((name, url), []).append(st['title'])
    for (name, url), titles in seen.items():
        uniq = list(dict.fromkeys(titles))
        shown = '; '.join(uniq[:3]) + (f' and {len(uniq) - 3} more' if len(uniq) > 3 else '')
        rows.append([str(len(rows) + 1), name, url, f'{len(uniq)} item{"s" if len(uniq) != 1 else ""} for {code}: {shown}'])
    if code in NO_PICK and not rows:
        for nm, loc in (('MMSU public sources', 'mmsu.edu.ph news, resources and SDG pages'), ('Focal person’s mailbox', 'Email records'), ('Links supplied by the team', 'Team submissions')):
            rows.append([str(len(rows) + 1), nm, loc, f'Nothing found for {code}'])
    add(table([500, 2500, 3300, 3780], ['#', 'Site or office', 'URL or location', 'What was found'], rows))
    add(parse_xml(para(run('Not yet explored', b=True, color='1B4D3E', sz=28), before=200, after=80, keep=True, bottom='1B4D3E')))
    add(intro('Sources the team should still search. Suggestions are listed; add your own.'))
    add(P['notyet'])

    # ---- 2 indicators to report
    add(heading1('2 · Indicators to report', pagebreak=True))
    add(parse_xml(para(run('SDG 15 · Life on Land · data year 2025'), after=80)))
    add(table([1300, 8780], ['Indicator', 'Description'], [[txt(code, b=True), DESC[code]]]))

    # ---- 3 optional peers
    if code in PEERS:
        add(heading1('3 · Optional: what other universities submit'))
        add(intro('What other universities claim for this indicator, and where MMSU might hold the same kind of evidence.'))
        add(table([2300, 3900, 3880], ['University', 'What it submits (indicator and type of evidence)', 'What to look for at MMSU'], [[a, b, c] for a, b, c in PEERS[code]]))
        add(parse_xml(para(run('[Add the THE edition and URL for each result before using this page.]', i=True, color='C55A11', sz=15), before=60, after=60)))

    # ---- 4 evidence
    add(heading1('4 · Evidence by indicator', pagebreak=True))
    add(parse_xml(para(run(f'SDG {code} · {ind["title"]}', b=True, color='1B4D3E', sz=26), after=60, keep=True, bottom='1B4D3E')))
    add(parse_xml(para(run(ind['wording'], i=True), before=60, after=40, keep=True)))
    add(parse_xml(para(run('Evidence year: ' + EVYEAR.get(code, 'in place by 2025'), b=True, sz=17), after=60, keep=True)))
    stories = {}
    for st in ind['stories']: stories[C.skey(st['title'])] = st
    order = []
    pk = PICK.get(code)
    if pk: order.append(pk[0])
    order += [C.skey(s['title']) for s in ind['stories'] if s['section'] != 'continuing' and C.skey(s['title']) not in order]
    order += [C.skey(s['title']) for s in ind['stories'] if s['section'] == 'continuing' and C.skey(s['title']) not in order]
    if pk:
        url = find_url(ind, pk[2])
        add(parse_xml(para(run('Submission pick: ', b=True, color='C55A11', sz=16) + run(f'{pk[1]}, {url}' + (' ' + pk[3].strip() if pk[3].strip() else ''), sz=16), after=60, left='C9A227', shd='FBF3D5', ind=140)))
    else:
        add(parse_xml(para(run('Submission pick: ', b=True, color='C55A11', sz=16) + run(NO_PICK[code][0], sz=16), after=60, left='C9A227', shd='FBF3D5', ind=140)))
        s_, m_, f_ = NO_PICK[code][1]
        add(table([1900, 8180], None, [[txt('No evidence yet', b=True), [[('Searched: ', {'b': True}), (s_, {})], [('Missing: ', {'b': True}), (m_, {})], [('Follow-up: ', {'b': True}), (f_, {}), (' [assign a name]', {'color': 'C55A11'})], [('Do not create or backdate a document to fill a gap.', {'i': True})]]]], label_first=True))
    if code == '15.2.2':
        add(parse_xml(para(run('Supporting practice (internal evidence, not the policy)', b=True, color='5B5B57', sz=16), before=120, after=40, keep=True)))
    for key in order:
        st = stories[key]
        add(parse_xml(para(run(st['title'], b=True, color='1B4D3E', sz=22), before=200, after=80, jc='center', keep=True)))
        if key in NOTE or (st['section'] == 'continuing' and st['tag']):
            add(parse_xml(para(run(NOTE.get(key, st['tag']), i=True, color='5B5B57', sz=15), after=60, jc='center', keep=True)))
        if st['images']:
            add(photo_table(doc, st['images'])); add(parse_xml(para('', after=60)))
        if key in RECORD:
            r = RECORD[key]; labels = ['Policy title', 'Approved by', 'Reference no.', 'Date approved or last reviewed', 'Section that answers the question']
            rr = []
            for lab, v in zip(labels, r):
                parts = v.split(O)
                line = []
                for n_, part in enumerate(parts):
                    if part: line.append((part, {}))
                    if n_ < len(parts) - 1: line.append((O, {'color': 'C55A11'}))
                rr.append([txt(lab, b=True), [line]])
            add(table([2600, 7480], None, rr, label_first=True)); add(parse_xml(para('', after=60)))
        for ptxt in st['paras']:
            add(parse_xml(para(run(ptxt), after=100)))
        add(parse_xml(para(run('Source', b=True, color='5B5B57', sz=16), before=40, after=20, keep=True)))
        for s in st['sources']:
            add(parse_xml(para(run('• ' + src_line(s), sz=15), after=20)))
    if pk or code == '15.2.2':
        add(parse_xml(para(run('Only the submission pick is entered in the portal. The other items are internal evidence.', i=True, color='5B5B57', sz=15), before=100, after=100)))
    if code == '15.3.4':
        add(parse_xml(para(run('No items yet. Do not create or backdate a document to fill a gap.', i=True, color='5B5B57', sz=15), before=100, after=100)))

    # ---- 5 before submission
    add(heading1('5 · Before submission'))
    add(P['check'])
    if M['confirm']:
        add(parse_xml(para(run('Open items for this indicator', b=True, color='1B4D3E', sz=20), before=160, after=60, keep=True)))
        for c in M['confirm']:
            add(parse_xml(para(run('☐ ', sz=17) + run(c, sz=17), after=40, left='C9A227', shd='FBF3D5', ind=140)))

    # ---- footer: SDG number + indicator
    for sec in doc.sections:            # footer text sits inside a table, so edit the w:t nodes directly
        for t in sec.footer._element.iter(qn('w:t')):
            if t.text and 'SDG 15' in t.text: t.text = t.text.replace('SDG 15', f'SDG 15 · {code}')
    doc.core_properties.title = f'SDG {code} Evidence Report 2025 · MMSU'
    path = os.path.join(OUT, f'SDG-{code}_Evidence-Report.docx'); doc.save(path); return path


def protos(doc):
    b = list(doc.element.body)
    chk = copy.deepcopy(b[32]); rows = chk.findall(qn('w:tr'))
    p0 = rows[0].findall('.//' + qn('w:p'))[1]
    set_first_text(rows[0].findall('.//' + qn('w:p'))[1], 'The indicator on page 2 has a submission pick or a note that no evidence was found')
    return {'cover': b[34], 'info': b[2], 'notyet': b[8], 'check': chk}


if __name__ == '__main__':
    for ind in DATA:
        print(build(ind, protos))
