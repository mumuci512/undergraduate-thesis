# 实际执行命令

均在 `/home/ysheng4/research/GSMF-RS-DIL` 执行；Python为 `/home/ysheng4/miniconda3/envs/GSMF_RS_DIL/bin/python`，GPU操作在沙箱外运行。OMP_NUM_THREADS=2、OPENBLAS_NUM_THREADS=2。没有启动正式脚本。

1. 读取AGENTS、REPRO、任务文件、旧PLAN/STATUS/RESULTS与必要源码；git status/diff/rev-parse，版本导入；/usr/lib/wsl/lib/nvidia-smi、df -h、free -h、tmux ls。
2. `python /tmp/step2_setup.py`：生成新stage配置和formal-resolved，建立新64步账本，重算三个固定最终权重SHA。脚本已另存preparation-scripts。
3. `python tools/road/run.py convert --source experiments/road_clear_to_fog/formal-seed0-20261108-resume01/source/iter_60000.pth --output experiments/road_lwf_bn/prepare-seed0-20261110-153000/conversion --stages ft gsmf lwf gsmf_teacher_bn`，日志conversion.log。
4. `python tools/road/verify_lwf_bn.py --output experiments/road_lwf_bn/prepare-seed0-20261110-153000`。attempt1在Runner数据集注册域未初始化时失败，读取训练数据/预留步骤之前，0次更新；修复register_all_modules后attempt2退出0、两次更新。第一次合成loss检查已经通过，证据保留。两份controlled-console日志保留。
5. `bash experiments/road_lwf_bn/prepare-seed0-20261110-153000/debug-chain.sh`，原GSMF4、LwF8、BN8、新两组resume各4；完整命令见该脚本及每训练目录invocation.json/resolved.py、resolved-resume*.py，debug-chain.exit=0。
6. `python /tmp/step2_manifests.py`：首次因比较相对路径与绝对路径而断言失败，未更改训练/无更新；改用绝对路径后通过旧配置回归、数据审计/清单hash和eval清单生成，脚本已归档。预检2/full500严格区分。
7. `bash experiments/road_lwf_bn/prepare-seed0-20261110-153000/eval-precheck.sh`：新增两模型×(四条件2场景 + ACDC固定4样本)，10单元共24张真实逐图评价；各单元日志、evaluation.json、预测及独立矩阵保留。
8. `python tools/road/verify_lwf_bn_saved.py --output experiments/road_lwf_bn/prepare-seed0-20261110-153000`：无优化更新；strict-reload-console.log，strict-reload-evidence.json。
9. `python experiments/road_fog_severity/eval-final-seed0-20261109-182100/scripts/verify_inputs.py <severity>/prepared-20261110 <severity>/data-audit-20261110`：全部配对数据与原审计文件SHA重核；severity-input-verification.log。
10. `bash experiments/road_lwf_bn/prepare-seed0-20261110-153000/tmux-probe.sh`：仅CUDA查询与tmux持久会话/退出码探针，不含训练；日志和exit=0保留。
11. `bash experiments/road_lwf_bn/prepare-seed0-20261110-153000/final-save-check.sh`：为最后增加的保存状态等于内存状态断言、新stage显式账本门禁，各2步真实B数据验证。总预算34/64，失败尝试0优化步，不重置旧账本。
12. `python tools/road/lwf_bn_formal.py --prepare experiments/road_lwf_bn/prepare-seed0-20261110-153000 --check-only`：只核查READY指纹、CUDA、磁盘和severity文件；不运行正式训练。preflight-check.log。

语法与差异检查：项目环境py_compile/compileall、bash -n新脚本、git diff --check；最终快照/证据汇总由preparation-scripts内finalize_prepare.py生成。只在确认本轮成果后更新REPRO。
