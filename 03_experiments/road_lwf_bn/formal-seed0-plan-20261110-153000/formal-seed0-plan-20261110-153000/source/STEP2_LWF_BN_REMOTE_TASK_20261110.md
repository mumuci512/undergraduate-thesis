# 第2项远程任务：LwF对照、教师BN诊断与后续重复

编写日期：2026-11-10（Asia/Shanghai）。本文件依据通过`home-wsl`对远程工程的实际只读核查编写，不要求远程能读取学校论文目录。此次未修改远程源码、数据或实验，未启动训练或Codex任务。

## 已核查的现场与使用方式

- SSH别名：`home-wsl`；项目：`/home/ysheng4/research/GSMF-RS-DIL`；训练环境：`/home/ysheng4/miniconda3/envs/GSMF_RS_DIL`。
- 远程当前HEAD：`315f273929c09ffa991a1f1d6f95e304641386ce`；工作区有`REPRO.md`修改和未跟踪`handoff_exports/`，本次均未改动。
- 已读取根`AGENTS.md`及相关代码目录；未发现这些目录下的额外`AGENTS.md`。该文件SHA-256为`ba20032b3c1c63bd68f082b4db151c59cfc3ebb23e1822786bddad3e613bc029`。
- 远程规则明确要求：**“完整训练前先通过小规模验证确认代码正确。”及“启动耗时的正式训练前，先向用户报告实验方案并取得确认。”** 因此先发送提示词一，拿到具体实现、短运行证据和正式方案后，再发送提示词二；没有因本地准备提示词而授权远程正式训练。
- 现有`tools/road/run.py`、`road_dil/config.py`及`road_dil/checkpoints.py`只支持`source/ft/gsmf`；不是现成的`--stage lwf`命令。`road_dil/hooks.py`对带`backbone_1`的模型硬编码学生浅层冻结检查；新对照须按实际更新策略检查，不能删除全部审计。
- `DIL_EncoderDecoder.loss()`已有`DIL_type == 'LwF'`分支；`DIL_HinLoss`已实现温度soft cross-entropy，现有GSMF输出蒸馏T=2、权重0.5。这个接口尚不等于道路LwF实验已完成，也不能仅改变`DIL_type`就声称已得到常规LwF对照。
- `road_dil/budget.py`支持独立账本路径，默认仍指向首轮100步账本；本轮需要独立调试额度。远端没有`rg`，可用Python或`grep`，不必因此安装工具或升级环境。
- 已实算Source／FT／GSMF三个最终权重SHA，与本地接收记录一致。GPU查询为RTX 3080、20GB；当时没有tmux server。这只是一次现场快照，实际运行前仍须复查负载。
- 远程`/snap/bin/codex`为`codex-cli 0.114.0`，`codex exec --help`可用；该CLI的`codex login status`返回`Not logged in`。这不代表VS Code扩展没有登录。当前可通过SSH直接操作工程，但尚未通过CLI调度另一个Codex，也未接管任何已有聊天。

可直接复制下方相应代码框到现有远程Codex。也可在本地PowerShell传文件：

```powershell
scp 'C:\undergraduate_thesis\02_baselines\GSMF-RS-DIL\STEP2_LWF_BN_REMOTE_TASK_20261110.md' 'home-wsl:/home/ysheng4/research/GSMF-RS-DIL/STEP2_LWF_BN_REMOTE_TASK_20261110.md'
```

然后发送：

```text
请读取项目根目录的 STEP2_LWF_BN_REMOTE_TASK_20261110.md，执行“提示词一”代码框内的任务。本轮先完成代码、真实短运行和可确认的正式方案；提示词二及以后的正式训练暂不执行。
```

## 提示词一：复用现有工程，完成两组实现和短运行

```text
请在 /home/ysheng4/research/GSMF-RS-DIL 中，为已完成的Cityscapes→ACDC-fog道路19类DIL实验准备第2项：一个LwF式输出蒸馏对照和一个GSMF旧教师BN单变量诊断。请实际完成代码、配置、严格初始化、真实数据短运行及正式执行入口；本轮停止在可供我确认的具体正式方案，不启动4000步正式训练。

一、先恢复现场，复用已经存在的设施

1. 读取适用AGENTS.md、REPRO.md的当前道路段落，以及下述实验的PLAN／STATUS／RESULTS和必要代码。尊重“先短运行、正式训练前确认”的项目规则。保留既有未提交改动、遥感配置、权重、数据和结果，不提交或推送Git，不升级环境。
2. 工程根目录为 /home/ysheng4/research/GSMF-RS-DIL；环境Python为 /home/ysheng4/miniconda3/envs/GSMF_RS_DIL/bin/python。历史为PyTorch 1.9.1+cu111、MMCV 2.0.0、MMEngine 0.8.2、MMSegmentation 1.2.1，现场核对后复用。缺少rg时用Python或grep，不因此安装依赖。
3. 两域正式运行为 experiments/road_clear_to_fog/formal-seed0-20261108-resume01；多雾强度评价为 experiments/road_fog_severity/eval-final-seed0-20261109-182100，已完成evaluation-20261110的12组正式评价。
4. 道路入口是tools/road/run.py，配置工厂为road_dil/config.py，严格初始化在road_dil/checkpoints.py，训练审计在road_dil/hooks.py；多强度场景清单、输入审计、顺序推理和汇总脚本在上述severity目录的prepared-20261110、data-audit-20261110及scripts下。复用这些设施，不另建一套数据、指标或任务管理框架。
5. 现有CLI和build／cfg_for只支持source、ft、gsmf，不能假设已有--stage lwf。允许增加明确的新道路stage／配置或独立入口；旧stage默认行为必须保持兼容。评价器不能把带冻结教师的新方法错误当成纯单分支，也不能误用原版GSMF配置加载新权重。

二、固定权重、数据和拟正式预算

1. 已完成运行的最终检查点如下，路径均相对于上述两域正式运行目录：
   source/iter_60000.pth
   SHA-256 a66c958ee774d27566b901ad6570c0a3b83263e9d74389e1c2e025c6c2673d93
   ft/iter_4000.pth
   SHA-256 99914df527d8506c33178ef6ea1caf7f0ed1d07369858e37275205d60a57d516
   gsmf/iter_4000.pth
   SHA-256 fc227c57dc3e47a134ef51b282964654a0210f3c06f00bd0d3e81b706850b24a
   三者已在2026-11-10现场重新计算一致，运行前仍核对。新增两组均重新从同一个Source出发，不从FT或GSMF最终权重继续训练，不重训Source。
2. 继续使用experiments/road_clear_to_fog/data的既有清单：Cityscapes A_train/A_val=2975/500；ACDC-fog B_train/B_val=400/100。增量训练只读取B_train，禁止旧图回放，不加入Foggy训练图、其他天气或正常参考图。类别0..18，ignore=255；Cityscapes labelIds映射一次，ACDC按实际encoding处理。
3. 拟正式方案为两组各seed 0、4000步，batch 2、512×512裁剪、FP32、AdamW lr=1e-5、betas=(0.9,0.999)、weight_decay=0.001、PolyLR power=0.9/end=4000、每1000步验证／保存，固定iter_4000作主结果。数据增强、采样、预处理、优化器和学习率计划与既有增量配置对齐；每组独立新建优化器。若现场配置与这些记录有实质性差异，查清后在方案中列明，不悄悄换预算。
4. 本轮不搜索超参数、不挑验证集最高checkpoint。首轮LwF只是明确默认配置的基础对照；未合理调参和重复前，不能因其单次差就认定其机制无效。

三、组A：LwF-DIL道路分割对照

1. 检查mmseg/segmentors/DIL_encoder_decoder.py的DIL_type='LwF'路径、mmseg/decode_head/DIL_decode_head.py的loss_by_feat和mmseg/losses/dil_hin_loss.py；优先复用现有有效代码。明确称“LwF-DIL：固定19类单头分割适配”，不是原始分类多任务实验的逐项复现。
2. 同一Source去掉辅助头后初始化教师和学生，严格逐键检查形状与值复制；可复用现有双分支转换并用新配置加载。教师全参数和运行状态固定，采用推理行为，输出detach／no_grad；学生采用与FT等价的部署分割器和可更新范围，不保留GSMF额外的stem/layer1冻结。公共GS-AUFPN分割器本身的图／注意力模块保留，不把更换分割器混入方法比较。
3. 学生损失只保留新域像素CE和教师输出蒸馏，关闭额外特征蒸馏，不添加回放、伪标签、置信度筛选或类别加权。优先沿用现有输出蒸馏T=2、loss_weight=0.5作为首轮默认，明确记录soft cross-entropy的实际归约、作用分辨率及是否含T²缩放。当前DIL_HinLoss没有显式T²，也没有根据ignore_index屏蔽像素；不能仅凭函数参数就声称已忽略255。保留或调整蒸馏像素支持的选择须在新方法配置／报告中明示，不改原版GSMF损失；不要把soft CE的教师熵常数误判为相同logits时蒸馏失败。
4. 核对CE忽略255、教师和学生看到同一增强输入、输出19通道、插值和对齐一致。用手工小张量核对输出蒸馏值及学生梯度，并验证教师无梯度、所有参数／缓冲区不变。
5. 新方法部署只使用学生；如沿用双分支命名，则所有评价只调用backbone_1/decode_head_1，不能按真实天气ID选择分支。保存学生与FT初始化输出等价性及严格保存／重载证据。

四、组B：GSMF旧教师BN单变量诊断

1. 从Source重新转换初始化，保持原版GSMF的学生浅层冻结、学生BN行为、所有损失与系数、Dropout及其他训练设置。
2. 唯一策略变化是旧教师backbone和decode_head中的BN使用初始化时的源running_mean/running_var，并停止更新这些缓冲及num_batches_tracked；BN仿射参数延续原版冻结。学生backbone_1/decode_head_1的归一化策略不变。
3. 这同时改变教师BN前向所用统计和统计更新，准确命名为“teacher_bn_source_stats”，不声称只改了更新计数。不要将整个教师设为eval，从而同时关闭其Dropout；不要给全模型统一设置norm_eval=True。
4. 确保MMEngine递归model.train()、周期验证后恢复训练、保存重载／resume后，策略依旧生效。采用明确的局部子类／配置开关／hook实现，默认关闭；不做无法追溯的全局monkey patch。
5. 与原版做配置diff及一次相同输入的受控前向／优化审计：初始化值和可训练参数集合一致；变化范围仅为教师BN行为；原版仍维持原有教师BN策略，新组教师BN全程不变，教师其他模块及学生training标志符合约定。两组学生实际更新数值不必相同，因为教师输出已变。
6. 本组是机制诊断，不能预设BN是主要遗忘原因，也不将归一化开关本身包装为新算法。

五、短运行、审计与正式方案

1. 建议新目录experiments/road_lwf_bn/prepare-seed0-<唯一时间>，集中保存PLAN、STATUS、实现说明、resolved配置、数据／代码／初始化哈希、命令和验证证据。现有训练与severity目录只读复用。
2. 本轮真实数据调试总预算最多64个优化步骤，包含原版控制、两组短训、失败尝试及resume验证。使用新目录独立账本；road_dil.budget.reserve已支持path，必要时最小扩展入口传入，不重置或借用首轮100步旧账本，也不关闭预算检查。
3. 先通过导入和小张量损失验证，再对少量真实B_train数据短训。至少覆盖原版GSMF控制、LwF-DIL和教师BN变体的梯度／状态检查，两新增组保存重载；用适当短链路验证优化器／调度器／迭代位置resume及BN策略恢复。合成夹具检查与真实数据检查分别标注，短训指标不作为正式效果。
4. road_dil/hooks.py目前会对所有有backbone_1的模型断言学生stem/layer1不变，不适用于允许学生全量更新的LwF。按明确stage／冻结策略适配审计，分别验证应冻结和应更新的组；保留原版检查，不删除全部断言或伪造PASS。训练前即明确参数requires_grad，避免首步才冻结导致审计误记。
5. 核查GPU当前任务、显存及WSL／宿主可用磁盘；不终止其他任务。预估两组正式训练、全量评价、checkpoint和预测的时间／空间。建立tmux持久顺序脚本、真实状态／退出码、查看及resume入口；不无限重试，不自动追加种子或天气。
6. 拟正式评价为每新增模型5个条件：Cityscapes val500晴天、同500场景三档Foggy，以及ACDC-fog val100。沿用severity的完整场景清单与原滑窗512/stride341、预处理、标签规则。先用两个固定场景及少量ACDC样本验证入口、19通道、分支及状态不变；不因debug文件名就误用2张结果冒充完整评价。
7. 输出我可确认的唯一正式方案：两组准确配置／损失／更新范围、初始化SHA、训练预算、评价协议、代码diff、短运行证据、资源估计、正式命令、运行目录、恢复方式。若存在阻塞，完成其余独立准备后集中说明。正式训练须等我发送提示词二，不能沿用2026-11-08仅针对旧三组的授权。

最后用中文简要报告实际修改、验证、遗留问题和方案文件位置。只在本轮准备达到阶段成果时更新远程REPRO.md当前道路状态，不把两组正式实验记为已完成。
```

## 提示词二：确认后执行两组seed 0正式训练、评价与回传

在检查提示词一返回的实际方案后发送。若方案有实质性修改，先在消息中写明最终选择。

```text
我确认上一轮第2项准备结果中的唯一正式方案，授权执行其中LwF-DIL与GSMF teacher_bn_source_stats两组seed 0实验，各4000步，并完成五条件评价、独立指标核验和轻量回传包。本次不重训Source，不重跑已有FT／原版GSMF训练，不追加seed 1/2、超参数搜索、其他天气或新模块。

先读取适用AGENTS.md、本轮PLAN／STATUS、代码diff和短运行证据；核对我确认的配置、代码、数据、初始化指纹与现场一致，GPU／磁盘可用。若只有一套已确认方案且检查通过，直接执行已授权范围，不反复询问；实质性协议差异或无法通过的错误须如实报告。

用已验证的tmux持久脚本在单GPU上顺序运行两组，每组从同一Source转换起点、新优化器开始。保留固定iter_4000和完整恢复状态；真实记录运行标识、配置、日志、退出码、各阶段进度和资源。失败即停止依赖阶段、保留失败现场，不自动反复重试或扩大预算。启动后检查实际进程和loss进展；后台启动不等于完成，也不能承诺没有监测机制的持续监控。

每组结束后在晴天500、三档配对Foggy各500及ACDC-fog100上冻结评价，共10个新增完整评价单元、4200次逐图评价。所有组无真实测试天气ID路由，无TTA；参数及全部缓冲区评价前后不变。记录真实学生分支调用、完整检查点SHA和实际图像数。

从每个条件全部像素累计的19×19混淆矩阵计算mIoU和逐类IoU，GT行／预测列，255忽略，union=0排除，GT缺失但有预测时该类为0。独立重读保存的预测和原始标签复算矩阵并核对GT直方图。不要平均逐图mIoU冒充全集mIoU。

汇总Source／FT／原版GSMF／LwF-DIL／教师BN变体的五条件表，最终25个模型×条件条目中15个可复用旧结果。复用须核对检查点、数据清单、预处理、分支和指标来源；保留来源路径与新旧标记，不伪造本轮重新推理。必要回归检查使用少量固定输入，不无故全量重跑旧组。

输出完整19类表和逐强度曲线，沿用上轮固定6个场景：frankfurt_000000_011074、frankfurt_000001_008688、frankfurt_000001_015328、frankfurt_000001_041074、frankfurt_000001_073911、lindau_000049_000019。保留这些场景在新增两模型四条件的48份原始预测及清晰同样例对比；如加入ACDC样例，先固定ID，不按效果挑图。

分别分析晴天保持、各合成强度绝对性能／相对晴天下降、真实ACDC-fog适应、逐类取舍和成本。不要用五条件简单平均掩盖配对场景重复权重，也不预设新组优于原版。明确单种子、真实／合成跨库差异、ACDC强度支持未知；当前不能主张严格未见强度泛化、统计显著或已证明BN因果解释。

生成独立轻量交接包：PLAN／STATUS／RESULTS／SUMMARY、实际配置、命令、代码版本和最小可恢复源码／补丁、训练及评价日志、冻结／BN审计、10个新增矩阵与独立核验、五模型汇总及逐类CSV／JSON、曲线和固定样例、数据／权重／完整预测的远程索引。没有提交的新代码须实际打包，不能只说Git可恢复。保留原结果，权重、原始数据、全量预测、环境和.git留远程。

保存MANIFEST.sha256，覆盖包内除清单自身外的全部文件；生成tar.gz及外置同名.sha256，校验解包后文件集合与哈希。更新本轮STATUS和远程REPRO.md；未结束时明确真实剩余项。最后给出两组完成状态、五条件结果、关键限制、包和SHA文件的绝对路径，以及使用home-wsl获取它们的scp命令。学校本地接收目标为C:\undergraduate_thesis\03_experiments\road_lwf_bn\<run_id>\，不要尝试在远程写入这个Windows路径。
```

## 提示词三：换会话后恢复或核查进度

```text
请恢复本工程experiments/road_lwf_bn下最近一次已获我确认的第2项任务。先读AGENTS.md、该轮PLAN／STATUS及authorization证据，核对实际tmux／进程、日志、退出码和checkpoint，不仅依赖“running”文字。不要重复启动仍在运行的任务，不覆盖已有结果，不把准备阶段授权扩为正式训练授权。

按已确认范围继续尚未完成的训练／评价／指标核验／打包；若正式训练尚未确认，仅报告准备状态。中断恢复须校验模型、优化器、调度器、迭代位置和教师BN策略，区分resume与只加载权重；RNG／采样游标未完整恢复则明示限制。已完成单元须校验输入与产物指纹后才复用。最后给出真实进度、阻塞和准确下一步。
```

## 提示词四：首轮结果审阅后，启动基础对照的关键重复

此条是独立后续授权，首轮不自动执行。默认重复FT、原版GSMF与LwF-DIL；教师BN变体是否进入重复，待首轮结果后明确选择。

```text
我已审阅第2项seed 0结果。请在同一Source iter_60000检查点下，对FT、原版GSMF和LwF-DIL分别补增量seed 1与2，每组每seed 4000步，共6次新增训练、24000步；本条不包含教师BN变体、源模型重训或超参数搜索。

复用已通过验证的配置与五条件评价，只改变实际增量随机种子。现有road_dil/config.py默认seed=0，旧run.py的invocation也曾硬编码seed=0；确保配置、PyTorch／NumPy／Python、采样／worker及记录使用真正的1／2，不得只改目录名或日志标签。同seed组对齐数据及增强随机流，模型初始化引起的RNG消耗差异若不能完全隔离则如实记录。

每次从相同Source转换状态及新优化器开始，按单GPU顺序执行，采用独立目录，保存完整日志／状态／权重与哈希。不重跑已完成seed 0，不覆盖旧结果。每个新增模型评价晴天500、三档配对合成雾各500、ACDC-fog100，共30个新增评价单元；继续逐预测独立复算、分支及状态检查。

报告0／1／2逐次结果、各条件均值与标准差、同seed方法差值及成本，不把三个强度当成独立训练重复。明确这只检验固定源模型的增量随机性；三次运行不自动证明统计显著，也未覆盖源训练随机性。完成后按本轮已有轻量交接规范另行打包、校验并提供home-wsl回传命令。
```

## 本地依据与官方用法

- [第1项接收与分析](../../03_experiments/road_fog_severity/REVIEW_eval-final-seed0-20261109-182100.md)；[原两域接收核验](../../03_experiments/road_clear_to_fog/REVIEW_formal-seed0-20261108-resume01.md)。远程执行不依赖这两个本地路径，必要事实已写入提示词。
- [OpenAI Docs：Prompting Codex](https://learn.chatgpt.com/docs/prompting#prompting-codex)：任务行为、相关代码、约束与验收写入可执行交接。本文按本项目现场代码与授权边界编写。
- [OpenAI Docs：Non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode)：`codex exec`可运行独立CLI任务，但本次远程CLI未登录，未进行模型调用。后续若使用CLI，先核查现场版本帮助和登录，不读取或回传认证文件，不使用绕过审批／沙箱的选项。
