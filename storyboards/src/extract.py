"""Parse the SDG 15 Evidence Compendium (v4 .docx) into data.json.
Usage: python3 -I extract.py <compendium.docx> <out_dir>   (writes data.json + assets/)"""
import sys, re, json, zipfile, os, io
from xml.etree import ElementTree as ET
from PIL import Image

W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
WP='http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
q=lambda ns,t:'{%s}%s'%(ns,t)

def main(docx,out):
    z=zipfile.ZipFile(docx)
    rels={m.group(1):m.group(2) for m in re.finditer(r'<Relationship [^>]*?Id="(rId\d+)"[^>]*?Target="([^"]+)"',z.read('word/_rels/document.xml.rels').decode())}
    rels.update({m.group(2):m.group(1) for m in re.finditer(r'<Relationship [^>]*?Target="([^"]+)"[^>]*?Id="(rId\d+)"',z.read('word/_rels/document.xml.rels').decode())})
    root=ET.fromstring(z.read('word/document.xml'))
    os.makedirs(out+'/assets',exist_ok=True)
    saved={}
    def save_img(target):
        if target in saved: return saved[target]
        raw=z.read('word/'+target); name=os.path.splitext(os.path.basename(target))[0]
        im=Image.open(io.BytesIO(raw))
        if target.endswith('.png'):
            fn=name+'.png'; im.save(f'{out}/assets/{fn}',optimize=True)
        else:
            im=im.convert('RGB'); im.thumbnail((1500,1500)); fn=name+'.jpg'; im.save(f'{out}/assets/{fn}',quality=82,optimize=True)
        saved[target]=fn; return fn
    # status table (first table)
    tbl=root.find('.//'+q(W,'tbl'))
    status={}
    for tr in tbl.findall(q(W,'tr'))[1:]:
        tcs=tr.findall(q(W,'tc'))
        txt=lambda tc:'\n'.join(''.join(t.text or '' for t in p.iter(q(W,'t'))) for p in tc.findall(q(W,'p'))).strip()
        code=txt(tcs[0]); status[code]={'question':txt(tcs[1]),'status':txt(tcs[2])}
    inds=[]; cur=None; story=None; section='2025'; mode=None
    def ptext(p): return ''.join(t.text or '' for t in p.iter(q(W,'t')))
    for p in root.iter(q(W,'p')):
        st=p.find(q(W,'pPr')+'/'+q(W,'pStyle'))
        sty=st.get(q(W,'val')) if st is not None else ''
        txt=ptext(p).strip()
        imgs=[]
        for d in p.iter(q(WP,'docPr')):
            pass
        for dr in p.iter(q(WP,'inline')):
            bl=next(dr.iter(q(A,'blip')),None); dp=dr.find(q(WP,'docPr'))
            if bl is None: continue
            target=rels[bl.get(q(R,'embed'))]
            imgs.append({'file':save_img(target),'caption':(dp.get('descr') or dp.get('title') or '') if dp is not None else ''})
        if sty=='Heading1':
            m=re.match(r'SDG (15\.\d\.\d) · (.*)',txt)
            if m:
                cur={'code':m.group(1),'title':m.group(2),'wording':'','note':'','stories':[]}; inds.append(cur); story=None; section='2025'; mode='ind'
            else: cur=None
            continue
        if cur is None: continue
        if sty=='Heading2':
            story={'title':txt,'section':section,'tag':'','images':[],'paras':[],'sources':[]}; cur['stories'].append(story); mode='story'; continue
        if txt in ('Evidence from 2025',): section='2025'; continue
        if txt=='Continuing implementation' : section='continuing'; continue
        if txt.startswith('Policies and programmes that began before 2025'): continue
        if story is None:
            if txt.startswith(('Support or','Have a','Work directly','Offer','Include','Collaborate','Have water')) and not cur['wording']: cur['wording']=txt
            elif re.match(r'(DRAFT|NO ENTRY YET|No 2025 item)',txt): cur['note']=txt
            continue
        if imgs: story['images']+=imgs; continue
        if not txt: continue
        if txt=='Source': mode='src'; continue
        caps={i['caption'] for s in cur['stories'] for i in s['images']}
        if txt in caps or txt in {c.replace('"','“') for c in caps}: continue
        if mode=='src' or p.find(q(W,'pPr')+'/'+q(W,'numPr')) is not None:
            story['sources'].append(txt); continue
        if re.match(r'(Continuing implementation|Policy|Policies|Plan|Continuing role|2025, with)\b.*',txt) and len(txt)<140 and not story['tag'] and not story['paras']:
            story['tag']=txt; continue
        story['paras'].append(txt)
    for c in inds:
        c.update(status[c['code']])
    json.dump(inds,open(out+'/data.json','w'),indent=1,ensure_ascii=False)
    for c in inds: print(c['code'],c['status'],'|',len(c['stories']),'stories |',c['wording'][:50])
main(sys.argv[1],sys.argv[2])
