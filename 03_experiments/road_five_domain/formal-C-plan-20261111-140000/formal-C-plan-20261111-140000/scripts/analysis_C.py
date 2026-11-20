"""Explicit single-seed order comparison, including domain positions and signed changes."""
import csv,json
from pathlib import Path
import numpy as np
from road_dil.protocol import CLASSES,sha256,write_json
from tools.road.five_common import REAL

def read(p):return json.loads(Path(p).read_text())
def csvsave(p,rows):
 with Path(p).open('x',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def report(prep,run,out,training,cells):
 plans=read(prep/'formal-plans.json');arun=Path(plans['A']['formal_output']);ai=read(arun/'results-index.json');ao=Path(ai['directory']);assert sha256(ao/'cells.json')==ai['cells_sha256']
 am=read(ao/'stage-matrices.json');ad=read(ao/'signed-deltas-and-forgetting.json');cm=read(out/'stage-matrices.json');cd=read(out/'signed-deltas-and-forgetting.json');acells=read(ao/'cells.json');al={(c['model'],c['condition']):c for c in acells};cl={(c['model'],c['condition']):c for c in cells};orders=dict(main='ABCDE',reverse='AEDCB');domain=dict(A='clear',B='fog',C='rain',D='snow',E='night');matrices=[];comparisons=[];finals=[];after_learning=[];stage_changes=[];forgetting=[];contributions=[];road=[];synthetic=[]
 for m in ('ft','gsmf'):
  main=am[m+'-seed0-ABCDE'];rev=cm[m+'-seed0-AEDCB'];assert len(main)==len(rev)==5
  for order,rows,deltas in [('main',main,ad[m+'-seed0-ABCDE']),('reverse',rev,cd[m+'-seed0-AEDCB'])]:
   for t,row in enumerate(rows):
    seen=[domain[x] for x in orders[order][:t+1]];assert row['seen_domains']==seen and np.isclose(row['seen_domain_equal_mean'],np.mean([row['values'][d] for d in seen]))
    matrices.append(dict(method=m,order=orders[order],position=t,after_domain=domain[orders[order][t]],model=row['stage'],**row['values'],seen_domain_equal_mean=row['seen_domain_equal_mean']))
    if t:
     prev=rows[t-1]
     for d in REAL:stage_changes.append(dict(method=m,order=orders[order],position=t,trained_domain=domain[orders[order][t]],condition=d,before_model=prev['stage'],after_model=row['stage'],after_minus_before=row['values'][d]-prev['values'][d],after_minus_Source=row['values'][d]-rows[0]['values'][d]))
    lookup=al if order=='main' else cl
    for d in seen:
     cell=lookup[row['stage'],d];mat=np.asarray(cell['confusion_matrix'],np.int64);gt=mat[0].sum();road.append(dict(method=m,order=orders[order],position=t,model=row['stage'],condition=d,road_GT_pixels=int(gt),**{'road_to_'+k:float(mat[0,j]/gt) if gt else None for j,k in enumerate(CLASSES)}))
     source=lookup['source',d]
     for k in CLASSES:contributions.append(dict(method=m,order=orders[order],position=t,model=row['stage'],condition=d,class_name=k,IoU=cell['IoU'][k],Source_IoU=source['IoU'][k],signed_delta_IoU_over19_pp=None if cell['IoU'][k] is None or source['IoU'][k] is None else (cell['IoU'][k]-source['IoU'][k])/19))
   for letter in orders[order]:
    d=domain[letter];j=orders[order].index(letter);v=rows[j]['values'][d];after_learning.append(dict(method=m,order=orders[order],condition=d,learned_position=j,learned_model=rows[j]['stage'],mIoU_when_learned=v,final_model=rows[-1]['stage'],final_mIoU=rows[-1]['values'][d],final_minus_when_learned=rows[-1]['values'][d]-v))
   for d in [domain[x] for x in orders[order][:-1]]:
    j=orders[order].index(next(x for x,y in domain.items() if y==d));ref=max(rows[j:-1],key=lambda r:r['values'][d]);v=deltas['old_domain_forgetting'][d];assert ref['stage']==v['reference_stage'] and np.isclose(ref['values'][d]-rows[-1]['values'][d],v['signed_forgetting']);forgetting.append(dict(method=m,order=orders[order],condition=d,reference_model=ref['stage'],reference_mIoU=ref['values'][d],final_model=rows[-1]['stage'],final_mIoU=rows[-1]['values'][d],signed_forgetting=v['signed_forgetting']))
  for d in REAL:
   finals.append(dict(method=m,condition=d,main_final_model=main[-1]['stage'],reverse_final_model=rev[-1]['stage'],main_mIoU=main[-1]['values'][d],reverse_mIoU=rev[-1]['values'][d],reverse_minus_main=rev[-1]['values'][d]-main[-1]['values'][d]))
   letter=next(k for k,v in domain.items() if v==d);a=orders['main'].index(letter);b=orders['reverse'].index(letter)
   for t in range(5):comparisons.append(dict(method=m,condition=d,comparison='same_number_of_updates_different_domains',main_position=t,reverse_position=t,main_model=main[t]['stage'],reverse_model=rev[t]['stage'],main_last_domain=domain[orders['main'][t]],reverse_last_domain=domain[orders['reverse'][t]],main_mIoU=main[t]['values'][d],reverse_mIoU=rev[t]['values'][d],reverse_minus_main=rev[t]['values'][d]-main[t]['values'][d]))
   comparisons.append(dict(method=m,condition=d,comparison='immediately_after_learning_same_domain_different_positions',main_position=a,reverse_position=b,main_model=main[a]['stage'],reverse_model=rev[b]['stage'],main_last_domain=d,reverse_last_domain=d,main_mIoU=main[a]['values'][d],reverse_mIoU=rev[b]['values'][d],reverse_minus_main=rev[b]['values'][d]-main[a]['values'][d]))
  finals.append(dict(method=m,condition='five_real_equal_mean',main_final_model=main[-1]['stage'],reverse_final_model=rev[-1]['stage'],main_mIoU=ad[m+'-seed0-ABCDE']['final_five_real_domain_mean'],reverse_mIoU=cd[m+'-seed0-AEDCB']['final_five_real_domain_mean'],reverse_minus_main=cd[m+'-seed0-AEDCB']['final_five_real_domain_mean']-ad[m+'-seed0-ABCDE']['final_five_real_domain_mean']))
  for cond in ('clear','fog005','fog010','fog020'):
   a=al[main[-1]['stage'],cond];b=cl[rev[-1]['stage'],cond];synthetic.append(dict(method=m,condition=cond,main_model=a['model'],reverse_model=b['model'],main_mIoU=a['mIoU'],reverse_mIoU=b['mIoU'],reverse_minus_main=b['mIoU']-a['mIoU']))
 for name,rows in [('stage-matrices-both-orders',matrices),('explicit-stage-order-comparisons',comparisons),('final-order-comparison',finals),('changes-after-learning',after_learning),('all-stage-signed-changes',stage_changes),('signed-forgetting-both-orders',forgetting),('road-destinations-both-orders',road),('class-contributions-both-orders',contributions),('synthetic-final-order-comparison',synthetic)]:csvsave(out/(name+'.csv'),rows)
 proof=dict(status='PASS',seed=0,source_fixed=True,main_order='ABCDE',reverse_order='AEDCB',main_results_index_sha256=sha256(arun/'results-index.json'),main_cells_sha256=ai['cells_sha256'],domain_positions={o:{domain[l]:i for i,l in enumerate(order)} for o,order in orders.items()},finals=finals,comparisons=comparisons,after_learning=after_learning,forgetting=forgetting,note='Single seed order sensitivity only; same-position rows learn different current domains. Immediately-after-learning rows compare different sequence positions; no stable ranking or significance claim.')
 write_json(out/'explicit-order-comparison.json',proof)
 lines=['# 阶段C：seed 0顺序变化','', 'FT与原版GSMF各从共同Source，按A→E(Night)→D(Snow)→C(Rain)→B(Fog)完成4×4000步，共8次、32份周期checkpoint。46个新增评价格、10248次逐图推理及保存预测独立重读；共同Source八格按指纹复用A，合计54格。固定iter4000，不按验证表现选择。','', '## 阶段×五真实域矩阵','', 'mIoU（%）；提前评价未来域不计入当时已见均值。','', '|方法|顺序|位置|刚学完|模型|CS|Fog|Rain|Snow|Night|已见域等权均值|','|---|---|---:|---|---|---:|---:|---:|---:|---:|---:|']
 for r in matrices:lines.append('|%s|%s|%d|%s|%s|%.4f|%.4f|%.4f|%.4f|%.4f|%.4f|'%(r['method'],r['order'],r['position'],r['after_domain'],r['model'],*[r[d] for d in REAL],r['seen_domain_equal_mean']))
 lines+=['','## 最终部署模型对照','', '主序最终模型在Night后，反序最终模型在Fog后；均经历四次增量更新。','', '|方法|真实域/均值|主序最终Night后|反序最终Fog后|反序−主序(pp)|','|---|---|---:|---:|---:|']
 for r in finals:lines.append('|{method}|{condition}|{main_mIoU:.4f}|{reverse_mIoU:.4f}|{reverse_minus_main:+.4f}|'.format(**r))
 lines+=['','## 同域刚学完时的对照','', '主序Fog/Rain/Snow/Night分别在位置1/2/3/4，反序为4/3/2/1。下表逐项指明不同位置；它不控制历史暴露与训练时序。','', '|方法|域|主序位置/模型|反序位置/模型|主序mIoU|反序mIoU|反序−主序|','|---|---|---|---|---:|---:|---:|']
 for r in comparisons:
  if r['comparison'].startswith('immediately'):lines.append('|{method}|{condition}|{main_position}/{main_model}|{reverse_position}/{reverse_model}|{main_mIoU:.4f}|{reverse_mIoU:.4f}|{reverse_minus_main:+.4f}|'.format(**r))
 lines+=['','## 各域学完后的变化','', '|方法|顺序|域|学完位置|学完mIoU|最终mIoU|最终−学完(pp)|','|---|---|---|---:|---:|---:|---:|']
 for r in after_learning:lines.append('|{method}|{order}|{condition}|{learned_position}|{mIoU_when_learned:.4f}|{final_mIoU:.4f}|{final_minus_when_learned:+.4f}|'.format(**r))
 lines+=['','## 带符号旧域遗忘','', 'max(已学且早于最终阶段的mIoU)−最终mIoU，保留负值。主序最终新域Night、反序最终新域Fog分别排除；两顺序的旧域集合不同，均值须按各自定义理解。','', '|方法|顺序|旧域|参照模型|参照mIoU|最终mIoU|遗忘(pp)|','|---|---|---|---|---:|---:|---:|']
 for r in forgetting:lines.append('|{method}|{order}|{condition}|{reference_model}|{reference_mIoU:.4f}|{final_mIoU:.4f}|{signed_forgetting:+.4f}|'.format(**r))
 lines+=['','## 最终模型合成雾条件（单列）','', '|方法|条件|主序Night后|反序Fog后|反序−主序(pp)|','|---|---|---:|---:|---:|']
 for r in synthetic:lines.append('|{method}|{condition}|{main_mIoU:.4f}|{reverse_mIoU:.4f}|{reverse_minus_main:+.4f}|'.format(**r))
 lines+=['','## 描述与限制','']
 for m in ('ft','gsmf'):
  v=next(r for r in finals if r['method']==m and r['condition']=='five_real_equal_mean');lines.append('%s最终五真实域等权均值从主序%.4f变为反序%.4f，变化%+.4f个百分点。'%(m.upper(),v['main_mIoU'],v['reverse_mIoU'],v['reverse_minus_main']))
 f=next(r for r in finals if r['method']=='ft' and r['condition']=='five_real_equal_mean');g=next(r for r in finals if r['method']=='gsmf' and r['condition']=='five_real_equal_mean');lines.append('GSMF−FT最终五域均值差：主序%+.4f，反序%+.4f个百分点。仅描述本seed的顺序敏感性，不据此推断稳定排序或统计显著。'%(g['main_mIoU']-f['main_mIoU'],g['reverse_mIoU']-f['reverse_mIoU']))
 lines+=['','主序/反序同更新次数的逐域差值见explicit-stage-order-comparisons.csv；逐阶段after-before、相对Source变化、新域适应及遗忘见all-stage-signed-changes.csv、signed-deltas-and-forgetting.json。CS及已学ACDC的road去向、指定类别面积比/召回/误报来源top3、19类signed ΔIoU/19见confusion-tracking.json和CSV；不作因果归因，不报FWT。','', '首域E用Source去辅助头严格转换；GSMF师生完整克隆且独立存储，后域仅继承同方法/seed/顺序前域学生参数和BN缓冲，丢弃旧教师；每域新AdamW/iter0。FT全量CE；原GSMF教师参数冻结、训练态BN/Dropout保留，学生stem/layer1参数冻结且BN更新；损失CE+Hin(T2/.5)+特征KL(T1/1,idx1/2/3)。输出KD覆盖stride4全部logit像素含ignore/padding，无显式T²。','', '训练仅当前域train，无旧图回放。batch2/crop512/FP32、AdamW1e-5/wd.001、PolyLR4000，每1000当前域验证保存，随机种子0作用于全局/采样器/worker；确定性限制继承准备证据。评价原生分辨率、ImageNet、512/341滑窗、仅学生，19类、GT行/预测列/ignore255，累计全集矩阵；union0排除/null，GT缺失有预测记0。无oracle/TTA/测试BN更新；参数和持久/非持久缓冲核验见独立检查。','', 'Source固定且未重训；单seed不覆盖Source随机性。CUDA双线性反向不保证逐位确定；中断resume不能保证RNG/采样游标精确恢复。官方共享视频目录披露，未独立核实地理/邻帧隔离；跨库差异不能全部归因天气，不主张严格未见强度泛化。无LwF/BN变体、其他seed、搜索或新模块。','', '训练入口墙钟合计%.2f分钟；各阶段训练/验证耗时、显存与评价格耗时见resource-costs.json。独立重读/图表/打包另计。'%(sum(v['training_wall_seconds'] for v in training.values())/60)]
 (run/'RESULTS.md').write_text('\n'.join(lines)+'\n');(run/'SUMMARY.md').write_text('\n'.join(lines)+'\n');write_json(run/'RESULTS_READY.json',dict(status='verified_pending_figures_package',new_cells=46,reused_cells=8,total_cells=54,new_images=10248,training_runs=8,periodic_checkpoints=32))
