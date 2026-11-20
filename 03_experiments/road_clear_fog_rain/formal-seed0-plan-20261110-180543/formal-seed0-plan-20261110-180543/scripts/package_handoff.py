#!/usr/bin/env python
"""Explicit light package allowlist, safe unpack, exact file-set and SHA verification."""
import argparse,csv,json,os,shutil,subprocess,sys,tarfile,tempfile
from pathlib import Path
from datetime import datetime,timezone,timedelta
ROOT=Path('/home/ysheng4/research/GSMF-RS-DIL');sys.path.insert(0,str(ROOT))
from road_dil.protocol import sha256,write_json
from tools.road.rain_common import METHODS,PARENTS,SEVERITY,OLD,LWF

def read(p):return json.loads(Path(p).read_text())
def copy(src,dst):
 src=Path(src);dst=Path(dst);dst.parent.mkdir(parents=True,exist_ok=True)
 assert src.is_file(),src;assert not dst.exists(),dst;shutil.copy2(str(src),str(dst))
def now():return datetime.now(timezone(timedelta(hours=8))).isoformat()
def main(prep,run):
 prep=Path(prep).resolve();run=Path(run).resolve();out=run/'results'
 assert read(out/'independent-final-check.json')['status']=='PASS'
 assert read(out/'protocol-independent-check.json')['status']=='PASS'
 assert read(out/'training-independent-check.json')['status']=='PASS'
 assert read(out/'fixed-sample-selection-and-index.json')['status']=='PASS'
 assert (run/'exit-code.txt').read_text().strip()=='0'
 cells=read(out/'42-cells.json');training=read(out/'training-independent-check.json');weights={}
 for m,(p,h) in PARENTS.items():
  assert sha256(p)==h;weights['source' if m=='source' else m+'_fog']=dict(path=str(p),sha256=h,bytes=p.stat().st_size)
 for m in METHODS:
  p=run/m/'iter_4000.pth';weights[m+'_rain']=dict(path=str(p),sha256=sha256(p),bytes=p.stat().st_size)
 predictions=[]
 for c in cells:
  name=c['model']+'-'+c['condition'];directory=Path(c['evidence'])
  predictions.append(dict(model=c['model'],condition=c['condition'],provenance=c['provenance'],images=c['images'],directory=str(directory/'predictions'),checkpoint_sha256=c['checkpoint_sha256'],evaluation=str(directory/'evaluation.json'),metrics=str(directory/'independent-metrics.json'),
   independent_prediction_index=str(out/'verification'/(name+'.json')) if c['provenance']=='new' else None))
 remote=dict(run=str(run),preparation=str(prep),project=str(ROOT),python='/home/ysheng4/miniconda3/envs/GSMF_RS_DIL/bin/python',unique_checkpoints=weights,
  Rain_periodic_checkpoints=training['periodic_checkpoints'],initializations=read(prep/'READY.json')['initializations'],predictions=predictions,
  datasets=dict(road_manifests=str(prep/'data'),Rain_archive_provenance=read(prep/'data/audit.json')['archive_provenance'],six_conditions=str(prep/'eval-manifests')),
  excluded=['all checkpoint payloads','raw datasets and archives','full prediction PNG sets','Conda environment','cookies/authentication files','.git'])
 write_json(run/'remote-index.json',remote)
 (run/'STATUS.md').write_text('# 当前状态\n\n'+now()+'：三组各4000步、22格7000逐图、42格来源/矩阵/逐类/训练与协议独立核验、固定72份CS新原始预测与Rain样例及图表均已完成。正在生成轻量包并进行安全成员/实际解包/文件集合与SHA核验；核验结束前不标完整任务complete。\n')
 packroot=run/'handoff';packroot.mkdir(exist_ok=False);content=packroot/'content'/run.name;content.mkdir(parents=True)
 for name in ['PLAN.md','PREPARED_PLAN.md','STATUS.md','RESULTS.md','SUMMARY.md','authorization.json','provenance.json','events.jsonl','status.json','exit-code.txt','remote-index.json','RESULTS_READY.json','independent-finalize.log','independent-finalize-exit.json','execution-summary.json','figures.log','figures-exit.json','postprocessing-provenance.json','postprocess-command.sh']:
  copy(run/name,content/name)
 copy(run/'validated-source.tar.gz',content/'source/validated-training-source.tar.gz')
 copy(prep/'code-fingerprint.json',content/'source/code-fingerprint.json')
 for name in ['AGENTS.md','REPRO.md','STEP3_RAIN_CHAIN_REMOTE_TASK_20261110.md']:
  copy(ROOT/name,content/'source'/name)
 for name in ['conda-linux-64.explicit.txt','pip-linux-64.lock.txt']:copy(ROOT/'environment'/name,content/'environment'/name)
 with (content/'source/git-diff.patch').open('x') as f:subprocess.run(['git','diff','--binary'],stdout=f,cwd=ROOT,check=True)
 with (content/'source/git-status.txt').open('x') as f:subprocess.run(['git','status','--short'],stdout=f,cwd=ROOT,check=True)
 shutil.copytree(run/'scripts',content/'scripts',ignore=shutil.ignore_patterns('__pycache__'))
 shutil.copytree(out,content/'results')
 # Each stage's exact command, console, exit status and resolved/audit artifacts.
 for p in run.iterdir():
  if p.is_file() and (p.name.startswith('train-') or p.name.startswith('eval-')) and p.suffix in ('.log','.json','.sh'):
   copy(p,content/'execution'/p.name)
 for m in METHODS:
  for p in (run/m).rglob('*'):
   if p.is_file() and p.suffix in ('.json','.py','.log') and 'vis_data' not in p.parts:copy(p,content/'training'/m/p.relative_to(run/m))
 for c in cells:
  directory=Path(c['evidence']);name=c['model']+'-'+c['condition']
  # Matrices/config/metadata for all 42 cells, including reused evidence.
  for p in directory.glob('*'):
   if p.is_file() and p.suffix in ('.json','.py','.txt'):copy(p,content/'evaluation'/name/p.name)
  if c['provenance']=='new':
   for p in directory.rglob('*.log'):
    if 'vis_data' not in p.parts:copy(p,content/'evaluation'/name/p.relative_to(directory))
 names=['READY.json','PREPARED_PLAN.md','STATUS.md','COMMANDS.md','authorization.json','environment.json','fixed-checkpoints.json','ancestor-provenance.json','evaluation-plan.json','rain-fixed-samples.json','initial-chain-verification.json','trained-chain-verification.json','short-runs-completion.json','contract-checks.json','small-evaluations.json','compatibility.json','validation-reentry.json','resource-estimate.json','source-snapshot.json','source-snapshot-verification.json','preparation-integrity.json','nonoptimization-times.json','debug-budget.json','formal-launch.log','formal-preflight-check.log','git-diff-final.patch','git-status-final.txt','validated-source.tar.gz','tmux-probe.sh','tmux-probe.log','tmux-probe.exit']
 for name in names:copy(prep/name,content/'preparation'/name)
 for p in (prep/'conversion').rglob('*.json'):copy(p,content/'preparation/conversion'/p.relative_to(prep/'conversion'))
 for p in prep.glob('*-formal-resolved.py'):copy(p,content/'preparation'/p.name)
 for p in (prep/'data').iterdir():
  if p.is_file() and p.suffix in ('.json','.jsonl'):copy(p,content/'data-index/three-domain-manifests'/p.name)
 for p in (prep/'eval-manifests').rglob('*'):
  if p.is_file():copy(p,content/'data-index/evaluation-manifests'/p.relative_to(prep/'eval-manifests'))
 rain_provenance=Path(read(prep/'data/audit.json')['archive_provenance']);copy(rain_provenance,content/'data-index/Rain-archive-provenance.json')
 for name in ['sample_ids.json','scene_ids.json']:copy(SEVERITY/'prepared-20261110'/name,content/'data-index'/('Cityscapes-'+name))
 for src,name in [(SEVERITY/'evaluation-20261110/independent-final-check.json','severity-independent-final-check.json'),(OLD/'final-independent-verification.json','two-domain-independent-final-check.json'),(LWF/'results/independent-final-check.json','LwF-Fog-independent-final-check.json')]:copy(src,content/'reused-source'/name)
 assert not list(content.rglob('*.pth'))
 # Only small preselected raw masks/aligned figures are included, not full prediction sets.
 CS_masks=list((content/'results/fixed-samples').rglob('*.png'));rain_masks=list((content/'results/rain-fixed-samples').rglob('*.png'))
 assert len(CS_masks)==72 and len(rain_masks)==42
 files={str(p.relative_to(content)):dict(sha256=sha256(p),bytes=p.stat().st_size) for p in sorted(content.rglob('*')) if p.is_file()}
 write_json(content/'MANIFEST.json',dict(files=files,excludes=['MANIFEST.json','MANIFEST.sha256'],protocol='Exact file set plus two manifest files; SHA-256 of every payload file'))
 hashes={name:row['sha256'] for name,row in files.items()};hashes['MANIFEST.json']=sha256(content/'MANIFEST.json')
 with (content/'MANIFEST.sha256').open('x') as f:
  for name,h in sorted(hashes.items()):f.write(h+'  '+name+'\n')
 archive=packroot/(run.name+'-light.tar.gz')
 with tarfile.open(str(archive),'x:gz',compresslevel=6) as tar:tar.add(str(content),arcname=run.name)
 digest=sha256(archive);side=Path(str(archive)+'.sha256');side.write_text(digest+'  '+archive.name+'\n')
 with tempfile.TemporaryDirectory(prefix='rain-handoff-unpack-',dir='/tmp') as temp:
  with tarfile.open(str(archive)) as tar:
   members=tar.getmembers();names=[m.name for m in members]
   assert len(names)==len(set(names))
   assert all(not m.name.startswith('/') and '..' not in Path(m.name).parts and (m.isdir() or m.isfile()) for m in members)
   assert all(Path(m.name).parts[0]==run.name for m in members)
   tar.extractall(temp)
  unpack=Path(temp)/run.name;actual={str(p.relative_to(unpack)) for p in unpack.rglob('*') if p.is_file()}
  assert actual==set(files)|{'MANIFEST.json','MANIFEST.sha256'}
  for name,h in hashes.items():assert sha256(unpack/name)==h,name
  assert sha256(unpack/'MANIFEST.sha256')==sha256(content/'MANIFEST.sha256')
 assert sha256(archive)==digest
 proof=dict(status='PASS',archive=str(archive),archive_sha256=digest,sha256_file=str(side),bytes=archive.stat().st_size,payload_files=len(files),safe_members=True,actual_unpack_verified=True,unpacked_file_set_exact=True,unpacked_all_SHA_match=True,raw_CS_sample_masks=72,raw_Rain_sample_masks=42,all_full_predictions_and_weights_remote=True)
 write_json(packroot/'handoff-verification.json',proof)
 completion=dict(status='complete',completed_at=now(),run=str(run),training_methods=3,steps_per_method=4000,new_evaluation_cells=22,new_images=7000,reused_cells=20,total_summary_cells=42,
  training_check_sha256=sha256(out/'training-independent-check.json'),protocol_check_sha256=sha256(out/'protocol-independent-check.json'),independent_prediction_check_sha256=sha256(out/'independent-final-check.json'),handoff=proof)
 write_json(run/'completion.json',completion)
 (run/'STATUS.md').write_text('# 当前状态\n\n'+now()+'：**complete**。三组Rain各4000步、22格新增完整评价7000逐图、旧20格核对复用、42格矩阵/逐类/阶段均值/差值、独立预测重读和训练/协议复核、图表、预先固定样例与轻量包安全解包/全文件SHA验证均完成。\n\n包：'+str(archive)+'\n\n外置SHA：'+str(side)+'\n\n实际退出码、来源及完成证据见events.jsonl、exit-code.txt、completion.json、results/*check.json、handoff/handoff-verification.json。权重/原始数据/全量预测留远端。包内STATUS保留打包前状态，最终完成由包外completion和解包核验记录证明，避免自引用哈希。未追加天气/种子/搜索/方法或重训旧阶段。\n')
 (prep/'STATUS.md').write_text('# 当前状态\n\n用户“继续提示词二”授权范围已全部完成，见`../'+run.name+'/completion.json`、STATUS.md与handoff/handoff-verification.json。三组各4000步、22格7000逐图、42格与独立复核/图表/固定样例及轻量包实际解包SHA均通过。PREPARED_PLAN/READY保留确认时不可变内容。\n')
 p=ROOT/'REPRO.md';s=p.read_text();a=s.index('<!-- ROAD_RAIN_CHAIN_CURRENT_BEGIN -->');b=s.index('<!-- ROAD_RAIN_CHAIN_CURRENT_END -->')+len('<!-- ROAD_RAIN_CHAIN_CURRENT_END -->')
 summary=read(out/'real-domain-stages.json')
 block=['<!-- ROAD_RAIN_CHAIN_CURRENT_BEGIN -->','## 当前道路工作：第3项真实三域链正式实验与轻量交接完成（2026-11-11）','',
  '- 用户“继续提示词二”授权的FT／原版GSMF／LwF-DIL，各自Fog学生→Rain4000步、22格7000次完整逐图、7000保存预测独立重读/GT直方图/协议核验、旧20格指纹核对复用、七checkpoint六条件42格/19类/阶段均值及差值、固定样例与图表、轻量包和实际解包全SHA核验全部完成。',
  '- 唯一正式目录：`'+str(run.relative_to(ROOT))+'`；实际流水线exit-code.txt=0，completion.json及handoff/handoff-verification.json均complete/PASS。详情见RESULTS.md/SUMMARY.md、results/*check.json与remote-index.json。',
  '- 固定seed0/batch2/crop512/FP32、AdamW1e-5/PolyLR4000，每1000验证/保存、主iter4000，无val择优，未重训Source/Fog。新优化器从0；12份周期checkpoint严格可读且优化器/调度器/iter完整。GSMF教师参数冻结、342个BN缓冲原训练态更新；LwF教师全部参数/缓冲固定于自己的Fog学生，学生浅层更新。推理全天气仅部署学生，参数/全部缓冲不变，无oracle/TTA/测试更新。',
  '- 最终Rain后CS/Fog/Rain及三真实域等权均值（%）：'+ '; '.join(m+' '+ '/'.join('%.4f'%summary[m][-1][k] for k in ('CS','Fog','Rain','seen_domain_equal_mean')) for m in METHODS)+'。各阶段已见域均值只含A、A/B、A/B/C；Source共享，未来Rain提前分数不纳入早期均值，合成四条件单列。',
  '- 交接包：`'+str(archive.relative_to(ROOT))+'`，外置同名.sha256，归档SHA `'+digest+'`。包内MANIFEST及安全成员/新目录实际解包/全文件集合与哈希一致；72份CS新原始样例、42份固定Rain样例及对齐图保留，权重/数据/全量预测留远端。',
  '- Rain官方train400/val100、A/B原清单与指纹保持。五个Rain共享视频目录披露，未独立证明地理/邻帧隔离；仅seed0，未主张统计显著、纯天气因果或严格未见强度泛化。LwF为未经搜索默认适配。无新增天气/种子/模块、下载、环境升级、checkpoint覆盖、Git提交或推送；当前授权任务已完成。更长序列仅作为后续考虑，未自动启动。',
  '<!-- ROAD_RAIN_CHAIN_CURRENT_END -->']
 p.write_text(s[:a]+'\n'.join(block)+s[b:])
 print(json.dumps(proof,indent=2,ensure_ascii=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--prepare',required=True);p.add_argument('--run',required=True);a=p.parse_args();main(a.prepare,a.run)
