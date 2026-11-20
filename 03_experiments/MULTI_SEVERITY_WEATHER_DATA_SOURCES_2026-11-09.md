# 多强度天气评价：数据来源与当前模型适用性

日期：2026-11-09（Asia/Shanghai）。性质：针对现有 Source／FT／GSMF 的评价数据来源核查与建议；核对作者论文、官方项目和代码说明，未下载数据或执行模型推理。不是逐篇阅读报告，也不是新增实验结果；本文不改变基线、训练协议或已有归档。

## 1. 当前最可行的选择

先用 **Cityscapes val 对应的晴天与 Foggy Cityscapes 三档雾版本**，得到同一组留出场景的四个评价点。该选择与当前19类模型衔接最直接，能够固定图像内容并沿用语义标签。[S1]

SHIFT 是雾、雨、光照连续变化的重要候选；其连续序列在行驶过程中改变条件，不能直接等同于同一固定画面的多强度重渲染。当前模型在 SHIFT 上的结果还包含真实到合成场景的迁移影响。[S3，§3.3、附录A.3；后一句为本项目协议分析]

## 2. 已核对的数据主干

| 目标                         | 来源、年份及角色                                                              | 强度与对应关系                                                                             | 获取方式与当前适用性                                                                                                                                                 |
| ---------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 雾：首轮主测试               | Foggy Cityscapes；IJCV 2018，基于真实道路图像的合成雾基准                     | 同一图像有 β=0.005、0.01、0.02 m⁻¹ 三档；加原始晴天形成四点；雾图继承原 Cityscapes 标注 | 经 Cityscapes 官网登录下载雾图，原始晴天和 gtFine 另从原数据集取得；目前优先使用 val 对应场景。[S1、S2]                                                              |
| 雨：下一轮受控扩展           | Weather Cityscapes；ICCV 2019／扩展 IJCV 2020，物理雨渲染                     | 官方列出 Cityscapes val 500帧、7档雨；源场景与语义保持对应                                 | 官网提供 val 的 rain_diff 包，标注约4 GB，需用官方工具结合原 Cityscapes 图像重建；不是直接下载即得最终雨图。原始标签单独准备。[S4、S5]                               |
| 雾／雨／昼夜：连续条件扩展   | SHIFT；CVPR 2022，合成驾驶域变化基准                                          | 连续雾、雨、云量及太阳高度角；提供细粒度条件描述和像素标签；不提供雪域                     | 使用官方 DevKit 按前视、RGB、semseg、val、images（1 fps）及 shift 类型选择下载；不是每张图都有多天气版本。[S3、S6]                                                   |
| 雪：快速受控诊断             | 常见图像扰动基准及 imagecorruptions 实现；ICLR 2019／CVPR 2020 为相关基准依据 | snow 算子有 severity=1…5；可作用于同一批 Cityscapes val 图像                              | 在本地生成并冻结同一套测试图像，沿用几何不变的标签；等级是算子等级，不是实测降雪量。不能将简单叠雪视为完整积雪道路外观。[S7、S8]                                     |
| 雾／雨／雪／夜：真实外部验证 | ACDC；ICCV 2021，后续扩展的真实恶劣条件基准                                   | 四类恶劣条件及正常条件对应图；不是每个场景的多档雾、雨、雪和光照控制扫描                   | 官方下载页面取得相应 RGB／GT；沿用有效划分。正常图与恶劣条件图来自不同记录，不直接复制像素标签。当前项目已有 fog，不表示其他域已准备就绪。[S9；最后一句来自项目状态] |

Foggy Cityscapes-refined 的550张是特定高质量训练／验证子集，不应与完整 val 场景集合混称；trainextra 的雾版本也不是完整三档。[S1]

Weather Cityscapes 官方发布说明中，train 雨数据为2995帧、8档，val 为500帧、7档，不能将训练包的档数直接写成验证协议。Cityscapes 图像缩小到1024×512；评价时须统一对应晴天与雨图的尺寸处理，GT缩放用最近邻，避免把分辨率差异归因于雨强。实际强度值、可用场景及文件完整性须在下载后从清单核实。[S4]

## 3. SHIFT 能回答什么

- 可以按雾／雨 severity 或太阳高度角分箱，比较固定模型在各条件的 mIoU；使用每张图自己的 GT。[S3]
- 连续序列中的车辆、行人和视点也随时间变化，因此曲线仍可能受场景组成影响。建议跨多个序列汇总、报告每箱样本量与类别支持量，不以单个序列证明强度的独立作用。这是对其数据生成方式的实验设计分析。
- 即便只选择 fogginess 或 raininess 方向，官方定义也会联动云量、降水／积水或 fog distance 等参数；更准确的名称是沿官方天气变化路径评价，不是仅改变一个物理参数的严格单变量试验。[S3，附录Tables 6–7]
- 夜间变化用太阳高度角描述，不把它直接解释为实际照度；SHIFT的条件参数也不能与Foggy Cityscapes的β互换。[S3]
- 正文说明23类分割标注；实际使用前须根据所取数据的编码和类别定义映射到当前19个 trainId，额外类别处理为 ignore，并核对双方类别含义。[S3，附录A.2]

以下是按 DevKit README 参数组合的示例，在已取得官方仓库的目录运行；本轮未执行，实际可用包与标签需要下载后核对：[S6]

```powershell
python download.py --view "[front]" --group "[img, semseg]" --split "[val]" --framerate "[images]" --shift "continuous/1x" ./data/SHIFT
```

它按数据组／划分下载，不表示会只下载雾方向，也不表示只下载少量样本。细粒度条件元数据需另核对所取包及官方说明。当前不建议先下载所有传感器、所有划分或10 fps视频。

## 4. 夜晚与雪天的补充来源及边界

**夜晚：** 若目标是具有标签的多级昼夜条件，优先考虑SHIFT。若只需同场景的便宜诊断，可对留出晴天图像定义曝光／gamma降暗等级并固定参数；结果称为“合成低照度稳健性”。真实夜间的车灯、路灯、曝光、色温、传感器噪声和运动模糊不能由降暗完整代表。

Dark Zurich（ICCV 2019，TPAMI 2022扩展）有白天、黄昏和夜间的对应场景，但白天／黄昏训练图主要无标注，不能据此直接计算三组完整GT mIoU，也不能把近似对应的白天GT直接复制到夜图。可用于定性分析或使用其带标注的夜间评价部分。[S10]

**雪天：** 先用 imagecorruptions 的五档 snow 固定场景诊断，再用 ACDC-snow 检查真实效果。若需要可计量的降雪强度、道路积雪和光照联合变化，应另选择明确支持雪和分割标签的仿真平台／数据，而不能假定 SHIFT 已含雪；本轮未确认一个可直接替代 Foggy Cityscapes、同时满足同场景多档雪和当前19类评价的官方现成数据包。[S3、S7、S9；最后一句为本轮核查范围]

**真实配对补充：** WeatherProof（2023预印本；2024相关挑战）提供晴天／恶劣天气配对及雨、雪、雾等效果，原文定义10类，含 terrain-snow、stone 等，与当前Cityscapes19类不一致。它有配对价值，但本轮未核实每个场景存在统一的多强度扫描；当前模型不能不经协议调整就计算其官方全类mIoU。不是首轮的低成本替代。[S11、S12]

不建议把任意去雨、去雪、图像增强数据集当成分割测试集：成对清晰图不等于有像素语义GT。生成式天气编辑也须核查是否改变物体、边界和语义，不能自动沿用原标签。以上是本项目评价要求。

## 5. 为什么仍考虑ACDC训练，何时改用合成训练

**ACDC不是唯一或已证明最优的训练来源。** 监督道路分割训练需要像素类别GT，当前Source／FT／GSMF不以真实天气强度作为训练输入，因此没有强度标签不妨碍训练。ACDC提供真实雾／雨／雪／夜图像及与Cityscapes兼容的19类标注，适合检验真实新条件适应和已学条件保持。[S9] 这说明其设定适用性，不证明训练效果必然优于合成数据。

Foggy／Weather Cityscapes同样可以用于训练。其优势是能够控制生成参数、匹配同一原始场景，更适合研究天气变化的独立影响，以及预先留出某些强度参数。Foggy Cityscapes作者已报告合成雾训练可改善真实Foggy Driving表现，因此不能因合成身份就否定其训练价值。[S1、S4、S5]

两条路线各有局限：当前Cityscapes→ACDC涉及相机、场景等跨数据集差异，不能将全部适应或遗忘归因为天气；只在某一合成器生成的数据上训练／测试，也不能直接证明真实天气或其他合成器上的效果。ACDC原文亦单列Cityscapes→ACDC正常条件的传感器迁移基准，说明跨库差异并非只有天气。[S9，扩展版§II、§III；其余为本项目协议分析]

当前建议保留已完成的真实天气实验，并用固定模型补合成多强度评价；它能回答受控稳健性，但ACDC没有强度标注，无法核实其训练强度范围，因此不足以证明严格未见强度泛化。若后者成为论文核心，应再从同一Source起点建立受控合成训练支路，例如增量训练仅用Foggy Cityscapes train的β=0.02，在独立val场景评价β=0、0.005、0.01、0.02；检查所有训练增强未引入留出强度。这是建议，未启动训练或更换数据集。

若主要训练改为合成路线，仍需按原始场景划分，不能将同一图的不同天气版本拆到训练和评价两侧。Source train原图与其增量雾变体共享几何内容本身不构成训练／测试泄漏，但会改变任务难度，且保留原图用于生成天气属于需披露的历史信息访问。若全部天气从一开始即可生成，应加入离线混合天气训练作为额外数据访问／未来条件访问参考，以检验顺序更新的性能与资源代价，不能仅因人为分批就证明DIL最有必要。该权限口径沿用[对照规划](COMPARISON_PLAN.md)。

### 5.1 训练数据应由论文要回答的问题决定

2026-11-09讨论补充：真实与合成之间的差异是训练数据选型的重要维度。强度信息便于定义实验，却不会自动使训练效果更好；没有强度标签也不妨碍普通像素监督训练。当前损失需要道路、车辆等像素类别GT，并不要求输入雨量或雾衰减系数。

ACDC采集协议刻意保留相应恶劣条件表现强烈的片段（S9，扩展版§III-A），因此不能假定它均匀覆盖从晴到浓雾的强度轴；无逐图物理强度标签也妨碍精确界定训练范围。这是把它作为强度泛化主证据的限制，不是必须放弃真实天气训练的理由。

| 核心问题 | 更匹配的主要训练来源 | 还需补充的证据 |
| --- | --- | --- |
| 分批学习真实天气后，能否适应新天气并保持已学条件？ | Cityscapes→ACDC等有像素标注的真实天气数据 | 过渡条件评价；注意跨库差异并非仅天气 |
| 只训练指定强度后，能否泛化到未训练过的中间强度？ | Foggy／Weather Cityscapes等有明确生成参数的受控数据 | 独立原始场景评价及真实天气验证；训练／增强排除留出强度 |
| 连续天气变化及更新规则对方法有何影响？ | SHIFT等含条件元数据、像素标签的连续变化数据 | 类别映射、序列内容变化控制及独立真实评价；连续数据本身不要求无提示训练 |

若论文核心转向第二项，受控合成训练可以成为主实验，ACDC转为真实天气验证；没有必要先把ACDC五域全部完成。若主问题仍是第一项，ACDC可以继续承担真实训练主线，合成数据用于机制诊断或额外训练支路。现有真实实验是可复用成果，但不是锁定后续数据来源的充分依据。此处为方案建议，未采纳训练数据替换。

### 5.2 合成与真实应分开验证什么

- Foggy／Weather Cityscapes是在真实道路图像上合成天气，保留了大量真实场景内容；SHIFT则整体由仿真生成。两者的域差异来源不同，不能把所有合成数据归为同一种失真程度。[S1、S3–S5]
- 物理渲染和图像扰动只能覆盖其建模因素；真实图像还受采集设备、曝光、天气空间分布等影响。只在同一生成器上评价可能得到依赖生成器特征的收益，须用真实留出数据检验。这是实验设计风险，不是已观察到本项目出现该问题。
- 真实数据同样受采集地域、设备、样本量及强度选择限制。不能先验认定真实训练必胜合成训练；Foggy Cityscapes已有合成雾监督训练改善真实Foggy Driving的直接实例，SHIFT也报告合成／真实联合训练改善部分真实域结果。[S1、S3附录B.2] 这些结果不保证本项目的DIL或遗忘收益。
- 当前ACDC训练模型的合成强度曲线，检验真实训练模型的受控稳健性；只用合成训练的模型在未参与其训练的ACDC留出集上评价，检验向真实天气的跨库泛化。若已使用ACDC训练，则其留出集是已接触天气／数据来源的评价，不能称该模型对全新真实目标域的零样本验证。

### 5.3 当前建议的最小训练对照

先完成现有三模型的多雾强度评价；若要检验受控强度学习，再从同一个Cityscapes源检查点分支，给FT与GSMF各建立一个Foggy Cityscapes train的合成雾增量版本。初始可只用β=0.02，在独立val原始场景评价晴天及三档雾，并在未用于该支路训练的ACDC-fog留出集评价真实迁移。原有CS→ACDC-fog版本保留，所有版本同时报告晴天保持、各合成强度和真实雾天成绩。

该方案回答所选强度训练及跨真实天气的适用性。若要比较“合成训练能否替代当前真实训练”，还应给合成训练选择明确的强度覆盖方案，必要时补三档混合；不能把只训练单一β的结果当成所有合成训练的最好表现。匹配骨干、源检查点、增量计算和调参预算，明确样本量／场景覆盖及强度范围；即便如此，两数据集仍包含内容等差异，结论应限定为这两种具体训练配置，不声称隔离出了数据真实性的全部因果效应。

用作开发与选型的ACDC／Foggy验证集不能再称最终未接触测试；独立测试应在方案固定后使用。若混入真实样本或读取旧源图重新生成天气，分别登记真实数据与历史访问权限。暂不要求下载全部SHIFT、同时实现多种天气生成器或立即展开真实／合成／混合的全组合。

## 6. 现有三模型的建议评价协议

1. **按原始场景检查隔离。** 优先用原Cityscapes val；检查其原图、邻近帧及各天气变体是否进入Source／增量训练。相同原图的晴天／雾天不能分到训练与独立评价两侧。既有val已被评价过，不能因此宣称为从未接触的最终测试集；若后续反复选型，另留最终评价。
2. **使用同一组场景构成四点。** 晴天记 β=0，雾为0.005／0.01／0.02。可以对全部500个val场景评价，前提是数据齐全并通过上述隔离核查；不足时固定共同交集并记录缺失，不能让各强度用不同场景子集。
3. **固定模型与推理状态。** Source iter60000、FT／GSMF iter4000；核对实际分支、映射、预处理及checkpoint哈希；纯评价用eval模式，不更新BN、不做测试时适应。
4. **沿用累计混淆矩阵。** 每个模型、每个强度分别累计19×19矩阵，再计算逐类IoU和mIoU；GT=255忽略，union=0类置null并从均值排除。不要平均逐图mIoU。保留类别支持量及参与均值的类别。
5. **输出可核查结果。** 三条mIoU曲线横轴使用真实β值；另给逐类IoU表和相对晴天的下降。每个固定示例以“RGB／GT／Source／FT／GSMF”为列，以强度为行，所有模型用相同配色和场景。不要对四个离散点绘制未经支持的平滑拟合。
6. **限定结论。** 该试验首先回答固定模型的受控多强度稳健性及相对排序；ACDC-fog没有逐图强度标签，尚未核实训练强度范围，不称严格未见强度泛化；这不代表已确认存在官方轻雾子集。当前模型只经历晴天→雾天训练，直接测试雨／雪／夜属于跨天气外推评价，不能当作这些天气的已学域保持测试。新采集未标注图片可展示预测，不能单独产生有GT依据的mIoU。

上述为建议，未运行。当前模型／GT口径依据[已有结果总表](road_clear_to_fog/formal-seed0-20261108-resume01/RESULTS_SUMMARY.md)；后续顺序衔接[既有计划](NEXT_STEPS_AND_BASELINE_REVIEW_2026-11-09.md)。

## 7. 核查来源

以下均为作者／官方来源；“网页说明已核对”不代表数据下载、解包、标签映射或渲染结果已实测。新近资源仅作补充，不因年份替换与当前评价更匹配的经典基准。

- **S1：** Sakaridis等，*Semantic Foggy Scene Understanding with Synthetic Data*，IJCV 2018。[作者数据页](https://people.ee.ethz.ch/~csakarid/SFSU_synthetic/)，Foggy Datasets／Foggy Cityscapes：三档β、标签继承、refined与trainextra边界。
- **S2：** [Cityscapes官方下载入口](https://www.cityscapes-dataset.com/downloads/)，本轮未登录，入口重定向登录页；包内结构未实测。雾图常用包名为`leftImg8bit_trainvaltest_foggy.zip`，可辅助定位，最终以登录后的官方目录为准。
- **S3：** Sun等，*SHIFT: A Synthetic Driving Dataset for Continuous Multi-Task Domain Adaptation*，CVPR 2022。[作者原文含补充](https://arxiv.org/html/2206.08367v1)，§3.3、附录A.2–A.3及Tables 6–7。
- **S4：** Halder等，*Physics-Based Rendering for Improving Robustness to Rain*，ICCV 2019。[作者项目及数据下载页](https://team.inria.fr/rits/computer-vision/weather-augment/)，Weather Cityscapes与Notes：val 500帧七档、rain_diff重建、标签与尺寸。
- **S5：** Tremblay等，*Rain Rendering for Evaluating and Improving Robustness to Bad Weather*，IJCV 2020。[官方代码](https://github.com/astra-vision/rain-rendering)，支持Cityscapes、自定义雨强、深度输入和数据入口；本轮未复现旧版依赖。
- **S6：** [SHIFT官方DevKit](https://github.com/SysCV/shift-dev)，Downloading：front／img／semseg、val、images／videos及discrete／continuous选项。
- **S7：** [imagecorruptions官方代码与用法](https://github.com/bethgelab/imagecorruptions)，severity=1…5；[算子注册源码](https://raw.githubusercontent.com/bethgelab/imagecorruptions/master/imagecorruptions/__init__.py)。不能将brightness默认算子直接等同于夜间生成器。
- **S8：** Kamann与Rother，*Benchmarking the Robustness of Semantic Segmentation Models*，CVPR 2020。[正式论文](https://openaccess.thecvf.com/content_CVPR_2020/papers/Kamann_Benchmarking_the_Robustness_of_Semantic_Segmentation_Models_CVPR_2020_paper.pdf)。本文采用其常见扰动评价思路；自定义生成版本须记录实现，不能自动称与原基准逐项一致。
- **S9：** [ACDC官方概述](https://acdc.vision.ee.ethz.ch/overview)、[官方基准](https://acdc.vision.ee.ethz.ch/benchmarks)、[作者论文（含扩展信息）](https://arxiv.org/abs/2104.13395)、[扩展版全文v4](https://arxiv.org/html/2104.13395v4)。覆盖四种恶劣条件、正常场景对应和19类语义评价；不是按物理强度设计的同场景扫描；扩展版§II明确另设Cityscapes→ACDC正常条件的传感器迁移，§III-A说明采集偏向相应恶劣条件表现强烈的片段，§III-D说明类别与标注。
- **S10：** Sakaridis等，*Map-Guided Curriculum Domain Adaptation and Uncertainty-Aware Evaluation for Semantic Nighttime Image Segmentation*，TPAMI 2022。[ETH官方论文条目](https://www.research-collection.ethz.ch/entities/publication/822ffaa5-0da8-4862-96ee-71f57627a9d7)；[作者全文](https://people.ee.ethz.ch/~csakarid/MGCDA_UIoU/MGCDA_UIoU-Sakaridis%2BDai%2BVan_Gool-IEEE_TPAMI_20.pdf)。
- **S11：** Gella等，*WeatherProof: A Paired-Dataset Approach to Semantic Segmentation in Adverse Weather*，2023预印本。[作者原文](https://arxiv.org/html/2312.09534v1)，§3.2／Fig.3：准确配对及10类定义；本轮未将该标题登记为已核实CVPR正式录用。
- **S12：** [CVPR 2024 UG2+ Track 3官方数据说明](https://cvpr2024ug2challenge.github.io/dataset24_t3.html)，说明WeatherProof挑战数据入口与挑战val组合，使用时不得混用原论文和挑战划分。
