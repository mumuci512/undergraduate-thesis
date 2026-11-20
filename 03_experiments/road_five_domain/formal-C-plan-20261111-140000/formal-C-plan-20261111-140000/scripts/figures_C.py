"""Single-seed order figures and preselected aligned full-frame examples."""
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
 arun=Path(read(prep/'formal-plans.json')['A']['formal_output']);ao=Path(read(arun/'results-index.json')['directory']);am=read(ao/'stage-matrices.json');cm=read(out/'stage-matrices.json');ad=read(ao/'signed-deltas-and-forgetting.json');cd=read(out/'signed-deltas-and-forgetting.json');al={(c['model'],c['condition']):c for c in read(ao/'cells.json')};cl={(c['model'],c['condition']):c for c in read(out/'cells.json')};figs=out/'figures';figs.mkdir(exist_ok=False);methods=('ft','gsmf');orders=('ABCDE','AEDCB');stages=dict(ABCDE=['Source','Fog','Rain','Snow','Night'],AEDCB=['Source','Night','Snow','Rain','Fog']);colors=dict(ft='#2878b5',gsmf='#d84a38');save=helper.save
 def rows(m,o):return (am if o=='ABCDE' else cm)[m+'-seed0-'+o]
 fig,axes=plt.subplots(2,2,figsize=(12,10))
 for i,m in enumerate(methods):
  for j,o in enumerate(orders):
   ax=axes[i,j];vals=np.array([[r['values'][d] for d in REAL] for r in rows(m,o)]);im=ax.imshow(vals,vmin=0,vmax=100,cmap='viridis');ax.set_title(m.upper()+' '+o+' seed0');ax.set_xticks(range(5));ax.set_xticklabels(['CS','Fog','Rain','Snow','Night']);ax.set_yticks(range(5));ax.set_yticklabels(stages[o])
   for y in range(5):
    for x in range(5):ax.text(x,y,'%.1f'%vals[y,x],ha='center',va='center',color='white' if vals[y,x]<60 else 'black')
 fig.subplots_adjust(right=.9,wspace=.35,hspace=.3);fig.colorbar(im,cax=fig.add_axes([.92,.2,.015,.6]),label='mIoU (%)');save(fig,figs/'stage-matrices-both-orders')
 fig,axes=plt.subplots(1,2,figsize=(12,4.5))
 for ax,o in zip(axes,orders):
  for m in methods:ax.plot(range(5),[r['seen_domain_equal_mean'] for r in rows(m,o)],marker='o',label=m.upper(),color=colors[m])
  ax.set_title(o+' (seen domains differ by position)');ax.set_xticks(range(5));ax.set_xticklabels(stages[o]);ax.grid(alpha=.25);ax.legend();ax.set_ylabel('Seen-domain equal mean mIoU (%)')
 fig.tight_layout();save(fig,figs/'seen-domain-means-by-order')
 fig,ax=plt.subplots(figsize=(10,4.5));x=np.arange(5)
 for i,m in enumerate(methods):ax.bar(x+(i-.5)*.35,[rows(m,'AEDCB')[-1]['values'][d]-rows(m,'ABCDE')[-1]['values'][d] for d in REAL],.35,label=m.upper(),color=colors[m])
 ax.axhline(0,color='black',linewidth=.8);ax.set_xticks(x);ax.set_xticklabels(['CS','Fog','Rain','Snow','Night']);ax.set_ylabel('Final reverse (after Fog) - main (after Night), pp');ax.legend();fig.tight_layout();save(fig,figs/'final-real-domain-order-differences')
 fig,axes=plt.subplots(1,2,figsize=(12,4.5))
 for ax,o,ds,domains in zip(axes,orders,(ad,cd),(('clear','fog','rain','snow'),('clear','night','snow','rain'))):
  for i,m in enumerate(methods):ax.bar(np.arange(4)+(i-.5)*.35,[ds[m+'-seed0-'+o]['old_domain_forgetting'][d]['signed_forgetting'] for d in domains],.35,label=m.upper(),color=colors[m])
  ax.axhline(0,color='black',linewidth=.8);ax.set_xticks(range(4));ax.set_xticklabels(domains);ax.set_title(o+' (different old-domain sets)');ax.set_ylabel('Signed old-domain forgetting (pp)');ax.legend()
 fig.tight_layout();save(fig,figs/'signed-forgetting-both-orders')
 fig,axes=plt.subplots(1,2,figsize=(12,4.5),sharey=True)
 for ax,m in zip(axes,methods):
  for o,lookup in zip(orders,(al,cl)):
   final=rows(m,o)[-1]['stage'];ax.plot([0,.005,.01,.02],[lookup[final,c]['mIoU'] for c in ('clear','fog005','fog010','fog020')],marker='o',label=o+' final after '+stages[o][-1])
  ax.set_title(m.upper());ax.set_xlabel('Synthetic fog beta');ax.set_ylabel('mIoU (%)');ax.grid(alpha=.25);ax.legend(fontsize=8)
 fig.tight_layout();save(fig,figs/'synthetic-final-models-by-order')
 fig,axes=plt.subplots(2,2,figsize=(12,8),sharey=True)
 for i,m in enumerate(methods):
  for j,o in enumerate(orders):
   ax=axes[i,j];lookup=al if o=='ABCDE' else cl
   for target in ('terrain','truck','building'):
    k=CLASSES.index(target);vals=[]
    for row in rows(m,o):mat=np.asarray(lookup[row['stage'],'clear']['confusion_matrix']);vals.append(100*mat[0,k]/mat[0].sum())
    ax.plot(range(5),vals,marker='o',label='road -> '+target)
   ax.set_title(m.upper()+' '+o);ax.set_xticks(range(5));ax.set_xticklabels(stages[o],rotation=25);ax.set_ylabel('Fraction of GT road pixels (%)');ax.grid(alpha=.25);ax.legend(fontsize=8)
 fig.tight_layout();save(fig,figs/'CS-road-destinations-both-orders')
 fixed=read(prep/'fixed-samples.json');proof=[]
 for cond,ids in [('clear',fixed['CS']),('snow',fixed['DE']['D']['ids']),('night',fixed['DE']['E']['ids'])]:
  ev=read(Path(cl['ft-seed0-B',cond]['evidence'])/'evaluation.json');records=[json.loads(x) for x in Path(ev['manifest']).read_text().splitlines()];byid={r['id']:r for r in records}
  for ident in ids:
   r=byid[ident];panels=[];labels=[]
   for m in methods:
    for o,lookup in zip(orders,(al,cl)):
     panels.extend([Image.open(r['image']).convert('RGB'),helper.color(map_label(np.array(Image.open(r['label'])),r['encoding']))]);labels.extend([m.upper()+' '+o+' RGB','GT'])
     for st,row in zip(stages[o],rows(m,o)):
      name=row['stage'];p=Path(lookup[name,cond]['evidence'])/'predictions'/(Path(r['image']).stem+'.png');panels.append(helper.color(np.array(Image.open(p))));labels.append(m.upper()+' '+o+' '+st);proof.append(dict(condition=cond,id=ident,model=name,order=o,path=str(p),sha256=sha256(p)))
   helper.montage(panels,labels,7,figs/(cond+'-'+Path(r['image']).stem+'.png'))
 raw=[p for p in (out/'fixed-samples').rglob('*.png') if p.relative_to(out/'fixed-samples').parts[0]!='source'];assert len(raw)==144,len(raw)
 for p in raw:
  model,cond=p.relative_to(out/'fixed-samples').parts[:2];assert sha256(p)==sha256(Path(cl[model,cond]['evidence'])/'predictions'/p.name)
 proof=list({r['path']:r for r in proof}.values());write_json(out/'fixed-sample-selection-and-index.json',dict(status='PASS',selected_before_inference=True,selection_sha256=sha256(prep/'fixed-samples.json'),new_raw_CS_masks=48,new_raw_DE_masks=96,total_new_raw_masks=144,inherited_Source_raw_masks=12,aligned_figures=18,samples=proof,display='Full-frame nearest-neighbor thumbnails; fixed IDs across methods/stages/orders; no effect-based selection. Main-order raw examples indexed in phase A.'))
 print('PASS C figures and 18 fixed aligned examples; 144 new masks +12 inherited Source masks')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--prepare',required=True);p.add_argument('--run',required=True);a=p.parse_args();main(a.prepare,a.run)
