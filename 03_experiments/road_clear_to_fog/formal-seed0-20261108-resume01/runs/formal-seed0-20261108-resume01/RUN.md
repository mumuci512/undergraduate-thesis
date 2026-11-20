# 道路seed0正式恢复运行

2026-11-08在用户清理磁盘并要求继续后启动。恢复前复核C盘物理余量约187.8GiB，全部7950个数据文件与清单hash一致，训练代码fingerprint未变，无其他GPU计算任务。此前10:40的机器检查内核崩溃根因仍未确认，未将释放磁盘空间视作硬件故障已修复；再次失败时不自动重试。

原运行：`formal-seed0-20261108-001`。本次从该运行的`source/iter_40000.pth`恢复模型、AdamW、PolyLR和迭代计数，源目标保持60000；随后源最终模型A/B评价、严格转换、FT4000及A/B评价、GSMF4000及A/B评价、汇总。FT/GSMF从同一个正式源最终checkpoint初始化，单GPU顺序执行。完整恢复前核查见recovery-state-before-run.json；运行内恢复后精确比较见source/resume-verified-*.json。原checkpoint未保存RNG和数据迭代器状态，不能保证与不中断训练逐位一致。

训练会话：`road-recovery-20261108-105307-1597`；会话记录：`experiments/road_clear_to_fog/session-recovery-xB79mCPB`。

监测会话：`road-monitor-recovery-20261108-01`。实际执行的监测命令见monitor-command.sh；每20秒记录状态与真实退出码，更新STATUS/REPRO。全部训练及六组评价exit0后，独立重读1800张最终预测和原始标签，核对六个19×19矩阵、GT直方图、checkpoint hash及最终optimizer/scheduler位置，再发布RESULTS。旧运行及损坏文件均保留；没有追加种子、天气、算法或Git提交/推送。

从仓库根目录查看：

```bash
R=experiments/road_clear_to_fog/formal-seed0-20261108-resume01
bash tools/road/status.sh "$R"
bash tools/road/status.sh experiments/road_clear_to_fog/session-recovery-xB79mCPB
tail -f "$R/train_source-console.log"
cat "$R/monitor-heartbeat.json"
tail -f "$R/monitor-console.log"
tmux list-sessions
```

源恢复日志链接到source-session/console.log，源阶段真实退出码为source-session/exit-code.txt；总流水线真实退出码写到session-recovery-xB79mCPB/exit-code.txt；监测真实退出码写到monitor-exit-code.txt及monitor-shell-exit-code.txt。这些文件在对应进程退出后才出现，不将缺失退出码解释为成功。

再次中断时，先核对宿主进程/会话以及最新checkpoint是否可读、optimizer/scheduler/meta.iter是否一致，然后以新恢复标识继续；不要重复启动存活训练。恢复入口示例（仅在确认中断且对应文件验证通过后使用）：

```bash
bash tools/road/resume.sh source "$R/source" "$R/source/iter_50000.pth"
```

本恢复目录的首个计划保存点为iter50000，启动初期尚不存在；原运行的同名文件损坏，禁止使用。resume.sh只恢复指定训练阶段，余下转换/评价/训练须根据事件日志接续，不能从头覆盖原流水线结果。

源恢复段耗时与原有效段耗时分别记录；最终resource-accounting.json还列出原失败尝试中丢失的10000步及其实际消耗。源稳态耗时/显存取恢复段，最终指标固定最终checkpoint，不据val选预算。正式完整结果以final-independent-verification.json的PASS为准；主机/WSL停机会同时结束训练和监测。
