import sys,json
from pathlib import Path
import pdfplumber
sys.stdout.reconfigure(encoding='utf-8')
root=Path(__file__).parent
for stem in ['latex_default','latex_blank']:
    file=root/(stem+'.pdf')
    if not file.exists():
        continue
    with pdfplumber.open(file) as pdf:
        pages=[]
        for i,p in enumerate(pdf.pages,1):
            pages.append({'page':i,'width':p.width,'height':p.height,'chars':p.chars,'lines':p.lines,'rects':p.rects,'images':p.images,'text':p.extract_text()})
            print(stem,'PAGE',i,'size',p.width,p.height)
            print(p.extract_text())
            print('FONTS',sorted({(c['fontname'],round(c['size'],3)) for c in p.chars}))
            print('LINES',[(round(l['x0'],3),round(l['top'],3),round(l['width'],3),round(l['height'],3),l['linewidth']) for l in p.lines])
            for l in p.extract_text_lines():
                if any(k in l['text'] for k in ['毕业设计','课题名称','副标题','学院','专业','学生姓名','学号','年','审核','签名']):
                    print('POSITION',l['text'],round(l['x0'],3),round(l['top'],3))
        (root/(stem+'_layout.json')).write_text(json.dumps(pages,ensure_ascii=False,default=str),encoding='utf-8')
