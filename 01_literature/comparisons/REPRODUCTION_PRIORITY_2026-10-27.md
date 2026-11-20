# 复现对象优先级与启动方案（域增量方法、已开源、不限应用场景）

日期：2026-10-27（Asia/Shanghai）。

2026-11-02场景更新：用户已确定天气变化无明显域边界（[D-007](../../00_management/DECISIONS.md)）。本文件主要保留原协议复现的选择依据与步骤，不将下文阶段式工程流程直接当作道路主实验。已完成GSMF／FOCUS复现的进展以[当前状态](../../00_management/PROJECT_STATE.md)为准；道路对照与无边界适配统一见[对照总表](../../03_experiments/COMPARISON_PLAN.md)。

## 0 选型约束与修订记录

当前约束：

1. **必须是域增量（DIL）方法**（D-002）：方法以固定类别、顺序域学习和旧域保持为设计目标，并在 DIL 协议下验证。类增量方法在论文里附带做过一个 DIL 基准，不算 DIL 方法。
2. **必须有官方开源训练代码**（D-004）：只公开数据划分、增强配置或模型来源的仓库不算。
3. **不限应用场景**（D-005，用户转述师姐意见）：复现和优化的对象可以来自遥感、医学等领域；迁移到道路天气场景并针对性改进，正是本课题的创新空间。
4. **道路主场景为无明显天气域边界**（D-007，2026-11-02新增）：阶段式原方法可继续用于原协议复现与机制诊断；道路主实验须核对不依赖真实切换通知的适配规则，不能把固定天气子集硬切序列作为唯一验证。标签、回放、窗口／周期及域身份权限另定；静态DG保留作比较，不改换DIL主线。

修订记录（同日）：

- 初稿推荐 MILE（D-003）：无官方代码，撤回。
- 第二稿推荐 FALCON，以 PLOP、RCIL 为对照（D-004）：三者都是类增量方法，只附带 Cityscapes 城市域实验，不满足约束 1，撤回。
- 第三稿推荐 FOCUS，GSMF 为备选（D-005）。
- 本版：**用户选定 GSMF-RS-DIL 为主复现对象，FOCUS 改为 P1（D-006，已采纳）**。

依据：38 个条目的逐篇报告、[文献索引](../LITERATURE_INDEX.md)，以及当天对官方仓库目录、README 和数据可得性的核查（见第 7 节）。尚未安装环境、下载数据或训练；数值均为原论文报告值，不是本项目结果。

## 1 结论

| 角色 | 对象 | 优先级 | 说明 |
| --- | --- | --- | --- |
| 主复现对象 | **GSMF-RS-DIL**（LIT-026，TGRS 2024，遥感 DIL） | P0 | 固定类、有标注、不回放旧图、测试无需域 ID。官方代码为 Apache-2.0，基于 MMSegmentation；Zenodo 上有作者的 GS-AUFPN 与 GSMF 权重，`log/` 中有训练日志；原文用单张 RTX 4090。已有 B 级精读报告，已知代码缺陷见报告第 11 节。 |
| 基础方法 | FT、ER、EWC、LwF | P0 | 在 GSMF 的 MMSegmentation 工程中实现，与 GSMF 同数据、同协议比较。原文表 IX／X 给出 FT、LwF 和联合训练的数值，可直接对齐；EWC、ER 原文没有，属于新增。官方仓库不含这些对照的配置，需要自己写。 |
| 分割网络 | DeepLabV3+、SegFormer | P0（DeepLabV3+）／P1（SegFormer） | DeepLabV3+ 是 GSMF 论文表 V／VI 的单域对照，MMSegmentation 自带配置；SegFormer 在同一框架中配置，原文无对齐值。 |
| 第一补充 | **FOCUS**（LIT-033，MICCAI 2025，医学 DIL） | P1 | 代码（Apache-2.0）里的 sequential、rehearsal、ewc、lwf 训练器可作为自写 FT、ER、EWC、LwF 的实现参照；其首层特征回放机制留到道路迁移阶段使用。时间允许再复现其前列腺协议。 |
| 道路迁移与创新 | Cityscapes→ACDC（雾→雨→雪→夜） | P1 | 在同一 MMSegmentation 工程中完成，见第 5 节。 |

## 2 符合约束的候选比较

"同表内效果"只在各自论文的表格内有意义，跨论文不可排名。

| 候选 | 发表 | 是否 DIL 方法 | 应用与网络 | 同表内效果 | 代码实况 | 涵盖的对照 | 结论 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GSMF-RS-DIL（LIT-026） | TGRS 2024 | 是：双阶段，不回放旧图，冻结浅层加双蒸馏 | 遥感；GS-AUFPN（ResNet-101），MMSegmentation | Potsdam→Vaihingen 旧／新 61.91／65.81（FT 54.82／67.21，LwF 62.53／63.80） | Apache-2.0；6 次提交；有作者权重与日志；只给 GS-AUFPN 与 GSMF 的配置；有已知缺陷 | 论文：FT、LwF、联合训练；单域网络：DeepLabV3+、PSPNet、DANet 等 | **主对象（D-006）** |
| FOCUS（LIT-033） | MICCAI 2025 | 是：阶段式，首域后冻结编码器，回放首层稀疏特征 | 医学 MRI；2D U-Net（nnU-Net） | 前列腺 AVG 80.5（Seq.+GIN 76.5、MiB 59.0）；海马 89.5 | Apache-2.0；19 次提交；含 sequential、rehearsal、ewc、lwf、mib、plop 等训练器 | 论文：Seq.、EWC、MiB、TED、ccVAE | **P1** |
| MDIL-SS（LIT-034） | WACV 2022 | 是：多域增量，域专属适配器、BN 与解码器 | 道路（CS→BDD→IDD）；ERFNet | CS→BDD 后 CS／BDD 为 65.21／55.73（FT 40.05／52.74） | 有代码与检查点；缺文件、环境旧 | FT、FE、单头 FT、LwF、ILT | P2：测试需要域 ID |
| MineC2FNet（LIT-035） | IJCAI 2026 | 是：粗标签域→细标签域 | 矿区二类；TensorFlow | 精细域 mIoU 73.64 | 有缺失导入等问题 | MDIL-SS 等 | P3 |
| LwS（LIT-028） | TPAMI 2024 | 否：类与域同时增量 | 道路 | — | 有代码；固定类分支不完整 | FT、ILT、MiB、PLOP 等 | P3 |
| PLOP、RCIL、FALCON（LIT-040、041、039） | CVPR 2021／2022／2025 | 否：类增量方法，只附带城市域实验 | 道路 | — | 均开源 | — | 可选对照 |

## 3 全部文献的复现优先级

| 等级 | 含义 |
| --- | --- |
| P0 | 第一阶段必须完成，构成复现章节主体 |
| P1 | P0 跑通后进行 |
| P2 | 可选扩展或工程参考 |
| P3 | 只借鉴机制，不复现 |
| 不复现 | 没有官方训练代码，或不是 DIL 方法 |
| 待定 | 缺全文 |

### 3.1 P0：GSMF 原协议复现

| 对象 | 复现什么 | 对齐目标（原文值，mIoU） | 主要风险 |
| --- | --- | --- | --- |
| 评测复现 | 用作者 Zenodo 权重在测试划分上评测，先确认数据与评测管线 | 表 V：GS-AUFPN Potsdam 74.87；表 IX：GSMF 61.91／65.81；表 X：51.02／36.21 | 数据切块、通道（IRRG）、标签映射须与作者一致 |
| GS-AUFPN 单域 | Potsdam 80k 次训练（Urban 30k 次） | Potsdam 74.87、Vaihingen 69.77；Urban 44.41、Rural 35.89 | — |
| GSMF 增量 | Potsdam→Vaihingen 10k 次增量训练；随后 LoveDA Urban→Rural | 表 IX：61.91／65.81；表 X：51.02／36.21 | 教师 BN 是否真正冻结、图参数与空洞率是否与论文一致（报告第 11 节） |
| FT、LwF、联合训练 | 在同一工程中自写配置：FT 为从旧权重直接训新域；LwF 为只加输出蒸馏、不冻结；联合训练为两域混合 | 表 IX：FT 54.82／67.21，LwF 62.53／63.80，联合 74.45／66.84；表 X 对应行 | 原文未给各对照的实现细节，需记录自定配置 |
| EWC、ER | 在同一工程中新增：EWC 为阶段末估计 Fisher 并加二次惩罚；ER 为缓存少量旧域切片及标签混入新域批次 | 原文无，属新增 | ER 违反 GSMF"不回放旧图"的前提，只作"允许回放"的参考对照，缓存字节单列 |
| DeepLabV3+ 单域 | MMSegmentation 自带配置，按 GSMF 的数据与预算训练 | 表 V：Potsdam 73.94；表 VI：Urban 43.76 | MMSegmentation 自带的 Potsdam 转换脚本默认通道可能与 IRRG 不同，需核对 |

### 3.2 P1

| 对象 | 内容 | 说明 |
| --- | --- | --- |
| FOCUS（LIT-033） | 对照其 sequential、rehearsal、ewc、lwf 训练器检查自写实现；移植首层特征回放到道路阶段；时间允许再复现前列腺协议 | 前列腺表 2：FOCUS AVG 80.5；数据下载渠道待核 |
| SegFormer | 在 GSMF 工程中配置 SegFormer，先用公开 Cityscapes 权重验证评测管线 | 原文无对齐值 |
| 道路天气迁移 | 新增 Cityscapes 与 ACDC 域任务（19 类，评价用 val），用 DeepLabV3+／SegFormer 跑 FT、ER、EWC、LwF 和 GSMF 方案 | 外部参照：MILE 表 1（FT 58.85、EWC 59.18）、LIT-010 表 7／8，仅比趋势；GSMF 只验证过两域，五域需新设计 |
| LIT-017 Cityscapes、LIT-019 ACDC | 下载与划分 | 两者 test 标注不公开；ACDC 每天气 train 400、val 100（夜 106） |

### 3.3 P2、P3 与可选对照

- P2：LIT-034 MDIL-SS（唯一开源的道路 DIL 方法，测试需要域 ID；ERFNet 也是机器人部署的轻量候选）；LIT-021 IDD、LIT-022 BDD100K（需要更多道路域时）。
- P3：LIT-035 MineC2FNet；LIT-028 LwS。
- 可选对照：LIT-040 PLOP、LIT-041 RCIL、LIT-039 FALCON（类增量方法）。

### 3.4 不复现：没有官方训练代码

| 文献 | 保留用途 |
| --- | --- |
| LIT-023 MILE | 天气 DIL 协议与数值参照；LoRA 专家与原型路由思路 |
| LIT-024 PSS | 完整专家＋自编码器路由思路 |
| LIT-007 SimCS | 在线协议与 ER 容量参照 |
| LIT-008、LIT-009 | 基础方法实现细节、回放选样思路 |
| LIT-010 | 天气两阶段协议与 A／F 参照；浅层表征与 BN 的遗忘机制 |
| LIT-025、LIT-027 | 测试时路由、统计头思路 |
| LIT-032 Traffic Scenes | **待定**：取得全文后再判断 |

### 3.5 不复现：不是 DIL 方法

综述 LIT-001–006；类增量与其他任务 LIT-011–016；CTTA 的 LIT-036–038（按 D-002）。

## 4 GSMF 复现步骤

每个正式实验按 AGENTS.md 第六节在 `03_experiments/` 保存目标、配置、代码版本、结果和结论；复现代码放在 `02_baselines/`。

### 阶段 0：代码、环境与数据

1. **GPU**：本机没有 NVIDIA GPU，需服务器；原文用单张 24GB RTX 4090，batch 4。
2. **代码**：以固定提交建立 GSMF 代码副本，先修报告第 11 节可静态确认的缺陷：
   - `tools/checkpoint_process.py` 的 `parse_args` 没有调用 `parser.parse_args()`，且使用 `/result` 绝对路径；
   - LoveDA 配置把 `loss_name` 写成了 `oss_name`；
   - 两份主配置的 `_base_` 路径和自定义模块导入路径（`projects.DIL.mmseg` 与 `GSMF-RS-DIL.mmseg`）不一致；
   - 转换权重的输出位置与配置中 `load_from` 不一致。

   另需核对：图节点数与通道数是否与论文对调、最后两级是否用空洞卷积、教师 BN 是否保持 eval。
3. **环境**：README 给出 Python 3.8、CUDA 11.1；报告记录的依赖为 torch 1.8.0+cu111、mmcv 2.0.0、mmengine 0.8.2、mmseg 1.2.1，其中有作者本地 wheel，需换成公开安装包。若服务器显卡较新，可能需要升级版本，需自测兼容。
4. **数据**：ISPRS Potsdam 与 Vaihingen 的 IRRG 版本（Potsdam 24 张训练、14 张测试；Vaihingen 16／17；原图编号见论文 §IV-A），按 512×512、重叠 128 像素切块；LoveDA Urban、Rural。目录结构严格按仓库 `data/` 示例。ISPRS 数据的获取方式待核。

完成标志：作者权重的评测结果与表 V、IX 一致（允许小的舍入差异）。

### 阶段 1：训练复现

先训练 GS-AUFPN Potsdam 单域，再做 Potsdam→Vaihingen 的 GSMF 增量，与表 IX 和作者日志对照；然后做 LoveDA。

完成标志：GSMF 旧／新域接近 61.91／65.81。

### 阶段 2：基础方法与分割网络

在同一工程中实现 FT、LwF、联合训练（对齐表 IX／X），新增 EWC、ER；训练 DeepLabV3+ 单域（对齐表 V 的 73.94）。自写实现与 FOCUS 代码中的对应训练器对照检查。

完成标志：FT、LwF 接近原表，方法排序能解释。

### 阶段 3：道路天气迁移

在同一工程中加入 Cityscapes→ACDC 四天气序列，用 DeepLabV3+ 与 SegFormer 跑 FT、ER、EWC、LwF 和 GSMF 方案，记录阶段×域 mIoU 矩阵、遗忘、新域适应和资源成本。之后进入改进与机器人部署。

## 5 道路场景的创新切入点（待验证假设）

- GSMF 冻结编码器第一阶段，FOCUS 在首域后冻结整个编码器，两者都靠"固定浅层"保住旧域。LIT-010 发现，天气变化主要改变浅层表征与 BN 统计，这正是遗忘的重要来源。在天气 DIL 中，浅层既需要适应、又需要保旧，冻结策略可能限制新天气适应。可尝试的方向包括选择性解冻、BN／CN 处理、浅层特征回放。
- GSMF 只验证过两个域；天气序列有五个域，多步蒸馏与教师更新需要新设计。
- GSMF 的图推理模块针对遥感俯视图设计，对道路前视图是否有益需要单独验证。

以上都是研究假设，没有本项目实验支持。

## 6 风险与应对

| 风险 | 应对 |
| --- | --- |
| 官方仓库不含 FT、LwF 等对照的配置 | 在同一工程中自写，并对照 FOCUS 代码的实现；配置写入实验记录 |
| 已知代码缺陷与本地 wheel 依赖 | 按第 4 节逐项修复；先用作者权重做评测复现，再训练 |
| README 的迭代数标注不一致（GSMF 权重文件名为 10000，README 结果表写 80k） | 以论文 §IV-B 和作者日志为准，记录差异 |
| ISPRS 数据获取方式待核 | 先做 LoveDA（公开）也可完成方法复现 |
| 只有双域，且应用为遥感 | 原协议复现只验证代码与方法；道路效果在阶段 3 用统一协议验证 |
| 本机无 NVIDIA GPU | 使用服务器；原文配置为单张 24GB 显卡 |

## 7 依据与核查范围

- 逐篇报告：GSMF（LIT-026，含第 11 节代码核查）、FOCUS（LIT-033）、MDIL-SS（LIT-034）等，入口见[文献索引](../LITERATURE_INDEX.md)。
- 2026-10-27 核查（只看了网页、目录和 README，没有运行）：
  - GSMF：[官方仓库](https://github.com/HuangWBill/GSMF-RS-DIL)。许可证为 Apache-2.0；6 次提交，2 个未关闭 issue。README 给出 Python 3.8、CUDA 11.1、RTX 4090，以及 IRRG 数据目录、GS-AUFPN／GSMF 的训练与测试脚本、`tools/checkpoint_process.py`、4 份配置；作者权重在 Zenodo（记录 13950503）；未提供 FT、LwF、联合训练的配置。
  - FOCUS：[官方仓库](https://github.com/imigraz/FOCUS) README 与训练器目录。
  - MDIL-SS：[官方仓库](https://github.com/prachigarg23/MDIL-SS)。
  - PLOP、RCIL、FALCON 的摘要：[PLOP](https://arxiv.org/abs/2011.11390)、[RCIL](https://arxiv.org/abs/2203.05402)、[FALCON](https://arxiv.org/abs/2311.15965)。
  - 道路方向的开源 DIL 补查：[SurveyCSS](https://github.com/YBIO/SurveyCSS) 清单及多轮检索。
- 本文由 AI 辅助整理，不登记用户本人已读，也不代表任何方法已经复现。
