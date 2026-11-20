#!/usr/bin/env python
"""Additional independent formal training/protocol verification and result artifacts."""
import argparse,csv,gc,json,sys,subprocess
from pathlib import Path
from datetime import datetime,timezone,timedelta
import numpy as np
import torch
ROOT=Path('/home/ysheng4/research/GSMF-RS-DIL');sys.path.insert(0,str(ROOT))
from mmengine.config import Config
from road_dil.protocol import CLASSES,sha256,write_json
from road_dil.checkpoints import assert_state,build,validate_rain_input
from tools.road.rain_common import METHODS,CONDITIONS,PARENTS,OLD,LWF,SEVERITY
from tools.road.rain_formal import fingerprint

def read(p):return json.loads(Path(p).read_text())
def records(p):return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
def csvsave(p,rows):
 with Path(p).open('x',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main(prep,run):
 prep=Path(prep).resolve();run=Path(run).resolve();ready=read(prep/'READY.json')
 assert ready['code']==fingerprint()
 assert read(run/'provenance.json')['ready_sha256']==sha256(prep/'READY.json')
 assert (run/'exit-code.txt').read_text().strip()=='0'
 assert read(run/'status.json')['state']=='train_eval_complete_pending_summary'
 if not (run/'results').exists():
  subprocess.run([sys.executable,str(ROOT/'tools/road/rain_results.py'),'--prepare',str(prep),'--run',str(run)],check=True)
 out=run/'results';training={};periodic=[]
 events=[json.loads(x) for x in (run/'events.jsonl').read_text().splitlines()]
 for m in METHODS:
  work=run/m;initial=torch.load(str(prep/'conversion'/m/(m+'_init.pth')),map_location='cpu');inv=read(work/'invocation.json')
  assert inv['initialization_sha256']==ready['initializations'][m]['sha256'] and inv['optimizer']=='fresh' and inv['train_domain']=='C' and not inv['debug']
  assert sha256(prep/'conversion'/m/(m+'_init.pth'))==inv['initialization_sha256']
  fresh=read(work/'fresh-optimizer.json');assert fresh==dict(iteration=0,optimizer_state_empty=True,domain='C',scheduler_end=4000,seed=0)
  cfg=Config.fromfile(str(work/'resolved.py'))
  assert cfg.randomness.seed==0 and cfg.train_cfg.max_iters==4000 and cfg.param_scheduler[0].end==4000
  assert cfg.train_cfg.val_interval==cfg.default_hooks.checkpoint.interval==1000
  assert Path(cfg.train_dataloader.dataset.ann_file).resolve()==prep/'data/C_train.jsonl'
  assert Path(cfg.val_dataloader.dataset.ann_file).resolve()==prep/'data/C_val.jsonl'
  assert cfg.train_dataloader.batch_size==2 and cfg.model.data_preprocessor.size==(512,512)
  model=build(m);parameters=set(dict(model.named_parameters()))
  for i in (1000,2000,3000,4000):
   p=work/('iter_'+str(i)+'.pth');ck=torch.load(str(p),map_location='cpu')
   validate_rain_input(ck,m,work,True);assert ck['meta']['iter']==i and ck['meta']['seed']==0
   assert ck['meta']['parent_sha256']==PARENTS[m][1]
   assert ck['param_schedulers'][0]['end']==4000
   assert all(v['step']==i for v in ck['optimizer']['state'].values())
   assert_state(ck['state_dict'],model)
   periodic.append(dict(method=m,iteration=i,path=str(p),sha256=sha256(p),bytes=p.stat().st_size,optimizer_active_steps_all_equal_iteration=True))
   if i!=4000:del ck;gc.collect()
  state=ck['state_dict'];init=initial['state_dict'];audit=read(work/'audit-end-4000.json')
  assert len(audit['losses'])==4000 and np.all(np.isfinite(audit['losses'])) and audit['finite_all_checked_gradients']
  assert len(audit['validation_seconds'])==4
  changed={k for k,v in state.items() if not torch.equal(v,init[k])};teacher_changed_buffers=[]
  if m!='ft':
   teacher=[k for k in state if k.startswith(('backbone.','decode_head.'))]
   assert all(torch.equal(state[k],init[k]) for k in teacher if k in parameters)
   teacher_changed_buffers=[k for k in teacher if k not in parameters and k in changed]
   assert len(teacher_changed_buffers)==(342 if m=='gsmf' else 0)
   if m=='gsmf':
    assert not any(k in changed for k in parameters if k.startswith(('backbone_1.stem.','backbone_1.layer1.')))
   else:
    assert all(audit['groups'][g]['changed_parameters']>0 for g in ('backbone_1.stem','backbone_1.layer1'))
  train_event=next(e for e in events if e['stage']=='train-'+m and e['state']=='complete')
  training[m]=dict(initialization_sha256=inv['initialization_sha256'],parent_sha256=PARENTS[m][1],checkpoint_sha256=periodic[-1]['sha256'],iterations=4000,
   initialization_optimizer_fresh=True,all_periodic_checkpoints_complete=True,teacher_changed_buffers=teacher_changed_buffers,
   parameter_policy_verified=True,groups=audit['groups'],losses_all_4000_finite=True,
   gradient_check_scope=audit['gradient_check_scope'],finite_checked_gradients=True,total_parameters=audit['total_parameters'],trainable_parameters=audit['trainable_parameters'],
   train_wall_seconds=train_event['seconds'],train_step_seconds=audit['seconds_per_step_after_warmup'],
   val_seconds=audit['validation_seconds'],peak_allocated_MiB=audit['peak_allocated_MiB'],peak_reserved_MiB=audit['peak_reserved_MiB'],
   formal_resume_used=bool(list(work.glob('resume-verified-*.json'))))
  del state,init,initial,model,ck;gc.collect()
 write_json(out/'training-independent-check.json',dict(status='PASS',methods=training,periodic_checkpoints=periodic))
 cells=read(out/'42-cells.json');plan=read(prep/'evaluation-plan.json')['cells'];checks=[];hist={};resource=[]
 for cell in cells:
  name=cell['model'];cond=cell['condition'];expected=next(x for x in plan if x['model']==name and x['condition']==cond)
  directory=Path(cell['evidence']);ev=read(directory/'evaluation.json')
  ckpath=run/cell['method']/'iter_4000.pth' if name.endswith('_rain') else PARENTS[cell['method']][0]
  assert ev['checkpoint_sha256']==cell['checkpoint_sha256']==sha256(ckpath)
  assert ev['stage']==cell['method'] and ev['domain']==('A' if cond in CONDITIONS[:4] else ('B' if cond=='fog' else 'C'))
  assert ev['evaluated_images']==cell['images']==expected['images'] and ev['state_unchanged']
  files=list(directory.glob('*.py'));assert len(files)==1
  cfg=Config.fromfile(str(files[0]));manifest=Path(cfg.test_dataloader.dataset.ann_file)
  reference=(prep/'data'/('B_val.jsonl' if cond=='fog' else 'C_val.jsonl')) if cond in ('fog','rain') else prep/'eval-manifests'/cond/'A_val.jsonl'
  rs=records(manifest);ref=records(reference);fields=('id','image','label','encoding','domain','split')
  assert [{k:r[k] for k in fields} for r in rs]==[{k:r[k] for k in fields} for r in ref]
  assert len({r['id'] for r in rs})==len(rs)
  matrix=np.array(cell['confusion_matrix'],np.int64);truth=np.array([sum(r['label_histogram'].get(str(i),0) for r in ref) for i in range(19)],np.int64)
  assert np.array_equal(matrix.sum(1),truth)
  if cond in hist:assert hist[cond]==truth.tolist()
  else:hist[cond]=truth.tolist()
  if cell['method'] in ('gsmf','lwf'):
   assert ev['forward_calls']['backbone']==ev['forward_calls']['decode_head.conv_seg']==0
   assert ev['forward_calls']['backbone_1']>0 and ev['forward_calls']['decode_head_1.conv_seg']>0
  assert cfg.model.test_cfg.mode=='slide' and cfg.model.test_cfg.crop_size==(512,512) and cfg.model.test_cfg.stride==(341,341)
  checks.append(dict(model=name,condition=cond,provenance=cell['provenance'],images=len(rs),manifest=str(manifest),manifest_sha256=sha256(manifest),evaluation_sha256=sha256(directory/'evaluation.json'),checkpoint_sha256=cell['checkpoint_sha256'],exact_expected_ID_paths_encoding=True,GT_histogram_exact=True,student_only=True,state_unchanged=True))
  stage_event=next((e for e in events if e['stage']=='eval-'+name+'-'+cond and e['state']=='complete'),{})
  resource.append(dict(model=name,condition=cond,provenance=cell['provenance'],images=len(rs),test_loop_seconds=ev['seconds'],stage_wall_seconds=stage_event.get('seconds'),peak_allocated_MiB=ev.get('peak_allocated_MiB'),peak_reserved_MiB=ev.get('peak_reserved_MiB'),checkpoint_bytes=ev['checkpoint_bytes']))
 assert len(checks)==42 and sum(c['provenance']=='new' for c in checks)==22
 assert sum(c['images'] for c in checks if c['provenance']=='new')==7000
 assert all(hist[c]==hist['clear'] for c in CONDITIONS[:4])
 write_json(out/'protocol-independent-check.json',dict(status='PASS',cells=checks,gt_histograms=hist))
 csvsave(out/'evaluation-resource-costs.csv',resource);write_json(out/'resource-costs.json',dict(training=training,evaluation=resource,
  timing_scope='perf_counter/monotonic timings; raw MMEngine time/data_time retained separately; evaluation loop includes read/metrics/prediction PNG save, stage wall also includes model loading and entry reread',
  no_formal_speed_quality_ranking=True))
 long=[dict(model=c['model'],condition=c['condition'],class_name=k,IoU=c['IoU'][k],mIoU=c['mIoU'],provenance=c['provenance']) for c in cells for k in CLASSES]
 csvsave(out/'class-iou-long.csv',long);write_json(out/'class-iou-long.json',long)
 wide=[dict(class_name=k,**{c['model']+'/'+c['condition']:c['IoU'][k] for c in cells}) for k in CLASSES];csvsave(out/'class-iou-wide.csv',wide)
 summary=read(out/'real-domain-stages.json');delta=read(out/'stage-deltas.json');score={(c['model'],c['condition']):c['mIoU'] for c in cells}
 synthetic=[dict(model=m,**{c:score[m,c] for c in CONDITIONS[:4]}) for m in ['source']+[m+'_fog' for m in METHODS]+[m+'_rain' for m in METHODS]]
 csvsave(out/'synthetic-conditions.csv',synthetic)
 details=['# Cityscapes→ACDC-fog→ACDC-rain：正式 seed0 结果','', '三组各4000步、22个新增完整单元7000次逐图评价及独立预测重读完成；旧20格核对后复用，七个唯一checkpoint共42格。固定iter4000，无val择优。','', '| 方法/阶段 | CS晴天 | ACDC-fog | ACDC-rain | 已见域等权均值 |','|---|---:|---:|---:|---:|']
 for m,rows in summary.items():
  for r in rows:details.append('| %s/%s | %.4f | %.4f | %.4f | %.4f |'%(m,r['stage'],r['CS'],r['Fog'],r['Rain'],r['seen_domain_equal_mean']))
 details+=['','Source行共享展示；已见域均值依阶段只含CS、CS/Fog、CS/Fog/Rain。Source/Fog后Rain分数为未来域提前评价，未计入当时已见域均值。','', '| 方法 | Rain后CS−Fog后CS | Rain后Fog−Fog后Fog | CS相对Source累积差 | Rain适应增益 |','|---|---:|---:|---:|---:|']
 for m,d in delta.items():details.append('| %s | %+.4f | %+.4f | %+.4f | %+.4f |'%(m,d['CS_after_minus_Fog_stage'],d['Fog_after_minus_Fog_stage'],d['CS_cumulative_after_minus_Source'],d['Rain_adaptation_after_minus_own_Fog']))
 details+=['','差值统一after-before，可为负。旧域遗忘以已学且早于最终阶段的历史峰值为参照：CS=max(Source,Fog后)−Rain后；Fog=Fog后−Rain后。逐项见stage-deltas.json；不加入Rain零项，不报告FWT。','', '| 模型 | CS | Foggy .005 | Foggy .01 | Foggy .02 |','|---|---:|---:|---:|---:|']
 for row in synthetic:details.append('| %s | %.4f | %.4f | %.4f | %.4f |'%(row['model'],row['clear'],row['fog005'],row['fog010'],row['fog020']))
 details+=['','四个CS条件共享500场景和GT，属于固定合成评价条件；不视为四个训练域，不与真实域计算六条件混合均值。','', 'Rain后原版GSMF相对FT的CS/Fog/Rain差为 '+', '.join('%+.4fpp'%(score['gsmf_rain',c]-score['ft_rain',c]) for c in ('clear','fog','rain'))+'；相对LwF为 '+', '.join('%+.4fpp'%(score['gsmf_rain',c]-score['lwf_rain',c]) for c in ('clear','fog','rain'))+'。差异仅描述本次seed0结果。',
 '', '训练沿用CE及既定蒸馏/冻结策略：FT全量CE；GSMF教师参数固定、BN训练态更新，学生stem/layer1参数冻结但BN更新；LwF教师eval/no_grad全部状态固定于自己的Fog学生快照、学生全量更新。输出Hin T2/0.5为全原生logit像素（含ignore/padding）、无T²；GSMF另有特征KL(T1/1,idx1/2/3)，LwF无该项。CE保持原配置。未重训Source/Fog、未追加seed/搜索/天气/模块。',
 '', '全部预测按GT行/预测列累计矩阵，ignore255，union0写null并排除均值，GT缺失但预测出现为0。没有平均逐图mIoU。所有条件仅学生推理，参数/缓冲不变，无天气oracle/TTA/测试时更新。新增22格由另一实现重读全部保存PNG与原标签，核对尺寸/ID/GT直方图/累计矩阵。',
 '', '局限：仅seed0，不能声称稳定显著；跨库地点/设备/场景与天气同时变化，不能全部归因于天气。共享官方视频目录已披露，未独立证明地理/邻帧隔离。ACDC强度支持未知，不是严格未见强度泛化。LwF是未经搜索的固定19类默认适配，单次表现不否定机制。resume保留优化器/调度器/iter，但RNG/采样游标不能精确恢复，不承诺逐位一致。',
 '', '下一阶段可依据三域已测保持/适应现象评估更长天气序列的必要性；本轮不自动扩展天气、种子或方法。']
 (run/'RESULTS.md').write_text('\n'.join(details)+'\n');(run/'SUMMARY.md').write_text('\n'.join(details)+'\n')
 write_json(run/'RESULTS_READY.json',dict(status='verified_results_complete_pending_figures_handoff',new_cells=22,reused_cells=20,total_cells=42,new_images=7000,training_methods=3,steps_per_method=4000,protocol_check_sha256=sha256(out/'protocol-independent-check.json'),training_check_sha256=sha256(out/'training-independent-check.json')))
 print('PASS formal training and 42-cell independent protocol/report checks')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--prepare',required=True);p.add_argument('--run',required=True);a=p.parse_args();main(a.prepare,a.run)
