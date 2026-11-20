# FOCUS 复现记录

## 目标与成功标准

目标：忠实复现 FOCUS 的官方域增量医学图像语义分割实验，形成可验证、可追溯的结果，为后续在线持续域增量研究建立基线。

成功标准（计划）：确定论文目标实验、数据及划分、训练与评估协议和可接受的结果偏差；记录代码与依赖版本、数据来源及划分、命令、配置、随机种子和产物位置；完成真实训练与评估，并用可核查证据与论文结果对照。具体对照指标、数值、重复次数及容差：**待核实**。

## 官方来源与版本

- 官方仓库：[imigraz/FOCUS](https://github.com/imigraz/FOCUS)；论文 DOI：[10.1007/978-3-032-05185-1_22](https://doi.org/10.1007/978-3-032-05185-1_22)。
- 初始化基线：`d57650aff192744e22bfcb0c93793a078c74aad9`，本地 `master`，`origin` 指向官方仓库；2026-10-30 查询官方 `master` 指向同一提交。论文实验使用的确切代码版本：**待核实**。
- 项目基于 Lifelong-nnUNet；`requirements.txt` 固定 nnU-Net 提交 `77bc485ee025a61feb91cb0a0ed1c61a32a0f39f`，`hiddenlayer` 的分支本次解析为 `4b98f9e5cccebac67368f02b95f4700b522345b1`。实际依赖版本见下方环境清单。

## 已确认的官方代码说明与实验协议

以下为仓库 [README.md](../README.md) 的示例与 [create_3_split.py](../create_3_split.py) 的静态检查结果；它们与论文全部实验设置是否完全一致、运行行为及最终数据划分均 **待核实**。

- FOCUS 示例使用 2D、fold 0、每个任务 250 epochs、保存间隔 25、`CCD=0.9`、`DFP=0.05`、`num_samples_in_perc=1.0`、seed 1；README 说明 DFP 覆盖后者的样本选择。
- Hippocampus 顺序为 197 → 198 → 199，`layer_name=conv_blocks_context.3`；Prostate 顺序为 111 → 112 → 113 → 115，`layer_name=conv_blocks_context.6`。README 说明层名用于冻结配置，FOCUS 实际回放首层编码器特征。
- [FOCUS 论文](https://papers.miccai.org/miccai-2025/paper/0460_paper.pdf)规定训练/验证/测试为 56%/24%/20%。脚本 `do` 将各 fold 的原训练集打乱，以 `int(原训练数 * 0.3)` 为测试集，保留原验证集；每个任务重置 Python 随机种子 `123454321`。若原划分为 nnU-Net v1 默认五折（排序病例、`KFold(n_splits=5, shuffle=True, random_state=12345)`），得到的比例约为 56%/20%/24%，与论文验证、测试比例相反。原始划分来源和实际论文病例集合未知；**差异尚未解决，不生成最终划分**。
- `create_3_split.py` 映射 097→197、098→198、099→199；其主程序还会先处理前列腺任务，不能直接用于仅有三个海马任务的环境。它先创建 raw 目录符号链接，对旧预处理目录的非划分条目创建链接，另写新的 `splits_final.pkl`；依赖旧划分已存在，也不是幂等操作。脚本仅检查 train/test 互斥与总数，未检查验证集互斥及受试者跨集合泄漏。训练器读取 `train`/`val`，`evaluator3.py` 读取 `test`。应保留旧划分及病例身份映射，并在生成后独立验证三集合及受试者级互斥。
- FOCUS README 指向的 [Lifelong-nnUNet 预处理笔记本](https://github.com/MECLabTUDA/Lifelong-nnUNet/blob/cdbcd51fdf333fd4ad28cda4e854d6d0e0034452/distribution_aware__preprocessing.ipynb)在海马数据准备单元明确抛出 `NotImplementedError`；它随后要求先运行训练器产生默认 train/val 划分，再用脚本从 train 中抽取 30% 作为 test。因此公开笔记本所述默认流程与论文验证/测试比例的差异并非仅由假设造成；并未找到原始实验划分或 VOI 构造代码。
- [MICCAI 论文页面](https://papers.miccai.org/miccai-2025/0347-Paper0460.html)注明未提交补充材料；论文正文提供受试者数、双侧 VOI 和比例，但未给出裁剪边界、具体原始病例和划分清单。2026-10-30 检查 FOCUS 官方 `master`（远端仅列出该分支、无标签）与 README 指向的上游 `cl_vae` 当前代码后，仍未找到这些工件；不能排除作者在其他位置持有或发布。
- 这三个数据源及海马单类标签构建早于 FOCUS：2021 年 [Sanner 等](https://arxiv.org/abs/2109.01668)对 Dryad/HarP 描述左右两处固定位置各裁剪一个 64×64×48 VOI、合并为背景与海马两类；该工作单侧裁剪不能直接等同于 FOCUS 文中 Dryad/HarP 的双侧 VOI。2024 年 [ccVAE 工作](https://arxiv.org/abs/2407.21216)使用同一数据源并描述 260/50/270 样本，FOCUS 则报告 130/25/135 受试者和双侧 VOI；其具体转换的关系待核实。进一步检查 Lifelong-nnUNet `main`、`dev-continual_learning`、`dev-cl_ood`、`dev-task_agnostic_cl`、`dev-feature_replay` 及 [NCAdapt](https://github.com/MECLabTUDA/NCAdapt) 当前代码，未找到可证实为 FOCUS 版本的三域构造代码或病例划分。
- README 给出 `nnUNet_train_FOCUS`、GIN 顺序基线及其他基线；使用 `nnUNet_evaluate_all` 汇总 AVG、BWT、FWT，FWT 需要指定名称 `seq` 的单域模型。评估实际数据分区、指标计算和论文对应关系 **待核实**。

## 环境与数据约束

- 环境 `focus-repro`：WSL2 Ubuntu 22.04.5、Conda 4.12.0、Python 3.9.20、PyTorch 2.5.1+cu124、torchvision 0.20.1+cu124；RTX 3080 20480 MiB，驱动 616.92。`pip check`、核心依赖及 FOCUS trainer 导入和 GPU 最小张量运算通过。
- FOCUS README 指定 Python 3.9.20、CUDA Toolkit 12.4 和相应 PyTorch；继承的 [Lifelong-nnUNet 文档](../README_Lifelong-nnUNet.md) 给出较旧 CUDA/PyTorch 示例。本环境选用 CUDA 12.4 的 PyTorch 运行库，并未安装或验证完整 CUDA Toolkit（例如 `nvcc`）；论文实际 PyTorch 版本及完整训练兼容性 **待核实**。
- 原依赖安装需启用 `SKLEARN_ALLOW_DEPRECATED_SKLEARN_PACKAGE_INSTALL=True`（nnU-Net 依赖旧 `sklearn` 包名）；`python-gdcm` 3.2.6 源码包构建失败，选用有 Linux/Python 3.9 预编译包的 3.2.2；补充 `ipython==8.18.1` 以满足 hiddenlayer 未声明的导入依赖。
- `nnUNet_train_FOCUS --help` 当前失败：`run_training.py` 的 CCD 帮助文本含未转义的 `90%`，触发 argparse 格式化异常；未修改上游代码。普通训练路径是否受影响 **待核实**。
- WSL 仓库外目录 `/home/ysheng4/research/FOCUS-data`：原始来源 `sources/`，`nnUNet_raw_data_base=nnunet/raw_base`（内含 `nnUNet_raw_data`、`nnUNet_cropped_data`），`nnUNet_preprocessed=nnunet/preprocessed`，`RESULTS_FOLDER=results`，`EVALUATION_FOLDER=evaluation`。后三项路径均相对于上述目录。nnU-Net 使用 `results/nnUNet`，扩展使用 `results/nnUNet_ext`、`evaluation/nnUNet_ext`。`focus-repro` 的 Conda 环境变量保存后需重新激活；该版本 Conda 将含小写的键大写化，故两个 `nnUNet_*` 变量由环境下 `etc/conda/activate.d/focus-paths.sh` 设置，并由 `deactivate.d/focus-paths.sh` 恢复原值；另外两项由 `conda env config vars` 设置。已用 `conda run` 导入原版和扩展路径并断言有效。重建环境需重新配置这些路径与激活脚本。
- 三个来源均为 T1 MRI；[FOCUS 论文](https://papers.miccai.org/miccai-2025/paper/0460_paper.pdf)报告 DecathHip 130、Dryad 25、HarP 135 名受试者；前者为左右单侧预裁剪 VOI，后两者使用双侧 VOI。具体裁剪及受试者对应规则尚未取得，不能以早期 Lifelong 论文的单侧病例数直接替代。海马类别需统一；[Lifelong 文献](https://openaccess.thecvf.com/content/CVPR2022W/CLVision/papers/Ranem_Continual_Hippocampus_Segmentation_With_Transformers_CVPRW_2022_paper.pdf)描述合并区域为单个前景，具体三个域的原始标签映射及 FOCUS 实际转换版本待验证。
- [MSD Task04](https://medicaldecathlon.com/) 为 CC BY-SA 4.0，AWS 对象 `Task04_Hippocampus.tar` 的 HEAD 报 28,425,216 字节；官网报告 263 有标注训练、131 测试体积，旧文献另报告 260 训练体积，版本与筛选差异待核实。[Dryad MNI-HISUB25](https://datadryad.org/dataset/doi:10.5061/dryad.gc72v) 2016-10-22 版为 25 人，MRI 压缩包 9.92 GB，含 T1/T2 和人工亚区标注；具体文件及 Dryad 版本许可待核对。同一数据的 [NITRC 项目页](https://www.nitrc.org/projects/mni-hisub25/)列 CC BY-NC-SA 3.0，而其[下载协议页](https://www.nitrc.org/frs/downloadlink.php/7943)列 CC BY 3.0，不能据此推定 Dryad 版许可。[HarP 最终版](https://www.hippocampal-protocol.net/SOPs/index.php)提供 135 人人工标签；[图像说明](https://www.hippocampal-protocol.net/SOPs/labels.php)提醒 NIfTI 图像与 MINC 标签未保证完全匹配，另列原始 MINC 约 1.6 GB；ADNI 图像需申请并接受使用协议。[ADNI DUA](https://adni.loni.usc.edu/wp-content/themes/adni_2023/documents/ADNI_Data_Use_Agreement.pdf)对个人数据再分发及 AI 工具处理有限制，实际访问和使用本工具前需核实适用协议与数据保护条件。
- 2026-10-30 经用户批准下载：[MSD 原始包](https://msd-for-monai.s3.us-west-2.amazonaws.com/Task04_Hippocampus.tar)已保存在 `FOCUS-data/sources/msd/`，28,425,216 字节，SHA-256 `282d808a3e84e5a52f090d9dd4c0b0057b94a6bd51ad41569aef5ff303287771`（本地计算，尚未与上游校验值比对）。该包 `dataset.json` 声明 260 训练、130 测试体积；260 对训练图像及标签文件名匹配且与 JSON 一致，测试文件名与训练不交叉，260 对图像和标签均可读取、3D 几何信息一致、数值有限，空间分辨率 1 mm 各向同性，尺寸范围 xyz `[31,40,24]`–`[43,59,47]`，所有训练标签均包含 0/1/2。完整汇总见仓库外 `sources/msd/source-audit.json`；病例级受试者对应尚未证实，不能据文件名互斥推断无受试者泄漏。
- Dryad 官方网页文件流曾返回 HTTP 403，API 下载接口返回 HTTP 401；用户于 2026-10-30 提供原始压缩包，保存在 `FOCUS-data/sources/dryad/`。包大小 9,923,850,757 字节，MD5 `baab63e515e6bd997f3c3b03780038bb` 与 version 105 官方文件元数据一致，SHA-256 `42bd2391e3d0e57f4356b3f84247c570f67b74d3f00bd8860fed2f3c98954ee5`（本地计算）。完整解压成功，共 25 名受试者；每人均有标准和高分辨率 T1、T2、左右 MNI 空间标签。25 个标准 T1 MNI 图像及左右标签均为 197×233×189、1 mm 等距，几何信息匹配；50 个标准标签每个均含 0/1/2/3，左右前景没有体素重叠，图像数值有限；高分辨率 T1 与标签的头信息几何匹配，体素值未检查。结果详见 `sources/dryad/source-audit.json`；实际 FOCUS 选择的 T1 版本、双侧 VOI 构建与标签映射尚未核实。
- HarP 尚未取得并须先核实 ADNI 使用条件。原始来源、格式转换后的 nnU-Net raw、nnU-Net 裁剪及预处理输出须分别保存，且均不入 Git。

### 环境重建（Linux x86_64）

[Conda 显式包清单](conda-linux-64.explicit.txt)记录底层包及构建，[pip 版本清单](requirements-linux-64.lock.txt)记录 Python 包及 Git 依赖的实际提交；项目本身从当前工作区以 editable 方式安装。使用新的环境名，在项目根目录执行：

```bash
conda create -n focus-repro-restored --file repro/conda-linux-64.explicit.txt
conda activate focus-repro-restored
SKLEARN_ALLOW_DEPRECATED_SKLEARN_PACKAGE_INSTALL=True python -m pip install -r repro/requirements-linux-64.lock.txt
python -m pip install --no-deps -e .
python -m pip check
```

清单限定平台及包版本，但未锁定 pip 包文件哈希或构建时依赖；重建依赖外部仓库、索引及包持续可用，不能保证二进制逐字节一致。执行前应确认检出需要的项目提交；当前环境使用上述初始化基线及工作区内容。

## 实验记录与结果索引

### 临时两域 FOCUS 实验

- 2026-10-30 经用户确认：在 HarP 未取得、原论文病例和裁剪不可恢复的情况下，先做 MSD → Dryad 两域实验；此实验不是论文三域完整复现，且其结果不可直接作为论文指标复现。
- 使用 MSD 包 `dataset.json` 列出的 260 个有标注体积，排除目录中的 AppleDouble 文件；将标签 1、2 合并为单一前景。MSD 的受试者映射未知，按体积划分不能证明受试者级互斥，结果存在潜在泄漏。
- Dryad 使用 25 人的标准 T1 MNI 图像、左右标准 T1 MNI 标签，标签 1、2、3 以及左右合并为单一前景；只用 fold 0 训练受试者的标签确定 MNI 固定裁剪框，四周加 16 mm，裁剪起点 xyz `[42, 73, 24]`、大小 `[113, 77, 76]`。独立检查 25 人的前景均在该框内；验证和测试标签未用于确定裁剪框。此规则是临时方案，**不是**已核实的论文裁剪。
- 独立生成 fold 0：先以排序病例和 `KFold(n_splits=5, shuffle=True, random_state=12345)` 划分 train/val，再按官方 `create_3_split.py` 的 seed `123454321` 从原 train 中取 30% 为 test。MSD train/val/test 分别 146/52/62 个体积，Dryad 分别 14/5/6 人；检查了集合两两互斥及完整覆盖。其比例与论文声明的验证/测试比例有上述差异。Dryad 按受试者划分；MSD 无法验证受试者级划分。仅生成 fold 0，不能复用此裁剪框进行其他折的无泄漏验证。
- nnU-Net v1 的数据集分析和规划使用了全部病例（包括保留测试集）；除上述裁剪框外，规划不是严格的仅训练集拟合。`nnUNet_plan_and_preprocess -t 197 198 -pl3d None -tf 2 -tl 2 --verify_dataset_integrity` 成功完成，官方检查均报告 `Labels OK`、`Dataset OK`；生成 MSD 260、Dryad 25 个 2D 预处理病例。MSD 规划 patch `[56, 40]`、batch 366、每轴下采样 3 次；Dryad 分别 `[80, 128]`、81、`[4, 5]`。后续域训练实际使用的规划及网络行为以运行日志为准。
- 数据转换与划分脚本：[prepare_two_domain.py](prepare_two_domain.py)；训练脚本：[run_two_domain.sh](run_two_domain.sh)。项目基础提交 `d57650aff192744e22bfcb0c93793a078c74aad9`，脚本为该工作区新增文件。训练入口为官方 `nnUNet_train_FOCUS 2d -t 197 198 -f 0 -num_epoch 250 -save_interval 25 -s seg_outputs --store_csv -d 0 -layer_name conv_blocks_context.3 -num_samples_in_perc 1.0 -seed 1 -CCD 0.9 -DFP 0.05 --exp_name focus_two_domain`；仅限制数据增强进程和数值库线程数以适应机器资源，未改变训练 epoch 或 FOCUS 算法参数。`-seed 1` 的具体影响以代码为准，不应理解为所有随机源均已固定。
- 所有实验产物位于仓库外 `/home/ysheng4/research/FOCUS-data/experiments/two_domain/`；`preparation_manifest.json` 记录病例划分和裁剪，`preprocess.log`、`train.log` 保存运行记录，`results/` 保存检查点。训练于 2026-10-30 15:50 启动、23:11 完成（Asia/Shanghai）；日志中两个域均到达从 0 编号的 epoch 249，两域 `model_final_checkpoint.model` 均存在，`focus_trained_on.pkl` 记录两个域完成。
- 官方 `nnUNet_evaluate_all` 固定枚举的序列不包含 197→198；[evaluate_two_domain.py](evaluate_two_domain.py) 对该序列调用官方 `eval_task`，[watch_two_domain.sh](watch_two_domain.sh) 在训练进程退出且元数据确认两个域均完成后启动评估，日志位于 `evaluation-watcher.log`。两个阶段对两域均生成了测试预测、逐病例 CSV 和汇总文件。训练后测试 Dice（病例平均 ± 样本标准差）：MSD 域训练完成后，MSD 0.9044 ± 0.0206（62 个体积）、Dryad 0.5716 ± 0.0319（6 人）；继续训练 Dryad 后，MSD 0.8896 ± 0.0276、Dryad 0.9114 ± 0.0111。独立从保存的预测和原始二值标签重新计算了 4 组全部 136 个测试预测的 Dice，逐病例与 CSV 一致，图像尺寸、原点、间距和方向一致。以上为临时两域实验结果，并非论文三域复现结果。
- 官方跨任务指标汇总失败：`extract_metrics_from_csv_multi_mask` 在建立 mask 条目之前读取 `metrics[base_task][mask_name]`，产生 `KeyError: 'mask_1'`，因此自动输出不包含有效跨任务汇总；上述逐病例 Dice 和各域均值由独立计算核对，不依赖该汇总。单域 `seq` 对照尚未训练，无法给出官方定义的 FWT。尚未修改上游代码或核实论文指标公式及其对照关系。

## 当前阶段与下一步

- 当前阶段：临时两域 FOCUS 训练和测试预测已完成，测试 Dice 已独立核验；自动跨任务汇总存在上述代码错误。HarP 尚未取得，论文三域训练与评估尚未完成。
- 下一步：定位并修复跨任务指标汇总，核实指标定义；取得 HarP 并核实 ADNI 使用条件，继续核实原论文病例、VOI 和划分后完成三域复现。
