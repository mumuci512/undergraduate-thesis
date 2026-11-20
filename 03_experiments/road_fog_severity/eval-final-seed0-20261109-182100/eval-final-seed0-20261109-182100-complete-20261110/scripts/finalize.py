#!/usr/bin/env python3
"""Independently verify completed results and build an internal lightweight handoff."""
import csv,datetime,hashlib,json,math,os,shutil,tarfile,tempfile,traceback
from pathlib import Path
from fractions import Fraction
ROOT=Path('/home/ysheng4/research/GSMF-RS-DIL');RUN=ROOT/'experiments/road_fog_severity/eval-final-seed0-20261109-182100'; OUT=RUN/'evaluation-20261110';RESULT=OUT/'results';EXPORT=ROOT/'handoff_exports/eval-final-seed0-20261109-182100-complete-20261110'
BETAS=('0','0.005','0.01','0.02');STAGES=('source','ft','gsmf')
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
 return h.hexdigest()
def load(p):return json.loads(p.read_text())
def now():return datetime.datetime.now().astimezone().isoformat(timespec='seconds')
def main():
 assert (RUN/'acquisition-20261110/driver.exit').read_text().strip()=='0', 'driver failed or not finished'
 assert len(list((OUT/'precheck').glob('*/*/cell-proof.json')))==12 and len(list((OUT/'full').glob('*/*/cell-proof.json')))==12
 summary=list(csv.DictReader((RESULT/'results.csv').open()));classes=list(csv.DictReader((RESULT/'class_iou_long.csv').open()));assert len(summary)==12 and len(classes)==228
 lookup={(r['model'],r['beta']):r for r in summary};cl={(r['model'],r['beta'],int(r['trainId'])):r for r in classes};checks=[]; indexes={}
 for model in STAGES:
  for beta in BETAS:
   d=OUT/'full'/model/beta;matrix=load(RESULT/'matrices'/('%s_beta_%s.json'%(model,beta)))['matrix'];ev=load(d/'evaluation.json');proof=load(d/'cell-proof.json')
   assert len(matrix)==19 and all(len(row)==19 for row in matrix); gt=[sum(row) for row in matrix];pred=[sum(row[j] for row in matrix) for j in range(19)];diag=[matrix[i][i] for i in range(19)];union=[gt[i]+pred[i]-diag[i] for i in range(19)]
   terms=[Fraction(diag[i],union[i]) for i in range(19) if union[i]];mean=float(sum(terms,Fraction())/len(terms)*100)
   assert math.isclose(mean,float(lookup[model,beta]['mIoU_percent']),abs_tol=1e-10)
   for i in range(19):
    r=cl[model,beta,i];assert [int(r[k]) for k in ('gt_pixels','pred_pixels','intersection','union')]==[gt[i],pred[i],diag[i],union[i]]
    assert (r['iou_percent']=='' if union[i]==0 else math.isclose(float(r['iou_percent']),100*diag[i]/union[i],abs_tol=1e-10))
   assert sum(gt)==load(d/'independent-metrics.json')['valid_pixels'];assert ev['evaluated_images']==500
   assert set(k for k in proof['files'] if k.startswith('predictions/'))==set(str(p.relative_to(d)) for p in (d/'predictions').glob('*.png'))
   indexes[model+'/'+beta]=dict(remote_directory=str(d/'predictions'),files={k:v for k,v in proof['files'].items() if k.startswith('predictions/')})
   checks.append(dict(model=model,beta=beta,images=500,valid_pixels=sum(gt),classes_in_mean=len(terms),mIoU_percent=mean,seconds=ev['seconds'],peak_allocated_MiB=ev['peak_allocated_MiB']))
 assert len(list((RESULT/'matrices').glob('*.json')))==12 and len(list((RESULT/'matrices').glob('*.csv')))==12
 assert len(list((RESULT/'samples').glob('*.png')))==6 and len(list((RESULT/'samples').rglob('beta_*.png')))==72
 assert (RESULT/'miou.png').is_file() and (RESULT/'miou.svg').is_file()
 (OUT/'independent-final-check.json').write_text(json.dumps(dict(status='PASS',timestamp=now(),matrix_direction='GT rows, prediction columns',checks=checks,notes='Fraction arithmetic independently recomputes IoU; prior evaluator independently reread each saved prediction/GT; aggregate independently checked each GT histogram.'),indent=2)+'\n')
 (OUT/'prediction-index.json').write_text(json.dumps(indexes,indent=2)+'\n')
 ref={'source':71.5087,'ft':54.2915,'gsmf':55.2078}
 lines=['# 固定模型的受控合成多雾强度稳健性评价','',f'完成时间：{now()}。固定最终模型、seed 0；Cityscapes fine val **500 个共同场景**，原始晴天及三档合成雾，所有指标由整个场景集合累计混淆矩阵计算。','', '| 模型 | β=0 | β=0.005 | β=0.01 | β=0.02 |','|---|---:|---:|---:|---:|']
 for m in STAGES:lines.append('| %s | %s |'%(m.upper(),' | '.join('%.4f%%'%float(lookup[m,b]['mIoU_percent']) for b in BETAS)))
 lines+=['','相对同模型晴天下降（百分点）：']
 for m in STAGES:lines.append('- %s：%s。'%(m.upper(),'，'.join('β=%s：%.4f pp'%(b,float(lookup[m,b]['drop_vs_clear_pp'])) for b in BETAS[1:])))
 lines+=['','GSMF 减 FT（百分点）：'+ '，'.join('β=%s：%+.4f'%(b,float(lookup['gsmf',b]['mIoU_percent'])-float(lookup['ft',b]['mIoU_percent'])) for b in BETAS)+'。','', '各模型 β=0.02 相对晴天变化最大的五个可比较类别（IoU百分点）：']
 for m in STAGES:
  delta=[]
  for i in range(19):
   a=cl[m,'0',i];b=cl[m,'0.02',i]
   if a['iou_percent'] and b['iou_percent']:delta.append((float(b['iou_percent'])-float(a['iou_percent']),a['classname']))
  delta.sort();lines.append('- '+m.upper()+'：'+'，'.join('%s %+.2f'%(name,value) for value,name in delta[:5])+'。')
 lines+=['','晴天一致性核查（本次减历史500张参考值，百分点）：'+ '，'.join('%s %+.5f'%(m.upper(),float(lookup[m,'0']['mIoU_percent'])-ref[m]) for m in STAGES)+'。']
 if any(abs(float(lookup[m,'0']['mIoU_percent'])-ref[m])>0.05 for m in STAGES):lines+=['**注意：晴天结果与历史参考相差超过 0.05 pp，需调查样本、权重、分支、映射和依赖。**']
 lines+=['','## 协议和限制','', '三个最终 checkpoint 的哈希、完整逐类表、GT行/预测列混淆矩阵、单元耗时和峰值显存见随包文件。图例样例由 seed 20261109 从完整共同场景推理前固定。GSMF 所有条件都走 backbone_1/decode_head_1。', '源训练清单与本次 val 无相同原帧或 sequence；ACDC 训练图像和本次晴天图像的已存文件/像素哈希无交集。跨数据集地理和邻近帧独立未证明，ACDC-fog训练强度支持未核实；不能宣称严格未见强度泛化、真实连续流适应或统计显著性。', '三个模型是一个 seed；没有本轮重新训练、TTA、调参或模型选择。', '原始图像和权重均远程保留，预测全量远程索引见 prediction-index.json。包中预览包含缩小的 Cityscapes/Foggy 数据画面，仅供数据许可持有人内部研究；原始图像没有单独打包，禁止将数据或修改版本再次分发，使用须符合随数据集提供的许可证。', 'ZIP 本地 SHA-256 为 08394f585ebe14017f05a7be93e9a237be868b544abf719a692aefae9383b2a1，val 图在提取时通过 ZIP 内CRC；本地 MD5 与用户提供的官方页面校验值 4166ad66c806459ef071d97b1a8c54b1 一致。', '所有包中绝对路径均指远程保留位置，论文项目目标为 03_experiments/road_fog_severity/eval-final-seed0-20261109-182100/。', '源码恢复 commit 315f273929c09ffa991a1f1d6f95e304641386ce；未提交脚本随包附带，环境与 SHA 证据见 evidence/。']
 (RUN/'SUMMARY.md').write_text('\n'.join(lines)+'\n')
 state=load(OUT/'status.json');state['state']='评价与独立复核完成，正在打包';state['updated']=now();(OUT/'status.json').write_text(json.dumps(state,indent=2,ensure_ascii=False)+'\n')
 (RUN/'STATUS.md').write_text('# 当前状态\n\n更新时间：'+now()+'。**12/12 全量单元及12/12 两场景预检完成，独立复核通过，正在生成并核验回传包。**\n\n逐单元日志、退出码、预测及状态：`evaluation-20261110/`；结果汇总：`SUMMARY.md`。\n')
 EXPORT.mkdir(parents=True,exist_ok=False)
 for name in ('SUMMARY.md','STATUS.md','PLAN.md'):shutil.copy2(RUN/name,EXPORT/name)
 (EXPORT/'STATUS.md').write_text('# 当前状态\n\n12/12 两场景预检及12/12 全量单元完成；指标已独立复核。该包应以外置 SHA-256 及包内 MANIFEST.sha256 校验。完整预测和权重远程保留。\n')
 for name in ('data-audit-20261110','prepared-20261110','scripts','evidence','acquisition-20261110'):
  shutil.copytree(RUN/name,EXPORT/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 shutil.copytree(RESULT,EXPORT/'results')
 for name in ('fingerprint.json','status.json','independent-final-check.json','prediction-index.json'):shutil.copy2(OUT/name,EXPORT/name)
 shutil.copytree(OUT/'logs',EXPORT/'logs')
 for phase in ('precheck','full'):
  for model in STAGES:
   for beta in BETAS:
    src=OUT/phase/model/beta;dest=EXPORT/'cells'/phase/model/beta;dest.mkdir(parents=True)
    for name in ('evaluation.json','independent-metrics.json','reloaded-prediction-metrics.json','cell-proof.json','exit-code.txt'):shutil.copy2(src/name,dest/name)
 files=sorted(p for p in EXPORT.rglob('*') if p.is_file()); manifest=EXPORT/'MANIFEST.sha256';manifest.write_text(''.join(sha(p)+'  ./'+str(p.relative_to(EXPORT))+'\n' for p in files))
 archive=EXPORT.parent/(EXPORT.name+'.tar.gz');checksum=EXPORT.parent/(archive.name+'.sha256')
 with tarfile.open(archive,'w:gz') as tf:tf.add(EXPORT,arcname=EXPORT.name)
 checksum.write_text(sha(archive)+'  '+archive.name+'\n')
 with tempfile.TemporaryDirectory(prefix='road-fog-unpack-',dir='/tmp') as temp:
  with tarfile.open(archive,'r:gz') as tf:tf.extractall(path=temp)
  unpack=Path(temp)/EXPORT.name; lines=(unpack/'MANIFEST.sha256').read_text().splitlines()
  names=set()
  for line in lines:
   expected,name=line.split('  ',1);path=unpack/name;assert sha(path)==expected;names.add(path.relative_to(unpack).as_posix())
  assert names==set(p.relative_to(unpack).as_posix() for p in unpack.rglob('*') if p.is_file() and p.name!='MANIFEST.sha256')
 report=dict(status='PASS',timestamp=now(),archive=str(archive),archive_sha256=sha(archive),sha256_file=str(checksum),manifest_file_count=len(files),archive_bytes=archive.stat().st_size,unpacked_file_set_and_hashes_verified=True)
 (OUT/'handoff-verification.json').write_text(json.dumps(report,indent=2)+'\n')
 (RUN/'STATUS.md').write_text('# 当前状态\n\n更新时间：'+now()+'。**12/12 全量单元、12/12 两场景预检、独立复核和回传包校验全部完成。**\n\n详情见 `SUMMARY.md`、`evaluation-20261110/independent-final-check.json` 和 `evaluation-20261110/handoff-verification.json`。完整预测远程保留，索引见 `evaluation-20261110/prediction-index.json`。\n')
 repro=ROOT/'REPRO.md';s=repro.read_text();a=s.index('<!-- ROAD_FOG_SEVERITY_CURRENT_BEGIN -->');b=s.index('<!-- ROAD_FOG_SEVERITY_CURRENT_END -->',a)+len('<!-- ROAD_FOG_SEVERITY_CURRENT_END -->')
 section='<!-- ROAD_FOG_SEVERITY_CURRENT_BEGIN -->\n## 固定模型的受控合成多雾强度评价：完成（2026-11-10）\n\n500个共同 Cityscapes fine val 场景，晴天与三档合成雾，预检和12/12正式单元、矩阵独立复核、图表及回传包核验通过。完整证据、结果和约束见 `experiments/road_fog_severity/eval-final-seed0-20261109-182100/SUMMARY.md`，预测远程保留。ZIP val 图通过内部CRC，ZIP MD5 与用户提供的官方值一致。训练清单的原帧/记录与哈希检查未见重叠，跨数据集地理或邻近帧独立未证明。\n<!-- ROAD_FOG_SEVERITY_CURRENT_END -->'
 repro.write_text(s[:a]+section+s[b:]);print(json.dumps(report,indent=2))
if __name__=='__main__':
 try:main()
 except BaseException:
  traceback.print_exc();raise
