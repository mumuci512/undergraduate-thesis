# LIT-007 至 LIT-016 比较方法与复现启动建议

核对日期：2026-10-26（Asia/Shanghai）。分析对象为本地十份 Word 文献报告；结合当前候选的“天气和光照变化、类别固定、有标注、无显式域切换提示”的道路分割方向提出建议。本文是已有报告的定向综合，不声称覆盖整个领域，也不代表已确定正式基线或完成复现。

选型建议已根据同日补检修正：本文用于整理已有报告，不能单凭这批文献确定2026年的主复现对象。应先比较2024–2026年的相关论文及公开工程，再在选中框架内建立FT/ER等基础对照；EWC/LwF按比较需要补充，不作为开始新方法前的必经前置步骤。原两阶段路线保留为工程验证备选。详见[新近文献补检与复现选型修正](RECENT_DIL_SEGMENTATION_REPRODUCTION_SCREEN_2026-10-26.md)。

## 逐篇报告中的主要比较方法

下表列报告实际记录的核心对照；完整实验配置和原论文定位仍由逐篇报告负责。联合训练、额外真值诊断、网络架构对照与组件消融单独标明。

| 文献与年份 | 研究设定 | 核心比较方法 | 本文方法、参考组或消融 | 报告定位 |
| --- | --- | --- | --- | --- |
| [LIT-007 SimCS](../paper_reports/LIT-007_simcs_odics.docx)，2024 | 有标注、固定类别的在线域增量道路分割 | NT、EWC、MAS、LwF、ER | 在上述方法上叠加 CARLA/VIPER 模拟数据；Supervised 联合训练为非增量参考 | 第2节分组、第3节协议、第4节结果；原文 Table 1、附录 Tables 5–7 |
| [LIT-008 Kalb 等](../paper_reports/LIT-008_kalb_class_domain_segmentation.docx)，2021 正式发表／2022 预印本 | 类增量与域增量分开实验 | FT、FE、L2、EWC、MAS、LwF、Replay；DIL 中另有 LwF+Replay，CIL 中另有 CIL 分割蒸馏及其+Replay | Replay 缓存32/64张；DeepLabV3/ERFNet 架构筛选；联合训练参考 | 第2节、第5节；原文 Tables I–III |
| [LIT-009 智能回放选样](../paper_reports/LIT-009_replay_smart_data_selection.docx)，2022 | 有标注、已知边界的类增量与双域增量分割 | FT、随机回放；CIL 中另有 CIL 蒸馏；选样比较包括类均衡样本、类均衡缓存、多样化类均衡、Mean Entropy、Mean Loss、最高损失等 | RSS：编码器特征→UMAP→k-means→簇中心近邻；另讨论 GSS、BRISQUE、总变差等策略；Offline 为联合训练参考 | 第2–4节；原文 Tables I–III。报告未抄录原文所有策略的完整结果 |
| [LIT-010 天气域遗忘](../paper_reports/LIT-010_principles_forgetting_weather.docx)，2023 | 有标注、CS→单个 ACDC 天气的四条独立两阶段路线 | FT、EWC、Replay | DINO预训练、AutoAlbument增强、CN替换BN的逐项组合；DeepLabV3+/R50、SegFormer-B2、ERFNet为架构对照；BN重估为访问旧数据的机制诊断 | 第2–3节；原文 Tables 5–8 |
| [LIT-011 JASCL](../paper_reports/LIT-011_joint_nonstationarity_jascl.docx)，2026，按本地报告所载 | 少样本、类域联合变化；含半监督分割 | 报告重点记录 Vanilla、UCL（医学）、GAPS（道路） | JASCL、JASCL+GAPS；去GAS/去PAS消融。U-Net、MedFormer、DeepLab、SAM是架构 | 第3节表2、第4节；原文 Tables 2–8、34、36 |
| [LIT-012 SimCIS](../paper_reports/LIT-012_simcis_continual_segmentation.docx)，2025 | ADE20K类增量语义／全景分割 | FT、MiB、PLOP、SSUL、EWF、CoMFormer、BalConpas、ECLIPSE、CoMasTRe；各协议方法集合不完全相同 | SimCIS；QPA/CSL/VQ组件、图像与虚拟查询回放对照；joint为离线参考；Mask2Former为网络基础 | 第3节表B、第4节表C–E；原文 Tables 1–6 |
| [LIT-013 TOPICS+](../paper_reports/LIT-013_topics_plus_hierarchical_ciss.docx)，2025会期／2026章节在线 | 医疗场景层次类增量分割 | PLOP、MiB、MiB+AWT、DKD、TOPICS | TOPICS+；层次Dice、伪标签及类别树变体消融 | 第5节分组；原文 Tables 1–3 |
| [LIT-014 UCB](../paper_reports/LIT-014_ucb_uncertainty_class_balance.docx)，2025 | VOC/ADE20K类增量语义分割 | 核心成对比较：PLOP、SSUL、CoinSeg及其+UCB；另有PLOP+NeST、ST/URN/MBS不确定性对照 | UA、CB及二者组合消融；GT、DW使用额外真值，属于诊断。报告未抄录主表全部外部排行 | 第3–4节；原文 Tables I–IV、VII–VIII |
| [LIT-015 EW-DETR](../paper_reports/LIT-015_ew_detr_evolving_world_detection.docx)，2026 | 类域同时增量、开放世界目标检测 | ORE-EBUI、OW-DETR、PROB、CAT、ORTH、DuET、OWOBJ | EW-DETR的D-DETR/RF两种实现；双LoRA、QNorm-Obj、EUMix消融。各对照被改为本文无样本EWOD协议 | 第2节“实验分组与可比性”；原文 Tables 1–4、S4–S6 |
| [LIT-016 AIR](../paper_reports/LIT-016_air_geometric_consistency_ocil.docx)，ICLR 2027匿名在审，未确认录用 | 有标注、分段单遍在线类增量图像分类 | 主回放对照：iCaRL、DER、SCR、ER-ACE、L2P-R、MEMO、EASE-R、TagFex、MOS-R；无回放对照：L2P、DualPrompt、RanPAC、RanDumb、EASE、APER-adapter、MOS、PROL | Adapter+ER、+HGA、+MGC消融；轻量对照另有ER、DER++、OCM、GSA、OnPro、ERSM等；MGC配合DER++/LwF/PCR作替代约束 | 第3节P1–P5；原文 Tables 1–5、15 |

## 从这些报告能归纳出的基线主干

这里的“主干”仅指这批文献中与当前候选问题直接相关的基础对照，不依据出现次数宣称全领域影响力。

| 方法类别 | 核心方法与作用 | 与天气域增量分割的关系 | 本地证据 |
| --- | --- | --- | --- |
| 基础训练 | FT/NT顺序更新；FE冻结编码器；L2限制参数偏移 | FT/NT应先跑通；FE可诊断冻结表征对适应的限制 | LIT-007–010；FE/L2详见LIT-008 |
| 真实样本回放 | ER/Replay混合历史图像及像素标签 | 直接相关，优先实现；缓存政策、容量和旧样本训练次数需明确 | LIT-007–010 |
| 参数正则化 | EWC以Fisher近似保护重要参数；MAS采用另一种重要性估计 | 可提供无旧图像缓存的经典对照，但重要性更新及边界信息需对齐 | EWC见LIT-007/008/010；MAS见LIT-007/008 |
| 预测蒸馏 | LwF用旧模型输出约束当前模型 | 可提供另一种无旧图像缓存对照；仍需旧模型及额外前向 | LIT-007/008；LIT-016仅为分类中的替代约束 |
| 回放选样 | 随机、类别覆盖、熵统计、RSS表征聚类 | ER稳定后再比较选样收益；RSS原版访问全阶段数据 | LIT-009 |
| 训练与归一化 | 预训练、增强、CN | 直接相关的强训练配置；改善需拆分组件，记录额外预训练与增强成本 | LIT-010 |
| 模拟数据辅助 | SimCS(CARLA/VIPER) | 直接相关的候选方法，可叠加FT或ER；需新增模拟数据与标签映射 | LIT-007 |
| 类增量分割专用 | MiB、PLOP、SSUL、CoinSeg、ECLIPSE等 | 主要处理新增类与背景标注漂移；固定类全标注DIL须重新适配和验证 | LIT-012–014 |
| 其他任务启发 | JASCL、EW-DETR、AIR | 少样本类域联合变化、检测、分类的方法参考；直接复现不能回答本课题问题 | LIT-011/015/016 |

具体证据：LIT-007 Table 1中，NT四域终点平均mIoU为40.5，ER(800)为46.2，ER+VIPER为48.3；LIT-008 Table III中，FT为49.9、Replay(64)为56.1；LIT-009 Table III中，FT为48.3、随机回放为56.2、RSS和Mean Entropy均为57.2。三篇的骨干、数据流、训练与缓存条件不同，只能在各自表内比较。它们共同支持优先建立ER对照，不能据此保证本项目提升幅度。[对应报告结果节；SimCS原文§5.1、Table 1](https://arxiv.org/html/2211.16234v2#S5.SS1)

LIT-010 Table 7中，Replay对Night/Rain的遗忘F为5.6/2.9点，预训练+增强+CN组合为7.9/8.0点；组合的学习准确率A更高。保持与适应存在权衡，评价时不能只挑一个汇总指标。该结论限于两条独立两阶段路线。[LIT-010报告第3节](../paper_reports/LIT-010_principles_forgetting_weather.docx)

## 两阶段基础工程的备选验证顺序

以下适用于已决定自行搭建有标注DIL基础工程的情况；当前主复现对象优先级以[新近文献补检](RECENT_DIL_SEGMENTATION_REPRODUCTION_SCREEN_2026-10-26.md)为准，不要求先完成以下全部项目再选择新方法。

1. **先跑通一条两阶段路线。** 候选起点为DeepLabV3+／ResNet-50、19类、有标注Cityscapes→ACDC Rain。先得到源域模型，评估CS与Rain；再顺序微调，重复评估两域。随后独立运行CS→Night。这个先后顺序是工程建议；LIT-010原实验四天气各自独立。
2. **加入随机ER。** 从相同源域检查点分支，初步考虑32/64张旧图及标签、旧新各半批；该容量参考LIT-008/009，移植到天气协议属于本项目基础实验，不是对LIT-010表7的严格数值复现。若直接复现SimCS，应使用其FIFO与800张主配置。
3. **加入EWC或LwF。** 两者可先择一：EWC补参数保护对照，LwF补预测保持对照。固定骨干、预训练、数据划分及调参预算；单列额外模型、重要性张量、回放曝光和总耗时。
4. **验证LIT-010训练组合。** 从相同配置逐项检验预训练、增强、CN；区分额外预训练的收益与增量学习模块的收益。可进一步尝试ER与这些训练配置的组合，作为待验证实验。
5. **再扩展方法和序列。** ER稳定后考虑LIT-009选样或LIT-007 SimCS；初始流程验证后扩展多天气顺序、不同顺序与无切换提示流，再决定是否加入SegFormer架构对照。更换骨干后需要重建对应FT/ER比较。

最低评价记录应包括：两个阶段的模型检查点；更新前后两域mIoU组成的2×2矩阵；旧域遗忘F；更新后的新旧域平均mIoU；训练时间、峰值显存与缓存实际字节。正式结论再补多随机种子。LIT-010的A=(mIoU₀,₀+mIoU₁,₁)/2，与最终新旧域平均不是同一个量。

起步两阶段实验用于核查工程和基本遗忘现象；若最后研究问题坚持无切换提示，则需要额外验证算法在不知道天气切换点时的重要性估计、教师更新、缓存维护及归一化策略。LIT-007的EWC/MAS/LwF比较行获得边界信息；LIT-009的完整阶段聚类和LIT-016的任务末校准也依赖分段，不能直接记为无边界方案。[LIT-007报告第1/5节](../paper_reports/LIT-007_simcs_odics.docx)、[LIT-009报告第1/5节](../paper_reports/LIT-009_replay_smart_data_selection.docx)、[LIT-016报告第1/2节](../paper_reports/LIT-016_air_geometric_consistency_ocil.docx)

## 本次核查的公开复现资源

截至2026-10-26，仅核查下列公开页面及仓库目录，没有下载权重、安装环境或运行训练。

| 对象 | 本次可确认内容 | 对启动的实际含义 |
| --- | --- | --- |
| [LIT-010作者仓库 feature-reuse-css](https://github.com/tobiaskalb/feature-reuse-css) | 提供增强YAML、示例、预训练权重入口和模型来源；当前目录未见完整训练主程序 | 可复用配方和模型来源，仍需搭建训练与持续评价流程；不能称为完整可直接运行工程 |
| [LIT-008/009作者仓库 disjoint_cityscape_splits](https://github.com/tobiaskalb/disjoint_cityscape_splits) | README明确关联两篇论文，主要内容是Disjoint Cityscapes三阶段JSON及标签映射 | 属于类增量划分资源，不能当成DIL训练工程 |
| [SimCS原文与附录](https://arxiv.org/html/2211.16234v2) | 已核对核心对照、边界例外与缓存配置；本次有限标题/作者检索未定位可确认的官方完整训练仓库 | 不断言未开源；严格复现仍需核对实现来源、数据划分及模拟数据准备 |

LIT-010仓库README指定DeepLabV3+来源为segmentation_models.pytorch，并列encoder_name=resnet50、encoder_output_stride=8、decoder_channels=512。精确复现需要保留这些配置并固定兼容版本；不能直接采用库默认参数后声称等价。[作者README Model Sources](https://github.com/tobiaskalb/feature-reuse-css#model-sources)

LIT-013/014的既有报告已记录官方代码核查，LIT-015报告未定位可确认官方训练仓库，LIT-016报告记录匿名仓库401。本次没有重新核验后三项的当前访问状态，不把此前记录扩展为当前可运行性结论。

## 容易混淆的名称与证据边界

- FT和NT在这里均指基础顺序训练，但不同论文的初始化、BN策略、学习率和迭代预算并不相同。
- DeepLabV3、DeepLabV3+、ERFNet、SegFormer、Mask2Former是网络架构；EWC、LwF、ER等是持续学习机制。LIT-007使用DeepLabV3，LIT-010主要使用DeepLabV3+／R50。
- LIT-008的“CIL法”是特定分割蒸馏方法名；CIL也可表示类增量设定，两种含义须区分。
- LIT-016主表DER为Dynamically Expandable Representation；DER++为Dark Experience Replay相关方法，不能混称。
- Joint/Offline/Supervised组可重访完整历史数据，作为离线参考；GT/DW等使用额外真值，作为诊断。二者都应与符合目标信息约束的持续学习组分开解释。
- 本文不核定方法在整个领域的热门程度，不按年份或会场直接选基线。当前候选方向来自PROJECT_STATE，最终资源、协议和研究方案仍未定案。

本文由AI辅助完成报告文本提取、对照整理和公开资源核查；没有形成新的实验有效性证据，也未修改逐篇报告、正式研究方向或研究决策。
