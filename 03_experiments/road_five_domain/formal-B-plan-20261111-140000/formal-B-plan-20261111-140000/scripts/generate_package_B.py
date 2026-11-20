"""Retain stage A's accepted allowlist, safe unpack and full hash checks for phase B."""
from pathlib import Path
base=Path('experiments/road_five_domain/formal-A-plan-20261111-140000/scripts/package_A.py')
dest=Path('experiments/road_five_domain/prepare-20261111-140000/postprocessing-B/package_B.py')
s=base.read_text();s=s[:s.index(" p=ROOT/'REPRO.md';")]
s=s.replace('Stage-A','Stage-B').replace("['new_cells']==62", "['new_cells']==104").replace('len(weights)==13','len(weights)==17').replace('authorization-A.json','authorization-B.json')
s=s.replace('阶段A六次4000步、62新格15878逐图、42复用格、104格汇总','阶段B十六次4000步、104新格26496逐图、8个Source复用格、112格汇总')
s=s.replace('阶段B暂缓、C未授权','阶段C未授权').replace('阶段B暂缓，C未授权','阶段C未授权').replace('阶段B暂缓，阶段C未授权','阶段C未授权')
s=s.replace("==192", "==300").replace('five-A-handoff-verify-','five-B-handoff-verify-').replace('raw_CS_samples=36,raw_DE_samples=156','raw_CS_samples=96,raw_DE_samples=192,inherited_Source_raw_masks=12')
s=s.replace("phase='A'", "phase='B'").replace('training_runs=6','training_runs=16').replace('periodic_checkpoints=24','periodic_checkpoints=64').replace('new_cells=62,new_images=15878,reused_cells=42,total_cells=104','new_cells=104,new_images=26496,reused_cells=8,total_cells=112')
s=s.replace("next_phase='B deferred by latest user instruction; C not authorized'", "next_phase='C not authorized'")
s=s.replace('阶段A六次4000步、24份完整周期checkpoint、62新格15878逐图与42旧格复用共104格','阶段B十六次4000步、64份完整周期checkpoint、104新格26496逐图与8个Source复用共112格')
anchor=" inherited=read(prep/'data/audit.json')['inherited_ABC_audit'];"
extra=""" # Explicit seed0 and shared Source provenance used by all three-seed tables.
 a=Path(read(prep/'formal-plans.json')['A']['formal_output']);ao=Path(read(a/'results-index.json')['directory'])
 for name in ('completion.json','results-index.json','RESULTS.md','remote-index.json','handoff/handoff-verification.json'):
  copy(a/name,content/'reused-seed0/A'/name)
 for name in ('cells.json','stage-matrices.json','signed-deltas-and-forgetting.json','confusion-tracking.json','training-independent-check.json','protocol-independent-check.json','verification.json'):
  copy(ao/name,content/'reused-seed0/A/results'/name)
 copy(a/'scripts/figures_A.py',content/'reused-seed0/A/scripts/figures_A.py')
"""
s=s.replace(anchor,extra+anchor)
s+='''
 p=ROOT/'REPRO.md';text=p.read_text();a=text.index('<!-- ROAD_FIVE_DOMAIN_CURRENT_BEGIN -->');b=text.index('<!-- ROAD_FIVE_DOMAIN_CURRENT_END -->')+len('<!-- ROAD_FIVE_DOMAIN_CURRENT_END -->');stats=read(out/'three-seed-all-conditions.json');finals='; '.join(m+' '+ '/'.join('%.4f±%.4f'%(stats['conditions']['4/'+d][m]['mean'],stats['conditions']['4/'+d][m]['sample_std']) for d in ('clear','fog','rain','snow','night')) for m in ('ft','gsmf'))
 block='<!-- ROAD_FIVE_DOMAIN_CURRENT_BEGIN -->\\n## 当前道路工作：第5项阶段B正式实验及轻量交接完成（'+now()[:10]+'）\\n\\n- 用户授权完成任务文件阶段B。FT/GSMF seed1/2固定Source→Fog→Rain→Snow→Night，16次各4000步、64份完整周期checkpoint、104新增评价格26496逐图独立重读核验，Source8格复用A共112格；三种子配对统计/样本SD、关键Fog/Rain重复、旧域遗忘/误判去向、图表/预固定样例及轻量包实际安全解包全SHA通过。阶段A既有seed0结果保留；C未授权，不自动启动。\\n- 正式目录：`'+str(run.relative_to(ROOT))+'`，exit-code.txt=0、completion.json complete、handoff/handoff-verification.json PASS。每阶段新AdamW/iter0，同方法同seed继承前域学生完整参数与BN缓冲；配置/数据/Source与准备指纹一致。batch2/crop512/FP32、AdamW1e-5/PolyLR4000，每1000验证/保存，固定iter4000，无val择优。GSMF保留教师训练态BN与浅层冻结参数语义；部署只用学生，无oracle/TTA/测试更新。\\n- 最终Night后CS/Fog/Rain/Snow/Night三种子mIoU均值±样本SD（%）：'+finals+'。逐seed、同seed GSMF−FT、已见域均值和带符号遗忘详见RESULTS.md及results-index.json。\\n- 包：`'+str(archive.relative_to(ROOT))+'`，外置同名.sha256，SHA `'+digest+'`。权重/原图/全量预测留远程；包内冻结状态与包外完成证据分开避免自引用。\\n- n=3仅覆盖固定Source的增量随机性，不证明显著或稳定排序，不覆盖Source训练随机性。官方共享视频目录披露，未独立核实地理/邻帧隔离；不将跨库差异全部归因天气，不主张严格未见强度泛化。CUDA反向不逐位确定，resume不保证RNG/采样游标精确恢复。无LwF/BN变体、Source或seed0重训、阶段C、搜索、环境升级、删除旧数据checkpoint、Git提交或推送。\\n<!-- ROAD_FIVE_DOMAIN_CURRENT_END -->'
 p.write_text(text[:a]+block+text[b:])
 copy(run/'status.json',run/'driver-status-final.json')
 state=dict(time_utc=datetime.now(timezone.utc).isoformat(),phase='B',state='complete',actor='verified_package',actor_pid=os.getpid(),exit_code=0,archive=str(archive),archive_sha256=digest,next_phase='C not authorized')
 with (run/'events.jsonl').open('a') as f:f.write(json.dumps(state)+'\\n')
 temp=run/'status-complete.tmp';temp.write_text(json.dumps(state,indent=2)+'\\n');temp.replace(run/'status.json')
 print(json.dumps(proof,ensure_ascii=False,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--prepare',required=True);p.add_argument('--run',required=True);a=p.parse_args();main(a.prepare,a.run)
'''
dest.write_text(s)
print('Generated B safe package and completion checks')
