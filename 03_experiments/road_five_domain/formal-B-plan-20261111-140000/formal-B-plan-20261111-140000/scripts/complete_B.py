"""Persistent B-only completion supervisor; monitor real processes, stop on failure, never retry."""
import json,os,shlex,subprocess,sys,time,traceback
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path('/home/ysheng4/research/GSMF-RS-DIL');sys.path.insert(0,str(ROOT))
from road_dil.protocol import sha256,write_json
from analysis_B import normalize_source
prep=ROOT/'experiments/road_five_domain/prepare-20261111-140000';run=ROOT/'experiments/road_five_domain/formal-B-plan-20261111-140000'
os.chdir(str(ROOT));start=time.monotonic();driver_pid=json.loads((run/'status.json').read_text())['driver_pid']
def now():return datetime.now(timezone(timedelta(hours=8))).isoformat()
def event(state,**kw):
 row=dict(time=now(),supervisor_pid=os.getpid(),state=state,**kw)
 with (run/'completion-events.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
 tmp=run/'completion-status.tmp';tmp.write_text(json.dumps(row,indent=2)+'\n');tmp.replace(run/'completion-status.json')
def active():
 status=json.loads((run/'status.json').read_text());task=status.get('task','');child=status.get('child_pid');done=sum(p.is_file() for p in run.glob('*-seed[12]-[BCDE]/iter_4000.pth'));index=run/'completed-evaluations.json';evaluations=len(json.loads(index.read_text())) if index.exists() else 0
 logfile=next(iter(sorted(run.glob(task+'-*.log'),key=lambda p:p.stat().st_mtime,reverse=True)),None) if task else None
 tail=[]
 if logfile:
  with logfile.open('rb') as f:f.seek(max(0,logfile.stat().st_size-4096));tail=f.read().decode(errors='replace').splitlines()[-3:]
 row=dict(time=now(),driver_pid=driver_pid,driver_state=status,child_pid=child,training_complete=done,training_total=16,evaluation_complete=evaluations,evaluation_total=104,log=str(logfile) if logfile else None,last_log_lines=tail,WSL_free_GiB=os.statvfs(str(ROOT)).f_bavail*os.statvfs(str(ROOT)).f_frsize/2**30,host_free_GiB=os.statvfs('/mnt/c').f_bavail*os.statvfs('/mnt/c').f_frsize/2**30)
 with (run/'monitor.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
 tmp=run/'monitor.tmp';tmp.write_text(json.dumps(row,indent=2)+'\n');tmp.replace(run/'monitor-latest.json')
 (run/'STATUS.md').write_text('# 当前状态\n\n'+now()+'：阶段B运行中，训练%d/16，新增评价%d/104；当前%s。尚未完成独立复核和交接，不标complete。\n\n实测进程/日志/磁盘见monitor-latest.json，正式退出码见exit-code.txt，完成监督见completion-status.json。任一失败停止整阶段，不自动重试。阶段C未授权。\n'%(done,evaluations,task))
 return row
try:
 sources={str(p.relative_to(run)):sha256(p) for p in sorted((run/'scripts').glob('*.py'))};write_json(run/('postprocessing-provenance-recovery-'+time.strftime('%Y%m%d-%H%M%S')+'.json'),dict(sources=sources,python=sys.executable,scope='Only phase B verification/plots/handoff; C not authorized',created_at=now()))
 event('waiting_training_evaluation_and_independent_results',driver_pid=driver_pid)
 tick=0
 while not (run/'exit-code.txt').exists():
  os.kill(driver_pid,0)
  if tick%6==0:active()
  tick+=1;time.sleep(10)
 assert (run/'exit-code.txt').read_text().strip()=='0','Formal pipeline failed; no dependent postprocessing'
 assert json.loads((run/'status.json').read_text())['state']=='train_eval_verified_pending_handoff'
 active();event('normalizing_inherited_Source_provenance');normalize_source(prep,run)
 for name in ('verify_report_B','figures_B','package_B'):
  for path,h in sources.items():assert sha256(run/path)==h,'Postprocessing code drift: '+path
  cmd=[sys.executable,str(run/'scripts'/(name+'.py')),'--prepare',str(prep),'--run',str(run)];(run/(name+'-command.sh')).write_text(shlex.join(cmd)+'\n');event('running',task=name,command=cmd);t=time.monotonic()
  with (run/(name+'.log')).open('x') as f:
   child=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT);event('running',task=name,child_pid=child.pid);rc=child.wait()
  write_json(run/(name+'-exit.json'),dict(command=cmd,exit_code=rc,seconds=time.monotonic()-t));assert rc==0,(name,rc)
 completion=json.loads((run/'completion.json').read_text());assert completion['status']=='complete' and completion['handoff']['status']=='PASS';event('complete',seconds=time.monotonic()-start,archive=completion['handoff']['archive'],next_phase='C not authorized');(run/'completion-supervisor.exit').write_text('0\n')
except BaseException as e:
 event('failed',error=repr(e));(run/'completion-supervisor.exit').write_text('1\n');(run/'STATUS.md').write_text('# 当前状态\n\n'+now()+'：阶段B失败，保留现场，不自动重试、不标complete。错误：'+repr(e)+'。详见completion-supervisor.log、completion-status.json及正式status.json/exit-code.txt。阶段C未授权。\n')
 p=ROOT/'REPRO.md';text=p.read_text();a=text.index('<!-- ROAD_FIVE_DOMAIN_CURRENT_BEGIN -->');b=text.index('<!-- ROAD_FIVE_DOMAIN_CURRENT_END -->')+len('<!-- ROAD_FIVE_DOMAIN_CURRENT_END -->');block='<!-- ROAD_FIVE_DOMAIN_CURRENT_BEGIN -->\n## 当前道路工作：第5项阶段B中断待调查（'+now()[:10]+'）\n\n- 用户已授权阶段B，正式目录：`'+str(run.relative_to(ROOT))+'`。实际失败：`'+repr(e)+'`，未完成、不自动重试。完成项、进程与日志见STATUS.md、monitor-latest.json、status.json、completion-status.json；未启动阶段C。阶段A已完成证据保留在formal-A-plan-20261111-140000。\n<!-- ROAD_FIVE_DOMAIN_CURRENT_END -->';p.write_text(text[:a]+block+text[b:]);traceback.print_exc();raise
