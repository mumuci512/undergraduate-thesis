#!/usr/bin/env python
"""Five-domain scientific figures and fixed-before-inference aligned full-frame examples."""
import argparse,json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path('/home/ysheng4/research/GSMF-RS-DIL');sys.path.insert(0,str(ROOT))
from road_dil.protocol import CLASSES,PALETTE,sha256,write_json,map_label
from tools.road.five_common import REAL

def read(p):return json.loads(Path(p).read_text())
def records(p):return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
def color(a):
 out=np.zeros((*a.shape,3),np.uint8)
 for i,c in enumerate(PALETTE):out[a==i]=c
 return Image.fromarray(out)
def save(fig,path):
 for ext in ('png','pdf','svg'):fig.savefig(str(path)+'.'+ext,dpi=180,bbox_inches='tight')
 plt.close(fig)
def montage(panels,labels,cols,path):
 w,h,lh=300,169,26;rows=(len(panels)+cols-1)//cols;canvas=Image.new('RGB',(w*cols,(h+lh)*rows),'white');draw=ImageDraw.Draw(canvas)
 try:font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
 except OSError:font=ImageFont.load_default()
 for i,(im,label) in enumerate(zip(panels,labels)):
  x=(i%cols)*w;y=(i//cols)*(h+lh);draw.text((x+3,y+4),label,fill='black',font=font);im=im.copy();im.thumbnail((w,h),Image.Resampling.NEAREST if hasattr(Image,'Resampling') else Image.NEAREST);canvas.paste(im,(x,y+lh))
 canvas.save(path)
def main(prep,run):
 prep=Path(prep).resolve();run=Path(run).resolve();out=Path(read(run/'results-index.json')['directory']);assert read(out/'training-independent-check.json')['status']=='PASS' and read(out/'protocol-independent-check.json')['status']=='PASS';figs=out/'figures';figs.mkdir(exist_ok=False);cells=read(out/'cells.json');lookup={(c['model'],c['condition']):c for c in cells};matrices=read(out/'stage-matrices.json');deltas=read(out/'signed-deltas-and-forgetting.json');methods=('ft','gsmf','lwf');stages=['Source','Fog','Rain','Snow','Night'];colors=dict(ft='#2878b5',gsmf='#d84a38',lwf='#399456')
 fig,axes=plt.subplots(1,3,figsize=(15,4.5))
 for ax,m in zip(axes,methods):
  rows=matrices[m+'-seed0-ABCDE'];vals=np.array([[r['values'][d] for d in REAL] for r in rows]);im=ax.imshow(vals,vmin=0,vmax=100,cmap='viridis');ax.set_title(m.upper());ax.set_xticks(range(5));ax.set_xticklabels(['CS','Fog','Rain','Snow','Night'],rotation=35);ax.set_yticks(range(5));ax.set_yticklabels(stages)
  for i in range(5):
   for j in range(5):ax.text(j,i,'%.1f'%vals[i,j],ha='center',va='center',color='white' if vals[i,j]<60 else 'black',fontsize=9)
 fig.subplots_adjust(right=.91,wspace=.3);fig.colorbar(im,cax=fig.add_axes([.93,.2,.015,.6]),label='mIoU (%)');save(fig,figs/'five-real-domain-stage-matrices')
 fig,ax=plt.subplots(figsize=(8,4.5))
 for m in methods:ax.plot(range(5),[r['seen_domain_equal_mean'] for r in matrices[m+'-seed0-ABCDE']],marker='o',label=m.upper(),color=colors[m])
 ax.set_xticks(range(5));ax.set_xticklabels(stages);ax.set_ylabel('Seen real-domain equal mean mIoU (%)');ax.set_xlabel('After training stage');ax.grid(alpha=.25);ax.legend();fig.tight_layout();save(fig,figs/'seen-domain-mean')
 fig,axes=plt.subplots(1,3,figsize=(14,4),sharey=True);beta=[0,.005,.01,.02];conditions=('clear','fog005','fog010','fog020')
 for ax,m in zip(axes,methods):
  for label,name in zip(stages,['source',m+'_fog',m+'_rain',m+'-seed0-D',m+'-seed0-E']):ax.plot(beta,[lookup[name,d]['mIoU'] for d in conditions],marker='o',label=label)
  ax.set_title(m.upper());ax.set_xlabel('Synthetic fog beta');ax.set_xticks(beta);ax.grid(alpha=.25);ax.legend(fontsize=8)
 axes[0].set_ylabel('mIoU (%)');fig.tight_layout();save(fig,figs/'synthetic-fog-separate-conditions')
 fig,ax=plt.subplots(figsize=(9,4.5));x=np.arange(4);width=.25
 for i,m in enumerate(methods):ax.bar(x+(i-1)*width,[deltas[m+'-seed0-ABCDE']['old_domain_forgetting'][d]['signed_forgetting'] for d in REAL[:-1]],width,label=m.upper(),color=colors[m])
 ax.axhline(0,color='black',linewidth=.8);ax.set_xticks(x);ax.set_xticklabels(['CS','Fog','Rain','Snow']);ax.set_ylabel('Signed old-domain forgetting (pp)');ax.legend();fig.tight_layout();save(fig,figs/'signed-old-domain-forgetting')
 fig,axes=plt.subplots(1,3,figsize=(14,4),sharey=True)
 for ax,m in zip(axes,methods):
  names=['source',m+'_fog',m+'_rain',m+'-seed0-D',m+'-seed0-E']
  for target in ('terrain','truck','building'):
   j=CLASSES.index(target);ys=[]
   for name in names:
    mat=np.array(lookup[name,'clear']['confusion_matrix']);ys.append(100*mat[0,j]/mat[0].sum())
   ax.plot(range(5),ys,marker='o',label='road -> '+target)
  ax.set_title(m.upper());ax.set_xticks(range(5));ax.set_xticklabels(stages,rotation=30);ax.grid(alpha=.25);ax.legend(fontsize=8)
 axes[0].set_ylabel('Fraction of GT road pixels (%)');fig.tight_layout();save(fig,figs/'CS-road-misclassification-destinations')
 # Exactly the preselected IDs; full frames, no chosen crops.
 fixed=read(prep/'fixed-samples.json');proof=[]
 for cond,ids in [('clear',fixed['CS']),('snow',fixed['DE']['D']['ids']),('night',fixed['DE']['E']['ids'])]:
  for ident in ids:
   rs=records(read(Path(lookup['ft-seed0-E',cond]['evidence'])/'evaluation.json')['manifest']);r=next(r for r in rs if r['id']==ident);panels=[];labels=[]
   for m in methods:
    panels += [Image.open(r['image']).convert('RGB'),color(map_label(np.array(Image.open(r['label'])),r['encoding']))];labels += [m.upper()+' '+cond+' RGB','GT']
    for label,name in zip(stages,['source',m+'_fog',m+'_rain',m+'-seed0-D',m+'-seed0-E']):
     pred=Path(lookup[name,cond]['evidence'])/'predictions'/(Path(r['image']).stem+'.png');panels.append(color(np.array(Image.open(pred))));labels.append(m.upper()+' after '+label);proof.append(dict(condition=cond,id=ident,model=name,path=str(pred),sha256=sha256(pred)))
   montage(panels,labels,7,figs/(cond+'-'+Path(r['image']).stem+'.png'))
 raw=list((out/'fixed-samples').rglob('*.png'));assert len(raw)==192,len(raw)
 for path in raw:
  rel=path.relative_to(out/'fixed-samples');model,cond=rel.parts[:2];original=Path(lookup[model,cond]['evidence'])/'predictions'/path.name;assert sha256(path)==sha256(original)
 proof=list({r['path']:r for r in proof}.values());write_json(out/'fixed-sample-selection-and-index.json',dict(status='PASS',selected_before_inference=True,selection=str(prep/'fixed-samples.json'),selection_sha256=sha256(prep/'fixed-samples.json'),CS_fixed_scenes=6,Snow_fixed_scenes=6,Night_fixed_scenes=6,new_raw_CS_masks=36,all_DE_raw_masks=156,total_raw_masks=192,aligned_figures=18,samples=proof,display='Full frame nearest-neighbor thumbnail; no selection by effect and no selected crops.'))
 print('PASS scientific figures and 18 fixed aligned full-frame examples; 192 raw masks')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--prepare',required=True);p.add_argument('--run',required=True);a=p.parse_args();main(a.prepare,a.run)
