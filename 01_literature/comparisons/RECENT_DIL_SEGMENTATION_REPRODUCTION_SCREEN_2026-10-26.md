# 2024至2026年域增量持续分割文献补检与复现选型修正

2026-11-02设定补记：用户已确定课题天气变化无明显域边界，见[D-007](../../00_management/DECISIONS.md)。本文保留原检索时的候选判断、文献原协议与代码核验范围；阶段式方法不因此改写为无边界方法，其道路适配须另行验证。当前主场景与对照规划以[PROJECT_STATE](../../00_management/PROJECT_STATE.md)及[对照总表](../../03_experiments/COMPARISON_PLAN.md)为准，本次未重新检索或变更逐篇阅读状态。

日期：2026-10-26（Asia/Shanghai）。本次按用户要求，在同日初筛基础上扩展检索并复核原文，回答为何LIT-007–010偏旧、2024年及以后有哪些符合域增量持续分割的新工作。时间上包含2024年，优先检查2025–2026年；截至2026-10-26，不含尚未公开的未来研究。本文是定向检索与来源核验，不是系统性综述、规范逐篇阅读报告或训练复现记录。6篇已下载原文登记为LIT-023–028；当前MILE、PSS、GSMF-RS-DIL及另行入库的FOCUS（LIT-033）已形成正式阅读报告，实际阅读状态以[文献索引](../LITERATURE_INDEX.md)为准。Traffic Scenes另登记为LIT-032，仅书目已核实，全文待获取。本次补录MDIL-SS、MineC2FNet、BECoTTA、Hybrid-TTA和GOLD为LIT-034–038，均为未读，未新增本地正式PDF或逐篇报告。索引收录与取得本地PDF分别记录。CTTA条目按D-002仅作相邻资料，文中早期替代主路线建议已撤回。

## 为什么此前推荐与师姐／组内文献差异明显

从已有清单和阅读路线可以确认，此前检索集中于SimCS和Kalb的一条早期研究线，关注问题定义、协议和遗忘机制，缺少2025–2026年原始方法、作者后续工作和公开工程的覆盖。这是此前检索不充分；旧论文适合作为基础参照，但不能代替新近方法候选清单。不能据此判断域增量分割没有新工作或普遍不开源。SimCS的正式发表年为2024，并非四篇全部早于2024。

另一项差异来自研究范围：LIT-012/013/014是类增量分割，LIT-015是类域联合增量检测，LIT-016是在线类增量分类；LIT-011覆盖类、域和监督联合变化。它们能提供现代方法线索，但不能将其方法数量或代码数量直接当作固定类别道路天气DIL的对照。这里是研究设定区别，不是降低新近检索要求的理由。

相关工作引用、主实验比较、仓库已有实现、在本机跑通，是四种不同证据。“方法多”不能单独证明更适合作为本课题基线；“首页无代码链接”也不证明未开源。例如LIT-010确有[作者资源仓库](https://github.com/tobiaskalb/feature-reuse-css)，主要公开增强配置、示例和模型来源，尚不能据此称完整训练工程。较早的[LIT-034：MDIL-SS，WACV 2022](https://github.com/prachigarg23/MDIL-SS)则有分阶段训练与评价代码。此前应把代码状态作为独立筛选项，而不能由年份或首页排版推断。

## 本轮结论

应先补齐2024–2026年的相关方法和代码证据，再确定主复现对象。EWC/LwF是可保留的经典比较方法，不应成为进入现代方法复现前必须逐一重写和训练的前置课程。更合适的顺序是：选择设定适配且开源材料较完整的工程，在其框架内跑通基础对照和本文方法，再补最终论文需要的其他对照。

本轮新增的关键遗漏是MILE：PSS作者团队在ICPR 2026发表了直接面向天气、地理和模态域增量分割的LoRA专家方法。它比泛化到其他任务的新方法更值得先核对。保留LIT-007–010作为协议／机制参照，同时用MILE、PSS及待核全文的Traffic Scenes补齐直接道路DIL候选。

检索时（2026-10-26）的有标注、无显式域切换提示均为候选；现已按D-007确定无明显天气边界，监督等其余权限另定。以下分别列直接道路DIL、类别与域联合变化、持续测试时适应；保留各论文原设定，不将其直接当作已满足本课题无边界主场景的证据。

## 检索范围与领域主干

检索时间范围为2024-01-01至2026-10-26，另保留早期问题定义与公开基准工程。核心检索词包括domain-incremental semantic segmentation、domain incremental segmentation、online domain-incremental continual segmentation、adverse driving conditions；另用continual test-time adaptation检查相邻研究，单独标明监督差异。采用题名、作者及GitHub补查，沿综述、PSS→MILE作者后续工作和引用链追踪；检索命中数不是去重后的研究数量，不报告PRISMA式覆盖率。

主干先核对以下四类资料，再纳入后面的新近补充：

| 主干角色 | 文献或基准 | 本轮用途与边界 |
| --- | --- | --- |
| 持续分割综述 | LIT-006，Yuan与Zhao；[作者维护的SurveyCSS](https://github.com/YBIO/SurveyCSS)；[出版商登记](https://api.crossref.org/works/10.1109/TPAMI.2024.3446949) | 已核实正式发表于IEEE TPAMI 46(12):10891–10910，2024；本地仍是arXiv v2。综述和持续更新清单用于发现文献，不能代替每篇原文核验；清单中的大量CIL论文须排除或另列。 |
| 在线有标注DIL协议 | [SimCS，AAAI 2024](https://ojs.aaai.org/index.php/AAAI/article/view/28952)，LIT-007 | 密集标注、计算受限、四数据集顺序流；支撑在线协议比较，非纯天气变化。 |
| 天气遗忘机制与两阶段评价 | [Kalb与Beyerer，CVPR 2023](https://openaccess.thecvf.com/content/CVPR2023/html/Kalb_Principles_of_Forgetting_in_Domain-Incremental_Semantic_Segmentation_in_Adverse_Weather_CVPR_2023_paper.html)，LIT-010 | CS→单个ACDC天气的独立两阶段路线；保留浅层表征、BN/CN和保持／适应权衡证据。 |
| 公开多域工程与数据主干 | [LIT-034：MDIL-SS，WACV 2022作者代码](https://github.com/prachigarg23/MDIL-SS)；Cityscapes、ACDC、BDD100K、IDD（LIT-017/019/021/022）；SHIFT见PSS原文§4.1 | MDIL采用域专属组件，部分标签异构且推理用域ID，不能自动等同于无提示固定类DIL。道路数据集负责域和标签协议，不能把单次分割基准成绩当持续学习成绩。 |

本轮未定位到一份可确认覆盖截至2026年、专门面向“有标注、固定类、未知训练边界的道路天气DIL”的完整综述或统一排行榜；现有持续分割综述加原始协议／作者引用链共同作为检索主干。这是本次检索的边界，不是断言此类资料不存在。本文不按论文数量、会场或期刊JIF给新方法评学术影响力；未系统核实被引量和后续采用情况，因此不宣称下列新论文已是公认代表作或领域最强。

## 优先阅读：直接道路域增量新文献

| 工作 | 年份与发表信息 | 本次确认的研究设定及纳入依据 | 开源核查与当前角色 |
| --- | --- | --- | --- |
| **LIT-023：[MILE: Mixture of Incremental LoRA Experts for Continual Semantic Segmentation across Domains and Modalities](https://arxiv.org/html/2605.03555v2)** | **ICPR 2026**；[Springer正式章节](https://link.springer.com/chapter/10.1007/978-3-032-31438-3_26)首次在线2026-08-06，LNCS16821:387–401，章节引用年2027；不是尚未录用的纯预印本 | §3–4/Table1：有标注、19类，CS日间→ACDC雾→雨→雪→夜间。冻结SegFormer-B5基础网络，为每阶段新增LoRA专家，以ConvNeXt-Tiny域原型路由测试图像；训练阶段边界已知，测试无需真实域ID。**与当前天气DIL最直接的新近方法候选** | 已核对arXiv v2正文、主表及PDF第8页表图，并以[ICPR录用名单](https://icpr2026.org/acceptedPapersTrack.html)和Springer核实发表。本次在全文、作者机构页和题名／作者+GitHub检索中未定位可确认官方训练仓库；值得优先读，不能称开源即用。 |
| LIT-024：[Domain-Incremental Semantic Segmentation for Autonomous Driving Under Adverse Driving Conditions／PSS](https://arxiv.org/html/2501.05246v1) | ICPRAM 2025，496–506；[正式论文](https://www.scitepress.org/Papers/2025/132491/132491.pdf)，DOI 10.5220/0013249100003905 | 固定类别道路分割，使用CS、ACDC及SHIFT；为每个训练域学习分割专家和自编码器，测试按重建误差选择专家。§3/算法1按已知任务建立新专家；测试无需真实域ID，不等于训练无切换提示 | 已核对方法、训练及结果节；在所查原文、标题/作者和GitHub仓库元数据检索中未定位可确认官方训练工程。优先深入阅读的直接相关对象，暂不能按“开源即用”选中 |
| LIT-032：[Domain-Incremental Semantic Segmentation for Traffic Scenes](https://doi.org/10.1109/TITS.2024.3525005) | IEEE TITS 26(4):5067–5081，2025-04；Crossref DOI登记核对 | 标题与书目确认其直接面向交通场景DIL；原文全文本次未能取得，实验协议、指标及结果未核实 | 已登记文献索引，状态未读、全文待获取；未确认官方训练仓库。暂不作核心效果推荐，不把检索摘要当成完整方法核验 |

MILE Table1在学完五域后的域平均mIoU为**64.14**，同表FT为58.85、EWC为59.18、ILT为57.04、联合训练为66.85；64.14是五域最终均值，不是遗忘率。MILE训练仍按已知阶段建立专家，专家及原型存储随域数增长。表中ST/PSS†是由单任务模型代表的oracle域选择参考，不能说已经完整复现PSS自动路由后证明MILE优于它。以上不能外推为未知训练边界或相同参数预算下成立。[arXiv v2 §3–4/Table1](https://arxiv.org/html/2605.03555v2#S4)

PSS（LIT-024）§4.4/Table1在CS→整体ACDC两阶段报告PSS最终均值60.53、FT51.70、生成回放44.79、joint61.67。其中Replay使用GANformer生成图像并由旧模型产生伪标签，不是真实旧图像及标签ER。PSS保存多个完整域专家；不能把其结果同MILE五天气协议、SimCS或本项目未运行的实验横比。[原文§4.4/Table1](https://arxiv.org/html/2501.05246v1#S4.SS4)

Traffic Scenes本次核实作者为Yazhou Liu、Haoqi Chen、Pongsak Lasang、Zheng Wu，[IEEE记录ID为10843143](https://ieeexplore.ieee.org/document/10843143/)，[出版商登记元数据](https://api.crossref.org/works/10.1109/TITS.2024.3525005)确认2025年4月卷期；DOI含2024不代表正式发表年。IEEE正文未取得，因此固定类别、监督、训练／测试域ID、数据流和效果均待核实。本次不能因题名就把它列为已验证主复现对象。

## 在主干之后补充：其他应用的DIL及联合变化

以下不是道路天气领域的代表作排名；按其明确的DIL设定或可借鉴机制纳入，应用差异及代码状态分别记录。

| 工作 | 年份、发表状态与实际证据 | 对本课题的用途及代码状态 |
| --- | --- | --- |
| **LIT-025：[Remembering by Reconstructing: Domain Incremental Learning With Test-Time Training on Video Streams](https://arxiv.org/html/2605.31108v1)** | 2026-05-29预印本，正式录用待核实。§3–4：按域训练LoRA、测试利用MAE重建在线更新LoRA混合系数；分割使用Domains-Campus与SAM3生成标签，非CS→ACDC。Table1分割FAA（Dice）0.458±0.007、遗忘0.011±0.010；FAA不是道路mIoU | 用于借鉴连续视频中域专家恢复和测试时选择；训练分阶段、测试无标签，不是仅靠源模型的标准CTTA。摘要称代码／数据将在发表后发布；本次未定位完整公开资源。 |
| **LIT-026：[GSMF-RS-DIL](https://github.com/HuangWBill/GSMF-RS-DIL)**，完整题名见索引 | **IEEE TGRS 2024**，DOI10.1109/TGRS.2024.3481875。原文§III-D、IV：Potsdam→Vaihingen六类、LoveDA Urban→Rural七类，均为监督两阶段固定类DIL；图空间推理、早期层冻结及多特征蒸馏。TablesIX/X已核对 | **可优先审查的开源DIL工程补充**，但为遥感，且只验证双域。作者仓库有训练、配置、模型、日志和权重入口；配置含projects.DIL路径，[Issue1](https://github.com/HuangWBill/GSMF-RS-DIL/issues/1)／[Issue2](https://github.com/HuangWBill/GSMF-RS-DIL/issues/2)记录导入问题。已发布≠本机已跑通。 |
| **LIT-033：[FOCUS: Feature Replay with Optimized Channel-Consistent Dropout for U-Net Skip-Connections](../../第三批文献/LIT-033_Joham_2025_FOCUS_MICCAI.pdf)** | **MICCAI 2025**，LNCS15973:219–229，DOI10.1007/978-3-032-05185-1_22。医学固定类别监督DIL：海马三域、前列腺四域；训练阶段边界已知，首域后冻结编码器，以稀疏首层特征回放保留U-Net跳跃连接，结合CCD、域平衡采样和GIN增强。默认推理使用最后训练头，不按真实测试域选择历史头 | **已有代码的DIL工程补充，工程验证顺序在GSMF之后**。已完成[B级重点精读报告](../paper_reports/LIT-033_focus_sparse_feature_replay.docx)及作者代码静态核对；[官方工程](https://github.com/imigraz/FOCUS)有FOCUS、Seq.、EWC、MiB、TED、ccVAE等训练与评价入口。医学到道路迁移、首域后冻结的适应限制、回放目标及实际缓存成本仍需验证；未安装或训练，尚未选为主基线。 |
| **LIT-027：[Smoothing Continual Segmentation Oscillations with Latent Domain PPCA Decoder／MoPPCA](https://proceedings.mlr.press/v292/boum25a.html)** | **TerraBytes ICML Workshop 2025**，PMLR292:124–140，非ICML主会。§3、5：FLAIR十地理域有标注序列、固定建筑／背景二类，冻结DINOv2并保存域／类PPCA统计，测试自动推断域。Table2最终mIoU0.76、OI0.16、MAS0.008 | 补充长域序列、性能振荡和统计专家机制；OI/MAS衡量波动，不能直接当遗忘率。仅建筑二类不能直接证明道路19类有效。本次查全文／PMLR及作者题名检索，未定位可确认官方代码。 |
| **LIT-028：[Learning with Style: Continual Semantic Segmentation Across Tasks and Domains／LwS](https://www.research.unipd.it/handle/11577/3513552)** | **TPAMI 2024**，46(11):7434–7450，DOI10.1109/TPAMI.2024.3397461；首次预印本2022。已取得作者机构公开的期刊正式版。类与域联合变化、风格迁移和蒸馏，不当作2024首次提出的纯DIL新方法 | [作者仓库](https://github.com/marco-toldo/LwS)有训练／测试和划分代码，适合作为工程与联合变化补充；固定类配置的损失及评价仍需核对。此前静态初筛发现部分脚本参数适配问题，见下表。 |

GSMF TablesIX/X的结果须保持原口径：ISPRS旧／新域为61.91/65.81 mIoU，LoveDA为51.02/36.21；其ΔmIoU是相对各域单任务参考的平均相对变化，非历史最佳到最终的遗忘率。单域分割表中的大量架构也不能计作增量实验比较方法。PPCA Table2的MoPPCA与高维DIPPCA最终mIoU同为0.76，主要差别之一是波动；不能笼统写“全面最好”。[GSMF原文TablesIX/X](https://raw.githubusercontent.com/HuangWBill/GSMF-RS-DIL/master/paper.pdf)，[PPCA原文Table2](https://raw.githubusercontent.com/mlresearch/v292/main/assets/boum25a/boum25a.pdf)

另一条2026补充线索[LIT-035：MineC2FNet](https://ijcai.org/proceedings/2026/800)已正式发表于IJCAI2026的AI and Social Good分支，研究粗标签域→细标签域矿区分割。本次重新核对[作者仓库](https://github.com/risqiutama/MineC2FNet)，已确认包含训练入口、TensorFlow/Keras蒸馏实现和配置，撤回早期“只有README占位”的描述；数据及权重链接内容、可运行性与论文效果仍未验证。原文旧粗域成绩明显下降、作者以标签粗细差异解释，故不把新域得分直接视作保持旧域能力的证据；未纳入此前六篇入库原文，本次仅补录索引，状态未读。

## 无标注持续适应分支的公开工程

本节在同日初筛基础上再次核对公开工程。CTTA不代替上面的有标注DIL文献；但对于尚未限定目标流监督方式的“视觉条件变化下道路持续分割”课题，它可以成为正式研究及主复现候选路线，不只是方法借鉴。采用前需明确改变的是目标域监督、更新与评价协议。

这一分支与天气、光照、持续更新、固定类别及无测试域提示高度相关，但目标流无像素标签，通常以在线流上预测评价为主。它与目前候选的有标注DIL，在监督、源数据访问、更新时机和遗忘评价方面有差别。选择它作主方案意味着需要明确研究设定调整。

| 工作 | 年份与原始来源 | 场景与核验边界 | 作者代码初筛 |
| --- | --- | --- | --- |
| BECoTTA（LIT-036） | [ICML 2024，PMLR 235:27072–27093](https://proceedings.mlr.press/v235/lee24ab.html) | 面向CTTA的低秩专家混合，覆盖天气分割；本次重点核对正式摘要和README，未复核全套结果 | [官方仓库](https://github.com/daeunni/BECoTTA)提供环境、ACDC配置和初始化权重入口。README注明当前公开版为w/WAD；渐变场景构造与warmup初始化仍在TODO中，材料完整性须分实验判断 |
| Hybrid-TTA（LIT-037） | ICCV 2025，2877–2886；[正式论文](https://openaccess.thecvf.com/content/ICCV2025/papers/Park_Hybrid-TTA_Continual_Test-time_Adaptation_via_Dynamic_Domain_Shift_Detection_ICCV_2025_paper.pdf)；首次预印本2024 | CS→ACDC多轮持续适应，动态域偏移检测、全量/适配器更新切换及重建辅助任务。核对摘要、实验比较和效率表；不是有标注目标流训练 | [官方仓库](https://github.com/hhhyyeee/Hybrid-TTA)于2025-10-28宣布代码发布，包含环境、ACDC配置、scripts/ours.py和源权重入口；尚未安装运行，老版本PyTorch/MMCV依赖需核对 |
| GOLD（LIT-038）／The Golden Subspace: Where Efficiency Meets Generalization in Continual Test-Time Adaptation | [CVPR 2026，3866–3875](https://openaccess.thecvf.com/content/CVPR2026/html/Lai_The_Golden_Subspace_Where_Efficiency_Meets_Generalization_in_Continual_Test-Time_CVPR_2026_paper.html)；[预印本原文](https://arxiv.org/html/2603.21928v1) | §5.3/Table 3在CarlaTTA合成道路流测试昼夜、雾、雨、混合变化及highway；核对问题设定、方法概述、分割结果和仓库 | [官方仓库](https://github.com/AIGNLAI/GOLD)提供Linux/CUDA环境、segmentation目录、GOLD配置、数据及源权重入口，并包含分割版TENT/CoTTA/MEMO/GTTA等。适合优先审查“新近且涵盖多种比较方法的工程”；没有验证下载链接和运行结果 |

GOLD的Table 3并非所有序列最好：day2night、clear2fog、highway较强；dynamic中GOLD48.9低于TENT50.8，clear2rain中GOLD71.0也低于Source71.8。故“年份最新、论文称SOTA”不能独立决定本项目主对象；应比较同一监督、数据、骨干与预算下的保持、适应及成本。[原文§5.3/Table 3](https://arxiv.org/html/2603.21928v1#S5.SS3)

## 代码核查的可追溯记录

本次通过GitHub API核对目录及分支提交，并静态读取README、部分配置与入口。以下提交不代表已安装、已跑通或可复现论文全部数字。

| 仓库 | 固定提交 | 本次看到的实物与问题 |
| --- | --- | --- |
| GOLD（LIT-038） | 0bd18942e804df7dbccc01609f4f59effcc85ff7 | segmentation/test_time.py、cfgs/gold.yaml；methods中含gold、tent、cotta、memo、gtta、asm、bn、norm_ema、sm_ppm等。分类目录的方法不能自动算作已有分割实现 |
| Hybrid-TTA（LIT-037） | 7ea3c93fede7ac1e1ff3c425523b9060cae1e16b | scripts/ours.py、local_configs、mmseg/mmpretrain及requirements；源检查点需另取 |
| BECoTTA（LIT-036） | 388f3188e0b8a526b885a3ede56b17c1d964053c | 提供在线主流程；README对渐变场景构造、warmup仍列TODO。未检验初始化权重实际可下载性 |
| LwS | f786069a8d863fe35ed865d549e2e813e7adbfd0 | main.py/train.py/test.py、数据划分和脚本。scripts/Shift.sh使用的continue_training、save_or_load_from_common、save_or_load_from_iter三个选项在utils/arg.py中未找到；需核对入口解析、修正示例再运行。CBI.sh的选项与该参数文件静态匹配 |
| FOCUS（LIT-033） | 未固定提交；2026-10-26的master分支快照 | nnunet_ext/training/network_training/focus/nnUNetTrainerFOCUS.py、setup.py中的训练入口及README评价命令均有实物；已完成精读与静态核查。回放目标、CCD缩放、冻结范围和实际缓存成本待动态验证。[缓存代码与来源记录](../../tmp/strict_dil_audit_2026_10_26/)；未安装或运行 |

GOLD、Hybrid-TTA、BECoTTA和LwS四项是同日先前初筛固定提交，不追认为完整工程或效果核验；FOCUS另按未固定提交的分支快照记录。本轮新增GSMF静态检查：tools/train/train_GSMF-RS-DIL.py、configs/gsmf_rs_dil_r101-d8_4xb4-80k_ISPRS-512x512.py、mmseg/segmentors/DIL_encoder_decoder.py等实际文件；推理入口只调用适应后分支，未看到外给测试域ID参数。文件快照及路径问题见tmp/dil_refresh_2026_10_26/remote/evidence_remote.md。**LIT-026确有官方训练代码，不是LIT-023–028中只有LwS公开实现。**没有安装／训练、验证权重下载或复现论文数字。

本轮已入库6篇PDF及[来源／SHA-256清单](../papers_recent_dil/SOURCE_MANIFEST.json)，阅读入口见[文献索引LIT-023–028](../LITERATURE_INDEX.md)。原文表图核验包括MILE PDF第8页、GSMF第12/14页、PPCA第8页；不将局部核验记为全文精读。先前代码快照保留于tmp/recent_dil_2024_2026/；本轮全文提取、书目响应、表图和未取得Traffic Scenes全文的证据暂存tmp/dil_refresh_2026_10_26/。未下载模型权重或完整数据，未触发训练，未向外部模型发送组内匿名稿。

## 不开源论文怎样复现，以及CTTA是否适合作为主对象

### 阅读价值与工程启动分别判断

MILE、PSS与天气DIL相关，适合优先阅读；这不构成优先从零重建它们的充分理由。LIT-023–028是相关文献清单，不应按编号逐个复现。首个主对象还应有可取得的实现、源权重、数据协议及合理计算成本。未定位官方仓库不能写成已证实未开源；GSMF与LwS则已确认有真实训练代码，工程完整性和设定匹配另作判断。

无作者代码仍可独立实现：先使用公开分割框架和相应预训练权重，依据原文重写核心模块、损失、训练流程和评价，再对照原协议的基础方法、主结果及消融。缺少的超参数、预处理、初始化等必须记录为未报告及本项目实现假设，不能把合理猜测当作者实现。可查询作者材料或取得作者答复；本轮没有联系作者。工程跑通只表示实现能运行，不能据此声称恢复了论文效果。

若关键细节或资源始终缺失，更适合将工作定位为独立实现、机制验证或改编实验。鉴于当前尚未启动训练，不建议为首个主对象优先承担大量闭源工程重建成本；论文机制仍可用于方法设计。

本次较少找到同时满足“新近、道路天气、固定类别、有标注目标流、训练未知边界、官方工程完整”的对象，但没有完成足以统计全领域供给的系统性检索，不能推出该领域没有开源方法。当前资料更充分支持的判断是：已核实的直接道路DIL候选仍有工程缺口；CTTA已有多套面向相同天气变化问题的公开工程，值得进入正式选型。

### 两种研究设定的具体差别

| 维度 | 当前有标注DIL候选 | 无标注CTTA候选 |
| --- | --- | --- |
| 源模型 | 可以先在有标注Cityscapes上训练 | 同样可用有标注Cityscapes训练的源模型，不是全程无监督 |
| 新域更新 | 使用新天气的像素真值计算监督损失 | 新天气真值不进入适应更新；可用伪标签、一致性、熵或重建等信号 |
| 数据与标签 | Cityscapes、ACDC等可用于监督序列 | 仍可用相同数据，但目标标签只交给评价程序，不因数据集带标注就失去CTTA资格 |
| 历史信息 | 是否回放旧图像/标签、是否可见边界由协议指定 | 常限制适应时访问源数据；教师、缓存、初始化和域间状态是否重置须逐方法核对 |
| 评价 | 各阶段×各域mIoU、旧域遗忘、新域适应等 | 原协议的流上分域/分轮mIoU与连续适应；原域保持或固定旧域探针需单独评价 |
| 部署含义 | 适合获取新条件标注后继续训练模型 | 若目标是部署后面对无标签新场景直接更新，CTTA更自然；实际实时性仍需测量 |

CTTA并非只有一次目标域适应：其核心是持续变化中保持更新状态，避免适应累积造成性能下降。流上平均mIoU改善不自动证明所有旧域都保留；新增保持评测时只做不更新的测量，不能让旧域评价图像改变模型状态后再继续原序列。先预测后更新或同帧适应后预测等时序，以原论文和实现为准。

### 三个CTTA工程的启动优先级

| 候选 | 本轮确认的实物 | 优先条件及未解决项 |
| --- | --- | --- |
| **LIT-037：Hybrid-TTA，ICCV2025** | 官方README、scripts/ours.py、B5适应配置及requirements均可公开读取；配置use_gt=False，提供Cityscapes源权重入口与ACDC运行命令 | **真实天气CS→ACDC方向优先验证**。原文§5.1为四天气循环10轮，采用SegFormer-B5；旧PyTorch/MMCV依赖、完整数据/权重可获取性、实际显存和速度尚未运行验证。[作者工程](https://github.com/hhhyyeee/Hybrid-TTA)、[原文](https://openaccess.thecvf.com/content/ICCV2025/papers/Park_Hybrid-TTA_Continual_Test-time_Adaptation_via_Dynamic_Domain_Shift_Detection_ICCV_2025_paper.pdf) |
| **LIT-038：GOLD，CVPR2026** | segmentation/methods/gold.py、cfgs/gold.yaml、test_time.py及环境文件可读取；分割入口实际导入并配置Source、TENT、CoTTA、GOLD等 | **渐变视频流或多对照工程方向优先验证**。原始分割协议是CarlaTTA合成道路流，非ACDC；先验证原协议，迁移ACDC属于新增实验。公开环境为Linux/CUDA，数据/源权重下载及运行结果未验证。[作者工程](https://github.com/AIGNLAI/GOLD)、[原文§5.3](https://arxiv.org/html/2603.21928v1#S5.SS3) |
| **LIT-036：BECoTTA，ICML2024** | 作者提供MoDE专家适应代码、ACDC配置和初始化权重入口 | 适合补充低秩专家方法。README注明公开版基于w/WAD，渐变场景构造和warmup初始化仍列TODO；恢复全部论文实验的准备材料不齐，应降低首次完整复现的优先级。[作者工程](https://github.com/daeunni/BECoTTA)、[正式论文页](https://proceedings.mlr.press/v235/lee24ab.html) |

上述优先级依据数据贴合和工程材料，不是跨协议性能排名。Hybrid-TTA/GOLD都值得作为主复现候选，不必因为此前有监督设定只是候选，就将它们永久排除。当前建议先做Hybrid-TTA的环境、源权重与小段ACDC流验证；若重点是连续渐变或需要统一多方法框架，则先做GOLD原始CarlaTTA验证。CTTA路线尚未最终选定，当前没有启动正式实验。

选择CTTA后，对照应优先核对Source、TENT、CoTTA及选中方法；不能把使用目标真值的FT/ER直接与无标签CTTA当成同监督对照。比较需统一源检查点、初始化预热、目标标签权限、源数据访问、缓存、分辨率、更新时序与计算预算。只更新少量参数不代表总模型很小，尤其SegFormer-B5的部署成本仍需实测。

本轮再次直接读取Hybrid-TTA、GOLD、GSMF的12个公开源文件并保存快照及SHA-256于tmp/ctta_reproduction_audit_2026_10_26/；GitHub API遭遇限流，因此没有重新确认当前HEAD提交，先前固定提交与本轮分支文件快照分别记录。没有安装环境、下载完整数据/权重或执行适应。本节为复现选型建议，不修改PROJECT_STATE中的监督设定，不记录已完成复现。

## 对师兄建议的具体采用方式

“新近、效果强、开源较完整、覆盖前人方法”是合理的主复现对象筛选原则。实际采用时，顺序应为：先判断任务与监督是否可比，再比较同协议效果及资源成本，最后检验工程能否运行。相关工作引用过一个方法，不等于实验表比较过；表里比较过，不等于公开代码包含对应实现；实现存在，不等于在本机、分割任务及同协议下已验证。

可执行的选型建议是：

1. 有标注DIL候选设定暂不变时，优先读**MILE→PSS**，核对阶段边界、LoRA专家增长、路由与预算；继续取得Traffic Scenes全文。已有代码的DIL工程按**GSMF（LIT-026）→FOCUS（LIT-033）**进入运行与迁移可行性评估；二者的精读与静态核查已完成，FOCUS需重点核对特征回放目标、缓存成本、冻结限制及医学到道路的适配。LwS作联合变化／工程补充。保留SimCS和天气遗忘论文作为协议／机制参照，不先把四篇旧论文全部重建。论文阅读优先级与工程启动优先级分别判断。
2. 若研究问题选择无标注天气连续适应，则优先审查GOLD和Hybrid-TTA，BECoTTA补充专家路由与渐变条件。GOLD工程覆盖多种分割对照，Hybrid-TTA更直接使用CS→ACDC；不能跨两套数据表宣布谁总体最强。
3. 将本轮已找到的候选压缩为少数工程进行环境、数据、权重及小规模预测验证。选中工程后，先跑原协议的Source/FT等基础对照与本文方法；有标注DIL补ER，再按最终比较需要加入EWC/LwF。无标注CTTA则优先使用该领域可比的Source、TENT、CoTTA等。
4. 不必等待所有新论文精读完才开始准备环境；也不宜在未审查新工程前投入大量时间逐个手写经典方法。早期小规模运行只验证工程，正式研究结论仍需原协议、明确预算和重复实验。

目前尚不能在保持所有候选约束不变的同时，指定一篇“最新、效果最好、完整开源、精确满足无边界有监督天气DIL”的已验证答案。**MILE很贴近天气DIL，但训练边界及公开工程仍有限制；GSMF有真实训练代码，但应用和双域协议有差异。**缺的是少数候选的协议与工程核验，不是先完成一套EWC/LwF课程。当前不更改研究方向、不预先选定主基线。

本轮由academic-research-suite及PDF技能辅助完成定向检索、书目／原文核验和选型分析，并将Traffic Scenes来源核查与遥感补充核查委托给两个有界子任务。没有执行系统性综述、影响力排名、训练或效果复现；未取得原文、未定位仓库和代码仅有占位，分别记录，不相互替代。

## 2026-10-30 医学DIL遗漏复核与补检

用户指出：TED及ccVAE已经是FOCUS比较的域增量持续分割方法，为何此前近期文献检索未纳入。回查时，本索引最大编号为LIT-041，未独立登记两篇题名；旧检索报告只在FOCUS行列出TED/ccVAE作为代码或实验对照。FOCUS正文p.5的§2.1、p.6–8主表和参考文献[11]/[25]已经提供了明确线索。这是检索覆盖与引用链跟进的遗漏，不能以医学应用或2024年份为排除依据。

### 可从项目记录确认的流程缺口

1. 早期检索沿SimCS/Kalb线索并优先筛道路天气对象，后续虽扩到医学和遥感，覆盖仍不完整。应用相关性应决定阅读及复现优先级，不能代替DIL领域收录标准。
2. FOCUS已完成正式报告，相关对照及参考文献却未转为逐篇身份与设定核验，引用链没有闭环。仅知道“某篇论文比较了TED/ccVAE”，不等于已经系统纳入其原始研究。
3. “符合DIL的领域文献”与“当前适合作为主复现对象的工程”没有保持足够清楚的输出边界。代码、应用及资源限制是第二步筛选条件；未入选工程清单不能被解释为不存在相关文献或没有公开资源。

以上根据现存清单、报告与决策记录归纳，不能据此复原每一次具体搜索或把搜索关键词失误当成已证实的唯一原因。两篇都是2024年，均在原报告2024–2026时间范围内。本次没有证据支持它们因不属于DIL而被合理排除。

### 已补录的原始论文

| 文献 | 核实的身份与设定 | 资源核验及剩余工作 |
| --- | --- | --- |
| LIT-042 TED | Zhu等，*Boosting knowledge diversity, accuracy, and stability via tri-enhanced distillation for domain continual medical image segmentation*；MedIA94:103112，2024，DOI10.1016/j.media.2024.103112。作者摘要与仓库说明其为域持续医学分割，采用知识蒸馏减轻遗忘。 | [作者摘要及书目](https://pubmed.ncbi.nlm.nih.gov/38401270/)；[作者公开项目](https://github.com/PerceptionComputingLab/TED_DCMIS)明确链接论文并提供项目结构及运行说明。未逐表核验、审查完整训练代码或运行。 |
| LIT-043 ccVAE | Lemke等，*Distribution-Aware Replay for Continual MRI Segmentation*；PILM2024，LNCS15197:73–85，DOI10.1007/978-3-031-73483-0_7；原文§2明确域增量MRI分割、域/切片位置双条件和特征生成回放。 | [Springer正式章节](https://link.springer.com/chapter/10.1007/978-3-031-73483-0_7)；[作者全文§2](https://arxiv.org/html/2407.21216v1#S2)。原文与出版商给出[Lifelong-nnUNet的cl_vae分支](https://github.com/MECLabTUDA/Lifelong-nnUNet/tree/cl_vae)，已读分支README；未核验ccVAE训练入口完整性、依赖或可运行性。 |

两篇的正式阅读状态仍为“未读”，仅作检索级核验，不产生虚构的全文阅读、实验复现或用户已读记录。VAE是通用模型，ccVAE才是这里对应的具体持续分割方法。

### 本次修正的范围

补齐已确认的两篇遗漏及其来源，不声称已完成全领域穷尽检索，不因补录自动推翻或重选D-006的GSMF主基线。后续比较复现对象，应把这两篇加入相同的监督、训练/测试边界、历史数据访问、代码与资源核查表后再评价。

作者TED仓库当前还列出CauAug_DCMIS、TKRL_DCMIS后续研究链接。本次只记为待核实线索，尚未核对完整书目、发表年份和原始实验设定，不预先列为已确认核心候选。后续引用链应按“综述/基准→原始对照→作者后续研究”逐项跟进；相关性、代码状态和研究类型分开记录。

