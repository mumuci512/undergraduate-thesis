#!/usr/bin/env python
"""Scientific plots and preselected aligned comparisons; no sample selection by results."""
import argparse,json,csv,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path('/home/ysheng4/research/GSMF-RS-DIL');sys.path.insert(0,str(ROOT))
from road_dil.protocol import CLASSES,PALETTE,sha256,write_json,map_label
from tools.road.rain_common import METHODS,CONDITIONS,SEVERITY

def read(p):return json.loads(Path(p).read_text())
def records(p):return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
def color(a):
 rgb=np.zeros((*a.shape,3),np.uint8)
 for k,c in enumerate(PALETTE):rgb[a==k]=c
 return Image.fromarray(rgb)
def savefig(fig,base):
 for suffix in ('png','pdf','svg'):fig.savefig(str(base)+'.'+suffix,dpi=180,bbox_inches='tight')
 plt.close(fig)
def montage(panels,labels,cols,rows,path):
 tw,th=288,162;labelheight=26
 canvas=Image.new('RGB',(tw*cols,(th+labelheight)*rows),'white');draw=ImageDraw.Draw(canvas)
 try:font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',13)
 except OSError:font=ImageFont.load_default()
 for i,(im,label) in enumerate(zip(panels,labels)):
  x=(i%cols)*tw;y=(i//cols)*(th+labelheight);draw.text((x+4,y+4),label,fill='black',font=font)
  panel=im.copy();panel.thumbnail((tw,th),Image.Resampling.NEAREST if hasattr(Image,'Resampling') else Image.NEAREST);canvas.paste(panel,(x,y+labelheight))
 canvas.save(path)
def main(prep,run):
 prep=Path(prep).resolve();run=Path(run).resolve();out=run/'results';assert read(out/'protocol-independent-check.json')['status']=='PASS'
 figs=out/'figures';figs.mkdir(exist_ok=False);cells=read(out/'42-cells.json');lookup={(c['model'],c['condition']):c for c in cells};stages=read(out/'real-domain-stages.json')
 colors=dict(ft='#2878b5',gsmf='#d84a38',lwf='#399456');beta=[0,.005,.01,.02]
 fig,axes=plt.subplots(1,3,figsize=(13,3.7),sharey=True)
 for ax,m in zip(axes,METHODS):
  for label,key,style,color_ in [('Source','source',':','#333333'),('After Fog',m+'_fog','--',colors[m]),('After Rain',m+'_rain','-',colors[m])]:
   ax.plot(beta,[lookup[key,c]['mIoU'] for c in CONDITIONS[:4]],linestyle=style,marker='o',label=label,color=color_)
  ax.set_title(m.upper());ax.set_xlabel('Synthetic fog beta');ax.set_xticks(beta);ax.grid(alpha=.25);ax.legend(fontsize=9)
 axes[0].set_ylabel('mIoU (%)');fig.suptitle('Fixed paired Cityscapes scenes; seed 0');fig.tight_layout();savefig(fig,figs/'synthetic-miou')
 fig,axes=plt.subplots(1,3,figsize=(13,3.7),sharey=True)
 rows=[]
 for ax,m in zip(axes,METHODS):
  for label,key,style,color_ in [('Source','source',':','#333333'),('After Fog',m+'_fog','--',colors[m]),('After Rain',m+'_rain','-',colors[m])]:
   ys=[lookup[key,c]['mIoU']-lookup[key,'clear']['mIoU'] for c in CONDITIONS[:4]]
   ax.plot(beta,ys,linestyle=style,marker='o',label=label,color=color_)
   rows.extend(dict(model=key,beta=b,condition=c,mIoU=lookup[key,c]['mIoU'],condition_minus_own_clear_pp=y) for b,c,y in zip(beta,CONDITIONS[:4],ys))
  ax.axhline(0,color='gray',linewidth=.7);ax.set_title(m.upper());ax.set_xlabel('Synthetic fog beta');ax.set_xticks(beta);ax.grid(alpha=.25);ax.legend(fontsize=9)
 axes[0].set_ylabel('Condition minus own clear (pp)');fig.tight_layout();savefig(fig,figs/'synthetic-change-from-clear')
 with (out/'synthetic-change-from-clear.csv').open('x',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 fig,axes=plt.subplots(1,3,figsize=(12,4.4),sharey=True)
 for ax,m in zip(axes,METHODS):
  vals=np.array([[lookup[k,c]['mIoU'] for c in ('clear','fog','rain')] for k in ('source',m+'_fog',m+'_rain')]);im=ax.imshow(vals,vmin=0,vmax=100,cmap='viridis')
  ax.set_title(m.upper());ax.set_xticks(range(3));ax.set_xticklabels(['CS','ACDC-fog','ACDC-rain']);ax.set_yticks(range(3));ax.set_yticklabels(['Source','After Fog','After Rain'])
  for i in range(3):
   for j in range(3):ax.text(j,i,'%.2f'%vals[i,j],ha='center',va='center',color='white' if vals[i,j]<65 else 'black',fontsize=10)
 fig.subplots_adjust(right=.90,wspace=.3);fig.colorbar(im,cax=fig.add_axes([.92,.22,.015,.56]),label='mIoU (%)');savefig(fig,figs/'real-domain-stage-matrices')
 final=[lookup[m+'_rain',c] for m in METHODS for c in ('clear','fog','rain')];values=np.array([[r['IoU'][k] if r['IoU'][k] is not None else np.nan for r in final] for k in CLASSES])
 fig,ax=plt.subplots(figsize=(10,8));im=ax.imshow(values,aspect='auto',vmin=0,vmax=100,cmap='viridis');ax.set_yticks(range(19));ax.set_yticklabels(CLASSES);ax.set_xticks(range(9));ax.set_xticklabels([r['model']+'/'+r['condition'] for r in final],rotation=55,ha='right');fig.colorbar(im,label='IoU (%)');fig.tight_layout();savefig(fig,figs/'final-class-iou')
 # Use exactly the earlier fixed IDs, without inspecting outcomes to select scenes.
 cs=read(SEVERITY/'prepared-20261110/sample_ids.json');rain=read(prep/'rain-fixed-samples.json');sampleproof=[]
 for scene in cs['ids']:
  panels=[];labels=[]
  for cond in CONDITIONS[:4]:
   rs=records(read(Path(lookup['ft_rain',cond]['evidence'])/'evaluation.json')['manifest'])
   r=next(r for r in rs if r['id']==scene);panels.extend([Image.open(r['image']).convert('RGB'),color(map_label(np.array(Image.open(r['label'])),r['encoding']))]);labels.extend([cond+' input',cond+' GT'])
   for m in METHODS:
    path=Path(lookup[m+'_rain',cond]['evidence'])/'predictions'/(Path(r['image']).stem+'.png');panels.append(color(np.array(Image.open(path))));labels.append(m.upper()+' after Rain')
    sampleproof.append(dict(type='CS',scene=scene,condition=cond,method=m,prediction=str(path),sha256=sha256(path)))
  montage(panels,labels,5,4,figs/('CS-'+scene+'.png'))
 rainrecords={r['id']:r for r in records(prep/'data/C_val.jsonl')}
 for ident in rain['ids']:
  r=rainrecords[ident];panels=[];labels=[]
  for suffix in ('_fog','_rain'):
   panels.extend([Image.open(r['image']).convert('RGB'),color(map_label(np.array(Image.open(r['label'])),r['encoding']))]);labels.extend(['Rain input','GT'])
   for key in [m+suffix for m in METHODS]+['source']:
    path=Path(lookup[key,'rain']['evidence'])/'predictions'/(Path(r['image']).stem+'.png');panels.append(color(np.array(Image.open(path))));labels.append(key)
    sampleproof.append(dict(type='Rain',id=ident,model=key,prediction=str(path),sha256=sha256(path)))
  montage(panels,labels,6,2,figs/('Rain-'+Path(r['image']).stem+'.png'))
 sampleproof=list({r['prediction']:r for r in sampleproof}.values())
 write_json(out/'fixed-sample-selection-and-index.json',dict(status='PASS',CS_selection_evidence=str(SEVERITY/'prepared-20261110/sample_ids.json'),CS_selection_sha256=sha256(SEVERITY/'prepared-20261110/sample_ids.json'),Rain_selection_evidence=str(prep/'rain-fixed-samples.json'),Rain_selection_sha256=sha256(prep/'rain-fixed-samples.json'),CS_new_raw_predictions=72,Rain_unique_raw_predictions=42,Rain_fixed_scenes=6,selected_before_inference=True,samples=sampleproof,display='Full frame resized by nearest neighbor; colorized GT/prediction, no selected crops'))
 print('PASS figures and predetermined aligned samples')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--prepare',required=True);p.add_argument('--run',required=True);a=p.parse_args();main(a.prepare,a.run)
