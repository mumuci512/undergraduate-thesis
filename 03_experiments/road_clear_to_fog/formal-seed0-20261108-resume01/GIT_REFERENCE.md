# Git恢复依据

仓库：https://github.com/mumuci512/GSMF-RS-DIL

- 训练时实际基准HEAD：`e141e523e86f98f772ee787bb2aa95272f38e4fe`；工作区有未提交修改及未跟踪道路代码。不能仅checkout这个基准就当成实际训练代码。
- 当前本地分支：`repro/isprs`，当前HEAD：`315f273929c09ffa991a1f1d6f95e304641386ce`。该提交是在训练结束后产生的代码/文档上传提交，不是训练时HEAD。
- 只读`git ls-remote personal HEAD refs/heads/main`已确认用户仓库main指向该完整SHA，详见[远端原始查询](version/remote-check.json)。这证明明确commit可恢复，不依赖分支最新版。
- 原源训练和恢复流水线的66个源码成员哈希完全相同，且均与该后续提交对应文件SHA-256逐一一致。因此这些源码以及已上传的PLAN/STATUS/RESULTS/DATA、环境锁文件不重复放入压缩包。
- 训练时脏状态、原始Git diff和provenance保留在runs下；原始diff是证据，不是把当前差异冒充训练差异。恢复这66个文件无需另打补丁；没有执行提交、reset、fetch或推送。
- `gsmf_rs_dil/__init__.py`不在当时66文件哈希快照中。它可从该commit获取，但训练时内容未核实；训练分支也未单独存档。FT/GSMF共享恢复流水线启动快照，未分别保存每个子进程启动瞬间的全源码快照。
- 原始日志、完整配置、矩阵、预测、checkpoint和控制器脚本大多未上传。后续提交中只有明确列入清单的代码、协议和结果文档，不能推断全部实验产物已上传。

完整省略文件恢复清单见[GIT_FILES.tsv](GIT_FILES.tsv)，含仓库相对路径、精确commit、SHA-256及放回位置；训练分阶段证据见[TRAINING_VERSION.json](version/TRAINING_VERSION.json)。

可在课题机器新位置获取代码（仅恢复文件，不运行训练或评价）：

```bash
git clone https://github.com/mumuci512/GSMF-RS-DIL code
git -C code checkout --detach 315f273929c09ffa991a1f1d6f95e304641386ce
python3 tools/restore_git_files.py --repo code --destination git_restored
```

也可以复用已存在且含该commit的克隆。restore脚本只用`git show COMMIT:path`读取清单文件，逐个核验SHA后写入新位置；不会替你fetch或运行模型。包内生成结果总表不是原上传RESULTS文件的重复拷贝，原RESULTS请从Git恢复。
