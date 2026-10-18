# 本科毕业论文研究仓库

本仓库保存文献、方法复现、实验、机器人部署和论文写作成果。工作规范见 [AGENTS.md](AGENTS.md)，当前研究方向、阶段和近期目标以 [PROJECT_STATE.md](00_management/PROJECT_STATE.md) 为准。新任务按需读取相关成果，达到研究里程碑时更新状态。

原始[任务书](<20260928144022150248_盛曦-毕业设计(论文)任务书2.doc>)和[综述文献](综述/)保留原位；[原始资料校验快照](00_management/INITIAL_SOURCE_INVENTORY.json)是初始化时的固定历史记录。

## 文件职责

| 路径 | 职责 |
| --- | --- |
| `AGENTS.md` | 稳定的研究工作规范 |
| `00_management/PROJECT_STATE.md` | 唯一的当前全局研究状态 |
| `00_management/DECISIONS.md` | 具有长期影响的研究决策及依据 |
| `00_management/INITIAL_SOURCE_INVENTORY.json` | 原始资料的固定校验快照 |
| `00_management/archive/` | 一次性迁移前的任务清单、工作日志和阶段规划，仅作历史参考 |
| `01_literature/LITERATURE_INDEX.md` | 文献 ID、书目信息、阅读状态及报告位置 |
| `01_literature/survey_reports/`、`paper_reports/`、`comparisons/` | 逐篇报告、综合对比和相关阅读资料 |
| `02_baselines/` | 基线代码、版本与运行说明 |
| `03_experiments/` | 正式实验目标、协议、配置、版本、结果与分析 |
| `04_robot/` | 平台约束、部署和验证记录 |
| `05_writing/` | 开题、毕业论文及潜在投稿材料 |
| `06_meetings/` | 真实的导师交流与会议记录 |

六篇本地综述的阅读报告和综合对比报告为 Word 文件，入口见[文献索引](01_literature/LITERATURE_INDEX.md)。原始论文尚未收集核验，正式实验和机器人部署尚未开始；目录或占位文件不代表研究成果已经完成。

研究成果记录在相应用途目录，文献进度只在索引中维护；全局阶段与近期目标只在状态文件中维护。正式实验应保留足以复现的方法、数据与评价协议、代码版本、配置、结果及结论。Git 提交和推送由用户决定。
