"""Preserve original audit; account for the interrupted/resumed Snow run using checkpoint history."""
import json,subprocess,sys,time
from pathlib import Path
import numpy as np
import torch
from road_dil.protocol import sha256,write_json
from tools.road.rain_results import independently_rebuild

def effective_audit(prep,run,row,checkpoint,audit):
 work=Path(row['work']);resume_files=sorted(work.glob('resume-verified-*.json'));assert row['key']=='gsmf-seed2-D' and len(resume_files)==1
 resume=json.loads(resume_files[0].read_text());assert resume['iteration']==3000 and resume['optimizer_exact'] and resume['scheduler_exact']
 parent=work/'iter_3000.pth';assert sha256(parent)=='d31159ab6a53b28ad9cb018cc9594e56032fdef6ab94071b249221e9c8c65994'
 saved=torch.load(str(parent),map_location='cpu');prefix=saved['message_hub']['log_scalars'];final=checkpoint['message_hub']['log_scalars'];losses=np.asarray(final['train/loss']._log_history);assert len(losses)==4000 and len(audit['losses'])==1000 and len(audit['validation_seconds'])==1
 assert np.array_equal(losses[:3000],prefix['train/loss']._log_history) and np.array_equal(losses[3000:],np.asarray(audit['losses'])) and np.all(np.isfinite(losses))
 # MMEngine saves iter_4000 before the final validation, just as iter_3000 was
 # saved before its interrupted validation. The checkpoint must retain exactly
 # the two completed prefix validations; final validation is certified by the
 # resumed hook audit (one call) and its completed 100/100 validation log.
 assert len(prefix['val/mIoU']._log_history)==len(final['val/mIoU']._log_history)==2
 assert np.array_equal(prefix['val/mIoU']._log_history,final['val/mIoU']._log_history)
 logs=sorted(run.glob('train-gsmf-seed2-D-*.log'),key=lambda p:p.stat().st_mtime)
 assert logs and 'Iter(val) [100/100]' in logs[-1].read_text()
 # Checkpoint 3000 was saved before its validation. Complete that immutable student's evaluation,
 # after all formal inference, without touching training state or counting it among 104 new final cells.
 target=run/'recovery-periodic-gsmf-seed2-D-3000';cmd=[sys.executable,str(Path.cwd()/'tools/road/run.py'),'eval','--stage','gsmf','--domain','D','--manifests',str(prep/'data'),'--checkpoint',str(parent),'--work-dir',str(target)]
 t=time.monotonic()
 if not target.exists():
  (run/'recovery-periodic-3000-command.sh').write_text(__import__('shlex').join(cmd)+'\n')
  with (run/'recovery-periodic-3000.log').open('x') as f:result=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
  write_json(run/'recovery-periodic-3000-exit.json',dict(exit_code=result.returncode,seconds=time.monotonic()-t,command=cmd));assert result.returncode==0
 ev=json.loads((target/'evaluation.json').read_text());assert ev['evaluated_images']==100 and ev['state_unchanged'] and ev['checkpoint_sha256']==sha256(parent)
 metrics,index=independently_rebuild(target,ev['manifest']);assert metrics['confusion_matrix']==json.loads((target/'independent-metrics.json').read_text())['confusion_matrix']
 valtimes=np.asarray(prefix['val/time']._log_history);assert len(valtimes)==200
 effective=dict(audit);effective['losses']=losses.tolist();effective['validation_seconds']=[float(valtimes[:100].sum()),float(valtimes[100:].sum()),ev['seconds'],audit['validation_seconds'][0]]
 proof=dict(status='PASS',checkpoint_saved_before_final_validation=True,validation_history_in_checkpoint=2,final_validation_confirmed_by_hook_and_log=True,resume_checkpoint=str(parent),resume_checkpoint_sha256=sha256(parent),resume_state_evidence=str(resume_files[0]),prefix_steps=3000,resumed_steps=1000,losses_complete_and_finite=True,loss_history_exactly_preserves_prefix=True,original_audit_unchanged=True,raw_audit_sha256=sha256(work/'audit-end-4000.json'),supplemental_validation=str(target),supplemental_images=100,supplemental_validation_independent_matrix=metrics['confusion_matrix'],validation_timing_note='First two timings are sums of original checkpoint per-image val/time history; third is supplemental eval test-loop time; fourth is resumed hook wall time. Not homogeneous pure-GPU timings.',gradient_note='Prefix hook certificate was not saved before interruption. Its 3000 per-step finite losses and model/optimizer finite states are retained in checkpoint; original registered hook enforces gradient finiteness each step. Resumed 1000-step hook audit and final freeze/BN comparisons verified separately.',wall_time_note='Interrupted original command has no exit-time file; resumed command wall time is a lower bound for full Snow run. Original log timestamps separately preserve the prefix interval.',RNG_note='RNG/sampler cursor were not checkpointed; resumed trajectory need not equal an uninterrupted run.')
 write_json(run/'resume-audit-reconciliation.json',proof)
 return effective
