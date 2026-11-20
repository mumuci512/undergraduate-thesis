#!/usr/bin/env python
"""Read-only phase-A progress/resource recorder, no retries, signals, or next phase."""
import json,os,re,shutil,subprocess,time
from pathlib import Path
from datetime import datetime,timezone,timedelta
run=Path('/home/ysheng4/research/GSMF-RS-DIL/experiments/road_five_domain/formal-A-plan-20261111-140000');root=run.parents[2]
while True:
 try:
  state=json.loads((run/'status.json').read_text());task=state.get('task','pipeline');logs=sorted(run.glob(task+'-*.log'),key=lambda p:p.stat().st_mtime);last=None
  if logs:
   lines=logs[-1].read_text(errors='replace').splitlines();progress=[x for x in lines if 'Iter(train)' in x or 'Iter(test)' in x or 'Iter(val)' in x]
   if progress:last=re.sub(r'\x1b\[[0-9;]*m','',progress[-1])
  index=run/'completed-evaluations.json';evaluations=len(json.loads(index.read_text())) if index.exists() else 0
  training=len([p for p in run.glob('train-*-exit.json') if json.loads(p.read_text())['exit_code']==0])
  gpu=subprocess.run(['/usr/lib/wsl/lib/nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader'],capture_output=True,text=True)
  completion=(run/'completion.json').exists();failed=((run/'exit-code.txt').exists() and (run/'exit-code.txt').read_text().strip()!='0') or ((run/'completion-supervisor.exit').exists() and (run/'completion-supervisor.exit').read_text().strip()!='0')
  row=dict(time=datetime.now(timezone(timedelta(hours=8))).isoformat(),state=state['state'],task=task,training_complete=training,total_training=6,evaluations_complete=evaluations,total_new_evaluations=62,progress=last,gpu=gpu.stdout.strip(),free_WSL_GiB=round(shutil.disk_usage(root).free/2**30,2),free_host_GiB=round(shutil.disk_usage('/mnt/c').free/2**30,2),all_complete=completion,failed=failed)
  with (run/'resource-monitor.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
  print(json.dumps(row,ensure_ascii=False),flush=True)
  if completion or failed:break
 except Exception as e:print(json.dumps(dict(monitor_error=repr(e))),flush=True)
 time.sleep(30)
