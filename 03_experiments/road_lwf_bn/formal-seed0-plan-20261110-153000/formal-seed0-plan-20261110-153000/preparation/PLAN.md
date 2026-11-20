# 第2项唯一拟正式方案（等待提示词二）

准备目录：`experiments/road_lwf_bn/prepare-seed0-20261110-153000`。
拟正式输出（尚不存在）：`experiments/road_lwf_bn/formal-seed0-plan-20261110-153000`。
本文件为本轮唯一方案；本轮仅准备和真实数据短测，**未授权、未启动任何4000步训练或全量新增评价**。

## 两组方法与依据

A=`lwf`，准确称为 **LwF-DIL：固定19类单头分割适配**，不是原始分类多任务实验逐项复现。复用作者 `DIL_EncoderDecoder` 的部署/训练头接口、`DIL_BaseDecodeHead.loss_by_feat`、`DIL_HinLoss`。道路局部 `RoadDIL` 子类明确教师 no_grad/detach、eval 与递归 train 恢复策略。学生部署网络的参数键、图/注意力模块及初始化 logits 与 FT 等价；教师和学生均从去掉辅助头的同一 Source 初始化。教师全参数及全部缓冲固定，教师 Dropout 关闭；学生全部47,832,297个参数可训练，BN与Dropout保持FT式训练行为，取消GSMF学生stem/layer1冻结。

LwF损失仅 CE(weight=1) + 输出soft CE(T=2, weight=0.5)，不含特征KL/其他特征蒸馏，无回放、伪标签、置信度筛选、类别加权。soft CE为 `-0.5*mean_N,H,W(sum_c softmax(z_teacher/2)*log_softmax(z_student/2))`；不乘T²。512裁剪下作用于原生128×128、19通道logits，学生/教师同尺度，无额外插值；按现有函数在所有logit像素计算，**不按GT=255屏蔽，也包含padding对应位置**。loss的reduction参数没有改变这里实际固定mean的实现。相同logits时soft CE为正的教师熵常数，梯度为零。CE先bilinear插值至512×512，align_corners=False，ignore255产生零损失/梯度；原版avg_non_ignore=False保留（均值分母包含忽略位置）。这是明确的首轮默认，不搜索超参，单次低结果不能判定LwF机制无效。

B=`gsmf_teacher_bn`，准确策略名 **teacher_bn_source_stats**。原版GSMF全部损失/系数保留：CE=1，输出Hin T2/0.5，多层KL T1/1、idx=[1,2,3]。仅教师backbone/decode_head的BN采用初始化Source running_mean/running_var，不更新这些缓冲或num_batches_tracked；BN仿射参数继续冻结。教师其他模块（含Dropout）仍train；不把整个教师eval，不设置全模型norm_eval。学生stem/layer1冻结、其余47,587,721个参数可训练、所有学生BN训练行为均与原版一致。这个变化同时影响教师BN前向所用统计与统计更新；不是“只冻结计数”。本组是机制诊断，不预设BN是主要遗忘原因，不包装成新算法。

两组推理统一只调用backbone_1/decode_head_1，不依据真实天气路由。原版遥感代码/损失文件未修改。原道路stage默认配置逐项相等的回归检查已通过；原版运行入口提前落实原有requires_grad冻结，避免首步才冻结导致审计漏记，未更改其BN/Dropout行为。新策略默认不作用于旧stage。

## 固定初始化与数据

复用 `experiments/road_clear_to_fog/formal-seed0-20261108-resume01/source/iter_60000.pth`。
SHA-256：`a66c958ee774d27566b901ad6570c0a3b83263e9d74389e1c2e025c6c2673d93`。
FT和原GSMF最终SHA亦已重算，与任务文件一致，见fixed-checkpoints.json。新增两组都重新从此Source严格转换，不从已训FT/GSMF继续、不重训Source；教师/学生逐键键集、形状和值复制证据见conversion/conversion.json。正式直接加载本目录已严格验证的各自初始化文件，文件SHA另在READY.json固定。

训练清单原样复用 `experiments/road_clear_to_fog/data/B_train.jsonl`，ACDC fog官方train400；不读取Cityscapes训练图、Foggy图、其他天气、正常参考图。原清单A_train/A_val/B_train/B_val数量2975/500/400/100。0..18类，ignore255；Cityscapes labelIds仅映射一次，ACDC原清单trainIds保持。清单、审计和源数据索引指纹见data-provenance.json、READY.json；四条件2000个原图/GT的既有审计哈希通过verify_inputs.py重新核查。

## 正式训练预算（每组相同）

seed0；4000优化步；batch2；512×512；FP32；新建AdamW(lr=1e-5, betas=(0.9,0.999), weight_decay=.001)，无梯度累积/AMP/clip；PolyLR(power=.9, eta_min=0, begin0,end4000)。验证与checkpoint均每1000步；保留1000/2000/3000/4000，固定iter_4000主结果，不挑best。

RandomResize((2048,1024), ratio=.5–2, keep_ratio)，RandomCrop512(cat_max_ratio=.75)，RandomFlip .5，PhotoMetricDistortion；BGR增强后转RGB，ImageNet mean/std，pad_val0/seg_pad255。InfiniteSampler，worker2；seed0/deterministic=True/cudnn_benchmark=False，与既有增量配置一致。两新组相同模型构造量，训练入口设置真实seed0；不声称跨方法完全隔离了所有RNG消耗。每组模型与新优化器独立，不继承Source optimizer。

## 正式五条件评价

每组晴天Cityscapes官方val500；同500场景Foggy beta .005/.01/.02各500；ACDC-fog val100。两组共10个单元、4200次逐图评价。四配对条件精确复用severity/prepared-20261110的完整场景清单；本目录eval-manifests/full仅复制同一记录为A_val.jsonl，逐项指纹可追溯。预检另用precheck固定2场景；不能以预检代替full。ACDC完整评价直接使用原B_val100。precheck使用固定原B_val_debug的4例，无按效果选样。

原分辨率，无TTA，512裁剪/stride341滑窗，pad到32倍数；统一学生分支，19通道。参数及所有缓冲评价前后逐键hash要求不变。每单元累计19×19矩阵（GT行/预测列、255忽略、union0排除、GT缺失但预测出现为0），MMSeg与独立矩阵一致；重读所有保存预测及原始标签再独立复算。记录checkpoint SHA、实际图像数及分支调用；不能平均逐图mIoU。与原Source/FT/GSMF15单元可按哈希/协议核对后复用，本轮不重跑旧组全量评价。

## 资源与执行

RTX3080 20GiB；环境仍Python3.8.20/PyTorch1.9.1+cu111/MMCV2.0.0/MMEngine0.8.2/MMSeg1.2.1，无升级/下载/系统修改。短测LwF约0.210秒/步、峰值allocated2619MiB；BN变体约0.188秒/步、2279MiB（小样本，包含梯度诊断；不保证正式吞吐）。旧完整配对评价每500图约250–267秒，ACDC100约53–56秒。

估算：8000步纯训练约26.5分钟；8次B100周期验证约7.5分钟；两模型五条件评价约36分钟；加初始化、保存、独立核验/图表/打包，建议预留 **1.5–2.5小时或更长**。checkpoint各约730MiB，8份约5.7GiB；两份初始化约0.72GiB，全量预测无压缩上界约8.2GiB，含日志/图表/交接建议 **新增预留20GiB**。准备文件约10GiB级另存不删除；现场WSL空闲约690GiB，Windows C盘约120GiB（动态VHD受宿主限制，正式前复查）。不终止其他任务，不自动重试、追加seed/天气或超参搜索。

正式启动入口（仅在用户发送提示词二后）：

```bash
# 下一轮把用户原文授权、确认时间、READY.json SHA写入authorization.json：
# {"prompt_two_confirmed": true, "ready_sha256": "<真实SHA>", "user_message": "<提示词二原文>", "confirmed_at": "...+08:00"}
bash tools/road/lwf_bn_start.sh \
  experiments/road_lwf_bn/prepare-seed0-20261110-153000 --confirmed-prompt-two
```

该入口先校验READY代码/数据/初始化/配置指纹、CUDA和磁盘，再tmux持久顺序执行lwf训练→其五评价→BN变体训练→其五评价。阶段commands、日志、PID、events、状态及退出码真实记录；失败即停止。尚未创建authorization.json。tmux本轮仅做CUDA查询/退出码探针，不含训练。流水线完成标志明确为train_eval_complete_pending_summary；提示词二还须按其要求汇总五模型、GT直方图核验、曲线/固定样例和轻量包，不能把后台启动或训练/推理结束当作整个任务完成。

查看和恢复：

```bash
bash tools/road/lwf_bn_status.sh experiments/road_lwf_bn/formal-seed0-plan-20261110-153000
# 选择最新能完整读取且含optimizer/scheduler的checkpoint；无仍在运行任务、无更晚checkpoint后：
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 \
 /home/ysheng4/miniconda3/envs/GSMF_RS_DIL/bin/python tools/road/run.py train \
 --stage lwf --resume <正式目录>/lwf/iter_1000.pth --work-dir <正式目录>/lwf
# BN组stage=gsmf_teacher_bn同理。恢复会保存resume-verified文件核验optimizer/scheduler/iter。
# 不是--load；不恢复RNG或采样游标，不承诺与不中断逐位一致。
```

恢复后按正式目录每阶段退出码、完成checkpoint SHA和评价图像数核查已完成单元；仅继续缺失单元，评价使用新独立工作目录，不覆盖失败现场。完整评价命令模板：

```bash
P=/home/ysheng4/miniconda3/envs/GSMF_RS_DIL/bin/python
$P tools/road/run.py eval --stage lwf --domain A --checkpoint <正式目录>/lwf/iter_4000.pth \
 --manifests experiments/road_lwf_bn/prepare-seed0-20261110-153000/eval-manifests/full/0.005 --work-dir <新目录>
$P tools/road/run.py eval --stage lwf --domain B --checkpoint <正式目录>/lwf/iter_4000.pth --work-dir <新目录>
```

A条件分别beta0/.005/.01/.02，BN组替换stage及checkpoint，均不使用--debug。resume及单元恢复本轮未执行正式步骤，具体执行由下一轮核查现场后完成。

## 证据、限制和授权边界

实施说明见IMPLEMENTATION.md；本轮实际命令见COMMANDS.md、debug-chain.sh、eval-precheck.sh及训练invocation/resolved；短测结果见VALIDATION.md和各JSON；源码恢复见validated-source.tar.gz、git-diff.patch与code-fingerprint.json。本轮无Git提交/推送，已有REPRO改动和handoff_exports保留。

当前无方法效果结论；短测IoU不作正式效果。单种子不能证明统计显著性；真实/合成跨库差异及ACDC训练强度支持未知，不能称严格未见强度泛化。BN诊断不预设因果解释。正式预算和评价未发现与记录的实质性配置差异。
