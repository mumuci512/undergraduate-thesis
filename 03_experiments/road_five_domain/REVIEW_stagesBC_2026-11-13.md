# 第5项阶段B／C接收核验与研究进展（2026-11-13）

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: validate
- Origin Date / Last Updated: 2026-11-13（Asia/Shanghai）
- Verification Status: ANALYZED。离线核对归档、文件清单、源码指纹、训练链记录、矩阵与三种子统计；未独立重跑模型。
- Model Reproduction Verdict: CANNOT_VERIFY（本机无完整权重、原始数据及全量预测）
- Version Label: road_five_domain_stagesBC_received_v1
- Overall Confidence: CAUTION。结果可作固定Source下的描述性比较，不构成显著性或普遍排序证明。

## 1. 实际完成范围与成果入口

用户于2026-11-13确认第5项阶段B和C已完成。两阶段授权记录也已随包收录；当前完成状态不再沿用阶段A快照中的“B暂缓、C未授权”。

| 阶段 | 已完成训练 | 新增评价 | 汇总范围 | 直接入口 |
| --- | --- | --- | --- | --- |
| B | FT／原版GSMF，seed 1／2，共同Source→Fog→Rain→Snow→Night；16次×4000步 | 104格，26,496次逐图 | 8格Source复用，共112格；与阶段A的seed 0合成三种子分析 | [接收目录](formal-B-plan-20261111-140000/)、[原始汇总](formal-B-plan-20261111-140000/formal-B-plan-20261111-140000/RESULTS.md)、[三种子表](formal-B-plan-20261111-140000/formal-B-plan-20261111-140000/results/three-seed-statistics.csv) |
| C | FT／原版GSMF，seed 0，共同Source→Night→Snow→Rain→Fog；8次×4000步 | 46格，10,248次逐图 | 8格Source复用，共54格；逐项对照主序seed 0 | [接收目录](formal-C-plan-20261111-140000/)、[原始汇总](formal-C-plan-20261111-140000/formal-C-plan-20261111-140000/RESULTS.md)、[顺序对照](formal-C-plan-20261111-140000/formal-C-plan-20261111-140000/results/explicit-order-comparison.json) |

两阶段合计24次新增训练、150格新增评价、36,744次逐图评价。B的Fog／Rain终点同时完成第2项FT／GSMF两域／三域关键重复，不另计为新增独立实验。Source未重训，seed 0主序沿用已有结果；LwF、教师BN变体未新增重复。

## 2. 接收核验与证据边界

本机3886项检查全部通过。脚本：[review_received_stage5BC.py](review_received_stage5BC.py)；逐项结果及复算统计：[REVIEW_stagesBC_2026-11-13_checks.json](REVIEW_stagesBC_2026-11-13_checks.json)。脚本仅使用标准库读取归档和记录，不执行包内代码。

| 归档 | 字节数 | SHA-256 |
| --- | ---: | --- |
| B | 35,436,328 | `3794ef1b81e7c1247b9717466710607ddfecd8393a1a5c571848e99dae336fc4` |
| C | 23,261,147 | `bfc3f86dcbb6bd458a19ce3fb194afb9f5c7058b3e3ca636e0f478be3b1adc37` |

核验覆盖：外置SHA、安全成员路径、实际解包后的文件集合与字节一致性、两份MANIFEST、训练源码指纹、授权与READY绑定、退出码、结果索引、166格19×19矩阵的逐类IoU／mIoU／有效像素复算、Source与阶段A的矩阵及检查点身份、24条训练父子SHA链、随机种子与新优化器配置，以及三种子阶段矩阵和均值／样本标准差。远程训练／协议独立检查记录为PASS；这些记录与本机实际模型重跑不同。

**打包前状态快照与最终回执。** 两包内STATUS及监督进程记录均冻结在“正在打包”，这是交接说明明确披露的快照，不作为当前仍在运行的证据。C的包外[completion.json](formal-C-plan-20261111-140000/completion.json)和[handoff-verification.json](formal-C-plan-20261111-140000/handoff-verification.json)均已收到。B自身接收目录只有归档和外置SHA，但C包的`reviewed-B`保留了B的[completion.json](formal-C-plan-20261111-140000/formal-C-plan-20261111-140000/reviewed-B/completion.json)及[handoff-verification.json](formal-C-plan-20261111-140000/formal-C-plan-20261111-140000/reviewed-B/handoff/handoff-verification.json)。两阶段最终回执均为complete／PASS，已与各自实际归档及训练／协议／结果检查SHA绑定；B完成时间为11月13日16:24，C为21:27（Asia/Shanghai）。B回执的“C not authorized”是B完成时的范围快照，后续C授权文件已收录。本次未登录远程机器。

**中断恢复。** B的GSMF seed 2 Snow从iter3000恢复模型、优化器和调度器后续训1000步。包内[恢复核对](formal-B-plan-20261111-140000/formal-B-plan-20261111-140000/execution/resume-audit-reconciliation.json)记录前缀loss保留、合计4000步及补做的100张iter3000验证；补做评价不计入104个最终格。RNG及采样游标未精确恢复，不能声称等价于不停机完整训练。

**方法与数据。** 每阶段仅当前域train，无旧图回放，固定iter4000，无val择优；FT全量CE，GSMF沿用教师参数冻结但训练态BN更新、学生stem／layer1参数冻结但BN更新，以及原输出／特征蒸馏。每域重新建立AdamW；评价仅当前学生、19类、原生分辨率512／341滑窗，无真实域ID路由、TTA或测试更新。细节以各包resolved配置、源码及协议检查为准。原有ACDC官方train／val共享视频目录、Night val仅两个视频、跨库采集差异等限制继续保留；未重新证明地理／邻帧独立。

## 3. 阶段B：三种子结果

下表为已见真实域等权mIoU（%），均值±样本标准差（ddof=1，n=3）。配对差值先对同seed计算GSMF−FT，再统计均值和标准差；不能用两个方法的SD相减。

| 更新阶段 | FT | GSMF | 配对GSMF−FT（pp） |
| --- | ---: | ---: | ---: |
| Fog后（两域） | 57.6664±0.7011 | 58.4273±1.4163 | +0.7608±0.8474 |
| Rain后（三域） | 58.7612±0.3579 | 57.1593±1.0286 | −1.6019±0.7916 |
| Snow后（四域） | 55.2542±1.1299 | 54.8882±0.7624 | −0.3660±0.4400 |
| Night后（五域最终） | 48.0393±0.7148 | 49.4435±0.7367 | +1.4042±0.2349 |

最终五域均值的逐seed配对差为+1.4124／+1.1653／+1.6350pp；Rain后三域均值在三个seed均低于FT。Fog后有一个seed的两域均值差为负，Snow后也不全同号。因此可确认“本轮主序三次增量链的最终差值均为正，且阶段行为不同”，不能将其扩展为每阶段、每域或任意顺序均占优。

最终各真实域的GSMF−FT三种子均值±SD：CS +0.6217±0.8813pp、Fog +2.3345±0.8493pp、Rain +2.0620±0.5664pp、Snow +2.1014±0.5135pp、Night −0.0983±0.3562pp。原版优势主要出现在Fog／Rain／Snow，当前新域Night没有对应提升。

旧域平均遗忘为FT 12.1176±0.8545pp、GSMF 9.2811±1.0354pp，配对差为−2.8364±0.9019pp。定义为每个旧域在**已学且早于最终阶段**的最高mIoU减最终值，四个旧域等权；不加入Night零项，保留负值。遗忘差与最终绝对分数应同时解释：GSMF在Rain／Snow刚学完时的分数也较低，不能把较小遗忘全部解释为更好的最终保持。

三档合成雾单列：Fog后GSMF−FT均值为+0.8022／+0.8095／+0.8240pp，Night后为+0.3485／+0.1564／+0.5158pp，不合并进五真实域均值。没有为B的Rain／Snow终点补插合成雾结果，也不主张严格未见强度泛化。

包内混淆追踪显示，FT与GSMF在三个seed的Fog后均有CS road→terrain／truck高于Source；Rain／Snow后road→building也在三个seed中同向增加。这支持将共同误判作为下一轮诊断线索，但尚未识别BN、冻结或蒸馏中的唯一原因，也不能据此定量分离数据集与训练设定的贡献。

## 4. 阶段C：顺序变化

主序为CS→Fog→Rain→Snow→Night，反序为CS→Night→Snow→Rain→Fog。均从相同Source进行四次增量更新；下表为最终部署学生的mIoU（%），只比较seed 0。

| 顺序／方法 | CS | Fog | Rain | Snow | Night | 五域等权均值 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 主序FT | 53.2786 | 57.0810 | 43.2148 | 43.7064 | 38.7919 | 47.2145 |
| 主序GSMF | 52.9036 | 59.3877 | 45.7989 | 46.3704 | 38.6739 | 48.6269 |
| 反序FT | 51.5266 | 64.9446 | 51.2663 | 52.4110 | 18.5916 | 47.7480 |
| 反序GSMF | 55.1093 | 65.7608 | 52.3436 | 53.2630 | 17.4147 | 48.7783 |

反序最终GSMF−FT均值为+1.0302pp，主序同seed为+1.4124pp。反序相对主序的总均值只变化FT +0.5335pp／GSMF +0.1514pp，但Night分别低20.2003／21.2593pp，Fog／Rain／Snow各高约6–9pp。总均值接近不能说明逐域表现对顺序稳健。

反序Night刚学完为FT 38.3751%、GSMF 36.3356%，最终分别降19.7835／18.9209pp。Night作为中间旧域时的保持是可检查的问题；主序把Night放在最后，不能单凭主序最终均值检验其长期保持。两顺序的历史暴露位置、最终新域和旧域集合不同，不能只比较两种“旧域平均遗忘”后归因于某个机制。

## 5. 统计解释、资源限制与项目衔接

11／11类统计误读已检查：

| 检查项 | 本次处理／剩余边界 |
| --- | --- |
| Simpson悖论 | 同时列逐域、逐阶段及总均值；总均值接近仍可能有Night大幅下降，不将其认定为已发生严格Simpson反转 |
| 生态谬误 | 以域等权均值描述模型，不外推单图或单像素都获益 |
| Berkson／选择偏差 | 官方验证划分及视频覆盖有限；未证明可代表所有道路条件 |
| 碰撞变量偏差 | 未作条件回归或额外筛选，不作因果识别 |
| 基率忽略 | mIoU按类等权；类频差异与稀有类波动不能仅用总体均值解释 |
| 均值回归 | 保留所有三个seed及固定终点，不按结果挑选最佳seed |
| 幸存者偏差 | 披露B中断、恢复及补做验证，不把恢复链描述为未中断实验 |
| 多重比较／到处寻找效应 | 本次无显著性检验，全部差值为描述性结果，无p值／显著性主张 |
| 分析路径自由度 | 固定原任务的顺序／预算／终点；机制追踪为探索性，未确认新方法 |
| 相关当因果 | 同向误判不证明BN或数据集是唯一原因 |
| 反向因果 | 顺序明确但机制未隔离，不从终点分数反推训练模块的因果作用 |

Source的三行是同一个模型复用，SD=0不表示Source训练稳定性已检验。n=3只覆盖固定Source下的增量随机性；C只有一个seed，CUDA非确定性及恢复限制继续保留。未独立重读远程全量预测或重训模型，复现结论为CANNOT_VERIFY，不能将离线记录检查标为模型VERIFIED。

训练入口墙钟：B有退出码命令合计222.01分钟，但不包含中断命令的原始3000步前缀时间；C合计124.07分钟。评价与其他处理另计。C记录了资源竞争及框架日志time／ETA异常，见[RESOURCE_NOTES](formal-C-plan-20261111-140000/formal-C-plan-20261111-140000/execution/RESOURCE_NOTES.md)；这些耗时不能当作独占GPU吞吐或纯推理延迟。本次未查询最新磁盘余量或远程文件存续情况。

本轮完成第5项既定A–C基础实验，并补齐第2项FT／GSMF关键重复。当前进入第4项的机制筛选与最小验证准备：综合Rain／Snow适应劣势、共同CS误判及反序Night保持问题，再选择一个主要假设；主要新模块尚未实现。原版GSMF继续作为已选基线与工程基座，未更换主基线，未自动确定论文最终训练边界、强度泛化协议或新增训练任务。最新全局进度以[PROJECT_STATE](../../00_management/PROJECT_STATE.md)为准，执行清单见[计划§7、§11](../NEXT_STEPS_AND_BASELINE_REVIEW_2026-11-09.md)。
