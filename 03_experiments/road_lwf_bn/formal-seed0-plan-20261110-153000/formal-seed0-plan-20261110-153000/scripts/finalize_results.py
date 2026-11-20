#!/usr/bin/env python
"""Independent saved-prediction verification and five-model/five-condition report.
No training, GPU inference, checkpoint selection, or data modification.
"""
import argparse,csv,hashlib,json,shutil,sys,time
from pathlib import Path
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
ROOT=Path('/home/ysheng4/research/GSMF-RS-DIL');sys.path.insert(0,str(ROOT))
from mmengine.config import Config
from road_dil.protocol import CLASSES,PALETTE,LABEL_IDS,sha256
from road_dil.config import make_config
from road_dil.hooks import tensor_hash
from road_dil.checkpoints import build,assert_state
import torch
PREP=ROOT/'experiments/road_lwf_bn/prepare-seed0-20261110-153000'
OLD=ROOT/'experiments/road_clear_to_fog/formal-seed0-20261108-resume01'
SEV=ROOT/'experiments/road_fog_severity/eval-final-seed0-20261109-182100'
MODELS=('source','ft','gsmf','lwf','gsmf_teacher_bn')
CONDS=('clear','fog005','fog010','fog020','acdc')
BETAS=dict(clear='0',fog005='0.005',fog010='0.01',fog020='0.02')
DISPLAY=dict(source='Source',ft='FT',gsmf='GSMF',lwf='LwF-DIL',gsmf_teacher_bn='GSMF teacher_bn_source_stats')
SAMPLES=('frankfurt_000000_011074','frankfurt_000001_008688','frankfurt_000001_015328','frankfurt_000001_041074','frankfurt_000001_073911','lindau_000049_000019')

def write(path,obj):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('x') as f:json.dump(obj,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def csvwrite(path,rows):
 with path.open('x',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def read(path):return json.loads(Path(path).read_text())
def records(path):return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
def target(path,encoding):
 raw=np.asarray(Image.open(path))
 assert raw.ndim==2
 if encoding=='labelIds':
  lut=np.full(256,255,dtype=np.uint8)
  for i,k in enumerate(LABEL_IDS):lut[k]=i
  assert np.all(((raw>=0)&(raw<=33))|(raw==255)), 'Invalid raw labelIds'
  return lut[raw]
 assert encoding=='trainIds' and np.all((raw<19)|(raw==255))
 return raw.astype(np.uint8)
def pixels(pred,gt):
 assert pred.shape==gt.shape and pred.ndim==2 and np.all((pred>=0)&(pred<19))
 mask=gt!=255
 return np.bincount((gt[mask].astype(np.int64)*19+pred[mask].astype(np.int64)).ravel(),minlength=361).reshape(19,19)
def metrics(c):
 assert c.shape==(19,19) and np.all(c>=0)
 gt=c.sum(1);pr=c.sum(0);inter=np.diag(c);union=gt+pr-inter
 iou=np.divide(inter,union,out=np.full(19,np.nan),where=union>0)*100
 return dict(matrix=c.tolist(),gt_histogram=gt.tolist(),prediction_histogram=pr.tolist(),intersection=inter.tolist(),union=union.tolist(),iou_percent=[None if np.isnan(x) else float(x) for x in iou],mIoU_percent=float(np.nanmean(iou)),valid_pixels=int(c.sum()))
def selfcheck():
 g=np.array([[0,0,1,255],[1,2,2,255]],np.uint8);p=np.array([[0,1,1,18],[2,2,3,0]],np.uint8)
 c=pixels(p,g);manual=np.zeros((19,19),np.int64)
 for a,b in zip(g.ravel(),p.ravel()):
  if a!=255:manual[a,b]+=1
 assert np.array_equal(c,manual)
 r=metrics(c);assert r['valid_pixels']==6 and r['iou_percent'][3]==0 and r['iou_percent'][4] is None
 assert abs(r['mIoU_percent']-100*(.5+1/3+1/3+0)/4)<1e-10
 print('PASS independent fixture: GT rows/pred cols, ignore255, absent and prediction-only classes')

def source_records(cond):
 if cond=='acdc':return records(ROOT/'experiments/road_clear_to_fog/data/B_val.jsonl')
 return records(PREP/'eval-manifests/full'/BETAS[cond]/'A_val.jsonl')
def cell_dir(run,model,cond):
 if model in ('source','ft','gsmf'):
  if cond=='acdc':return OLD/('eval_'+model+'_B')
  return SEV/'evaluation-20261110/full'/model/BETAS[cond]
 return run/('eval-'+model+('-acdc' if cond=='acdc' else '-beta'+BETAS[cond]))
def ckpath(run,model):return (OLD if model in ('source','ft','gsmf') else run)/model/('iter_60000.pth' if model=='source' else 'iter_4000.pth')
def verify_cfg(d,stage,recs):
 files=list(d.glob('*.py'));assert len(files)==1,(d,files)
 cfg=Config.fromfile(str(files[0]));base=make_config(stage)
 assert cfg.model.test_cfg==base['model']['test_cfg']
 assert cfg.model.data_preprocessor==base['model']['data_preprocessor']
 assert cfg.test_dataloader.dataset.pipeline==base['test_dataloader']['dataset']['pipeline']
 loaded=records(cfg.test_dataloader.dataset.ann_file)
 fields=('id','image','label','encoding')
 assert [[r[k] for k in fields] for r in loaded]==[[r[k] for k in fields] for r in recs],str(d)
 head='decode_head_1' if stage in ('gsmf','lwf','gsmf_teacher_bn') else 'decode_head'
 assert cfg.model[head].num_classes==19
 if stage in ('lwf','gsmf_teacher_bn'):assert cfg.model.teacher_policy==base['model']['teacher_policy']
 return dict(resolved_config=str(files[0]),config_sha256=sha256(files[0]),manifest=str(cfg.test_dataloader.dataset.ann_file),manifest_sha256=sha256(cfg.test_dataloader.dataset.ann_file),slide=[512,512],stride=[341,341],TTA=False)

def training_audit(run,out):
 rows={}
 for stage in ('lwf','gsmf_teacher_bn'):
  p=ckpath(run,stage);ck=torch.load(str(p),map_location='cpu');init=torch.load(str(PREP/'conversion'/(stage+'_init.pth')),map_location='cpu')
  assert ck['meta']['iter']==4000 and all(k in ck for k in ('optimizer','param_schedulers'))
  initial=init['state_dict'];state=ck['state_dict'];model=build(stage);assert_state(state,model)
  teacher=[k for k in state if k.startswith(('backbone.','decode_head.'))]
  assert all(torch.equal(state[k],initial[k]) for k in teacher)
  audit=read(run/stage/'audit-end-4000.json');assert audit['finite_all_checked_gradients']
  for k in ('backbone','decode_head'):
   assert audit['groups'][k]['changed_parameters']==audit['groups'][k]['changed_bn_buffers']==0
  for k in ('backbone_1.stem','backbone_1.layer1'):
   g=audit['groups'][k]
   assert (g['changed_parameters']>0 and g['gradient_tensors_first_step']>0) if stage=='lwf' else (g['changed_parameters']==g['gradient_tensors_first_step']==0)
  assert all(v.get('step',0)==4000 for v in ck['optimizer']['state'].values())
  rows[stage]=dict(checkpoint=str(p),checkpoint_sha256=sha256(p),iterations=4000,optimizer_saved=True,scheduler_saved=True,optimizer_active_parameter_steps_all_4000=True,teacher_state_tensors_exact_source=len(teacher),audit=str(run/stage/'audit-end-4000.json'),initialization_sha256=sha256(PREP/'conversion'/(stage+'_init.pth')),teacher_policy=make_config(stage)['model']['teacher_policy'],groups=audit['groups'],trainable_parameters=audit['trainable_parameters'],total_parameters=audit['total_parameters'],peak_allocated_MiB=audit['peak_allocated_MiB'],seconds_per_step=audit['seconds_per_step_after_warmup'])
  del ck,init,model
 write(out/'training-check.json',dict(status='PASS',models=rows))
 return rows

def main(run):
 run=Path(run).resolve();assert (run/'exit-code.txt').read_text().strip()=='0'
 assert read(run/'status.json')['state']=='train_eval_complete_pending_summary'
 out=run/'results';out.mkdir(exist_ok=False)
 observations=read(run/'timing-observations.json')
 observations['negative_logger_entries']={p.name:[line for line in p.read_text().splitlines() if 'time: -' in line] for p in run.glob('*.log') if p.name.startswith(('train-','eval-'))}
 observations['resource_step_statistic']='RoadAudit seconds_per_step_after_warmup: synchronized perf_counter compute step, excluding data wait. Stage wall duration uses monotonic; raw wall-based data waits retained with possible negative clock observations.'
 (run/'timing-observations.json').write_text(json.dumps(observations,indent=2)+'\n')
 selfcheck();train=training_audit(run,out)
 hashes={m:sha256(ckpath(run,m)) for m in MODELS}
 fixed=read(PREP/'fixed-checkpoints.json')
 for m in ('source','ft','gsmf'):assert hashes[m]==fixed[str(ckpath(run,m).relative_to(ROOT))]
 manifests={c:source_records(c) for c in CONDS}
 expected_ids=read(SEV/'prepared-20261110/scene_ids.json')
 assert all([r['id'] for r in manifests[c]]==expected_ids for c in BETAS)
 assert tuple(read(SEV/'prepared-20261110/sample_ids.json')['ids'])==SAMPLES
 hist={};gtinfo={}
 for cond,recs in manifests.items():
  assert len(recs)==(100 if cond=='acdc' else 500)
  h=np.zeros(19,np.int64);ignored=0
  for r in recs:
   y=target(r['label'],r['encoding']);h+=np.bincount(y[y!=255],minlength=19)[:19];ignored+=int((y==255).sum())
  hist[cond]=h;gtinfo[cond]=dict(images=len(recs),gt_histogram=h.tolist(),valid_pixels=int(h.sum()),ignored_pixels=ignored)
 assert all(np.array_equal(hist[c],hist['clear']) for c in BETAS)
 write(out/'gt-histograms.json',gtinfo)
 data={};summary=[];long=[];proof=[]
 for m in MODELS:
  for c in CONDS:
   d=cell_dir(run,m,c);ev=read(d/'evaluation.json');recs=manifests[c]
   assert ev['stage']==m and ev['checkpoint_sha256']==hashes[m] and ev['evaluated_images']==len(recs) and ev['state_unchanged']
   cfgproof=verify_cfg(d,m,recs)
   if m in ('gsmf','lwf','gsmf_teacher_bn'):
    assert ev['forward_calls']['backbone']==ev['forward_calls']['decode_head.conv_seg']==0
    assert ev['forward_calls']['backbone_1']>0 and ev['forward_calls']['decode_head_1.conv_seg']>0
   else:assert ev['forward_calls']['backbone']>0 and ev['forward_calls']['decode_head.conv_seg']>0
   if (d/'cell-proof.json').exists():
    provenance=read(d/'cell-proof.json')
    for name in ('evaluation.json','independent-metrics.json','reloaded-prediction-metrics.json','exit-code.txt'):
     assert sha256(d/name)==provenance['files'][name], str(d/name)
   saved=read(d/'independent-metrics.json');reload=read(d/'reloaded-prediction-metrics.json')
   assert saved['confusion_matrix']==reload['confusion_matrix']
   assert saved.get('actual_logit_shapes') and all(x[0]==19 for x in saved['actual_logit_shapes'])
   if m in ('lwf','gsmf_teacher_bn'):
    assert (run/('eval-'+m+('-acdc' if c=='acdc' else '-beta'+BETAS[c])+'.exit')).read_text().strip()=='0'
    # A third independent implementation rereads every saved prediction and original GT.
    matrix=np.zeros((19,19),np.int64);prediction_files=[]
    for r in recs:
     p=d/'predictions'/(Path(r['image']).stem+'.png');pred=np.asarray(Image.open(p));y=target(r['label'],r['encoding'])
     matrix+=pixels(pred,y);prediction_files.append(dict(id=r['id'],path=str(p),sha256=sha256(p),label=r['label']))
    assert len(list((d/'predictions').glob('*.png')))==len(recs)
    assert np.array_equal(matrix,np.array(saved['confusion_matrix'],np.int64))
    write(out/'verification'/('%s_%s_predictions.json'%(m,c)),prediction_files)
    origin='new_inference_this_run'
   else:
    # Reuse previous complete independent reread. Never mark as newly inferred.
    matrix=np.array(saved['confusion_matrix'],np.int64);origin='reused_verified_previous_run'
   r=metrics(matrix);assert np.array_equal(matrix.sum(1),hist[c])
   assert abs(r['mIoU_percent']-saved['mIoU'])<1e-9
   assert abs(r['mIoU_percent']-ev['metrics']['mIoU'])<.011
   r.update(model=m,condition=c,images=len(recs),checkpoint_sha256=hashes[m],origin=origin,source_directory=str(d),matrix_direction='GT rows, prediction columns')
   data[m,c]=r
   write(out/'matrices'/('%s_%s.json'%(m,c)),r)
   with (out/'matrices'/('%s_%s.csv'%(m,c))).open('x',newline='') as f:
    w=csv.writer(f);w.writerow(['GT/prediction']+list(CLASSES));w.writerows([[CLASSES[i]]+row for i,row in enumerate(matrix.tolist())])
   summary.append(dict(model=m,condition=c,images=len(recs),mIoU_percent=r['mIoU_percent'],drop_vs_own_clear_pp=None,delta_vs_source_same_condition_pp=None,checkpoint_sha256=hashes[m],origin=origin,source_directory=str(d),seconds=ev['seconds'],peak_allocated_MiB=ev['peak_allocated_MiB']))
   for i,name in enumerate(CLASSES):long.append(dict(model=m,condition=c,trainId=i,classname=name,IoU_percent=r['iou_percent'][i],GT_pixels=r['gt_histogram'][i],predicted_pixels=r['prediction_histogram'][i],intersection=r['intersection'][i],union=r['union'][i]))
   proof.append(dict(model=m,condition=c,origin=origin,matrix_equals_saved_and_reloaded=True,GT_histogram_matches_original_labels=True,independent_third_prediction_reread=m in ('lwf','gsmf_teacher_bn'),state_unchanged=ev['state_unchanged'],forward_calls=ev['forward_calls'],actual_logit_shapes=saved['actual_logit_shapes'],protocol=cfgproof,checkpoint_sha256=hashes[m]))
   print('Verified',m,c,len(recs),r['mIoU_percent'],flush=True)
 for row in summary:
  m,c=row['model'],row['condition'];row['drop_vs_own_clear_pp']=None if c=='acdc' else data[m,'clear']['mIoU_percent']-row['mIoU_percent'];row['delta_vs_source_same_condition_pp']=row['mIoU_percent']-data['source',c]['mIoU_percent']
 csvwrite(out/'five-model-summary.csv',summary);write(out/'five-model-summary.json',summary);csvwrite(out/'class-iou-long.csv',long);write(out/'class-iou-long.json',long)
 wide=[]
 for i,name in enumerate(CLASSES):
  row=dict(trainId=i,classname=name)
  for m in MODELS:
   for c in CONDS:row[m+'_'+c]=data[m,c]['iou_percent'][i]
  wide.append(row)
 csvwrite(out/'class-iou-wide.csv',wide);write(out/'class-iou-wide.json',wide)
 write(out/'independent-final-check.json',dict(status='PASS',new_cells=10,reused_cells=15,new_images=4200,classes=list(CLASSES),matrix_direction='GT rows / predicted columns',classes_union_zero_excluded=True,GT_absent_prediction_present_IoU_zero=True,not_per_image_average=True,checks=proof,old_severity_verification=str(SEV/'evaluation-20261110/independent-final-check.json'),old_two_domain_verification=str(OLD/'final-independent-verification.json')))
 plots(out,data);samples(out,run,manifests);report(out,run,data,train,summary)
 write(run/'RESULTS_READY.json',dict(status='verified_results_complete',results_directory=str(out),cells=25,new_cells=10,reused_cells=15,new_images=4200))

def plots(out,data):
 xs=[0,.005,.01,.02];cs=list(BETAS)
 for drop in (False,True):
  fig,ax=plt.subplots(figsize=(9,5))
  for m in MODELS:
   ys=[data[m,c]['mIoU_percent'] for c in cs]
   if drop:ys=[ys[0]-y for y in ys]
   ax.plot(xs,ys,marker='o',label=DISPLAY[m])
  ax.set_xticks(xs);ax.set_xlabel('Synthetic fog attenuation beta (1/m)');ax.set_ylabel('Drop from own clear mIoU (pp)' if drop else 'mIoU (%)');ax.grid(alpha=.3);ax.legend(fontsize=8);ax.set_title('500 matched scenes; fixed final checkpoints; seed 0');fig.tight_layout()
  for ext in ('png','svg','pdf'):fig.savefig(out/(('fog-drop' if drop else 'fog-miou')+'.'+ext),dpi=180)
  plt.close(fig)
 # Full per-class table remains in CSV/JSON; heatmap shows concrete trade-offs.
 fig,axes=plt.subplots(1,5,figsize=(17,10),sharey=True)
 for ax,c in zip(axes,CONDS):
  vals=np.array([[np.nan if x is None else x for x in data[m,c]['iou_percent']] for m in MODELS]).T
  image=ax.imshow(vals,aspect='auto',vmin=0,vmax=100,cmap='viridis');ax.set_xticks(range(5));ax.set_xticklabels(['Src','FT','GSMF','LwF','BN'],rotation=45);ax.set_title(c);ax.set_yticks(range(19));ax.set_yticklabels(CLASSES)
 fig.colorbar(image,ax=list(axes),shrink=.7,label='IoU (%)');fig.savefig(out/'class-iou-heatmap.png',dpi=170,bbox_inches='tight');plt.close(fig)

def samples(out,run,manifests):
 palette=np.zeros((256,3),np.uint8);palette[:19]=np.array(PALETTE)
 sampleindex=[];lookup={c:{r['id']:r for r in recs} for c,recs in manifests.items() if c!='acdc'}
 for scene in SAMPLES:
  fig,axes=plt.subplots(4,7,figsize=(25,10.5))
  fig.suptitle(scene+' — fixed before current training; ignore=black')
  for i,c in enumerate(BETAS):
   r=lookup[c][scene];rgb=Image.open(r['image']).convert('RGB');y=target(r['label'],r['encoding'])
   axes[i,0].imshow(rgb);axes[i,1].imshow(palette[y]);axes[i,0].set_ylabel(c)
   for j,m in enumerate(MODELS,2):
    src=cell_dir(run,m,c)/'predictions'/(Path(r['image']).stem+'.png');p=np.asarray(Image.open(src));assert p.shape==y.shape
    if m in ('source','ft','gsmf'):
     cellproof=read(src.parents[1]/'cell-proof.json')
     assert sha256(src)==cellproof['files']['predictions/'+src.name]
    axes[i,j].imshow(palette[p])
    if m in ('lwf','gsmf_teacher_bn'):
     dst=out/'fixed-samples/raw-predictions'/scene/m/(c+'.png');dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
     sampleindex.append(dict(scene=scene,model=m,condition=c,source_prediction=str(src),saved_prediction=str(dst),sha256=sha256(dst)))
   for ax in axes[i]:ax.set_xticks([]);ax.set_yticks([])
  for j,t in enumerate(('RGB','GT','Source','FT','GSMF','LwF-DIL','Teacher BN')):axes[0,j].set_title(t)
  fig.legend(handles=[Patch(color=np.array(PALETTE[i])/255,label=CLASSES[i]) for i in range(19)]+[Patch(color='black',label='ignore')],loc='lower center',ncol=10,fontsize=8)
  fig.tight_layout(rect=(0,.09,1,.96));dest=out/'fixed-samples';dest.mkdir(exist_ok=True);fig.savefig(dest/(scene+'.png'),dpi=160);plt.close(fig)
 assert len(sampleindex)==48
 write(out/'fixed-samples/prediction-index.json',sampleindex)
 write(out/'fixed-samples/selection.json',dict(ids=list(SAMPLES),source=str(SEV/'prepared-20261110/sample_ids.json'),selection='Fixed six previous-run scenes, unchanged; no outcome-based selection',new_original_predictions=48))

def report(out,run,data,train,summary):
 events=[json.loads(x) for x in (run/'events.jsonl').read_text().splitlines()]
 costs={m:dict(**train[m],training_wall_seconds=next(r['seconds'] for r in events if r['stage']=='train-'+m and r['state']=='complete'),evaluation_seconds=sum(r['seconds'] for r in summary if r['model']==m),evaluation_stage_wall_seconds=sum(r['seconds'] for r in events if r['stage'].startswith('eval-'+m+'-') and r['state']=='complete')) for m in ('lwf','gsmf_teacher_bn')}
 write(out/'resource-costs.json',costs)
 oldsummary=read(sorted(OLD.glob('summary-*.json'))[-1]);accounting=read(OLD/'resource-accounting.json')
 oldcosts=oldsummary['costs']
 oldcosts['source']['training_wall_seconds']=accounting['source_useful_segments_wall_seconds']
 resource_rows=[]
 for m in MODELS:
  if m in oldcosts:
   r=oldcosts[m];resource_rows.append(dict(model=m,origin='reused_previous_run',training_wall_seconds=r['training_wall_seconds'],peak_allocated_MiB=r['train_peak_allocated_MiB'],total_parameters=r['total_parameters'],trainable_parameters=r['trainable_parameters'],deploy_parameters=47832297,evaluation_five_conditions_test_loop_seconds=sum(x['seconds'] for x in summary if x['model']==m),evaluation_five_conditions_stage_wall_seconds=None))
  else:
   r=costs[m];resource_rows.append(dict(model=m,origin='new_this_run',training_wall_seconds=r['training_wall_seconds'],peak_allocated_MiB=r['peak_allocated_MiB'],total_parameters=r['total_parameters'],trainable_parameters=r['trainable_parameters'],deploy_parameters=47832297,evaluation_five_conditions_test_loop_seconds=r['evaluation_seconds'],evaluation_five_conditions_stage_wall_seconds=r['evaluation_stage_wall_seconds']))
 write(out/'five-model-resource-costs.json',dict(rows=resource_rows,old_summary_source=str(sorted(OLD.glob('summary-*.json'))[-1]),old_source_segment_accounting=accounting,source_note='Source wall time is useful pre-resume and resumed segments; original discarded10000 updates not included. Observed all-attempt lower bound retained in accounting.'))
 csvwrite(out/'five-model-resource-costs.csv',resource_rows)
 lines=['# 第2项seed0正式结果','','两组各4000步训练、10个完整评价单元4200次逐图、第三路径预测重读与GT直方图核验完成；表中旧15单元来自已验证旧结果，本轮未重新推理。固定iter_4000，不按val择优。','','| 模型 | 晴天500 | Foggy .005 /500 | Foggy .01 /500 | Foggy .02 /500 | ACDC-fog100 |','|---|---:|---:|---:|---:|---:|']
 for m in MODELS:lines.append('| '+DISPLAY[m]+' | '+' | '.join('%.4f'%data[m,c]['mIoU_percent'] for c in CONDS)+' |')
 lines+=['','| 模型 | 晴天保持相对Source pp | .005相对自身晴天下降pp | .01下降pp | .02下降pp | ACDC相对Source增量pp |','|---|---:|---:|---:|---:|---:|']
 for m in MODELS:
  vals=[data[m,'clear']['mIoU_percent']-data['source','clear']['mIoU_percent']]+[data[m,'clear']['mIoU_percent']-data[m,c]['mIoU_percent'] for c in ('fog005','fog010','fog020')]+[data[m,'acdc']['mIoU_percent']-data['source','acdc']['mIoU_percent']]
  lines.append('| '+DISPLAY[m]+' | '+' | '.join('%.4f'%x for x in vals)+' |')
 lines+=['','不计算五条件简单平均：四组Cityscapes条件重复同500场景，不能把重复场景赋予四倍独立权重。旧域保持、合成强度下降与真实ACDC适应分别解释。','', '## 相对原GSMF的实测差异','']
 for m in ('lwf','gsmf_teacher_bn'):
  vals=[data[m,c]['mIoU_percent']-data['gsmf',c]['mIoU_percent'] for c in CONDS]
  lines.append(DISPLAY[m]+'相对原GSMF按晴天/.005/.01/.02/ACDC依次为 '+', '.join('%+.4f pp'%x for x in vals)+'。')
 lines+=['','## 保持、强度变化与真实雾适应','']
 for m in ('lwf','gsmf_teacher_bn'):
  clear=data[m,'clear']['mIoU_percent'];src=data['source','clear']['mIoU_percent'];acdc=data[m,'acdc']['mIoU_percent']
  lines.append('%s：晴天相对Source为%+.4fpp，相对FT为%+.4fpp；真实ACDC相对Source为%+.4fpp，相对FT为%+.4fpp。晴天保持与真实雾适应分开评价，不把两者差异全部归因于天气。'%(DISPLAY[m],clear-src,clear-data['ft','clear']['mIoU_percent'],acdc-data['source','acdc']['mIoU_percent'],acdc-data['ft','acdc']['mIoU_percent']))
  for c in ('fog005','fog010','fog020'):
   v=data[m,c]['mIoU_percent'];lines.append('%s / %s：绝对mIoU %.4f%%，相对自身晴天下降%+.4fpp，相对Source同强度%+.4fpp。'%(DISPLAY[m],c,v,clear-v,v-data['source',c]['mIoU_percent']))
  seq=[data[m,c]['mIoU_percent'] for c in BETAS]
  lines.append('该模型四个配对采样强度点'+('随雾强不增。' if all(a>=b for a,b in zip(seq,seq[1:])) else '存在非单调变化；不把有限采样点解释为连续强度函数。'))
 lines+=['','## 逐类取舍','']
 for m in ('lwf','gsmf_teacher_bn'):
  for c in ('clear','acdc'):
   dif=np.array(data[m,c]['iou_percent'])-np.array(data['gsmf',c]['iou_percent']);order=np.argsort(dif)
   lines.append('%s / %s 相对原GSMF，最高三项差值：%s；最大下降：%s。完整19类×25单元见class-iou-wide.csv/JSON。'%(DISPLAY[m],c,', '.join('%s %+.2fpp'%(CLASSES[i],dif[i]) for i in order[-3:][::-1]),', '.join('%s %+.2fpp'%(CLASSES[i],dif[i]) for i in order[:3])))
 lines+=['','## 成本与审计','','| 模型 | 训练墙钟秒（含周期验证/保存） | 同步步骤秒/步（不含数据等待） | 峰值allocated MiB | 可训练参数 | 五条件测试循环秒 |','|---|---:|---:|---:|---:|---:|']
 for m,c in costs.items():lines.append('| %s | %.2f | %.5f | %.1f | %d | %.2f |'%(DISPLAY[m],c['training_wall_seconds'],c['seconds_per_step'],c['peak_allocated_MiB'],c['trainable_parameters'],c['evaluation_seconds']))
 lines+=['','五模型历史/本轮资源并列见five-model-resource-costs.csv/JSON，来源明确区分；Source使用有效前段+resume合计墙钟，失败尝试下界另保留；共同部署参数47,832,297。','新两组教师全部参数/缓冲与Source逐键一致；LwF浅层实际更新，BN组浅层参数保持原版冻结、学生BN继续更新。推理两域均仅学生分支；所有参数/缓冲评价前后不变。optimizer/scheduler与iter4000完整保留。所有活动AdamW参数状态step=4000。测试循环秒包含Runner.test中的读图、指标与预测保存，排除其后预测重读和最终复核/打包；新两组另记录包括加载/入口内重读的evaluation_stage_wall_seconds。时间非纯推理延迟，不据共享系统负载断言速度优劣。日志曾出现负的MMEngine time/data_time值（time.time差值，可能受墙钟调整影响，未独立证明原因）；阶段耗时采用monotonic，表中步骤均值采用RoadAudit同步后的perf_counter（排除前2步，不含墙钟数据等待）；原始等待记录保留但可能受墙钟调整影响。原始记录见timing-observations.json。','', '## 解释边界','','仅seed0，不能声称统计显著；真实ACDC与合成Cityscapes存在跨库差异，天气不是唯一变化。ACDC训练强度支持未知，不能称严格未见强度泛化。LwF为固定19类单头分割适配，T2/0.5首轮默认、KD全像素无T²、不搜索超参；单次表现不能否定机制。teacher_bn_source_stats同时改变教师BN前向统计和统计更新、保留教师Dropout；本单变量诊断只说明该设置在本次运行的影响，不能证明BN是主要遗忘原因。','', '## 完整19类表','']
 for c in CONDS:
  lines+=['### '+c,'','| 类别 | Source | FT | GSMF | LwF-DIL | Teacher BN |','|---|---:|---:|---:|---:|---:|']
  for i,name in enumerate(CLASSES):lines.append('| '+name+' | '+' | '.join('null' if data[m,c]['iou_percent'][i] is None else '%.4f'%data[m,c]['iou_percent'][i] for m in MODELS)+' |')
 (run/'RESULTS.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path);p.add_argument('--self-check',action='store_true');a=p.parse_args()
 if a.self_check:selfcheck()
 else:main(a.run)
