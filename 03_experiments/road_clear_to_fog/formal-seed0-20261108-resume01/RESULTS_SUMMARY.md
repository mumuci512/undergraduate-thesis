# 已完成道路seed0结果总表

A：Cityscapes官方val 500张；B：ACDC fog官方val 100张。训练集为2975/400张；保留官方划分。

| 模型 | A mIoU% | B mIoU% | 旧域下降pp | 新域适应增量pp | 两域等权平均% | 状态 |
|---|---:|---:|---:|---:|---:|---|
| source | 71.5087 | 49.6097 | 0.0000 | 0.0000 | 60.5592 | 已完成、已评价、独立核验PASS |
| ft | 54.2915 | 62.3066 | 17.2172 | 12.6970 | 58.2991 | 已完成、已评价、独立核验PASS |
| gsmf | 55.2078 | 63.0304 | 16.3009 | 13.4207 | 59.1191 | 已完成、已评价、独立核验PASS |

19类按trainId 0..18的顺序为：road, sidewalk, building, wall, fence, pole, traffic light, traffic sign, vegetation, terrain, sky, person, rider, car, truck, bus, train, motorcycle, bicycle。GT=255忽略；累计整域19×19混淆矩阵后计算逐类IoU，union=0类置null并排除均值，GT无该类但有预测则IoU=0。不是逐图mIoU平均。

旧域下降=Source A−当前A；新域增量=当前B−Source B；等权均值=(A+B)/2。

GSMF相对FT：A约+0.9163pp，B约+0.7237pp；两者均有旧域遗忘，两域均值仍低于Source。本次仅seed0，不能写成统计显著结论。跨数据集包含地点/设备/场景差异，不能全归因于天气。

源从iter40000恢复至60000；模型、AdamW、PolyLR与迭代位置精确恢复，但原checkpoint无RNG和数据游标，不能认为与不停机逐位相同。FT/GSMF各4000，均从同一最终源checkpoint初始化，无旧域训练回放。

表格来源：包内 [原始最终核验JSON](runs/formal-seed0-20261108-resume01/final-independent-verification.json)。
完整逐类数值见 [CSV](results/per_class_IoU.csv)，六个矩阵见results/confusion_*.csv；已有原始JSON保存在runs下。
资源见 [resource_costs.csv](results/resource_costs.csv) 与原始summary/resource-accounting.json。A/B评价含I/O、指标和保存，不是纯GPU延迟；正式模型GFLOPs、独立纯推理延迟未测。
源有效分段墙钟约10248.93秒，FT约1153.76秒，GSMF约931.98秒；峰值allocated分别2552.22/2435.38/2279.37MiB。共享负载及分段测量限制速度比较。
