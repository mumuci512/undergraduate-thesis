"""Compare real PDF glyphs and frame geometry against native Word output."""
import argparse,json,hashlib
from pathlib import Path
import pdfplumber

p=argparse.ArgumentParser()
p.add_argument('reference',type=Path)
p.add_argument('candidate',type=Path)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
def chars(page):
    return [c for line in page.extract_text_lines() for c in line['chars'] if c['text'].strip()]
def family(c):
    return c['fontname'].split('+')[-1]
def rules(page):
    horizontal={};vertical=[]
    shapes=list(page.rects)
    for line in page.lines:
        width=line['linewidth']
        if line['height']==0:
            shapes.append({'x0':line['x0'],'x1':line['x1'],'top':line['top']-width/2,'width':line['width'],'height':width,'non_stroking_color':line['stroking_color']})
        elif line['width']==0:
            shapes.append({'x0':line['x0']-width/2,'x1':line['x1']+width/2,'top':line['top'],'width':width,'height':line['height'],'non_stroking_color':line['stroking_color']})
    for r in shapes:
        color=r.get('non_stroking_color',0)
        color=color[0] if isinstance(color,(tuple,list)) else color
        if color!=0:continue
        if 0<r['height']<1:
            key=(round(r['top'],2),round(r['height'],2))
            horizontal.setdefault(key,[]).append([r['x0'],r['x1']])
        if 0<r['width']<1 and r['height']>20:
            vertical.append([r['x0'],r['top'],r['width'],r['height']])
    result=[]
    for (top,height),parts in horizontal.items():
        merged=[]
        for left,right in sorted(parts):
            if merged and left<=merged[-1][1]+.025:merged[-1][1]=max(right,merged[-1][1])
            else:merged.append([left,right])
        result.extend([left,top,right-left,height] for left,right in merged if right-left>2)
    return sorted(result+vertical,key=lambda r:(round(r[1],2),round(r[0],2),r[2]))
checks=[]; differences=[]
with pdfplumber.open(a.reference) as ref,pdfplumber.open(a.candidate) as candidate:
    checks.append({'check':'page_count','pass':len(ref.pages)==len(candidate.pages),'reference':len(ref.pages),'candidate':len(candidate.pages)})
    for i,(rp,cp) in enumerate(zip(ref.pages,candidate.pages),1):
        checks.append({'check':'page_size','page':i,'pass':abs(rp.width-cp.width)<.001 and abs(rp.height-cp.height)<.001})
        rc,cc=chars(rp),chars(cp)
        same=''.join(c['text'] for c in rc)==''.join(c['text'] for c in cc)
        checks.append({'check':'visible_text','page':i,'pass':same,'reference_characters':len(rc),'candidate_characters':len(cc)})
        rr,cr=rules(rp),rules(cp)
        rule_error=max((abs(x-y) for r,c in zip(rr,cr) for x,y in zip(r,c)),default=0)
        checks.append({'check':'rule_geometry','page':i,'pass':len(rr)==len(cr) and rule_error<.025,'reference_rules':len(rr),'candidate_rules':len(cr),'maximum_error_bp':rule_error})
        if same:
            dx=[];dy=[];ds=[]; fonts=[]; colors=[]
            for x,y in zip(rc,cc):
                dx.append(abs(x['x0']-y['x0']))
                dy.append(abs((rp.height-x['matrix'][5])-(cp.height-y['matrix'][5])))
                ds.append(abs(x['size']-y['size']))
                if family(x)!=family(y):fonts.append([x['text'],family(x),family(y)])
                xc=x['non_stroking_color'];yc=y['non_stroking_color']
                xc=xc[0] if isinstance(xc,(list,tuple)) else xc
                yc=yc[0] if isinstance(yc,(list,tuple)) else yc
                if abs(xc-yc)>.00001:colors.append([x['text'],xc,yc])
            checks += [
                {'check':'glyph_origins','page':i,'pass':max(dx+dy,default=0)<.025,'maximum_x_error_bp':max(dx,default=0),'maximum_baseline_error_bp':max(dy,default=0)},
                {'check':'font_sizes','page':i,'pass':max(ds,default=0)<.001,'maximum_error_bp':max(ds,default=0)},
                {'check':'font_faces','page':i,'pass':not fonts,'differences':fonts},
                {'check':'text_colors','page':i,'pass':not colors,'differences':colors}]
            differences.append({'page':i,'max_x_bp':max(dx,default=0),'max_y_bp':max(dy,default=0)})
result={'reference_sha256':hashlib.sha256(a.reference.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(a.candidate.read_bytes()).hexdigest(),'checks':checks,'all_pass':all(c['pass'] for c in checks)}
a.out.parent.mkdir(parents=True,exist_ok=True)
a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'all_pass':result['all_pass'],'failed':[x for x in checks if not x['pass']],'positions':differences},ensure_ascii=False))
raise SystemExit(0 if result['all_pass'] else 1)
