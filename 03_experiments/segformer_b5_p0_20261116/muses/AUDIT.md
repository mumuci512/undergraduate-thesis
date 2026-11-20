# MUSES RGB夜雨／夜雪：P0数据审计

日期：2026-11-16（Asia/Shanghai）。AI辅助定向核验；未开展模型训练。本次完成官方文件目录与元数据的全量清点，并解码4组RGB／语义标签样本；未下载完整RGB或完整语义标签归档。

**结论：夜雨和夜雪各有train 150、val 25、test 75张RGB；仅train／val公开语义标签。** 两条件的公开val合计50张，可用于固定模型的复合条件初测。论文中的“每条件250张”是跨split总量，不能当成250张训练图。

## 1. 清点依据与实际范围

- 当前官方下载站：[公开包目录](https://muses.ethz.ch/MUSES_packages/)。SDK固定版本为[`ad09c1bca986c2e8a037b514e728b704d70037ed`](https://github.com/timbroed/MUSES/tree/ad09c1bca986c2e8a037b514e728b704d70037ed)，2026-02-16提交。原站已停用。
- 下载小包[`gnss_trainvaltest.zip`](https://muses.ethz.ch/MUSES_packages/gnss_trainvaltest.zip)（1,093,942字节），从中读取官方`meta.json`，共2,500条。该包仅用于读取元数据和清单，不将GNSS作为模型输入。
- 对[`frame_camera_trainvaltest.zip`](https://muses.ethz.ch/MUSES_packages/frame_camera_trainvaltest.zip)及[`gt_semantic_trainval.zip`](https://muses.ethz.ch/MUSES_packages/gt_semantic_trainval.zip)使用HTTP Range读取ZIP中央目录。RGB归档共5,662,843,611字节，语义归档88,330,362字节；本轮未整包下载。
- 全量核对得到2,500条RGB记录、1,750条`labelTrainIds`记录。训练／验证RGB与标签按`split＋weather＋time_of_day＋scene_id`一一对应；缺配、孤立标签及meta/RGB不一致均为0。`test`没有公开语义标签条目。
- 额外按字节范围取得train／val×夜雨／夜雪各1组，共4张RGB与4张标签；8个PNG均通过解码，尺寸均1920×1080，RGB为三通道，标签为单通道。4张标签的值域均属于`0–18 ∪ {255}`。全量目录核对与小样本像素核验是不同证据范围。

原始HTTP请求、Content-Range、来源URL与SHA见[sources/FETCH_MANIFEST.json](sources/FETCH_MANIFEST.json)、[样本获取记录](sources/SAMPLE_FETCH_MANIFEST.json)；所有保存源文件的SHA见[SOURCE_HASHES.json](SOURCE_HASHES.json)。两轮HTTP读取合计13,886,554字节，包含重复读取的ZIP目录和样本压缩数据。

## 2. 官方split逐组合计数

每格为“RGB条目数／公开labelTrainIds条目数”，由官方ZIP目录与meta实际清点；完整机器表见[split_counts.tsv](split_counts.tsv)，逐图路径见[rgb_inventory.jsonl](rgb_inventory.jsonl)。

| 光照 | 天气 | train | val | test | RGB合计 |
|---|---|---:|---:|---:|---:|
| day | clear | 300／300 | 50／50 | 150／0 | 500 |
| day | fog | 200／200 | 33／33 | 100／0 | 333 |
| day | rain | 200／200 | 34／34 | 100／0 | 334 |
| day | snow | 200／200 | 33／33 | 100／0 | 333 |
| night | clear | 150／150 | 25／25 | 75／0 | 250 |
| night | fog | 150／150 | 25／25 | 75／0 | 250 |
| **night** | **rain** | **150／150** | **25／25** | **75／0** | **250** |
| **night** | **snow** | **150／150** | **25／25** | **75／0** | **250** |
| 合计 | | 1,500／1,500 | 250／250 | 750／0 | 2,500 |

night-clear、day-rain、day-snow可作为同数据集单属性参照，避免只比较不同数据集而将所有差异归于属性组合。当前清点不把MUSES任何样本并入Cityscapes／ACDC训练集；未来若要声明未见组合，须审计源模型预训练与全部训练清单。

## 3. RGB与语义标签接入

实际归档路径模式为：

```text
muses/frame_camera/{split}/{weather}/{day|night}/{scene_id}_frame_camera.png
muses/gt_semantic/{train|val}/{weather}/{day|night}/{scene_id}_gt_labelTrainIds.png
```

**真实标签后缀含`_gt_`。** 例如：

```text
frame_camera/val/rain/night/REC0012_frame_218762_frame_camera.png
gt_semantic/val/rain/night/REC0012_frame_218762_gt_labelTrainIds.png
```

站点README列出的通用`{scene_id}_{suffix}.png`模式省略了`gt`，不能直接照抄该字符串构造路径。本轮逐图清单已记录真实归档路径。

语义标签提供`labelIds`、`labelTrainIds`、`labelColor`三种；分割接入直接使用`labelTrainIds`，19类按Cityscapes顺序，`ignore_index=255`、`reduce_zero_label=False`，不二次进行labelId→trainId映射。`labelColor`仅供显示；`gt_uncertainty`是另一类标注，不能把其255值直接当作语义标签或自动遮掉所有困难但有语义真值的像素。标准语义mIoU与AUPQ不是同一指标。[官方站点数据说明](https://muses.ethz.ch/README.md)

19类映射已从[Cityscapes官方labels.py](https://github.com/mcordts/cityscapesScripts/blob/master/cityscapesscripts/helpers/labels.py)静态解析并保存为[cityscapes_19_class_mapping.json](cityscapes_19_class_mapping.json)；源文件快照与SHA随档保存。RGB通道顺序、归一化和模型推理尺寸须与B5源权重配置一致，不因MUSES原图为1920×1080另行擅改。

## 4. 划分隔离、标签权限与获取状态

[ECCV原文§3.2–3.3，pp.7–9](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/07626.pdf)说明采用Cityscapes的19类，按条件分层划分，跨条件保持地理隔离，测试真值保留用于提交评测。这些是作者报告的设计；本轮未独立复核GPS距离。

实际文件名检查：train／val、train／test、val／test均无相同scene_id，但共享REC录制序列ID分别为36、34、25个。**不能将“地理隔离”扩写成“整段录制序列完全隔离”。** 共享录制ID也不足以证明地理泄漏；应保留官方split，不自行按文件顺序重切。完整交集保存在[audit_summary.json](audit_summary.json)。

新站顶层README仍含“先注册”和“所有集合标签公开”的旧表述；与实际下载目录、固定SDK README及包目录README末尾的隐藏test说明不一致。本轮匿名HTTP请求取得公开目录、元数据和8个样本，均为200／206，无需登录；这只描述当前读取结果。实际目录仅列`gt_semantic_trainval.zip`，未列test标签包，因此本项目不能本地计算官方test mIoU。SDK给出Codabench入口，但本轮没有验证提交功能、注册要求或上传预测。[SDK说明](https://github.com/timbroed/MUSES/blob/ad09c1bca986c2e8a037b514e728b704d70037ed/README.md)、[包目录README](https://muses.ethz.ch/MUSES_packages/README.md)

SDK明确数据用于非商业研究，完整许可原件已保存为[sources/License.pdf](sources/License.pdf)及SDK副本；本轮没有提交注册、接受新协议或向评测服务上传。后续实际使用遵守原许可，不能因下载链接公开就视为无使用限制。

## 5. 复算与剩余边界

在本目录执行：

```powershell
python audit_muses.py
```

该命令离线重算全部表格、meta配对、split交集、19类映射、样本尺寸和值域以及源文件SHA；Python 3.8+，样本检查另需Pillow、NumPy。重新获取官方快照可用`python audit_muses.py --fetch`；重新取得固定4组样本用`--fetch-samples`。在线模式检查HTTP 206，拒绝服务器忽略Range而整包下载；所有提取文件均落在本任务目录。

P0已完成数据范围清点与4组真实样本检查。仍未下载其余2,496张RGB及其余1,746张公开标签，未逐张解码、全量校验标签像素、复核地理距离或执行模型评价。按本轮数据用途，先将官方val的夜雨25／夜雪25及单条件参照锁作固定模型评价；需要训练时只取官方train并另设训练内选择集，不反复用这50张保留评价图调参。
