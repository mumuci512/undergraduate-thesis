#!/usr/bin/env python
"""Independent stage-B training/protocol verification, signed tables and descriptive report."""
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
 prep=Path(prep).resolve();run=Path(run).resolve();ready=read(prep/'READY.json');plan=read(prep/'formal-plans.json')['B'];assert ready['code']==fingerprint();assert read(run/'provenance.json')['ready_sha256']==sha256(prep/'READY.json');assert (run/'exit-code.txt').read_text().strip()=='0';assert read(run/'status.json')['state']=='train_eval_verified_pending_handoff'
 if not (run/'formal-conversion-logits-check.json').exists():
  cmd=[sys.executable,str(run/'scripts/verify_conversion_logits_B.py'),'--prepare',str(prep),'--run',str(run)];(run/'verify_conversion_logits_B-command.sh').write_text(shlex.join(cmd)+'\n');t=time.monotonic()
  with (run/'verify_conversion_logits_B.log').open('x') as f:result=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
  write_json(run/'verify_conversion_logits_B-exit.json',dict(command=cmd,exit_code=result.returncode,seconds=time.monotonic()-t));assert result.returncode==0
 assert read(run/'formal-conversion-logits-check.json')['status']=='PASS'
 if not (run/'nonpersistent-buffer-audit.json').exists():
  cmd=[sys.executable,str(run/'scripts/verify_nonpersistent_buffers_B.py'),'--prepare',str(prep),'--run',str(run)];(run/'verify_nonpersistent_buffers_B-command.sh').write_text(shlex.join(cmd)+'\n');t=time.monotonic()
  with (run/'verify_nonpersistent_buffers_B.log').open('x') as f:result=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
  write_json(run/'verify_nonpersistent_buffers_B-exit.json',dict(command=cmd,exit_code=result.returncode,seconds=time.monotonic()-t));assert result.returncode==0
 assert read(run/'nonpersistent-buffer-audit.json')['status']=='PASS'
 idx=read(run/'results-index.json');out=Path(idx['directory']);assert sha256(out/'cells.json')==idx['cells_sha256'];assert read(out/'verification.json')['analysis_complete'];events=[json.loads(x) for x in (run/'events.jsonl').read_text().splitlines()];training={};periodic=[]
 for row in plan['runs']:
  key,m,d,seed=row['key'],row['method'],row['domain'],row['seed'];work=Path(row['work']);initpath=run/'initialization'/key/(m+'_init.pth');initial=torch.load(str(initpath),map_location='cpu');inv=read(work/'invocation.json');parent=Path(row['parent']);h=sha256(parent)
  assert inv['initialization_sha256']==sha256(initpath) and inv['optimizer']=='fresh' and inv['train_domain']==d and inv['seed']==seed and inv['order']=='ABCDE' and not inv['debug'] and not inv['synthetic_fixture'];validate_stage_input(initial,m,work,False,d,seed,'ABCDE');assert initial['meta']['parent_sha256']==h
  fresh=read(work/'fresh-optimizer.json');assert fresh==dict(iteration=0,optimizer_state_empty=True,domain=d,scheduler_end=4000,seed=seed)
  cfg=Config.fromfile(str(work/'resolved.py'));assert cfg.randomness.seed==seed and cfg.randomness.deterministic and cfg.train_cfg.max_iters==cfg.param_scheduler[0].end==4000 and cfg.train_cfg.val_interval==cfg.default_hooks.checkpoint.interval==1000;assert cfg.train_dataloader.batch_size==2 and cfg.model.data_preprocessor.size==(512,512);assert cfg.optim_wrapper.optimizer.lr==1e-5 and cfg.optim_wrapper.optimizer.weight_decay==.001
  expected_cfg=cfg_for(m,prep/'data',d);assert cfg.train_dataloader.dataset.pipeline==expected_cfg.train_dataloader.dataset.pipeline and cfg.model.data_preprocessor==expected_cfg.model.data_preprocessor
  assert Path(cfg.train_dataloader.dataset.ann_file)==prep/('data/'+d+'_train.jsonl') and Path(cfg.val_dataloader.dataset.ann_file)==prep/('data/'+d+'_val.jsonl')
  model=build(m);parameters=set(dict(model.named_parameters()))
  for i in (1000,2000,3000,4000):
   path=work/('iter_%d.pth'%i);ck=torch.load(str(path),map_location='cpu');validate_stage_input(ck,m,work,True,d,seed,'ABCDE');assert ck['meta']['iter']==i and ck['meta']['seed']==seed and ck['meta']['parent_sha256']==h and ck['param_schedulers'][0]['end']==4000;assert all(v['step']==i for v in ck['optimizer']['state'].values());assert_state(ck['state_dict'],model)
   assert all(bool(torch.isfinite(v).all()) for v in ck['state_dict'].values())
   assert all(bool(torch.isfinite(v).all()) for state in ck['optimizer']['state'].values() for v in state.values() if torch.is_tensor(v))
   periodic.append(dict(run=key,domain=d,iteration=i,path=str(path),sha256=sha256(path),bytes=path.stat().st_size,optimizer_scheduler_iteration_exact=True,all_model_and_optimizer_tensors_finite=True))
   if i!=4000:del ck;gc.collect()
  before=initial['state_dict'];after=ck['state_dict'];changed={k for k in after if not torch.equal(after[k],before[k])};audit=read(work/'audit-end-4000.json');raw_audit=audit
  if list(work.glob('resume-verified-*.json')):
   from recover_audit_B import effective_audit
   audit=effective_audit(prep,run,row,ck,audit)
  assert len(audit['losses'])==4000 and np.all(np.isfinite(audit['losses'])) and audit['finite_all_checked_gradients'] and len(audit['validation_seconds'])==4
  teacher_changed=[]
  if m!='ft':
   teacher=[k for k in after if k.startswith(('backbone.','decode_head.'))];assert all(torch.equal(after[k],before[k]) for k in teacher if k in parameters);teacher_changed=[k for k in teacher if k not in parameters and k in changed];assert len(teacher_changed)==(342 if m=='gsmf' else 0)
   if m=='gsmf':assert not any(k in changed for k in parameters if k.startswith(('backbone_1.stem.','backbone_1.layer1.')))
   else:assert all(audit['groups'][g]['changed_parameters']>0 for g in ('backbone_1.stem','backbone_1.layer1'))
  train=next(e for e in events if e.get('task')=='train-'+key and e['state']=='complete');exits=sorted(run.glob('train-'+key+'-*-exit.json'));elapsed=sum(read(p)['seconds'] for p in exits)
  training[key]=dict(method=m,domain=d,seed=seed,iterations=4000,parent=str(parent),parent_sha256=h,initialization=str(initpath),initialization_sha256=sha256(initpath),final_checkpoint_sha256=periodic[-1]['sha256'],fresh_optimizer=True,periodic_all_complete=True,teacher_changed_buffers=teacher_changed,groups=audit['groups'],losses_all_finite=True,gradient_check_scope=audit['gradient_check_scope'],finite_checked_gradients=True,training_wall_seconds=elapsed,seconds_per_step=audit['seconds_per_step_after_warmup'],validation_seconds=audit['validation_seconds'],peak_allocated_MiB=audit['peak_allocated_MiB'],peak_reserved_MiB=audit['peak_reserved_MiB'],total_parameters=audit['total_parameters'],trainable_parameters=audit['trainable_parameters'],resume_used=bool(list(work.glob('resume-verified-*.json'))),audit_segments_reconciled=(audit is not raw_audit),training_wall_time_includes_interrupted_prefix=(audit is raw_audit))
  del initial,ck,before,after,model;gc.collect()
 write_json(out/'training-independent-check.json',dict(status='PASS',runs=training,periodic_checkpoints=periodic))
 cells=read(out/'cells.json');assert len(cells)==112;checks=[];resources=[];histograms={};lookup={(c['model'],c['condition']):c for c in cells}
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
 assert sum(c['provenance']=='new' for c in checks)==104 and sum(c['images'] for c in checks if c['provenance']=='new')==26496 and all(histograms[c]==histograms['clear'] for c in ('fog005','fog010','fog020'))
 write_json(out/'protocol-independent-check.json',dict(status='PASS',cells=checks,GT_histograms=histograms));write_json(out/'resource-costs.json',dict(training=training,evaluation=resources,timing='monotonic/perf_counter; entry includes loading/reread, test loop includes I/O/metric/prediction saves; no pure GPU latency claim'));csvsave(out/'evaluation-resource-costs.csv',resources)
 csvsave(out/'class-iou-long.csv',[dict(model=c['model'],condition=c['condition'],class_name=k,IoU=c['IoU'][k],mIoU=c['mIoU'],provenance=c['provenance']) for c in cells for k in CLASSES]);csvsave(out/'class-iou-wide.csv',[dict(class_name=k,**{c['model']+'/'+c['condition']:c['IoU'][k] for c in cells}) for k in CLASSES])

 from analysis_B import report
 report(prep,run,out,training,cells)
 print('PASS phase B: 16 training/64 checkpoints; 104 new/8 Source reused; independent verification/report')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--prepare',required=True);p.add_argument('--run',required=True);a=p.parse_args();main(a.prepare,a.run)
