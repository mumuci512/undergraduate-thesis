# 家中保留的权重索引

实际文件不在交接包。完整路径、SHA-256、大小及续训字段见[WEIGHTS.json](WEIGHTS.json)或[CSV](WEIGHTS.csv)。

报告使用source iter60000、FT iter4000和GSMF iter4000，均为固定最终checkpoint；save_best关闭，不是按保留集挑选的最佳权重。三者均含optimizer/scheduler/meta。原iter40000为恢复输入，原iter50000损坏且不可用；转换权重和ImageNet权重仅用于初始化，不能作为完整状态resume。
