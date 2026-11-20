"""Scientific plots for the three paired seeds and fixed-before-inference examples."""
import argparse,importlib.util,json,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
ROOT=Path('/home/ysheng4/research/GSMF-RS-DIL');sys.path.insert(0,str(ROOT))
from road_dil.protocol import CLASSES,sha256,write_json,map_label
from tools.road.five_common import REAL
spec=importlib.util.spec_from_file_location('accepted_figures_A',ROOT/'experiments/road_five_domain/formal-A-plan-20261111-140000/scripts/figures_A.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
def read(p):return json.loads(Path(p).read_text())
def main(prep,run):
 prep=Path(prep).resolve();run=Path(run).resolve();out=Path(read(run/'results-index.json')['directory']);assert read(out/'training-independent-check.json')['status']==read(out/'protocol-independent-check.json')['status']=='PASS'
 ao=Path(read(Path(read(prep/'formal-plans.json')['A']['formal_output'])/'results-index.json')['directory']);allcells=read(ao/'cells.json')+read(out/'cells.json');lookup={(c['model'],c['condition']):c for c in allcells};matrices=read(out/'three-seed-stage-matrices.json');stats=read(out/'three-seed-all-conditions.json');figs=out/'figures';figs.mkdir(exist_ok=False);stages=['Source','Fog','Rain','Snow','Night'];colors=dict(ft='#2878b5',gsmf='#d84a38');methods=('ft','gsmf');save=helper.save
 fig,axes=plt.subplots(2,3,figsize=(15,9))
 for i,m in enumerate(methods):
  for s in range(3):
   ax=axes[i,s];rows=matrices['%s-seed%d-ABCDE'%(m,s)];vals=np.array([[r['values'][d] for d in REAL] for r in rows]);im=ax.imshow(vals,vmin=0,vmax=100,cmap='viridis');ax.set_title('%s seed%d'%(m.upper(),s));ax.set_xticks(range(5));ax.set_xticklabels(['CS','Fog','Rain','Snow','Night'],rotation=25);ax.set_yticks(range(5));ax.set_yticklabels(stages)
   for y in range(5):
    for x in range(5):ax.text(x,y,'%.1f'%vals[y,x],ha='center',va='center',color='white' if vals[y,x]<60 else 'black',fontsize=9)
 fig.subplots_adjust(right=.91,wspace=.3,hspace=.3);fig.colorbar(im,cax=fig.add_axes([.93,.2,.015,.6]),label='mIoU (%)');save(fig,figs/'stage-matrices-all-three-seeds')
 fig,ax=plt.subplots(figsize=(8,4.5))
 for m in methods:
  for s in range(3):ax.plot(range(5),[r['seen_domain_equal_mean'] for r in matrices['%s-seed%d-ABCDE'%(m,s)]],color=colors[m],alpha=.25,linewidth=1)
  vs=[stats['composites']['seen-domain-mean-after-'+st][m] for st in stages];ax.errorbar(range(5),[v['mean'] for v in vs],yerr=[v['sample_std'] for v in vs],marker='o',capsize=4,label=m.upper()+' mean +/- sample SD',color=colors[m])
 ax.set_xticks(range(5));ax.set_xticklabels(stages);ax.set_ylabel('Seen real-domain equal mean mIoU (%)');ax.grid(alpha=.25);ax.legend();fig.tight_layout();save(fig,figs/'seen-domain-mean-three-seeds')
 fig,ax=plt.subplots(figsize=(9,5))
 for c in REAL:
  vs=[stats['paired_gsmf_minus_ft']['%d/%s'%(t,c)] for t in range(5)];ax.errorbar(range(5),[v['mean'] for v in vs],yerr=[v['sample_std'] for v in vs],marker='o',capsize=3,label=c)
 ax.axhline(0,color='black',linewidth=.8);ax.set_xticks(range(5));ax.set_xticklabels(stages);ax.set_ylabel('Paired GSMF - FT mIoU (pp), mean +/- sample SD');ax.grid(alpha=.25);ax.legend();fig.tight_layout();save(fig,figs/'paired-differences-three-seeds')
 fig,axes=plt.subplots(1,2,figsize=(13,4.5),sharey=True)
 for ax,t in zip(axes,(1,4)):
  for m in methods:
   vs=[stats['conditions']['%d/%s'%(t,c)][m] for c in ('clear','fog005','fog010','fog020')];ax.errorbar([0,.005,.01,.02],[v['mean'] for v in vs],yerr=[v['sample_std'] for v in vs],marker='o',capsize=4,label=m.upper(),color=colors[m])
  ax.set_title('After '+stages[t]);ax.set_xlabel('Synthetic fog beta');ax.grid(alpha=.25);ax.legend()
 axes[0].set_ylabel('mIoU (%), mean +/- sample SD');fig.tight_layout();save(fig,figs/'synthetic-fog-three-seeds-sparse-plan')
 consistency=read(out/'confusion-consistency-three-seeds.json');fig,axes=plt.subplots(2,3,figsize=(15,8),sharex=True)
 for i,m in enumerate(methods):
  for j,target in enumerate(('terrain','truck','building')):
   ax=axes[i,j]
   for s,v in consistency[m][target]['fractions_per_seed'].items():ax.plot(range(5),100*np.asarray(v),marker='o',label='seed'+s)
   ax.set_title(m.upper()+': GT road -> '+target);ax.set_xticks(range(5));ax.set_xticklabels(stages,rotation=25);ax.grid(alpha=.25);ax.legend()
  axes[i,0].set_ylabel('GT road pixels predicted as target (%)')
 fig.tight_layout();save(fig,figs/'CS-road-confusion-three-seeds')
 fixed=read(prep/'fixed-samples.json');proof=[]
 for cond,ids in [('clear',fixed['CS']),('snow',fixed['DE']['D']['ids']),('night',fixed['DE']['E']['ids'])]:
  ev=read(Path(lookup['ft-seed1-E',cond]['evidence'])/'evaluation.json');records=[json.loads(x) for x in Path(ev['manifest']).read_text().splitlines()];byid={r['id']:r for r in records}
  for ident in ids:
   r=byid[ident];panels=[];labels=[]
   for m in methods:
    for s in range(3):
     panels.extend([Image.open(r['image']).convert('RGB'),helper.color(map_label(np.array(Image.open(r['label'])),r['encoding']))]);labels.extend(['%s seed%d %s RGB'%(m.upper(),s,cond),'GT'])
     names=['source',m+'_fog',m+'_rain',m+'-seed0-D',m+'-seed0-E'] if s==0 else ['source']+['%s-seed%d-%s'%(m,s,d) for d in 'BCDE']
     for st,name in zip(stages,names):
      p=Path(lookup[name,cond]['evidence'])/'predictions'/(Path(r['image']).stem+'.png');panels.append(helper.color(np.array(Image.open(p))));labels.append('%s s%d after %s'%(m.upper(),s,st));proof.append(dict(condition=cond,id=ident,model=name,path=str(p),sha256=sha256(p)))
   helper.montage(panels,labels,7,figs/(cond+'-'+Path(r['image']).stem+'.png'))
 raw=[p for p in (out/'fixed-samples').rglob('*.png') if p.relative_to(out/'fixed-samples').parts[0]!='source'];assert len(raw)==288,len(raw)
 for p in raw:
  model,cond=p.relative_to(out/'fixed-samples').parts[:2];assert sha256(p)==sha256(Path(lookup[model,cond]['evidence'])/'predictions'/p.name)
 proof=list({r['path']:r for r in proof}.values());write_json(out/'fixed-sample-selection-and-index.json',dict(status='PASS',selected_before_inference=True,selection_sha256=sha256(prep/'fixed-samples.json'),new_raw_CS_masks=96,new_raw_DE_masks=192,total_new_raw_masks=288,inherited_Source_raw_masks=12,aligned_figures=18,samples=proof,display='Full-frame nearest-neighbor thumbnails, fixed IDs shared across methods/stages/seeds; no effect-based selection.'))
 print('PASS B plots and fixed 18 aligned examples; 288 new raw masks, 12 inherited Source masks')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--prepare',required=True);p.add_argument('--run',required=True);a=p.parse_args();main(a.prepare,a.run)
