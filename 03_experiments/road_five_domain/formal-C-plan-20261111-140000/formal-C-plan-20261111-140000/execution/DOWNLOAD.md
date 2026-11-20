# 阶段C轻量交接获取方式

本文件预先记录固定输出路径；文件存在与本文本均不代表实验已完成。最终以本正式目录的completion.json中status=complete、handoff/handoff-verification.json中status=PASS，以及completion-supervisor.exit为0为准。检查失败时后台停止并保留现场。

远程正式目录：`/home/ysheng4/research/GSMF-RS-DIL/experiments/road_five_domain/formal-C-plan-20261111-140000`

归档：`/home/ysheng4/research/GSMF-RS-DIL/experiments/road_five_domain/formal-C-plan-20261111-140000/handoff/formal-C-plan-20261111-140000-light.tar.gz`

外置SHA：同归档路径追加`.sha256`。实际SHA在完成打包后生成，并记录于handoff/handoff-verification.json与completion.json，不预先填写。

学校本地接收目录：`C:\undergraduate_thesis\03_experiments\road_five_domain\formal-C-plan-20261111-140000\`

阶段C完成后，在学校Windows PowerShell执行：

```powershell
$dest = 'C:\undergraduate_thesis\03_experiments\road_five_domain\formal-C-plan-20261111-140000'
New-Item -ItemType Directory -Force -Path $dest | Out-Null
scp 'home-wsl:/home/ysheng4/research/GSMF-RS-DIL/experiments/road_five_domain/formal-C-plan-20261111-140000/handoff/formal-C-plan-20261111-140000-light.tar.gz*' $dest
scp 'home-wsl:/home/ysheng4/research/GSMF-RS-DIL/experiments/road_five_domain/formal-C-plan-20261111-140000/completion.json' $dest
scp 'home-wsl:/home/ysheng4/research/GSMF-RS-DIL/experiments/road_five_domain/formal-C-plan-20261111-140000/handoff/handoff-verification.json' $dest
Get-FileHash -Algorithm SHA256 (Join-Path $dest 'formal-C-plan-20261111-140000-light.tar.gz')
Get-Content (Join-Path $dest 'formal-C-plan-20261111-140000-light.tar.gz.sha256')
```

先对照外置SHA，再检查安全成员路径，在新目录解包并核对MANIFEST.sha256与全文件集合。后台已做实际安全解包及全SHA核验，接收端仍应独立核对。权重、数据和全量预测留远程，路径索引在remote-index.json。当前后台只负责远程交接产物的生成和核验，不自动向学校电脑传输。
