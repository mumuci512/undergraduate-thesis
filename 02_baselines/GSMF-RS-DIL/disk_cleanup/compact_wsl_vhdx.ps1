<#
compact_wsl_vhdx.ps1 - give space freed inside WSL back to drive C: by compacting ext4.vhdx,
plus optional Windows-side cleanup. Kept ASCII-only on purpose: Windows PowerShell 5.1 reads
BOM-less scripts with the ANSI code page.

Run it on the Windows host in an elevated session: ssh home-gpu
(NOT ssh home-wsl - shutting WSL down would kill that session).

  powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\samsh\wsl-maint\compact_wsl_vhdx.ps1 [-Mode X]

  -Mode Check     (default, read-only) C: free space, vhdx size, WSL state, GSMF jobs in WSL.
  -Mode SelfTest  run the SYSTEM-task + diskpart + log path with read-only diskpart commands
                  (list vdisk / list volume); WSL is not touched. Run once before Compact.
  -Mode Compact   wsl --shutdown -> diskpart compact, run as a one-off SYSTEM scheduled task so it
                  survives an SSH disconnect -> WSL restarted through the 'Start WSL Ubuntu' task
                  -> sshd checked. Refuses while GSMF python processes run in WSL (unless -Force).
  -Mode Status    show the compaction log and task state; finishes up after a reconnect.
  -Mode StartWsl  start WSL + sshd only.
  -Mode WinClean  show Windows-side caches. With -Apply: empty the pip cache and delete Temp items
                  older than 7 days; add -DisableHibernate (powercfg /h off) and/or -Dism
                  (DISM component cleanup) to do those too.
#>
[CmdletBinding()]
param(
    [ValidateSet('Check', 'SelfTest', 'Compact', 'Status', 'StartWsl', 'WinClean')]
    [string]$Mode = 'Check',
    [string]$Distro = 'Ubuntu-22.04',
    [string]$StartTaskName = 'Start WSL Ubuntu',
    [switch]$Force,
    [switch]$Apply,
    [switch]$DisableHibernate,
    [switch]$Dism
)

$ErrorActionPreference = 'Stop'
$env:WSL_UTF8 = '1'
$Work = Join-Path $env:ProgramData 'wsl-compact'
$Log = Join-Path $Work 'compact.log'
$TaskName = 'WSL-Compact-Once'
$LxssKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss'

function Say([string]$m) { Write-Host ('[{0}] {1}' -f (Get-Date -Format 'HH:mm:ss'), $m) }
function GB([double]$b) { [math]::Round($b / 1GB, 1) }
function Short([string]$s) { $s.Substring(0, [math]::Min(150, $s.Length)) }

function Invoke-Native([scriptblock]$Block) {
    # Windows PowerShell 5.1 turns native stderr into terminating errors when EAP=Stop.
    $old = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { & $Block 2>&1 | ForEach-Object { ("$_" -replace "`0", '').TrimEnd() } }
    finally { $ErrorActionPreference = $old }
}

function Test-Admin {
    $p = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Assert-Admin {
    if (-not (Test-Admin)) { throw 'Administrator rights are required (use ssh home-gpu with an admin account).' }
}

function Assert-NotInsideWsl {
    $id = $PID
    for ($i = 0; $i -lt 6; $i++) {
        $p = Get-CimInstance Win32_Process -Filter "ProcessId=$id" -ErrorAction SilentlyContinue
        if (-not $p) { break }
        if ($p.Name -match '^(wsl|wslhost|wslrelay)\.exe$') {
            throw 'Started from inside WSL (home-wsl). Run this from the Windows side: ssh home-gpu.'
        }
        if (-not $p.ParentProcessId -or $p.ParentProcessId -eq $id) { break }
        $id = $p.ParentProcessId
    }
}

function Get-DistroNames {
    @(Get-ChildItem $LxssKey | ForEach-Object { (Get-ItemProperty $_.PSPath).DistributionName })
}

function Get-VhdxPath {
    $item = Get-ChildItem $LxssKey | ForEach-Object { Get-ItemProperty $_.PSPath } |
        Where-Object { $_.DistributionName -eq $Distro } | Select-Object -First 1
    if (-not $item) { throw "Distro '$Distro' not found under $LxssKey (run as the Windows user that owns WSL)." }
    $base = [string]$item.BasePath
    if ($base.StartsWith('\\?\')) { $base = $base.Substring(4) }
    $v = Join-Path $base 'ext4.vhdx'
    if (-not (Test-Path -LiteralPath $v)) { throw "vhdx not found: $v" }
    return $v
}

function Get-RunningDistros {
    $names = Get-DistroNames
    $out = Invoke-Native { wsl.exe --list --running --quiet }
    return @($out | ForEach-Object { $_.Trim() } | Where-Object { $names -contains $_ })
}

function Get-ActiveJobs {
    $out = Invoke-Native { wsl.exe -d $Distro -e bash -c "pgrep -af '[e]nvs/GSMF_RS_DIL/bin/python' || true" }
    return @($out | Where-Object { $_ -match 'GSMF_RS_DIL' })
}

function Test-Unlocked([string]$Path) {
    try { $fs = [IO.File]::Open($Path, 'Open', 'ReadWrite', 'None'); $fs.Close(); return $true }
    catch { return $false }
}

function Test-Attached([string]$Path) {
    try { return [bool](Get-DiskImage -ImagePath $Path -ErrorAction Stop).Attached } catch { return $false }
}

function Get-CFree { (Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'").FreeSpace }

function Show-Space([string]$Vhdx) {
    $c = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
    Say ('C: free {0} GB of {1} GB' -f (GB $c.FreeSpace), (GB $c.Size))
    Say ('vhdx   {0} GB  {1}' -f (GB (Get-Item -LiteralPath $Vhdx).Length), $Vhdx)
}

function Start-Wsl {
    $task = Get-ScheduledTask -TaskName $StartTaskName -ErrorAction SilentlyContinue
    if ($task) {
        Say "Starting WSL through scheduled task '$StartTaskName' ..."
        Start-ScheduledTask -TaskName $StartTaskName
    } else {
        Say "Task '$StartTaskName' not found; starting WSL directly ..."
        Invoke-Native { wsl.exe -d $Distro -u root --exec /usr/bin/systemctl start ssh } | Out-Host
    }
    for ($i = 0; $i -lt 40; $i++) {
        Start-Sleep -Seconds 3
        if ((Get-RunningDistros) -contains $Distro) {
            $state = (Invoke-Native { wsl.exe -d $Distro -u root -e systemctl is-active ssh }) -join ' '
            if ($state -match '(^|\s)active(\s|$)') {
                Say "WSL '$Distro' is running and sshd is active; 'ssh home-wsl' should work again."
                return $true
            }
        }
        if ($i -eq 20) {
            Say 'Not up yet; trying a direct start ...'
            Invoke-Native { wsl.exe -d $Distro -u root --exec /usr/bin/systemctl start ssh } | Out-Host
        }
    }
    Say "WARNING: WSL/sshd not confirmed. Try: wsl -d $Distro -u root --exec /usr/bin/systemctl start ssh"
    return $false
}

function Start-DiskpartTask([string]$Name, [string]$Script, [string]$LogPath, [string]$OnFail, [string]$After) {
    # Writes a runner script and starts it as a one-off SYSTEM scheduled task (survives SSH disconnect).
    $runner = Join-Path $Work "$Name.ps1"
    $failLine = ''
    if ($OnFail) { $failLine = "if (`$code -ne 0) { cmd.exe /c `"diskpart.exe /s $OnFail >> $LogPath 2>&1`" }" }
    @(
        "`$log = '$LogPath'",
        "'START ' + (Get-Date -Format s) | Out-File -FilePath `$log -Encoding ascii",
        "cmd.exe /c `"diskpart.exe /s $Script >> $LogPath 2>&1`"",
        '$code = $LASTEXITCODE',
        $failLine,
        "'EXIT=' + `$code | Out-File -FilePath `$log -Append -Encoding ascii",
        $After,
        "'DONE ' + (Get-Date -Format s) | Out-File -FilePath `$log -Append -Encoding ascii"
    ) | Set-Content -LiteralPath $runner -Encoding ASCII
    Remove-Item -LiteralPath $LogPath -ErrorAction SilentlyContinue
    $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File $runner"
    $principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 8) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    Register-ScheduledTask -TaskName $Name -Action $action -Principal $principal -Settings $settings -Force | Out-Null
    Start-ScheduledTask -TaskName $Name
}

function Wait-Done([string]$LogPath, [int]$IntervalSec, [double]$MaxMinutes, [switch]$Progress) {
    $t0 = Get-Date
    while ($true) {
        Start-Sleep -Seconds $IntervalSec
        if ((Test-Path -LiteralPath $LogPath) -and (Select-String -LiteralPath $LogPath -Pattern '^DONE' -Quiet)) { return $true }
        $mins = [math]::Round(((Get-Date) - $t0).TotalMinutes, 1)
        if ($Progress) {
            $last = ''
            if (Test-Path -LiteralPath $LogPath) { $last = ((Get-Content -LiteralPath $LogPath -Tail 1 -Encoding Default) -replace '\s+', ' ').Trim() }
            Say "compacting ... $mins min  $last"
        }
        if ($mins -gt $MaxMinutes) { return $false }
    }
}

function Complete-Compact([string]$Vhdx, [double]$Before) {
    $text = @(Get-Content -LiteralPath $Log -Encoding Default)
    $exit = $text | Where-Object { $_ -match '^EXIT=' } | Select-Object -Last 1
    Say "diskpart finished: $exit"
    if ($exit -ne 'EXIT=0') {
        Say 'Compaction reported an error. Full log:'
        $text | ForEach-Object { Write-Host "  $_" }
    }
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    if ((Test-Attached $Vhdx) -and -not ((Get-RunningDistros) -contains $Distro)) {
        Say 'vhdx still attached; detaching ...'
        Invoke-Native { diskpart.exe /s (Join-Path $Work 'detach.txt') } | Out-Host
    }
    if ($Before -gt 0) { Say ('vhdx {0} GB -> {1} GB' -f (GB $Before), (GB (Get-Item -LiteralPath $Vhdx).Length)) }
    Show-Space $Vhdx
    [void](Start-Wsl)
}

function Invoke-Compact {
    Assert-Admin
    Assert-NotInsideWsl
    $vhdx = Get-VhdxPath
    Show-Space $vhdx
    $before = (Get-Item -LiteralPath $vhdx).Length
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing -and $existing.State -eq 'Running') { throw 'A compaction task is already running; use -Mode Status.' }
    $hasStartTask = [bool](Get-ScheduledTask -TaskName $StartTaskName -ErrorAction SilentlyContinue)
    if (-not $hasStartTask) { Say "WARNING: task '$StartTaskName' not found; WSL will only be restarted by this session." }

    if ((Get-RunningDistros).Count -gt 0) {
        $jobs = @(Get-ActiveJobs)
        if ($jobs.Count -gt 0) {
            $jobs | ForEach-Object { Say ('running in WSL: ' + (Short $_)) }
            if (-not $Force) { throw 'GSMF training/evaluation is still running in WSL. Wait for it to finish (or use -Force to kill it).' }
        }
        Say 'Shutting down WSL (wsl --shutdown) ...'
        Invoke-Native { wsl.exe --shutdown } | Out-Host
    }
    for ($i = 0; $i -lt 60 -and -not (Test-Unlocked $vhdx); $i++) { Start-Sleep -Seconds 2 }
    if (-not (Test-Unlocked $vhdx)) { throw 'The vhdx is still in use (did something restart WSL?). Check "wsl -l -v" and retry.' }
    if (Test-Attached $vhdx) { throw 'The vhdx is attached as a disk; detach it first (diskpart: select vdisk file=...; detach vdisk).' }

    New-Item -ItemType Directory -Force -Path $Work | Out-Null
    $dp = Join-Path $Work 'compact.txt'
    $dd = Join-Path $Work 'detach.txt'
    @("select vdisk file=`"$vhdx`"", 'attach vdisk readonly', 'compact vdisk', 'detach vdisk') |
        Set-Content -LiteralPath $dp -Encoding ASCII
    @("select vdisk file=`"$vhdx`"", 'detach vdisk') | Set-Content -LiteralPath $dd -Encoding ASCII
    $after = "'NO-START-TASK' | Out-File -FilePath `$log -Append -Encoding ascii"
    if ($hasStartTask) {
        $after = "Start-ScheduledTask -TaskName '$StartTaskName'; 'WSL-START-REQUESTED' | Out-File -FilePath `$log -Append -Encoding ascii"
    }
    Start-DiskpartTask $TaskName $dp $Log $dd $after
    Say "Compaction running as SYSTEM task '$TaskName' (log: $Log)."
    Say 'If this SSH session drops, the task carries on and restarts WSL itself; reconnect and use -Mode Status.'
    if (-not (Wait-Done $Log 30 480 -Progress)) { throw 'Timed out after 8 h; check -Mode Status.' }
    Complete-Compact $vhdx $before
}

function Invoke-SelfTest {
    # Exercises the same SYSTEM-task + diskpart + log-marker path with read-only diskpart commands.
    Assert-Admin
    New-Item -ItemType Directory -Force -Path $Work | Out-Null
    $name = 'WSL-Compact-SelfTest'
    $dp = Join-Path $Work 'selftest.txt'
    $log = Join-Path $Work 'selftest.log'
    @('list vdisk', 'list volume') | Set-Content -LiteralPath $dp -Encoding ASCII
    Start-DiskpartTask $name $dp $log '' "'AFTER-HOOK-RAN' | Out-File -FilePath `$log -Append -Encoding ascii"
    Say "Self-test task '$name' started (diskpart 'list vdisk' and 'list volume' only) ..."
    $done = Wait-Done $log 3 3
    $text = @()
    if (Test-Path -LiteralPath $log) { $text = @(Get-Content -LiteralPath $log -Encoding Default) }
    $text | ForEach-Object { Write-Host "  $_" }
    Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $dp, $log, (Join-Path $Work "$name.ps1") -ErrorAction SilentlyContinue
    if ($done -and ($text -contains 'EXIT=0') -and ($text -contains 'AFTER-HOOK-RAN')) {
        Say 'SELF-TEST PASSED: SYSTEM task, diskpart, log markers and after-hook all work.'
    } else {
        Say 'SELF-TEST FAILED: do not run -Mode Compact until this is understood.'
    }
}

function Show-Status {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task) { Say "Task '$TaskName' state: $($task.State)" } else { Say "Task '$TaskName' not registered (already cleaned up, or never started)." }
    $hasDone = $false
    if (Test-Path -LiteralPath $Log) {
        Say "Log $Log :"
        Get-Content -LiteralPath $Log -Encoding Default | ForEach-Object { Write-Host "  $_" }
        $hasDone = [bool](Select-String -LiteralPath $Log -Pattern '^DONE' -Quiet)
    } else { Say 'No compaction log.' }
    $vhdx = Get-VhdxPath
    Show-Space $vhdx
    Say ('Running distros: ' + ((Get-RunningDistros) -join ', '))
    if ($task -and $task.State -ne 'Running' -and $hasDone) {
        Assert-Admin
        Complete-Compact $vhdx 0
    }
}

function Show-Check {
    $vhdx = Get-VhdxPath
    Show-Space $vhdx
    Say ('Elevated session: ' + (Test-Admin))
    $running = @(Get-RunningDistros)
    Say ('Running distros: ' + ($running -join ', '))
    if ($running -contains $Distro) {
        Invoke-Native { wsl.exe -d $Distro -e df -h / /mnt/c } | ForEach-Object { Write-Host "  $_" }
        $jobs = @(Get-ActiveJobs)
        if ($jobs.Count -gt 0) {
            Say "GSMF python processes running in WSL ($($jobs.Count)) - do NOT compact yet:"
            $jobs | ForEach-Object { Write-Host ('  ' + (Short $_)) }
        } else { Say 'No GSMF python processes in WSL; compaction would not interrupt experiments.' }
    }
    $t = Get-ScheduledTask -TaskName $StartTaskName -ErrorAction SilentlyContinue
    if ($t) { Say "Start task '$StartTaskName' found (state $($t.State))." } else { Say "WARNING: start task '$StartTaskName' not found." }
    $c = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($c) { Say "Leftover compaction task '$TaskName' state: $($c.State) (see -Mode Status)." }
}

function Get-TreeSize([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return 0 }
    $s = (Get-ChildItem -LiteralPath $Path -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
    if ($s) { return $s } else { return 0 }
}

function Invoke-WinClean {
    $pip = Join-Path $env:LOCALAPPDATA 'pip\cache'
    $tmp = $env:TEMP
    $cut = (Get-Date).AddDays(-7)
    $old = @(Get-ChildItem -LiteralPath $tmp -Force -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt $cut })
    $oldSize = 0
    foreach ($o in $old) { if ($o.PSIsContainer) { $oldSize += Get-TreeSize $o.FullName } else { $oldSize += $o.Length } }
    $hib = Get-ChildItem -LiteralPath 'C:\' -Force -File -Filter 'hiberfil.sys' -ErrorAction SilentlyContinue | Select-Object -First 1
    Say ('pip cache          {0} GB  {1}' -f (GB (Get-TreeSize $pip)), $pip)
    Say ('Temp older than 7d {0} GB  {1} ({2} items)' -f (GB $oldSize), $tmp, $old.Count)
    if ($hib) { Say ('hiberfil.sys       {0} GB' -f (GB $hib.Length)) }
    Say ('C: free {0} GB' -f (GB (Get-CFree)))
    if (-not $Apply) {
        Say 'Preview only. Add -Apply to clean pip cache + old Temp items; with -Apply also -DisableHibernate and/or -Dism.'
        return
    }
    if (Test-Path -LiteralPath $pip) {
        Get-ChildItem -LiteralPath $pip -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }
    $old | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    if ($DisableHibernate) { Assert-Admin; Invoke-Native { powercfg.exe /hibernate off } | Out-Host; Say 'Hibernation off (fast startup is off too).' }
    if ($Dism) { Assert-Admin; Say 'Running DISM component cleanup (can take 10+ min) ...'; Invoke-Native { Dism.exe /Online /Cleanup-Image /StartComponentCleanup } | Out-Host }
    Say ('C: free now {0} GB' -f (GB (Get-CFree)))
}

switch ($Mode) {
    'Check'    { Show-Check }
    'SelfTest' { Invoke-SelfTest }
    'Compact'  { Invoke-Compact }
    'Status'   { Show-Status }
    'StartWsl' { [void](Start-Wsl) }
    'WinClean' { Invoke-WinClean }
}
