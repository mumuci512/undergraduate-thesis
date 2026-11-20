#!/usr/bin/env python3
"""Aggregate 12 completed existing road evaluator outputs; never infer missing cells."""
import argparse,csv,hashlib,json,shutil,sys
from pathlib import Path
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
ROOT=Path('/home/ysheng4/research/GSMF-RS-DIL');sys.path.insert(0,str(ROOT))
from road_dil.protocol import CLASSES,PALETTE,map_label
BETAS=('0','0.005','0.01','0.02');STAGES=('source','ft','gsmf')
HASHES=dict(source='a66c958ee774d27566b901ad6570c0a3b83263e9d74389e1c2e025c6c2673d93',ft='99914df527d8506c33178ef6ea1caf7f0ed1d07369858e37275205d60a57d516',gsmf='fc227c57dc3e47a134ef51b282964654a0210f3c06f00bd0d3e81b706850b24a')
def write_csv(path,rows,fields):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def main():
    p=argparse.ArgumentParser();p.add_argument('--prepared',type=Path,required=True);p.add_argument('--audit',type=Path,required=True);p.add_argument('--runs',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    audit=json.loads((a.audit/'audit.json').read_text()); manifest=a.audit/'available_manifest.csv'
    if hashlib.sha256(manifest.read_bytes()).hexdigest()!=audit['manifest_sha256']:raise ValueError('data manifest hash changed')
    scenes=json.loads((a.prepared/'scene_ids.json').read_text());samples=json.loads((a.prepared/'sample_ids.json').read_text())['ids']; n=len(scenes)
    rows=list(csv.DictReader(manifest.open())); data={(r['base_scene_id'],r['beta']):r for r in rows}; results={}; details={}
    if len(scenes)!=len(set(scenes)) or len(samples)!=6 or not set(samples).issubset(scenes): raise ValueError('invalid scene/sample set')
    gt_hist=np.zeros(19,dtype=np.int64)
    for scene in scenes:
        target=map_label(np.array(Image.open(data[scene,'0']['gt'])),'labelIds')
        gt_hist+=np.bincount(target[target!=255],minlength=19)[:19]

    for stage in STAGES:
        for beta in BETAS:
            d=a.runs/stage/beta
            if (d/'exit-code.txt').read_text().strip()!='0':raise ValueError('failed cell '+str(d))
            ev=json.loads((d/'evaluation.json').read_text());m=json.loads((d/'independent-metrics.json').read_text());reload=json.loads((d/'reloaded-prediction-metrics.json').read_text())
            if ev['checkpoint_sha256']!=HASHES[stage] or ev['evaluated_images']!=n or not ev['state_unchanged']:raise ValueError('invalid evaluation '+str(d))
            if m['confusion_matrix']!=reload['confusion_matrix']:raise ValueError('reload matrix mismatch '+str(d))
            calls=ev['forward_calls']
            if stage=='gsmf':
                if calls.get('backbone')!=0 or calls.get('decode_head.conv_seg')!=0 or not calls.get('backbone_1') or not calls.get('decode_head_1.conv_seg'):raise ValueError('wrong deployment branch')
            elif not calls.get('backbone') or not calls.get('decode_head.conv_seg'):raise ValueError('missing deployment branch calls')
            if not m.get('actual_logit_shapes') or any(x[0]!=19 for x in m['actual_logit_shapes']):raise ValueError('invalid logit shapes')
            c=np.array(m['confusion_matrix'],dtype=np.int64);gt=c.sum(1);pred=c.sum(0);inter=np.diag(c);union=gt+pred-inter
            vals=np.divide(inter,union,out=np.full(19,np.nan),where=union>0)*100
            mean=float(np.nanmean(vals))
            if c.shape!=(19,19) or not np.array_equal(gt,gt_hist) or int(c.sum())!=m['valid_pixels'] or not np.isclose(mean,m['mIoU'],rtol=0,atol=1e-9):raise ValueError('matrix mismatch '+str(d))
            results[stage,beta]=(c,gt,pred,inter,union,vals,mean);details[stage,beta]=ev
    a.out.mkdir(parents=True,exist_ok=False);(a.out/'matrices').mkdir();(a.out/'samples').mkdir()
    long=[];summary=[];wide=[]
    for stage in STAGES:
        for beta in BETAS:
            c,gt,pred,inter,union,vals,mean=results[stage,beta]
            info=dict(model=stage,beta=beta,n_images=n,mIoU_percent=mean,drop_vs_clear_pp=results[stage,'0'][-1]-mean,checkpoint_sha256=HASHES[stage],data_manifest_sha256=audit['manifest_sha256'],seconds=details[stage,beta]['seconds'],peak_allocated_MiB=details[stage,beta]['peak_allocated_MiB'])
            summary.append(info)
            (a.out/'matrices'/('%s_beta_%s.json'%(stage,beta))).write_text(json.dumps(dict(**info,rows='GT',columns='prediction',classes=list(CLASSES),matrix=c.tolist(),valid_pixels=int(c.sum())),indent=2)+'\n')
            write_csv(a.out/'matrices'/('%s_beta_%s.csv'%(stage,beta)),[dict(gt_class=name,**{str(CLASSES[j]):int(c[i,j]) for j in range(19)}) for i,name in enumerate(CLASSES)],['gt_class']+list(CLASSES))
            for i,name in enumerate(CLASSES):
                long.append(dict(model=stage,beta=beta,trainId=i,classname=name,gt_pixels=int(gt[i]),pred_pixels=int(pred[i]),intersection=int(inter[i]),union=int(union[i]),iou_percent=None if np.isnan(vals[i]) else float(vals[i]),included_in_mean=bool(union[i])))
    for i,name in enumerate(CLASSES):
        row=dict(trainId=i,classname=name)
        for stage in STAGES:
            for beta in BETAS:
                value=results[stage,beta][5][i];row[stage+'_beta_'+beta]=None if np.isnan(value) else float(value)
        wide.append(row)
    write_csv(a.out/'results.csv',summary,list(summary[0]));write_csv(a.out/'class_iou_long.csv',long,list(long[0]));write_csv(a.out/'class_iou_wide.csv',wide,list(wide[0]));(a.out/'results.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    fig,ax=plt.subplots(figsize=(8,5))
    for stage in STAGES:ax.plot([float(b) for b in BETAS],[results[stage,b][-1] for b in BETAS],marker='o',label=stage.upper())
    ax.set_xticks([float(b) for b in BETAS]);ax.set_xlabel(r'Synthetic fog attenuation $\beta$ (m$^{-1}$)');ax.set_ylabel('mIoU (%)');ax.grid(alpha=.3);ax.legend();ax.set_title('Fixed final models, single seed; %d matched validation scenes'%n);fig.tight_layout();fig.savefig(a.out/'miou.png',dpi=180);fig.savefig(a.out/'miou.svg');plt.close(fig)
    palette=np.array(list(PALETTE)+[(0,0,0)]*237,dtype=np.uint8)
    def color(x):return palette[np.asarray(x,dtype=np.uint8)]
    for scene in samples:
        fig,axes=plt.subplots(4,5,figsize=(20,9.5));fig.suptitle(scene+' — synthetic fog; ignore: black')
        for i,beta in enumerate(BETAS):
            r=data[scene,beta]; rgb=Image.open(r['image']).convert('RGB');gt=map_label(np.array(Image.open(r['gt'])),'labelIds')
            axes[i,0].imshow(rgb);axes[i,1].imshow(color(gt));axes[i,0].set_ylabel('β='+beta)
            for j,stage in enumerate(STAGES,2):
                pred_path=a.runs/stage/beta/'predictions'/(Path(r['image']).stem+'.png'); pred=Image.open(pred_path)
                if pred.size!=rgb.size:raise ValueError('prediction size mismatch')
                axes[i,j].imshow(color(pred)); target=a.out/'samples'/scene/stage;target.mkdir(parents=True,exist_ok=True);shutil.copy2(pred_path,target/('beta_'+beta+'.png'))
            for ax in axes[i]:ax.set_xticks([]);ax.set_yticks([])
        for j,title in enumerate(('RGB','GT','Source','FT','GSMF')):axes[0,j].set_title(title)
        fig.legend(handles=[Patch(color=np.array(PALETTE[i])/255,label=CLASSES[i]) for i in range(19)]+[Patch(color='black',label='ignore')],loc='lower center',ncol=10,fontsize=7);fig.tight_layout(rect=(0,.08,1,.96));fig.savefig(a.out/'samples'/(scene+'.png'),dpi=140);plt.close(fig)
if __name__=='__main__':main()
