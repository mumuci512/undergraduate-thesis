# 阶段C正式方案

授权原文：完成STEP5_FIVE_DOMAIN_SEEDS_REMOTE_TASK_20261111.md的阶段c

FT/GSMF seed0，共同Source→Night(E)→Snow(D)→Rain(C)→Fog(B)，各4000步，共8次。batch2/crop512/FP32，AdamW1e-5/wd.001，PolyLR4000，每1000当前域验证保存，固定iter4000。首域E严格Source去辅助头，后续同方法seed顺序前域学生参数与全部BN缓冲；每域新optimizer/iter0。46新评价格10248次逐图，Source八格复用A；独立预测重读、主序seed0对照、图表/固定样例、轻量包安全实际解包及全SHA全通过后才complete。

训练与数据、配置和环境严格复用PREPARED_PLAN/READY；C在准备阶段已有Source→E真实短训及完整转换/seed/冻结语义验证，不追加调试优化。源码核心指纹未漂移；当前Git HEAD d9d3298aee037ee7bb9e78ee2f1b67d8793ef3d0，准备/历史运行版本各按原provenance记录。

启动：bash tools/road/five_start.sh /home/ysheng4/research/GSMF-RS-DIL/experiments/road_five_domain/prepare-20261111-140000 C --confirmed
后处理由本运行scripts/complete_C.py串行监督；失败保留证据，不自动重训或无限重试。后处理脚本与SHA记录在postprocessing-provenance.json；正式驱动/每次入口命令、日志、退出码和checkpoint元信息全留存。

阶段B完成记录与包不变；不新增LwF/BN变体、其他seed、搜索、模块、Source重训或其他实验。不升级环境，不删除/覆盖旧数据和checkpoint，不提交/推送。
