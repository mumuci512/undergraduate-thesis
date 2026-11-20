# 第2项seed0交接摘要

计算状态：两组各4000步、10个新增完整评价单元4200次逐图、独立矩阵/GT核验、五模型25条目汇总、逐类表/曲线/固定样例均完成。

| 模型 | 晴天 | Foggy .005 | Foggy .01 | Foggy .02 | ACDC-fog |
|---|---:|---:|---:|---:|---:|
| source | 71.5087 | 69.0118 | 65.2689 | 57.1493 | 49.6097 |
| ft | 54.2915 | 53.9792 | 51.0625 | 44.8280 | 62.3066 |
| gsmf | 55.2078 | 54.6756 | 51.7873 | 45.6621 | 63.0304 |
| lwf | 52.0610 | 51.1078 | 47.8919 | 41.5538 | 59.7877 |
| gsmf_teacher_bn | 52.2870 | 51.2670 | 48.0762 | 42.0735 | 58.7811 |

旧15单元为核对checkpoint、场景/标签、预处理、滑窗、分支、指标来源后的复用，本轮没有重跑旧模型全量推理；新10单元明确标记new_inference_this_run。

固定iter4000；无best选择、追加seed、超参搜索或天气。每组仅B_train400监督增量；同一Source SHA a66c958ee774d27566b901ad6570c0a3b83263e9d74389e1c2e025c6c2673d93。LwF输出蒸馏T2/0.5、全像素无T²；BN变体只调整教师BN源统计，教师Dropout/学生行为保留。

所有新增预测已独立重读原标签重算矩阵，行GT/列预测、ignore255、union0排除、仅有预测的类为0，GT直方图一致。两新组教师状态全部严格等于源值；评价前后所有参数和缓冲区不变，仅学生分支19通道推理。

原始新48份固定样例预测和六场景五模型同图对比已保留；没有增加按效果挑选的ACDC样例。完整19类结果见results/class-iou-wide.csv/JSON，强度绝对曲线及相对晴天下降曲线均有PNG/SVG/PDF。

单种子，真实/合成跨库差异，ACDC强度支持未知；不主张严格未见强度泛化、统计显著、LwF机制无效或BN因果解释。五条件不作简单平均。

恢复：保留完整optimizer/scheduler/iter；如未来中断恢复，不恢复RNG/采样游标，不承诺逐位一致。权重、数据、完整预测和环境均留远端。

源码恢复：以provenance记录的Git HEAD为基底，解开source/validated-training-source.tar.gz覆盖所列代码，并复用source/gsmf_rs_dil/__init__.py；preparation/validated-source.tar.gz另含准备版本完整源码/AGENTS/REPRO。source/git-diff.patch仅作审查，不作为新增文件的唯一恢复来源。

正式计算流水线exit-code.txt=0；最终交接校验见包外handoff-verification.json与外置.sha256。包内STATUS记录已完成的计算/核验和归档校阅状态；最终归档SHA及独立解包证明在包外handoff-verification.json，MANIFEST覆盖包内除自身外全部文件。
