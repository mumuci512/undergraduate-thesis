# 第5项唯一分阶段正式方案

更新：2026-11-11T14:26:34.512835+08:00。**准备通过／正式未启动**。准备目录：`/home/ysheng4/research/GSMF-RS-DIL/experiments/road_five_domain/prepare-20261111-140000`。阶段A/B/C均未获得授权、未创建正式目录；未运行4000步或完整正式评价。

## 现场、数据与来源

当前HEAD `89b6e014891630da865578197396236ef2a49140`，与任务文件旧快照a93b90c不同；本轮保留现场，不提交/推送/重置、不升级环境。旧训练来源由ancestors.json所列历史provenance与其SHA追溯，当前HEAD仅说明本轮源码起点。
A/B/C原manifest字节与记录/实际图像标签SHA复核；Snow(D)400/100、Night(E)400/106，独立目录解压train/val RGB、trainIds及交叉核对labelIds，CRC/长度/逐文件SHA通过。D/E全部解码、同尺寸RGB三通道/整数单通道、19类0..18/255及两种编码逐像素一致；test/ref未提取。A/B/C解码哈希继承原全量审计，实际文件字节重核，D/E解码像素哈希本轮重算。涉及D/E的帧ID、RGB字节/解码哈希重复为0。完整清单、直方图/manifest与归档指纹见data/audit.json及各archive-provenance.json。
Snow train/val共享视频目录：GOPR0122, GOPR0604, GOPR0606, GOPR0607, GP010607, GP030176；Night共享：GOPR0351。官方划分不变，未独立核实地理/邻帧隔离。
协议：边界已知、固定19类、完整监督；每阶段优化只读当前train，无旧图回放、参考图或合成天气训练。val仅验证/评价，不择超参/checkpoint；未来域提前评价不纳入当时已见均值。域ID用于数据/统计，部署仅学生，无天气oracle/TTA/测试BN更新。主顺序借用MILE顺序，不据跨骨干表排名，不自动确定论文最终边界协议。

| 祖先/父模型 | SHA-256 |
|---|---|
| source | `a66c958ee774d27566b901ad6570c0a3b83263e9d74389e1c2e025c6c2673d93` |
| ft | `99914df527d8506c33178ef6ea1caf7f0ed1d07369858e37275205d60a57d516` |
| gsmf | `fc227c57dc3e47a134ef51b282964654a0210f3c06f00bd0d3e81b706850b24a` |
| lwf | `854d83357a912713a27cf27283b024f3e7fd7dab47043434d312b136ec9b6843` |
| ft_rain | `ac04f676ed6ec53d6e8bf2267c5c06aad05e3db1537558e752cd7c98b8e68e34` |
| gsmf_rain | `754f53ec406b6efeac4ed9fb82364614b0fd9a9d603bd9298f35878a8f2a83f3` |
| lwf_rain | `f88ed8621d7fab8cfef1d6a91fb1991de60b4da649547bd625df06450d498527` |

## 初始化、seed与方法

阶段A三方法分别继承自己的Rain学生→Snow→Night；阶段B/C同一共同Source，后续只取同方法/同seed/同顺序的前域部署学生。Source去辅助头；FT全量单分支698张量，GSMF/LwF将学生698张量克隆为独立教师/学生1396张量，参数与全部BN缓冲均完整继承，丢弃旧教师。各键父SHA/父键/目标键/shape/值SHA见conversion/*/conversion.json；真输入师生与父部署输出完全相等，严格保存重载一致。后续正式尚未产生的Snow/Night父SHA只能运行时计算，禁止预编造；驱动以精确父路径和SHA传递，每次保存于初始化及checkpoint元数据。
每个新域为新优化器、iter0，排除父optimizer/scheduler/iter；resume必须同绝对运行目录、方法、域、seed、顺序，恢复优化器/调度器/iter。拒绝上一域optimizer。当前MMEngine未保存RNG/采样游标，resume后可重复前面的增强序列，不声称与不停机逐位一致。
真实seed接通：--seed默认0，cfg.randomness→Runner全局Python/NumPy/Torch/CUDA、InfiniteSampler及worker2初始化，deterministic=True。实际E域seed0重复两次前4个batch的ID/缩放/裁剪/翻转/增强输入哈希及首个loss逐位一致；后续loss最大绝对差约7.43e-5，严格确定性诊断见determinism-diagnostic.json（不声称全训练逐位一致），seed0与1样本序列不同。已完成Rain seed0配置逐项相等核对；历史训练没有样本序列记录，只能比配置。所有增量seed从固定Source开始，不覆盖Source训练随机性。详见seed-verification.json、seed-runtime-source.txt、各invocation/resolved/manifest-resolution。
FT全参数CE。原GSMF教师参数冻结、训练态BN和Dropout保留，学生stem/layer1参数冻结但BN更新；CE+Hin(T2/.5)+特征KL(T1/1,idx[1,2,3])。LwF教师eval/no_grad、全部参数缓冲固定，学生全量更新；仅CE+输出KD，无特征KL。输出KD覆盖原生stride4所有logit像素（含ignore/padding），无显式T²；CE ignore255/avg_non_ignore=False沿用，不改损失，不加BN变体。

## 真实短运行证据

本轮独立锁定账本 `60/64` 优化步：三方法各D 4+4同运行resume、各E4；FT/GSMF各Source→B seed1四步、Source→E反序seed0四步；FT E同seed重复/异seed各四步。全部有限loss/梯度，冻结/更新与BN策略、实际周期验证后train、19通道、严格保存重载通过。GSMF教师BN变化 342 项，LwF教师BN变化 0 项。seed2入口/配置/初始化已核验，未额外做seed2优化。
三方法×8条件=24个真实小样本评价，共66张；实际评价入口、原标签/保存预测独立重读、ID/尺寸/GT直方图/矩阵一致，仅学生且状态不变。无优化转换/推理独立计时见final-real-verification.json，所有命令/日志/退出码及账本保留。短训mIoU不作正式效果。
失败记录：数据准备首次语法错误、静态dataset检查首次未注册默认scope、续核验首次报告重复使用排他写入文件名均为零优化；首轮smoke在完成60步后因要求所有后续loss逐位相等的过严断言停止。针对性零优化诊断确定PyTorch1.9.1的upsample_bilinear2d_backward_out_cuda无确定性实现；首loss及全部增强/输入逐位一致，后续loss最大微差7.43e-5已披露，保留原训练/日志，续做核验不重训、不重置账本。正式汇总代码仅做语法/形状和复用真实小样本重读验证，完整正式结果/图表/打包只能在后续真实产物上验收。

## 三阶段唯一预算与命令

每次4000步/batch2/crop512/FP32，AdamW lr1e-5, betas(.9,.999),wd.001；PolyLR power.9/end4000，每1000当前域val验证并保存，固定iter4000为主。RandomResize(2048,1024)/ratio(.5,2)、crop cat_max_ratio.75、flip.5、PhotoMetricDistortion；其余与Rain resolved一致。每域400训练图约20轮曝光，不按短训/val改预算。实质差异仅当前域manifest、严格父学生快照元信息及B阶段seed1/2；不重训Source/Fog/Rain seed0。
8条件：CS500、同500场景Foggy三档β.005/.01/.02各500、fog100/rain100/snow100/night106。原生分辨率、ImageNet、slide512/stride341、无TTA，统一19类、GT行/预测列、ignore255；全集累计矩阵，union0排除写null、GT缺失但有预测为0，不平均逐图mIoU。formal-plans.json逐格标reused/new、父子路径和来源SHA；旧42格checkpoint/全ID/图像标签指纹/预处理/分支/指标/GT直方图复核通过，只复用不声称本轮推理。

### 阶段A

唯一目录：`/home/ysheng4/research/GSMF-RS-DIL/experiments/road_five_domain/formal-A-plan-20261111-140000`。训练6次；新增62格、15878次逐图。
A：三方法seed0各Rain→D→E；先全部D再全部E。总13 checkpoint×8=104格，42复用；7旧模型D/E提前评价14格1442图，6新模型×8=48格14436图。
测得短训外推：训练计算1.32h、周期验证0.58h、评价循环4.49h；含I/O/独立重读/报告和1.5安全系数总约11.3h（非保证）。checkpoint 15.7GiB，初始化约1.8GiB；预测按本轮最大PNG外推0.44GiB、不压缩上界30.9GiB。每次启动WSL/宿主各须至少40GiB；本次磁盘门禁通过。

```bash
bash tools/road/five_start.sh /home/ysheng4/research/GSMF-RS-DIL/experiments/road_five_domain/prepare-20261111-140000 A --confirmed
```

### 阶段B

唯一目录：`/home/ysheng4/research/GSMF-RS-DIL/experiments/road_five_domain/formal-B-plan-20261111-140000`。训练16次；新增104格、26496次逐图。
B：seed1-FT、seed1-GSMF、seed2-FT、seed2-GSMF，每条B→C→D→E。16新checkpoint×五真实域=80格14496图；B后/E后各三档Foggy=24格12000图。共同Source8格复用A；若A未完成可训练/评价，Source分析等待A证据。LwF/BN变体不加入。
测得短训外推：训练计算3.24h、周期验证1.47h、评价循环7.56h；含I/O/独立重读/报告和1.5安全系数总约20.9h（非保证）。checkpoint 39.9GiB，初始化约4.3GiB；预测按本轮最大PNG外推0.73GiB、不压缩上界51.6GiB。每次启动WSL/宿主各须至少70GiB；本次磁盘门禁**未通过，正式启动前须另行解决空间。**

```bash
bash tools/road/five_start.sh /home/ysheng4/research/GSMF-RS-DIL/experiments/road_five_domain/prepare-20261111-140000 B --confirmed
```

### 阶段C

唯一目录：`/home/ysheng4/research/GSMF-RS-DIL/experiments/road_five_domain/formal-C-plan-20261111-140000`。训练8次；新增46格、10248次逐图。
C：FT/GSMF seed0，Source→E→D→C→B。8新checkpoint×五真实域=40格7248图；最终B后三Foggy=6格3000图。共同Source复用A。
测得短训外推：训练计算1.62h、周期验证0.73h、评价循环2.90h；含I/O/独立重读/报告和1.5安全系数总约9.4h（非保证）。checkpoint 20.0GiB，初始化约2.1GiB；预测按本轮最大PNG外推0.29GiB、不压缩上界19.9GiB。每次启动WSL/宿主各须至少35GiB；本次磁盘门禁通过。

```bash
bash tools/road/five_start.sh /home/ysheng4/research/GSMF-RS-DIL/experiments/road_five_domain/prepare-20261111-140000 C --confirmed
```

上述命令仅在对应提示词二/三/四或明确确认后执行。届时将用户原文、确认时间、READY真实SHA写入authorization-A/B/C.json：`{"phase":"A|B|C","confirmed":true,"ready_sha256":"<真实SHA>","user_message":"<原文>","confirmed_at":"...+08:00"}`。本轮不存在此类文件。
只读预检：`python tools/road/five_formal.py --prepare <本准备目录> --phase A|B|C --check-only`（须使用指定环境Python）；状态：`bash tools/road/five_status.sh <正式目录>`；同授权运行恢复：`bash tools/road/five_resume.sh <准备目录> A|B|C --confirmed`。tmux持久探针实际exit0；driver全阶段共享锁、记录实际PID/命令/状态/退出码，失败停止整阶段、不无限重试、不自动进入下一阶段。主机/WSL停机会中断，不承诺额外持续监控。

## 分析与验收约定

five_results.py独立重读每格保存预测与原GT，输出逐类IoU/矩阵、共享Source行的阶段×五真实域R、只含已见域的等权均值及最终五真实域均值；合成条件单列，不算8条件混合均值。差值为after-before：逐阶段所有域变化、相对Source累计变化、新域相对前模型适应增益。旧域遗忘=max(已学且早于最终阶段)-最终，写参照阶段、保留负值，不含最终新域零项，不报FWT。
B完成后seed0来自旧Fog/Rain+A Snow/Night，列seed0/1/2、均值/样本标准差及同seed GSMF−FT差值及其均值/样本标准差；n3仅固定Source的增量随机性，不证明显著。C写明域在顺序中的位置，比较主序与反序的明确阶段，仅描述单seed敏感性。
CS每checkpoint及已学ACDC：road真值预测去向top5；terrain/truck/train/sky/building/fence/bicycle预测/GT面积比、召回、误报来源top3；相对Source的signed ΔIoU/19（当前−Source，负数为下降）。仅描述，不作因果。固定6个CS ID及预先seed0选定的D/E val各6 ID在fixed-samples.json；所有方法/seed/阶段共用，不按效果选图，原始预测远程保留。
后续正式阶段须另验训练/checkpoint元信息/全部评价格、独立指标、曲线/固定样例对齐、资源记录及轻量包。包名<正式run-id>-light.tar.gz，MANIFEST覆盖除自身外全部，外置SHA；安全成员检查、新目录实际解包核对集合与全SHA。权重/原图/全量预测/环境/.git留远程，不含认证文件。只有全部完成才标complete；驱动结束仅train_eval_verified_pending_handoff，不冒充交接完成。

## 资源限制和停止边界

本轮空闲WSL 645.5GiB、宿主C 57.1GiB。阶段按各自门禁独立检查，三阶段累计checkpoint/预测占用会增长，不能假设当前空间能连续容纳全部。未删除数据或checkpoint；若宿主不足，须用户另行提供空间/批准清理。
本轮停止：准备通过，A/B/C正式训练、完整新评价、最终结果/图表/交接包均未执行。没有Source重训、搜索、新模块、正常参考/合成训练、环境升级、大规模下载、Git提交/推送或旧checkpoint覆盖。
