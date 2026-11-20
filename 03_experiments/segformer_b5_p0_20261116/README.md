# P0执行报告：协议、SegFormer-B5资源校准与MUSES清单

日期：2026-11-16（Asia/Shanghai）。任务来源：[导师反馈研究计划§7的P0](../../01_literature/comparisons/ADVISOR_FEEDBACK_RESEARCH_2026-11-16.md#7-建议的下一步执行计划)。本报告为AI辅助工程执行与来源核验，未增加逐篇阅读报告或用户本人已读标记。

**P0已完成：形成一页工作协议；在家中20GB GPU上完成官方B5源权重严格加载、200步真实数据短训和906张五域Source评价；完成MUSES夜雨／夜雪实际文件目录与标签清点。B5可继续作为P1工程底座，无须因本轮显存成本改用B2。** 本次不是MILE复现，也未启动P1的正式FT／ER／Joint训练。

## 1. 协议与源权重

[PROTOCOL.md](PROTOCOL.md)固定本轮19类完整监督、已知训练切换点、固定模型测试及不提供真实测试域ID；明确FT、ER、MILE参照与Joint的历史权限，ER容量留待P1按实际预算锁定。阶段式设置仅用于本轮校准，不登记为论文最终协议或新的主方法选择。

使用OpenMMLab官方`87a052ec` Cityscapes完整分割权重，MiT-B5＋256通道分割头，81,974,739参数；980个参数／缓冲区键严格匹配。公开配方为ImageNet-1K主干→Cityscapes train，未发现ADE20K中转，但未独立取得原始预训练逐样本历史。此权重已经学习Cityscapes，本轮没有重新训练160k步源阶段。权重来源、完整SHA及训练清单路径见[prepare.json](remote/prepare.json)；与NVlabs原版768通道头的差异见[配方审计](recipe/RECIPE_AUDIT.md)。

实际运行复用已有`GSMF_RS_DIL`依赖环境：PyTorch1.9.1+cu111、MMCV2.0.0、MMEngine0.8.2、MMSeg1.2.1；初次执行所在仓库HEAD为`d9d3298aee037ee7bb9e78ee2f1b67d8793ef3d0`，该值仅作历史来源。本实验现已独立迁至`~/research/segformer_b5_p0_20261116/`，与GSMF工程平级，不导入GSMF工程代码。未修改原训练模块、既有数据、历史检查点或驱动。单GPU将SyncBN转换为普通BN并保留参数及统计。初始运行环境、源码快照和pip版本见[environment.json](remote/environment.json)、[runtime_source](remote/runtime_source/)与[pip_freeze.txt](remote/pip_freeze.txt)。

## 2. 20GB实测结果

真实ACDC Fog train清单固定前32张，seed0，随机缩放／1024²裁剪／翻转／颜色扰动，完整模型微调；AdamW主干lr6e-5、头lr×10、weight_decay0.01。200步常数学习率仅为资源探针，不作为正式FT调参结果。

| 项目 | 实测值 |
|---|---:|
| GPU物理显存 | RTX3080，20,480MiB |
| microbatch／梯度累积／有效batch | 1／1／1 |
| AMP／梯度检查点 | FP16／关闭 |
| 完成的真实优化更新 | 200次；全部实际执行 |
| 训练循环总耗时 | 139.78秒 |
| 第21–200步平均／中位耗时 | 0.6957／0.6897秒／步 |
| 同一统计范围吞吐 | 1.4375图／秒 |
| 训练峰值allocated／reserved | 15.0855／15.5898GiB |
| 有限loss／梯度，参数更新，保存后严格重载 | 全部通过 |

峰值在保存／创建重载模型之前捕获；吞吐包括本轮数据供给与同步，不是纯GPU算子速度或机器人端到端延迟。初始GPU约占用810MiB，未发现其他模型训练进程；本次数据子集、负载与完整正式训练仍有差异，不能把这一吞吐直接当所有方法预算。

首轮默认AMP scale65536在首次反传出现非有限梯度，尚未完成优化更新，见[原始失败日志](logs/execution.txt)。将初始scale改为256后，从同一官方源权重全新开始，200步loss／梯度全部有限、无跳步；失败尝试不并入成功吞吐。无需开启梯度检查点；更大有效batch可在后续评估梯度累积，但不自动等同于多卡SyncBN batch12。

精确执行条件见[effective_probe_config.json](remote/effective_probe_config.json)、[逐步日志](remote/train_amp_scale256/steps.jsonl)和[result.json](remote/train_amp_scale256/result.json)。`resolved.py`保留模型与官方优化器分组快照，其中继承的160k训练循环／scheduler未执行；本次实际使用脚本手动200步循环，以effective配置及结果回执为准。

## 3. 固定Source五域评价

重新加载原始官方源权重，使用FP32、单尺度(2048,1024)等比缩放、1024²滑窗／stride768、无flip，恢复原图尺寸累计混淆矩阵。评分不是上述200步Fog短训后的模型成绩。

| 域 | 官方val样本数 | Source mIoU（%） |
|---|---:|---:|
| A：Cityscapes | 500 | 82.0842 |
| B：ACDC Fog | 100 | 75.0359 |
| C：ACDC Rain | 100 | 64.4077 |
| D：ACDC Snow | 100 | 61.4686 |
| E：ACDC Night | 106 | 30.9138 |
| 五域等权均值 | 共906张 | **62.7820** |

最差域为Night，30.9138%。每域19类均有有效union；模型全state_dict评价前后字节指纹相同，且与200步短训前指纹相同，见[source_state_check.json](remote/source_state_check.json)。逐类IoU及推理资源见[source_results.json](remote/source_results.json)，每域混淆矩阵保存为`remote/source_{A–E}_confusion.csv/.npy`。

**与官方发布值有未定位的差异：** 本次CS为82.0842，较该权重发布单尺度82.25低0.1658pp。官方对应训练日志末次val确为82.25；显式测试配置未发现不同。原环境PyTorch1.8.0／MMCV1.3.15／MMSeg0.19.0+与本次不同，注意力兼容和后处理路径也有版本变更，但缺少逐图对照，不能把它们断言为偏差原因。核验材料见[配方审计第6节](recipe/RECIPE_AUDIT.md)。本轮已取得可追溯的强Source起点，仍不称精确恢复官方发布分数。

这些是**Source-only验证集分数**，不能与MILE表1的最终五域FT／MILE分数混作同协议排名；尚不能据此声称达到SOTA、降低遗忘或验证新机制。当前清单版本为CS2975/500、ACDC训练各400，Night val106；不是默认将ACDC2025扩展版全部标注并入训练。现有manifest与当前文件存在性已核对，未重新哈希全量原始图像。评价的GT边际像素计数与既有标签直方图逐类一致，ACDC共享视频目录的隔离边界仍保留。

## 4. MUSES夜雨／夜雪清点

通过官方下载包的ZIP中央目录与meta，逐条交叉核对2,500张RGB及1,750份公开trainIds标签，缺配／孤立标签均为0；不是仅引用论文总数。

| 条件 | train：RGB／标签 | val：RGB／标签 | test：RGB／公开标签 |
|---|---:|---:|---:|
| Night＋Rain | 150／150 | 25／25 | 75／0 |
| Night＋Snow | 150／150 | 25／25 | 75／0 |

取得并解码train／val×两条件各一对RGB与标签：共8个PNG，均1920×1080，标签值域检查通过。真实标签后缀为`_gt_labelTrainIds.png`，直接使用0–18／255，不二次映射；test真值不公开。完整RGB包约5.66GB，本轮没有整包下载，仅取得元数据、目录和固定4对样本；没有执行MUSES模型评价。

逐图路径、全24格统计、19类映射、来源SHA和获取脚本均见[muses/AUDIT.md](muses/AUDIT.md)。录制REC标识跨split重叠，作者的地理隔离声明尚未独立验证；共享REC也不能直接判定泄漏。之后可使用两条件各25张val作固定复合条件初测，不据现有数据审计宣称严格未见组合泛化。

## 5. 证据接收、验证与P1入口

轻量接收包包含46份文件，1,167,535字节，SHA256：`c3cae0eeea90ad7b5168780a3b1da05d75aff803c28bbee51a75d64602b1d44f`。本机已校验归档SHA、安全提取路径、payload逐文件SHA、200步资源统计、五域矩阵及独立GT边际；来源快照与MUSES清点也已离线复算。结果见[VERIFICATION.json](VERIFICATION.json)。

```powershell
python 03_experiments/segformer_b5_p0_20261116/scripts/verify_evidence.py
python 03_experiments/segformer_b5_p0_20261116/muses/audit_muses.py
```

当前远程独立实验目录：**`/home/ysheng4/research/segformer_b5_p0_20261116/`**。官方源权重及`train_amp_scale256/smoke_200.pth`均在此目录；原GSMF内的P0目录及对应导出包已迁出。运行、准备、导出入口和工作manifest已切换到新根目录。`data/`软链接只读复用原始数据，Python依赖环境仍复用现有环境；未移动原始数据或改动GSMF实验。

迁移时48份原文件逐项比对，两个模型权重SHA不变；改写后的5497条清单记录的图像／标签路径均存在，新根目录导入及入口编译通过，没有重新训练或评价。回执见[MIGRATION.json](MIGRATION.json)、[MIGRATION_VERIFICATION.json](MIGRATION_VERIFICATION.json)与[当前文件哈希清单](CURRENT_MANIFEST.json)。远程`provenance/`保留原始源码、配置、manifest和接收包。本机`remote/`、原始归档及[完整成功日志](logs/execution_scale256.txt)作为初次执行的不可改写证据保留，因此其中旧路径代表当时运行位置；不据迁移后的脚本冒充原执行版本。历史包校验清单见[EVIDENCE_MANIFEST.json](remote/EVIDENCE_MANIFEST.json)。

后续P1可从此同一官方源SHA建立FT／ER／Joint，使用完整官方train训练、官方val选择超参数，先锁定学习率／预算搜索范围、ER容量及调参预算；不再从train另扣验证集或以val替代官方test。MILE具体checkpoint、头宽、优化器、步数、完整输入及评价split等缺项已对齐列出；官方完整训练工程仍未确认，SATS默认配置不能代填。没有这些材料时只称文献参照或明确声明的本项目适配比较，不登记MILE忠实复现完成。

## 6. 后续正式评测要求（2026-11-17更新）

用户要求已写入根目录[AGENTS.md](../../AGENTS.md)及[D-012](../../00_management/DECISIONS.md)，后续对话应自动遵守：train训练、val调参、test正式测试；测试标签隐藏时必须提交官网获取正式成绩并保存回执。本报告62.7820%仍是五域官方val的等权均值，不是官网test分数。

ACDC账号已注册，正在等待官方审核；当前官方测试状态为“待官方评测”，尚无官方成绩。本轮按用户最新指令仅维护规范，未启动P1。
