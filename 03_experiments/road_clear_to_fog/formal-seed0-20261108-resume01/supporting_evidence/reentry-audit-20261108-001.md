# 道路 DIL 接续核查

核查日期：2026-11-08（Asia/Shanghai）。本次未启动训练、未覆盖既有实验产物。

- 已读取根目录 AGENTS.md、REPRO.md 及本实验 PLAN/STATUS/RESULTS；未发现其他适用 AGENTS.md。
- 沙箱内 tmux socket 返回权限错误、进程列表仅见沙箱进程，因此另在宿主执行只读核查。宿主 tmux 默认 socket 不存在，真实进程表无训练 Python/tmux 进程，WSL nvidia-smi 计算进程查询为空。不存在需要保留或恢复的运行中道路任务。
- 主链路 `debug-real-20261107/status.json` 为 all/complete/exit0；会话 `session-debug-D1aLvF6R/exit-code.txt` 为0。events 中环境、三次训练、转换、六组完整评价和汇总均为 complete/exit0；训练日志完成 iter8 后验证，六组评价日志均到500/500或100/100。
- 本次实际 CPU 重载三个主模型 iter8：source/FT/GSMF 的 meta.iter 与全部 AdamW step 均为8，optimizer state 数分别361/356/317；PolyLR end=8、last_step=7、_global_step=8，最终LR=0。三个checkpoint的 SHA-256 均与各自A/B评价输入记录一致。它们是已完成的8步调试模型，不能当作正式长训练的中断点。
- 本次实际重载主源 iter4：meta.iter=4，全部AdamW step=4，PolyLR end=8、last_step=4、_global_step=4，LR=4.6646696566721594e-05。已有 `debug-real-resume-20261107/source/resume-verified-*.json` 记录恢复时optimizer/scheduler逐项精确一致；日志、completion及本次重载均确认已完成至iter8，最终AdamW step=8及调度器位置一致。续训能力验证已经结束，无需重复恢复。
- 旧 `debug-real-profile384-20261107/ft/iter_4.pth` 实际重载仍报缺失ZIP central directory，大小25,165,824字节；旧日志末尾截断，没有可靠的正常退出码。保留其 interrupted_by_host_reboot 状态，不从损坏文件恢复。
- 替代探测 `debug-real-profile384-reboot-20261107` 的 FT/GSMF 均有 exit0、completion PASS 和验证结束日志。本次实际重载两份iter8均有完整optimizer/scheduler，meta.iter与全部AdamW step均为8，PolyLR最终位置一致。这是独立重跑完成的资源探测，不是旧探测的无缝resume。
- 真实调试预算账本维持52/100，包括失败预留。本次未消耗训练步数。
- 当前代码fingerprint及数据audit SHA-256与ready.json完全一致；输出盘空闲约742GiB，超过建议正式输出预留20GiB。

当前已确认的工程及真实短运行工作均已完成。尚未确认启动正式长训练；既定待确认方案为seed0、crop512、batch2，源60000步、FT/GSMF各4000步，固定最终checkpoint，预计4–6小时或更长，输出预留20GiB。正式源阶段按PLAN从ImageNet初始化开始，不延长已结束的8步调试调度器。
