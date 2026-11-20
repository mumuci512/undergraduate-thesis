# 本轮实际入口与命令索引

工作目录始终为 `/home/ysheng4/research/GSMF-RS-DIL`，解释器 `/home/ysheng4/miniconda3/envs/GSMF_RS_DIL/bin/python`。GPU操作使用可访问WSL设备的执行权限；不安装驱动/依赖。所有训练/eval子命令和真实退出码/monotonic耗时在本目录`*-command.sh`和`*-exit.json`，实际resolved/invocation及MMEngine日志在各工作目录。

环境变量：`OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2`；driver运行另用`PYTHONUNBUFFERED=1`。准备目录下记为`P=experiments/road_clear_fog_rain/prepare-seed0-20261110-180543`。

实际执行顺序及证据：

1. `python tools/road/prepare_rain_data.py --prepare "$P"` → `data-preparation.log`、data/audit.json及独立提取provenance。
2. Python内联循环重算四权重SHA、调用`convert_incremental(PARENTS[m][0], P/'conversion'/m, m, PARENTS[m][1])`（m依ft/gsmf/lwf），并以`write_json`创建limit64/reserved0账本；实际转换入口源码和逐键报告保存，`conversions.log`、fixed-checkpoints.json。未调用旧Source转换。
3. `python tools/road/verify_rain_chain.py --prepare "$P"` → 初次无优化语法错误日志、修复后`initial-chain-verification-attempt2.log/json`。
4. `python tools/road/prepare_rain_protocol.py --prepare "$P"` → 两次无优化失败（旧precheck文件名及旧简版清单缺hash字段）；失败清单目录保留为eval-manifests-attempt1/2。采用原severity指纹丰富清单后attempt3通过，protocol-preparation-attempt3.log、compatibility.json/evaluation-plan.json。
5. `python tools/road/rain_smoke.py --prepare "$P"` → 第一次FT实际4步后保存接口冲突，failed-attempt1-*及short/ft-failed-save-attempt1保留，账本不返还4步。兼容修复后重启同一准备driver，新独立short/ft目录；成功三组各4+4步。每次实际命令见short-*/resume-*-command.sh，完成short-runs-completion.json，完整账本28/64。
6. `python tools/road/rain_eval_smoke.py --prepare "$P"` → eval-smoke-driver.log；三组×六条件18格48张小固定样本、独立重读一致。每格evaluation、standalone-independent-check和保存预测保留。
7. `python tools/road/verify_rain_chain.py --prepare "$P" --trained` → trained-chain-verification.log/json；无优化。曾与FT-clear小样本短暂同时运行；资源估算排除该评价计时点。
8. `python tools/road/check_rain_contracts.py --prepare "$P"` → contract-checks.log/json，真实400/100清单解析和负向拒绝检查；夹具仅用于拒绝错误域，无优化。
9. Python内联核对三Fog运行invocation所指初始化SHA、conversion共同Source SHA及历史provenance，保存ancestor-provenance.json。
10. `python tools/road/preflight.py --output "$P/environment.json"` → environment.log/json；仅CUDA/roi_align内核与系统快照。
11. `tmux new-session -d -s road-rain-probe-20261110-180543 'bash /home/ysheng4/research/GSMF-RS-DIL/experiments/road_clear_fog_rain/prepare-seed0-20261110-180543/tmux-probe.sh'` → 仅CUDA查询，tmux-probe.exit=0。
12. `python tools/road/verify_rain_validation.py --prepare "$P"` → validation-reentry.log/json；三组真实C验证后train模式恢复，无优化。
13. `python tools/road/finalize_rain_preparation.py --prepare "$P"` → 完成唯一方案、资源、源码安全解包/哈希和READY。随后`python tools/road/rain_formal.py --prepare "$P" --check-only`做只读最终预检；没有正式训练授权文件。

无优化检查的阶段wall time可从对应驱动exit JSON/报告获得；初始转换和严格重载还保存检查报告。真实训练步数和失败保守预留只看本轮debug-budget.json；不使用旧账本。
