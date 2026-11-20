"""Complete only the diagnosed postprocessing repair; reuse all completed training/evaluation."""
import json,os,shlex,subprocess,sys,time,traceback
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path('/home/ysheng4/research/GSMF-RS-DIL');sys.path.insert(0,str(ROOT))
from road_dil.protocol import sha256,write_json
from tools.road.rain_formal import fingerprint
prep=ROOT/'experiments/road_five_domain/prepare-20261111-140000';run=ROOT/'experiments/road_five_domain/formal-B-plan-20261111-140000';os.chdir(str(ROOT))
stamp=time.strftime('%Y%m%d-%H%M%S');start=time.monotonic()
def event(state,**kw):
 row=dict(time=datetime.now(timezone(timedelta(hours=8))).isoformat(),supervisor_pid=os.getpid(),state=state,**kw)
 with (run/'completion-events.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
 tmp=run/'completion-status.tmp';tmp.write_text(json.dumps(row,indent=2)+'\n');tmp.replace(run/'completion-status.json')
try:
 assert fingerprint()==json.loads((prep/'READY.json').read_text())['code']
 assert (run/'exit-code.txt').read_text().strip()=='0' and len(json.loads((run/'completed-evaluations.json').read_text()))==104
 idx=json.loads((run/'results-index.json').read_text());out=Path(idx['directory']);assert idx['source_provenance_normalized'] and sha256(out/'cells.json')==idx['cells_sha256'];assert json.loads((out/'verification.json').read_text())['status']=='PASS'
 sources={str(p.relative_to(run)):sha256(p) for p in sorted((run/'scripts').glob('*.py'))};write_json(run/('finalization-provenance-'+stamp+'.json'),dict(sources=sources,reason='Correct checkpoint-before-validation accounting; preserve original failed evidence. No retraining or repeated final cells.',results_index=idx,python=sys.executable))
 (run/'STATUS.md').write_text('# 当前状态\n\n'+datetime.now(timezone(timedelta(hours=8))).isoformat()+'：16/16训练、104/104最终评价及26496张预测独立重读通过。已定位并修正续训审计中checkpoint先保存、后验证的次数假设，正在重新独立验收/图表/打包；不重训、不重跑104格，不标complete。阶段C未授权。\n')
 for name in ('verify_report_B','figures_B','package_B'):
  for path,h in sources.items():assert sha256(run/path)==h,'Postprocessing code drift: '+path
  cmd=[sys.executable,str(run/'scripts'/(name+'.py')),'--prepare',str(prep),'--run',str(run)];log=run/('finalization-'+name+'-'+stamp+'.log');(run/('finalization-'+name+'-'+stamp+'-command.sh')).write_text(shlex.join(cmd)+'\n');event('running',task=name,log=str(log));t=time.monotonic()
  with log.open('x') as f:
   child=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT);event('running',task=name,child_pid=child.pid,log=str(log));rc=child.wait()
  write_json(run/('finalization-'+name+'-'+stamp+'-exit.json'),dict(command=cmd,exit_code=rc,seconds=time.monotonic()-t));assert rc==0,(name,rc)
 completion=json.loads((run/'completion.json').read_text());assert completion['status']=='complete' and completion['handoff']['status']=='PASS';event('complete',seconds=time.monotonic()-start,archive=completion['handoff']['archive'],next_phase='C not authorized');(run/('finalization-'+stamp+'.exit')).write_text('0\n')
except BaseException as e:
 event('failed',error=repr(e));(run/('finalization-'+stamp+'.exit')).write_text('1\n');(run/'STATUS.md').write_text('# 当前状态\n\n'+datetime.now(timezone(timedelta(hours=8))).isoformat()+'：后处理未完成，错误'+repr(e)+'。16次训练与104格最终评价保留，不自动重试、不标complete。阶段C未授权。\n');traceback.print_exc();raise
