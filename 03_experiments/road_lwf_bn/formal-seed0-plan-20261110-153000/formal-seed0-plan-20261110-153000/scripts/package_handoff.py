#!/usr/bin/env python
"""Create a light, independently unpack-verified prompt-two handoff; never copy weights/data/full predictions."""
import argparse,hashlib,json,os,shutil,subprocess,sys,tarfile,tempfile
from pathlib import Path
from datetime import datetime,timezone,timedelta
ROOT=Path('/home/ysheng4/research/GSMF-RS-DIL');sys.path.insert(0,str(ROOT))
from road_dil.protocol import sha256
PREP=ROOT/'experiments/road_lwf_bn/prepare-seed0-20261110-153000'
OLD=ROOT/'experiments/road_clear_to_fog/formal-seed0-20261108-resume01'
SEV=ROOT/'experiments/road_fog_severity/eval-final-seed0-20261109-182100'

def write(path,obj):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('x') as f:json.dump(obj,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def read(path):return json.loads(Path(path).read_text())
def copy(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
def main(run):
 run=Path(run).resolve();proof=read(run/'results/independent-final-check.json');assert proof['status']=='PASS' and proof['new_images']==4200
 assert read(run/'RESULTS_READY.json')['status']=='verified_results_complete'
 assert (run/'exit-code.txt').read_text().strip()=='0'
 costs=read(run/'results/resource-costs.json');summ=read(run/'results/five-model-summary.json')
 packroot=run/'handoff';packroot.mkdir(exist_ok=False);content=packroot/'content'/run.name;content.mkdir(parents=True)
 now=datetime.now(timezone(timedelta(hours=8))).isoformat()
 # Remote indices contain hashes and paths; all large weights/data/full predictions stay remote.
 weights={}
 for m in ('source','ft','gsmf','lwf','gsmf_teacher_bn'):
  p=(OLD if m in ('source','ft','gsmf') else run)/m/('iter_60000.pth' if m=='source' else 'iter_4000.pth')
  weights[m]=dict(path=str(p),sha256=sha256(p),bytes=p.stat().st_size)
 prediction_index=[]
 for check in proof['checks']:
  model,cond=check['model'],check['condition'];row=next(r for r in summ if r['model']==model and r['condition']==cond)
  prediction_index.append(dict(model=model,condition=cond,origin=check['origin'],directory=str(Path(row['source_directory'])/'predictions'),images=row['images'],checkpoint_sha256=row['checkpoint_sha256'],metrics_source=str(Path(row['source_directory'])/'independent-metrics.json'),prediction_hash_list=(str(run/'results/verification'/('%s_%s_predictions.json'%(model,cond))) if model in ('lwf','gsmf_teacher_bn') else None)))
 initializations={m:dict(path=str(PREP/'conversion'/(m+'_init.pth')),sha256=sha256(PREP/'conversion'/(m+'_init.pth'))) for m in ('lwf','gsmf_teacher_bn')}
 periodic=[dict(model=m,path=str(p),sha256=sha256(p),bytes=p.stat().st_size) for m in ('lwf','gsmf_teacher_bn') for p in sorted((run/m).glob('iter_*.pth'))]
 remote=dict(initializations=initializations,periodic_checkpoints=periodic,project=str(ROOT),run=str(run),preparation=str(PREP),weights=weights,predictions=prediction_index,data=dict(training_manifests=str(ROOT/'experiments/road_clear_to_fog/data'),paired_scene_ids=str(SEV/'prepared-20261110/scene_ids.json'),paired_data_audit=str(SEV/'data-audit-20261110/audit.json'),paired_data_records=str(SEV/'data-audit-20261110/available_manifest.csv')),environment_python='/home/ysheng4/miniconda3/envs/GSMF_RS_DIL/bin/python',excluded=['weights','raw datasets','full predictions','Conda environment','.git'])
 write(run/'remote-index.json',remote)
 # Mark computation complete separately from package verification, preserving live pipeline status.json.
 summary=['# 第2项seed0交接摘要','', '计算状态：两组各4000步、10个新增完整评价单元4200次逐图、独立矩阵/GT核验、五模型25条目汇总、逐类表/曲线/固定样例均完成。', '', '| 模型 | 晴天 | Foggy .005 | Foggy .01 | Foggy .02 | ACDC-fog |','|---|---:|---:|---:|---:|---:|']
 for model in ('source','ft','gsmf','lwf','gsmf_teacher_bn'):
  summary.append('| '+model+' | '+' | '.join('%.4f'%next(r['mIoU_percent'] for r in summ if r['model']==model and r['condition']==c) for c in ('clear','fog005','fog010','fog020','acdc'))+' |')
 summary+=['','旧15单元为核对checkpoint、场景/标签、预处理、滑窗、分支、指标来源后的复用，本轮没有重跑旧模型全量推理；新10单元明确标记new_inference_this_run。','', '固定iter4000；无best选择、追加seed、超参搜索或天气。每组仅B_train400监督增量；同一Source SHA '+weights['source']['sha256']+'。LwF输出蒸馏T2/0.5、全像素无T²；BN变体只调整教师BN源统计，教师Dropout/学生行为保留。','', '所有新增预测已独立重读原标签重算矩阵，行GT/列预测、ignore255、union0排除、仅有预测的类为0，GT直方图一致。两新组教师状态全部严格等于源值；评价前后所有参数和缓冲区不变，仅学生分支19通道推理。','', '原始新48份固定样例预测和六场景五模型同图对比已保留；没有增加按效果挑选的ACDC样例。完整19类结果见results/class-iou-wide.csv/JSON，强度绝对曲线及相对晴天下降曲线均有PNG/SVG/PDF。','', '单种子，真实/合成跨库差异，ACDC强度支持未知；不主张严格未见强度泛化、统计显著、LwF机制无效或BN因果解释。五条件不作简单平均。','', '恢复：保留完整optimizer/scheduler/iter；如未来中断恢复，不恢复RNG/采样游标，不承诺逐位一致。权重、数据、完整预测和环境均留远端。','', '源码恢复：以provenance记录的Git HEAD为基底，解开source/validated-training-source.tar.gz覆盖所列代码，并复用source/gsmf_rs_dil/__init__.py；preparation/validated-source.tar.gz另含准备版本完整源码/AGENTS/REPRO。source/git-diff.patch仅作审查，不作为新增文件的唯一恢复来源。','', '正式计算流水线exit-code.txt=0；最终交接校验见包外handoff-verification.json与外置.sha256。包内STATUS是打包时的计算完成状态，避免把包内后验验证写入其自身造成哈希循环。']
 (run/'SUMMARY.md').write_text('\n'.join(summary)+'\n')
 (PREP/'STATUS.md').write_text('# 当前状态\n\n已获提示词二授权，正式计算与独立核验已完成，轻量包生成/校验中。正式状态见 ../'+run.name+'/STATUS.md。准备PLAN.md和READY.json是确认时不可变方案/指纹快照。\n')
 (run/'STATUS.md').write_text('# 当前状态\n\n更新时间：'+now+'。**两组训练、10单元4200次完整评价、独立核验、五模型25条目/逐类/曲线/固定样例已完成；轻量包正在生成并待独立解包校验。**\n\n运行标识：'+run.name+'。真实训练/评价阶段退出码均0。results/independent-final-check.json为PASS；旧15单元复用明确标注。剩余仅交接包文件集合与哈希核验。\n')
 for name in ('PLAN.md','PREPARED_PLAN.md','STATUS.md','RESULTS.md','SUMMARY.md','authorization.json','provenance.json','events.jsonl','status.json','exit-code.txt','remote-index.json','RESULTS_READY.json','independent-finalize.log','postprocess-command.sh','monitor-last-check.txt','old-protocol-precheck.json','early-checkpoint-lwf-1000.json','timing-observations.json','validated-source.tar.gz'):
  if name=='validated-source.tar.gz':copy(run/name,content/'source/validated-training-source.tar.gz')
  else:copy(run/name,content/name)
 shutil.copytree(run/'results',content/'results')
 shutil.copytree(run/'scripts',content/'scripts',ignore=shutil.ignore_patterns('__pycache__'))
 # Exact training configurations, invocations, audit and raw train/eval logs.
 for name in ('train-lwf','train-gsmf_teacher_bn'):
  for suffix in ('.log','.exit','-command.sh'):copy(run/(name+suffix),content/'execution'/(name+suffix))
 for model in ('lwf','gsmf_teacher_bn'):
  d=run/model
  for p in d.rglob('*'):
   if p.is_file() and p.suffix in ('.py','.json','.log') and 'vis_data' not in p.parts:copy(p,content/'training'/model/p.relative_to(d))
 for d in sorted(run.glob('eval-*')):
  if not d.is_dir():continue
  for p in d.rglob('*'):
   if p.is_file() and p.suffix in ('.py','.json','.log') and 'predictions' not in p.parts and 'vis_data' not in p.parts:copy(p,content/'evaluation'/d.name/p.relative_to(d))
  for suffix in ('.log','.exit','-command.sh'):copy(run/(d.name+suffix),content/'execution'/(d.name+suffix))
 for name in ('READY.json','PLAN.md','STATUS.md','VALIDATION.md','IMPLEMENTATION.md','COMMANDS.md','validation-summary.json','controlled-real-check.json','controlled-input.json','strict-reload-evidence.json','conversion/conversion.json','config-diff.json','data-provenance.json','fixed-checkpoints.json','environment.json','preflight-check.log','preflight-check.exit','preparation-integrity.json','code-fingerprint.json','validated-source.tar.gz','validated-source.tar.gz.sha256','authorization.json','debug-budget.json','git-diff.patch'):
  copy(PREP/name,content/'preparation'/name)
 for p in PREP.glob('synthetic-loss-check*.json'):copy(p,content/'preparation'/p.name)
 for p in PREP.glob('*formal-resolved.py'):copy(p,content/'preparation'/p.name)
 copy(ROOT/'gsmf_rs_dil/__init__.py',content/'source/gsmf_rs_dil/__init__.py')
 copy(ROOT/'AGENTS.md',content/'source/AGENTS.md')
 copy(ROOT/'STEP2_LWF_BN_REMOTE_TASK_20261110.md',content/'source/STEP2_LWF_BN_REMOTE_TASK_20261110.md')
 with (content/'source/git-diff.patch').open('x') as f:subprocess.run(['git','diff','--binary'],cwd=ROOT,stdout=f,check=True)
 with (content/'source/git-status.txt').open('x') as f:subprocess.run(['git','status','--short'],cwd=ROOT,stdout=f,check=True)
 for name in ('conda-linux-64.explicit.txt','pip-linux-64.lock.txt'):copy(ROOT/'environment'/name,content/'environment'/name)
 copy(SEV/'prepared-20261110/sample_ids.json',content/'data-index/fixed-sample-ids.json')
 copy(SEV/'prepared-20261110/scene_ids.json',content/'data-index/paired-scene-ids.json')
 # Small manifest records contain only local path/encoding/ID provenance; no images or labels.
 for p in (ROOT/'experiments/road_clear_to_fog/data').glob('*.jsonl'):copy(p,content/'data-index/original-road-manifests'/p.name)
 for p in (PREP/'eval-manifests').rglob('*'):
  if p.is_file():copy(p,content/'data-index/evaluation-manifests'/p.relative_to(PREP/'eval-manifests'))
 copy(SEV/'evaluation-20261110/independent-final-check.json',content/'reused-source/old-severity-independent-check.json')
 copy(OLD/'final-independent-verification.json',content/'reused-source/old-two-domain-independent-check.json')
 # Explicit input- and source-provenance available without old large folders.
 forbidden=[p for p in content.rglob('*') if p.is_file() and p.suffix=='.pth'];assert not forbidden
 manifest={str(p.relative_to(content)):sha256(p) for p in sorted(content.rglob('*')) if p.is_file()}
 with (content/'MANIFEST.sha256').open('x') as f:
  for name,h in manifest.items():f.write(h+'  '+name+'\n')
 archive=packroot/(run.name+'-light.tar.gz')
 with tarfile.open(archive,'x:gz',compresslevel=6) as tar:tar.add(content,arcname=run.name)
 digest=sha256(archive);side=Path(str(archive)+'.sha256');side.write_text(digest+'  '+archive.name+'\n')
 # Independently extract to a fresh directory and verify exact file set and all hashes.
 with tempfile.TemporaryDirectory(prefix='road-lwf-bn-unpack-',dir='/tmp') as tmp:
  with tarfile.open(archive) as tar:
   for m in tar.getmembers():assert not m.name.startswith('/') and '..' not in Path(m.name).parts and not m.issym() and not m.islnk()
   tar.extractall(tmp)
  unpacked=Path(tmp)/run.name
  actual={str(p.relative_to(unpacked)) for p in unpacked.rglob('*') if p.is_file()}
  assert actual==set(manifest)|{'MANIFEST.sha256'}
  for name,h in manifest.items():assert sha256(unpacked/name)==h,name
  assert sha256(unpacked/'MANIFEST.sha256')==sha256(content/'MANIFEST.sha256')
 assert sha256(archive)==digest and side.read_text().split()[0]==digest
 verification=dict(status='PASS',archive=str(archive),archive_sha256=digest,sha256_file=str(side),bytes=archive.stat().st_size,manifest_files=len(manifest),unpacked_file_set_exact=True,unpacked_all_hashes_match=True,manifest_excludes_only_itself=True,no_checkpoints_or_raw_data=True,new_predictions_retained_in_package=48,all_full_predictions_remote=True)
 write(packroot/'handoff-verification.json',verification)
 write(run/'completion.json',dict(status='complete',completed_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),training_models=2,steps_per_model=4000,new_evaluation_cells=10,new_images=4200,reused_cells=15,total_summary_cells=25,handoff=verification))
 (run/'STATUS.md').write_text('# 当前状态\n\n更新时间：'+datetime.now(timezone(timedelta(hours=8))).isoformat()+'。**complete：两组各4000步、10个新增完整评价单元4200次逐图、独立矩阵/GT核验、五模型25条目/19类表、曲线、固定样例与轻量交接包全部完成。**\n\n交接包：'+str(archive)+'\n\n外置SHA：'+str(side)+'\n\n解包后的文件集合与全部哈希一致，见handoff/handoff-verification.json；真实训练/评价总退出码0。旧15单元复用明确标注，数据/权重/全量预测保留远端。无剩余任务；未追加seed/搜索/天气，不作统计显著/严格未见强度/BN因果主张。包内STATUS保留打包前的计算完成状态，最终校验由包外completion.json和handoff-verification.json证明。\n')
 (PREP/'STATUS.md').write_text('# 当前状态\n\n提示词二已全部完成；两组各4000步、10单元4200次完整评价、独立核验、25条目/19类表/曲线/固定样例/轻量包及解包哈希校验均通过。正式目录：`../'+run.name+'`，完成证据completion.json与handoff/handoff-verification.json。没有追加seed/搜索/天气；本目录PLAN/READY保留为确认时不可变快照。\n')
 p=ROOT/'REPRO.md';text=p.read_text();start=text.index('<!-- ROAD_LWF_BN_CURRENT_BEGIN -->');end=text.index('<!-- ROAD_LWF_BN_CURRENT_END -->')+len('<!-- ROAD_LWF_BN_CURRENT_END -->')
 block='''<!-- ROAD_LWF_BN_CURRENT_BEGIN -->
## 道路第2项：seed0正式实验与轻量交接全部完成（2026-11-10）

- 用户“继续提示词二”授权的两组LwF-DIL / teacher_bn_source_stats各4000步、10单元4200次完整逐图评价、独立预测重读/GT直方图核验、五模型25条目与19类表、曲线/固定6场景新48份原始预测、轻量包及解包哈希核验全部完成。
- 正式目录：`experiments/road_lwf_bn/formal-seed0-plan-20261110-153000`。结果与限制见RESULTS.md/SUMMARY.md，真实完成状态见completion.json、STATUS.md及handoff/handoff-verification.json；训练/评价流水线exit-code.txt=0。
- 两组均同一Source严格转换、全新AdamW，seed0/batch2/crop512/FP32、固定iter4000；教师全部状态等于Source，评价只学生分支、19通道、参数/缓冲不变。旧15单元按指纹/协议核对复用，不伪称本轮重新推理。
- 交接包和外置SHA在本正式目录handoff/，文件名为formal-seed0-plan-20261110-153000-light.tar.gz及同名.sha256，解包文件集合与MANIFEST全文件哈希一致。权重、数据、全量预测和环境均留远端，索引remote-index.json。
- 仅seed0；真实/合成跨库、ACDC强度支持未知，不主张统计显著、严格未见强度泛化或已证明BN因果解释；LwF为未搜索超参的默认适配对照，KD全像素无T²。未追加seed/搜索/天气，未重训旧组，无Git提交/推送。当前无剩余已授权任务；后续重复须另行明确授权。
<!-- ROAD_LWF_BN_CURRENT_END -->'''
 p.write_text(text[:start]+block+text[end:])
 print(json.dumps(verification,ensure_ascii=False,indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);main(p.parse_args().run)
