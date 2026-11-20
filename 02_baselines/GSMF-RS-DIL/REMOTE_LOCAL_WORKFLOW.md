# 本地论文项目与远程GSMF工程的联动

日期：2026-11-09（Asia/Shanghai）。状态：操作说明与评价提示词已准备；本轮未连接远程、修改SSH配置、安装远程Codex、同步文件或启动模型评价。

**最新接收（2026-11-11）：** 第3项三域首轮已完成并回传至[road_clear_fog_rain/formal-seed0-plan-20261110-180543/](../../03_experiments/road_clear_fog_rain/formal-seed0-plan-20261110-180543/)，[本机分析](../../03_experiments/road_clear_fog_rain/REVIEW_formal-seed0-plan-20261110-180543.md)记录900项核验、42格结果及包外最终完成／SHA证据。下文任务发送流程为准备时记录，不重新执行已完成训练；后续天气或重复须确定新范围。

**第3项准备时的记录（2026-11-10）：** 用户要求推进真实多天气链，已编写[STEP3_RAIN_CHAIN_REMOTE_TASK_20261110.md](STEP3_RAIN_CHAIN_REMOTE_TASK_20261110.md)，并以拒绝覆盖不同内容的方式新建到`home-wsl:/home/ysheng4/research/GSMF-RS-DIL/STEP3_RAIN_CHAIN_REMOTE_TASK_20261110.md`。两端均24,969字节，SHA-256为`3e978b4b70cea8b61be0ef3870059cf46a2eab0c4a8312618902569685d3f665`。已只读核对当前HEAD、Rain归档400／100图像与trainIds配对、四份Source／Fog检查点SHA；当时未解压Rain、修改训练代码或启动Codex／训练。第2项首轮已完成，后文“未启动第2项”及CLI登录状态均为当时快照。

在现有远程Codex中发送：“请读取`/home/ysheng4/research/GSMF-RS-DIL/STEP3_RAIN_CHAIN_REMOTE_TASK_20261110.md`，完整执行提示词一，先完成Rain三域链准备和真实短运行，不执行提示词二的正式训练。”准备产出具体方案后，再按该文件提示词二确认执行；中断恢复用提示词三。轻量结果接收目录改为`03_experiments/road_clear_fog_rain/<正式run-id>/`，其余SHA／安全解包流程沿用。

**后续核查（2026-11-10）：** 已使用用户给定别名`home-wsl`成功SSH连接`/home/ysheng4/research/GSMF-RS-DIL`，只读查看项目规则、代码入口和实验记录，并重新计算Source／FT／GSMF最终权重SHA一致。当前沙箱账号不能读取用户默认SSH配置，实际通过受审批的命令显式使用`C:\Users\sissi\.ssh\config`连接，未修改配置或复制密钥；无须因普通沙箱内别名解析失败就判断主机不可达。远程CLI`/snap/bin/codex`为0.114.0、登录状态`Not logged in`，未启动Codex任务；VS Code扩展登录与独立CLI登录须分别核查。第2项当前任务文件为[STEP2_LWF_BN_REMOTE_TASK_20261110.md](STEP2_LWF_BN_REMOTE_TASK_20261110.md)。下文评价任务及占位SSH别名属于11月9日历史示例，新的连接使用`home-wsl`；未启动第2项训练。

随后已将该任务文件以“存在不同内容则拒绝覆盖”的方式新建到远程项目根目录。远程与本地均为19,943字节，SHA-256均为`c784a5bafff2f45cc8866585d71a3ce0e541e24a474951d1fe8e56e46738e6af`。这是本轮唯一新增的远程项目文件，未更改训练代码、实验或运行状态。

## 1. 当前最省事的方式

本地`C:\undergraduate_thesis`负责研究资料和结果接收，远程`/home/ysheng4/research/GSMF-RS-DIL`负责代码、数据、权重和GPU推理。继续使用已有Tailscale／SSH连接，给远程Codex一个自包含任务文件，完成后回传轻量结果包。

本次任务文件：[FOG_SEVERITY_REMOTE_TASK.md](FOG_SEVERITY_REMOTE_TASK.md)。它已写入三个最终checkpoint的路径／SHA、四条件协议、GSMF部署分支、指标、预测图和回传要求。第一次可直接复制其代码框到远程Codex；以后可传文件，不必重述整段研究历史。

## 2. 传任务文件，再让远程Codex执行

在本地PowerShell运行，`你的WSL的SSH别名`必须替换为平时能登录家中WSL的别名。它应落到实际运行模型的Linux环境，不要把Windows宿主机误当作WSL。

```powershell
Set-Location -LiteralPath 'C:\undergraduate_thesis'
$remoteHost = '你的WSL的SSH别名'
ssh $remoteHost 'pwd'
scp '.\02_baselines\GSMF-RS-DIL\FOG_SEVERITY_REMOTE_TASK.md' "${remoteHost}:/home/ysheng4/research/GSMF-RS-DIL/FOG_SEVERITY_REMOTE_TASK_20261109.md"
```

使用与现有连接一致的SSH密钥／跳板配置，不在文档或任务文件中填写密码、私钥或令牌。本地已确认存在ssh.exe、scp.exe和tar.exe；尚未确认任何远程主机别名或连接可用性。

打开原有VS Code远程窗口中的GSMF仓库，向其中的Codex发送：

```text
请读取 /home/ysheng4/research/GSMF-RS-DIL/FOG_SEVERITY_REMOTE_TASK_20261109.md，按文件中代码框内的完整任务执行。它是我本轮明确要求的评价范围。先检查现场状态，数据齐全时继续完成实际评价和轻量包，不重新训练。缺数据则先完成可以独立完成的准备，并明确列出需要我提供的文件。
```

如使用SSH终端中的Codex CLI，从`/home/ysheng4/research/GSMF-RS-DIL`启动现有已登录的`codex`后发送同一句即可。单纯scp传文件不会自动触发远程Codex；上述发送消息才是开始任务的步骤。

## 3. 也可在桌面端直接打开远程项目

OpenAI官方文档支持桌面端通过SSH添加远程项目，在远程文件系统和shell执行。若当前客户端显示Settings → Connections → SSH：

1. 复用本地SSH配置中的具体Host别名，确认`ssh <别名>`连接到家中WSL。
2. 远程需已安装并登录Codex，而且登录shell的PATH能找到`codex`。仅在交互终端能找到而普通SSH命令找不到时，需要修正远程PATH；本轮未检查或改动。
3. 在Connections启用该SSH主机，选择`/home/ysheng4/research/GSMF-RS-DIL`作为远程项目。
4. 在远程项目聊天中发送上述任务文件读取指令。若客户端没有该入口，可继续现有VS Code远程方式，不必为本次评价更换工具。

这让本地界面操作远程工程；不会自动把两个仓库的文件或独立聊天合并。当前会话仍针对本地论文目录，没有因写好此文档就获得远程执行能力。[OpenAI Docs：Remote connections](https://learn.chatgpt.com/docs/remote-connections#connect-to-an-ssh-host)

官方另有聊天Hand off功能，要求目的地主机上已保存同一个Git仓库的项目；它传递聊天和Git状态。当前论文仓库与GSMF训练仓库是不同项目，不能直接假设符合条件；数据、checkpoint等未版本化大文件也不能假定随聊天交接迁移。当前更适合任务文件＋结果包。[OpenAI Docs：Hand off a chat](https://learn.chatgpt.com/docs/remote-connections#hand-off-a-chat-between-hosts)

## 4. 取回轻量结果

远程Codex结束后应给出本次压缩包和外置SHA文件的实际路径。把以下两个远程路径占位符替换为其返回值。归档文件名须与外置校验文件中的文件名相符。

```powershell
Set-Location -LiteralPath 'C:\undergraduate_thesis'
$remoteHost = '你的WSL的SSH别名'
$receivedDir = Join-Path (Get-Location).Path ('03_experiments\road_fog_severity\received-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $receivedDir -ErrorAction Stop | Out-Null
scp "${remoteHost}:/远程Codex给出的实际路径/结果包.tar.gz" $receivedDir
scp "${remoteHost}:/远程Codex给出的实际路径/结果包.tar.gz.sha256" $receivedDir
Get-ChildItem -LiteralPath $receivedDir
```

需要跳板时复用已有Host配置，scp与ssh使用相同别名；不要在这里虚构IP、端口或跳板地址。这里的接收目录每次新建，不覆盖上次归档；scp失败时先核对实际路径与退出状态。

然后在本地论文项目的Codex发送：

```text
请接收刚下载到03_experiments/road_fog_severity/received-实际时间/的多雾强度评价包。先校验压缩包SHA，检查归档成员路径安全，再解压到新的独立目录；按MANIFEST核对文件集合与哈希。从12个累计混淆矩阵独立复算mIoU和逐类表，核对权重／数据／推理分支证据及同场景预测图。检查与既有三模型结果的关系，明确完成、缺失及限制，不将远程路径当作本机文件。保存接收核验报告；仅在取得实际新结果后按里程碑更新PROJECT_STATE。不要重跑训练或修改原始结果。
```

## 5. 长期维护的最小约定

| 内容 | 权威位置／传递方式 |
| --- | --- |
| 课题目标、阶段、长期决策 | 本地PROJECT_STATE／DECISIONS，由本地接收实际证据后维护 |
| 具体任务 | 一个带日期的任务文件，通过复制文字或scp发给远程 |
| 代码、配置与启动脚本 | 远程工程为执行依据；Git按精确commit追溯，未提交改动带快照／diff |
| 数据、环境、模型、完整预测 | 保留远程，回传路径／SHA索引 |
| 本次实时状态 | 本次运行目录的STATUS及实际进程／日志，不能只看旧文档的running |
| 指标、矩阵、图、核验及少量样例 | 轻量包回传本地，按运行ID归档 |

Git适合共享小型代码与说明，提交／推送仍由用户决定。本轮不设置两个目录的全量双向自动同步，也不要求把模型、数据或整个论文资料库复制到另一端。具体下一项任务继续复用同一交接方式即可。
