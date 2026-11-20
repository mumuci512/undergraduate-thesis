# 第3项唯一正式方案：准备通过／正式未启动

准备目录：`/home/ysheng4/research/GSMF-RS-DIL/experiments/road_clear_fog_rain/prepare-seed0-20261110-180543`。
唯一拟正式目录：`/home/ysheng4/research/GSMF-RS-DIL/experiments/road_clear_fog_rain/formal-seed0-plan-20261110-180543`（尚未创建）。

已完成 Rain 数据审计、三份严格初始化、真实短训、同运行resume、六条件小样本评价及旧20格复用核查。没有授权记录，未启动4000步训练或22格完整评价。

## 父子链及初始化

| 方法 | Fog父SHA-256 | Rain初始化SHA-256 | 状态张量 |
|---|---|---|---:|
| ft | `99914df527d8506c33178ef6ea1caf7f0ed1d07369858e37275205d60a57d516` | `08c88c478e77f3d973ee190cd9a70cf744d6b3f2532f586c3bc8fd1e62c4328d` | 698 |
| gsmf | `fc227c57dc3e47a134ef51b282964654a0210f3c06f00bd0d3e81b706850b24a` | `3fa5208149044b2a1838aedeca0d9081b0468d04910fb957fede0e0db98d7c5f` | 1396 |
| lwf | `854d83357a912713a27cf27283b024f3e7fd7dab47043434d312b136ec9b6843` | `a4c48fd47ce7db2a01084e386e2d1d0026228265f4e56b30f8c5da1a8da0d96b` | 1396 |

共同Source SHA：`a66c958ee774d27566b901ad6570c0a3b83263e9d74389e1c2e025c6c2673d93`。三方法分别继承自己的Fog学生，旧训练来源及各自Source初始化证据见ancestor-provenance.json；不把当前HEAD代作旧训练版本。FT完整继承698键；GSMF/LwF只用backbone_1/decode_head_1的698键，克隆为新的教师与学生1396键。丢弃Fog内旧教师；参数及全部持久BN缓冲逐值一致，独立存储。转换输入不含父optimizer、scheduler或iter；键映射、shape、哈希和有意排除项在conversion/*/conversion.json。真实512裁剪eval输出最大误差全部0，重载复核通过。正式使用未经过短训优化的初始化。

## 数据与协议

Rain已独立提取到data/acdc_rain_step3_20261110-180543；归档SHA核对后选取train/val RGB、trainIds及用于逐像素交叉核对的labelIds，共1500成员，CRC/长度/逐文件SHA通过，约0.97GiB。C_train400、C_val100全部解码、三通道RGB/单通道整数标签及同尺寸检查通过，两种编码映射后全像素一致。19类顺序同原协议，trainIds原样使用、ignore255。A2975/500、B400/100原清单字节不变且实际图像/标签SHA重核。C与全A/B清单、C train/val之间无帧ID、RGB字节或解码像素哈希重复；A/B解码哈希来自原审计，实际文件字节已重核，未重新解码全部A/B。

Rain官方train/val共享GOPR0400、GOPR0402、GP010400、GP020402、GP030400五个视频目录；继承官方划分，不自动删样本或重分，不声称地理/邻近帧独立。C优化只读C_train，周期验证只读C_val；A/B及固定Foggy仅供评价，无回放、normal参考、test或其他天气训练。Rain固定6样例于推理前seed0选定，见rain-fixed-samples.json；Cityscapes沿用severity既有6场景及选择证据。

任务为边界已知、固定19类、完整监督的三域工程/现象验证；域ID用于数据统计，部署所有天气均仅当前学生，无天气oracle、TTA或测试BN更新。此原型不自动确定最终论文边界协议。

## 方法及唯一训练预算

FT／原版GSMF／LwF-DIL各seed0，Rain4000优化步，batch2、crop512、FP32，AdamW(lr1e-5,betas=.9/.999,wd=.001)，PolyLR(power.9,end4000,eta_min0)。每1000步C_val验证及保存，保留1000/2000/3000/4000，主结果固定iter4000，不择优。约20轮图像曝光，不按短训/val临时加减任一方法预算。RandomResize((2048,1024),ratio.5–2)、RandomCrop512(cat_max_ratio.75)、flip.5、PhotoMetricDistortion；ImageNet均值方差、BGR增强后转RGB、pad0/seg255、worker2、InfiniteSampler，实际seed0/deterministic=True/cudnn_benchmark=False。正式配置见三份*-formal-resolved.py，较各自已完成Fog配置的实质变化仅父学生快照及B→C清单。

FT全参数CE更新，无教师/辅助头。GSMF保留教师参数冻结但训练态BN更新及Dropout、学生stem/layer1参数冻结但BN更新；教师从自己的Fog学生开始，不使用teacher_bn_source_stats变体。LwF教师eval/no_grad，参数和全部缓冲固定于自己的Fog学生快照，学生全量更新，无特征KD。

CE权重1，bilinear至标签尺寸，ignore255，avg_non_ignore=False（均值分母包含ignore位置）。两蒸馏法输出Hin为-0.5*mean_NHW(sum_C softmax(z_teacher/2)*log_softmax(z_student/2))；原生stride4/19通道logit，全像素含ignore/padding，无显式T²。GSMF另有KL(T1/weight1,idx[1,2,3])：每层按样本C/H/W均值、层均值，MMEngine再按batch归约；实现中KL的T²在T1为1。LwF无此特征项，是固定19类默认适配对照，未经超参搜索。冻结梯度不等于冻结BN状态。

## 真实准备验证

三组各同一运行iter0→4保存停止→resume至8，共24个成功真实优化步；首次FT保存兼容性失败的4步另计，总28/64，未重置账本。首次失败因CheckpointHook同时传入meta，与MMEngine内部meta冲突，修复为before_save_checkpoint合并元信息。失败目录、日志及保守预留均保留。新优化器状态为空、seed0；resume optimizer/scheduler/iter逐值相等；所有loss及逐步梯度有限，冻结/更新参数和BN按策略变化，严格保存重载及19通道通过。

三方法×六条件真实小样本18格：CS和各Foggy2张，Fog4张、Rain4张，每方法16张、总48张。实际评价入口与独立预测重读/混淆矩阵/GT直方图/尺寸/ID集合一致，推理状态不变，仅学生分支。小样本mIoU不作为正式方法效果。无优化转换/推理检查耗时在各exit JSON及日志单列。初始验证一次语法错误、清单准备两次路径/旧简版记录字段不匹配均保留失败日志，均为0优化步。

## 42格评价及指标

evaluation-plan.json逐格列明20 reused＋22 new。唯一checkpoint共7个：共同Source，三方法Fog后，三方法Rain后；各CS500、Foggy .005/.01/.02各500、Fog100、Rain100，共42格。旧20格=severity12＋旧两域ACDC3＋LwF五格，已按checkpoint、实际完整ID/图像标签SHA、映射、预处理、分支、19×19矩阵和GT直方图核对，保留原证据路径/SHA；历史debug命名或full标记不用于推断实际样本数。

新增22格：Source/FT-Fog/GSMF-Fog/LwF-Fog各Rain100，共4格400次；FT/GSMF/LwF的Rain后各六条件，共18格6600次；合计7000次。四个未来Rain提前分数不计入当时已见域均值。

原生分辨率，ImageNet预处理，512滑窗/stride341，无TTA；四个CS条件同500场景/GT。每格累计GT行/预测列、ignore255的19×19矩阵，union0排除并写null，GT缺失但有预测为0，不平均逐图mIoU。新增22格独立重读保存PNG与原标签，核对全量ID、尺寸、GT直方图和矩阵；旧格复核保存矩阵与出处。

rain_results.py生成42格及每方法Source/Fog后/Rain后×CS/Fog/Rain矩阵，Source行共享。已见均值分别只含A、A/B、A/B/C，最终三真实域均值与合成条件分开，不算六条件混合均值。after-before报告Rain后相对各自Fog后的CS/Fog差、CS相对Source累积差、Rain适应增益、三档合成变化。可报旧域遗忘=max(已学且早于最终阶段的分数)-最终，CS参照Source/Fog后、Fog只参照Fog后，保留负值，不加Rain零项、不报FWT。新增固定CS原始预测72份，另存固定Rain样例，后续作对齐图。

## 资源及执行入口

| 方法 | 同步优化秒/步 | 峰值allocated MiB | 短训checkpoint MiB |
|---|---:|---:|---:|
| ft | 0.1717 | 2435.4 | 548.2 |
| gsmf | 0.1852 | 2279.4 | 729.5 |
| lwf | 0.2406 | 2622.7 | 731.4 |

按本轮观测估算12000步纯计算约39.8分钟，7000逐图评价保守约126.6分钟，12次周期C_val约14.7分钟；再加模型加载/保存、独立重读/报告余量30分钟和1.3安全系数，建议预留3–5小时或更长。小清单、诊断/热身、系统负载影响明显，不承诺历史或短训速度。FT-clear小样本曾与无优化等价复核短暂重叠，已排除该点作速率上界。

12份正式checkpoint估算7.85GiB；7000张单通道uint8预测未压缩上界约13.65GiB，PNG依压缩率变化；样例、日志、源码/图表/轻量包另计，正式新增预留30GiB，准备文件另存不清理。当前WSL约675.6GiB、宿主C约98.1GiB可用，启动前复核两处均≥30GiB，保存GPU进程快照，不终止其他任务。

仅在用户提示词二或明确确认这套方案后，将授权原文、确认时间及本READY真实SHA写入authorization.json：`{"prompt_two_confirmed":true,"ready_sha256":"<sha256>","user_message":"<原文>","confirmed_at":"...+08:00"}`。本轮未创建授权文件。

```bash
# 正式前只读核查（不启动训练）
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 /home/ysheng4/miniconda3/envs/GSMF_RS_DIL/bin/python tools/road/rain_formal.py --prepare /home/ysheng4/research/GSMF-RS-DIL/experiments/road_clear_fog_rain/prepare-seed0-20261110-180543 --check-only
# 唯一正式启动命令（用户确认后）
bash tools/road/rain_start.sh /home/ysheng4/research/GSMF-RS-DIL/experiments/road_clear_fog_rain/prepare-seed0-20261110-180543 --confirmed-prompt-two
# 状态查询
bash tools/road/rain_status.sh /home/ysheng4/research/GSMF-RS-DIL/experiments/road_clear_fog_rain/formal-seed0-plan-20261110-180543
# 已授权同一运行中断后，先核对实际进程；仅续未完成训练/评价
bash tools/road/rain_resume.sh /home/ysheng4/research/GSMF-RS-DIL/experiments/road_clear_fog_rain/prepare-seed0-20261110-180543 --confirmed-prompt-two
# 22格完成后独立复核与42格汇总
/home/ysheng4/miniconda3/envs/GSMF_RS_DIL/bin/python tools/road/rain_results.py --prepare /home/ysheng4/research/GSMF-RS-DIL/experiments/road_clear_fog_rain/prepare-seed0-20261110-180543 --run /home/ysheng4/research/GSMF-RS-DIL/experiments/road_clear_fog_rain/formal-seed0-plan-20261110-180543
```

入口复核代码/完整源码快照、实际环境版本、数据/父权重/初始化/配置指纹，tmux持久顺序执行三组训练和22格评价，驱动加文件锁，记录PID、命令、单步退出码/events/status；失败停止依赖阶段，无自动重试。训练/评价完成只标train_eval_complete_pending_summary，随后独立核验、图表及轻量包才可标整个正式任务complete。未来最终包唯一名为formal-seed0-plan-20261110-180543-light.tar.gz，MANIFEST逐文件SHA与包外SHA，安全成员检查并新目录实际解包；权重/数据/全量预测留远端。

resume只接受同一方法、domain C、同一个绝对work_dir的完整优化器/调度器/iter checkpoint，拒绝Fog优化器和其他Rain运行。选择最新完整保存点，目标仍总4000；无法精确恢复RNG/数据游标，不能声称与不停机逐位一致。未完成评价用新恢复目录，完成单元按证据跳过，不覆盖checkpoint/预测。主机/WSL停机仍会中断tmux；本轮只验证持久启动/退出码探针，不承诺未建立的持续监控。

## 边界与待执行项

本轮准备完成；正式三组4000步、22格完整评价、最终42格汇总/图表和轻量包均未执行。未来完整数据路径的最终汇总只有在真实正式产物上才能验证；本轮独立重读函数已在48张真实小样本预测上验证。仅seed0，不代表稳定显著；跨库差异不能全部归因天气，不声称严格未见强度泛化；不扩Snow/Night、其他种子、搜索、模块或架构。没有下载、环境升级、Git提交/推送、数据删除或checkpoint覆盖。

补充证据：`validation-reentry.json`为三组实际C验证循环→model.train()恢复策略检查（另12张验证输入、0优化）；`nonoptimization-times.json`单列转换/等价检查的文件系统时间区间下界及评价的单调计时，不将近似区间当精确perf_counter。seed0已落实，但不声称跨方法增强RNG逐位配对。
