# 远程C盘空间核查与清理方案（2026-11-11）

本文件依据2026-11-11约17:15通过`home-wsl`和`home-gpu`做的只读核查。**没有删除或移动任何文件，也没有关闭WSL**；当时阶段A的6次训练已经结束，进程正在跑62格评价。清理和压缩脚本在[disk_cleanup/](disk_cleanup/)，执行步骤见§5。**已于2026-11-11 20:12–20:35执行完毕，结果见§7。**

## 1. 现场快照

| 位置                                 | 数值                                                                                                                       |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------- |
| Windows C盘（WSL内`df -h /mnt/c`） | 952G，已用916G，**剩37G（97%）**                                                                                     |
| WSL根分区（`df -h /`）             | 1007G，已用328G，“可用628G”：这是虚拟盘上限，不是真实空间                                                                |
| `ext4.vhdx`                        | 329.5GB，`C:\Users\samsh\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu22.04LTS_79rhkp1fndgsc\LocalState\ext4.vhdx` |
| WSL版本                              | 2.6.3.0，根分区已带`discard`挂载                                                                                         |

WSL2把整个Linux文件系统放在C盘上的一个动态vhdx里。Linux里新写文件会让vhdx变大，删文件却不会让它自动缩小。所以不能看WSL里`df -h /`，判断空间要看`df -h /mnt/c`。现在vhdx大小和内部实际占用几乎相等，单做压缩也收不回空间，必须先在WSL里删文件，再压缩vhdx。

## 2. 空间去向

WSL内按文件修改日期统计（GB，十进制）：10/28–10/30 ISPRS复现约141GB；11/07 58.6、11/08 9.8、11/10 68.9、11/11 42.0，即道路实验约180GB。这和“GSMF复现时C盘还剩180多G”对得上：剩下的空间基本被道路实验用完了。

`~/research/GSMF-RS-DIL`共275GiB：`experiments` 186GiB，`data` 87GiB（其中`data/road_raw`下有三个原始zip共56GiB，Foggy zip占31GB）。checkpoint按用途分类：

| 类别                                                                     |   大小 | 个数 |
| ------------------------------------------------------------------------ | -----: | ---: |
| ISPRS周期checkpoint（`isprs-full-20261028-ucOKFM/{base,incremental}`） | 86.3GB |  129 |
| 道路debug／synthetic／prepare短训权重                                    | 48.1GB |   72 |
| 已接收道路正式运行的中间步（含Source iter_10000–50000）                 | 18.0GB |   27 |
| 2026-10-28 smoke实验权重                                                 |  6.2GB |   10 |
| 阶段A中间步iter_1000–3000                                               | 12.6GB |   18 |
| 道路正式最终权重（保留）                                                 |  9.8GB |   14 |

Windows侧（不含vhdx）：Steam 138GB、NetEase 46.5GB、Tencent Games 28GB、XboxGames 16GB、`orish`用户41.7GB、`samsh`下的Downloads 22GB／Videos 19GB／.android 16GB、AppData\Local\Temp 12GB、Windows侧pip缓存6.2GB、hiberfil.sys 11.9GB、System Volume Information 14.7GB。

## 3. 阶段B需求

16次训练、每次4个checkpoint：FT 8×4×0.575≈18.4GB，GSMF 8×4×0.765≈24.5GB，共约43GB，加上转换和预测，按50GB估算。C盘只剩37GB，还要给Windows留余量，不够。根分区按`errors=remount-ro`挂载，C盘写满时写入会失败，文件系统可能变成只读，正在写的checkpoint会损坏。

清理第一、二档并压缩虚拟盘后，C盘预计可用约190GB，阶段B（约50GB）和阶段C（8次训练，约21GB）都放得下，不需要改动“保留每1000步checkpoint”的约定。

## 4. 清理清单

规则写在[disk_cleanup/wsl_cleanup.sh](disk_cleanup/wsl_cleanup.sh)里。2026-11-11 17:39在远程只读预览（`plan --tier2`）的结果：

| 档位                   | 内容                                                                                                                   | 个数 |   大小 |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------- | ---: | -----: |
| 第一档                 | ISPRS `base/iter_1000–79000`、`incremental/iter_200–9800`                                                        |  128 | 86.1GB |
| 第一档                 | 道路`debug*`／`synthetic*`／`prepare*`目录里的`iter_*.pth`（只删权重，日志、manifest、`eval-manifests`保留） |   72 | 48.1GB |
| 第一档                 | `*smoke-20261028`里的`iter_*.pth`                                                                                  |    7 |  4.7GB |
| 第二档（`--tier2`）  | 4个已接收正式运行的iter_1000–3000，以及Source iter_10000–50000                                                       |   27 | 18.0GB |
| 第二档（`--stageA`） | 阶段A的18个中间步；status.json为complete才允许                                                                         |   18 | 12.6GB |

脚本自动保护、绝不删除：ISPRS `base/iter_80000.pth`、`incremental/iter_10000.pth`、`conversion/iter_80000_DIL.pth`，Source `iter_60000.pth`，各正式运行的`iter_4000.pth`，`formal-plans.json`／`READY.json`里出现的全部57个`.pth`，源码、配置、`scripts/`中引用到的路径，以及正在被进程打开的文件。上述4个必须保留的文件只要缺一个，脚本就停止。核对结果：预览清单里正式终点权重、阶段A文件、计划引用文件均为0个；`five_formal.py`只校验源码指纹，不读取短训权重。

**第三档：移出本机，不删除，56GB。** `data/road_raw`下的三个zip（Foggy 31GB、ACDC 17GB、Cityscapes 12GB）都已解压，但Cityscapes需要账号才能重新下载，应复制到外置盘并校验后再删原件（`export-zips`）。目标不能是`/mnt/c`，因为那还是同一块C盘。远程目前只有一个无介质的读卡器D:。

**缓存。** WSL：pip 4.6GB、conda pkgs 2.5GB（`caches --apply`）。Windows：pip缓存6.2GB、Temp中超过7天的1.3GB、`hiberfil.sys` 11.9GB（`-Mode WinClean -Apply [-DisableHibernate]`；关闭休眠会同时关闭快速启动，对常开的训练机没有影响）。

**非研究文件。** 游戏和其他用户目录约290GB，由机器使用者决定，脚本不处理。

## 5. 执行步骤

### 5.0 准备情况（2026-11-11 20:07）

- 阶段A：远程`status.json`为`complete`，没有GSMF进程和tmux会话，阶段B/C目录还没创建。本机已收到回传包，SHA256 `c09bbf78…a31e`与远程记录一致，包里不含权重。本机还没有解包做正式接收核验；核验只用包内内容和远程保留的`iter_4000`，所以删除阶段A的中间步不影响核验。
- 用`plan --tier2 --stageA`预览：252个文件、169.6GB；被保护的只有ISPRS两个`last_checkpoint`终点；阶段A只列入18个iter_1000–3000，`iter_4000`和`initialization/*_init.pth`都不在清单里。C盘可用40GB。
- 脚本版本：

| 位置 | 文件 | SHA256（前12位） |
| --- | --- | --- |
| WSL | `~/disk_cleanup/wsl_cleanup.sh` | `6ea690c16c87` |
| Windows | `C:\Users\samsh\wsl-maint\compact_wsl_vhdx.ps1` | `fe2bb4f4f8e2` |

  20:05版只改了两处：`apply`会和最近一次`plan`的清单逐个路径比对；压缩后的补救detach只在WSL没有运行时才执行。删除规则没有变化。
- 已在远程实测：`plan`、`--stageA`保护条件、`apply`的比对与非交互拒绝（未删除任何文件）、`Check`、`WinClean`预览、在WSL里调用时拒绝执行、`SelfTest`。`apply`真正删除和`Compact`真正压缩都没有运行过。

本地修改脚本后，在`C:\undergraduate_thesis`下用这两条命令重新上传：

```
scp 02_baselines/GSMF-RS-DIL/disk_cleanup/wsl_cleanup.sh home-wsl:disk_cleanup/wsl_cleanup.sh
scp 02_baselines/GSMF-RS-DIL/disk_cleanup/compact_wsl_vhdx.ps1 home-wsl:/mnt/c/Users/samsh/wsl-maint/compact_wsl_vhdx.ps1
```

### 5.1 两个脚本分别怎么运行

| | `wsl_cleanup.sh`（删文件） | `compact_wsl_vhdx.ps1`（压缩、重启WSL） |
| --- | --- | --- |
| 从哪登录 | 本机终端输入`ssh home-wsl` | 本机终端输入`ssh home-gpu` |
| 登录后的提示符 | `ysheng4@…:~$`（Linux） | `C:\Users\samsh>`（Windows cmd） |
| 运行方法 | `bash ~/disk_cleanup/wsl_cleanup.sh <子命令> [选项]` | 先`cd C:\Users\samsh\wsl-maint`，再`powershell -NoProfile -ExecutionPolicy Bypass -File compact_wsl_vhdx.ps1 -Mode <模式>` |
| 只读的部分 | `scan`、`plan`、不加`--apply`的`caches` | `-Mode Check`、`-Mode SelfTest`、`-Mode Status`、不加`-Apply`的`WinClean` |
| 会改动的部分 | `apply`（要输入`YES`）、`caches --apply`、`export-zips` | `-Mode Compact`（会关闭WSL）、`-Mode WinClean -Apply` |

`-ExecutionPolicy Bypass`只对这一次调用生效，不会改动系统设置。`.ps1`不能在home-wsl里运行，脚本检测到会直接拒绝。下文的`PS1`是`powershell -NoProfile -ExecutionPolicy Bypass -File compact_wsl_vhdx.ps1`的简写，前提是已经`cd`到`C:\Users\samsh\wsl-maint`。

### 5.2 操作步骤

**步骤1：预览（WSL，只读，约3分钟）**

```
ssh home-wsl
bash ~/disk_cleanup/wsl_cleanup.sh plan --tier2 --stageA
```

检查：
- 没有出现“应保留的文件不存在”。
- 合计约252个文件、169.6GB。
- “被保护”部分只有ISPRS的`iter_80000`和`iter_10000`。
- 清单里没有`iter_4000.pth`。

需要逐条看时，用`less ~/disk_cleanup_logs/<时间>-plan/delete.tsv`。数字明显不对就停下，把输出发给Claude。

**步骤2：删除（WSL，约1分钟）**

```
bash ~/disk_cleanup/wsl_cleanup.sh apply --tier2 --stageA
```

参数必须和步骤1完全相同。先确认输出里有“与上次预览…的清单完全一致”，再输入`YES`（大写），输入其他内容都会取消。完成后会显示“已删除 252 个文件”，记录保存在`~/disk_cleanup_logs/<时间>-apply/deleted.tsv`。

这时`/`的Used会从约329G降到约171G，但`/mnt/c`的Avail仍然是约40G。这是正常的，要等步骤4压缩之后C盘空间才会增加。

**步骤3：核对并清缓存（WSL）**

```
bash ~/disk_cleanup/wsl_cleanup.sh plan --tier2 --stageA    # 应显示“合计 0 个文件”，且没有报错
bash ~/disk_cleanup/wsl_cleanup.sh caches --apply           # 可选，pip 4.6GB + conda 2.5GB
exit
```

第一条再跑一次`plan`：结果为0，说明删干净了；没有报错，说明必须保留的4个文件都还在。

**步骤4：压缩虚拟盘（Windows）**

压缩前关闭本机连着home-wsl的VS Code远程窗口，并确认没有其他人在用这台机器的WSL。然后：

```
ssh home-gpu
cd C:\Users\samsh\wsl-maint
PS1 -Mode Check
PS1 -Mode Compact
```

- `Check`必须显示`No GSMF python processes in WSL`。
- `Compact`会依次输出`Shutting down WSL`、`Compaction running as SYSTEM task`，之后每30秒输出一行`compacting ... N min`。用时取决于磁盘，估计几分钟到几十分钟。
- 正常结束时会看到`diskpart finished: EXIT=0`、`vhdx 329.6 GB -> 约170 GB`、`C: free 约195 GB`，以及`sshd is active`。
- 等待时按Ctrl+C或SSH断线，都只是停止显示进度：压缩任务在后台继续，结束后会自动重启WSL。重新`ssh home-gpu`并`cd`到`C:\Users\samsh\wsl-maint`后，运行`PS1 -Mode Status`查看结果并收尾。

**步骤5：清Windows缓存（可选，Windows）**

```
PS1 -Mode WinClean                           # 预览
PS1 -Mode WinClean -Apply -DisableHibernate  # pip缓存6.2GB + 7天前Temp 1.3GB + 休眠文件11.9GB
exit
```

**步骤6：验证（本机）**

```
ssh home-wsl "df -h /mnt/c; ls -la ~/research/GSMF-RS-DIL/experiments/road_clear_to_fog/formal-seed0-20261108-resume01/source/iter_60000.pth; nvidia-smi --query-gpu=memory.used --format=csv"
```

C盘可用应达到约195–210GB，Source权重存在，GPU正常。之后把步骤2、4、6的输出发给Claude，用来更新本文件和PROJECT_STATE；接着做阶段A的本机接收核验，再发送阶段B提示词。

**以后：** 阶段B（或C）完成并接收后，运行`plan --run road_five_domain/formal-B-plan-20261111-140000`和对应的`apply`清理它的中间步，再重复步骤4。

**附：移走原始zip（可选，约56GB）。** 在远程主机插上外置盘（假设盘符为E:）。如果WSL里没有自动出现，先执行`sudo mkdir -p /mnt/e && sudo mount -t drvfs E: /mnt/e`。然后运行`bash ~/disk_cleanup/wsl_cleanup.sh export-zips /mnt/e/GSMF_raw_zips`复制并校验，原件保留；确认后加`--apply`再运行一次，才删除原件。去向记录在`data/road_raw/MOVED_ZIPS.tsv`。

### 5.3 出错时

| 现象 | 处理 |
| --- | --- |
| `plan`／`apply`提示“应保留的文件不存在” | 脚本已经停止，没有删除任何文件。把输出发给Claude查原因 |
| `apply`提示“与上次预览不一致” | 输入`NO`取消，用和`plan`相同的参数重新运行 |
| `apply`提示“当前不是交互终端” | 先`ssh home-wsl`登录再运行，或者用`ssh -t home-wsl "bash ~/disk_cleanup/wsl_cleanup.sh apply …"` |
| `Check`／`Compact`提示有GSMF进程 | 等进程结束。只有确认是残留进程时才加`-Force`，它会强制结束这些进程 |
| `Compact`提示`vhdx is still in use` | 有东西重新拉起了WSL。在home-gpu运行`wsl --shutdown`，再执行`PS1 -Mode Compact` |
| `diskpart finished: EXIT=1`或其他非0 | vhdx是以只读方式挂载的，数据不受影响；脚本已经detach并重启WSL。把`C:\ProgramData\wsl-compact\compact.log`发给Claude |
| `WARNING: WSL/sshd not confirmed` | 运行`PS1 -Mode StartWsl`；仍然不行就重启远程主机，开机任务会拉起WSL |

不建议在实验期间用`wsl --manage ... --set-sparse true`让vhdx自动缩小：WSL把这项标为可能损坏数据，需要额外加unsafe参数才能开启。

## 7. 执行结果（2026-11-11）

| 步骤 | 结果 |
| --- | --- |
| WSL删除（20:12，`apply --tier2 --stageA`） | 252个文件、169.6GB：ISPRS中间权重128个、道路debug／prepare短训72个、smoke 7个、正式运行中间步45个（含阶段A的18个）。记录在远程`~/disk_cleanup_logs/20261111-201244-apply/deleted.tsv`。WSL根分区已用从329G降到171G |
| 删除后核对 | 再运行`plan --tier2 --stageA`，结果为0个文件；4个必须保留的文件都在；`iter_60000.pth`为612,017,669字节 |
| WSL缓存 | pip剩7.8M，conda pkgs剩646M |
| 压缩（20:15:54–20:34:40，约19分钟） | diskpart `EXIT=0`；vhdx从330.6GB压到166.5GB；C盘可用226.9GB；WSL通过开机任务自动重启，sshd为active；临时计划任务已删除 |
| Windows清理（`WinClean -Apply -DisableHibernate`） | hiberfil.sys已删除，pip缓存为0 |
| 20:41复查 | C盘可用约243GB（WSL重新创建了约4GB的swap.vhdx）；WSL根分区已用165G |
| GPU | `/dev/dxg`存在；`/usr/lib/wsl/lib/nvidia-smi`识别出RTX 3080 20GB；GSMF_RS_DIL环境中torch 1.9.1+cu111的CUDA可用，矩阵乘法测试通过。直接运行`nvidia-smi`提示找不到，是因为SSH非交互会话的PATH里不含`/usr/lib/wsl/lib`，用完整路径即可，与清理无关 |

20:41时GPU利用率95%、显存占用4.3GB，来自Windows侧正在运行的游戏《Minecraft Dungeons II》，不是WSL进程。阶段B开始前要确认GPU负载；共享负载下测得的速度不能代表正常训练速度。

## 6. 以后怎么查

- WSL内：`df -h /mnt/c`；`du -xh --max-depth=1 ~/research/GSMF-RS-DIL/experiments | sort -rh | head`；`find ~/research -name 'iter_*.pth' -printf '%h\n' | sort | uniq -c`。如果允许安装软件，`ncdu -x ~`可以交互式浏览。
- Windows侧：WizTree（读取MFT，很快）或“设置→系统→存储”。这两个工具只能把`ext4.vhdx`显示成一个大文件，看不到里面的内容；vhdx里面的占用要在WSL里用du或ncdu查。
