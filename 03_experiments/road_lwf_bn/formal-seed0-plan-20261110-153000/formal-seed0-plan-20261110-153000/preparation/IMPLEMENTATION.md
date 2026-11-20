# 实施说明与变更归属

本轮不修改 `mmseg/` 作者原文件、已有遥感配置、已有数据/权重/训练和severity结果；不升级环境、不下载、不Git提交/推送。保留原REPRO改动、任务文件及handoff_exports。

- `road_dil/models.py`：新增局部RoadDIL。fixed_eval路径教师no_grad + detach，教师所有模块eval；BN诊断路径调用原loss，train()仅重设教师BN为eval。重写train()保证MMEngine周期验证、递归train和resume加载后仍生效，不使用全局monkey patch。freeze_before_training将原有参数冻结语义提前，便于首步梯度审计；原GSMF的BN缓冲更新行为仍保留。
- `road_dil/config.py`、`configs/road/lwf_acdc_fog.py`、`configs/road/gsmf_teacher_bn_acdc_fog.py`：新增明确stage。BN组与原版配置diff仅model.type和teacher_policy。LwF关闭浅层冻结和feature KL，其余公共分割器结构不变。原stage静态配置与make_config逐项相等。
- `road_dil/checkpoints.py`：convert可选stages，默认仍ft/gsmf；新组逐键严格复制同一Source的无辅助头状态。build允许新stage。新的转换报告记录每键来源/shape/hash与exact_value_copy_verified。
- `road_dil/hooks.py`：按实际冻结开关检查浅层冻结/更新，保留原版冻结断言；新组额外断言教师BN缓冲不变；每个训练迭代核查教师/学生training标志。debug每一步梯度/损失有限检查保留，resume前optimizer/scheduler/iter精确核验保留。
- `tools/road/run.py`：新stage、独立--budget-ledger，新stage debug必须显式账本；默认旧账本不变。新stage评价用自己的配置严格加载；双分支全部检查仅学生调用。conv_seg输出19通道逐次断言，保存实际shape；评价前后所有状态hash不变，重读保存预测和原GT复算矩阵。增加保存checkpoint与结束内存模型逐键hash相等断言，随后strict reload。
- `road_dil/budget.py`：只改超限错误文字，独立路径及锁定/失败预留语义不变。
- `tools/road/verify_lwf_bn.py`：合成手算/解析梯度/ignore255检查，加真实B同一增强输入的原版与BN变体受控各1次优化。训练参数集合/初值一致，标志仅教师BN变化，教师无梯度，原版BN更新而变体不更新。验证模式返回也覆盖。另核对LwF学生与FT初始化真实输入logits逐值相等。
- `tools/road/verify_lwf_bn_saved.py`：真实短训与resume checkpoint全部teacher状态逐键等于Source；严格保存/重载合成固定输入logits逐值相等；重载后train策略核验。合成forward与真实训练证据分开标注。
- `tools/road/lwf_bn_formal.py`、`lwf_bn_start.sh`、`lwf_bn_status.sh`：正式门禁、tmux顺序入口、日志/阶段退出码/事件/查看入口。正式运行目录必须新建，失败停止；不自动重试，不处理未经确认的重复。授权文件必须匹配READY的SHA；本轮没有生成授权文件。完整恢复直接使用经实测的run.py --resume。

方法改动：LwF式对照；GSMF教师BN来源统计诊断。必要基础设施改动：新stage/严格转换/审计/评价/独立账本/执行门禁。没有宣称这些是作者原始道路实验。

所有train进程在建立优化器和进入first-step审计前已经落实requires_grad；原版旧教师和学生浅层既有冻结不改变更新目标。BN诊断从Source重新开始，没有从原GSMF最终权重继续。

`before-validation.patch`是首次实现后快照；最终完整tracked差异见`git-diff.patch`，新增未跟踪源码包含在`validated-source.tar.gz`，不能只依赖Git恢复。config-diff.json为实际配置递归diff。
