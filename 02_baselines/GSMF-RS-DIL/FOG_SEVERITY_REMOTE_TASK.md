# 发给远程 Codex：现有三模型的独立场景多雾强度评价

编写日期：2026-11-09（Asia/Shanghai）。状态：本地交接指令已准备，未访问远程实时工程、下载雾图或启动推理。将下面代码框内的文字粘贴到远程 GSMF 仓库的 Codex，或把本文件传到远程后让它读取。此指令自包含，不要求远程能读取学校的论文目录。

```text
请在现有 GSMF-RS-DIL 道路工程中，实际完成现有 Source／FT／GSMF 三个最终模型在“独立场景、晴天＋三档雾强度”上的固定模型评价，输出 mIoU 曲线、完整逐类表和同场景预测对比，并整理轻量回传包。我已确定这轮评价范围，请直接完成数据可用时的检查、必要评价代码、少量预检、全量推理和结果打包；不只给计划，不需要重新训练。

一、定位工程与已完成模型

1. 先读本机适用 AGENTS.md、工程 README，以及已有道路实验的 PLAN／STATUS／RESULTS／DATA 和评价入口。不要假定学校 C:\undergraduate_thesis 在这里存在。以下路径与哈希来自2026-11-08归档，是定位线索；先现场验证存在性、内容和当前状态。
2. 已知工程根目录：/home/ysheng4/research/GSMF-RS-DIL
   已完成正式运行根目录：/home/ysheng4/research/GSMF-RS-DIL/experiments/road_clear_to_fog/formal-seed0-20261108-resume01
   已知环境：/home/ysheng4/miniconda3/envs/GSMF_RS_DIL
   代码仓库：https://github.com/mumuci512/GSMF-RS-DIL
   训练后恢复提交：315f273929c09ffa991a1f1d6f95e304641386ce
   原训练基准HEAD：e141e523e86f98f772ee787bb2aa95272f38e4fe，训练时含道路代码等未提交改动。不要只checkout原基准就认为恢复了训练代码，不要reset或覆盖当前改动。
3. 固定使用以下三个最终检查点，均非best选择：
   Source：<正式运行根目录>/source/iter_60000.pth
   SHA-256：a66c958ee774d27566b901ad6570c0a3b83263e9d74389e1c2e025c6c2673d93
   FT：<正式运行根目录>/ft/iter_4000.pth
   SHA-256：99914df527d8506c33178ef6ea1caf7f0ed1d07369858e37275205d60a57d516
   GSMF：<正式运行根目录>/gsmf/iter_4000.pth
   SHA-256：fc227c57dc3e47a134ef51b282964654a0210f3c06f00bd0d3e81b706850b24a
   这里的尖括号表示使用第2项给出的实际运行根目录。验证三份完整SHA；若不符，先保留差异并查归档，不悄悄换模型。不要使用转换初始化、ImageNet、遥感六类、iter8调试或损坏的iter50000权重替代。
4. 优先复用上次已验证的评价路径和模型加载。归档中的Source／FT评价使用backbone、decode_head；GSMF使用backbone_1、decode_head_1，即增量后的部署分支，两种天气均如此。现场确认实际forward调用；不按天气切换到旧分支。若导出单分支，先验证与原评价分支在固定输入上的输出等价，并记录转换规则。
5. 记录实际Git HEAD、dirty diff、相关代码哈希、环境、模型／数据配置和命令。保留旧训练与评价目录；新代码尽量放在独立评价入口，不改训练算法、冻结策略或损失。无需Git提交或推送。

二、准备同场景四条件数据与隔离检查

1. 使用Cityscapes fine官方val对应的同一组场景，包含：原始晴天（画图记β=0）和Foggy Cityscapes的β=0.005、0.01、0.02 m^-1三档。优先完整500个val场景，共2000张输入；三模型共6000次逐图评价，滑窗的内部forward次数另计。
2. 核对已有合法数据、已下载归档及相关配置；Foggy Cityscapes官方说明：https://people.ee.ethz.ch/~csakarid/SFSU_synthetic/ ，图像下载入口：https://www.cityscapes-dataset.com/downloads/ 。常用雾图包名为leftImg8bit_trainvaltest_foggy.zip，最终以官方目录和实际包为准。
3. 不要求重新下载已有Cityscapes原图／GT。若缺少雾图，继续完成不依赖雾图的代码、配置和打包接口；明确缺少的包、官方入口、磁盘需求及需要用户提供的登录／文件信息。不要绕过账号、使用不明镜像，或未经明确范围就下载全套视频／额外数据。少量样例不冒充全量完成。
4. 用原始city／sequence／frame标识关联晴天、三档雾与同一个GT，检查每景恰有四条件、图像尺寸一致且标签对齐。按原始场景核对Source和FT／GSMF实际训练清单，防止同一原图或其天气变体跨到评价集；有邻近帧访问也披露，未核实的地理隔离不得宣称已证明。已知Source训练为Cityscapes train，增量训练为ACDC-fog train，仍以实际清单为准。
5. 不把Foggy train／trainextra／refined子集当成完整val。若数据缺失，优先补齐；确实无法补齐时固定四条件共同可用场景，单列缺失并报告实际N，不能让各强度用不同场景，也不能标作完整500场景。
6. 保存数据清单：base_scene_id、condition／beta、图像与GT实际路径及SHA-256、官方划分、配对与隔离检查结论。保留本次实际读取的数据与预处理来源。
7. 统一19类trainId 0..18：road, sidewalk, building, wall, fence, pole, traffic light, traffic sign, vegetation, terrain, sky, person, rider, car, truck, bus, train, motorcycle, bicycle。GT=255忽略；核对labelIds到trainIds映射，避免二次转换。Foggy图沿用对应原图标签，不用伪标签或正常／雾图混配。

三、固定推理和小量预检

1. 本轮不训练、不微调、不调参、不做TTA。三个模型全部eval、关闭梯度，不更新BN统计或其他模型状态。沿用上次各模型已验证的预处理／滑窗策略，核对颜色顺序、归一化、缩放和输出还原；四种强度使用相同输入规则。不为某一模型或强度单独改推理尺寸。
2. 检查GPU已有任务、可用显存与磁盘，单GPU顺序评价，不终止别人的进程。先对两个固定场景的四条件和三个模型预检，核对加载、实际分支、输出19通道、标签映射、预测尺寸及模型状态不变；预检只验证链路。
3. 预检通过且数据齐全后直接执行全量评价，不再询问是否开始已授权的推理。预计耗时根据当前吞吐给出；长任务使用现有tmux等持久会话，保存日志、退出码和恢复入口。只跳过经过哈希与配置核对且已完整结束的单元，失败单元不计完成。
4. 全量晴天结果用于一致性核查。既有500张Cityscapes val的mIoU参考：Source=71.5087%，FT=54.2915%，GSMF=55.2078%。它们不是这次必须凑出的目标；若明显不一致，检查样本、模型、分支、映射、预处理、依赖及精度，记录原因，不能用旧数值覆盖本次结果。数据子集变化时不要求与完整500张结果一致。

四、指标与正式输出

1. 每个“模型×beta”分别在整个固定场景集合累计19×19混淆矩阵，再计算逐类IoU和mIoU；不是平均逐图mIoU。GT=255忽略，union=0的类置null并排除均值，GT没有但预测有的类IoU=0。记录矩阵方向、类别顺序、gt_pixels、pred_pixels、intersection、union以及实际参与均值的类别。
2. 保存12个混淆矩阵的机器可读文件及可直接查看的CSV；结果长表包含model、beta、n_images、mIoU_percent、相对本模型晴天的下降pp、checkpoint_sha256、数据清单哈希。另输出完整19类×模型×强度的IoU长表和便于比较的宽表，数值保留足够精度。
3. 用标准绘图工具输出mIoU曲线PNG及SVG或PDF：三条线对应Source／FT／GSMF，横轴用真实β数值0、0.005、0.01、0.02，纵轴mIoU%；仅连接实测点，不作平滑拟合或伪造密集采样。标注场景数、合成雾、固定最终模型和单seed。
4. 推理前固定6个可用val场景，使用固定随机种子20261109选取并保存sample_ids.json，不根据结果挑最好样例。每景画一个四行五列对比：行是晴天／三档雾，列是RGB／GT／Source／FT／GSMF；统一类别配色、ignore显示和图例，字号清晰。保存这些样例的原始trainId预测PNG和适合报告阅读的预览图；不只给彩色叠加图。
5. 完整预测保留远程，记录路径及索引；轻量回传包只带六个样例的预测和预览，原始数据图像按数据许可处理。另记录推理时间和峰值显存；无需为本轮新增完整GFLOPs或纯GPU延迟实验。
6. 独立从保存的矩阵复算mIoU与逐类表，检查样本计数、矩阵有效像素总数、图表数值以及推理前后全部参数／缓冲区状态不变。复用已有可靠指标核验工具即可，避免另建大量管理框架。
7. 分析随强度变化的绝对性能、相对晴天下降、GSMF相对FT差异和主要类别；不预设GSMF更优。称为“固定模型的受控合成多雾强度稳健性评价”。ACDC-fog没有逐图强度标注，训练强度支持未核实，因此不写“严格未见强度泛化”，也不写成真实连续流适应或统计显著结论。

五、运行目录和轻量回传

1. 在experiments/road_fog_severity/eval-final-seed0-20261109-<唯一时间或后缀>/创建本次目录，记录实际路径，保留原归档。保存PLAN.md、STATUS.md、SUMMARY.md、数据清单／检查、模型清单、完整resolved配置、相关脚本、命令、版本／环境证据、日志、退出码、指标矩阵、CSV和图。
2. STATUS.md记录真实已完成单元、失败／缺失项、运行会话或进程和最后核查时间。启动成功不写成全部完成；不承诺对话结束后没有实际机制的持续监控。
3. 生成独立轻量回传目录，包括SUMMARY、STATUS、机器可读结果与12个矩阵、全部逐类表、曲线、六个场景对比与其原始预测、数据／权重索引、精确代码／配置及必要日志。权重、数据归档、Conda、.git、完整预测留远程；包内绝对路径须标为“远程保留”，不能当成已经回传。
4. 保存MANIFEST.sha256，校验包内全部文件（清单自身除外）；打包tar.gz或zip，并验证解包后文件集合与哈希。另保存外置同名.sha256，用于传输校验。原则上控制为轻量包，图太大就生成清晰缩略预览，完整分辨率保留远程并索引。
5. 包在本地论文项目的目标归档位置为03_experiments/road_fog_severity/<本次run_id>/。不要尝试在远程写入学校C盘路径，也不要求远程存在论文项目。若恢复需要Git文件，提供精确commit和路径；未提交的新脚本须实际带入包，不能仅写“Git可恢复”。

完成后用中文汇报：实际数据范围、三个checkpoint核验、12组是否完成、四强度结果表、关键限制、运行目录、轻量包及其SHA文件的绝对路径，以及从本地获取包的scp命令模板。SSH主机别名未知时用明确占位符，不猜测地址或凭据。缺数据时清楚列出阻塞和已完成准备，不能声称评价已经完成。
```

本地依据：[权重索引](../../03_experiments/road_clear_to_fog/formal-seed0-20261108-resume01/WEIGHTS.json)、[原结果](../../03_experiments/road_clear_to_fog/formal-seed0-20261108-resume01/RESULTS_SUMMARY.md)、[数据来源与协议](../../03_experiments/MULTI_SEVERITY_WEATHER_DATA_SOURCES_2026-11-09.md)。这些链接用于本地追溯，远程执行只需代码框内的完整指令及现场工程。
