# 第5项阶段B已授权正式方案

用户授权“回复上下文，完成STEP5_FIVE_DOMAIN_SEEDS_REMOTE_TASK_20261111.md的阶段B”。本阶段仅FT/原版GSMF，增量seed1/2，共同Source→Fog(B)→Rain(C)→Snow(D)→Night(E)，每域4000步，共16次。顺序seed1-FT、seed1-GSMF、seed2-FT、seed2-GSMF。任何失败停止整阶段，无自动重试。

batch2/crop512/FP32、AdamW1e-5/PolyLR4000，每1000验证与保存，固定iter4000，无val择优。每阶段新优化器/iter0，仅继承同方法同seed前域部署学生及全部BN缓冲，完整保留原版GSMF冻结参数/训练态BN语义。

104新增格26496逐图：每checkpoint五真实域80格，Fog/Night后三档Foggy24格；Source八格复用阶段A。独立重读全部新增预测及GT重建矩阵，核对ID/GT直方图/推理分支及全部参数缓冲不变。seed0来自既有Fog/Rain及阶段A；逐seed、样本SD、同seed GSMF−FT、已见均值/遗忘/误判去向、图表/固定样例、轻量包安全成员/实际解包/全SHA验证完成后才标complete。

2026-11-11实际完整预检PASS：源码/环境/数据/Source指纹一致，GPU无其他compute任务；WSL约792GiB、宿主约247GiB，均超过B的70GiB门禁，解除准备阶段旧空间障碍。原PREPARED_PLAN是历史不可变证据，本文件记录当前授权与现场。保守总估计20.9小时，不作耗时保证。

不重训Source/seed0，不加入LwF/BN变体/搜索，不启动阶段C，不删除旧checkpoint、不升级环境、不Git提交推送。
