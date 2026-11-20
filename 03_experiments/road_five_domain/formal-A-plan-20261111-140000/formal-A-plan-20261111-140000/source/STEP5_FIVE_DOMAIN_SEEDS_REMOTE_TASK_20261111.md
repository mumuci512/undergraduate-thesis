# 第5项远程任务：五域天气链、关键种子与顺序变化

编写日期：2026-11-11（Asia/Shanghai）。本文件依据通过`home-wsl`对远程工程的实际只读核查编写，不要求远程能读取学校论文目录。此次未修改远程源码、数据或实验，未解压Snow／Night，未启动训练或Codex任务。执行顺序依据见本地[后续实验顺序§10](../../03_experiments/NEXT_STEPS_AND_BASELINE_REVIEW_2026-11-09.md)；远程执行所需事实已写入下方提示词。

## 已核查的现场与使用方式

- SSH别名：`home-wsl`；项目：`/home/ysheng4/research/GSMF-RS-DIL`；训练环境：`/home/ysheng4/miniconda3/envs/GSMF_RS_DIL`。
- 远程当前HEAD：`a93b90c76f13733920f824a03e21020dee08430c`。工作区有第3项留下的未提交修改：`REPRO.md`、`road_dil/{checkpoints,config,data,hooks}.py`、`tools/road/{extract_data,run}.py`，以及未跟踪的`STEP3_RAIN_CHAIN_REMOTE_TASK_20261110.md`和`tools/road/rain_*.py／*.sh`、`check_rain_contracts.py`、`finalize_rain_preparation.py`、`prepare_rain_*.py`。本次均未改动；执行时不得重置或提交。
- 根`AGENTS.md`的SHA-256仍为`ba20032b3c1c63bd68f082b4db151c59cfc3ebb23e1822786bddad3e613bc029`。远程规则要求：**“完整训练前先通过小规模验证确认代码正确。”及“启动耗时的正式训练前，先向用户报告实验方案并取得确认。”** 因此提示词一只做准备；阶段A／B／C的正式训练分别由提示词二／三／四授权。
- 数据：`data/road_raw/rgb_anon_trainvaltest.zip`按路径模式计数，snow train／val／test为400／100／500，night为400／106／500；`gt_trainval.zip`中snow为400／100、night为400／106份`_gt_labelTrainIds.png`。目前只解压了fog（`data/acdc`）和rain（`data/acdc_rain_step3_20261110-180543`）。Snow／Night尚未做逐像素、逐文件哈希核验，也未检查帧配对。
- 代码：`road_dil/config.py`的`make_config`对增量阶段只接受`train_domain`为B／C；`tools/road/run.py`的`--train-domain`、`--domain`只接受A／B／C；`tools/road/extract_data.py`的`--weather`只接受fog／rain。**`road_dil/config.py`第86行附近为`randomness=dict(seed=0, deterministic=True)`，`tools/road/run.py`第149行附近的invocation写死`seed=0`**，所以seed 1／2必须真正接通，不能只改目录名。第3项已增加`convert-incremental`（ft／gsmf／lwf）。
- 第3项Rain最终检查点均在`experiments/road_clear_fog_rain/formal-seed0-plan-20261110-180543/{ft,gsmf,lwf}/iter_4000.pth`，含1000–4000步周期checkpoint；FT单个约575MB，GSMF约765MB（含优化器状态）。下方SHA取自本地接收的42格记录，本次未在远程重算。
- 资源快照：RTX 3080 20GB，已用1497MiB、利用率0%；没有tmux server；根分区可用667GB。第3项实测每次4000步训练14–16分钟、显存峰值不到3GB；CS规模500张评价约5分钟，ACDC约100张约1.2分钟。这些只是一次现场与历史观测，运行前仍须复查。

可直接复制下方相应代码框到现有远程Codex。也可在本地PowerShell传文件：

```powershell
scp 'C:\undergraduate_thesis\02_baselines\GSMF-RS-DIL\STEP5_FIVE_DOMAIN_SEEDS_REMOTE_TASK_20261111.md' 'home-wsl:/home/ysheng4/research/GSMF-RS-DIL/STEP5_FIVE_DOMAIN_SEEDS_REMOTE_TASK_20261111.md'
```

然后发送：

```text
请读取项目根目录的 STEP5_FIVE_DOMAIN_SEEDS_REMOTE_TASK_20261111.md，执行“提示词一”代码框内的任务：准备Snow／Night数据、D／E域入口、真实seed接通、五域链与顺序变化的严格转换、真实短运行和分阶段正式方案。本轮停止在准备完成；提示词二及以后的正式训练暂不执行。
```

## 提示词一：准备Snow／Night、真实种子与五域链短运行

```text
请在 /home/ysheng4/research/GSMF-RS-DIL 中，实际完成第5项的执行准备：把已完成的Cityscapes(A)→ACDC-fog(B)→ACDC-rain(C)三域链扩展为A→B→C→ACDC-snow(D)→ACDC-night(E)五域链，并为后续关键种子和一条顺序变化做好入口。完成必要代码、数据、严格转换、真实短运行、可执行正式入口及分阶段正式方案；本轮不启动任何4000步正式训练，也不提前跑完整正式评价。

一、恢复现场与范围

1. 读取适用AGENTS.md、REPRO.md当前道路段落，以及下述旧实验的PLAN／PREPARED_PLAN／STATUS／RESULTS和必要源码。先核查实际Git HEAD／工作区、Python环境、GPU进程、tmux及磁盘，不把历史文档里的running当作实际状态。2026-11-11只读核查时HEAD为a93b90c76f13733920f824a03e21020dee08430c，工作区有第3项未提交的源码修改和未跟踪rain工具；全部保留，不提交、不推送、不重置，不升级环境，不终止别人的进程。
2. 环境Python为 /home/ysheng4/miniconda3/envs/GSMF_RS_DIL/bin/python；历史为Python3.8.20、PyTorch1.9.1+cu111、MMCV2.0.0、MMEngine0.8.2、MMSeg1.2.1、RTX3080 20GB，现场核对后复用。缺rg用Python／grep，不为此安装软件。
3. 只读复用的旧目录：两域experiments/road_clear_to_fog/formal-seed0-20261108-resume01；强度评价experiments/road_fog_severity/eval-final-seed0-20261109-182100；第2项experiments/road_lwf_bn/formal-seed0-plan-20261110-153000；第3项experiments/road_clear_fog_rain/prepare-seed0-20261110-180543与formal-seed0-plan-20261110-180543。本轮新建独立experiments/road_five_domain/prepare-<唯一时间>；三个正式阶段以后各自另建formal目录。
4. 协议不变：阶段边界已知、固定19类、完整监督、增量阶段无旧图训练回放。推理所有条件只用当前部署学生，不提供真实天气ID选分支；域ID只用于数据与统计。不自动确定论文最终边界协议。域字母固定为A=Cityscapes、B=ACDC-fog、C=ACDC-rain、D=ACDC-snow、E=ACDC-night。主序列A→B→C→D→E与MILE相同，只借用其顺序，不据跨骨干原表排名。
5. 本轮准备三个正式阶段，均不执行：
   阶段A：FT／原版GSMF／LwF-DIL各自从自己的Rain最终学生，seed 0续训D再续训E，共6次训练。
   阶段B：FT／原版GSMF的增量seed 1与2，从同一Source分别跑B→C→D→E，共16次训练；它同时承担第2项的关键重复。LwF与教师BN变体不进入阶段B。
   阶段C：FT／原版GSMF的seed 0，从同一Source跑顺序变化A→E→D→C→B，共8次训练。
   不新增模块、超参数搜索、teacher_bn_source_stats变体、其他分割器、正常参考图、合成天气训练或Source重训。

二、锁定祖先和父检查点

运行前重新计算SHA-256，检查路径和来源，不重新训练Source、Fog或Rain阶段。

共同Source（所有阶段、所有seed的祖先）：
experiments/road_clear_to_fog/formal-seed0-20261108-resume01/source/iter_60000.pth
a66c958ee774d27566b901ad6570c0a3b83263e9d74389e1c2e025c6c2673d93

seed 0的Fog学生（只作阶段A的历史祖先核对，不再训练）：
experiments/road_clear_to_fog/formal-seed0-20261108-resume01/ft/iter_4000.pth
99914df527d8506c33178ef6ea1caf7f0ed1d07369858e37275205d60a57d516
experiments/road_clear_to_fog/formal-seed0-20261108-resume01/gsmf/iter_4000.pth
fc227c57dc3e47a134ef51b282964654a0210f3c06f00bd0d3e81b706850b24a
experiments/road_lwf_bn/formal-seed0-plan-20261110-153000/lwf/iter_4000.pth
854d83357a912713a27cf27283b024f3e7fd7dab47043434d312b136ec9b6843

阶段A的Rain父检查点（SHA来自本地接收记录，现场重算后再用）：
experiments/road_clear_fog_rain/formal-seed0-plan-20261110-180543/ft/iter_4000.pth
ac04f676ed6ec53d6e8bf2267c5c06aad05e3db1537558e752cd7c98b8e68e34
experiments/road_clear_fog_rain/formal-seed0-plan-20261110-180543/gsmf/iter_4000.pth
754f53ec406b6efeac4ed9fb82364614b0fd9a9d603bd9298f35878a8f2a83f3
experiments/road_clear_fog_rain/formal-seed0-plan-20261110-180543/lwf/iter_4000.pth
f88ed8621d7fab8cfef1d6a91fb1991de60b4da649547bd625df06450d498527

每条链只继承同方法、同seed、同顺序的上一阶段学生；不能统一从原版GSMF、Source或其他seed的检查点开始。旧结果与本轮结果分别记录源码版本，不把当前HEAD当成旧训练的完整来源。

三、Snow(D)／Night(E)数据准备和隔离审计

1. 使用工程内已有归档data/road_raw/rgb_anon_trainvaltest.zip和gt_trainval.zip，无需重新下载。只选择rgb_anon/{snow,night}/{train,val}/下_rgb_anon.png及gt/{snow,night}/{train,val}/下_gt_labelTrainIds.png；必要时读取对应labelIds交叉核对。不提取test、*_ref参考图或其他天气。GT ZIP每帧有多种文件，不能把全部标签相关PNG当作图像数。2026-11-11按路径模式计数为snow 400／100、night 400／106；以实际配对结果为准，Night验证集不截断成100。
2. 新建独立解压目录，例如data/acdc_snow_step5_<唯一时间>和data/acdc_night_step5_<唯一时间>，不覆盖data/acdc、Rain目录或旧archive-provenance.json。最小扩展tools/road/extract_data.py的weather选项到snow／night，保留默认fog及已用rain的行为；或复用其安全解压函数。校验成员路径、CRC、解压长度及逐文件SHA，保存来源、选择规则和磁盘估计。不读取cookie／认证文件。
3. 建立按完整帧ID、split明确配对的D_train／D_val／E_train／E_val清单及独立debug清单。检查全部图像／标签可解码、同尺寸、三通道图像和单通道整数标签、trainIds只含0..18/255、19类顺序与既有完全一致。与B／C相同，只用labelTrainIds作语义标签，不重复映射，不按像素值猜encoding，不混用invIds、颜色标签或无效区域掩码；积雪路面等按ACDC原标注，不自行重标。
4. 统计D、E各自train／val的帧ID、RGB字节SHA重复和共同视频目录，以及与A／B／C既有训练、验证清单的帧／哈希重合；可再检查归一化解码图像哈希，逐项说明检查范围。发现相同RGB跨split等实质泄漏时先查明，不能自动删样本或重分官方划分来凑数。视频目录交叉单独披露；未独立核实地理隔离时明确标注。
5. A／B／C清单继续沿用旧记录与指纹，不重建出不同划分。每个增量阶段的训练dataloader只读当前域的train清单；所有val只用于定时验证或固定评价，不参与优化。未来域的提前评价不用于选超参数或挑checkpoint。
6. 新建本轮完整审计及manifest哈希，不向旧审计文件随意添加D／E。若关键数据缺失，先完成独立代码和转换准备，集中列出缺失；未经授权不进行大规模下载。

四、D／E域与通用阶段入口

1. 逐项处理road_dil/data.py的域检查、config.py的train_domain白名单、run.py的--train-domain／--domain choices与cfg_for重定位，以及本轮用到的审计、汇总和正式驱动。第3项的rain_formal.py、rain_results.py、rain_start.sh、rain_status.sh、rain_resume.sh等是三域专用；可以泛化，也可以另建第5项对应脚本，但旧A／B／C命令的默认行为必须保持不变。不能把D／E的文件改名为C、继续在报告里冒充Rain。
2. 阶段C的第一个增量域是E而不是B。核实Source→增量的转换和配置路径能接受任意增量train_domain，GSMF／LwF的教师仍为Source去掉辅助头后的状态；不能沿用把首个增量阶段硬编码为B的默认值。
3. 所有正式／debug／val dataloader解析后都检查实际manifest路径、record.domain和split，并写入运行记录。配置与manifest审计适配新的五域协议，不关闭旧数据门禁。

五、真实接通增量seed

1. 新增明确的--seed（或等价配置项），默认0以兼容旧命令。把它落实到cfg.randomness.seed、采样器seed、dataloader worker初始化、Python／NumPy／PyTorch随机源及invocation／resolved配置记录；deterministic设置沿用旧配置。不能只改目录名、日志标签或报告中的seed字样。
2. 用短运行验证：同一seed重复两次，前k个batch的样本ID、裁剪／翻转参数和首个loss一致（或在确定性限度内一致，如有cuDNN非确定性须说明）；seed 0与1的样本序列不同。核对新入口在seed 0时的配置diff与旧seed 0行为一致；若旧运行未记录样本序列，如实说明只能核对配置。
3. 所有seed都从同一个Source iter_60000出发，只改变增量随机性；同一条链的每个阶段使用同一个seed。明确记录这不覆盖Source训练的随机性。

六、严格初始化：Source→首个增量域，增量→增量

1. 首个增量阶段（阶段B的B域、阶段C的E域）沿用原Source转换：FT从Source单分支去掉辅助头；GSMF与LwF由Source去辅助头后同时得到教师和学生。保持旧convert的严格检查，禁止strict=False、随机分类头或静默丢键。
2. 后续阶段复用第3项已验证的convert-incremental：FT完整继承上一阶段单分支参数与全部缓冲；GSMF与LwF只取上一阶段部署学生backbone_1.*／decode_head_1.*，转换为新的教师backbone.*／decode_head.*，并逐值克隆为新学生。复制BN running_mean、running_var、num_batches_tracked等全部持久缓冲；丢弃上一阶段已过时的旧教师。
3. 每个目标键记录父checkpoint SHA、父键、目标键、形状及值哈希；检查完整键集合、19通道头和数值相等，教师与学生独立存储、无共享引用。eval模式下同一真实输入，新学生和新教师都与父部署学生输出等价，保存重载后再核对一次。
4. 每个新阶段都是新域初始化，不是resume：排除父optimizer／param_schedulers／iter，新建AdamW并从iter0开始4000步计划，把父运行、父域、新域、方法、seed、顺序、转换规则和SHA写入元信息。只有同一阶段运行中断时才恢复该阶段的优化器／调度器／迭代位置；必须拒绝用上一阶段的优化器状态作为resume。

七、方法语义保持

1. FT：全量更新，只用CE。
2. 原版GSMF：教师参数冻结，但原版训练态BN统计可更新、教师Dropout保持原行为；学生stem/layer1参数冻结、BN保留既有行为；损失为CE、输出Hin（T2／权重0.5）及特征KL（T1／权重1，idx[1,2,3]）。每阶段教师来自上一阶段自己的学生完整状态，不能固定在最初Source统计，也不能套用teacher_bn_source_stats变体。冻结梯度不等于冻结运行状态。
3. LwF-DIL：沿用第2项实现，教师eval/no_grad、全部参数和缓冲固定为上一阶段自己的学生快照；学生与FT部署结构相同、全量更新；只有CE和输出KD，没有特征KD。单次默认配置不代表最优LwF。
4. 不调损失。记录输出KD覆盖全原生stride4 logit像素（含ignore／padding）、无显式T²的实际实现，不因ignore_index参数就声称KD已屏蔽255。
5. 复用RoadAuditHook的差异化策略，在optimizer建立前确认requires_grad；分别检查参数、BN缓冲和模块train/eval标志，覆盖周期验证后model.train()、保存重载与resume后的教师策略。不删除原有冻结断言来迁就新阶段。推理始终只用部署学生，无天气oracle路由、无TTA、无测试时BN重估，参数和全部缓冲前后不变。

八、正式预算与评价计划（三个阶段各自确认后才执行）

1. 每个增量阶段：4000步，batch2，crop512，FP32，AdamW lr1e-5、betas(.9,.999)、wd.001，PolyLR power.9、end4000，每1000步在当前域val上验证并保存，固定iter_4000为主结果。增强沿用RandomResize(2048,1024)/ratio(.5,2)、RandomCrop cat_max_ratio.75、flip.5、PhotoMetricDistortion；其余以已完成Rain阶段resolved配置为准，列出实质差异。每域约400张训练图、约20轮曝光；不按短训或val表现增减某一方法或某一域的预算。
2. 评价条件共8个：Cityscapes val500晴天；同500场景三档Foggy（β=.005／.01／.02）各500；ACDC-fog val100、ACDC-rain val100、ACDC-snow val100、ACDC-night val106（以实际审计数为准）。合成条件沿用同一GT、同一场景清单、原生分辨率、ImageNet预处理、512滑窗/stride341、无TTA。debug名称不代表只有两张，完整评价必须按清单数及ID核对。
3. 阶段A：一个共同Source加三种方法各自Fog后、Rain后、Snow后、Night后，共13个检查点×8条件=104格。已有42格（7个检查点×6条件）在指纹与协议一致时复用；新增为7个旧检查点在D、E val的提前评价14格（1442图），以及6个新检查点×8条件48格（14436图），合计62格、15878次逐图评价。
4. 阶段B：每个seed、每种方法有Fog后、Rain后、Snow后、Night后4个新检查点，共16个。每个检查点评价五个真实域（CS500、fog100、rain100、snow100、night106），共80格、14496图；三档Foggy只评价Fog后和Night后检查点，共24格、12000图。合计104格、26496次逐图评价。共同Source的8格复用阶段A结果。
5. 阶段C：FT／GSMF各4个新检查点（E后、D后、C后、B后），每个评价五个真实域，共40格、7248图；最终B后检查点再评三档Foggy，共6格、3000图。合计46格、10248次。共同Source复用。
6. 按实际审核数量重新列算术。复用格仅在checkpoint SHA、manifest逐图ID／图像与标签指纹、标签规则、预处理、分支和指标协议一致时复用；每格记录reused／new及原证据路径与SHA。不能把复用格声称为本轮重新推理，也不能把未来域提前评价计入当时的已见域均值。
7. 指标：GT行／预测列，ignore255；全集累计混淆矩阵求IoU，union=0排除并写null，GT缺失而有预测时该类为0。新增格须独立重读保存的预测与原标签重建矩阵，核对GT直方图、尺寸和ID集合；不要平均逐图mIoU冒充全集mIoU。

九、结果定义与分析输出

1. 每种方法、每个seed、每个顺序输出阶段×真实域矩阵R[t,j]（Source加四个增量阶段×五个真实域），Source行共享并明确重复展示。已见域等权均值按阶段只含已学域；最终五真实域等权均值与合成条件分开报告，不算八条件混合总均值，不把同场景四个强度当作四个独立训练域。
2. 报告after-before差值（允许正负）：每个旧域在后续每次更新后的变化、相对共同Source的累积变化、新域相对上一阶段模型的适应增益。最终旧域遗忘F_j=max_{已学j且早于最终的阶段t} R[t,j]−R[final,j]，写清参照阶段并保留负值；不把最终新域的零项混入旧域均值。不报告需要随机初始化基线才能定义的FWT。
3. 阶段B完成后，对seed 0／1／2（seed 0来自既有两域、第3项及阶段A的FT／GSMF链）分别给出逐seed值、均值和样本标准差，以及同seed的GSMF−FT差值及其均值和标准差。明确n=3只检验固定Source下的增量随机性，不构成统计显著性证明。
4. 混淆去向追踪：对每个检查点的CS晴天矩阵，输出road真值像素被预测为各类的比例（前5项），terrain、truck、train、sky、building、fence、bicycle的预测面积／真值面积比、召回率及误报来源前3类，以及各类相对Source的mIoU下降贡献（ΔIoU/19）。另对ACDC各已学域输出同样的road去向。这用于检查“晴天道路被误判为地形／卡车／建筑”这类与方法无关的误判是否在后续域反复出现；只作描述，不作因果结论。
5. 固定样例：沿用severity的6个CS场景（frankfurt_000000_011074、frankfurt_000001_008688、frankfurt_000001_015328、frankfurt_000001_041074、frankfurt_000001_073911、lindau_000049_000019），保存新增检查点在CS晴天下的原始预测；Snow／Night在推理前按固定seed从审计后的val清单预选少量帧，所有方法、阶段和seed使用相同ID，不按效果挑图。全量预测留远程。

十、真实短运行与资源

1. 本轮真实数据调试最多64个优化步骤，三种方法、D／E两域、seed接通检查、阶段C首域E转换、失败尝试及resume验证合计；另建本轮锁定账本，不重置或借用旧100步／64步账本，不关闭budget.reserve。无优化的转换与推理检查单独计时。
2. 先做导入／标签检查和严格转换，再用少量真实D_train、E_train短训。至少覆盖：三种方法从Rain父模型进入D的有限loss／梯度、应冻结和应更新参数、教师和学生BN实际变化、19通道、严格保存重载；D→E的增量转换；FT／GSMF在seed 1下从Source进入B的转换与短训；阶段C从Source进入E的转换与短训；同一短运行中断后的优化器／调度器／iter恢复；seed可重复性与差异性检查。对五个真实域和三档Foggy各取小固定样本走实际评价入口。夹具检查不冒充真实数据检查，短训mIoU不作为正式效果。
3. 用短训实际吞吐、显存和小样本评价耗时，分别估计阶段A／B／C的训练、评价、checkpoint及预测占用，计入周期验证、I/O和安全余量。参考量级：第3项每次4000步训练14–16分钟，CS规模评价约5分钟、ACDC约1.2分钟；FT每个checkpoint约575MB、GSMF约765MB，每次训练4个。不把历史低负载速度当保证；现场检查WSL与宿主可用盘及其他GPU任务。
4. 为三个阶段分别建立tmux持久顺序入口、真实状态／退出码、状态查询和resume入口；一个阶段结束不得自动启动下一个阶段，不无限重试，不自动追加种子、天气或方法。保存resolved配置、代码diff、受影响训练源码完整快照及SHA（含未跟踪文件）、环境、数据／父权重／初始化指纹、命令和短运行证据；正式执行前可校验这些指纹未漂移。

十一、本轮停止条件与交付

完成可检查的PREPARED_PLAN／STATUS、D／E数据审计、seed接通证据、各类转换与真实短运行、兼容性检查、源码差异／指纹、资源估计后，用中文报告实际完成、未完成和阻塞。分阶段A／B／C给出唯一推荐的正式命令、输出目录、父子来源与SHA、训练次数和评价格清单。若有多个备选，先收敛为推荐的一套，不要求我批准含糊方案。

遵守根AGENTS.md“正式训练前报告并确认”：等我发送提示词二／三／四或明确确认相应阶段后，才进入正式训练和完整评价；旧实验授权不跨用到本项。阶段完成时更新远程REPRO.md当前道路状态，准确写“准备通过／正式未启动”，保留历史结果。
```

## 提示词二：确认后执行阶段A（seed 0续训Snow→Night）

在检查提示词一返回的实际方案后发送。若方案改变了4000步、数据、方法或评价格数，先在消息中写明最终选择。

```text
我确认上一轮第5项准备结果中阶段A的唯一正式方案，授权执行：FT／原版GSMF／LwF-DIL各自从自己的Rain最终学生严格初始化，seed 0，先在ACDC-snow训练集(D)训练4000步，再从各自Snow学生在ACDC-night训练集(E)训练4000步，共6次训练；并完成计划中的62个新增评价单元、104格汇总、独立指标核验和轻量交接。本次不重训Source／Fog／Rain，不执行阶段B或C，不追加种子、超参数搜索、新模块或合成训练。

1. 读取适用AGENTS.md、已确认的PREPARED_PLAN／STATUS、实现diff及真实短运行证据；核对实际配置、代码、环境、父权重、严格转换和数据指纹与确认时一致。通过后直接执行已授权范围，不反复询问；实质性协议漂移或失败须如实报告，不能悄悄放宽检查。
2. 正式从未经debug优化的初始化开始，不能用短训权重。每次训练新建优化器、iter0、固定4000步计划。GSMF和LwF的Snow教师来自各自Rain学生，Night教师来自各自Snow学生，完整继承参数和BN缓冲；GSMF保留原版训练态教师BN行为，LwF保持教师全部状态固定；推理只用学生。
3. 用已验证的tmux持久入口在单GPU上顺序运行：三种方法的Snow阶段完成并通过审计后，再运行各自的Night阶段。保留每1000步和固定iter4000的完整checkpoint及恢复状态，记录实际进程、loss、退出码、训练／验证／评价耗时和资源。先确认后台进程实际开始；启动不等于完成。失败即停止依赖阶段、保留现场，不无限重试、不挤占其他进程，不承诺未建立机制的持续监控。
4. 完成7个旧检查点在D／E val的提前评价14格，以及6个新检查点×8条件48格，共62格；旧42格按指纹／协议核对后复用。每格核对全量ID与数量、实际学生分支、完整checkpoint SHA和参数／缓冲前后不变；无天气ID路由、无TTA或测试时更新。训练期定时验证结果不冒充最终评价。
5. 从全量累计混淆矩阵计算mIoU／19类IoU，独立重读新增62格的预测和原始GT重建矩阵并核对GT直方图；核对复用格证据。按方案输出五域阶段矩阵、已见域均值、最终五真实域均值、after-before差值、旧域遗忘、合成强度表／曲线，以及第九节第4条的混淆去向追踪。保留负值，不声称单seed稳定或显著，不把跨库差异全部归因于天气，不声称严格未见强度泛化。
6. 保存固定CS样例与预先固定的Snow／Night样例原始预测及对齐图。生成独立轻量交接包：PLAN／STATUS／RESULTS／SUMMARY、真实完成与退出码证据、方法与配置、训练源码快照／diff与指纹、环境／命令、数据审计与父子转换报告、检查点与预测的远程索引、104格逐项来源与矩阵／逐类表、独立核验、图表、少量样例和资源记录。权重、原始数据、全量预测、环境和.git留远程，不打包cookie或认证文件。
7. 包名用<正式run-id>-light.tar.gz；包内MANIFEST.sha256覆盖除清单自身外的全部文件，包外另给同名.sha256。在新临时目录检查安全成员路径并实际解包，核对文件集合与哈希，避免把旧包递归打入新包。
8. 训练、全部评价、独立复核及包校验都完成后才标complete、更新远程REPRO.md；中断或缺格时准确记录部分完成。最后用中文报告五域主表、各旧域在Snow／Night更新后的变化、原版相对FT／LwF的观察、混淆去向是否重复出现、限制，以及包和SHA文件的绝对路径与使用home-wsl获取的scp命令。学校本地接收目录为C:\undergraduate_thesis\03_experiments\road_five_domain\<run_id>\，不要尝试在远程写入这个Windows路径。阶段B不自动启动。
```

若希望阶段A与B连续运行，可在提示词二末尾追加一句：“阶段A全部完成并通过独立核验与打包后，直接按提示词三执行阶段B。”否则审阅阶段A结果后再单独发送提示词三。

## 提示词三：阶段B（FT／GSMF的seed 1与2完整五域链）

```text
我确认第5项准备结果中阶段B的唯一正式方案，授权执行：FT与原版GSMF分别使用增量seed 1和2，从同一Source iter_60000（a66c958e…3d93）严格初始化，依次在ACDC-fog(B)、ACDC-rain(C)、ACDC-snow(D)、ACDC-night(E)训练集上各训练4000步，共16次训练；并完成计划中的104个新增评价单元、独立指标核验和轻量交接。本条不包含LwF-DIL、教师BN变体、Source重训、超参数搜索、阶段C或新模块。

1. 先读取适用AGENTS.md、PREPARED_PLAN／STATUS、seed接通证据和实现diff；核对配置、代码、数据和Source指纹未漂移。若阶段A已完成，核对其结果与复用的Source格；若阶段A未完成，不影响本阶段训练，但Source的8格复用须等其证据存在后再汇总。
2. seed必须真实作用于cfg.randomness、采样器、worker、Python／NumPy／PyTorch，并写入每次运行的invocation与resolved配置；不得只改目录名或标签。同一条链的四个阶段使用同一seed。每阶段新建优化器、iter0，只继承同方法、同seed上一阶段的学生；首阶段B按原Source转换，后续用convert-incremental。不重跑任何seed 0运行，不覆盖旧结果。
3. 用已验证的tmux持久入口在单GPU上顺序执行，建议顺序为seed1-FT、seed1-GSMF、seed2-FT、seed2-GSMF，每条链四个阶段依次完成；某阶段失败即停止该链的后续阶段并保留现场，其他链是否继续按方案中预先写明的规则处理，不临时改变。记录实际进程、loss、退出码、耗时和资源。
4. 每个新检查点评价五个真实域（CS500、fog100、rain100、snow100、night106），Fog后与Night后检查点再评价三档Foggy，共104格、26496次逐图（按实际清单重新核对）。继续逐预测独立复算矩阵、核对分支和参数／缓冲不变。
5. 报告seed 0／1／2的逐次结果、各条件均值与样本标准差、同seed的GSMF−FT差值及其均值和标准差、各阶段的已见域均值与旧域遗忘，以及第九节第4条的混淆去向追踪在三个seed间是否一致。其中Fog后与Rain后检查点即为两域、三域的关键重复，须单独列出并与既有seed 0结果对照。明确这只检验固定Source的增量随机性，n=3不证明统计显著，也不覆盖源训练随机性。
6. 按阶段A的轻量交接规范另行打包、生成MANIFEST与外置SHA、实际解包核验；本地接收目录为C:\undergraduate_thesis\03_experiments\road_five_domain\<run_id>\。全部完成后才标complete并更新远程REPRO.md，最后用中文报告结果、限制、包路径和home-wsl的scp命令。阶段C不自动启动。
```

## 提示词四：阶段C（顺序变化，审阅A／B后再发）

此条是独立后续授权，默认不随阶段A／B执行。顺序A→E→D→C→B是建议，审阅阶段A／B结果后可改为其他顺序，但须在消息中写明。

```text
我已审阅第5项阶段A／B结果，授权执行阶段C：FT与原版GSMF的seed 0，从同一Source iter_60000严格初始化，按顺序ACDC-night(E)→ACDC-snow(D)→ACDC-rain(C)→ACDC-fog(B)各训练4000步，共8次训练；并完成计划中的46个新增评价单元、独立指标核验和轻量交接。不含LwF、其他种子、超参数搜索或新模块。

首阶段E按原Source转换，GSMF的教师与学生均为Source去辅助头后的状态，不能沿用首个增量域硬编码为B的默认值；后续阶段用convert-incremental继承同方法上一阶段学生。每阶段新优化器、iter0、固定4000步，seed 0真实生效。每个新检查点评价五个真实域，最终B后检查点再评价三档Foggy；共同Source格复用。按已有规范独立复算矩阵、核对分支与状态。

报告顺序变化下的阶段×真实域矩阵、最终五真实域均值、各域在学完后的变化与旧域遗忘，并与主序列A→B→C→D→E的seed 0结果逐项对照（同一域在两种顺序中所处位置不同，须写明比较的是哪个阶段）。只描述单seed下的顺序敏感性，不据此给出稳定排名。按已有轻量交接规范打包、校验，给出本地接收目录C:\undergraduate_thesis\03_experiments\road_five_domain\<run_id>\和home-wsl的scp命令。
```

## 提示词五：换会话后恢复或核查进度

```text
请恢复本工程experiments/road_five_domain下最近一次第5项任务。先读AGENTS.md、REPRO.md、该轮PREPARED_PLAN／STATUS及authorization证据，明确运行ID、所属阶段（准备／A／B／C）和剩余任务；核对实际tmux／进程、日志、退出码和checkpoint，不仅依赖“running”文字。若有多个无法区分的正式运行，列出差异后再定位，不随便新建一条链。

不要重复启动仍在运行的进程，不从头重训已完成的阶段，不覆盖checkpoint／预测，不重跑已核验完成的评价单元，不把准备阶段授权扩为正式训练授权，也不把某一阶段的授权扩到其他阶段。未完成的训练只从同方法、同seed、同顺序、同域、同一运行中最后可读的完整checkpoint恢复模型／优化器／调度器／迭代位置；目标仍是该阶段总4000步，不是再加4000步。不能用上一阶段的checkpoint做resume，也不能重新转换教师导致丢失本阶段训练状态。检查原版GSMF／LwF各自的冻结与教师BN策略以及seed记录。

无法精确恢复RNG或采样游标时如实披露，不宣称与不停机逐位一致；权重损坏或缺关键状态时保留现场并说明。调试修复使用剩余独立账本，不重置预算或无限重试。按已有授权继续剩余训练／评价／独立核验／图表和轻量包，严格区分复用、已完成、新补及缺失；全部检查通过才标complete。最后用中文报告恢复点、实际补做内容、限制和最终包路径。
```

## 提示词六（可选）：GSMF学生冻结模块BN统计的零训练评价诊断

不训练、不改检查点文件，可在阶段A之前或之后独立发送。它不是新方法，只用来区分CS晴天下降中浅层BN统计漂移的贡献；第2项测试的是训练时的教师BN，与此不同。

```text
请在 /home/ysheng4/research/GSMF-RS-DIL 中做一项只评价、不训练的诊断，命名为eval_probe_student_frozen_bn_source_stats，新建独立目录experiments/road_five_domain/probe-bn-<唯一时间>。

1. 对象为原版GSMF的seed 0检查点：Fog后experiments/road_clear_to_fog/formal-seed0-20261108-resume01/gsmf/iter_4000.pth（fc227c57…0b24a）和Rain后experiments/road_clear_fog_rain/formal-seed0-plan-20261110-180543/gsmf/iter_4000.pth（754f53ec…a83f3）；若阶段A已完成，再加其Snow后与Night后GSMF检查点。参照Source为experiments/road_clear_to_fog/formal-seed0-20261108-resume01/source/iter_60000.pth（a66c958e…3d93）。运行前重算全部SHA。
2. 依据原版冻结策略和实际requires_grad审计，确定学生backbone_1中参数被冻结的模块（预期为stem与layer1）。先核对这些模块的参数与Source对应backbone参数逐值相等；若不相等，停止并报告，不继续替换。
3. 只在内存中把这些冻结模块的BN running_mean与running_var替换为Source对应值，其余全部参数和缓冲保持原样；不覆盖原检查点。记录被替换的键、数量和替换前后差异的统计，并核对其他张量逐值不变。
4. 用既有评价入口、学生分支、512滑窗/stride341、无TTA，在CS val500晴天以及该检查点已学过的每个ACDC域val上评价替换后的模型；原模型对应格复用既有结果。按既有规则保存累计混淆矩阵并独立复算。
5. 报告替换前后的mIoU、19类IoU变化、CS上road真值被预测为terrain／building等的比例变化，以及已学ACDC域上的代价。只作诊断描述：不能据此宣称BN统计是遗忘的唯一原因，也不把这一替换本身当作改进方法。生成小型轻量包与SHA，给出home-wsl的scp命令；本地接收目录为C:\undergraduate_thesis\03_experiments\road_five_domain\<run_id>\。
```

## 本地接收时的核验重点

回传包放入`03_experiments/road_five_domain/<正式run-id>/`后，先核对归档SHA及安全成员路径，再在新目录解包、核对MANIFEST。阶段A重点核对六次训练的父子来源（Rain→Snow→Night）、D／E数据审计与Night实际验证数、62新／42复用格的来源和阶段均值；阶段B重点核对seed是否真实生效（invocation、resolved配置与样本序列证据），以及16个检查点的同seed父子链；阶段C核对首域E的Source转换。复算全部新增矩阵，并用本地[analyze_cs_confusion_shift.py](../../03_experiments/road_clear_fog_rain/analyze_cs_confusion_shift.py)的同一口径对照混淆去向。只有取得实际结果证据后才登记第5项相应阶段完成；本文件本身只是任务交接成果。
