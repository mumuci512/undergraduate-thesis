# 道路seed0正式运行

2026-11-08用户确认并启动。仅源60000、FT4000、GSMF4000步，seed0、batch2、crop512；同一正式源最终checkpoint，单GPU顺序训练与评价。正式模型从ImageNet初始化开始；未延长调试模型调度器。实际运行argv、Git状态/diff、训练代码快照及hash见provenance.json和各阶段invocation.json。

训练会话：`road-formal-20261108-001353-5635`，流水线PID5645，启动核查源训练PID5741。

监测会话：`road-monitor-formal-seed0-20261108-001`，启动核查监测PID5833。每20秒检查事件/进程并更新STATUS及REPRO；六组最终评价与流水线exit0后，独立重读1800张预测及原始标签，校验六个矩阵、全GT直方图、checkpoint哈希和optimizer/scheduler/迭代位置，发布正式RESULTS。失败保留日志并退出，不重试训练、不追加实验。

监测代码快照：本目录formal_control.py；实际执行仓库实验根目录的同名文件（authorization.json记录hash，运行期间不要修改）。监测预验证：debug-finalizer-check-20261108-001.json。启动证据：startup-verified.json。启动前全部7950数据文件与清单哈希通过，GPU无其他计算进程，输出盘空闲约742GiB。

从仓库根目录查看：

```bash
R=experiments/road_clear_to_fog/formal-seed0-20261108-001
bash tools/road/status.sh "$R"
bash tools/road/status.sh experiments/road_clear_to_fog/session-formal-t2rn7qx2
tail -f "$R/train_source-console.log"
cat "$R/monitor-heartbeat.json"
tail -f "$R/monitor-console.log"
tmux list-sessions
```

后续阶段日志为train_ft-console.log、train_gsmf-console.log、eval_<stage>_<A/B>-console.log；每步训练loss由现有RoadAuditHook检查有限。events.jsonl保留每阶段真实退出码，session-formal-t2rn7qx2/exit-code.txt仅在流水线退出后出现。监测真实退出码分别保存为monitor-exit-code.txt和monitor-shell-exit-code.txt；训练complete不等同于独立核验complete，最终以final-independent-verification.json的PASS和顶层STATUS为准。

仅在训练已中断、确认无对应真实进程，且已重载核验最新完整checkpoint的optimizer、param_schedulers、meta.iter之后恢复该阶段：

```bash
R=experiments/road_clear_to_fog/formal-seed0-20261108-001
# 启动初期尚无checkpoint；首次源保存点为iter_10000。
# last_checkpoint指向的文件也必须确认可读，不能仅信路径存在。
bash tools/road/resume.sh source "$R/source" "$(cat "$R/source/last_checkpoint")"
# B阶段同理，stage与目录同时换成ft或gsmf。
```

resume恢复模型、优化器、调度器和迭代位置；已有hook会在更新前逐项比较恢复状态。仅加载权重不能称为无缝续训。遇到损坏检查点或不匹配状态不执行此命令；不可覆盖失败记录，修复后重跑须新运行标识。现有resume脚本只恢复指定训练阶段，不会自动重新运行原流水线或后续评价；恢复后需要根据已完成events按原协议接续余下转换/评价/训练，使用新的评价目录和独立会话记录。主机停机会同时终止训练和监测，不存在停机后的自动恢复承诺。

全部完成后：正式比较矩阵、19类IoU、旧域下降、新域增量、等权均值和资源表见本目录及上级RESULTS.md；精确六个19×19矩阵见final-independent-verification.json，原始预测与评价证据见各eval目录。单种子及跨数据集限制随结果保留，不根据val选择checkpoint或追加预算。
