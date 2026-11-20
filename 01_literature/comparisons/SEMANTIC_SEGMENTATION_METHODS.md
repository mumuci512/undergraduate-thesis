# 语义分割方法分类与已读文献对照

日期：2026-10-27（Asia/Shanghai）。

用途：解释二维图像语义分割的主要技术路线，以及它们与本项目域增量持续学习方法的关系。本文为概念性综合，结合现有文献索引、比较报告和原始论文作定向核对，不是系统性文献综述或完整模型排行榜。新增例子用于说明技术类别，不表示纳入正式候选、完成逐篇精读或运行复现。

## 1. 先分清任务、网络和学习方法

**语义分割是任务；CNN、Transformer、图神经网络是构建模型的技术；回放、蒸馏和参数隔离是学习策略。** 三者不是同一层级。

语义分割给图像每个有效像素赋予语义类别，如道路、行人、汽车、天空。同类的不同个体不必分开；实例分割则需要区分不同个体；全景分割进一步统一可数物体的实例与背景区域。Mask2Former 这样的通用架构可用于不同分割任务，不能仅凭网络名称认定实验任务。[S4]

常见分割模型可以从功能上理解为：

```mermaid
flowchart LR
    A[输入图像] --> B[编码器或骨干：提取特征]
    B --> C[上下文建模与多尺度融合]
    C --> D[解码器或预测头]
    D --> E[逐像素语义类别]
```

这是功能分解，不要求每个网络都严格包含四个独立模块。跳跃连接、并行分支和查询解码等会改变连接方式。

| 观察维度 | 回答的问题 | 常见分类 |
| --- | --- | --- |
| 特征计算机制 | 特征怎样交互？ | CNN、Transformer、GNN、状态空间模型，以及它们的组合 |
| 网络组织方式 | 特征怎样提取与恢复？ | 编码器—解码器、特征金字塔、多分辨率并行、双分支等 |
| 预测方式 | 怎样得到最终类别图？ | 逐像素分类、掩码分类／集合预测等 |
| 监督和词汇范围 | 标签来自哪里，能预测哪些类？ | 全监督、半监督、弱监督；固定类别、开放词汇等 |
| 学习环境 | 数据怎样到达，分布怎样变化？ | 离线学习、持续学习；域增量、类增量；域自适应、域泛化等 |
| 工程目标 | 在什么资源下运行？ | 高精度、实时、轻量、端侧部署等 |

这些维度可以组合。例如，“Transformer 编码器＋逐像素分类＋全监督＋固定类别＋域增量学习”是一种完整描述。

## 2. 按特征计算机制分类

### 2.1 传统特征与图模型：理解历史边界

深度网络之前，可以提取颜色、纹理等人工特征，使用分类器预测像素／区域类别，再用马尔可夫随机场、条件随机场（MRF／CRF）表达标签间关系。DenseCRF 是相关结构化预测方法的代表，也可以作为深度网络输出的细化环节。[S11]

阈值、聚类、区域生长、分水岭和图割等能划分图像，但划出不同区域不自动等于识别“道路、汽车、天空”。完成语义分割仍需要把区域与语义标签联系起来。**使用图结构或图割不等于使用图神经网络。**

### 2.2 CNN：通过卷积提取和组合局部特征

普通卷积在规则像素网格的局部邻域上计算，共享卷积核参数；逐层组合后得到更大范围的语义信息。常见设计同时处理三个问题：扩大上下文范围、保留细节、融合不同尺度。

| CNN 内部的设计重点 | 代表例子与年份 | 解释 |
| --- | --- | --- |
| 全卷积密集预测 | FCN，2015 | 将分类网络改造成输出空间预测图的网络，并恢复输出分辨率，是现代深度语义分割的重要基础。[S1] |
| 编码器—解码器与跳跃连接 | U-Net，2015 | 编码器压缩并提取语义，解码器恢复空间分辨率；跳跃连接传递浅层细节。[S2] |
| 空洞卷积与多尺度上下文 | DeepLabv3+，2018 | 空洞卷积扩大感受野，ASPP 聚合不同尺度，解码器进一步改善边界。[S3] |
| 金字塔池化 | PSPNet，2017 | 在不同区域尺度上池化，补充局部区域与整体场景上下文。[S6] |
| 保持高分辨率并反复融合 | HRNet 相关像素标注架构，2019 | 高、低分辨率分支并行并交换信息，减少细节在连续下采样中丢失。[S7] |
| 面向实时推理的结构 | ENet，2016；BiSeNet，2018 | 压缩计算，或让空间细节与语义上下文走不同分支，再融合预测。[S8] |

这些是交叉的设计思路，不是严格互斥的家族。例如 DeepLabv3+ 同时也是编码器—解码器结构。

“CNN 只看局部”仅适合描述普通单层卷积的直接交互范围。多层卷积、空洞卷积、全局池化或附加注意力都能让 CNN 利用更大范围的信息。其实际精度、速度和天气鲁棒性取决于具体设计与训练，不能由“CNN”三个字直接判断。

### 2.3 Transformer：通过注意力建立特征之间的联系

Transformer 利用注意力，根据输入特征计算不同位置或查询之间的交互权重。相对于普通卷积的固定局部连接，它可以更直接地建模较远位置之间的关系。不过，实际视觉 Transformer 可能使用窗口、降采样或其他高效结构，不能假定每层都计算全图所有像素对。

在本项目中，应重点区分两种使用位置。

**SegFormer：Transformer 主要用于编码器。** 其 MiT 分层编码器提取多尺度特征，轻量 MLP 解码头进行融合并得到像素类别预测。MLP 解码头不意味着整个模型属于“纯 MLP 模型”；编码器中也保留卷积操作。[S5]

**Mask2Former：Transformer 解码器用于查询和掩码预测。** 模型提取图像特征及像素嵌入，再用查询预测一组掩码和对应类别，汇总为需要的分割输出。它可以搭配 ResNet 等 CNN 骨干，也可以搭配 Swin Transformer 骨干；因此“使用 Transformer”不等于“骨干一定是 Transformer”。[S4]

| 比较项 | SegFormer | Mask2Former |
| --- | --- | --- |
| 主要标志 | 分层 Transformer 编码器＋轻量解码头 | 掩码注意力 Transformer 解码器＋掩码分类 |
| 典型中间表示 | 多尺度空间特征 | 像素嵌入和一组查询 |
| 典型预测形式 | 各位置的类别分数 | 各查询的掩码与类别，再形成最终输出 |
| 用于什么任务 | 主要面向语义分割 | 架构可用于语义、实例和全景分割 |

Transformer 不保证比 CNN 更准确或更适合持续学习；两类网络也都存在轻量与大型版本。预训练、输入分辨率、参数量、训练预算与实现方式需要一起比较。

### 2.4 GNN／图推理：按关系组织节点并传递信息

图神经网络把特征表示成节点与边，通过邻居聚合、图卷积或图注意力更新节点。节点可以对应像素、超像素、区域或学习到的潜在特征；边可以表达空间邻近或学习到的联系。它不要求信息只能沿规则网格的相邻像素传播。

用于图像分割时，一种常见组合是：先用 CNN 提取规则特征图，再投影到图空间作关系推理，最后投影回空间特征图。图推理的收益和代价取决于节点构造、连接方式和投影过程；不能仅凭引入 GNN 就判断优于注意力或卷积。

**LIT-026 的精确归类是“CNN 骨干＋图空间推理＋注意力融合”，其分割模型名为 GS-AUFPN；GSMF-RS-DIL 还包含域增量训练机制。**

对照原文第 4 页、Fig. 3、§III-A/B：

1. ResNet-101 编码器提取四阶段特征。
2. 深层特征进入 GSR 模块：学习投影到图空间，进行图卷积，再投影回原空间。
3. 以特征金字塔组织多尺度特征，DCAU 模块作注意力融合与上采样。
4. 分割头输出逐像素类别。

这里的图节点由特征学习聚合得到，并不表示预先给每个“道路／建筑”类别设一个节点；模型也不是从原始图像开始全部由 GNN 构成。CNN 与 GNN 的作用是组合关系。[S9]

原文：[LIT-026 期刊版](../../第二批文献/LIT-026_Huang_2024_GSMF_RS_DIL_TGRS.pdf)；既有报告：[LIT-026 阅读报告](../paper_reports/LIT-026_gsmf_rs_dil_graph_multifeature.docx)。

### 2.5 其他计算机制与混合设计

CNN、Transformer 和 GNN 并未穷尽全部路线。例如，状态空间模型（SSM）通过状态传播处理长范围信息；SegMAN（CVPR 2025）组合状态空间模型与局部注意力，体现了不同机制共同建模的路线。[S10]

还存在引入循环计算、MLP 特征混合或生成式建模的分割研究。概念学习时应先掌握主干，不宜把每个新增模块都列为同等成熟、相互排斥的大类。

“混合架构”是组合方式：CNN＋Transformer、CNN＋图推理、SSM＋注意力等均可成立；它不是一种独立于这些机制的新基本算子。

## 3. 按输出方式分类：像素分类与掩码分类

**逐像素分类**直接构建空间位置与类别的分数。例如，对有 K 个类别的任务，为每个位置得到 K 个分数，再恢复至需要的输出分辨率并选择类别。FCN、U-Net、DeepLabv3+、SegFormer 属于典型例子。这不表示像素之间没有联系：预测前的特征提取已融合上下文。

**掩码分类／集合预测**先预测若干“区域掩码＋类别”，再得到语义或实例输出。MaskFormer／Mask2Former 是代表。查询数量不必等于类别数量，查询不必永久绑定固定类别；同一类别也可能由多个查询预测。[S4]

这与 CNN／Transformer 是两个维度。例如，Mask2Former 可以用 CNN 骨干提取特征，同时用 Transformer 解码器作掩码分类。换成掩码预测也不自动把语义分割实验变成实例分割实验。

## 4. 基础模型、开放词汇、轻量化应放在哪里

**基础模型**描述预训练规模、通用能力及迁移方式，不是与 CNN、Transformer 平行的基本计算机制。

SAM（2023）原始设计重点是提示式掩码生成。得到对象区域，并不自动得到本课题要求的固定道路类别标签；接入固定类别语义分割时需要相应的类别识别、任务头或适配方案。[S12]

**开放词汇语义分割**根据文本类别描述预测区域，可以涉及训练分割标注未覆盖的类别。例如 OVSeg（CVPR 2023）利用适配后的 CLIP 作开放词汇分割。[S13] 开放词汇与固定类别是任务及词汇范围的差别，不是 CNN／Transformer 之别。

**实时、轻量、边界感知、多模态**分别描述资源目标、优化重点或输入信息，也都可以与多种架构组合。“更新参数少”还不能代替完整模型的显存、计算量和推理速度测量。

## 5. 与已读文献的对应

以下对应来自已有索引和比较报告；LIT-026 的架构另对照本地原文第 4 页及 Fig. 3 核实。

| 已读文献 | 分割网络层面 | 学习方法／研究问题层面 |
| --- | --- | --- |
| LIT-007，SimCS | DeepLabv3 | 用模拟数据辅助域增量持续分割 |
| LIT-010，天气域遗忘分析 | DeepLabv3+／ResNet-50、SegFormer-B2、ERFNet 等架构对照 | 分析天气变化的遗忘及相应缓解措施 |
| LIT-012，SimCIS | Mask2Former | 类增量分割中的查询与学习机制 |
| LIT-023，MILE | SegFormer-B5 | 增量 LoRA 专家及路由，研究跨域／模态持续学习 |
| LIT-026，GSMF-RS-DIL | GS-AUFPN：ResNet-101＋GSR＋DCAU | 冻结部分特征层、特征约束与输出蒸馏等域增量机制 |
| LIT-033，FOCUS | U-Net 系列 | 稀疏特征回放、跳跃连接利用及持续学习 |

项目内部依据：[LIT-007–016 比较](LIT-007-016_BASELINE_COMPARISON.md)、[近期 DIL 比较](RECENT_DIL_SEGMENTATION_REPRODUCTION_SCREEN_2026-10-26.md)、[文献索引](../LITERATURE_INDEX.md)。

## 6. 本课题怎样使用这套分类

本课题是“视觉条件变化下道路场景语义分割的持续学习方法研究”，当前研究主线为 DIL。选分割网络与选持续学习机制是关联但不同的研究选择：

- 网络提供表征和预测能力：如 DeepLabv3+、SegFormer、Mask2Former。
- 持续学习机制控制怎样更新、保存和使用历史知识：如回放、蒸馏、参数约束、冻结、适配器、专家和路由。
- 数据协议定义要解决什么问题：类别是否固定、目标数据有没有标签、训练边界是否可见、测试是否知道域 ID。

阅读或记录一篇方法时，可使用以下一句话模板：

> 本文在【数据／增量设定】下，以【骨干＋上下文模块＋解码器／预测头】完成【像素／掩码预测】，通过【学习策略】处理【遗忘／适应等问题】。

比较新机制是否有效，应在统一骨干、初始化／预训练、数据、监督、分辨率和预算后对照，区分架构本身的收益与持续学习机制的收益。涉及掩码查询的方法还需检查机制是否依赖这种输出结构，不能默认可以直接替换到任何分割网络。

本次分类不确定或更换主基线，不构成研究里程碑，因此无需更新全局研究状态或长期决策。

## 7. 依据与核对范围

检索与核对方式：先以既有项目资料恢复相关方法及编号，核查基础原始方法与综述入口，再定向核对用户点名模型及一个新近机制示例；优先使用原论文、官方会议论文库和作者工程。涉及模型性能优劣的泛化判断均未由单篇结果推出。没有开展新实验，也没有为这些背景论文新增 LIT 编号。

| 标记 | 论文／来源与年份 | 本文使用范围与依据 |
| --- | --- | --- |
| S1 | Long、Shelhamer、Darrell. Fully Convolutional Networks for Semantic Segmentation. CVPR 2015. [原文](https://www.cv-foundation.org/openaccess/content_cvpr_2015/papers/Long_Fully_Convolutional_Networks_2015_CVPR_paper.pdf) | 全卷积密集预测；作者论文原始材料／作者工程入口核对 |
| S2 | Ronneberger、Fischer、Brox. U-Net: Convolutional Networks for Biomedical Image Segmentation. 2015. [作者稿](https://arxiv.org/abs/1505.04597) | 收缩／扩张路径及定位目标；原论文入口核对 |
| S3 | Chen 等. Encoder-Decoder with Atrous Separable Convolution for Semantic Image Segmentation. ECCV 2018. [作者稿](https://arxiv.org/abs/1802.02611) | DeepLabv3+ 的空洞卷积、多尺度与解码器设计；原论文摘要核对 |
| S4 | Cheng 等. Masked-attention Mask Transformer for Universal Image Segmentation. CVPR 2022. [原文](https://arxiv.org/html/2112.01527v3) | §3.1–3.2 的组件与预测形式，§4 的 ResNet／Swin 骨干；原文相关部分核对 |
| S5 | Xie 等. SegFormer: Simple and Efficient Design for Semantic Segmentation with Transformers. NeurIPS 2021. [原文](https://arxiv.org/html/2105.15203v3) | §3.1–3.2 的 MiT 编码器与 MLP 解码头、卷积组件；原文相关部分核对 |
| S6 | Zhao 等. Pyramid Scene Parsing Network. CVPR 2017. [官方入口](https://openaccess.thecvf.com/content_cvpr_2017/html/Zhao_Pyramid_Scene_Parsing_CVPR_2017_paper.html) | 金字塔池化设计；官方原论文条目核对 |
| S7 | Sun 等. High-Resolution Representations for Labeling Pixels and Regions. 2019. [作者稿](https://arxiv.org/abs/1904.04514) | 保持高分辨率表征的路线；原论文条目与摘要核对 |
| S8 | Paszke 等. ENet. 2016. [作者稿](https://arxiv.org/abs/1606.02147)；Yu 等. BiSeNet. 2018. [作者稿](https://arxiv.org/abs/1808.00897) | 实时目标及双分支例子；原论文条目与摘要核对；不直接引用其历史 FPS 比较 |
| S9 | Huang、Ding、Deng. Domain-Incremental Learning for Remote Sensing Semantic Segmentation With Multifeature Constraints in Graph Space. IEEE TGRS 62, 2024. DOI: 10.1109/TGRS.2024.3481875. [作者官方工程](https://github.com/HuangWBill/GSMF-RS-DIL) | 本地期刊原文第 4 页／Fig. 3／§III-A/B 核对，辅以作者工程说明；未运行代码 |
| S10 | Fu、Lou、Yu. SegMAN: Omni-scale Context Modeling with State Space Models and Local Attention for Semantic Segmentation. CVPR 2025. [作者稿](https://arxiv.org/abs/2412.11890) | SSM 与局部注意力组合；原论文入口、摘要及官方会议条目核对，不据此声称该机制普遍最优 |
| S11 | Krähenbühl、Koltun. Efficient Inference in Fully Connected CRFs with Gaussian Edge Potentials. NeurIPS 2011. [官方原文](https://proceedings.neurips.cc/paper/4296-efficient-inference-in-fully-connected-crfs-with-gaussian-edge-potentials.pdf) | 图模型与像素标签关系；官方原文条目及作者稿摘要核对；arXiv 上传年 2012 不替代会议年 |
| S12 | Kirillov 等. Segment Anything. 2023. [作者稿](https://arxiv.org/abs/2304.02643) | 提示式掩码生成的任务边界；原论文入口与摘要核对 |
| S13 | Liang 等. Open-Vocabulary Semantic Segmentation With Mask-Adapted CLIP. CVPR 2023. [官方原文](https://openaccess.thecvf.com/content/CVPR2023/papers/Liang_Open-Vocabulary_Semantic_Segmentation_With_Mask-Adapted_CLIP_CVPR_2023_paper.pdf) | 开放词汇与文本类别描述的例子；官方原论文条目及摘要核对 |

概念框架的交叉检查入口：Thisanke 等（2023），[Semantic Segmentation using Vision Transformers: A survey](https://arxiv.org/abs/2305.03273)。本次只核对其研究范围及入口，不标记为本项目新增已读综述。
