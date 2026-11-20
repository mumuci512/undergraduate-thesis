# 第3项：Cityscapes→ACDC-fog→ACDC-rain接收与分析

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: validate
- Origin Date / Last Updated: 2026-11-11（Asia/Shanghai）
- Verification Status: ANALYZED；归档、文件集合、配置／来源和矩阵复算通过，未独立重跑模型。
- Model Reproduction Verdict: CANNOT_VERIFY（本机没有完整权重、原始GT与全量预测）
- Version Label: road_clear_fog_rain_seed0_received_v1

## 1. 结果位置与实际完成范围

- [本地接收目录](formal-seed0-plan-20261110-180543/)：原始轻量包、外置SHA及补回的最终完成记录。
- [解包后的正式结果](formal-seed0-plan-20261110-180543/formal-seed0-plan-20261110-180543/RESULTS.md)：完整三阶段真实域表、合成强度表、方法和资源说明。
- [42格指标与来源](formal-seed0-plan-20261110-180543/formal-seed0-plan-20261110-180543/results/42-cells.csv)、[逐类表](formal-seed0-plan-20261110-180543/formal-seed0-plan-20261110-180543/results/class-iou-wide.csv)、[混淆矩阵](formal-seed0-plan-20261110-180543/formal-seed0-plan-20261110-180543/results/matrices/)、[图表](formal-seed0-plan-20261110-180543/formal-seed0-plan-20261110-180543/results/figures/)。
- [本机检查脚本](review_received_step3.py)与[900项检查记录](REVIEW_formal-seed0-plan-20261110-180543_checks.json)。

FT／原版GSMF／LwF-DIL各自沿自己的Fog模型在Rain训练400张上完成seed 0／4000步，固定iter4000。新增22个完整评价单元、7000次逐图评价；核对复用旧20格，七个唯一检查点形成42格，不重复计算共同Source。72份新增CS固定样例预测及42份Rain样例预测随包保存；权重、原始数据与全量预测仍在远程。

远程正式目录为`/home/ysheng4/research/GSMF-RS-DIL/experiments/road_clear_fog_rain/formal-seed0-plan-20261110-180543`，本地解包目录不是可直接运行训练的完整工程。

## 2. 接收与协议核验

归档为13,730,584字节，SHA-256为`d5bff048c7415019cd29ef2ea3623a42d450492030b23463b4753d48be77f988`。归档成员路径和类型安全，新目录实际解包文件与归档一致；671份payload及两份manifest，共673个文件，SHA清单覆盖672份文件，全部通过。训练源码快照89份与准备／授权／正式指纹一致，原模型及损失源码与第2项快照一致。

本地最初只有压缩包。包内STATUS停留在“正在生成轻量包”，不据此将训练判为未完成。已通过`home-wsl`只读取回包外最终[completion.json](formal-seed0-plan-20261110-180543/completion.json)、[解包核验记录](formal-seed0-plan-20261110-180543/handoff-verification.json)、[最终状态页](formal-seed0-plan-20261110-180543/REMOTE_FINAL_STATUS.md)、最终status／pipeline记录及外置SHA；归档SHA和最终状态关联哈希一致，实际流水线退出码为0。远程说明包内保存打包前状态以避免自引用。补回记录及来源见[接收凭据](formal-seed0-plan-20261110-180543/REMOTE_COMPLETION_RECEIPT_2026-11-11.json)，未改动原包内文件。

本机独立复算42份整数混淆矩阵的mIoU、19类IoU、GT／预测计数及交并集，与JSON／CSV一致；旧20矩阵与第2项本地归档逐元素相同。CS及三档Foggy共享同500场景／GT，ACDC-fog与Rain各100张；GT有效像素与清单直方图一致。22份远程全量预测重读记录的ID数量和矩阵匹配，114份本地固定样例的SHA与索引匹配。已目视检查真实域阶段热图及合成强度曲线，数值与表一致。

三份父权重SHA匹配前两项记录；FT单分支698个state张量完整继承，GSMF／LwF从各自Fog学生698个张量复制成教师与新学生1396个目标张量，包含BN缓冲、独立存储，旧教师排除。转换报告、逐键来源和源码逻辑一致，真实输入eval输出等价／保存重载检查的远程记录通过。本机未重新读取实际权重张量，不能把这些关联记录称为本机重新完成的数值转换实验。

正式配置仅用C_train优化、C_val定时验证，新建AdamW／iter0，三组seed0、batch2、crop512、FP32、lr1e-5、PolyLR4000。教师策略保持原定义：GSMF教师参数固定而342个BN缓冲发生变化；LwF教师全部状态固定于自己的Fog学生，学生全量更新。三组4000次loss记录均有限，全梯度检查仅覆盖首步；没有正式resume。评价只用学生、参数／缓冲不变，已见域均值不纳入未来域提前评价。Rain官方train／val共享五个视频目录，未发现记录内帧ID／RGB字节及解码像素重复，但地理／邻帧独立未获证明。

## 3. Rain阶段后的主要结果

数值为mIoU%，差值为百分点（pp）。

| 方法 | CS晴天 | ACDC-fog | ACDC-rain | 三真实域等权均值 |
| --- | ---: | ---: | ---: | ---: |
| FT | 57.7056 | 63.1118 | 54.6443 | 58.4872 |
| 原版GSMF | 55.8056 | 62.3571 | 53.2537 | 57.1388 |
| LwF-DIL | 49.2420 | 55.8377 | 50.0044 | 51.6947 |

原版GSMF相对FT三域分别为−1.9001／−0.7547／−1.3905pp，均值低1.3484pp；相对本轮LwF三域仍较高。**两域Fog结束时GSMF略高于FT的排序，没有延续到Rain结束。** 这支持继续检查多次更新中的机制收益，尚不支持单seed的稳定排名或立即更换主基线。

| 方法 | Rain后CS−Fog后CS | Rain后Fog−Fog后Fog | Rain后Rain−Fog后Rain |
| --- | ---: | ---: | ---: |
| FT | +3.4141 | +0.8051 | +7.6861 |
| 原版GSMF | +0.5978 | −0.6732 | +6.2774 |
| LwF-DIL | −2.8190 | −3.9500 | +3.8316 |

FT更新Rain后，CS与Fog同时提高；原版GSMF的CS略回升、Fog下降，LwF的CS与Fog都下降。三组均提高Rain，不能把较低结果说成没有学到新域。FT对Fog的历史峰值遗忘为−0.8051pp，保留负号；不能把所有旧域变化都预设成单调遗忘。

| Rain后模型 | CS晴天 | Foggy .005 | Foggy .01 | Foggy .02 |
| --- | ---: | ---: | ---: | ---: |
| FT | 57.7056 | 55.5461 | 52.0375 | 44.8873 |
| 原版GSMF | 55.8056 | 54.3821 | 51.0934 | 44.8087 |
| LwF-DIL | 49.2420 | 47.6961 | 44.4264 | 38.0898 |

Rain后的原版GSMF三档合成雾相对自己的Fog后结果分别下降0.2935／0.6938／0.8534pp；FT各档略有提高。Source在这套CS同场景条件仍较高。三真实域均值与合成条件分别报告，不把六条件混成一个总均值，不把四个CS强度视为四个独立训练域。

## 4. 结果边界与下一阶段依据

第3项的真实三域链式首轮完成；严格未见强度泛化的受控合成训练支路未开展，Snow／Night、seed1/2、顺序变化及主要新机制也未开展。本次结果不自动批准下一项训练或确定论文最终训练边界。

多域后原版优势未保留，说明扩域提供了两域不能回答的信息。后续仍宜先落实较完整原版天气参考的数据与预算，再依据持续出现的适应／保持问题选一个主要机制；同时保留关键种子和顺序重复。不能由本次差值唯一归因于教师BN、特征KD或浅层冻结；LwF改变多个机制，且只试了默认配置。现有验证集已被多轮观察，不能称为完全未接触的最终测试。

训练单调计时约46.19分钟，新增评价约69.04分钟，后处理另计。部分UTC事件差与monotonic耗时不一致，MMEngine日志存在负time/data_time；原因未独立证明，资源只按已记录monotonic/perf_counter解释，不据本轮共享负载比较方法纯GPU速度。历史Source有已披露的resume限制，不因本轮未resume而消失。

## 5. 统计与方法检查（11/11）

结论等级为`CAUTION`：内部一致性通过，没有多种子置信区间或显著性检验，未编造p值。

| 检查项 | 判断 |
| --- | --- |
| Simpson悖论 | 已分真实域／合成条件报告；尚无完整逐城／场景分组推断，不由总均值排除局部反转 |
| 生态谬误 | 域级排名不代表每类、每帧或所有真实道路均同序 |
| 选择偏差 | 使用完整官方val与预选样例；跨库场景和拍摄条件仍限制外推 |
| Collider偏差 | 没有新增协变量控制分析，不作条件筛选后的因果推断 |
| 基率忽略 | GT直方图及像素数已核对；mIoU是类等权，真实域均值另作域等权 |
| 均值回归 | 两域小幅优势在三域反转，单次变化不等于稳定趋势，需重复 |
| 幸存者偏差 | 三组、42格全部报告，完成与退出码证据齐全，无缺格伪装 |
| 多重探索 | 42格与完整逐类表保存，选取差值仅作描述，不作显著性宣称 |
| 分析分叉 | 已确认方案、固定iter4000，无按val择优；长期反复观察val的限制保留 |
| 相关当因果 | 不能从排名反转定位唯一模块；GSMF与FT在Rain开始时已有不同Fog起点 |
| 反向因果 | 顺序与评价时间明确，不从最终错误反推唯一训练原因 |
