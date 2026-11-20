<!-- ROAD_FIVE_DOMAIN_CURRENT_BEGIN -->
## 当前道路工作：第5项阶段A正式实验及轻量交接完成（2026-11-11）

- 最新用户范围“暂时先完成阶段A”。阶段A全部完成；B暂缓，C未授权，不自动启动。
- 正式目录：`experiments/road_five_domain/formal-A-plan-20261111-140000`；六次各4000步、24份完整周期checkpoint、62新增评价格15878逐图与42旧格指纹复用共104格、独立预测重读/GT直方图/训练与协议复核、图表/预固定样例及轻量包安全解包/全SHA全部通过。实际exit-code.txt=0，completion.json与handoff/handoff-verification.json complete/PASS。
- 三方法seed0分别自己的Rain学生→Snow→Night，batch2/crop512/FP32、AdamW1e-5/PolyLR4000，每1000验证/保存，固定iter4000，无val择优。教师/学生完整参数与BN缓冲逐阶段严格继承；GSMF教师参数冻结/训练态BN更新、LwF教师全部状态固定。所有条件仅当前学生推理，参数/缓冲不变，无oracle/TTA/测试更新。
- 最终Night后CS/Fog/Rain/Snow/Night（%）：ft 53.2786/57.0810/43.2148/43.7064/38.7919; gsmf 52.9036/59.3877/45.7989/46.3704/38.6739; lwf 42.0937/52.1572/42.9603/42.7344/33.6891。阶段已见域均值只含已学域，未来域提前分数不计入；最终五真实域均值与合成条件单列。具体变化/负遗忘/混淆去向见RESULTS.md与results-index.json所指目录。
- 包：`experiments/road_five_domain/formal-A-plan-20261111-140000/handoff/formal-A-plan-20261111-140000-light.tar.gz`，外置同名.sha256，SHA `c09bbf786f0b55cdf8500c8ac691d8e69d69baaeed751b3616d685ac959ba31e`。权重/原图/全量预测留远程。包内预完成STATUS与包外最终完成证据分开，避免自引用。
- Snow400/100、Night400/106，A/B/C原清单保持。官方共享视频目录已披露，未独立证明地理/邻帧隔离；仅seed0、不主张稳定显著/纯天气因果/严格未见强度泛化。LwF未搜索超参；CUDA反向非逐位确定，resume不保证RNG/采样游标精确恢复。未重训Source/Fog/Rain seed0、未删除/覆盖旧数据checkpoint，未升级环境。
<!-- ROAD_FIVE_DOMAIN_CURRENT_END -->

<!-- ROAD_RAIN_CHAIN_CURRENT_BEGIN -->
## 第3项真实三域链正式实验与轻量交接完成（2026-11-11）

- 用户“继续提示词二”授权的FT／原版GSMF／LwF-DIL，各自Fog学生→Rain4000步、22格7000次完整逐图、7000保存预测独立重读/GT直方图/协议核验、旧20格指纹核对复用、七checkpoint六条件42格/19类/阶段均值及差值、固定样例与图表、轻量包和实际解包全SHA核验全部完成。
- 唯一正式目录：`experiments/road_clear_fog_rain/formal-seed0-plan-20261110-180543`；实际流水线exit-code.txt=0，completion.json及handoff/handoff-verification.json均complete/PASS。详情见RESULTS.md/SUMMARY.md、results/*check.json与remote-index.json。
- 固定seed0/batch2/crop512/FP32、AdamW1e-5/PolyLR4000，每1000验证/保存、主iter4000，无val择优，未重训Source/Fog。新优化器从0；12份周期checkpoint严格可读且优化器/调度器/iter完整。GSMF教师参数冻结、342个BN缓冲原训练态更新；LwF教师全部参数/缓冲固定于自己的Fog学生，学生浅层更新。推理全天气仅部署学生，参数/全部缓冲不变，无oracle/TTA/测试更新。
- 最终Rain后CS/Fog/Rain及三真实域等权均值（%）：ft 57.7056/63.1118/54.6443/58.4872; gsmf 55.8056/62.3571/53.2537/57.1388; lwf 49.2420/55.8377/50.0044/51.6947。各阶段已见域均值只含A、A/B、A/B/C；Source共享，未来Rain提前分数不纳入早期均值，合成四条件单列。
- 交接包：`experiments/road_clear_fog_rain/formal-seed0-plan-20261110-180543/handoff/formal-seed0-plan-20261110-180543-light.tar.gz`，外置同名.sha256，归档SHA `d5bff048c7415019cd29ef2ea3623a42d450492030b23463b4753d48be77f988`。包内MANIFEST及安全成员/新目录实际解包/全文件集合与哈希一致；72份CS新原始样例、42份固定Rain样例及对齐图保留，权重/数据/全量预测留远端。
- Rain官方train400/val100、A/B原清单与指纹保持。五个Rain共享视频目录披露，未独立证明地理/邻帧隔离；仅seed0，未主张统计显著、纯天气因果或严格未见强度泛化。LwF为未经搜索默认适配。无新增天气/种子/模块、下载、环境升级或checkpoint覆盖；当前实验任务已完成。更长序列仅作为后续考虑，未自动启动。
<!-- ROAD_RAIN_CHAIN_CURRENT_END -->

<!-- ROAD_LWF_BN_CURRENT_BEGIN -->
## 道路第2项：seed0正式实验与轻量交接全部完成（2026-11-10）

- 用户“继续提示词二”授权的两组LwF-DIL / teacher_bn_source_stats各4000步、10单元4200次完整逐图评价、独立预测重读/GT直方图核验、五模型25条目与19类表、曲线/固定6场景新48份原始预测、轻量包及解包哈希核验全部完成。
- 正式目录：`experiments/road_lwf_bn/formal-seed0-plan-20261110-153000`。结果与限制见RESULTS.md/SUMMARY.md，真实完成状态见completion.json、STATUS.md及handoff-reviewed/handoff-verification.json；训练/评价流水线exit-code.txt=0。
- 两组均同一Source严格转换、全新AdamW，seed0/batch2/crop512/FP32、固定iter4000；教师全部状态等于Source，评价只学生分支、19通道、参数/缓冲不变。旧15单元按指纹/协议核对复用，不伪称本轮重新推理。
- 最终校阅交接包和外置SHA在本正式目录handoff-reviewed/（初版handoff/保留），文件名为formal-seed0-plan-20261110-153000-light.tar.gz及同名.sha256，解包文件集合与MANIFEST全文件哈希一致。权重、数据、全量预测和环境均留远端，索引remote-index.json。
- 仅seed0；真实/合成跨库、ACDC强度支持未知，不主张统计显著、严格未见强度泛化或已证明BN因果解释；LwF为未搜索超参的默认适配对照，KD全像素无T²。未追加seed/搜索/天气，未重训旧组。当前无剩余已授权任务；后续重复须另行明确授权。
<!-- ROAD_LWF_BN_CURRENT_END -->

<!-- ROAD_FOG_SEVERITY_CURRENT_BEGIN -->
## 固定模型的受控合成多雾强度评价：完成（2026-11-10）

500个共同 Cityscapes fine val 场景，晴天与三档合成雾，预检和12/12正式单元、矩阵独立复核、图表及回传包核验通过。完整证据、结果和约束见 `experiments/road_fog_severity/eval-final-seed0-20261109-182100/SUMMARY.md`，预测远程保留。ZIP val 图通过内部CRC，ZIP MD5 与用户提供的官方值一致。训练清单的原帧/记录与哈希检查未见重叠，跨数据集地理或邻近帧独立未证明。

本次评价 Git 归档已独立提交至本地分支 `repro/road-fog-severity-20261110` 并推送个人仓库 `main`，提交 `f204c4f5754ec91f0052a779c8f4c92143886183`；远程提交及树 `961576d643cea1c050c963d040a0e0463a02702d` 均已核验。未包含其他实验未提交修改、数据集、权重或含原图的预览；当前工作分支未切换。
<!-- ROAD_FOG_SEVERITY_CURRENT_END -->

# GSMF-RS-DIL 复现状态

<!-- ROAD_FORMAL_CURRENT_BEGIN -->
更新时间：2026-11-08 12:45:16 +08:00

正式seed0状态：**complete**。全部训练、六组完整val评价、严格转换及独立预测核验均完成；流水线与监测实际退出码均为0，训练/监测会话已正常结束，当前无训练任务。正式结果及资源成本已写入RESULTS.md。

- 输出：`experiments/road_clear_to_fog/formal-seed0-20261108-resume01`
- 持久训练会话：`road-recovery-20261108-105307-1597`
- 预算：源60000、FT4000、GSMF4000；batch2/crop512；只运行本次授权范围。
- 阶段退出码：运行目录events.jsonl；总退出码：会话目录exit-code.txt。
- 本轮持久监测已完成：以20秒间隔检查事件/进程，最终独立重读1800张预测并更新RESULTS/REPRO，随后正常退出。
- 主机/WSL停机会中断训练和监测，须人工核对完整状态后resume。
- 本运行从原运行iter40000恢复模型/AdamW/PolyLR/迭代位置；原始损坏iter50000保留。原checkpoint未保存RNG及数据迭代器状态，不声称与不停机逐位一致。

<!-- ROAD_FORMAL_CURRENT_END -->

更新：2026-11-08

- **当前目标**：保留已完成的 ISPRS Potsdam → Vaihingen 复现；新增独立 Cityscapes fine 正常白天 → ACDC fog 的道路19类有监督两阶段 DIL。用户已于2026-11-08授权既定seed0正式训练，范围仅源60000、FT/GSMF各4000步。
- **上游版本**：`e141e523e86f98f772ee787bb2aa95272f38e4fe`；该版本为作者上游基准；工作区变更和个人仓库状态可通过 Git 查询。
- **阶段**：环境、合成输入、作者权重单切片评估，以及样例上的基础训练→权重转换→增量训练各一次迭代已通过；完整数据已生成并通过文件清单验证，正式数据训练链路单步及作者权重完整评估通过；ISPRS 正式基础训练 80,000 次、权重转换、增量训练 10,000 次和最终完整评估均已完成。
- **硬件和环境**：WSL2 Ubuntu 22.04.5；NVIDIA GeForce RTX 3080 20 GB，计算能力 8.6；`nvidia-smi` 显示驱动 615.71.08、CUDA UMD 13.4。独立环境 `GSMF_RS_DIL` 位于 `~/miniconda3/envs/GSMF_RS_DIL`，从本机 `Bridge` 复制并调整，移除了与本项目无关且产生冲突的包和指向其他项目的路径；未修改 Windows 驱动或系统 CUDA。
- **实际版本**：Python 3.8.20、PyTorch 1.9.1+cu111、torchvision 0.10.1+cu111、MMCV 2.0.0（OpenMMLab 的 cu111/torch1.9 wheel）、MMEngine 0.8.2、MMSegmentation 1.2.1、NumPy 1.24.4、OpenCV 4.8.0.74、YAPF 0.40.1。`pip check` 无依赖冲突；torchvision 编译扩展可加载。项目实际导入链还需要 `regex`、`ftfy` 等，见锁定文件。当前环境未安装 torchaudio；所查模型、数据、评估及训练入口未直接导入它。
- **与作者环境的区别**：README 要求 Python 3.8、CUDA 11.1 和严格依赖版本；`requirements.txt` 写的是 PyTorch 1.8.0+cu111、torchvision 0.9.0+cu111、torchaudio 0.8.0，MMCV wheel 和 MMSegmentation 等使用作者本机路径，无法直接安装。此处复用现有 1.9.1+cu111/0.10.1+cu111，是环境替代，不能视为作者原始版本；1.8.0 在本机未实测，不能据此断言其不兼容。PyTorch 当前构建包含 `sm_86`，在本机实际运行通过；NVIDIA WSL 文档要求使用 Windows 主机驱动，不在 WSL 安装 Linux 显卡驱动。`nvidia-smi` 的 CUDA UMD 版本不等于 PyTorch 自带的 CUDA 运行时版本。
- **版本记录及重建**：`environment/conda-linux-64.explicit.txt` 是 Conda 平台包的精确列表，`environment/pip-linux-64.lock.txt` 为完整 pip 版本快照，包含克隆环境中保留的额外包。可在 Linux x86-64 依次执行 `conda create -n GSMF_RS_DIL_rebuilt --file environment/conda-linux-64.explicit.txt`，再执行 `conda run -n GSMF_RS_DIL_rebuilt python -m pip install -r environment/pip-linux-64.lock.txt`。重建会下载大型 PyTorch wheel；本次为避免大规模下载未在全新环境实测完整重建，源站可用性及额外包的构建仍需验证。MMCV wheel 针对 torch 1.9/CUDA 11.1，不能随意换 torch 或 CUDA。
- **验证**：`env -u PYTHONPATH conda run --no-capture-output -n GSMF_RS_DIL python tools/verify_environment.py`。GPU 矩阵乘法与 MMCV CUDA `roi_align` 均通过；按原 Potsdam 和 ISPRS 配置构建 ResNet-101 模型并调用 `init_weights()`，采用 seed 0、随机初始化、合成输入 `(2, 3, 64, 64)` 和随机 6 类标签。Potsdam 总损失 2.728696，361 个梯度张量；ISPRS 总损失 3.178860，其中 CE 2.266464、Hin 0.911814、KL 0.000581，317 个梯度张量，旧 backbone/head 无梯度，新 backbone/head 有梯度；所有损失及梯度有限。峰值显存分别约 419 MiB 和 818 MiB。使用 `model.parse_losses` 与 MMEngine 一致地归约按样本返回的 KL 损失；未执行优化器更新。日志在本地忽略目录 `experiments/environment-validation-20261028/`。四个训练/测试入口在无 `PYTHONPATH` 时均能导入对应 ISPRS 配置；该项仅检查导入，不代表完整训练或评估通过。
- **代码差异**：修正 Potsdam 和 ISPRS 顶层配置的 `_base_` 路径和自定义导入；新增 `gsmf_rs_dil` 包入口映射已有自定义模块，避免与安装的 MMSegmentation `mmseg` 冲突；四个训练/测试入口加入项目根目录搜索路径；新增可重复运行的合成验证脚本。未更改模型结构、损失函数、训练策略或数据划分。
- **待解决**：仓库自带的 Potsdam 和 Vaihingen 各只有 1 对训练样例和 1 对验证样例；已另外获取并准备完整数据，作者权重的完整评估已通过。转换脚本已修复并在样例上验证；LoveDA 等其他顶层配置路径和导入未修复。README 模型表将 ISPRS 增量阶段写成 80,000 次，但论文、配置和作者日志均为 10,000 次，正式实验采用 10,000 次。
- **当前下一步**：本轮已授权道路seed0工作全部完成，无需继续训练或恢复。源60000、FT/GSMF各4000及六组完整官方val评价、1800张最终预测独立核验均通过；精确比较、逐类IoU、资源及恢复限制见experiments/road_clear_to_fog/RESULTS.md。未追加种子/天气/算法。

- **GS-AUFPN Potsdam 单切片测试（2026-10-28）**：经用户同意从 README 所链接的 Zenodo 获取作者 `iter_80000_potsdam.pth`，保存在 Git 忽略目录 `checkpoints/`；623,587,959 字节，MD5 `248a18fbea74ca6ee7abb5d2cd4bd3f1`，与 Zenodo 元数据一致。使用现有 512×512 验证切片 `top_potsdam_4_14_IRRG_1_5`、seed 0、batch size 1、整图推理、无 TTA 和作者 checkpoint；指定 `model.pretrained=None` 避免加载多余的 backbone 预训练权重。原测试入口运行成功，aAcc 90.92%、mIoU 63.40%、mAcc 69.75%；六类 IoU 依次为 89.22、85.32、69.60、45.93、90.35、0.00%。独立混淆矩阵计算 mIoU 63.4041739%，与 MMSeg 汇总一致；还用合成样例检验了 255 忽略标签、缺失类别和跨样本计数累计。IoU 按整个数据集累计交并集，再对有效类别求均值，包括 clutter；并非逐图 IoU 平均。作者日志对应 3,150 张验证切片，mIoU 74.87%，不可与本地单张结果直接比较。命令、日志、输出预测和计算细节在 `experiments/potsdam-test-smoke-20261028/`。
- **本次兼容性及限制**：原 YAPF 0.43.0 与 MMEngine 0.8.2 的 `FormatCode(..., verify=...)` 不兼容，导致 Runner 初始化失败；已在项目 Conda 环境改用作者指定的 YAPF 0.40.1 并更新 pip 锁定文件，`pip check` 通过。原 `LoadSingleRSImageFromFile` 需要 `osgeo.gdal`，本环境未安装；GDAL 3.0.2 与现有 Python 3.8.20 无法共同解析，允许降级 Python 的方案涉及大量依赖变更，未执行。本次测试仅在实验目录加入临时 `osgeo.gdal` 适配器，调用临时安装的 Rasterio 1.3.10 自带 GDAL 3.8.4，不是原生 osgeo 绑定；此切片读取结果与 tifffile 逐像素逐通道一致。独立 tifffile 调试推理同为 63.40%，两次预测有 1 个像素不同，原因未确定。作者原版 GDAL 环境、其他切片及完整数据上的一致性仍待验证；未更改模型、损失或训练策略。

- **GSMF-RS-DIL ISPRS 双域单切片测试（2026-10-28）**：经用户同意从 README 链接的 Zenodo 获取 `iter_10000_isprs.pth`，保存于 Git 忽略目录 `checkpoints/`，772,540,155 字节，MD5 `c74eb75c697eec402d731ebe6ef82818`，与 Zenodo 元数据一致。原测试入口加载 checkpoint，日志未报告参数键不匹配；使用原合并数据集和 DGIoUMetric 分域统计、seed 0、batch size 1、整图推理、无 TTA，`model.pretrained=None`。旧域 Potsdam（`top_potsdam_4_14_IRRG_1_5`）aAcc 90.14%、mIoU 62.34%、mAcc 68.62%；新域 Vaihingen（`top_mosaic_09cm_area27_5_0`）aAcc 84.36%、mIoU 55.29%、mAcc 79.13%。独立混淆矩阵计算的 mIoU 分别为 62.3350% 和 55.2887%，与框架汇总一致。两域 mIoU 均含 clutter：Vaihingen 的标签无 clutter，但预测出现 clutter，因此该类 IoU 为 0，而类别准确率未定义。作者推理路径对两域都使用增量分支 `backbone_1`、`decode_head_1`。作者 README 的完整验证集结果为 61.91% 和 65.81%，与各单切片结果不能直接比较。两张影像使用先前的临时 Rasterio GDAL 适配器读取，并与 tifffile 逐像素逐通道一致；尚未验证原生 osgeo GDAL。命令、运行配置、日志、预测和独立指标在 `experiments/gsmf-isprs-test-smoke-20261028/`；未更改模型、损失或训练策略。

- **训练链路小规模验证（2026-10-28）**：修复 `tools/checkpoint_process.py` 参数解析和不一致的默认路径，支持明确指定输入/输出，拒绝覆盖输出；保持去除辅助头及复制旧/新分支的映射，未改网络或训练策略。在仅各一对训练与验证样例、临时 Rasterio/GDAL 适配器、seed 0、原图 512×512、batch 4 下，基础阶段随机初始化（`model.pretrained=None`）训练 1 次，loss 2.4121、训练日志 memory 11574 MiB，并保存 checkpoint、完成验证；将此 checkpoint 转换，706 个原权重中去除 8 个辅助头张量，双分支 1396 个张量的键和值逐一核对一致。增量阶段加载该转换结果，无键不匹配警告，训练 1 次，loss 2.5076、CE 1.6320、Hin 0.8756、KL 约 0、训练日志 memory 10908 MiB，保存 checkpoint 并完成双域验证。权重检查确认旧 backbone 和 head、新 backbone 的 stem 和 layer1 参数未变化，新 backbone 的 layer2 和新 head 参数发生变化。两次均覆盖迭代数、验证与保存频率为 1，优化器及 batch 维持配置；该验证不是正式结果。命令、配置、日志和 checkpoint 在 `experiments/train-smoke-20261028/`。
- **论文与正式方案**：论文确认 ISPRS 使用 NIR/R/G，原图训练划分为 Potsdam 24 张、Vaihingen 16 张，剩余各 14、17 张用于测试，切片 512×512 且重叠 128；具体训练 ID、边缘处理依据等和运行命令见 `experiments/isprs-repro-plan-20261028/PLAN.md`。论文写离散随机缩放，但作者代码和实际日志均为连续 0.5–2.0，本方案采用代码实现并记录差异。正式基础初始化为 `open-mmlab://resnet101_v1c`，日志确认作者使用该权重；已获用户同意从 OpenMMLab 下载到 `checkpoints/pretrained/resnet101_v1c-e67eebb6.pth`，大小 178,791,759 字节，SHA-256 `e67eebb62faab570c7c2268f93f5b68db2cd1730d5397923f34b39820c691d64`，已使用该权重通过一轮样例训练和验证，日志 `experiments/pretrained-train-smoke-20261028/`。完整数据已准备并核对清单；原生 GDAL 尚未验证，实际数据单步训练、作者权重完整评估和正式训练均已完成。

- **数据来源核对**：ISPRS 当前 benchmark 总览（https://isprs.org/resources/datasets/benchmarks/UrbanSemLab/default.aspx）称 2018 年起所有参考数据可下载，列出的 Potsdam 和 Vaihingen 包分别为 13.3 GB、16.0 GB，须遵守其使用条款；旧的单域页面仍称测试标签未公开。已按官方归档内容下载所需影像和标签并完成预处理，完整验证结果与作者报告一致；标签个别像素及 Potsdam 4_12 的完整标签存在已记录的差异。

- **模型实现差异**：论文 Implementation Details 说最后两次下采样换成膨胀率 2 和 4 的卷积；作者基础训练配置及日志实际 `dilations=(1,1,1,1)`、`strides=(1,2,2,2)`，增量配置同样如此。以作者实际训练配置及日志为复现依据，保留此差异，不能将其说成论文文字一致。
- **数据获取进度**：用户授权在本机不存在完整数据时获取 ISPRS 数据。项目及已检查的用户目录仅发现示例；官方数据总包含无关数据，已按官方公开口令访问，并使用 HTTP 范围读取顺序获取论文相关 IRRG 和全量标签成员。原始包、下载日志和校验值存于 `data/ISPRS_raw_downloads/` 和 `experiments/isprs-data-acquisition-20261028/`；两域影像及所需标签已获取且外层 ZIP 成员 CRC 校验通过，SHA-256 记录在 `experiments/isprs-data-acquisition-20261028/ranges.log`；完整切片准备及文件清单核验已完成。官方 Vaihingen 使用条款限定研究用途、不向第三方分发，并要求论文引用和致谢；条款备份于该实验目录。

- **Potsdam 切片与标签初步核对**：官方 IRRG 的 `top_potsdam_2_10_IRRG` 原图左上 512×512 与仓库训练示例影像逐像素、逐通道相同；官方完整 RGB 标签映射到仓库六类索引后，训练样例 `2_10_0_0` 有 4 像素不同、验证样例 `4_14_1_5`（原图行 384、列 1920）有 2 像素不同，均是官方低植被而示例为 impervious surface。训练原图的旧 participants 标签在这 4 像素上与完整标签相同，差异原因尚未知。已采用官方参与者训练标签和完整验证标签，不能声称与作者所有原始标签逐像素完全一致。完整窗口按 384 步长生成，其验证切片总数及作者权重指标与日志一致。

- **Vaihingen 切片核对**：从官方原包逐项下载并校验 area11、area27 影像与完整标签；仓库训练样例 `area11_0_0` 和验证样例 `area27_5_0` 影像与原图对应窗口逐像素、逐通道一致。官方标签颜色映射后与样例分别差 8、7 个像素，涉及多个类别，原因未明。按论文原图划分和 384 步长仅保留完整窗口，官方标签尺寸计算出 Vaihingen 训练 387、验证 442 张；Potsdam 验证 3150 张，两域验证共 3592 张，与作者日志一致。该证据支持窗口边缘规则，但不证明所有作者切片或标签完全相同。

- **Potsdam 标签异常**：官方 `5_Labels_all.zip` 中训练原图 `4_12` 的标签 3600 万像素均不属于标准六色，常见颜色如 [9,222,221]；`5_Labels_for_participants.zip` 的同名训练标签为标准六色。已检查选用的 24 张 Potsdam participants 训练标签、14 张 Potsdam complete 验证标签及 33 张 Vaihingen complete 标签，全部只含六种标准颜色；影像包及完整预处理均已完成。准备脚本将 Potsdam 训练标签改用官方 participants 包、验证标签使用官方 complete 包，遇到非标准颜色直接报错；其余差异和实际每个标签来源、SHA-256 保存在数据清单。标签来源问题及决定见下载和核对日志。
- **本机训练性能初测**：使用下载的 ImageNet 预训练、4×512×512 和临时 GDAL 适配器、同一个训练示例运行 20 次迭代；热身后日志约 0.22–0.23 秒/步，峰值首步记录 11574 MiB，非完整数据吞吐及验证耗时，不能作为正式总耗时保证。`experiments/train-timing-20261028/`。尝试对现有环境执行 GDAL 3.6 Conda dry-run，9 分钟仍未解决且占用近 6 GB 内存，已中止，未改环境。

- **GDAL 兼容性方案**：新增 `gsmf_rs_dil.datasets.isprs_tif_loader.LoadISPRSTiff` 并仅在 ISPRS 配置中替代原 `LoadSingleRSImageFromFile`；以环境中已有 tifffile 读取本项目三通道 TIFF，保持输入 float32、通道顺序和元信息，未调整模型或优化策略。七张仓库样例及生成切片与早先 Rasterio/GDAL 适配读取结果逐像素、dtype 和 shape 一致；不等于已在原生 osgeo GDAL 下完成验证。独立环境 GDAL 3.6 dry-run 在约 9 分钟及近 6 GB 占用时中止，没有修改环境。

- **TIFF 适配器端到端检查**：不设置 `PYTHONPATH`，实际 ImageNet 预训练权重下完成基础阶段 1 次优化、保存、验证，转换所得 checkpoint 后完成增量阶段 1 次优化、保存及双域验证；增量 checkpoint 加载没有参数键不匹配。基础 loss 2.7446，增量 loss 2.6991。预训练 checkpoint 中分类层 `fc.weight`、`fc.bias` 被忽略，与作者原始日志一致；是预训练分类头与分割骨干的预期差异。原生 GDAL 未验证，样例验证不能替代完整数据核对。命令和日志位于 `experiments/tif-loader-chain-smoke-20261028/`。

- **冻结语义核对**：一次增量优化前后比较发现，旧 backbone/head 及新 backbone stem、layer1 的可训练参数不变，但这些模块的 BatchNorm running mean/variance 分别有 212/212、16/16、6/6、20/20 个张量改变。作者代码只关闭参数梯度且 `norm_eval=False`，训练模式仍更新统计量；为忠实复现保留此行为，不把冻结参数等同于完全冻结模块状态。

- **完整数据准备**：`tools/prepare_isprs.py` 按论文原图划分、384 步长生成影像和标签，以官方 Potsdam participants 训练标签、complete 验证标签及 Vaihingen complete 标签为源，验证六色与原图配对并逐切片记录 SHA-256 和原图坐标。命令位于 `experiments/isprs-prepare-20261028/command.sh`，输出目录为 `data/ISPRS_prepared_20261028`。生成及复核通过：Potsdam 训练 5400、验证 3150，Vaihingen 训练 387、验证 442；全部 18,758 个影像/标签文件的 SHA-256 与清单一致，训练与验证原图 ID 无交集；数据占约 9.3 GiB。完整评估及正式数据单步检查已通过。

- **完整数据训练单步验证**：在 `data/ISPRS_prepared_20261028` 上采用实际预训练权重、seed 0 和 batch size 4 运行基础训练 1 次、保存并转换，随后加载转换权重在 Vaihingen 训练 1 次并保存。基础 loss 2.5470，增量 loss 2.6986；仅迭代数、验证和 checkpoint 频率用于调试而覆盖，非正式训练。命令、解析配置、日志和 checkpoint 位于 `experiments/full-data-train-smoke-20261028/`。作者权重完整评估已通过。

- **作者基础权重完整验证**：对准备的 3150 张 Potsdam 验证切片，用原测试入口、作者 `iter_80000_potsdam.pth`、新 TIFF 兼容加载器、无 TTA 和 batch size 1 得到 aAcc 88.72%、mIoU 74.87%、mAcc 83.30%，aAcc 与 mIoU 与作者日志一致；输出和命令位于 `experiments/full-data-author-checkpoint-20261028/`。作者增量权重完整评估也已通过，见下。

- **作者增量权重完整双域验证**：对 Potsdam 3150 张及 Vaihingen 442 张验证切片，用作者 `iter_10000_isprs.pth`、原分域评估、batch size 1、无 TTA，Potsdam aAcc 81.09%、mIoU 61.91%、mAcc 72.01%；Vaihingen aAcc 86.20%、mIoU 65.81%、mAcc 76.18%。两域 mIoU 均与作者报告一致。命令、配置、预测和日志在 `experiments/full-data-author-checkpoint-20261028/`。这验证作者权重及数据评估流程，不代表本机已训练复现。
- **正式实验已获确认**：使用已生成的数据和 ImageNet 预训练权重，按 `experiments/isprs-repro-plan-20261028/run-after-confirmation.sh` 独立保存源码状态、命令、数据和权重校验、日志、checkpoint 与最终测试；基础 80000 次后转换，增量 10000 次，seed 0、batch 4，保持作者优化器和验证间隔。样例热身后训练约 0.22–0.23 秒/步，完整权重测试约 0.023–0.028 秒/切片，粗略总耗时约 8–10 小时或更长（实际取决于负载、I/O、保存），checkpoint 约 80–90 GiB，当前空闲约 909 GiB。作者 CheckpointHook 出现更优 mIoU 会删除此前的 best checkpoint，间隔 checkpoint 保留；用户已确认该训练方案及最佳 checkpoint 自动清理行为。

- **正式训练启动（2026-10-28）**：用户已确认上述实验方案及旧最佳 checkpoint 的自动清理。初次后台启动在准备 provenance 时被执行环境终止，未开始训练，目录 `experiments/isprs-full-20261028-EySQ7d/` 保留；随后在持久会话重新启动并已完成，实验目录 `experiments/isprs-full-20261028-ucOKFM/`，启动脚本 PID 74819，已观测到训练迭代与有限损失，状态及阶段记录位于该目录 `provenance/`，训练输出位于 `base-console.log`。脚本已依次完成权重转换、增量训练和两次评估，状态文件显示 complete。

- **正式训练首次阶段检查（2026-10-28 23:59，本地时间）**：当时实验 `experiments/isprs-full-20261028-ucOKFM/` 正在运行，启动脚本 PID 74819；第 1000 次迭代 `base/iter_1000.pth` 已保存并成功读取，包含 706 个模型张量、优化器和调度器状态；对 3150 张 Potsdam 验证切片得到 aAcc 81.63%、mIoU 63.00%、mAcc 75.02%，当时保存了 `base/best_mIoU_iter_1000.pth`，随后按原始最佳 checkpoint 机制被更优权重替换；训练继续至 1000 次之后。此为早期验证，不是最终复现结果。完整实验及最终指标见下。

- **ISPRS 正式训练完成（2026-10-29）**：用户确认后在 `experiments/isprs-full-20261028-ucOKFM/` 运行，`provenance/status.txt` 为 `complete`，基础训练到 80,000 次、转换和增量训练到 10,000 次均有日志和最终 checkpoint，最终两阶段完整测试于本地时间 07:33:15 完成。基线使用 ImageNet ResNet-101、seed 0、batch 4、AdamW lr 1e-4；增量以本次基础训练的第 80,000 次权重转换初始化，seed 0、batch 4、AdamW lr 1e-5。最终测试 batch 1、无 TTA，基线 Potsdam aAcc 88.37%、mIoU 74.01%、mAcc 82.48%；增量 Potsdam aAcc 82.75%、mIoU 63.76%、mAcc 73.23%，Vaihingen aAcc 86.21%、mIoU 65.67%、mAcc 74.96%。与作者 README 的 74.87%、61.91%、65.81% 相比，mIoU 差异依次为 -0.86、+1.85、-0.14 个百分点。该次是单种子实验，环境和标签来源差异见上，不应据此归因或断言统计显著性。
- **权重和结果记录**：基础权重 `base/iter_80000.pth`、转换权重 `conversion/iter_80000_DIL.pth`、增量权重 `incremental/iter_10000.pth` 的 SHA-256 与 `provenance/base-weights.sha256` 和 `provenance/incremental-weights.sha256` 均一致；输入权重、数据清单与 `provenance/inputs.sha256` 一致。最终测试命令、配置、预测和日志均在同一实验目录。基础训练最佳验证 mIoU 为 74.58%（第 52,000 次）；按既定方案转换和最终测试均采用第 80,000 次权重，而非最佳 checkpoint。

- **结果汇总与可视化（2026-10-30）**：从正式模型的全部保存预测与标签重建三个 6×6 混淆矩阵，aAcc、mAcc、mIoU 与原测试日志精度一致；补算基础 Potsdam、增量 Potsdam 和增量 Vaihingen mF1 分别为 83.84%、75.53%、77.86%。论文对照、各类别 IoU、案例选择规则与图见 `experiments/isprs-results-20261030/RESULTS.md`；精确矩阵及脚本位于同目录。案例分别为 `top_potsdam_5_15_IRRG_1_11` 与 `top_mosaic_09cm_area27_0_3`，先筛选至少四类各占 1% 的切片，再选单图 mIoU 最接近候选集中位数者，不能将单图结果与全域混淆矩阵汇总结果混用。


- **道路迁移工程（2026-11-07）**：修改前只读核对远端 master 与本地 HEAD 均为 `e141e523e86f98f772ee787bb2aa95272f38e4fe`；已有未提交遥感修改保留且快照至 `experiments/road_clear_to_fog/preflight/`，无提交/推送。新增 `road_dil/`、`configs/road/`、`tools/road/` 和独立实验协议，不更改旧模型/损失。两阶段源训练一次，FT/GSMF共享同一19类道路源权重；严格逐键转换，原GSMF参数冻结/训练态BN语义保留，统一新部署分支。完整正式入口有tmux、退出码、严格前置检查、源码/配置快照、评价/汇总及保留optimizer/scheduler的resume；正式门禁需真实短链路通过。
- **道路正式训练前状态（真实验证完成，2026-11-07）**：四个官方归档已解压/校验，全量数据审计PASS（City2975/500、fog400/100），ACDC官方共享3个源视频目录按作者地理划分协议记录。源/FT/GSMF各8步、严格转换/保存重载及六组完整官方val评价均完成；全部梯度有限，19通道输出、冻结参数及BN行为、统一新分支推理正确。三个最终checkpoint哈希及1800张预测CRC/尺寸/类别通过验证，384裁剪资源对照和optimizer/scheduler续训能力验证通过。本轮调试预算使用52/100步；总证据`experiments/road_clear_to_fog/real-validation-evidence-20261107.json`，产物检查`experiments/road_clear_to_fog/evidence/artifact-integrity.json`。正式训练未启动；建议seed0源60000、B各4000、batch2/crop512，估算约4.18小时加余量，预留4–6小时或更长、输出20GiB。道路STATUS/PLAN为当前记录，正式长训练待用户确认。

- **遥感版本 Git 备份完成（2026-11-07）**：按用户要求，将城市道路修改前的19个遥感复现文件提交为 `e2ebda781dc9eaba1e74a20bd5161ea7cbd887f8`，已推送至用户私有仓库 `https://github.com/mumuci512/GSMF-RS-DIL` 的 `main`。远端提交与Git树均已核对一致。独立本地分支 `repro/isprs-before-road` 跟踪 `personal/main`；原作者 `origin` 保留，新增 `personal` 指向用户仓库。备份期间道路工作区、HEAD 和主索引保持原样，当时未推送道路代码、数据、checkpoint 或新增日志。审阅清单、验证、推送记录和已核验bundle见 `experiments/isprs-before-road-backup-20261107/`。本仓库局部Git署名复用已核验Windows配置，GitHub认证仅用于mumuci512；未改全局Git配置或Conda环境。
