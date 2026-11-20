#!/usr/bin/env python
"""Independent stage-A training/protocol verification, signed tables and descriptive report."""
import argparse,csv,gc,json,sys,time,subprocess,shlex
from pathlib import Path
import numpy as np
import torch
from mmengine.config import Config
ROOT=Path('/home/ysheng4/research/GSMF-RS-DIL');sys.path.insert(0,str(ROOT))
from road_dil.protocol import CLASSES,sha256,write_json
from road_dil.checkpoints import build,assert_state,validate_stage_input
from tools.road.rain_formal import fingerprint
from tools.road.five_common import CONDITIONS,REAL
from tools.road.run import cfg_for

def read(p):return json.loads(Path(p).read_text())
def records(p):return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
def csvsave(p,rows):
 with Path(p).open('x',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main(prep,run):
 prep=Path(prep).resolve();run=Path(run).resolve();ready=read(prep/'READY.json');plan=read(prep/'formal-plans.json')['A'];assert ready['code']==fingerprint();assert read(run/'provenance.json')['ready_sha256']==sha256(prep/'READY.json');assert (run/'exit-code.txt').read_text().strip()=='0';assert read(run/'status.json')['state']=='train_eval_verified_pending_handoff'
 if not (run/'formal-conversion-logits-check.json').exists():
  cmd=[sys.executable,str(run/'scripts/verify_conversion_logits_A.py'),'--prepare',str(prep),'--run',str(run)];(run/'verify_conversion_logits_A-command.sh').write_text(shlex.join(cmd)+'\n');t=time.monotonic()
  with (run/'verify_conversion_logits_A.log').open('x') as f:result=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
  write_json(run/'verify_conversion_logits_A-exit.json',dict(command=cmd,exit_code=result.returncode,seconds=time.monotonic()-t));assert result.returncode==0
 assert read(run/'formal-conversion-logits-check.json')['status']=='PASS'
 if not (run/'nonpersistent-buffer-audit.json').exists():
  cmd=[sys.executable,str(run/'scripts/verify_nonpersistent_buffers_A.py'),'--prepare',str(prep),'--run',str(run)];(run/'verify_nonpersistent_buffers_A-command.sh').write_text(shlex.join(cmd)+'\n');t=time.monotonic()
  with (run/'verify_nonpersistent_buffers_A.log').open('x') as f:result=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
  write_json(run/'verify_nonpersistent_buffers_A-exit.json',dict(command=cmd,exit_code=result.returncode,seconds=time.monotonic()-t));assert result.returncode==0
 assert read(run/'nonpersistent-buffer-audit.json')['status']=='PASS'
 idx=read(run/'results-index.json');out=Path(idx['directory']);assert sha256(out/'cells.json')==idx['cells_sha256'];assert read(out/'verification.json')['analysis_complete'];events=[json.loads(x) for x in (run/'events.jsonl').read_text().splitlines()];training={};periodic=[]
 for row in plan['runs']:
  key,m,d=row['key'],row['method'],row['domain'];work=Path(row['work']);initpath=run/'initialization'/key/(m+'_init.pth');initial=torch.load(str(initpath),map_location='cpu');inv=read(work/'invocation.json');parent=Path(row['parent']);h=sha256(parent)
  assert inv['initialization_sha256']==sha256(initpath) and inv['optimizer']=='fresh' and inv['train_domain']==d and inv['seed']==0 and inv['order']=='ABCDE' and not inv['debug'] and not inv['synthetic_fixture'];validate_stage_input(initial,m,work,False,d,0,'ABCDE');assert initial['meta']['parent_sha256']==h
  fresh=read(work/'fresh-optimizer.json');assert fresh==dict(iteration=0,optimizer_state_empty=True,domain=d,scheduler_end=4000,seed=0)
  cfg=Config.fromfile(str(work/'resolved.py'));assert cfg.randomness.seed==0 and cfg.randomness.deterministic and cfg.train_cfg.max_iters==cfg.param_scheduler[0].end==4000 and cfg.train_cfg.val_interval==cfg.default_hooks.checkpoint.interval==1000;assert cfg.train_dataloader.batch_size==2 and cfg.model.data_preprocessor.size==(512,512);assert cfg.optim_wrapper.optimizer.lr==1e-5 and cfg.optim_wrapper.optimizer.weight_decay==.001
  expected_cfg=cfg_for(m,prep/'data',d);assert cfg.train_dataloader.dataset.pipeline==expected_cfg.train_dataloader.dataset.pipeline and cfg.model.data_preprocessor==expected_cfg.model.data_preprocessor
  assert Path(cfg.train_dataloader.dataset.ann_file)==prep/('data/'+d+'_train.jsonl') and Path(cfg.val_dataloader.dataset.ann_file)==prep/('data/'+d+'_val.jsonl')
  model=build(m);parameters=set(dict(model.named_parameters()))
  for i in (1000,2000,3000,4000):
   path=work/('iter_%d.pth'%i);ck=torch.load(str(path),map_location='cpu');validate_stage_input(ck,m,work,True,d,0,'ABCDE');assert ck['meta']['iter']==i and ck['meta']['seed']==0 and ck['meta']['parent_sha256']==h and ck['param_schedulers'][0]['end']==4000;assert all(v['step']==i for v in ck['optimizer']['state'].values());assert_state(ck['state_dict'],model)
   assert all(bool(torch.isfinite(v).all()) for v in ck['state_dict'].values())
   assert all(bool(torch.isfinite(v).all()) for state in ck['optimizer']['state'].values() for v in state.values() if torch.is_tensor(v))
   periodic.append(dict(run=key,domain=d,iteration=i,path=str(path),sha256=sha256(path),bytes=path.stat().st_size,optimizer_scheduler_iteration_exact=True,all_model_and_optimizer_tensors_finite=True))
   if i!=4000:del ck;gc.collect()
  before=initial['state_dict'];after=ck['state_dict'];changed={k for k in after if not torch.equal(after[k],before[k])};audit=read(work/'audit-end-4000.json');assert len(audit['losses'])==4000 and np.all(np.isfinite(audit['losses'])) and audit['finite_all_checked_gradients'] and len(audit['validation_seconds'])==4
  teacher_changed=[]
  if m!='ft':
   teacher=[k for k in after if k.startswith(('backbone.','decode_head.'))];assert all(torch.equal(after[k],before[k]) for k in teacher if k in parameters);teacher_changed=[k for k in teacher if k not in parameters and k in changed];assert len(teacher_changed)==(342 if m=='gsmf' else 0)
   if m=='gsmf':assert not any(k in changed for k in parameters if k.startswith(('backbone_1.stem.','backbone_1.layer1.')))
   else:assert all(audit['groups'][g]['changed_parameters']>0 for g in ('backbone_1.stem','backbone_1.layer1'))
  train=next(e for e in events if e.get('task')=='train-'+key and e['state']=='complete');exits=sorted(run.glob('train-'+key+'-*-exit.json'));elapsed=sum(read(p)['seconds'] for p in exits)
  training[key]=dict(method=m,domain=d,seed=0,iterations=4000,parent=str(parent),parent_sha256=h,initialization=str(initpath),initialization_sha256=sha256(initpath),final_checkpoint_sha256=periodic[-1]['sha256'],fresh_optimizer=True,periodic_all_complete=True,teacher_changed_buffers=teacher_changed,groups=audit['groups'],losses_all_finite=True,gradient_check_scope=audit['gradient_check_scope'],finite_checked_gradients=True,training_wall_seconds=elapsed,seconds_per_step=audit['seconds_per_step_after_warmup'],validation_seconds=audit['validation_seconds'],peak_allocated_MiB=audit['peak_allocated_MiB'],peak_reserved_MiB=audit['peak_reserved_MiB'],total_parameters=audit['total_parameters'],trainable_parameters=audit['trainable_parameters'],resume_used=bool(list(work.glob('resume-verified-*.json'))))
  del initial,ck,before,after,model;gc.collect()
 write_json(out/'training-independent-check.json',dict(status='PASS',runs=training,periodic_checkpoints=periodic))
 cells=read(out/'cells.json');assert len(cells)==104;checks=[];resources=[];histograms={};lookup={(c['model'],c['condition']):c for c in cells}
 for c in cells:
  directory=Path(c['evidence']);ev=read(directory/'evaluation.json');assert sha256(c['checkpoint'])==c['checkpoint_sha256']==ev['checkpoint_sha256'];assert ev['state_unchanged'] and ev['stage']==c['method'] and ev['domain']==c['domain'] and ev['evaluated_images']==c['images']==CONDITIONS[c['condition']][1]
  cfgfiles=list(directory.glob('*.py'));assert len(cfgfiles)==1;cfg=Config.fromfile(str(cfgfiles[0]));rs=records(cfg.test_dataloader.dataset.ann_file);manifest=prep/'eval-manifests'/c['condition']/'A_val.jsonl' if c['condition'] in ('clear','fog005','fog010','fog020') else prep/('data/'+c['domain']+'_val.jsonl');ref=records(manifest);fields=('id','image','label','encoding','domain','split');assert [{k:r[k] for k in fields} for r in rs]==[{k:r[k] for k in fields} for r in ref];assert len({r['id'] for r in rs})==len(rs)
  truth=[sum(r['label_histogram'].get(str(i),0) for r in ref) for i in range(19)];assert np.asarray(c['confusion_matrix'],np.int64).sum(1).tolist()==truth
  if c['condition'] in histograms:assert histograms[c['condition']]==truth
  else:histograms[c['condition']]=truth
  baseline=cfg_for(c['method'],prep/'data');assert cfg.model.data_preprocessor==baseline.model.data_preprocessor and cfg.test_dataloader.dataset.pipeline==baseline.test_dataloader.dataset.pipeline
  assert cfg.model.test_cfg.mode=='slide' and cfg.model.test_cfg.crop_size==(512,512) and cfg.model.test_cfg.stride==(341,341)
  if c['method'] in ('gsmf','lwf'):assert ev['forward_calls']['backbone']==ev['forward_calls']['decode_head.conv_seg']==0 and ev['forward_calls']['backbone_1']>0
  if c['provenance']=='new':
   assert not ev['debug'] and not ev['synthetic_fixture'] and ev['full_official_split'];proof=read(out/'verification'/(c['model']+'-'+c['condition']+'.json'));assert proof['status']=='PASS' and len(proof['predictions'])==len(rs);assert proof['metrics']['confusion_matrix']==c['confusion_matrix'];assert {v['id'] for v in proof['predictions']}=={r['id'] for r in ref}
  checks.append(dict(model=c['model'],condition=c['condition'],provenance=c['provenance'],images=len(ref),checkpoint_sha256=c['checkpoint_sha256'],manifest=str(manifest),manifest_sha256=sha256(manifest),exact_ID_paths_encoding=True,GT_histogram_exact=True,student_only=True,state_unchanged=True,evaluation_sha256=sha256(directory/'evaluation.json')))
  name='eval-'+c['model']+'-'+c['condition'];exits=sorted(run.glob(name+'-*-exit.json'));resources.append(dict(model=c['model'],condition=c['condition'],provenance=c['provenance'],images=len(ref),test_loop_seconds=ev['seconds'],entry_wall_seconds=sum(read(p)['seconds'] for p in exits) if exits else None,checkpoint_bytes=ev['checkpoint_bytes'],peak_allocated_MiB=ev.get('peak_allocated_MiB')))
 assert sum(c['provenance']=='new' for c in checks)==62 and sum(c['images'] for c in checks if c['provenance']=='new')==15878 and all(histograms[c]==histograms['clear'] for c in ('fog005','fog010','fog020'))
 write_json(out/'protocol-independent-check.json',dict(status='PASS',cells=checks,GT_histograms=histograms));write_json(out/'resource-costs.json',dict(training=training,evaluation=resources,timing='monotonic/perf_counter; entry includes loading/reread, test loop includes I/O/metric/prediction saves; no pure GPU latency claim'));csvsave(out/'evaluation-resource-costs.csv',resources)
 csvsave(out/'class-iou-long.csv',[dict(model=c['model'],condition=c['condition'],class_name=k,IoU=c['IoU'][k],mIoU=c['mIoU'],provenance=c['provenance']) for c in cells for k in CLASSES]);csvsave(out/'class-iou-wide.csv',[dict(class_name=k,**{c['model']+'/'+c['condition']:c['IoU'][k] for c in cells}) for k in CLASSES])
 matrices=read(out/'stage-matrices.json');deltas=read(out/'signed-deltas-and-forgetting.json');synthetic=[];road=[]
 stages_by_method={m:['source',m+'_fog',m+'_rain',m+'-seed0-D',m+'-seed0-E'] for m in ('ft','gsmf','lwf')}
 for m,names in stages_by_method.items():
  for t,name in enumerate(names):
   synthetic.append(dict(method=m,stage=name,**{d:lookup[name,d]['mIoU'] for d in ('clear','fog005','fog010','fog020')}))
   for cond in REAL[:t+1]:
    c=np.array(lookup[name,cond]['confusion_matrix'],np.int64);v=c[0];row=dict(method=m,stage=name,condition=cond,road_GT_pixels=int(v.sum()))
    row.update({'road_to_'+k:float(v[CLASSES.index(k)]/v.sum()) if v.sum() else None for k in CLASSES});road.append(row)
 csvsave(out/'synthetic-conditions.csv',synthetic);csvsave(out/'road-destinations-all-classes.csv',road)
 lines=['# 五域主序列：阶段 A seed0 正式结果','', '六次训练及62个新增完整评价格15878逐图完成；42旧格指纹核对后复用，共13检查点×8条件104格。固定iter4000，无val择优。Source行共享。','', '| 方法/阶段 | CS | Fog | Rain | Snow | Night | 已见域等权均值 |','|---|---:|---:|---:|---:|---:|---:|']
 for key,rs in matrices.items():
  for row in rs:lines.append('| %s/%s | %s | %.4f |'%(key,row['stage'],' | '.join('%.4f'%row['values'][d] for d in REAL),row['seen_domain_equal_mean']))
 lines+=['','各阶段均值只含当时已学域，未来域提前分数不计入。最终五真实域均值与合成条件分开，不算八条件混合均值。','', '| 方法/更新 | CS变化 | Fog变化 | Rain变化 | Snow变化 | Night变化 |','|---|---:|---:|---:|---:|---:|']
 for key,obj in deltas.items():
  for change in obj['stage_changes'][-2:]:lines.append('| %s/%s | %s |'%(key,change['stage'],' | '.join('%+.4f'%change['after_minus_before'][d] for d in REAL)))
 lines+=['','差值均after-before，保留正负；旧域遗忘=max(已学且早于最终阶段)-最终，参照阶段详见signed-deltas-and-forgetting.json，不加入Night零项，不报FWT。','', '| 方法 | 最终五真实域均值 | 旧域平均遗忘 |','|---|---:|---:|']
 for key,obj in deltas.items():lines.append('| %s | %.4f | %.4f |'%(key,obj['final_five_real_domain_mean'],obj['old_domain_mean_forgetting']))
 for other in ('ft','lwf'):
  lines+=['','最终GSMF−'+other+'：'+', '.join(d+' %+.4fpp'%(lookup['gsmf-seed0-E',d]['mIoU']-lookup[other+'-seed0-E',d]['mIoU']) for d in REAL)+'。仅描述当前seed0。']
 lines+=['','## 晴天道路误判去向','', '| 方法/阶段 | road→terrain % | road→truck % | road→building % |','|---|---:|---:|---:|']
 for r in road:
  if r['condition']=='clear':lines.append('| %s/%s | %.4f | %.4f | %.4f |'%(r['method'],r['stage'],100*r['road_to_terrain'],100*r['road_to_truck'],100*r['road_to_building']))
 for m in ('ft','gsmf','lwf'):
  for target in ('terrain','truck','building'):
   values={r['stage']:r['road_to_'+target] for r in road if r['method']==m and r['condition']=='clear'};base=values['source'];above=[name for name in (m+'-seed0-D',m+'-seed0-E') if values[name]>base]
   lines.append(m+' 的晴天 road→'+target+' 在Snow后/Night后分别为 %.4f%% / %.4f%%，Source为 %.4f%%；两次后续更新中有%d次高于Source。该计数仅为描述性参照，不作为显著性或因果证据。'%(100*values[m+'-seed0-D'],100*values[m+'-seed0-E'],100*base,len(above)))
 lines+=['','完整road top5、指定类别面积比/召回/误报来源top3、相对Source的ΔIoU/19见confusion-tracking.json；所有road去向见CSV。这里只描述误判在阶段中的变化，不推断因果。','', 'FT全量CE；原版GSMF教师参数冻结但训练态BN更新、学生stem/layer1参数冻结但BN更新；LwF教师eval/no_grad全部状态固定、学生全量更新。输出KD为原生stride4全像素（含ignore/padding）、无显式T²；不改损失、不加BN变体。所有天气仅部署学生，无oracle、TTA或测试更新。每格全量网络推理前后逐键比较参数及全部持久缓冲；非持久缓冲只有前处理mean/std，以实际安装前处理只读实现及全部2406张原生验证图的前处理前后比对另行核验，见nonpersistent-buffer-audit.json。', '', '局限：仅seed0，不证明显著或稳定排序；跨库差异不能全部归因天气；官方视频目录交叉已披露，地理/邻帧隔离未独立证明。LwF未经超参搜索。CUDA双线性插值反向不保证逐位确定，resume不能精确恢复RNG/采样游标。不主张严格未见强度泛化。', '', '训练墙钟合计 %.2f分钟；新增评价入口墙钟合计 %.2f分钟；独立复核/图表/打包另计。计时由monotonic/perf_counter给出，非纯GPU延迟。'%(sum(v['training_wall_seconds'] for v in training.values())/60,sum(v['entry_wall_seconds'] or 0 for v in resources if v['provenance']=='new')/60),'', '最新用户范围为“暂时先完成阶段A”：阶段B暂缓，阶段C未授权。']
 (run/'RESULTS.md').write_text('\n'.join(lines)+'\n');(run/'SUMMARY.md').write_text('\n'.join(lines)+'\n');write_json(run/'RESULTS_READY.json',dict(status='verified_pending_figures_package',new_cells=62,reused_cells=42,total_cells=104,new_images=15878,training_runs=6,periodic_checkpoints=24))
 print('PASS stage A: 6 training/24 checkpoints; 62 new/42 reused; independent protocol/report complete')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--prepare',required=True);p.add_argument('--run',required=True);a=p.parse_args();main(a.prepare,a.run)
