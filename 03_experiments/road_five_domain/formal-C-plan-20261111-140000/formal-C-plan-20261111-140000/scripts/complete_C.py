"""Supervise the authorized phase C; fail visibly, never retrain or retry silently."""
import json,os,shlex,subprocess,sys,time,traceback
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path('/home/ysheng4/research/GSMF-RS-DIL');sys.path.insert(0,str(ROOT))
from road_dil.protocol import sha256,write_json
from tools.road.rain_formal import fingerprint
prep=ROOT/'experiments/road_five_domain/prepare-20261111-140000';run=ROOT/'experiments/road_five_domain/formal-C-plan-20261111-140000';os.chdir(str(ROOT));started=time.monotonic()
def now():return datetime.now(timezone(timedelta(hours=8))).isoformat()
def event(state,**kw):
 row=dict(time=now(),supervisor_pid=os.getpid(),state=state,**kw)
 with (run/'completion-events.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
 temp=run/'completion-status.tmp';temp.write_text(json.dumps(row,indent=2)+'\n');temp.replace(run/'completion-status.json')
try:
 sources={str(p.relative_to(run)):sha256(p) for p in sorted((run/'scripts').glob('*.py'))};write_json(run/'postprocessing-provenance.json',dict(sources=sources,python=sys.executable,started_at=now(),core_code=fingerprint(),scope='No training/model/config changes. Phase-C-specific training and inference audit, Source provenance normalization, single-seed order report/plots/light package. Derived from accepted A/B verification where applicable.'))
 event('waiting_for_driver')
 while True:
  state=json.loads((run/'status.json').read_text());name=state['state']
  if name=='failed':raise RuntimeError('Formal driver failed: '+json.dumps(state))
  if name=='train_eval_verified_pending_handoff':break
  assert name in ('running','complete'),state
  pid=state['driver_pid'];os.kill(pid,0)
  done=[json.loads(x) for x in (run/'events.jsonl').read_text().splitlines()];ntrain=sum(e['state']=='complete' and e.get('task','').startswith('train-') for e in done);neval=sum(e['state']=='complete' and e.get('task','').startswith('eval-') for e in done)
  event('waiting_for_driver',driver=state,completed_training_runs=ntrain,completed_evaluation_cells=neval)
  (run/'STATUS.md').write_text('# 当前状态\n\n'+now()+'：阶段C运行中，完成训练%d/8，最终评价%d/46；当前%s。训练、独立复核与打包全部通过前不标complete。\n'%(ntrain,neval,state.get('task','transition')))
  time.sleep(30)
 assert (run/'exit-code.txt').read_text().strip()=='0' and len(json.loads((run/'completed-evaluations.json').read_text()))==46
 assert fingerprint()==json.loads((prep/'READY.json').read_text())['code']
 from normalize_source_C import normalize_source
 normalize_source(prep,run)
 for name in ('verify_report_C','figures_C','package_C'):
  for path,h in sources.items():assert sha256(run/path)==h,'Postprocessing code drift: '+path
  cmd=[sys.executable,str(run/'scripts'/(name+'.py')),'--prepare',str(prep),'--run',str(run)];log=run/(name+'.log');(run/(name+'-command.sh')).write_text(shlex.join(cmd)+'\n');t=time.monotonic()
  with log.open('x') as f:
   child=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT);event('running',task=name,child_pid=child.pid,command=cmd,log=str(log));rc=child.wait()
  write_json(run/(name+'-exit.json'),dict(command=cmd,exit_code=rc,seconds=time.monotonic()-t));assert rc==0,(name,rc)
 completion=json.loads((run/'completion.json').read_text());assert completion['status']=='complete' and completion['handoff']['status']=='PASS';event('complete',seconds=time.monotonic()-started,archive=completion['handoff']['archive']);(run/'completion-supervisor.exit').write_text('0\n')
except BaseException as e:
 event('failed',error=repr(e));(run/'completion-supervisor.exit').write_text('1\n');(run/'STATUS.md').write_text('# 当前状态\n\n'+now()+'：阶段C未完成，错误'+repr(e)+'。已产生训练、评价及检查证据保留；不自动重试、不标complete。\n');traceback.print_exc();raise
