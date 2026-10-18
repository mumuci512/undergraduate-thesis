# 研究任务清单

最后更新：2026-10-18（Asia/Shanghai）。仅 T-001 已完成；尚未执行正式文献阅读、方法选择、复现或实验。

状态只能使用：**待办、进行中、已完成、阻塞、取消**。优先级：P0 为近期优先，P1 为后续核心工作，P2 为可选拓展。依赖列为启动所需的前置任务；“计划”成果均尚未创建。依赖和时间可据实际资源调整，调整重要研究选择时同步记录决策。

| 任务 ID | 任务名称 | 所属研究阶段 | 优先级 | 状态 | 依赖关系 | 对应成果文件 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T-001 | 初始化长期研究管理系统与文献索引 | 管理初始化 | P0 | 已完成 | 无 | `AGENTS.md`；`README.md`；`.gitignore`；`00_management/`；`01_literature/LITERATURE_INDEX.md` | 已检查原始资料完整性；未进行正式阅读、Git 暂存或提交 |
| T-002 | 确认任务书边界、导师验收要求与真实时间安排 | 前期准备 | P0 | 待办 | T-001 | 计划：`06_meetings/YYYYMMDD_scope_confirmation.md` | 任务书为草稿；机器人部署及学校日期需确认 |
| T-003 | 盘点计算资源、机器人平台及部署约束 | 前期准备 | P0 | 待办 | T-001 | 计划：`04_robot/PLATFORM_CONSTRAINTS.md`；`03_experiments/RESOURCE_BUDGET.md` | GPU/显存、训练预算、系统、传感器、接口与实时性要求待确认 |
| T-004 | 制定文献阅读顺序、报告模板与覆盖目标 | 综述泛读 | P0 | 待办 | T-002 | 计划：`01_literature/comparisons/READING_PLAN.md` | 数十篇为导师要求的量级；具体篇目与泛读/精读口径待定 |
| T-005 | 泛读现有综述并梳理领域与问题设定 | 综述泛读 | P1 | 待办 | T-004 | 计划：`01_literature/survey_reports/LIT-xxx_short_topic.md`；`01_literature/comparisons/FIELD_MAP.md` | 现有 6 篇均未读；书目信息核对不计为泛读 |
| T-006 | 扩充原始论文并核验代码、数据和版本来源 | 原始论文收集 | P1 | 待办 | T-005 | 更新：`01_literature/LITERATURE_INDEX.md`；计划：`01_literature/comparisons/CANDIDATE_LIST.md` | 不把任务书参考文献自动视为已核验或已收集 |
| T-007 | 精读候选原始论文并比较复现与部署成本 | 原始论文精读 | P1 | 待办 | T-006 | 计划：`01_literature/paper_reports/LIT-xxx_short_topic.md`；`01_literature/comparisons/BASELINE_COMPARISON.md` | 记录事实、推断、疑点、资源需求与适用边界 |
| T-008 | 确定研究问题、复现对象和最低可行方案 | 问题与基线选择 | P1 | 待办 | T-002、T-003、T-007 | 计划：`03_experiments/RESEARCH_PROTOCOL.md`；更新：`00_management/DECISIONS.md` | 候选模型、数据集和基线尚未选定 |
| T-009 | 准备复现代码、环境与运行说明 | 方法复现 | P1 | 待办 | T-008 | 计划：`02_baselines/README.md` 及环境/版本记录 | 保留代码来源、版本、许可证与可复现命令；当前不安装训练环境 |
| T-010 | 落实数据划分、数据流、缓存与评估协议 | 方法复现 | P1 | 待办 | T-008 | 计划：`03_experiments/DATA_PROTOCOL.md` 及配置 | 草稿约束作为待确认参考；避免未来数据和测试信息泄漏 |
| T-011 | 运行并核验选定基线的复现结果 | 方法复现 | P1 | 待办 | T-009、T-010 | 计划：`03_experiments/YYYYMMDD_EXP-xxx_baseline/` | 保存命令、种子、配置、指标、失败记录及与原文差异 |
| T-012 | 根据失效现象提出并实现一项适量改进 | 改进方法 | P1 | 待办 | T-011 | 计划：`03_experiments/METHOD_PROPOSAL.md`；更新：`00_management/DECISIONS.md` | 创新性与有效性均须验证，不预设提升 |
| T-013 | 完成公平对比、必要消融与结果分析 | 实验验证 | P1 | 待办 | T-012 | 计划：`03_experiments/YYYYMMDD_EXP-xxx_evaluation/` | 控制骨干、划分、数据流、缓存及更新预算；报告资源代价 |
| T-014 | 实现机器人部署并验证平台表现 | 机器人部署 | P1 | 待办 | T-003、T-011 | 计划：`04_robot/DEPLOYMENT_PLAN.md`；`04_robot/DEPLOYMENT_REPORT.md` | 可先部署已验证基线；改进方法稳定后再同步，不默认平台在线训练 |
| T-015 | 持续整理开题、论文各章与最终归档材料 | 毕业论文写作 | P1 | 待办 | T-005 | 计划：`05_writing/OUTLINE.md` 及阶段稿件 | 相关工作可先写，方法/实验随证据完善；正式节点待确认 |
| T-016 | 评估 2027 年 3 月前成果的投稿潜力 | 潜在投稿 | P2 | 待办 | T-013 | 计划：`05_writing/SUBMISSION_FEASIBILITY.md` | 非硬性目标；届时核验具体渠道、要求和日期，不承诺录用 |
| T-017 | 建立导师沟通与阶段复盘记录 | 持续管理 | P1 | 待办 | T-001 | 计划：`06_meetings/YYYYMMDD_topic.md` | 首次真实沟通后记录，不虚构会议或导师意见；后续按次拆分任务 |

## 更新规则

- 开始实际执行后再标“进行中”；产出可核验且满足完成标准后再标“已完成”。等待前置工作不自动等于“阻塞”。
- 确实无法推进时标“阻塞”，在备注写明原因与解除条件；取消任务保留记录与原因，不复用 ID。
- 发生实质进展后同步状态与研究日志；不另建平行待办列表。
