#!/usr/bin/env python
"""Stage-A explicit light allowlist and actual safe-unpack/SHA verification; no next phase."""
import argparse,hashlib,json,os,shutil,subprocess,sys,tarfile,tempfile
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone,timedelta
ROOT=Path('/home/ysheng4/research/GSMF-RS-DIL');sys.path.insert(0,str(ROOT))
from road_dil.protocol import sha256,write_json

def read(p):return json.loads(Path(p).read_text())
def now():return datetime.now(timezone(timedelta(hours=8))).isoformat()
def copy(src,dst):
 src=Path(src);dst=Path(dst);assert src.is_file(),src;assert not dst.exists(),dst;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(str(src),str(dst))
def main(prep,run):
 prep=Path(prep).resolve();run=Path(run).resolve();out=Path(read(run/'results-index.json')['directory']);training=read(out/'training-independent-check.json');protocol=read(out/'protocol-independent-check.json');samples=read(out/'fixed-sample-selection-and-index.json');assert training['status']==protocol['status']==samples['status']=='PASS';assert (run/'exit-code.txt').read_text().strip()=='0';assert read(run/'RESULTS_READY.json')['new_cells']==62
 code=read(prep/'READY.json')['code']['files']
 with tarfile.open(str(run/'validated-source.tar.gz')) as tar:
  members=tar.getmembers();assert {m.name for m in members}==set(code) and all(m.isfile() for m in members)
  for member in members:
   stream=tar.extractfile(member);digest=hashlib.sha256()
   for block in iter(lambda:stream.read(8*1024*1024),b''):digest.update(block)
   assert digest.hexdigest()==code[member.name],member.name
 write_json(run/'formal-source-snapshot-verification.json',dict(status='PASS',files=len(code),all_member_content_SHA_equal_prepared_code=True,archive_sha256=sha256(run/'validated-source.tar.gz')))
 cells=read(out/'cells.json');weights={}
 for c in cells:
  path=Path(c['checkpoint']);weights[str(path)]=dict(path=str(path),sha256=c['checkpoint_sha256'],bytes=path.stat().st_size)
 assert len(weights)==13
 predictions=[dict(model=c['model'],condition=c['condition'],provenance=c['provenance'],images=c['images'],directory=str(Path(c['evidence'])/'predictions'),evaluation=str(Path(c['evidence'])/'evaluation.json'),checkpoint_sha256=c['checkpoint_sha256'],independent_index=str(out/'verification'/(c['model']+'-'+c['condition']+'.json')) if c['provenance']=='new' else None) for c in cells]
 remote=dict(project=str(ROOT),preparation=str(prep),run=str(run),results=str(out),weights=weights,periodic_checkpoints=training['periodic_checkpoints'],predictions=predictions,initializations={k:dict(path=v['initialization'],sha256=v['initialization_sha256'],parent=v['parent'],parent_sha256=v['parent_sha256']) for k,v in training['runs'].items()},data_audit=str(prep/'data/audit.json'),excludes=['weights','raw images/labels/archives','full predictions','Conda environment','.git','cookies/authentication files'])
 write_json(run/'remote-index.json',remote);(run/'STATUS.md').write_text('# 当前状态\n\n'+now()+'：阶段A六次4000步、62新格15878逐图、42复用格、104格汇总和训练/协议/指标独立核验、固定样例及图表通过。正在打包并核对实际解包SHA，核验完成前不标complete。阶段B暂缓、C未授权。\n')
 pack=run/'handoff';pack.mkdir(exist_ok=False);content=pack/'content'/run.name;content.mkdir(parents=True)
 for p in run.iterdir():
  if p.is_file() and p.suffix in ('.json','.md','.log','.sh','.txt'):copy(p,content/'execution'/p.name)
 for name in ('PLAN.md','PREPARED_PLAN.md','STATUS.md','RESULTS.md','SUMMARY.md','remote-index.json','authorization-A.json','provenance.json','exit-code.txt','results-index.json'):copy(run/name,content/name)
 shutil.copytree(run/'scripts',content/'scripts',ignore=shutil.ignore_patterns('__pycache__'));shutil.copytree(out,content/'results')
 for p in run.iterdir():
  if p.is_dir() and p.name in training['runs']:
   for f in p.rglob('*'):
    if f.is_file() and f.suffix in ('.json','.py','.log','.txt') and 'vis_data' not in f.parts:copy(f,content/'training'/p.name/f.relative_to(p))
 for p in (run/'initialization').rglob('*.json'):copy(p,content/'initializations'/p.relative_to(run/'initialization'))
 for c in cells:
  directory=Path(c['evidence']);name=c['model']+'-'+c['condition']
  for p in directory.iterdir():
   if p.is_file() and p.suffix in ('.json','.py','.txt'):copy(p,content/'evaluation'/name/p.name)
  if c['provenance']=='new':
   for p in directory.rglob('*.log'):
    if 'vis_data' not in p.parts:copy(p,content/'evaluation'/name/p.relative_to(directory))
 # Preparatory evidence is copied, never modified; it remains the authorized immutable baseline.
 for p in prep.iterdir():
  if p.is_file() and p.suffix in ('.json','.md','.log','.sh','.py','.txt','.patch') and not p.name.endswith('.tmp'):copy(p,content/'preparation'/p.name)
 for folder in ('data','configs','eval-manifests'):
  for p in (prep/folder).rglob('*'):
   if p.is_file() and p.suffix in ('.json','.jsonl','.py'):copy(p,content/'data-and-config-index'/folder/p.relative_to(prep/folder))
 for p in (prep/'conversion').rglob('*.json'):copy(p,content/'preparation/conversions'/p.relative_to(prep/'conversion'))
 for d,v in read(prep/'data/audit.json')['archive_provenance'].items():copy(v['path'],content/'data-and-config-index'/(d+'-archive-provenance.json'))
 for src,h in read(prep/'ancestors.json')['old_provenance_files'].items():
  assert sha256(src)==h;copy(src,content/'reused-provenance'/Path(src).relative_to(ROOT))
 inherited=read(prep/'data/audit.json')['inherited_ABC_audit'];copy(inherited,content/'reused-provenance/ABC-data-audit.json')
 for name in ('AGENTS.md','REPRO.md','STEP5_FIVE_DOMAIN_SEEDS_REMOTE_TASK_20261111.md'):copy(ROOT/name,content/'source'/name)
 for name in ('conda-linux-64.explicit.txt','pip-linux-64.lock.txt'):copy(ROOT/'environment'/name,content/'environment'/name)
 copy(prep/'validated-source.tar.gz',content/'source/prepared-verified-source.tar.gz');copy(run/'validated-source.tar.gz',content/'source/formal-training-source.tar.gz');copy(prep/'code-fingerprint.json',content/'source/code-fingerprint.json')
 with (content/'source/git-diff-final.patch').open('x') as f:subprocess.run(['git','diff','--binary'],cwd=ROOT,stdout=f,check=True)
 with (content/'source/git-status-final.txt').open('x') as f:subprocess.run(['git','status','--short'],cwd=ROOT,stdout=f,check=True)
 (content/'HANDOFF_README.md').write_text('# 交接核验说明\n\n所有训练、完整评价、独立指标与协议复核、样例和图表在归档前已通过。包内STATUS在最终归档校验前冻结，故仍写待打包核验；最终完成以远端包外completion.json、handoff/handoff-verification.json及同名外置SHA为准。这样避免归档SHA自引用。接收后仍应先检查归档SHA、安全成员路径，再在新目录实际解包并核对MANIFEST.sha256及文件集合。权重、原图、全量预测留远端，见remote-index.json。阶段B暂缓，C未授权。\n')
 assert not list(content.rglob('*.pth')) and len(list((content/'results/fixed-samples').rglob('*.png')))==192
 files={str(p.relative_to(content)):dict(sha256=sha256(p),bytes=p.stat().st_size) for p in sorted(content.rglob('*')) if p.is_file()};write_json(content/'MANIFEST.json',dict(files=files,manifest_self_exclusion=True));hashes={k:v['sha256'] for k,v in files.items()};hashes['MANIFEST.json']=sha256(content/'MANIFEST.json')
 with (content/'MANIFEST.sha256').open('x') as f:
  for name,h in sorted(hashes.items()):f.write(h+'  '+name+'\n')
 archive=pack/(run.name+'-light.tar.gz')
 with tarfile.open(str(archive),'x:gz',compresslevel=6) as tar:tar.add(str(content),arcname=run.name)
 digest=sha256(archive);side=Path(str(archive)+'.sha256');side.write_text(digest+'  '+archive.name+'\n')
 with tempfile.TemporaryDirectory(prefix='five-A-handoff-verify-',dir='/tmp') as temp:
  with tarfile.open(str(archive)) as tar:
   members=tar.getmembers();names=[m.name for m in members];assert len(names)==len(set(names))
   for m in members:
    path=PurePosixPath(m.name);assert not path.is_absolute() and '..' not in path.parts and path.parts[0]==run.name and (m.isdir() or m.isfile())
   tar.extractall(temp)
  unpack=Path(temp)/run.name;actual={str(p.relative_to(unpack)) for p in unpack.rglob('*') if p.is_file()};assert actual==set(files)|{'MANIFEST.json','MANIFEST.sha256'}
  for name,h in hashes.items():assert sha256(unpack/name)==h,name
  assert sha256(unpack/'MANIFEST.sha256')==sha256(content/'MANIFEST.sha256')
 assert sha256(archive)==digest
 proof=dict(status='PASS',archive=str(archive),archive_sha256=digest,sha256_file=str(side),bytes=archive.stat().st_size,payload_files=len(files),safe_members=True,actual_safe_unpack=True,exact_unpacked_file_set=True,all_unpacked_SHA_match=True,raw_CS_samples=36,raw_DE_samples=156,aligned_figures=18,weights_and_full_predictions_remote=True);write_json(pack/'handoff-verification.json',proof)
 completion=dict(status='complete',phase='A',completed_at=now(),training_runs=6,steps_per_run=4000,periodic_checkpoints=24,new_cells=62,new_images=15878,reused_cells=42,total_cells=104,training_check_sha256=sha256(out/'training-independent-check.json'),protocol_check_sha256=sha256(out/'protocol-independent-check.json'),independent_result_check_sha256=sha256(out/'verification.json'),handoff=proof,next_phase='B deferred by latest user instruction; C not authorized');write_json(run/'completion.json',completion)
 (run/'STATUS.md').write_text('# 当前状态\n\n'+now()+'：**complete**。阶段A六次4000步、24份完整周期checkpoint、62新格15878逐图与42旧格复用共104格，独立预测重读/GT直方图/训练策略核验、图表/固定样例及轻量包实际安全解包/文件集合/全SHA核验全部通过。\n\n包：'+str(archive)+'\n外置SHA：'+str(side)+'\n\n包内STATUS保留打包前状态，包外completion.json和handoff/handoff-verification.json为最终完成证据，避免自引用。权重/数据/全量预测留远程。阶段B暂缓，阶段C未授权。\n')
 p=ROOT/'REPRO.md';text=p.read_text();a=text.index('<!-- ROAD_FIVE_DOMAIN_CURRENT_BEGIN -->');b=text.index('<!-- ROAD_FIVE_DOMAIN_CURRENT_END -->')+len('<!-- ROAD_FIVE_DOMAIN_CURRENT_END -->');stages=read(out/'stage-matrices.json');finals='; '.join(m+' '+ '/'.join('%.4f'%stages[m+'-seed0-ABCDE'][-1]['values'][d] for d in ('clear','fog','rain','snow','night')) for m in ('ft','gsmf','lwf'))
 block='''<!-- ROAD_FIVE_DOMAIN_CURRENT_BEGIN -->
## 当前道路工作：第5项阶段A正式实验及轻量交接完成（2026-11-11）

- 最新用户范围“暂时先完成阶段A”。阶段A全部完成；B暂缓，C未授权，不自动启动。
- 正式目录：`'''+str(run.relative_to(ROOT))+'''`；六次各4000步、24份完整周期checkpoint、62新增评价格15878逐图与42旧格指纹复用共104格、独立预测重读/GT直方图/训练与协议复核、图表/预固定样例及轻量包安全解包/全SHA全部通过。实际exit-code.txt=0，completion.json与handoff/handoff-verification.json complete/PASS。
- 三方法seed0分别自己的Rain学生→Snow→Night，batch2/crop512/FP32、AdamW1e-5/PolyLR4000，每1000验证/保存，固定iter4000，无val择优。教师/学生完整参数与BN缓冲逐阶段严格继承；GSMF教师参数冻结/训练态BN更新、LwF教师全部状态固定。所有条件仅当前学生推理，参数/缓冲不变，无oracle/TTA/测试更新。
- 最终Night后CS/Fog/Rain/Snow/Night（%）：'''+finals+'''。阶段已见域均值只含已学域，未来域提前分数不计入；最终五真实域均值与合成条件单列。具体变化/负遗忘/混淆去向见RESULTS.md与results-index.json所指目录。
- 包：`'''+str(archive.relative_to(ROOT))+'''`，外置同名.sha256，SHA `'''+digest+'''`。权重/原图/全量预测留远程。包内预完成STATUS与包外最终完成证据分开，避免自引用。
- Snow400/100、Night400/106，A/B/C原清单保持。官方共享视频目录已披露，未独立证明地理/邻帧隔离；仅seed0、不主张稳定显著/纯天气因果/严格未见强度泛化。LwF未搜索超参；CUDA反向非逐位确定，resume不保证RNG/采样游标精确恢复。未重训Source/Fog/Rain seed0、未删除/覆盖旧数据checkpoint、未升级环境或Git提交/推送。
<!-- ROAD_FIVE_DOMAIN_CURRENT_END -->'''
 p.write_text(text[:a]+block+text[b:])
 copy(run/'status.json',run/'driver-status-final.json')
 state=dict(time_utc=datetime.now(timezone.utc).isoformat(),phase='A',state='complete',actor='verified_package',actor_pid=os.getpid(),exit_code=0,archive=str(archive),archive_sha256=digest,next_phase='B deferred; C not authorized')
 with (run/'events.jsonl').open('a') as f:f.write(json.dumps(state)+'\n')
 temp=run/'status-complete.tmp';temp.write_text(json.dumps(state,indent=2)+'\n');temp.replace(run/'status.json')
 print(json.dumps(proof,ensure_ascii=False,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--prepare',required=True);p.add_argument('--run',required=True);a=p.parse_args();main(a.prepare,a.run)
