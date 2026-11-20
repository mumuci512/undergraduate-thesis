# 第3项：真实三域链式基线——远程Codex任务

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: plan（远程执行任务交接）
- Origin Date / Last Updated: 2026-11-10
- Verification Status: 已通过SSH只读核查工程、Rain ZIP目录配对及四份检查点SHA；尚未解压Rain、修改训练代码、短训或开展第三域正式实验。
- Version Label: road_clear_fog_rain_seed0_v1

## 使用范围与现场依据

工程：`/home/ysheng4/research/GSMF-RS-DIL`，SSH别名：`home-wsl`。本文件给远程Codex使用；不要假设本地论文目录也在远程。

本轮推进 **Cityscapes→ACDC-fog→ACDC-rain**，沿用FT、原版GSMF、LwF-DIL三条链。先完成准备与真实短运行，再按用户确认的方案正式执行。Snow／Night、更换架构、新模块、重复种子和受控合成训练均不包含在本轮；三档Foggy继续作为固定评价条件。严格未见强度泛化若成为主目标，再另建受控合成训练／留出强度支路，不能由本轮结果替代。

2026-11-10 SSH核查结果：

- Git HEAD为`a93b90c76f13733920f824a03e21020dee08430c`，当次`git status --short`为空。它是当前工程状态，不替代旧训练各自的源码指纹。执行时重新核对，不重置后来出现的改动。
- 根`AGENTS.md`规定：“启动耗时的正式训练前，先向用户报告实验方案并取得确认。”因此提示词一完成可检查的准备，提示词二才授权正式训练。本轮用户请求准备提示词不等于已确认最终正式预算。
- 现有`data/acdc`只解压了fog。`data/road_raw/rgb_anon_trainvaltest.zip`已有rain训练400张、验证100张RGB；`gt_trainval.zip`有对应400／100张`_gt_labelTrainIds.png`。ZIP内按完整帧ID一一配对，无缺失，train／val帧ID无交集；尚未逐像素、逐文件哈希核验Rain。
- Rain官方train／val存在五个共同视频目录：`GOPR0400`、`GOPR0402`、`GP010400`、`GP020402`、`GP030400`。沿用官方划分并披露，不据目录交叉直接认定图像重复，也不能声称已证明视频／地理独立。
- `tools/road/run.py`已支持方法stage `source/ft/gsmf/lwf/gsmf_teacher_bn`，但训练工厂仍将所有增量阶段指向B，评价参数只接受A/B；`road_dil/data.py`也只接受A/B。`road_dil/checkpoints.convert`仍要求带辅助头的Source，不能直接转换已训双分支Fog模型。
- 已完成的第2项在`experiments/road_lwf_bn/formal-seed0-plan-20261110-153000`。不要重跑提示词一／二对应的旧实验；教师BN负结果变体本轮不扩展。

### 发给远程Codex的第一句话

```text
请读取 /home/ysheng4/research/GSMF-RS-DIL/STEP3_RAIN_CHAIN_REMOTE_TASK_20261110.md，完整执行其中“提示词一”的代码框任务：准备Cityscapes→ACDC-fog→ACDC-rain的FT／原版GSMF／LwF-DIL三域链、数据审计、真实短运行和唯一正式方案。复用已有Fog最终权重，不重训旧阶段；本轮停止在准备完成，暂不执行提示词二的正式训练。
```

## 提示词一：实现第三域链路、审计数据、完成短运行

```text
请在 /home/ysheng4/research/GSMF-RS-DIL 中，实际完成第3项真实三域链式基线的执行准备：Cityscapes(A)→ACDC-fog(B)→ACDC-rain(C)，方法为FT、原版GSMF、LwF-DIL。完成必要代码、数据、严格转换、真实短运行、可执行正式入口及唯一正式方案；本轮不启动4000步正式训练，也不提前跑完整22个新增正式评价单元。

一、恢复现场与范围

1. 读取适用AGENTS.md、REPRO.md当前道路段落，以及下述旧实验的PLAN／STATUS／RESULTS及必要源码。先核查实际Git HEAD／工作区、Python环境、GPU进程及磁盘，不把历史文档的running当作实际状态。保留所有既有改动／结果，不提交或推送Git，不升级环境，不终止别人的进程。
2. 环境Python为 /home/ysheng4/miniconda3/envs/GSMF_RS_DIL/bin/python；历史为Python3.8.20、PyTorch1.9.1+cu111、MMCV2.0.0、MMEngine0.8.2、MMSeg1.2.1、RTX3080 20GB，现场核对后复用。缺rg用Python／grep，不为此安装软件。
3. 旧两域正式目录：experiments/road_clear_to_fog/formal-seed0-20261108-resume01。旧强度评价：experiments/road_fog_severity/eval-final-seed0-20261109-182100。LwF正式目录：experiments/road_lwf_bn/formal-seed0-plan-20261110-153000。这些目录只读复用；本轮新增独立experiments/road_clear_fog_rain/prepare-seed0-<唯一时间>，正式目录另建。
4. 任务是阶段边界已知、固定19类、完整监督、无旧图训练回放的三域工程和现象验证。推理所有天气只用当前部署学生，不提供真实天气ID选分支；域ID只用于数据与统计。本轮原型不自动确定论文最终边界协议。不新增Snow／Night、seed1/2、调参、模块、其他分割器、正常参考图或合成天气训练。

二、锁定祖先和各方法自己的父检查点

运行前重新计算SHA-256，检查路径和来源，不重新训练Source或任何Fog阶段。

共同Source，仅作固定参考和祖先核对：
experiments/road_clear_to_fog/formal-seed0-20261108-resume01/source/iter_60000.pth
a66c958ee774d27566b901ad6570c0a3b83263e9d74389e1c2e025c6c2673d93

FT的Fog父检查点：
experiments/road_clear_to_fog/formal-seed0-20261108-resume01/ft/iter_4000.pth
99914df527d8506c33178ef6ea1caf7f0ed1d07369858e37275205d60a57d516

原版GSMF的Fog父检查点：
experiments/road_clear_to_fog/formal-seed0-20261108-resume01/gsmf/iter_4000.pth
fc227c57dc3e47a134ef51b282964654a0210f3c06f00bd0d3e81b706850b24a

LwF-DIL的Fog父检查点：
experiments/road_lwf_bn/formal-seed0-plan-20261110-153000/lwf/iter_4000.pth
854d83357a912713a27cf27283b024f3e7fd7dab47043434d312b136ec9b6843

三条链各自继承自己的Fog学生，不能统一从原版GSMF或Source重新开始Rain。旧结果与本轮结果分别记录源码版本，不把当前HEAD当成旧训练完整来源。

三、Rain数据准备和隔离审计

1. 优先使用工程内已有合法归档data/road_raw/rgb_anon_trainvaltest.zip和gt_trainval.zip，无需重新下载。只选择rgb_anon/rain/{train,val}/下_rgb_anon.png及gt/rain/{train,val}/下_gt_labelTrainIds.png；必要时读取对应labelIds交叉核对。不要提取test、normal参考图或其他天气。GT ZIP每帧有五种文件，不能把2000／500个标签相关PNG当作2000／500张训练／验证图像。
2. 选择新的独立解压目录，例如data/acdc_rain_step3_<唯一时间>，不覆盖data/acdc及旧archive-provenance.json。可最小扩展tools/road/extract_data.py的weather选择，保留旧默认fog行为，或复用其安全解压函数；其现有acdc选择条件硬编码fog，不能原样调用后冒充已提取Rain。校验归档成员路径、CRC、解压长度及逐文件SHA，保存来源、选择规则和磁盘估计。归档旧SHA可在data/acdc/archive-provenance.json定位，使用前核对；不读取cookie／认证文件。
3. 建立按完整帧ID、split明确配对的C_train.jsonl／C_val.jsonl，预计400／100，另有独立debug清单。检查全部图像／标签可解码、同尺寸、三通道图像和单通道整数标签、trainIds只含0..18/255、19类顺序与既有完全一致。trainIds不重复映射，不按像素取值猜encoding，不混用invIds、颜色标签和无效区域掩码作为语义标签。
4. 统计C训练／验证帧ID、RGB字节SHA重复、共同视频目录，以及与A/B既有训练和验证清单的帧／哈希重合；可检查归一化解码图像哈希，逐项说明检查范围。发现相同RGB却split不同等实质泄漏时先查明，不能自动删样本／重分官方划分来凑400／100。视频目录交叉单独披露，未独立核实地理隔离时明确标注。
5. A_train/A_val继续2975/500，B_train/B_val继续400/100；复用旧记录与指纹，不重建出不同划分。本轮Rain训练dataloader只读C_train，不能加载A_train/B_train、正常参考或Foggy训练图。A/B/C的val只供固定验证／评价，不参与优化；未来Rain的提前评价不用于反复选超参数或挑checkpoint。
6. 新建本轮完整审计及manifest哈希，不向旧两域audit.json随意添加C，也不仅把full_official_counts改成true跳过实际检查。若关键数据缺失，先完成独立代码和转换准备，集中列出缺失；无授权不执行大规模下载。

四、增量到增量的严格初始化——本轮核心

1. 先读road_dil/checkpoints.py、models.py、hooks.py及原DIL模型实际state_dict和部署路径。旧convert校验Source辅助头，再去掉它；Fog FT本已无辅助头，Fog双分支也不是Source结构。新增明确的incremental→incremental转换入口或参数，保持旧Source转换默认兼容。禁止用strict=False、随机分类头或静默丢键掩盖差异。
2. FT：取自己Fog最终模型的完整单分支backbone／decode_head参数与全部缓冲，严格初始化Rain单分支。没有教师、不增加辅助头，保持FT更新范围与CE。
3. GSMF与LwF：只取各自Fog检查点当前部署学生backbone_1.*／decode_head_1.*，转换成Rain旧教师backbone.*／decode_head.*，同时逐值克隆为Rain新学生backbone_1.*／decode_head_1.*。必须复制BN running_mean、running_var、num_batches_tracked及其他持久缓冲；丢弃Fog检查点内已经过时的backbone／decode_head教师，不把该旧教师当成已整合Fog的模型。
4. 每个目标键记录父checkpoint SHA、父键、目标键、形状、值／张量哈希；严格检查完整键集合、形状、19通道头、全部值相等，报告所有有意排除的键。历史部署单分支为698个state张量，双分支1396个，用实际构建核验，不只断言数量。新的教师与学生初始化数值相等，但采用独立存储，检查无共享参数／缓冲引用，防止训练学生时改动教师。
5. eval模式同一真实输入下，转换后部署学生应与转换前父模型部署输出等价；新教师也应与该父学生等价。比较的是确定性eval输出，不能要求GSMF训练态Dropout／BN下数值仍相同。记录最大误差及合理容差，保存重载后重复核对。
6. 这次是新域初始化，不是Fog训练resume。排除父optimizer／param_schedulers／旧iter等训练状态，为Rain从iter0新建AdamW及4000步计划。把父运行、父域B、新域C、方法、转换规则和SHA写入元信息与运行provenance。只有同一Rain运行中断时才恢复Rain优化器／调度器／迭代位置；必须拒绝用Fog优化器状态作为Rain resume，即使架构键完全相同。

五、C域入口与方法语义保持

1. 逐项处理road_dil/data.py的A/B检查、config.py增量train_domain='B'、run.py的cfg_for文件名重定位和eval --domain A/B限制，以及本轮用到的审计／汇总／正式驱动。方法身份与训练域分开表达，例如显式train_domain=C和eval_domain=C，不能只把C文件改名B、继续在报告中冒充Fog。本轮源码最小扩展，旧A/B命令默认不变。
2. 所有正式／debug／val dataloader解析后都检查实际manifest路径、record.domain和split；确认Rain优化用C_train，训练期定时验证用C_val，最终分别评价A/B/C。配置与manifest审计适配新的三域协议，不关闭旧数据门禁。CLI参数／配置的seed0必须落实到随机初始化、数据采样和增强，不能只有报告里写seed0；本轮不为未授权重复提前跑其他种子。
3. 原版GSMF沿用既有冻结、损失和训练模式：教师参数冻结，但原版训练态BN统计可更新、教师Dropout仍按原行为；学生stem/layer1参数冻结，学生BN保留既有行为。Rain教师从自己的Fog学生完整状态开始，不能继续固定在最初Source统计，也不能套用负结果teacher_bn_source_stats变体。冻结梯度不等于冻结运行状态。
4. LwF沿用第2项已实现RoadDIL固定教师eval/no_grad，Rain全程教师参数和缓冲不变；此时固定的是自己的Fog学生快照，不是最初Source。学生与FT部署架构相同并按既有LwF允许全量更新；只CE及输出KD，无额外特征KD。
5. 不调损失。核对现有CE权重1、输出Hin温度2/权重0.5，全原生stride4 logit像素含ignore/padding、无显式T²的已有实现；原版GSMF另有特征KL(T1/权重1、idx[1,2,3])，LwF没有它。记录实际归约，不因ignore_index参数就声称KD已屏蔽255；CE维持原配置。LwF只是固定19类道路适配对照，单次默认配置不代表最优LwF。
6. 复用RoadAuditHook已有差异化策略，检查requires_grad在optimizer建立前正确；分别核实参数、BN缓冲和模块train/eval标志。覆盖周期验证后model.train()、保存重载及resume后的教师策略，不删除原有冻结断言来迁就新方法。推理始终只用部署学生，无天气oracle路由、无TTA、无测试时BN重估，参数和全部缓冲不变。

六、真实短运行及拟正式资源

1. 本轮真实数据调试最多64个优化步骤，三种方法、失败尝试及resume验证合计，另建本轮锁定账本；不重置、借用旧100步／64步账本，不关闭budget.reserve。无优化的转换／推理检查单列时间。优先三组各少量真实Rain步骤，留足保存／resume预算，无需耗尽额度。
2. 先做导入／标签检查和严格转换，再用少量真实C_train短训。覆盖三组有限loss／梯度、应冻结和应更新参数、教师和学生BN实际变化、19通道、严格保存重载；三组均验证新阶段优化器起点与同一Rain短运行的resume。比较转换前后父学生输出；对A/B/C和三档Foggy的小固定样本走实际评价入口。夹具通过不冒充真实检查，短训mIoU不作为正式效果。
3. 拟正式为FT／原版GSMF／LwF各seed0、Rain4000步，batch2、crop512、FP32、AdamW lr1e-5/betas(.9,.999)/wd.001、PolyLR power.9/end4000、每1000步验证和保存、固定iter4000为主结果。增强沿用RandomResize(2048,1024)/ratio(.5,2)、RandomCrop cat_max_ratio.75、flip.5、PhotoMetricDistortion；其余以已完成Fog增量resolved配置为准，列出实质差异。Rain400张时约20轮曝光，不以短训或val效果临时增减某一方法预算。
4. 用短训实际吞吐、显存和小样本评价耗时，估计三组12000步、22个新增完整评价单元、全部checkpoint／预测占用；计入周期验证、I/O与安全余量，不把历史低负载速度当保证。现场检查WSL／宿主可用盘及其他GPU任务。
5. 复用现有顺序驱动／tmux／退出码／状态和独立核验设施，建立本轮正式启动、状态查询和resume入口。保存实际resolved配置、代码diff、受影响训练源码完整快照及SHA（包含未跟踪文件）、环境、数据／父权重／初始化指纹、命令和短运行证据。正式执行前可验证这些指纹未漂移。

七、正式评价计划——复用20格，新增22格

1. 每个固定检查点评价六个条件：Cityscapes val晴天500、三档同500场景Foggy(β=.005/.01/.02)各500、ACDC-fog val100、ACDC-rain val100。合成四条件仍用同一GT、同一场景清单、原生分辨率、ImageNet预处理、512滑窗/stride341、无TTA；debug名称不代表只有两张，完整评价必须按清单数及ID核对。
2. 共七个不同检查点：一个共同Source；三种方法各自Fog后；三种方法各自Rain后。七个×六条件=42格。已有Source及三种Fog模型的五条件共20格可核对后复用（12格来自severity、FT/GSMF的ACDC两格及Source的ACDC一格来自旧两域、LwF五格来自第2项）；不加入教师BN变体，不重复计共同Source。
3. 新增为四个旧模型在Rain val的提前评价4格，以及三个Rain后模型×六条件18格，总22格。预计新增逐图评价4×100+3×(500×4+100+100)=7000次。按实际审核数量重新列算术；不能把42格都声称本轮新跑，也不能把4格未来域提前评价计入当时已见域均值。
4. 旧20格仅在checkpoint SHA、manifest逐图ID／图像与标签指纹、标签规则、预处理、分支和指标协议一致时复用。为每格记录reused/new及原证据路径／SHA；保存每格累计19×19混淆矩阵、逐类IoU、全量样本数和有效像素。证据不够先查原始产物，不默默重跑全部旧模型或拼接不兼容结果。
5. 指标：GT行／预测列，ignore255；全集累计矩阵求IoU，union=0排除并写null，GT缺失而有预测为0。独立重读保存的预测与原标签重建新增22格矩阵，核对GT直方图、尺寸、ID集合和指标；旧格复核保存矩阵及来源，不平均逐图mIoU。
6. 输出每种方法的Source／Fog后／Rain后×CS／Fog／Rain真实域矩阵；Source行共享并明确重复展示。已见域等权均值按阶段分别只含A、A/B、A/B/C；最终三真实域等权均值与合成条件分开，不算六条件混合总均值，不把同场景四强度当四个独立训练域。另报Rain后相对Fog后的CS与Fog差值、CS相对共同Source累积差值、Rain后相对各自Fog模型的Rain适应增益，以及三档固定合成条件变化；差值统一after-before，允许正负，不预设遗忘单调。
7. 可附最终旧域遗忘F_j=max_{已学该域且早于最终的阶段} R[t,j]-R[Rain后,j]，j为CS/Fog。写清参照阶段并保留负值；不把最终新域Rain的零项混进旧域遗忘均值，不把未学域分数当历史已学峰值。不报告需尚未运行的随机任务基线才能定义的FWT。
8. 固定样例继续沿用severity既有6场景及选择证据，三个Rain后模型×四个CS条件×6=72份新原始预测，可制对齐图。Rain另在推理前从审计C_val按固定seed预选少量帧，所有方法／阶段使用相同ID，不挑看起来最好的图。全量预测留远程，轻量包只含少量样例、图、矩阵和索引。

八、本轮停止条件与交付

完成可检查的PREPARED_PLAN／STATUS、数据审计、三组转换与真实短运行、兼容性检查、源码差异／指纹、资源估计、唯一正式命令及恢复说明后，用中文报告实际完成、未完成和阻塞。给出正式输出目录、三份初始化SHA、三条父子来源、预算与22格评价清单。若有多个备选，先收敛为推荐的一套，不要求我批准含糊方案。

遵守根AGENTS.md“正式训练前报告并确认”：等我发送提示词二或明确确认该方案后，才进入正式训练和完整评价；旧实验授权不跨用到第三域。阶段完成时更新远程REPRO.md当前道路状态，准确写“准备通过／正式未启动”，保留历史结果，不把提示词当实际完成证据。
```

## 提示词二：确认具体方案后，正式训练、评价与交接

先查看提示词一返回的实际方案与证据，再发以下内容。若实际方案改变4000步、数据或方法，先把最终选择写清，不能原样确认一个不一致方案。

```text
我确认上一轮第3项准备结果中的唯一正式方案，授权执行Cityscapes→ACDC-fog→ACDC-rain三域链：FT／原版GSMF／LwF-DIL各自从自己的Fog最终学生严格初始化，只在Rain训练400张上各seed0、4000步；并完成计划中的22个新增完整评价单元、42格汇总、独立指标核验和轻量交接。本次不重训Source／Fog，不追加其他天气、种子、超参数搜索、新模块或合成训练。

1. 读取适用AGENTS.md、已确认PREPARED_PLAN／STATUS、实现diff及真实短运行证据；核对实际配置、代码、环境、父权重、严格转换和数据指纹与确认时一致。通过后直接执行已授权范围，不反复询问。实质性协议漂移或失败须如实报告，不能悄悄放宽检查。
2. 正式从三份未经过debug优化的Rain初始化开始，不能用短训最终权重。三组分别新优化器、iter0、固定4000计划；GSMF和LwF的Rain教师来自各自Fog学生，完整继承参数和BN缓冲。GSMF保留原版训练态教师BN行为，LwF保持该Fog教师全部状态固定；推理仅学生。
3. 用已验证tmux持久顺序入口执行三组，在单GPU顺序运行训练及评价，保留每1000步和固定iter4000完整checkpoint及恢复状态，记录实际进程、loss、退出码、训练／验证／评价耗时及资源。先验证后台进程实际开始；启动不等于完成。失败停止依赖阶段、保留现场，不无限重试、不挤占其他进程。保持真实状态记录，不承诺未建立机制的持续监控。
4. 完成四个旧模型的Rain val评价，以及三个Rain后模型的六条件评价，总22格／预计7000次逐图。旧20格按指纹／协议核对后复用，七个唯一检查点六条件汇总42格。每格核对全量ID与数量、实际学生分支、完整checkpoint SHA和参数／缓冲前后不变；无天气ID路由、无TTA／测试更新。定时验证的结果不冒充六条件最终完整评价。
5. 从全量累计混淆矩阵计算mIoU／19类IoU，并独立重读新增22格预测和原始GT重建矩阵及GT直方图；核对复用格证据。输出真实域阶段矩阵、已见域均值、最终三域均值、定义明确的旧域遗忘／适应差值，以及独立的合成强度表／曲线，不计算混合六条件总均值。保留负值，不声称单seed稳定显著，不把跨库差异都归因于天气，也不声称严格未见强度泛化。
6. 保存72份固定CS样例新原始预测及预先固定Rain样例／对齐图，记录选择规则。正式结果包包括：最终PLAN／STATUS／RESULTS、真实完成和退出码证据、方法与配置、实际训练源码快照／diff与指纹、环境／命令、数据与严格父子转换报告、七个检查点与预测的远程索引、42格逐项来源与矩阵／逐类表、独立核验、图表、少量样例、资源和恢复限制。权重、原始数据、全量预测留远程，不打包cookie／认证文件或整个环境。
7. 使用唯一包名如<正式run-id>-light.tar.gz；包内MANIFEST记录文件集合和SHA，包外另给归档SHA。在新临时目录检查安全成员路径并实际解包，核对文件集合／哈希，无递归把旧归档和新包打入自身。报告远程绝对路径和本地建议接收目录03_experiments/road_clear_fog_rain/<正式run-id>/。
8. 完成训练、全部评价、独立复核及包校验后才标complete、更新远程REPRO.md；中断或缺格则准确记录部分完成。最终中文报告三域主表、Fog在后续更新后的变化、原版相对FT/LwF的观察、合成条件变化、限制和包路径。下一阶段更长天气序列仅给依据与建议，本轮不自动启动。
```

## 提示词三：中断后检查现场并续作

仅用于已经用提示词二授权的同一正式运行。没有正式授权记录时，只能恢复准备工作。

```text
请恢复本轮已授权的第3项Cityscapes→ACDC-fog→ACDC-rain实验。先读取适用AGENTS.md、REPRO.md、本轮唯一正式运行的PLAN／STATUS／授权记录／指纹及实际进程和日志，明确运行ID与剩余任务；若有多个无法区分的正式运行，列出差异后再定位，不随便新建一条链。

不要重复启动仍在运行的进程，不从头重训完成的组，不覆盖checkpoint／预测，不重跑已核验完成的评价单元。未完成的Rain训练只从同方法、同域C、同运行中最后可读完整checkpoint恢复模型／优化器／调度器／迭代位置；目标仍为该组总4000步，不是再加4000步。不要使用Fog checkpoint做resume，或重新转换教师导致丢失Rain训练状态。明确检查原版GSMF／LwF各自的冻结和教师BN策略。

无法精确恢复RNG／数据游标时披露限制，不宣称与不停机逐位一致；权重损坏或恢复缺关键状态时保留现场并说明，不擅自切换父模型、只恢复权重后伪称完整resume。调试修复使用剩余独立账本，不重置预算或无限重试。

按已有授权继续完成剩余训练／22格新增评价／42格来源汇总／独立核验／图表和轻量包，严格区分复用、已完成、新补及缺失。全部检查通过才标complete。不要扩到Snow／Night、其他种子或新方法，最后用中文报告恢复点、实际补做内容、限制和最终包路径。
```

## 本地接收时的核验重点

回传包放入`03_experiments/road_clear_fog_rain/<正式run-id>/`后，先核对归档SHA及安全成员路径，再在新目录解包、核对MANIFEST。复算42格矩阵指标，重点核对三份Fog父检查点及学生→教师／新学生的完整参数与BN复制、C域训练来源、22新／20复用的出处和阶段均值。只有取得实际结果证据后才登记第三域完成；本文件本身是任务交接成果。
