# GSMF-RS-DIL：Potsdam → Vaihingen 复现结果

实验代码为上游 `e141e523e86f98f772ee787bb2aa95272f38e4fe` 加本项目兼容性修改。Potsdam 为旧域，Vaihingen 为新域。基础训练 80,000 次、转换该最终 checkpoint 后增量训练 10,000 次；seed 0，batch size 4；最终测试 batch size 1、无 TTA。Potsdam 验证切片 3,150 张，Vaihingen 442 张。下列数据为各域所有切片像素混淆矩阵累计后计算的指标。各表差值为复现减论文，单位为百分点（pp）。

## 与论文结果比较

| 阶段与验证域 | 指标 | 论文 | 本次复现 | 差值（pp） |
|---|---|---:|---:|---:|
| 基础训练：Potsdam | OA | 88.72% | 88.37% | -0.35 |
| 基础训练：Potsdam | mF1 | 84.56% | 83.84% | -0.72 |
| 基础训练：Potsdam | mIoU | 74.87% | 74.01% | -0.86 |
| 增量后旧域：Potsdam | mIoU | 61.91% | 63.76% | +1.85 |
| 增量后新域：Vaihingen | mIoU | 65.81% | 65.67% | -0.14 |

论文基础指标见 [论文](../../paper.pdf)及[官方 README](../../README.md)；跨域 mIoU 亦见官方 README 对应表格。OA 与测试日志的 aAcc 采用同一像素总体准确率口径。mF1 是本次从已保存的最终预测和真实标签重建混淆矩阵后计算，未从四舍五入的 IoU 近似转换。重新计算的 aAcc、mAcc 和 mIoU 均与测试日志显示精度一致。

## 本次复现：旧域与新域

| 阶段 | 域 | aAcc / OA | mAcc | mF1 | mIoU |
|---|---|---:|---:|---:|---:|
| 基础训练 | Potsdam（旧域） | 88.37% | 82.48% | 83.84% | 74.01% |
| 增量训练后 | Potsdam（旧域） | 82.75% | 73.23% | 75.53% | 63.76% |
| 增量训练后 | Vaihingen（新域） | 86.21% | 74.96% | 77.86% | 65.67% |

旧域 mIoU 从基础模型的 74.01% 降至增量模型的 63.76%，下降 10.25 个百分点。这是基于两个模型在相同旧域验证集上的结果。

各类别 IoU（%）：

| 类别 | 基础 Potsdam | 增量后 Potsdam | 增量后 Vaihingen |
|---|---:|---:|---:|
| 不透水表面 | 83.88 | 79.28 | 79.32 |
| 建筑 | 91.58 | 87.83 | 86.61 |
| 低矮植被 | 72.52 | 61.49 | 62.78 |
| 树木 | 73.64 | 56.42 | 74.65 |
| 汽车 | 82.88 | 74.40 | 56.10 |
| 杂类 | 39.57 | 23.17 | 34.58 |

mIoU 为六类 IoU 的均值，包含杂类；mAcc 为逐类召回率的均值。样例重叠切片按框架原评估口径累计，不做原图去重。

## 代表性预测

![旧域和新域的影像、标注与增量模型预测](segmentation-examples.png)

图中输入为 NIR/R/G 假彩色。每域先筛选真实标签中至少有四类各占 ≥1% 像素的切片，再选择单图 mIoU 最接近该候选集单图中位数的切片；不是按全数据集 mIoU 直接选取。Potsdam 切片 `top_potsdam_5_15_IRRG_1_11` 的单图 mIoU 为 54.64%；Vaihingen 切片 `top_mosaic_09cm_area27_0_3` 为 60.31%。单图 mIoU 不等同于汇总所有像素后计算的全域 mIoU。

## 可追溯文件与限制

- 基础模型：[最终测试日志](../isprs-full-20261028-ucOKFM/base-test-console.log)、[80,000 次 checkpoint](../isprs-full-20261028-ucOKFM/base/iter_80000.pth)。
- 增量模型：[最终测试日志](../isprs-full-20261028-ucOKFM/incremental-test-console.log)、[10,000 次 checkpoint](../isprs-full-20261028-ucOKFM/incremental/iter_10000.pth)。
- [混淆矩阵、指标和样例选择结果](metrics-and-selection.json)；[计算脚本](analyze.py)、[运行日志](analyze.log)、[制图脚本](figure.py)。
- 作者 checkpoint 在同一完整验证集上的 mIoU 为 74.87%、61.91%、65.81%，与作者报告一致。
- 本次仅运行一个 seed；PyTorch 等环境与作者不同，ISPRS TIFF 采用经样例核对的 tifffile 兼容读取器。Potsdam 一张官方完整训练标签颜色异常，采用同图官方 participants 训练标签；仓库例图与官方标签存在少量像素差异。不能从单次结果推断差异原因或统计显著性。
