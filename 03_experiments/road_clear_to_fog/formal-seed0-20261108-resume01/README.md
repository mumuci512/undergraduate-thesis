# 道路晴天→雾天seed0实验轻量交接包

实际完成运行ID：`formal-seed0-20261108-resume01`；源的前40000步来自`formal-seed0-20261108-001`。整理时间：20261108-174551（Asia/Shanghai）。本次只整理已有产物与CPU读取权重结构；没有重新训练、构建模型、运行模型评价或导出全量预测，没有修改原始实验结果或提交/推送Git。

## 直接查看

- [结果总表](RESULTS_SUMMARY.md)：三模型两域mIoU、旧域下降、新域增量、等权均值及限制。
- [Git恢复说明](GIT_REFERENCE.md)与[GIT清单](GIT_FILES.tsv)：必要源码、基础/继承配置、已上传协议文档和环境锁文件均定位到完整commit，不重复装入包。
- [缺项](MISSING_AND_LIMITATIONS.md)：缺预测对比图、部分训练时版本哈希、精确RNG游标等均如实列出。
- [权重索引](WEIGHTS.md)：最终/恢复/初始化权重的绝对路径、大小、SHA-256与optimizer/scheduler状态；权重本身保留家中。
- [实际文件来源清单](ARTIFACT_INVENTORY.csv)：逐项标明“包内已有”或“Git可恢复”，包内路径与恢复位置分开记录。
- [家中保留清单](HOME_RETAINED.json)和[全量预测索引](HOME_PREDICTIONS_INDEX.jsonl)：只带路径/大小/hash，不带这些大文件。
- 配置依赖见[CONFIG_DEPENDENCIES.json](CONFIG_DEPENDENCIES.json)，绝对路径重定位说明见[PATH_MAPPING.json](PATH_MAPPING.json)。

## 四种文件状态

| 状态 | 内容 | 是否已带回 |
|---|---|---|
| 包内已有 | runs下两段源训练、FT/GSMF、转换和六组评价的完整日志/原始JSON/标量、运行配置、命令、退出状态、环境快照、数据清单、控制器快照及少量既有数据预览 | 是，以MANIFEST为准 |
| Git可恢复 | 必要源码、原始配置及继承文件、PLAN/STATUS/RESULTS/DATA、REPRO、类别映射、依赖锁定文件 | 原文件省略；按GIT_FILES从明确commit恢复 |
| 家中保留 | 数据集/归档、Conda目录、.git、所有checkpoint、1800张全量预测、大型原始诊断与缓存 | 否，绝对路径不是随包文件 |
| 缺失/待核实 | 见缺项表；没有为补齐清单新增实验 | 否 |

## 解压到课题项目

压缩包有一个顶层目录`formal-seed0-20261108-resume01/`。在课题项目先创建`03_experiments/road_clear_to_fog/`，然后：

```bash
tar -xzf <本压缩包.tar.gz> -C 03_experiments/road_clear_to_fog/
cd 03_experiments/road_clear_to_fog/formal-seed0-20261108-resume01
sha256sum -c MANIFEST.sha256
```

如已进入完整目标目录，则解压时用`--strip-components=1`。无需在家中创建此课题目录，本次没有访问学校项目。

## 可恢复范围与家中路径

Git仓库为`https://github.com/mumuci512/GSMF-RS-DIL`。请先按GIT_REFERENCE恢复确切代码/文档；训练时的基准commit与训练后上传commit分开记录。原始配置及JSONL保留家中绝对路径作为证据，不会自动适配另一台机器；数据图像/标签、ImageNet权重和最终模型均需另行取回或按各自授权准备。不要把这些路径或last_checkpoint文本当成已经携带的checkpoint。

家中仓库根目录：`/home/ysheng4/research/GSMF-RS-DIL`；完整完成运行：`/home/ysheng4/research/GSMF-RS-DIL/experiments/road_clear_to_fog/formal-seed0-20261108-resume01`；原始中断运行：`/home/ysheng4/research/GSMF-RS-DIL/experiments/road_clear_to_fog/formal-seed0-20261108-001`；环境目录：`/home/ysheng4/miniconda3/envs/GSMF_RS_DIL`。最终三个checkpoint路径、SHA及状态见WEIGHTS。报告使用固定最终模型，未使用最佳checkpoint选择。

已有4张样例为RGB/GT/GT叠加预览，样本ID在examples/sample_ids.json；没有找到道路Source/FT/GSMF同样例预测对比图，本次没有补做。正式纯GPU延迟和GFLOPs未测。单seed0与跨数据集限制，以及中断恢复不保证逐位一致，均随结果保留。

## 验证

MANIFEST覆盖除自身外的全部包内文件。可运行`python3 tools/verify_package.py`进行文件集合与SHA核验；Git文件恢复由另一个只读Git提取脚本核验。包内Markdown相对链接均指向实际文件；家中路径和Git恢复位置只作为明确标注的索引。压缩包经过独立解包后再验证清单，压缩包SHA-256写在外置同名.sha256文件中。
