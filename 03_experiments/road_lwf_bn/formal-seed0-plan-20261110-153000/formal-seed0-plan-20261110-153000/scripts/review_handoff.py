#!/usr/bin/env python
"""Seal a wording-reviewed handoff; preserve first archive and all numerical results."""
import hashlib,json,shutil,tarfile,tempfile,sys
from pathlib import Path
from datetime import datetime,timezone,timedelta
ROOT=Path('/home/ysheng4/research/GSMF-RS-DIL');sys.path.insert(0,str(ROOT))
from road_dil.protocol import sha256
run=ROOT/'experiments/road_lwf_bn/formal-seed0-plan-20261110-153000'
old=run/'handoff';new=run/'handoff-reviewed';new.mkdir(exist_ok=False)
previous=json.loads((run/'completion.json').read_text())
assert previous['status']=='complete' and previous['handoff']['unpacked_all_hashes_match']
assert sha256(previous['handoff']['archive'])==previous['handoff']['archive_sha256']
content=new/'content'/run.name
shutil.copytree(old/'content'/run.name,content)
# Only descriptions and revision provenance change; every CSV, matrix, model and prediction stays identical.
shutil.copy2(run/'RESULTS.md',content/'RESULTS.md')
shutil.copy2(run/'scripts/finalize_results.py',content/'scripts/finalize_results.py')
shutil.copy2(Path(__file__),content/'scripts/review_handoff.py')
shutil.copy2(ROOT/'experiments/road_lwf_bn/prepare-seed0-20261110-153000/STATUS.md',content/'preparation/STATUS.md')
archive=new/(run.name+'-light.tar.gz');side=Path(str(archive)+'.sha256')
now=datetime.now(timezone(timedelta(hours=8))).isoformat()
status='# 当前状态\n\n更新时间：'+now+'。**complete：两组各4000步、10个新增完整评价单元4200次逐图、独立矩阵/GT核验、五模型25条目与19类表、曲线、固定样例及轻量交接均已完成。**\n\n本版仅修正“最大增加”包含负值时的措辞为“最高三项差值”，数值完全不变；初版归档保留。\n\n校阅版包：'+str(archive)+'\n\n外置SHA：'+str(side)+'\n\n最终文件集合/解包哈希证明见包外handoff-verification.json。权重、数据、全量预测和环境保留远端；未追加seed/搜索/天气。\n'
(content/'STATUS.md').write_text(status)
summary=(content/'SUMMARY.md').read_text()
summary=summary.replace('包内STATUS是打包时的计算完成状态，避免把包内后验验证写入其自身造成哈希循环。','包内STATUS记录已完成的计算/核验和归档校阅状态；最终归档SHA及独立解包证明在包外handoff-verification.json，MANIFEST覆盖包内除自身外全部文件。')
(content/'SUMMARY.md').write_text(summary)
review=dict(scope='Wording only: replace 最大增加 with 最高三项差值 where third-ranked delta can be negative. All numerical results/configurations/weights/predictions unchanged.',previous_archive=previous['handoff']['archive'],previous_archive_sha256=previous['handoff']['archive_sha256'],reviewed_at=now)
(content/'REPORT_REVIEW.json').write_text(json.dumps(review,indent=2,ensure_ascii=False)+'\n')
initial_files={str(p.relative_to(old/'content'/run.name)):sha256(p) for p in (old/'content'/run.name).rglob('*') if p.is_file()}
for p in (content/'results').rglob('*'):
 if p.is_file():assert sha256(p)==initial_files[str(p.relative_to(content))],str(p)
assert (content/'RESULTS.md').read_text().replace('最高三项差值：','最大增加：')==(old/'content'/run.name/'RESULTS.md').read_text()
# Manifest includes the review instructions and revised STATUS/RESULTS; excludes only itself.
manifest={str(p.relative_to(content)):sha256(p) for p in sorted(content.rglob('*')) if p.is_file() and p.name!='MANIFEST.sha256'}
(content/'MANIFEST.sha256').write_text(''.join(h+'  '+name+'\n' for name,h in manifest.items()))
with tarfile.open(archive,'x:gz',compresslevel=6) as tar:tar.add(content,arcname=run.name)
digest=sha256(archive);side.write_text(digest+'  '+archive.name+'\n')
with tempfile.TemporaryDirectory(prefix='road-lwf-bn-reviewed-unpack-',dir='/tmp') as tmp:
 with tarfile.open(archive) as tar:
  for m in tar.getmembers():assert not m.name.startswith('/') and '..' not in Path(m.name).parts and not m.issym() and not m.islnk()
  tar.extractall(tmp)
 unpacked=Path(tmp)/run.name
 actual={str(p.relative_to(unpacked)) for p in unpacked.rglob('*') if p.is_file()}
 assert actual==set(manifest)|{'MANIFEST.sha256'}
 for name,h in manifest.items():assert sha256(unpacked/name)==h,name
 assert sha256(unpacked/'MANIFEST.sha256')==sha256(content/'MANIFEST.sha256')
assert sha256(archive)==digest and side.read_text().split()[0]==digest
verification=dict(status='PASS',archive=str(archive),archive_sha256=digest,sha256_file=str(side),bytes=archive.stat().st_size,manifest_files=len(manifest),unpacked_file_set_exact=True,unpacked_all_hashes_match=True,manifest_excludes_only_itself=True,no_checkpoints_or_raw_data=True,new_predictions_retained_in_package=48,all_full_predictions_remote=True,numerical_results_identical_to_initial_archive=True,wording_review=review)
(new/'handoff-verification.json').write_text(json.dumps(verification,indent=2,ensure_ascii=False)+'\n')
(run/'completion-initial.json').write_text(json.dumps(previous,indent=2)+'\n')
previous['handoff']=verification;previous['review_completed_at']=datetime.now(timezone(timedelta(hours=8))).isoformat()
tmp=run/'completion-reviewed.tmp';tmp.write_text(json.dumps(previous,indent=2,ensure_ascii=False)+'\n');tmp.replace(run/'completion.json')
(run/'STATUS.md').write_text(status)
(run/'SUMMARY.md').write_text(summary)
(run/'REPORT_REVIEW.json').write_text(json.dumps(review,indent=2,ensure_ascii=False)+'\n')
p=ROOT/'REPRO.md';s=p.read_text().replace('交接包和外置SHA在本正式目录handoff/，','最终校阅交接包和外置SHA在本正式目录handoff-reviewed/（初版handoff/保留），').replace('及handoff/handoff-verification.json；','及handoff-reviewed/handoff-verification.json；');p.write_text(s)
print(json.dumps(verification,indent=2,ensure_ascii=False))
