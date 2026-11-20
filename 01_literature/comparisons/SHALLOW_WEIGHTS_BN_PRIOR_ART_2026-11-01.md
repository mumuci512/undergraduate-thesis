# 浅层权重与 BN 统计分离更新：研究先例核查

日期：2026-11-01（Asia/Shanghai）。任务：检索是否已有论文实验过分别控制网络权重与 BN 统计，评估其与 GSMF 候选优化方向的关系。

## 结论与核验范围

**存在直接先例。** 冻结模型参数而重估 BN 统计、分离网络参数与 EMA 统计更新、以及分离 BN 仿射参数与统计的更新，都已有公开论文和对应实验。“分离更新”本身不能表述为本课题首次提出的算法。

本次完成原文相关方法与实验的定点核验，保存9份公开PDF及来源哈希，另核对1篇2026年期刊论文的出版信息与摘要。未完成新增论文的规范逐篇阅读报告，不登记为正式已泛读/已精读或用户本人已读；未复现代码。新增条目为LIT-044—053，见[文献索引](../LITERATURE_INDEX.md)。

“GSMF同一骨干、同一蒸馏、只针对stem/layer1、在有标注道路天气DIL下进行完整四组合对照”是否已有完全一致实现，本轮未确认；这个有边界的未确认不能用于宣称研究空白。

## 一、先把三个对象区分开

| 对象 | 例子 | 与本次问题的关系 |
| --- | --- | --- |
| 网络可学习权重 W | 卷积核、分割头 | 可以冻结或通过梯度更新；有些论文更新全网，有些只更新BN仿射参数 |
| BN仿射参数 A | γ、β | 也是可学习参数，但不等同卷积权重；“BN参数更新”必须注明是否仅指它们 |
| BN统计 S | 当前批次均值/方差、供推理使用的运行均值/方差 | 批次统计、EMA缓冲、源/目标混合统计不是同一对象；不能把所有TTA方法都称作“更新running_mean” |

此外，BN.eval()会同时停止运行统计更新并改用保存统计归一化；仅停止EMA更新但继续用当前批次归一化，是另一种条件。比较时应记录前向使用什么统计，不能只记录requires_grad。

## 二、领域主干及直接先例

| 文献 | 已核对的原文实验/方法 | 与“分离更新”的对应 | 协议边界 |
| --- | --- | --- | --- |
| LIT-045 AdaBN，2016预印本／ICLR 2017 Workshop | §3.2算法1用目标域响应重新估计各BN层统计；§4在Office-31、Caltech-Bing评价 | 固定已有模型参数，通过统计替换适应目标域，是早期直接先例 | 域适应；不验证监督天气DIL的阶段性旧域保持 |
| LIT-044 BN Tricks，2022预印本 | §5.1、算法1、表2：用均衡批次仅前向更新EMA；参数学习阶段保持EMA不变 | 明确把网络参数更新与BN统计更新分开；最直接的方法先例 | 有旧样本缓存的类增量分类；并非只处理浅层 |
| LIT-046 Continual Normalization，ICLR 2022 | §3、表1：固定相同模型参数，仅替换测试归一化统计的BN/BN*诊断；§4提出GN与BN组合 | 直接支持归一化统计可独立影响持续学习性能 | BN*诊断使用全部任务训练数据，不是可部署的无历史数据方案 |
| LIT-047 TBBN，CVPR 2023 | §4与表5分别消融任务均衡均值/方差，以及任务均衡γ/β训练 | 已有人分别控制统计计算与仿射参数学习，且单独调整未必有效 | 基于样本回放的离线CIL；不等于卷积浅层冻结实验 |
| LIT-050 AdaB²N，NeurIPS 2023 | 表1梳理BN/CN/BNT/TBBN；§3—4分析统计近期偏置、训练适应性及测试EMA | 说明此方向已有系统方法谱系，统计平衡与模型适应需一起考虑 | 类增量/任务增量分类，不直接证明道路DIL效果 |
| LIT-048 TTN，ICLR 2023 | §2—3与表1—5：后训练学习层/通道统计混合系数；测试固定模型参数，混合源统计与测试批统计 | 统计处理可独立于测试时权重优化；分层差异也已有研究 | TTA；统计混合不等同EMA更新，额外源域后训练须计入 |

这些工作可沿CN、BNT、TBBN到AdaB²N的引用链交叉定位。综述导航参考IJCV 2024《In Search of Lost Online Test-Time Adaptation: A Survey》，但方法结论以对应原论文为准，不依赖二手摘要。

## 三、最直接的实验定位

### 1. BN Tricks：网络权重与EMA统计明确分开

原文p.5 §5.1和算法1明确采用两套更新过程：均衡批次仅前向跟踪EMA，当前与缓存批次用于参数学习时保持EMA固定。p.6表2在Seq-CIFAR-10上报告相关消融；ResNet-18、缓存500，结果为10次运行均值及标准差。

| 表2配置 | ACC（%） |
| --- | ---: |
| ER | 61.62 ± 1.59 |
| ER-BNT-Imbalance-Tracker | 66.83 ± 2.00 |
| ER-BNT | 72.08 ± 0.55 |

该组说明分离更新已被实际实验；完整方案还改变了批次构造及参数学习流程，不能把相对ER的全部提升归给一个冻结开关。

### 2. OD-TTA：BN统计与仿射参数采用不同批大小

LIT-051为2025预印本；核对正文§3.5、§4.3.3、附录A.4和表6。该对照在CIFAR-10-C用128个适应样本，统计更新批大小16、仿射更新批大小1；其余网络参数保持不变。

| 表6配置 | 平均准确率（%） |
| --- | ---: |
| 只适应BN统计 | 77.6 |
| 同步适应统计与仿射参数 | 77.8 |
| 分离适应 | 79.5 |

数字为原文配置结果；批大小、更新次序及方法损失等须按原文对齐，不能把差值当作监督道路DIL的预期收益。该文尚未核实主会发表，不标注为ICML论文。

## 四、近年补充与最接近道路场景的证据

- **LIT-049 MemBN，ECCV 2024。** 维护统计记忆并按层混合源统计与目标统计；分类同时比较纯归一化与优化型TTA，表5另有DeepLabV3+道路分割。p.12表5的Cityscapes→BDD100K、batch=1条件，TENT为40.78、TENT+MemBN为50.94 mIoU；这是无标签TTA的表内比较，不能当作GSMF监督DIL收益。
- **LIT-053 STEMS，2026。** 出版商确认《Diagnosing BN discrepancy in rehearsal-based class incremental learning》于2026-02-28发表于International Journal of Machine Learning and Cybernetics，17:153；摘要说明研究训练/推理BN差异并调节统计更新。正文为订阅内容，本次只核对书目与摘要。它与2022 BNT有作者和主题交集，但方法名、作者列表不同；不把两版算法或数值混为一谈。
- **LIT-052 Effects of Architectures on Continual Semantic Segmentation，2023预印本。** §IV与表III比较ResNet-50搭配BN、CN、GN、IN、LN、BRN在Cityscapes→ACDC中的表现；它支持归一化选择与DIL适应—保持相关，属于邻近机制证据，并非浅层权重/统计独立冻结实验。正式发表状态本次未核实。
- **已有LIT-010，CVPR 2023。** 表5在网络权重不变时，用旧域和新域图像重估BN统计，恢复部分旧域分数；这是本课题最直接的道路天气机制诊断。它已在已有报告中记录，不是本次发现的新方法。

补充线索：ICLR 2026 TTU Workshop稿《Efficient Test-Time Adaptation via Decoupled BN Update For Edge Devices》同样提出统计与仿射参数分离更新；检索可见PDF页眉和摘要，但录用状态未独立确认。作者与OD-TTA相同，内容可能重合，不作为第二份独立效果证据，也不标为ICLR主会。

## 五、对GSMF优化方向的影响

### 可以确定的结论

1. “卷积权重固定，只改BN统计”已有AdaBN等先例。
2. “参数学习与EMA统计分别更新”已有BNT直接先例。
3. “统计与BN仿射参数分离更新”已有OD-TTA实验；“按层混合旧/新统计”已有TTN、MemBN等方法。
4. 因此，方案A应以**已有机制指导下的诊断与基线增强**定位；新增一个BN冻结开关或常规四组合消融，不能直接表述为新算法。是否形成进一步研究贡献，仍需具体新设计及对照证据。

### 尚不能确定的结论

- 本轮没有确认与GSMF特定浅层冻结、双蒸馏、监督道路天气多阶段协议完全一致的既有实验，但也没有完成穷尽式新颖性检索。
- 不能据此声称“浅层冻结与BN统计解耦从未在道路DIL中研究”。
- 不能从分类/TTA结果推断改造GSMF后一定更好；数据访问、监督、测试时更新、旧域评价时点不同。

### 近期可用的实验安排（建议，未采纳）

先核验教师真正固定，再用相同初始化与双蒸馏比较学生浅层参数/统计四组合；同时设置与允许数据条件匹配的归一化或统计适应对照。区分卷积权重、BN γ/β、EMA及前向归一化来源，记录旧域保持、新域适应和成本。若进一步设计自适应混合、记忆或分层策略，必须与TTN、MemBN、AdaB²N等具体机制核对重合点。

## 六、检索记录与保存

检索日期2026-11-01。检索范围包括arXiv、CVF、OpenReview、NeurIPS正式论文集、ECVA、作者项目页和Springer出版页；正文结论优先来自原始PDF。沿CN/BNT/TBBN/AdaB²N与TTA综述引用链补检，并对2025—2026年的decoupled BN、frozen weights、statistics等关键词作定向查询。

代表检索式：

- `batch normalization continual learning freeze weights update running statistics ablation segmentation`
- `"Diagnosing Batch Normalization in Class Incremental Learning"`
- `"decoupled BN adaptation"`
- `batch normalization "statistics" "frozen" "continual" "2025"`
- `batch normalization "decouple" "2026" continual learning`

部分CVF/OpenReview直接访问受限时，用arXiv公开原文或正式作者版本核查。OD-TTA作者链接本地下载返回404，已从arXiv v1补取；失败尝试和成功来源均记录于[来源清单](../papers_bn_update/SOURCE_MANIFEST_2026-11-01.json)。未进行付费内容绕过、代码安装或训练。

## 原始来源

- LIT-044：[BNT arXiv v1](https://arxiv.org/abs/2202.08025)，§5、算法1—2、表2；本地[LIT-044](../papers_bn_update/LIT-044_Zhou_2022_BN_Tricks.pdf)。
- LIT-045：[AdaBN](https://arxiv.org/abs/1603.04779)，§3.2、算法1、§4；[ICLR 2017官方Workshop列表](https://iclr.cc/archive/www/doku.php?id=iclr2017:workshop_posters.html)。
- LIT-046：[CN](https://arxiv.org/abs/2203.16102)，§3—4、表1；[作者代码](https://github.com/phquang/Continual-Normalization)。
- LIT-047：[TBBN arXiv全文](https://arxiv.org/abs/2201.12559)，§4、表5；[CVPR正式条目](https://openaccess.thecvf.com/content/CVPR2023/html/Cha_Rebalancing_Batch_Normalization_for_Exemplar-Based_Class-Incremental_Learning_CVPR_2023_paper.html)。
- LIT-048：[TTN](https://arxiv.org/abs/2302.05155)，§2—3、表1—5；[作者项目页](https://sites.google.com/view/ttn-test-time-normalization/home)。
- LIT-049：[MemBN ECVA全文](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/04143.pdf)，§4—5、表3—6；[作者项目页](https://cvlab.postech.ac.kr/research/MemBN/)。
- LIT-050：[AdaB²N NeurIPS全文](https://papers.neurips.cc/paper_files/paper/2023/file/50ca96a1a9ebe0b5e5688a504feb6107-Paper-Conference.pdf)，表1、§3—4。
- LIT-051：[OD-TTA arXiv v1](https://arxiv.org/abs/2505.00986)，正文§3.5/4.3.3、附录A.4、表6；本地[LIT-051](../papers_bn_update/LIT-051_Ma_2025_OD_TTA.pdf)。
- LIT-052：[Effects of Architectures](https://arxiv.org/abs/2302.10718)，§IV、表III。
- LIT-053：[STEMS正式出版页](https://link.springer.com/article/10.1007/s13042-026-02993-x)，书目与摘要；DOI 10.1007/s13042-026-02993-x，未获得正文。
- 综述导航：[In Search of Lost Online Test-Time Adaptation: A Survey](https://link.springer.com/article/10.1007/s11263-024-02213-5)，仅用于方法链索引；未作为逐方法实验结论的唯一依据。
