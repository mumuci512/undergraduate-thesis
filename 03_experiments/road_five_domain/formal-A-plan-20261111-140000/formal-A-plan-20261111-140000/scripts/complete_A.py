#!/usr/bin/env python
"""Persistent stage-A completion supervisor, no retraining/retry/next phase."""
import json,os,shlex,subprocess,sys,time
from pathlib import Path
from datetime import datetime,timezone,timedelta
ROOT=Path('/home/ysheng4/research/GSMF-RS-DIL');sys.path.insert(0,str(ROOT))
from road_dil.protocol import sha256,write_json
prep=ROOT/'experiments/road_five_domain/prepare-20261111-140000';run=ROOT/'experiments/road_five_domain/formal-A-plan-20261111-140000';driver_pid=52917
os.chdir(str(ROOT));start=time.monotonic()
def event(state,**kw):
 row=dict(time=datetime.now(timezone(timedelta(hours=8))).isoformat(),supervisor_pid=os.getpid(),state=state,**kw)
 with (run/'completion-events.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
 (run/'completion-status.json').write_text(json.dumps(row,indent=2)+'\n')
try:
 event('waiting_training_evaluation_and_independent_results',driver_pid=driver_pid)
 while not (run/'exit-code.txt').exists():
  try:os.kill(driver_pid,0)
  except ProcessLookupError:raise RuntimeError('Formal driver stopped without an exit-code; preserve and investigate')
  time.sleep(10)
 assert (run/'exit-code.txt').read_text().strip()=='0','Formal pipeline failed; no dependent postprocessing'
 assert json.loads((run/'status.json').read_text())['state']=='train_eval_verified_pending_handoff'
 sources={str(p.relative_to(run)):sha256(p) for p in sorted((run/'scripts').glob('*.py'))};write_json(run/'postprocessing-provenance.json',dict(sources=sources,python=sys.executable,scope='Only phase A verification/plots/handoff; B deferred, C not authorized'))
 for name in ('verify_report_A','figures_A','package_A'):
  cmd=[sys.executable,str(run/'scripts'/(name+'.py')),'--prepare',str(prep),'--run',str(run)];(run/(name+'-command.sh')).write_text(shlex.join(cmd)+'\n');event('running',task=name,command=cmd);t=time.monotonic()
  with (run/(name+'.log')).open('x') as f:p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT);event('running',task=name,child_pid=p.pid);rc=p.wait()
  write_json(run/(name+'-exit.json'),dict(command=cmd,exit_code=rc,seconds=time.monotonic()-t));assert rc==0,(name,rc)
 completion=json.loads((run/'completion.json').read_text());assert completion['status']=='complete' and completion['handoff']['status']=='PASS';event('complete',seconds=time.monotonic()-start,archive=completion['handoff']['archive'],next_phase='B deferred; C not authorized');(run/'completion-supervisor.exit').write_text('0\n')
except BaseException as e:
 event('failed',error=repr(e));(run/'completion-supervisor.exit').write_text('1\n');raise
