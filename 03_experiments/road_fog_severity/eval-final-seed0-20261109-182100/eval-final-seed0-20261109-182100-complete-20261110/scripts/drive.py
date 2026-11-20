#!/usr/bin/env python3
"""Sequential two-scene precheck and full fixed-model evaluations; verified cell resume."""
import datetime,hashlib,json,os,shutil,subprocess,sys,time,traceback
from pathlib import Path
ROOT=Path('/home/ysheng4/research/GSMF-RS-DIL')
RUN=ROOT/'experiments/road_fog_severity/eval-final-seed0-20261109-182100'
PYTHON='/home/ysheng4/miniconda3/envs/GSMF_RS_DIL/bin/python'
TRAINED=ROOT/'experiments/road_clear_to_fog/formal-seed0-20261108-resume01'
PREP=RUN/'prepared-20261110'; AUDIT=RUN/'data-audit-20261110'; OUT=RUN/'evaluation-20261110'
BETAS=('0','0.005','0.01','0.02'); STAGES=('source','ft','gsmf')
CHECKPOINTS={'source':('source/iter_60000.pth','a66c958ee774d27566b901ad6570c0a3b83263e9d74389e1c2e025c6c2673d93'),'ft':('ft/iter_4000.pth','99914df527d8506c33178ef6ea1caf7f0ed1d07369858e37275205d60a57d516'),'gsmf':('gsmf/iter_4000.pth','fc227c57dc3e47a134ef51b282964654a0210f3c06f00bd0d3e81b706850b24a')}
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def dump(path,obj):
 tmp=path.with_name(path.name+'.tmp');tmp.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n');os.replace(str(tmp),str(path))
def stamp():return datetime.datetime.now().astimezone().isoformat(timespec='seconds')
def status(state,phase='',stage='',beta='',completed=None,detail=''):
 data=dict(updated=stamp(),state=state,phase=phase,model=stage,beta=beta,completed=completed or [],pid=os.getpid(),detail=detail,session='road-fog-severity-20261110',output=str(OUT))
 dump(OUT/'status.json',data)
 lines=['# 当前状态','',f'更新时间：{data["updated"]}。状态：**{state}**；会话 `{data["session"]}`，控制 PID {data["pid"]}。',f'当前单元：{phase} {stage} β={beta}。{detail}',f'完整正式单元：{len([x for x in data["completed"] if x.startswith("full/")])}/12。','',f'已完成：{", ".join(data["completed"]) or "无"}。','', '数据：Cityscapes fine val 500 场景，四条件 2000 输入，原标签 labelIds 映射一次；全量固定同一组。', '预检：必须先完成全部 12 个模型×条件的两场景检查，之后才进入全量。', '当前输出及日志：`evaluation-20261110/`；失败单元保留，恢复时只有经哈希和配置核对的成功单元才跳过。', 'ZIP 内 1500 个 val PNG CRC 已验证；官方独立 MD5 尚未提供，归档本地哈希见 `acquisition-20261110/archive-hashes.txt`。', '隔离检查仅证明清单中原帧、记录及图像哈希关系；跨数据集地理、近邻帧独立未证明。']
 (RUN/'STATUS.md').write_text('\n'.join(lines)+'\n')
def snapshot():
 # Existing committed code hashes were captured on 2026-11-09 at the training recovery HEAD.
 lines=(RUN/'evidence/code-sha256.txt').read_text().splitlines()
 for line in lines:
  expected,name=line.split('  ',1)
  if sha(ROOT/name)!=expected:raise ValueError('repository code differs from recorded hash: '+name)
 result={'code_manifest_sha256':sha(RUN/'evidence/code-sha256.txt'),'data_manifest_sha256':sha(AUDIT/'available_manifest.csv'),'audit_sha256':sha(AUDIT/'audit.json'),'scenes_sha256':sha(PREP/'scene_ids.json'),'samples_sha256':sha(PREP/'sample_ids.json'),'scripts':{},'prepared_manifests':{},'checkpoints':{}}
 for name in ('drive.py','aggregate.py','verify_inputs.py'):
  result['scripts'][name]=sha(RUN/'scripts'/name)
 for phase in ('precheck','full'):
  for beta in BETAS:
   for name in ('A_val_debug.jsonl','audit.json'):
    p=PREP/phase/beta/name;result['prepared_manifests'][str(p.relative_to(PREP))]=sha(p)
 for stage,(rel,expected) in CHECKPOINTS.items():
  h=sha(TRAINED/rel)
  if h!=expected:raise ValueError('checkpoint hash mismatch: '+stage)
  result['checkpoints'][stage]=h
 return result
def verify_cell(d,stage,phase,beta,signature,n):
 proof=json.loads((d/'cell-proof.json').read_text())
 if proof['signature']!=signature or proof['stage']!=stage or proof['phase']!=phase or proof['beta']!=beta:raise ValueError('cell provenance mismatch '+str(d))
 if (d/'exit-code.txt').read_text().strip()!='0':raise ValueError('cell exit nonzero')
 ev=json.loads((d/'evaluation.json').read_text());met=json.loads((d/'independent-metrics.json').read_text());again=json.loads((d/'reloaded-prediction-metrics.json').read_text())
 if ev['checkpoint_sha256']!=CHECKPOINTS[stage][1] or ev['evaluated_images']!=n or not ev['state_unchanged']:raise ValueError('evaluation proof mismatch')
 if met['confusion_matrix']!=again['confusion_matrix']:raise ValueError('matrix reload mismatch')
 if any(s[0]!=19 for s in met['actual_logit_shapes']) or not met['actual_logit_shapes']:raise ValueError('bad logit shape')
 calls=ev['forward_calls']
 if stage=='gsmf':
  if calls['backbone']!=0 or calls['decode_head.conv_seg']!=0 or calls['backbone_1']<=0 or calls['decode_head_1.conv_seg']<=0:raise ValueError('GSMF branch mismatch')
 elif calls['backbone']<=0 or calls['decode_head.conv_seg']<=0:raise ValueError('deployment branch mismatch')
 paths=list((d/'predictions').glob('*.png'))
 if len(paths)!=n:raise ValueError('unexpected prediction count')
 for name,expected in proof['files'].items():
  if sha(d/name)!=expected:raise ValueError('completed artifact changed '+str(d/name))
 if len(proof['files'])!=n+4:raise ValueError('incomplete proof')
def main():
 OUT.mkdir(exist_ok=True);(OUT/'logs').mkdir(exist_ok=True);done=[]
 status('准备中',detail='校验代码、输入和检查点哈希。')
 subprocess.run([PYTHON,'-c','import torch; assert torch.cuda.is_available(), "CUDA unavailable"'],check=True)
 subprocess.run([PYTHON,str(RUN/'scripts/verify_inputs.py'),str(PREP),str(AUDIT)],check=True)
 snap=snapshot(); signature=hashlib.sha256(json.dumps(snap,sort_keys=True).encode()).hexdigest(); fp=OUT/'fingerprint.json'
 if fp.exists():
  if json.loads(fp.read_text())['snapshot']!=snap:raise ValueError('configuration changed; refuse resume')
 else:dump(fp,dict(signature=signature,snapshot=snap))
 for phase in ('precheck','full'):
  for stage in STAGES:
   for beta in BETAS:
    label='/'.join((phase,stage,beta));d=OUT/label;n=2 if phase=='precheck' else 500
    if (d/'cell-proof.json').exists():
     verify_cell(d,stage,phase,beta,signature,n);done.append(label);status('运行中',phase,stage,beta,done,'已校验并复用完整单元。');continue
    if d.exists():
     failed=OUT/'failed-attempts';failed.mkdir(exist_ok=True)
     target=failed/(phase+'-'+stage+'-'+beta+'-'+str(time.time_ns()));shutil.move(str(d),str(target))
    d.parent.mkdir(parents=True,exist_ok=True)
    log=OUT/'logs'/(phase+'-'+stage+'-'+beta+'-'+str(time.time_ns())+'.log')
    cmd=[PYTHON,str(ROOT/'tools/road/run.py'),'eval','--stage',stage,'--domain','A','--checkpoint',str(TRAINED/CHECKPOINTS[stage][0]),'--manifests',str(PREP/phase/beta),'--work-dir',str(d),'--debug']
    status('运行中',phase,stage,beta,done,'正在执行；实时日志：'+str(log))
    with log.open('w') as f:
     f.write('COMMAND '+json.dumps(cmd)+'\n');f.flush();rc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,cwd=str(ROOT)).returncode
    (OUT/'logs'/(phase+'-'+stage+'-'+beta+'.exit')).write_text(str(rc)+'\n')
    if rc:raise RuntimeError('evaluation failed: '+label+' log '+str(log))
    (d/'exit-code.txt').write_text('0\n')
    artifacts=['evaluation.json','independent-metrics.json','reloaded-prediction-metrics.json','exit-code.txt']+[str(p.relative_to(d)) for p in sorted((d/'predictions').glob('*.png'))]
    dump(d/'cell-proof.json',dict(signature=signature,stage=stage,phase=phase,beta=beta,files={name:sha(d/name) for name in artifacts}))
    verify_cell(d,stage,phase,beta,signature,n);done.append(label);status('运行中',phase,stage,beta,done,'单元完成并核验。')
 status('汇总中',completed=done,detail='从保存矩阵重算指标并生成表格与样例图。')
 if not (OUT/'results').exists():subprocess.run([PYTHON,str(RUN/'scripts/aggregate.py'),'--prepared',str(PREP),'--audit',str(AUDIT),'--runs',str(OUT/'full'),'--out',str(OUT/'results')],check=True)
 status('推理完成，待最终独立复核与打包',completed=done)
if __name__=='__main__':
 try:main()
 except BaseException as e:
  traceback.print_exc()
  try:
   old=json.loads((OUT/'status.json').read_text());status('失败',old.get('phase',''),old.get('model',''),old.get('beta',''),old.get('completed',[]),repr(e))
  except Exception:pass
  sys.exit(1)
