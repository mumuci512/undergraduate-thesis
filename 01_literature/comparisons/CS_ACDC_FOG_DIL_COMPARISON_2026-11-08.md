# Cityscapes 与 ACDC-fog 域增量分割：文献及本项目结果对照

核查日期：2026-11-08。用途：道路天气 DIL 的进度交流与实验对照选型。按 academic-research-suite 的文献核查流程，结合本地原文、正式出版入口和作者预印本逐表核对；本次是定点比较，不新增逐篇阅读完成或实验完成记录。

**结论：有。最接近本项目两阶段监督协议的是 Kalb 与 Beyerer 的 CVPR 2023 工作；较新的 MILE（ICPR 2026）也单列 ACDC-fog，但报告的是五域序列全部学完后的结果。PSS（ICPRAM 2025）将 ACDC 四种天气合成一个增量域，不能把其 ACDC 分数写成雾天分数。**

## 1. 哪些文献真正匹配当前问题

| 文献／角色 | 训练序列与监督 | 是否单列 ACDC-fog | 与当前实验的关系 |
| --- | --- | --- | --- |
| LIT-010，Principles of Forgetting…，CVPR 2023；直接协议依据 | 有像素标签；分别开展 CS→Fog、CS→Night、CS→Rain、CS→Snow，四次独立两阶段实验 | 是 | 最接近本项目 CS→Fog；仍有骨干、预训练、裁剪与预算差异 |
| LIT-023，MILE，ICPR 2026；新近直接天气 DIL 方法 | 有标签；CS→Fog→Rain→Snow→Night，共五阶段 | 是 | 可参照多天气保持能力，表 1 不是第二阶段 Fog 学完时的成绩 |
| LIT-024，PSS，ICPRAM 2025；新近专家扩展方法 | 有标签；CS→ACDC，四种恶劣条件合成一个域 | 否 | 包含雾天数据，但主结果不能作为 Fog-only 成绩 |
| LIT-052，Effects of Architectures…，2023；架构／归一化参照 | 有标签；CS→ACDC | 表 II、III 仅给 ACDC 列 | 可分析架构与归一化，原表未单列 Fog，不纳入 Fog 排名 |
| LIT-007，SimCS，AAAI 2024；在线 DIL 代表方法 | 有标签；CS→IDD→BDD→ACDC，按在线计算预算训练 | 否 | 同时涉及地理／数据集变化，ACDC 汇总成绩不能替代 Fog-only 成绩 |

主干依据覆盖直接天气遗忘研究、天气专家方法和在线 DIL；补查 2025–2026 年同数据集工作时，大量命中属于目标无标签 CTTA／UDA，需按标签权限筛选。本表不是穷尽性系统综述。

来源：[CVPR 2023 原文](https://openaccess.thecvf.com/content/CVPR2023/papers/Kalb_Principles_of_Forgetting_in_Domain-Incremental_Semantic_Segmentation_in_Adverse_Weather_CVPR_2023_paper.pdf)、[MILE 原文 v2](https://arxiv.org/html/2605.03555v2)、[PSS 正式原文](https://www.scitepress.org/Papers/2025/132491/132491.pdf)、[架构论文原文](https://arxiv.org/html/2302.10718)、[SimCS 正式原文](https://ojs.aaai.org/index.php/AAAI/article/download/28952/29810)。

## 2. 直接两阶段 CS→ACDC-fog：最接近当前实验

以下 mIoU 为百分数，遗忘 F 为百分点（pp），越小越好。F＝源阶段 CS mIoU−增量结束后 CS mIoU。除本项目两行外，均为**同一篇 CVPR 2023 论文中的不同训练配置**，不是六篇独立方法论文。

| 来源／配置 | 源阶段 CS | 增量后 CS ↑ | 增量后 Fog ↑ | CS 遗忘 F ↓ | 原始位置 |
| --- | ---: | ---: | ---: | ---: | --- |
| CVPR 2023：FT，随机初始化源模型 | 72.0 | 44.0 | 69.0 | 28.0 | 表 2、3 |
| 同文：ImageNet 预训练＋FT | 73.9 | 50.1* | 68.8 | 23.8 | 表 3 |
| 同文：DINO 预训练＋FT | 75.0 | 55.4* | 72.4 | 19.6 | 表 3 |
| 同文：AutoAlb 增强＋FT | 72.2 | 57.5* | 68.2 | 14.7 | 表 3 |
| 同文：Barlow Twins 预训练＋FT | 73.9 | 59.5* | 71.4 | 14.4 | 表 3 |
| 同文：Continual Normalization（CN）＋FT | 71.2 | 52.1* | 67.1 | 19.1 | 表 4 |
| 本项目：FT，seed 0 | 71.51 | 54.29 | 62.31 | 17.22 | 交接包及本机离线复核 |
| **本项目：GSMF，seed 0** | **71.51** | **55.21** | **63.03** | **16.30** | 同上 |

\* 由原表已四舍五入的“源阶段 CS−遗忘”推算，精度仅保留 0.1；不是论文单独报告的原始评价值。FT 的 44.0 可直接在原表 2 核对。

模型与预算：该文主体采用 DeepLabV3+／ResNet-50，SGD，batch 8，裁剪 512×1024，CS 200 epochs、每个 ACDC 子域 150 epochs；本项目为 GS-AUFPN／ResNet-101，裁剪 512×512，源阶段 60000 steps、Fog 阶段 4000 steps。**同数据集、同序列只支持设定层面的参照，不能据绝对值认定跨论文方法优劣。** 原文第 4 节、表 2–4，PDF 第 3、5–7 页可核对。[原文在线版](https://arxiv.org/html/2303.14115)

该文表 6 还给出逐项叠加的组合结果，须保留原指标名称：

| 累积配置（CS→Fog） | Learning accuracy A ↑ | CS 遗忘 F ↓ |
| --- | ---: | ---: |
| FT | 70.5 | 28.0 |
| FT＋DINO | 73.7 | 19.6 |
| FT＋DINO＋AutoAlb | 73.9 | 11.7 |
| FT＋DINO＋AutoAlb＋CN | **75.4** | **7.3** |

这里 A＝（源阶段 CS mIoU＋增量后 Fog mIoU）/2；本项目原结果中的“最终两域均值”＝（增量后 CS mIoU＋增量后 Fog mIoU）/2，二者不同。组合配置的最终 CS、Fog 单项在表 6 未分别列出，因此不补写单项数字。表 7 的 EWC／Replay 只报告 Night、Rain，不能将其分数挪到 Fog。

## 3. MILE：包含 Fog，但在五阶段全部结束后评价

序列为 **CS(day)→Fog→Rain→Snow→Night**，所有方法使用 SegFormer-B5；下表各列为全部五阶段结束后的 mIoU。位置：原文表 1，PDF 第 8 页。

| MILE 文中的方法 | CS ↑ | Fog ↑ | Rain ↑ | Snow ↑ | Night ↑ | 五域均值 ↑ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ST／PSS† 参考 | 71.79 | 60.05 | 57.83 | 60.03 | 47.85 | 59.51 |
| FT | 63.26 | 65.43 | 58.22 | 56.41 | 50.93 | 58.85 |
| EWC | 65.48 | 68.13 | 57.87 | 55.99 | 48.42 | 59.18 |
| ILT | 66.33 | 65.89 | 58.04 | 55.73 | 39.19 | 57.04 |
| MILE†，已知测试域身份 | 71.21 | 70.55 | 64.17 | 66.20 | 49.95 | 64.42 |
| **MILE，自学习门控选择专家** | **71.21** | **70.30** | **64.06** | **65.16** | **49.95** | **64.14** |
| Joint Training，离线联合参考 | 72.29 | 75.65 | 67.05 | 67.07 | 52.19 | 66.85 |

† Oracle：测试时提供真实域身份。ST／PSS† 是该文用独立单任务专家加 oracle 表示的参考，不能当成 PSS 原论文已验证的五天气自动路由结果。

MILE 保存冻结主干及逐域 LoRA 专家，rank 16，每域 LoRA 约占主模型参数的 5%，并使用额外门控特征网络；与 GSMF 的增量分支及参数成本不同。其表 1 的 ΔP 是相对独立单任务模型的百分比变化，不是随时间测得的旧域遗忘，不能把 −0.81% 写成“遗忘 0.81pp”。[表 1 及第 4.2–4.3 节](https://arxiv.org/html/2605.03555v2)

发表口径：Springer 显示 ICPR 2026、首次在线 2026-08-06，但章节规范引用年为 2027；本文简称“MILE（2026）”，数值按作者 arXiv v2 核对。[正式出版元数据](https://link.springer.com/chapter/10.1007/978-3-032-31438-3_26)

## 4. 同时使用 CS 与 ACDC，但没有单独 Fog 成绩的相关工作

| 论文／设置 | 方法 | 最终 CS mIoU ↑ | 最终 ACDC 列 mIoU ↑ | 可核对的其他指标／限制 |
| --- | --- | ---: | ---: | --- |
| PSS，CS→全 ACDC | FT | 41.60 | 61.80 | 最终两域均值 51.70；CS 遗忘 19.93pp |
| 同上 | ILT | 37.62 | 36.24 | 最终两域均值 36.93 |
| 同上 | Replay（生成图像与伪标签） | 29.94 | 59.65 | 最终两域均值 44.79；不能理解为真实样本 ER |
| 同上 | **PSS** | **61.53** | **59.53** | 最终两域均值 60.53；CS 遗忘 0pp |
| 同上 | Joint Training，离线参考 | 61.98 | 61.36 | 最终两域均值 61.67 |
| Effects of Architectures…，CS→ACDC | UPerNet／ResNet-50（BN） | 60.7 | 72.4 | 遗忘 17.9pp；表 II、III |
| 同上 | UPerNet／ResNet-50（CN） | 64.8 | 72.1 | 遗忘 14.2pp；表 III |
| 同上 | UPerNet／ConvNeXt-T | 71.9 | 71.9 | 遗忘 9.0pp；表 II |
| SimCS，CS→IDD→BDD→ACDC | NT 基线 | 40.1 | 48.9 | 四数据集均值 40.5；主表 1，每批 N=4 次更新 |
| 同上 | ER＋VIPER（SimCS） | 48.5 | 52.0 | 四数据集均值 48.3；ER 缓存 800，另有合成数据 |

PSS 表 1 将 ACDC 四种天气合并；采用完整域专家与自编码器路由，原文 CS／ACDC 路由准确率为 100%，故保留了源专家成绩。其 0pp 遗忘依赖参数隔离和专家存储，不能等价于一个持续改写的共享模型完全不遗忘。**PSS 表 2 的 Fog=79.42 属于合成 SHIFT，不是 ACDC-fog。**[正式原文表 1、2及第 4.4 节](https://www.scitepress.org/Papers/2025/132491/132491.pdf)

架构论文原表只将目标列标为 ACDC，未单独列 Fog，故不将其 71.9／72.4 标为 Fog-only；本次不进一步推定未写明的逐天气聚合过程。[表 II、III](https://arxiv.org/html/2302.10718)

SimCS 的 ACDC 列同样是数据集级成绩，且先经历 IDD、BDD；四域均值不可与本项目两域均值比较。[主表 1](https://ojs.aaai.org/index.php/AAAI/article/download/28952/29810)

## 5. 对当前 GSMF 道路实验能得出的判断

- **有直接的天气 DIL 文献依据。** 当前两阶段并非没有前例；CVPR 2023 可作为设定、遗忘指标及浅层／归一化诊断的重要依据。
- **当前结果只能在自己的 FT 对照内评价方法收益。** GSMF 相比同源、同预算 FT：CS＋0.92pp、Fog＋0.72pp，最终两域均值＋0.82pp，但仍有 16.30pp 旧域遗忘。仅 seed 0，不能声称统计显著。
- **跨论文分数说明存在改进空间，不构成统一排行榜。** 目标阶段训练长度、输入面积、初始化、骨干、专家数量、测试域身份及评价时点均影响结果。较低遗忘还需结合新域分数判断，不能单看 F。
- **下一步建议，不是已采纳决策：** 先在现有两阶段协议、同一源检查点和预算下补充一种保持对照（如 LwF）及 BN 统计控制／浅层冻结诊断；如改用 CN 或不同源预训练，需重新训练相应源模型，不能继续声称源初始化完全相同。再决定是否复现 MILE 或扩展五天气序列，并同时记录参数／缓存成本。

本项目数据来源：[归档结果](../../03_experiments/road_clear_to_fog/formal-seed0-20261108-resume01/RESULTS_SUMMARY.md)、[本机离线核验](../../03_experiments/road_clear_to_fog/REVIEW_formal-seed0-20261108-resume01.md)。本机未重跑网络，未接收原始图像与权重。

## 6. 排除与证据边界

CoTTA、BECoTTA、Hybrid-TTA、GOLD 等相邻方法采用目标无标签测试时适应，不与上述完整像素标注监督 DIL 直接排名。另核查 WACV 2024 的 Towards Domain-Aware Knowledge Distillation for Continual Model Generalization：虽也使用“domain incremental”表述，其第 3.1 节明确接收无标签目标图像，属于 CTTA 权限；本文不将其归入监督两阶段主表。[原文](https://openaccess.thecvf.com/content/WACV2024/papers/Reddy_Towards_Domain-Aware_Knowledge_Distillation_for_Continual_Model_Generalization_WACV_2024_paper.pdf)

本次按“Cityscapes＋ACDC＋Fog＋domain-incremental／continual segmentation”补查近年文献，优先原论文及正式出版入口；未以二手摘要中的高 Fog 分数替代协议核查。尚不能声称“除这些之外不存在其他论文”。所有论文分数均为作者报告，未在本项目统一环境复现。

本地核查依据：LIT-010 表 2–4、6，LIT-023 表 1，LIT-024 表 1–2，LIT-052 表 II–III，LIT-007 主表 1；原文路径由[文献索引](../LITERATURE_INDEX.md)维护。定点核查不改变 LIT-052 的未读状态，也不登记用户本人已读。
