import json, zipfile, hashlib, sys
from pathlib import Path
from lxml import etree as E
import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
root=Path(__file__).parent
W={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
q=lambda s:'{'+W['w']+'}'+s
with zipfile.ZipFile(root/'word_converted.docx') as z:
    for name in z.namelist():
        if name.endswith('.xml') and name.startswith('word/'):
            out=root/'ooxml'/name
            out.parent.mkdir(parents=True,exist_ok=True)
            out.write_bytes(E.tostring(E.fromstring(z.read(name)),pretty_print=True,encoding='utf-8',xml_declaration=True))
    document=E.fromstring(z.read('word/document.xml'))
    lines=[]
    for i,p in enumerate(document.xpath('//w:body//w:p',namespaces=W),1):
        txt=''.join(p.xpath('.//w:t/text()',namespaces=W))
        lines.append(f'PARAGRAPH {i}: {txt}\n'+E.tostring(p,pretty_print=True,encoding='unicode'))
    (root/'word_paragraph_xml.txt').write_text('\n'.join(lines),encoding='utf-8')
native=json.loads((root/'word_native.json').read_text(encoding='utf-8-sig'))
lines=[]
for p in native['Paragraphs']:
    if p['Text'].strip('\r\x07\t\f '):
        lines.append(json.dumps(p,ensure_ascii=False))
(root/'word_paragraphs.jsonl').write_text('\n'.join(lines),encoding='utf-8')
for pdf in [root/'word_original.pdf',root/'../TongjiThesis-LaTeX-2026-10-30.pdf']:
    with pdfplumber.open(pdf) as d:
        pages=[]
        for i,p in enumerate(d.pages,1):
            pages.append({'page':i,'width':p.width,'height':p.height,'chars':p.chars,'lines':p.lines,'rects':p.rects,'images':p.images,'text':p.extract_text()})
        (root/(pdf.stem+'_layout.json')).write_text(json.dumps(pages,ensure_ascii=False,default=str),encoding='utf-8')
for p in native['Paragraphs']:
    if p['Text'].strip('\r\x07\t\f '):
        keys=['Index','Page','Text','FontFarEast','FontAscii','Size','Bold','Color','Alignment','FirstLineIndent','SpaceBefore','SpaceAfter','LineSpacingRule','LineSpacing','X','Y']
        print(json.dumps({k:p[k] for k in keys},ensure_ascii=False))
