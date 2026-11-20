# P0：SegFormer-B5 权重与 MILE 配方审计

日期：2026-11-16（Asia/Shanghai）。本报告为 AI 辅助定向核验；读取官方源配置、源权重对应训练日志首行和论文相关章节。所有下载原文及 SHA-256 见 [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json)。本文记录来源声明和可检查配置；实际权重 SHA、严格加载、Source 成绩及 20GB 测速由上级 P0 执行记录承担。

**本轮可用起点是 OpenMMLab 发布的 Cityscapes 19 类完整分割权重；它已学习 Cityscapes，不是仅有 ImageNet 预训练的随机分割头。P0 检查可用性并测速，不构成 MILE 复现。** MILE 所用 SATS 版本、源权重和完整训练配方仍无法由已核查公开材料恢复。

## 1. 权重来源、数据权限与加载规则

| 资产 | 已核实来源／用途 | 本轮处理与边界 |
|---|---|---|
| **B5 Cityscapes 完整模型，`87a052ec`** | [官方发布表](https://github.com/open-mmlab/mmsegmentation/blob/v1.2.1/configs/segformer/README.md)，[权重直链](https://download.openmmlab.com/mmsegmentation/v0.5/segformer/segformer_mit-b5_8x1_1024x1024_160k_cityscapes/segformer_mit-b5_8x1_1024x1024_160k_cityscapes_20211206_072934-87a052ec.pth)。对应 2021-12-06 训练日志，MMSeg 0.19.0+ | 用于 P0 固定 Source 与短训练共同起点。保留完整 backbone/head；迁移到 MMSeg 1.2.1 必须 `strict=True` 检查键与形状，不能随机重建头后仍称官方 Source。 |
| **MiT-B5 主干，`658746d9`** | [MMSeg v1.2.1 B5 配置](https://github.com/open-mmlab/mmsegmentation/blob/v1.2.1/configs/segformer/segformer_mit-b5_8xb1-160k_cityscapes-1024x1024.py) 指向 [主干权重](https://download.openmmlab.com/mmsegmentation/v0.5/pretrain/segformer/mit_b5_20220624-658746d9.pth)；NVlabs README 将用于训练的主干权重明确标为 ImageNet-1K | 这是从 ImageNet 主干重新训练道路源模型的选项；不能直接期待 19 类 Source 成绩。P0 不运行 160k 源训练。 |
| ADE20K B5 分割权重 | 官方发布表另列 150 类 ADE20K 模型，例如 `94cedf59`（512²）、`41d2845b`（640²） | 本轮不采用。若日后采用，需记录额外 ADE20K 像素监督和分类头重置；不能与 ImageNet-1K→Cityscapes 权限混同。 |

**预训练核验结论：** [SegFormer 原文 §4.1](https://arxiv.org/html/2105.15203#S4.SS1) 声明 encoder 用 ImageNet-1K、decoder 随机初始化；NVlabs README 的训练说明一致。`87a052ec` 的[对应完整训练配置](official_cityscapes_training_config_20211206.py)写的是 `pretrain/mit_b5.pth`，训练读取 Cityscapes `train`，验证／测试入口均读取 `val`，未在该配置中发现 ADE20K、Mapillary、coarse 或 train+val 混合。因原始主干文件历史 SHA 未在该日志内给出，“只有 ImageNet-1K→Cityscapes”是公开配方声明，不能当成逐样本训练历史的独立审计。此完整 Cityscapes 权重与 2022 年重新发布的主干文件也不能仅凭名称认定字节相同。

官方源模型训练期间使用公开 val 评价，因此本项目应称“Cityscapes 官方验证集基准评价”；不能称从未被上游开发者使用的独立盲测集。后续按2026-11-17用户确认的[D-012](../../../00_management/DECISIONS.md)，使用完整官方train训练、官方val选择超参数、官方test作最终评价；不再从train另扣验证集。隐藏test标签时须提交官网获取正式成绩，不以本地val替代。

## 2. 本权重的输入、网络与评价口径

以下从 v1.2.1 配置继承链和权重对应的历史日志配置交叉核对；快照采用扁平文件名保存供审计，原始继承路径不用于在当前扁平目录直接运行。

| 项目 | 官方可核查值 | P0 工程处理 |
|---|---|---|
| 主干／头 | MiT-B5，四阶段层数 `[3,6,40,3]`，输出通道 `[64,128,320,512]`；`SegformerHead.channels=256`，19 输出，无辅助头 | 保留结构、检查完整权重；参数数量以实际构建模型统计为准。 |
| 通道／归一化 | OpenCV 读 BGR，preprocessor `bgr_to_rgb=True`；RGB mean `[123.675,116.28,103.53]`，std `[58.395,57.12,57.375]`，像素按 0–255 输入 | 图像只做一次 BGR→RGB 和归一化。PIL 的 RGB 已转换数据不能再次按 BGR 处理。 |
| 训练输入 | 以 2048×1024 为基础随机缩放，比例 0.5–2.0；1024² 随机裁剪，cat_max_ratio 0.75；水平翻转 0.5、颜色扰动；padding 图像 0／标签 255 | 短训保留这一真实数据增强和裁剪规模，不用合成随机张量代替成本证据。 |
| 标签 | trainId 0–18，ignore 255，`reduce_zero_label=False` | 标签来源明确区分 labelIds／trainIds；只映射一次，禁止把类别 0 当背景删去。类别顺序见 [官方数据类](mmseg_cityscapes_dataset.py)。 |
| 默认 Source 推理 | 原图按 `(2048,1024)` 保比例 resize；1024² 滑窗、stride 768²；单尺度，无 flip | P0 Source 固定参数和全部 buffer、FP32、上述滑窗；各域同一模型，不用真实天气 ID 路由。 |
| 评价集 | 官方配置的 val 和 test_dataloader 均读 Cityscapes val；非隐藏 test 评测 | 报告使用实际完整样本清单；不以命令参数名 `test` 冒充官方 test。 |
| 指标 | 数据集级 mIoU | 全集累计 19×19 混淆矩阵，再算每类 IoU 和类均值；不平均逐图 mIoU；逐域报告后再等权平均。 |

**必须区分两套“B5”：** NVlabs 原版 [B5 Cityscapes 配置](NVlabs_b5_cityscapes.py) 的 decoder embedding 是 **768**；OpenMMLab 本权重的融合通道是 **256**。因此同叫 B5 也不保证头结构、参数数目和计算量相同。SegFormer 原文表 1(a) 中 Cityscapes B5 的 **82.4／84.0** 分别为单／多尺度；OpenMMLab 本权重发布值为 **82.25（SS）／83.48（MS+flip）**。本轮单尺度校准应优先核对 82.25，不能把 84.0 当同配置未达标证据。[原论文表1(a)](https://arxiv.org/html/2105.15203#S4.T1)、[OpenMMLab 模型表](https://github.com/open-mmlab/mmsegmentation/blob/v1.2.1/configs/segformer/README.md)

## 3. MILE 已报告、缺项与本轮采用值

核验范围：[MILE arXiv v2](https://arxiv.org/html/2605.03555v2) 的 §3.1–3.2、§4.1–4.3、§5，重点为 §4.2 和表 1；核对 SATS 官方 README、`argparser.py` 和 `run.py`。下表“未报告”只限这些已读材料，不断言作者没有内部配置。

| 配方项 | MILE 原文可确认 | 未恢复部分／P0 采用 |
|---|---|---|
| 底座 | SegFormer-B5 from SATS，所有方法采用该底座 | SATS commit、具体 head 配置及 checkpoint 未给出。P0 用上文 OpenMMLab 完整 Cityscapes 权重，属于本项目校准起点。 |
| 数据／类别 | CS 与 ACDC、固定 19 类；主序 CS→Fog→Rain→Snow→Night | ACDC具体版本、逐split数量、val/test和数据清单、正常参考图访问均未恢复；P0 复用已审计官方 train/val 清单并留路径／SHA。 |
| 预训练 | 分割底座预训练；路由另用 pretrained ConvNeXt-Tiny | 两者确切权重、ImageNet版本／其他监督数据未明确；不可假定与本项目相同。 |
| batch | 报告 12 | 是全局／每卡、GPU数量、梯度累积未明确。P0 是单卡 microbatch1、effective batch1 的资源短训，不冒充 batch12 复现。 |
| 学习率 | standard 初始／增量 0.01／0.001；LoRA 0.05／0.005 | 优化器、参数分组、动量、weight decay、scheduler未在上述原文中给出。P0 资源 probe 用官方 AdamW 分组，base lr6e-5 常数；不搬用 MILE 数值。 |
| 训练量／选择 | 未恢复完整步数、epoch、早停、seed、搜索预算 | P0 200步仅作资源与保存重载检查；P1预算另定。 |
| 输入／测试 | 未恢复裁剪、缩放增强、滑窗、多尺度和混淆矩阵细节 | P0采用上文权重对应官方输入与单尺度滑窗口径。 |
| 持续机制 | LoRA rank16，约5%；冻结base和旧专家；原型由各域训练数据计算，冻结ConvNeXt特征、余弦路由 | 注入模块清单、缩放系数、初始化／继承细节、源阶段LoRA与头处理未完整恢复。P0不实现LoRA／原型路由。 |
| 论文参照 | 表1 FT58.85、MILE自动路由64.14、oracle64.42、Joint66.85 | 这些是最终五域均值；不能与Source-only／单域Cityscapes结果比较，更不能把跨配置差距归因于持续机制。 |

**SATS 只用于解释来源，不能填补 MILE 缺项。** SATS 当前 `run.py` 使用 SGD（momentum0.9、Nesterov）；README 中 0.01／0.001、batch24及VOC30／ADE60 epochs是其自身实验。它不是 MILE 官方训练工程，也不是道路五天气配方。仅因学习率相似就推定 MILE 也用 SGD／30 epochs，没有原文支持。[SATS README](https://github.com/QIU023/SATS_Continual_Semantic_Seg)、[实际优化器快照](SATS_run.py)

本轮用完整标题及作者名检索代码入口，核对 arXiv abstract／HTML 中的外链，未确认 MILE 官方完整训练仓库；不据此断言仓库不存在，不联系作者，不把 SATS 仓库登记为 MILE 代码。

## 4. P0 工程选择和可比较边界

上级 [执行脚本](../scripts/run_b5_p0.py) 将完整源权重作为共同起点，真实 Fog 训练子集跑 200 步，全模型 AdamW、1024²、AMP，使用有限梯度／实际 optimizer step、权重指纹变化及保存重载检查。必要时开启 gradient checkpointing 再测速；SyncBN 在单卡转为普通 BN，Source eval 时固定状态。该短训与官方160k的scheduler、有效batch不同，**只衡量工程可行性，不产出正式FT效果**。实际运行是否通过、时延和峰值不能从源码推测，应读取返回的逐步日志与结果 JSON。

所有正式方法若从本完整 Cityscapes 源权重出发，应共享完全相同的 SHA 和预训练权限；ER／Joint的历史访问范围另按协议明示。若与 MILE论文表1作比较，应称“文献参照”，直到其配方和评价划分缺项被补齐，或明确声明本项目同协议适配比较。

## 5. 复核与限制

首批保存 18 份官方小型源文件／HTML，另保存对应权重训练日志的完整首行元数据并导出其中的配置；均留原URL、字节数及SHA。后续偏差核查新增的原始文件及派生比较也追加在同一manifest中。原文以HTML检查章节、表格和配置，不新增逐篇精读报告或用户本人已读标记。源码快照用于核验，不整套迁移旧版依赖；GPU机器仍复用既有 MMSeg1.2.1 环境。

本子任务没有下载任何模型权重或大型图像；权重真实字节校验和 GPU 行为由上级实际执行承担。公开元数据无法证明未披露的训练历史；MILE 官方配方仍有实质缺项。因此“B5加载／短训通过”“官方Source接近发布值”和“MILE忠实复现”是不同验收项目。

## 6. 本机82.0842 vs发布82.25：未定位的0.1658pp差异

P0 在完整 Cityscapes val 500 张上得到 **82.0842075% mIoU**，相对发布的单尺度 **82.25%** 为 **−0.1657925pp**。本节保留实际结果；没有通过改分母、标签、测试方案或重复选择运行来缩小偏差。[差异汇总](source_deviation_summary.json)

**官方82.25有对应日志支持。** 本次取得[完整官方训练日志](official_cityscapes_training_log_20211206.jsonl)，619,241 字节、SHA-256 `33774bae61da161e989184f0339be3cb995e5d85df32dd385f69ef48781dcbda`。其10次val按顺序为 79.17、79.76、81.58、81.84、81.66、82.25、82.12、81.63、82.36、82.25%；最后一次记录为 epoch431、lr0、mIoU0.8225。因此不能将差异解释为README数字错记或未对应最终训练记录。日志首行的测试配置仍是2048×1024、1024²滑窗、stride768、flip=False，与本次显式设置相同。[官方原始日志入口](https://download.openmmlab.com/mmsegmentation/v0.5/segformer/segformer_mit-b5_8x1_1024x1024_160k_cityscapes/segformer_mit-b5_8x1_1024x1024_160k_cityscapes_20211206_072934.log.json)

有界核查只读比较了 MMSeg v0.19.0 与 v1.2.1 的 `encoder_decoder.py`、`mit.py`、`embed.py`、`segformer_head.py`，并核查1.x的 `BaseSegmentor.postprocess_result` 与 decode head `predict_by_feat`；原始源码及[统一diff](mmseg_v0.19.0_vs_v1.2.1.diff)已保存。可确认：

- 官方日志环境为 **PyTorch1.8.0、MMCV1.3.15、MMSeg0.19.0+**；本次实际环境为 **PyTorch1.9.1、MMCV2.0.0、MMSeg1.2.1**。
- 0.x在推理函数内完成恢复尺寸、softmax并argmax；1.x将去padding、恢复原图尺寸和argmax放入 `BaseSegmentor.postprocess_result`。两版滑窗的窗口计数、重叠累加和除以覆盖次数的算法一致。
- MiT的 `EfficientMultiheadAttention` 在1.x中包含针对 **MMCV1.3.17** 接口变化的legacy分支，并调整query/key/value的维度转置路径。两版 `PatchEmbed` 和 `SegformerHead` 的核心前向在本次检查中未发现相应算法改动。

**这些只是已确认的环境与实现路径差异，不能作为0.1658pp的原因归因。** 本次没有重建精确的官方0.19.0+ commit／运行环境，没有在两个版本间进行同图预测或logit配对，也未独立隔离预处理数值、注意力实现或运行库影响。tag v0.19.0仅供源码比较，不能冒充官方带“+”版本的精确提交。当前结论是：**完成可追溯的B5 Source校准，存在−0.1658pp未定位偏差，尚未逐数值匹配官方成绩。** 不将“0.1pp以内”登记为通过，也不将该差异用于判断持续学习策略优劣。

可重复材料采集入口：[capture_source_deviation.py](capture_source_deviation.py)。它只读取官方日志／源码、产生摘要和diff，并更新来源manifest；不会运行模型或修改P0 Source结果与执行脚本。
