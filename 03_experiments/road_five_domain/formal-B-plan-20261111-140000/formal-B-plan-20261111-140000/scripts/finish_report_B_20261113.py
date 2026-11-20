"""Reuse completed independent checks; rederive identical numeric tables and finish presentation/handoff."""
import json,os,shlex,shutil,subprocess,sys,time,traceback
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path('/home/ysheng4/research/GSMF-RS-DIL');sys.path.insert(0,str(ROOT));os.chdir(str(ROOT))
from road_dil.protocol import sha256,write_json
from tools.road.rain_formal import fingerprint
from analysis_B import report
prep=ROOT/'experiments/road_five_domain/prepare-20261111-140000';run=ROOT/'experiments/road_five_domain/formal-B-plan-20261111-140000';stamp=time.strftime('%Y%m%d-%H%M%S')
def read(p):return json.loads(Path(p).read_text())
def event(state,**kw):
 row=dict(time=datetime.now(timezone(timedelta(hours=8))).isoformat(),supervisor_pid=os.getpid(),state=state,**kw)
 with (run/'completion-events.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
 tmp=run/'completion-status.tmp';tmp.write_text(json.dumps(row,indent=2)+'\n');tmp.replace(run/'completion-status.json')
try:
 assert fingerprint()==read(prep/'READY.json')['code']
 idx=read(run/'results-index.json');old=Path(idx['directory']);assert sha256(old/'cells.json')==idx['cells_sha256'] and read(old/'verification.json')['status']=='PASS'
 training=read(old/'training-independent-check.json');protocol=read(old/'protocol-independent-check.json');assert training['status']==protocol['status']=='PASS' and len(training['runs'])==16 and len(training['periodic_checkpoints'])==64 and len(protocol['cells'])==112
 assert sum(c['provenance']=='new' for c in protocol['cells'])==104 and sum(c['images'] for c in protocol['cells'] if c['provenance']=='new')==26496
 assert read(run/'formal-conversion-logits-check.json')['status']==read(run/'nonpersistent-buffer-audit.json')['status']==read(run/'resume-audit-reconciliation.json')['status']=='PASS'
 # Preserve the failed formatting attempt and all its numerical tables; create a new
 # derived result directory, copy checks with identical SHA, and recompute only analysis.
 derived={'three-seed-all-conditions.json','three-seed-stage-matrices.json','three-seed-deltas-and-forgetting.json','three-seed-statistics.csv','road-destinations-all-seeds.csv','class-change-contributions-all-seeds.csv','confusion-consistency-three-seeds.json'}
 out=run/('results-final-'+stamp);shutil.copytree(old,out,ignore=lambda directory,names:[n for n in names if Path(directory)==old and n in derived])
 for name in ('training-independent-check.json','protocol-independent-check.json','cells.json','verification.json'):assert sha256(old/name)==sha256(out/name)
 event('running',task='report_format_repair',reused_training_protocol_checks=str(old))
 report(prep,run,out,training['runs'],read(out/'cells.json'))
 for name in derived:assert sha256(out/name)==sha256(old/name),'Numerical artifact changed: '+name
 write_json(run/('results-index-before-format-fix-'+stamp+'.json'),idx);idx.update(directory=str(out),prior_results=str(old),analysis_numeric_artifacts_identical=True);tmp=run/'final-results-index.tmp';tmp.write_text(json.dumps(idx,indent=2)+'\n');tmp.replace(run/'results-index.json')
 sources={str(p.relative_to(run)):sha256(p) for p in sorted((run/'scripts').glob('*.py'))};write_json(run/('final-report-provenance-'+stamp+'.json'),dict(sources=sources,reused_checks={name:sha256(old/name) for name in ('training-independent-check.json','protocol-independent-check.json','verification.json')},original_results=str(old),final_results=str(out),all_rederived_numeric_files_SHA_identical=True,reason='Report formatting repair only; no training or final-cell inference repeated'))
 for name in ('figures_B','package_B'):
  for path,h in sources.items():assert sha256(run/path)==h
  cmd=[sys.executable,str(run/'scripts'/(name+'.py')),'--prepare',str(prep),'--run',str(run)];log=run/('final-report-'+name+'-'+stamp+'.log');(run/('final-report-'+name+'-'+stamp+'-command.sh')).write_text(shlex.join(cmd)+'\n');t=time.monotonic()
  with log.open('x') as f:
   child=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT);event('running',task=name,child_pid=child.pid,log=str(log));rc=child.wait()
  write_json(run/('final-report-'+name+'-'+stamp+'-exit.json'),dict(command=cmd,exit_code=rc,seconds=time.monotonic()-t));assert rc==0,(name,rc)
 assert read(run/'completion.json')['status']=='complete' and read(run/'handoff/handoff-verification.json')['status']=='PASS';event('complete',archive=read(run/'completion.json')['handoff']['archive'],next_phase='C not authorized');(run/('final-report-'+stamp+'.exit')).write_text('0\n')
except BaseException as e:
 event('failed',error=repr(e));(run/('final-report-'+stamp+'.exit')).write_text('1\n');traceback.print_exc();raise
