# 本轮资源计时说明

正式实验入口墙钟由 time.monotonic() 记录，RoadAuditHook 训练/验证耗时用 time.perf_counter()。MMEngine IterTimerHook 的日志 time/data_time/ETA 使用可跳变的 time.time()，本轮观察到负值；安装源码及原始负值行见 timing-observation.json 和 installed-mmengine-iter-timer-source.txt。不要用框架日志 ETA 代替实际完成时间。

2026-11-13 约19:55起，GSMF Snow后 Cityscapes 评价从约0.5秒/张明显减速，日志有每张约4–6秒的片段。约20:02的只读采样显示GPU利用率97%、SM 1935MHz、显存6115MiB、52°C、约290W；Windows GPU 3D计数器中Dungeons-WinGDK-Shipping进程有64%的瞬时利用率，vmwp约5%。这是共时观察，未做独立因果对照，不能将全部延迟定量归因于该进程。WSL NVML的compute-app列表无法提供有效进程归属，补用宿主只读计数器确认。证据见 resource-contention-observation.json 与 resource-slowdown-gpu-20261113-1959.txt。

保留全部宿主进程，未调整系统、驱动、进程优先级、实验配置或评价协议。训练已完成，继续原计划的评价与独立核验，实际入口耗时包含资源竞争、载入、I/O、预测保存和核验；不报告为纯GPU延迟或独占吞吐。早先结束时间估算取决于GPU可用性，不是完成证据。最终完成以completion.json、独立核验及包外handoff-verification.json为准。
