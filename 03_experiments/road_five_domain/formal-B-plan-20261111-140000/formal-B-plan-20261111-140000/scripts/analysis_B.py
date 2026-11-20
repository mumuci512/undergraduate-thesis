"""Three paired incremental seeds, sparse synthetic conditions, and descriptive confusion tracking."""
import csv,json
from pathlib import Path
import numpy as np
from road_dil.protocol import CLASSES,sha256,write_json
from tools.road.five_common import REAL

def read(p):return json.loads(Path(p).read_text())
def csvsave(p,rows):
 with Path(p).open('x',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def stat(values):
 return dict(per_seed=[float(x) for x in values],mean=float(np.mean(values)),sample_std=float(np.std(values,ddof=1)))
def normalize_source(prep,run):
 """Make inherited Source provenance explicit; preserve all original driver results."""
 idx=read(run/'results-index.json');out=Path(idx['directory']);cells=read(out/'cells.json')
 assert sha256(out/'cells.json')==idx['cells_sha256']
 a=Path(read(prep/'formal-plans.json')['A']['formal_output']);comp=read(a/'completion.json');ai=read(a/'results-index.json');ao=Path(ai['directory'])
 assert comp['status']=='complete' and comp['handoff']['status']=='PASS'
 assert sha256(ao/'cells.json')==ai['cells_sha256'] and sha256(ao/'training-independent-check.json')==comp['training_check_sha256'] and sha256(ao/'protocol-independent-check.json')==comp['protocol_check_sha256']
 acells=read(ao/'cells.json');ref={c['condition']:c for c in acells if c['model']=='source'}
 write_json(run/'driver-original-results-index.json',idx)
 write_json(out/'driver-original-cells.json',cells)
 inherited=[]
 for c in cells:
  if c['model']!='source':continue
  assert c==ref[c['condition']]
  c['inherited_provenance']=c['provenance'];c['provenance']='reused'
  c['reuse_origin']=dict(phase='A',cells=str(ao/'cells.json'),cells_sha256=ai['cells_sha256'],completion=str(a/'completion.json'),completion_sha256=sha256(a/'completion.json'))
  inherited.append(dict(condition=c['condition'],checkpoint_sha256=c['checkpoint_sha256'],evidence=c['evidence'],original_provenance=c['inherited_provenance']))
 assert len(inherited)==8
 # The original writer is exclusive; atomic replacement is an explicit postprocessing derivation.
 tmp=out/'normalized-cells.tmp';tmp.write_text(json.dumps(cells,indent=2)+'\n');tmp.replace(out/'cells.json')
 with (out/'cells.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['model','condition','provenance','images','mIoU','checkpoint_sha256','evidence']);w.writeheader();w.writerows({k:c.get(k) for k in w.fieldnames} for c in cells)
 idx.update(cells_sha256=sha256(out/'cells.json'),source_provenance_normalized=True,original_index=str(run/'driver-original-results-index.json'))
 tmp=run/'normalized-index.tmp';tmp.write_text(json.dumps(idx,indent=2)+'\n');tmp.replace(run/'results-index.json')
 write_json(out/'Source-reuse-check.json',dict(status='PASS',Source_cells=8,origin=str(a),origin_completion_sha256=sha256(a/'completion.json'),rows=inherited,note='Inherited A cells carry their original new/reused flags; explicitly marked reused in phase B. Original driver output preserved.'))

def report(prep,run,out,training,cells):
 plans=read(prep/'formal-plans.json');arun=Path(plans['A']['formal_output']);ao=Path(read(arun/'results-index.json')['directory']);seed0=read(ao/'cells.json');am=read(ao/'stage-matrices.json');ad=read(ao/'signed-deltas-and-forgetting.json');bm=read(out/'stage-matrices.json');bd=read(out/'signed-deltas-and-forgetting.json')
 lookup={(c['model'],c['condition']):c for c in cells};a_lookup={(c['model'],c['condition']):c for c in seed0};matrices={};deltas={}
 for m in ('ft','gsmf'):
  for s in (0,1,2):
   k='%s-seed%d-ABCDE'%(m,s);matrices[k]=(am if s==0 else bm)[k];deltas[k]=(ad if s==0 else bd)[k]
 def cell(m,s,t,c):
  name=('source' if t==0 else (m+'_fog' if t==1 else m+'_rain' if t==2 else m+'-seed0-'+('D' if t==3 else 'E'))) if s==0 else ('source' if t==0 else '%s-seed%d-%s'%(m,s,'BCDE'[t-1]))
  return (a_lookup if s==0 else lookup)[name,c]
 statistics={};paired={};flat=[];road=[];contributions=[]
 for t in range(5):
  conds=list(REAL)+(list(('fog005','fog010','fog020')) if t in (0,1,4) else [])
  for c in conds:
   key='%d/%s'%(t,c);statistics[key]={m:stat([cell(m,s,t,c)['mIoU'] for s in (0,1,2)]) for m in ('ft','gsmf')};paired[key]=stat([cell('gsmf',s,t,c)['mIoU']-cell('ft',s,t,c)['mIoU'] for s in (0,1,2)])
   for m in ('ft','gsmf'):
    v=statistics[key][m];flat.append(dict(stage=('Source','Fog','Rain','Snow','Night')[t],condition=c,method=m,seed0=v['per_seed'][0],seed1=v['per_seed'][1],seed2=v['per_seed'][2],mean=v['mean'],sample_std=v['sample_std'],paired_GSMF_minus_FT_mean=paired[key]['mean'],paired_sample_std=paired[key]['sample_std']))
   for s in (0,1,2):
    for m in ('ft','gsmf'):
     if c not in REAL[:t+1]:continue
     row=cell(m,s,t,c);mat=np.asarray(row['confusion_matrix'],np.int64);gt=mat[0].sum();v=dict(method=m,seed=s,stage=('Source','Fog','Rain','Snow','Night')[t],stage_index=t,condition=c,road_GT_pixels=int(gt));v.update({'road_to_'+k:float(mat[0,j]/gt) if gt else None for j,k in enumerate(CLASSES)});road.append(v)
     source=cell(m,s,0,c)
     for k in CLASSES:contributions.append(dict(method=m,seed=s,stage=t,condition=c,class_name=k,IoU=row['IoU'][k],Source_IoU=source['IoU'][k],signed_delta_IoU_over19_pp=None if row['IoU'][k] is None or source['IoU'][k] is None else (row['IoU'][k]-source['IoU'][k])/19))
 composites={};paired_composites={}
 for t in range(5):
  key='seen-domain-mean-after-'+('Source','Fog','Rain','Snow','Night')[t];composites[key]={m:stat([matrices['%s-seed%d-ABCDE'%(m,s)][t]['seen_domain_equal_mean'] for s in (0,1,2)]) for m in ('ft','gsmf')}
 for metric in ('final_five_real_domain_mean','old_domain_mean_forgetting'):
  composites[metric]={m:stat([deltas['%s-seed%d-ABCDE'%(m,s)][metric] for s in (0,1,2)]) for m in ('ft','gsmf')}
 for d in REAL[:-1]:composites['forgetting/'+d]={m:stat([deltas['%s-seed%d-ABCDE'%(m,s)]['old_domain_forgetting'][d]['signed_forgetting'] for s in (0,1,2)]) for m in ('ft','gsmf')}
 for k,v in composites.items():paired_composites[k]=stat([v['gsmf']['per_seed'][s]-v['ft']['per_seed'][s] for s in range(3)])
 # Independently check the driver's real-domain statistics against the evidence above.
 original=read(out/'seed-statistics.json')
 for t in range(5):
  for c in REAL:
   for m in ('ft','gsmf'):assert original['methods'][m][str(t)][c]==statistics['%d/%s'%(t,c)][m]
   assert original['paired_gsmf_minus_ft'][str(t)][c]==paired['%d/%s'%(t,c)]
 summary=dict(n=3,seed_order=[0,1,2],conditions=statistics,paired_gsmf_minus_ft=paired,composites=composites,paired_composites=paired_composites,scope='Fixed Source incremental randomness only; sample SD ddof=1; n=3 is not statistical significance; no Source randomness; synthetic conditions only Source/Fog/Night; no eight-condition mixed mean.')
 write_json(out/'three-seed-all-conditions.json',summary);write_json(out/'three-seed-stage-matrices.json',matrices);write_json(out/'three-seed-deltas-and-forgetting.json',deltas);csvsave(out/'three-seed-statistics.csv',flat);csvsave(out/'road-destinations-all-seeds.csv',road);csvsave(out/'class-change-contributions-all-seeds.csv',contributions)
 # Same descriptive reference as phase A, retain negative changes.
 repeated={}
 for m in ('ft','gsmf'):
  repeated[m]={}
  for target in ('terrain','truck','building'):
   values={str(s):[r['road_to_'+target] for r in sorted([r for r in road if r['method']==m and r['seed']==s and r['condition']=='clear'],key=lambda r:r['stage_index'])] for s in (0,1,2)}
   counts=[sum(v[t]>v[0] for v in values.values()) for t in range(5)]
   repeated[m][target]=dict(fractions_per_seed=values,above_Source_seed_count_by_stage=counts,consistent_above_Source_by_stage=[n==3 for n in counts],note='Descriptive comparison with shared Source; no significance or causal interpretation.')
 write_json(out/'confusion-consistency-three-seeds.json',repeated)
 lines=['# 阶段B：固定Source下的五域增量随机性','', '完成FT/GSMF×seed1/2×Fog→Rain→Snow→Night共16次4000步训练、64份周期checkpoint；104新增评价单元26496逐图独立复核。Source八格复用阶段A；seed0沿用既有Fog/Rain及阶段A，无重训。固定iter4000，无val择优。','', '## 三种子逐条件结果','', '数值为mIoU百分数，标准差为样本标准差(ddof=1)。Source三行来自同一权重，不是三个独立Source实验。Fog后和Rain后分别为两域与三域关键重复。','', '|阶段|条件|方法|seed0|seed1|seed2|均值±SD|配对GSMF−FT均值±SD|','|---|---|---|---:|---:|---:|---:|---:|']
 for r in flat:lines.append('|{stage}|{condition}|{method}|{seed0:.4f}|{seed1:.4f}|{seed2:.4f}|{mean:.4f}±{sample_std:.4f}|{paired_GSMF_minus_FT_mean:+.4f}±{paired_sample_std:.4f}|'.format(**r))
 lines+=['','## 已见域均值与旧域遗忘','', '|指标|方法|seed0|seed1|seed2|均值±SD|配对差值均值±SD|','|---|---|---:|---:|---:|---:|---:|']
 for k,obj in composites.items():
  for m,v in obj.items():p=paired_composites[k];lines.append('|%s|%s|%.4f|%.4f|%.4f|%.4f±%.4f|%+.4f±%.4f|'%(k,m,*v['per_seed'],v['mean'],v['sample_std'],p['mean'],p['sample_std']))
 lines+=['','已见域均值仅含当时已学域；五域全矩阵、逐阶段after-before、新域适应增益、累计相对Source变化和旧域遗忘参照阶段见three-seed-stage-matrices.json及three-seed-deltas-and-forgetting.json。旧域遗忘=max(已学且早于最终阶段)-最终，保留负值，不加入Night零项，不报FWT。合成三档只在Fog后/Night后比较，未评价格不插补。','', '## 晴天road误判去向的三种子一致性','', '|方法|去向|Fog后高于Source的seed数|Rain后|Snow后|Night后|','|---|---|---:|---:|---:|---:|']
 for m,targets in repeated.items():
  for target,v in targets.items():lines.append('|%s|road→%s|%s|'%(m,target,'|'.join(str(n)+'/3' for n in v['above_Source_seed_count_by_stage'][1:])))
 lines+=['','该表只按与共同Source比较描述方向，不把计数解释为统计检验。每个seed的road全去向与指定类别面积比/召回/误报来源top3、19类signed ΔIoU/19见CSV及confusion-tracking.json；seed0证据见阶段A。','', '## 方法、核验及限制','', 'FT全量CE；原版GSMF教师参数冻结但训练态BN更新，学生stem/layer1参数冻结但BN更新；CE+输出Hin(T2/.5)+特征KL(T1/1,idx1/2/3)。KD覆盖stride4全部像素含ignore/padding，无显式T²。每阶段仅当前域train，新AdamW/iter0；无旧图回放。所有评价仅当前学生，19类、原生分辨率、ImageNet、slide512/stride341，无oracle/TTA/测试更新，参数和全部缓冲不变。','', '真实seed由invocation/resolved、MMEngine全局随机源/采样器/worker初始化及准备阶段真实样本序列证据核验。全训练不保证逐位确定：CUDA双线性反向存在非确定性；resume不保证RNG/采样游标精确恢复。n=3只检验固定Source下增量随机性，不覆盖Source训练随机性，不构成显著性或稳定排序证明。官方视频目录交叉已披露，地理/邻帧隔离未独立证明；跨库差异不能全部归因天气，不主张严格未见强度泛化。未加入LwF、BN变体或阶段C。','', ('有退出码的训练命令墙钟合计%.2f分钟（不包含中断命令的原始3000步前缀时间）；评价入口墙钟与显存见resource-costs.json，独立复核/图表/打包另计。'% (sum(v['training_wall_seconds'] for v in training.values())/60)) + (' Snow seed2-GSMF从3000步恢复模型/优化器/调度器；前缀与续训loss由checkpoint历史核对，原始hook审计保留。3000步周期验证在中断前未执行，后续补做100张，单独记录且不计104最终评价格；RNG/采样游标未恢复，不保证不停机等价。详见resume-audit-reconciliation.json。' if (run/'resume-audit-reconciliation.json').exists() else '')]
 (run/'RESULTS.md').write_text('\n'.join(lines)+'\n');(run/'SUMMARY.md').write_text('\n'.join(lines)+'\n');write_json(run/'RESULTS_READY.json',dict(status='verified_pending_figures_package',new_cells=104,reused_cells=8,total_cells=112,new_images=26496,training_runs=16,periodic_checkpoints=64))
